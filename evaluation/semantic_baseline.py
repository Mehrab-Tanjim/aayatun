"""Measure keyword search at the exact head of Onix PR #1."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent / "aayatun-research"
REVISION = "bc755b9d2808f8da743494e5a7f516c3f0fcc6e2"


def cases_and_hashes():
    fixtures = {}
    cases = []
    for filename in ("challenge_v2.jsonl", "semantic_followup.jsonl"):
        data = (HERE / filename).read_bytes()
        fixtures[filename] = hashlib.sha256(data).hexdigest()
        for line in data.splitlines():
            case = json.loads(line)
            if filename == "challenge_v2.jsonl":
                if case["intent"] != "semantic":
                    continue
                case["expected"] = [r for r, grade in case["judgments"].items() if grade == 2]
                if not case["expected"]:
                    continue
            else:
                case["field"] = "translation"
            cases.append(case)
    return cases, fixtures


def main():
    os.chdir(REPO)
    sys.path.insert(0, str(REPO))
    engine = types.ModuleType("baseline")
    source = subprocess.check_output(["git", "show", f"{REVISION}:searchtool.py"])
    exec(compile(source, REVISION, "exec"), engine.__dict__)
    engine._load_vocab()
    engine._load_bk_tree()
    cases, hashes = cases_and_hashes()
    runs = {}
    for case in cases:
        hits, _ = engine.index_search(case["query"], 10, field=case["field"])
        refs = [f"{hit['surah']}:{hit['verse']}" for hit in hits]
        runs[case["id"]] = refs
    output = {"revision": REVISION, "fixtures": hashes, "runs": runs}
    (HERE / "semantic_baseline_results.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf8")
    for name, subset in (
        ("original (all fields)", [c for c in cases if c["id"].startswith("CH")]),
        ("original English translations", [c for c in cases if c["id"].startswith("CH")
         and c["field"] == "translation" and c["language"] == "en"]),
        ("new English", [c for c in cases if c["id"].startswith("SF") and c["language"] == "en"]),
        ("new multilingual", [c for c in cases if c["id"].startswith("SF") and c["language"] != "en"]),
    ):
        count = sum(bool(set(runs[c["id"]][:5]) & set(c["expected"])) for c in subset)
        print(name, count, "/", len(subset))


if __name__ == "__main__":
    main()
