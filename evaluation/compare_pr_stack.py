"""Compare Deploy, previous PR #1, and FCS on one fixed local search index."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import types


HERE = Path(__file__).resolve().parent
TOP_K = 10
REVISIONS = {
    "deploy": "d9cff5d3f21dc11423465893fb1839dd6c9251c0",
    "pr1": "bc755b9d2808f8da743494e5a7f516c3f0fcc6e2",
    "fcs": "54990b849f176d722fb087372c8875cb2d7c6e14",
}
COMMENTARY_FIELDS = {"ai": "ai", "en_tafsir": "en_tafsir"}
ARABIC = re.compile(r"[\u0600-\u06ff]")


def read_cases(path):
    data = path.read_bytes()
    cases = [json.loads(line) for line in data.decode("utf8").splitlines() if line.strip()]
    ids = set()
    queries = set()
    for case in cases:
        key = (case["query"].strip().casefold(), case["field"])
        if case["id"] in ids or key in queries or not key[0]:
            raise ValueError(f"Duplicate ID, duplicate query or empty query: {case['id']}")
        if case["field"] not in ("all", "ayah", "translation", "ai", "en_tafsir", "bn_tafsir"):
            raise ValueError(f"Invalid field in {case['id']}: {case['field']}")
        for ref, grade in case.get("judgments", {}).items():
            if not re.fullmatch(r"\d+:\d+", ref) or grade not in (1, 2):
                raise ValueError(f"Invalid judgment in {case['id']}: {ref}, {grade}")
        ids.add(case["id"])
        queries.add(key)
    if not cases:
        raise ValueError("Fixture contains no cases")
    return cases, data


def anchors(case):
    expected = set(case.get("expected") or [])
    if expected:
        return expected
    return {ref for ref, grade in case.get("judgments", {}).items() if grade == 2}


def folded(text):
    return " ".join((text or "").split()).casefold()


def validate_commentary(repo, cases):
    if len(cases) != 40:
        raise ValueError(f"Commentary fixture must contain 40 cases, found {len(cases)}")
    counts = defaultdict(int)
    errors = []
    with sqlite3.connect(f"{(repo / 'db/search.db').as_uri()}?mode=ro", uri=True) as db:
        for case in cases:
            field = case["field"]
            counts[field] += 1
            if field not in COMMENTARY_FIELDS:
                raise ValueError(f"Commentary case {case['id']} has non-commentary field {field}")
            if case.get("intent") != "multi" or case.get("language") != "en":
                raise ValueError(f"Commentary case {case['id']} must be an English multi-keyword query")
            if case.get("split") != "dev":
                raise ValueError(f"Commentary case {case['id']} must remain in the dev split")
            if case.get("provenance") != "model_authored_commentary_native":
                raise ValueError(f"Unexpected provenance in {case['id']}")
            if case.get("review") != "source_checked_independent_review_pending":
                raise ValueError(f"Independent review status is not explicit in {case['id']}")
            expected = anchors(case)
            if len(expected) != 1 or case.get("judgments") != {next(iter(expected)): 2}:
                raise ValueError(f"Commentary case {case['id']} needs one grade-2 anchor")
            ref = next(iter(expected))
            if case.get("family") != f"commentary-ref-{ref}":
                raise ValueError(f"Family and anchor disagree in {case['id']}")
            if len(case["query"].split()) < 3:
                raise ValueError(f"Commentary query is too short: {case['id']}")
            evidence = case.get("evidence_fragment") or ""
            if len(evidence.split()) < 3:
                raise ValueError(f"Evidence fragment is too short: {case['id']}")
            surah, verse = (int(part) for part in ref.split(":"))
            row = db.execute(
                f"SELECT {COMMENTARY_FIELDS[field]} FROM docs WHERE surah=? AND verse=?",
                (surah, verse),
            ).fetchone()
            if row is None or folded(evidence) not in folded(row[0]):
                errors.append(f"Evidence not found in {field} commentary at {ref}: {case['id']}")
    if dict(counts) != {"ai": 20, "en_tafsir": 20}:
        errors.append(f"Commentary fixture needs 20 AI and 20 English-tafsir cases, found {dict(counts)}")
    if errors:
        raise ValueError("\n".join(errors))
    return {"cases": len(cases), "field_counts": dict(counts), "source_evidence": "all_checked"}


def resolve_revision(repo, revision):
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", revision], text=True
    ).strip()


def dependency_hashes(repo, revisions):
    hashes = {
        name: subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", f"{revision}:searchnorm.py"], text=True
        ).strip()
        for name, revision in revisions.items()
    }
    if len(set(hashes.values())) != 1:
        raise ValueError(f"Search normalization differs across compared revisions: {hashes}")
    return hashes


def load_engine(repo, revision, scopes):
    source = subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{revision}:searchtool.py"]
    ).decode("utf8")
    module = types.ModuleType("pr_stack_revision")
    module.__file__ = str(repo / "searchtool.py")
    exec(compile(source, f"{revision}:searchtool.py", "exec"), module.__dict__)
    for scope in scopes:
        module.index_search("mercy", TOP_K, field=scope)
    module._load_vocab()
    module._load_bk_tree()
    return module


def first_rank(refs, expected):
    return next((rank for rank, ref in enumerate(refs, 1) if ref in expected), 0)


def run_search(engine, case):
    started = time.perf_counter()
    hits, _ = engine.index_search(case["query"], TOP_K, field=case["field"])
    elapsed = (time.perf_counter() - started) * 1000
    return {
        "results": [f"{hit['surah']}:{hit['verse']}" for hit in hits],
        "ms": round(elapsed, 3),
    }


def group_keys(case):
    keys = ["all"]
    for key in ("field", "intent", "kind", "language", "provenance", "split"):
        if case.get(key):
            keys.append(f"{key}={case[key]}")
    if (case.get("kind") or "").startswith("surah") and ARABIC.search(case["query"]):
        keys.append("surah_arabic")
    return keys


def summarize(cases, runs, engine):
    groups = defaultdict(list)
    for case in cases:
        expected = anchors(case)
        if not expected:
            continue
        refs = runs[case["id"]][engine]["results"]
        rank = first_rank(refs, expected)
        for key in group_keys(case):
            groups[key].append((case, rank))
    metrics = {}
    for key, rows in groups.items():
        ranks = [rank for _, rank in rows]
        timings = sorted(runs[case["id"]][engine]["ms"] for case, _ in rows)
        metrics[key] = {
            "n": len(rows),
            "successful_at_1": sum(rank == 1 for rank in ranks),
            "successful_at_5": sum(0 < rank <= 5 for rank in ranks),
            "hit_at_5": sum(0 < rank <= 5 for rank in ranks) / len(ranks),
            "mrr_at_10": sum(1 / rank if 0 < rank <= TOP_K else 0 for rank in ranks) / len(ranks),
            "p50_ms": timings[math.ceil(.50 * len(timings)) - 1],
            "p95_ms": timings[math.ceil(.95 * len(timings)) - 1],
        }
    return metrics


def comparison_rows(cases, runs, baseline, candidate):
    groups = defaultdict(list)
    for case in cases:
        expected = anchors(case)
        if not expected:
            continue
        baseline_refs = runs[case["id"]][baseline]["results"]
        candidate_refs = runs[case["id"]][candidate]["results"]
        baseline_rank = first_rank(baseline_refs, expected)
        candidate_rank = first_rank(candidate_refs, expected)
        row = {
            "id": case["id"],
            "query": case["query"],
            "field": case["field"],
            "baseline_rank": baseline_rank,
            "candidate_rank": candidate_rank,
            "baseline_success": 0 < baseline_rank <= 5,
            "candidate_success": 0 < candidate_rank <= 5,
        }
        for key in group_keys(case):
            groups[key].append(row)
    return groups


def summarize_comparison(rows):
    gained = [row for row in rows if not row["baseline_success"] and row["candidate_success"]]
    lost = [row for row in rows if row["baseline_success"] and not row["candidate_success"]]
    regressions = [
        row for row in rows
        if row["baseline_rank"] and
        (not row["candidate_rank"] or row["candidate_rank"] > row["baseline_rank"])
    ]
    top_five_losses = [
        row for row in lost if row["baseline_rank"] <= 5
    ]
    baseline_success = sum(row["baseline_success"] for row in rows)
    candidate_success = sum(row["candidate_success"] for row in rows)
    return {
        "n": len(rows),
        "baseline_successful_at_5": baseline_success,
        "candidate_successful_at_5": candidate_success,
        "gained": len(gained),
        "lost": len(lost),
        "net": candidate_success - baseline_success,
        "retained": sum(row["baseline_success"] and row["candidate_success"] for row in rows),
        "neither": sum(not row["baseline_success"] and not row["candidate_success"] for row in rows),
        "rank_regressions": len(regressions),
        "top_five_losses": len(top_five_losses),
    }, gained, lost, regressions, top_five_losses


def compare(cases, runs, baseline, candidate):
    groups = comparison_rows(cases, runs, baseline, candidate)
    summaries = {}
    details = {}
    for key, rows in groups.items():
        summary, gained, lost, regressions, losses = summarize_comparison(rows)
        summaries[key] = summary
        if key == "all":
            details = {
                "gained_cases": gained,
                "lost_cases": lost,
                "rank_regressions": regressions,
                "top_five_losses": losses,
            }
    return {"groups": summaries, **details}


def index_info(repo):
    path = repo / "db/search.db"
    if not path.is_file():
        raise FileNotFoundError(f"Build the search index first: {path}")
    with sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        docs = db.execute("SELECT count(*) FROM docs").fetchone()[0]
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "docs": docs,
        "english_stem": "english_stem" in tables,
        "docs_trgm": "docs_trgm" in tables,
        "sqlite_version": sqlite3.sqlite_version,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=HERE.parent.parent / "aayatun-research")
    parser.add_argument("--fixture", type=Path, default=HERE / "commentary_native.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-sha256")
    parser.add_argument(
        "--field", choices=["all", "ayah", "translation", "en_tafsir", "bn_tafsir", "ai"],
        help="Override the fixture field scope for generalized regression runs")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    fixture = args.fixture.resolve()
    output = args.output.resolve()
    cases, data = read_cases(fixture)
    fixture_hash = hashlib.sha256(data).hexdigest()
    if args.expected_sha256 and fixture_hash != args.expected_sha256:
        raise ValueError(f"Fixture hash mismatch: {fixture_hash}")
    if fixture.name == "challenge_v2.jsonl":
        manifest = json.loads((HERE / "challenge_manifest.json").read_text(encoding="utf8"))
        if manifest["query_sha256"] != fixture_hash:
            raise ValueError("Challenge fixture hash does not match its manifest")
    commentary = fixture.name == "commentary_native.jsonl"
    validation = validate_commentary(repo, cases) if commentary else None
    if args.field:
        cases = [{**case, "field": args.field} for case in cases]
    if args.validate_only:
        print(json.dumps({"fixture": fixture.name, "sha256": fixture_hash, "validation": validation}, indent=2))
        return

    revisions = {name: resolve_revision(repo, revision) for name, revision in REVISIONS.items()}
    norm_hashes = dependency_hashes(repo, revisions)
    info = index_info(repo)
    os.chdir(repo)
    sys.path.insert(0, str(repo))
    scopes = sorted({case["field"] for case in cases})
    engines = {name: load_engine(repo, revision, scopes) for name, revision in revisions.items()}
    runs = {}
    names = list(engines)
    for index, case in enumerate(cases):
        shift = index % len(names)
        order = names[shift:] + names[:shift]
        runs[case["id"]] = {name: run_search(engines[name], case) for name in order}
        if index % 100 == 0:
            print(f"{fixture.name} {index}/{len(cases)}", flush=True)

    metrics = {name: summarize(cases, runs, name) for name in engines}
    comparisons = {
        "fcs_vs_deploy": compare(cases, runs, "deploy", "fcs"),
        "fcs_vs_pr1": compare(cases, runs, "pr1", "fcs"),
    }
    report = {
        "fixture": fixture.name,
        "fixture_sha256": fixture_hash,
        "fixture_cases": len(cases),
        "answerable_cases": sum(bool(anchors(case)) for case in cases),
        "commentary_validation": validation,
        "field_override": args.field,
        "success_definition": "At least one expected relevant ayah appears in the first five results.",
        "revisions": revisions,
        "searchnorm_blob_hashes": norm_hashes,
        "index": info,
        "metrics": metrics,
        "comparisons": comparisons,
        "runs": [
            {
                "id": case["id"],
                "query": case["query"],
                "field": case["field"],
                "expected": sorted(anchors(case)),
                "rankings": runs[case["id"]],
            }
            for case in cases
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({
        "fixture": fixture.name,
        "sha256": fixture_hash,
        "all": {name: values["all"] for name, values in metrics.items()},
        "surah_arabic": {name: values.get("surah_arabic") for name, values in metrics.items()},
        "commentary_fields": {
            name: {key: value for key, value in values.items() if key in ("field=ai", "field=en_tafsir")}
            for name, values in metrics.items()
        },
        "comparisons": {
            pair: {key: value for key, value in result["groups"].items() if key in ("all", "surah_arabic")}
            for pair, result in comparisons.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
