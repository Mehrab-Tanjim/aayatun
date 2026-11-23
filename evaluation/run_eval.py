"""Compare Aayatun search on the same index and produce a blind review pool."""

import argparse
from collections import defaultdict
import importlib
import json
import math
import os
from pathlib import Path
import random
import sqlite3
from statistics import mean
import subprocess
import sys
import time
import types


HERE = Path(__file__).resolve().parent
TOP_K = 10


def read_cases(index):
    cases = [json.loads(line) for line in (HERE / "queries.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    ids = set()
    queries = set()
    groups = {}
    refs = {}
    with sqlite3.connect(f"{index.as_uri()}?mode=ro", uri=True) as db:
        corpus = {f"{s}:{v}" for s, v in db.execute("SELECT sura, ayah FROM verses")}
    for case in cases:
        key = (case["query"].strip().casefold(), case["field"])
        if case["id"] in ids or key in queries or not key[0]:
            raise ValueError(f"Duplicate ID, duplicate query or empty query: {case['id']}")
        ids.add(case["id"])
        queries.add(key)
        split = case["split"]
        group = case["group"]
        if groups.setdefault(group, split) != split:
            raise ValueError(f"Topic family crosses splits: {group}")
        if (case["intent"] == "no_answer") == bool(case["judgments"]):
            raise ValueError(f"Unexpected seed judgments for {case['id']}")
        for ref, grade in case["judgments"].items():
            if ref not in corpus or grade not in (1, 2):
                raise ValueError(f"Invalid reference or grade in {case['id']}: {ref}, {grade}")
            if refs.setdefault(ref, split) != split:
                raise ValueError(f"Verse {ref} crosses splits at {case['id']}")
    return cases


def load_baseline(ref):
    result = subprocess.run(["git", "show", f"{ref}:searchtool.py"], check=True,
                            capture_output=True, text=True, encoding="utf-8")
    baseline = types.ModuleType("eval_baseline")
    exec(compile(result.stdout, f"{ref}:searchtool.py", "exec"), baseline.__dict__)
    return baseline


def run_search(engine, case):
    start = time.perf_counter()
    hits, _ = engine.index_search(case["query"], TOP_K, field=case["field"])
    elapsed = (time.perf_counter() - start) * 1000
    refs = [f"{hit['surah']}:{hit['verse']}" for hit in hits]
    return {"results": refs, "ms": round(elapsed, 3)}


def summarize(rows, engine):
    answerable = [row for row in rows if row["case"]["judgments"]]
    negative = [row for row in rows if not row["case"]["judgments"]]
    ranks = []
    for row in answerable:
        anchors = {ref for ref, grade in row["case"]["judgments"].items() if grade == 2}
        results = row["runs"][engine]["results"]
        ranks.append(next((rank for rank, ref in enumerate(results, 1)
                           if ref in anchors), 0))
    timings = sorted(row["runs"][engine]["ms"] for row in rows)
    return {
        "n": len(rows),
        "answerable": len(answerable),
        "seed_hit_at_5": round(mean(0 < rank <= 5 for rank in ranks), 3) if ranks else None,
        "seed_mrr_at_10": round(mean(1 / rank if rank else 0 for rank in ranks), 3)
        if ranks else None,
        "no_answer_cases": len(negative),
        "no_answer_with_results": sum(bool(row["runs"][engine]["results"]) for row in negative),
        "p95_ms": timings[math.ceil(.95 * len(timings)) - 1],
    }


def make_review_pool(rows):
    pool = []
    for row in rows:
        case = row["case"]
        candidates = sorted(set(case["judgments"]).union(
            *(run["results"] for run in row["runs"].values())))
        random.Random(case["id"]).shuffle(candidates)
        pool.append({
            "id": case["id"], "query": case["query"], "field": case["field"],
            "candidates": [{"verse": ref, "grade": None, "notes": ""} for ref in candidates],
        })
    return pool


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=HERE.parent / "aayatun-research")
    parser.add_argument("--baseline-ref", help="Trusted local Git revision to load")
    parser.add_argument("--split", choices=("dev", "holdout", "all"), default="all")
    parser.add_argument("--intent", choices=("single", "multi", "phrase", "multilingual", "semantic", "no_answer"))
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    parser.add_argument("--pool", type=Path, help="Write candidates for independent review")
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    pool_path = args.pool.resolve() if args.pool else None
    if not (repo / "db/search.db").is_file():
        parser.error("Build db/search.db from the target repo before benchmarking.")
    cases = read_cases(repo / "db/quran.db")
    cases = [case for case in cases if args.split in ("all", case["split"])]
    if args.intent:
        cases = [case for case in cases if case["intent"] == args.intent]
    os.chdir(repo)
    sys.path.insert(0, str(repo))
    engines = {"current": importlib.import_module("searchtool")}
    if args.baseline_ref:
        engines["baseline"] = load_baseline(args.baseline_ref)
    for engine in engines.values():
        engine.index_search("mercy", TOP_K)
        # Initialize lazy typo handling outside measured requests.
        engine._load_vocab()
        engine._load_bk_tree()
    rows = []
    for i, case in enumerate(cases):
        order = list(engines)
        if i % 2:
            order.reverse()
        rows.append({"case": case, "runs": {
            name: run_search(engines[name], case) for name in order
        }})
    slices = defaultdict(list, {"all": rows})
    for row in rows:
        for key in ("split", "intent", "language", "difficulty"):
            slices[f"{key}={row['case'][key]}"].append(row)
    stats = {name: {key: summarize(group, name) for key, group in slices.items()}
             for name in engines}
    report = {
        "baseline_ref": args.baseline_ref,
        "current_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "sqlite_version": sqlite3.sqlite_version, "metrics": stats, "queries": rows,
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if pool_path:
        pool_path.write_text(json.dumps(make_review_pool(rows), ensure_ascii=False, indent=2)
                             + "\n", encoding="utf-8")
    print(json.dumps({name: values["all"] for name, values in stats.items()}, indent=2))


if __name__ == "__main__":
    main()
