"""Evaluate Onix deploy search against saved challenger rankings."""
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import types
from collections import defaultdict
from statistics import mean

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent / "aayatun-research"
BASE = "d9cff5d3f21dc11423465893fb1839dd6c9251c0"


def rank(case, refs):
    return next((i for i, ref in enumerate(refs, 1) if case["judgments"].get(ref) == 2), 0)


def main():
    cases = [json.loads(line) for line in (HERE / "challenge_v2.jsonl").read_text(encoding="utf8").splitlines()]
    previous = json.loads((HERE / "challenge_results.json").read_text(encoding="utf8"))
    manifest = json.loads((HERE / "challenge_manifest.json").read_text(encoding="utf8"))
    assert previous["dataset_sha256"] == manifest["query_sha256"]
    saved = {row["id"]: row["runs"] for row in previous["runs"]}
    os.chdir(REPO)
    sys.path.insert(0, str(REPO))
    assert not subprocess.check_output(["git", "diff", BASE, "928ff86", "--", "searchnorm.py"])
    engine = types.ModuleType("deploy_search")
    code = subprocess.check_output(["git", "show", BASE + ":searchtool.py"]).decode("utf8")
    exec(compile(code, BASE + ":searchtool.py", "exec"), engine.__dict__)
    engine._load_vocab()
    engine._load_bk_tree()
    runs = {}
    for i, case in enumerate(cases):
        hits, _ = engine.index_search(case["query"], 10, field=case["field"])
        runs[case["id"]] = [f"{h['surah']}:{h['verse']}" for h in hits]
        if i % 200 == 0:
            print(f"Deploy {i}/{len(cases)}", flush=True)
    modes = ["deploy", "sqlite_pr", "os_lexical", "os_phrase"]
    def result(c,mode):
        return runs[c["id"]] if mode == "deploy" else saved[c["id"]][mode]
    groups = defaultdict(list)
    for c in cases:
        if 2 not in c["judgments"].values():
            continue
        groups["all"].append(c)
        groups["intent=" + c["intent"]].append(c)
        groups["provenance=" + c["provenance"]].append(c)
        groups["split=" + c["split"]].append(c)
    metrics = {}
    intervals = {}
    rng = random.Random(20261122)
    for label, subset in groups.items():
        metrics[label] = {}
        for mode in modes:
            ranks = [rank(c,result(c,mode)) for c in subset]
            metrics[label][mode] = {"n": len(subset), "hit_at_5": mean(0 < r <= 5 for r in ranks),
                                    "mrr_at_10": mean(1 / r if r else 0 for r in ranks)}
        clusters = defaultdict(list)
        for c in subset:
            clusters[c["family"]].append(int(0 < rank(c,result(c,"sqlite_pr")) <= 5) -
                                         int(0 < rank(c,result(c,"deploy")) <= 5))
        values = list(clusters.values())
        bootstrap = []
        for _ in range(3000):
            sample = rng.choices(values, k=len(values))
            bootstrap.append(sum(map(sum,sample)) / sum(map(len,sample)))
        bootstrap.sort()
        intervals[label] = {"families": len(values), "difference": sum(map(sum,values))/sum(map(len,values)),
                            "ci_95": [bootstrap[75],bootstrap[2924]]}
    report = {"deploy_revision": BASE, "dataset_sha256": manifest["query_sha256"], "metrics": metrics,
              "pr_minus_deploy_hit5": intervals,
              "deploy_rankings": [{"id":c["id"],"results":runs[c["id"]]} for c in cases]}
    (HERE / "deploy_comparison.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    for label in ("all","intent=single","intent=multi","intent=phrase","intent=semantic","provenance=model_authored","provenance=automatic_known_item","split=frozen_public_test"):
        print(label, metrics[label], intervals[label], flush=True)


if __name__ == "__main__":
    main()
