"""Rank the exploratory multiword cases against pinned Aayatun revisions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
REVISIONS = {
    "deploy": "d9cff5d3f21dc11423465893fb1839dd6c9251c0",
    "pr1": "928ff8615c852f4178016ae8673d97d6c66bcb9e",
    "mixed_script": "78b9e909f5484ca7e5edda54841124a521b6e69a",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    fixture = (HERE / "difficult_multiword.jsonl").read_bytes()
    cases = [json.loads(line) for line in fixture.splitlines()]
    assert len({c["id"] for c in cases}) == len(cases)
    assert len({(c["query"].casefold(), c["field"]) for c in cases}) == len(cases)
    os.chdir(repo)
    sys.path.insert(0, str(repo))
    engines = {}
    for name, revision in REVISIONS.items():
        code = subprocess.check_output(["git", "show", revision + ":searchtool.py"]).decode("utf8")
        engine = types.ModuleType(name)
        exec(compile(code, revision + ":searchtool.py", "exec"), engine.__dict__)
        engine._load_vocab()
        engine._load_bk_tree()
        engines[name] = engine
    runs = []
    for case in cases:
        row = {"id": case["id"], "rankings": {}}
        for name, engine in engines.items():
            hits, _ = engine.index_search(case["query"], 10, field=case["field"])
            row["rankings"][name] = [f"{hit['surah']}:{hit['verse']}" for hit in hits]
        runs.append(row)
        print(case["id"], flush=True)
    report = {
        "fixture_sha256": hashlib.sha256(fixture).hexdigest(),
        "revisions": REVISIONS,
        "runs": runs,
    }
    (HERE / "difficult_multiword_results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )


if __name__ == "__main__":
    main()
