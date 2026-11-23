"""Compare pinned SQLite PR retrieval with OpenSearch lexical and phrase boost."""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import random
from statistics import mean
import subprocess
import sys
import time
import types
import urllib.request

HERE=Path(__file__).resolve().parent
FIELDS={"ayah":["ar"],"translation":["en"],"bn_tafsir":["bn_tafsir"],"en_tafsir":["en_tafsir"],"ai":["ai"],"all":["ar","en","bn_tafsir","en_tafsir","ai","surah_name"]}


def call(path, data, content_type="application/json"):
    req=urllib.request.Request("http://127.0.0.1:19200"+path,data=data.encode(),headers={"Content-Type":content_type})
    with urllib.request.urlopen(req,timeout=120) as response:
        return json.load(response)


def rank(case, refs):
    return next((i for i,r in enumerate(refs,1) if case["judgments"].get(r)==2),0)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--saved-runs", action="store_true")
    args=p.parse_args()
    repo=args.repo.resolve()
    cases=[json.loads(l) for l in (HERE/"challenge_v2.jsonl").read_text(encoding="utf8").splitlines()]
    manifest=json.loads((HERE/"challenge_manifest.json").read_text())
    assert hashlib.sha256((HERE/"challenge_v2.jsonl").read_bytes()).hexdigest()==manifest["query_sha256"]
    if args.saved_runs:
        previous=json.loads((HERE/"challenge_results.json").read_text(encoding="utf8"))
        runs={r["id"]:r["runs"] for r in previous["runs"]}
        assert set(runs)=={c["id"] for c in cases}
    else:
        # Fixed phrase weight chosen before observing this benchmark.
        runs={c["id"]:{} for c in cases}
        for mode in ("os_lexical","os_phrase"):
            for start in range(0,len(cases),100):
                batch=cases[start:start+100]
                lines=[]
                for c in batch:
                    fields=FIELDS[c["field"]]
                    text=c["query"].strip('"')
                    base={"multi_match":{"query":text,"fields":fields}}
                    query=base if mode=="os_lexical" else {"bool":{"must":[base],"should":[{"multi_match":{"query":text,"fields":fields,"type":"phrase","boost":3}}]}}
                    lines.extend([json.dumps({"index":"aayatun-eval-normalized"}),json.dumps({"size":10,"_source":False,"query":query})])
                response=call("/_msearch","\n".join(lines)+"\n","application/x-ndjson")
                for c,result in zip(batch,response["responses"]):
                    if "error" in result:raise RuntimeError(result["error"])
                    runs[c["id"]][mode]=[h["_id"] for h in result["hits"]["hits"]]
            print(mode,"complete",flush=True)
        os.chdir(repo)
        sys.path.insert(0,str(repo))
        engine=types.ModuleType("pinned_search")
        source=subprocess.check_output(["git","show","d39f74c:searchtool.py"]).decode("utf8")
        exec(compile(source,"d39f74c:searchtool.py","exec"),engine.__dict__)
        engine._load_vocab()
        engine._load_bk_tree()
        for i,c in enumerate(cases):
            hits,_=engine.index_search(c["query"],10,field=c["field"])
            runs[c["id"]]["sqlite_pr"]=[f"{h['surah']}:{h['verse']}" for h in hits]
            if i%200==0:print("SQLite",i,flush=True)
    groups=defaultdict(list)
    for c in cases:
        if c["judgments"]:
            groups["all"].append(c)
            groups["intent="+c["intent"]].append(c)
            groups["provenance="+c["provenance"]].append(c)
            groups["split="+c["split"]].append(c)
    summary={}
    for label,subset in groups.items():
        summary[label]={}
        for mode in ("sqlite_pr","os_lexical","os_phrase"):
            ranks=[rank(c,runs[c["id"]][mode]) for c in subset]
            summary[label][mode]={"n":len(subset),"hit_at_5":mean(0<r<=5 for r in ranks),"mrr_at_10":mean(1/r if r else 0 for r in ranks)}
    # Family-clustered bootstrap of paired hit@5 differences.
    rng=random.Random(20261122)
    intervals={}
    for label,subset in groups.items():
        cluster=defaultdict(list)
        for c in subset:
            diff=int(0<rank(c,runs[c["id"]]["os_phrase"])<=5)-int(0<rank(c,runs[c["id"]]["os_lexical"])<=5)
            cluster[c["family"]].append(diff)
        stats=[(sum(v),len(v)) for v in cluster.values()]
        estimates=[]
        for _ in range(2000):
            sampled=rng.choices(stats,k=len(stats))
            estimates.append(sum(v for v,n in sampled)/sum(n for v,n in sampled))
        estimates.sort()
        intervals[label]={"families":len(stats),"delta":sum(v for v,n in stats)/sum(n for v,n in stats),"bootstrap_95_percent":[estimates[49],estimates[1949]]}
    report={"sqlite_revision":"d39f74c","dataset_sha256":manifest["query_sha256"],
            "phrase_boost":3,"metrics":summary,"phrase_vs_lexical_hit5":intervals,
            "runs":[{"id":c["id"],"runs":runs[c["id"]]} for c in cases]}
    (HERE/"challenge_results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(summary["all"]),flush=True)


if __name__=="__main__":
    main()
