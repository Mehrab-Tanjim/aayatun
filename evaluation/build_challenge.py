"""Build a reproducible, corpus-grounded challenge fixture. Uses only stdlib."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import re
import sqlite3

HERE = Path(__file__).resolve().parent


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    with sqlite3.connect(repo / "db/search.db") as db:
        corpus = {f"{s}:{v}": {"en": en, "ar": ar, "bn": bn}
                  for s, v, en, ar, bn in db.execute("SELECT surah,verse,en,ar_orig,bn_tafsir FROM docs")}
    source = json.loads((HERE / "challenge_inputs.json").read_text(encoding="utf8"))
    cases = []
    evidence = {}
    def add(query, intent, language, field, refs, family, rationale, origin, evidence_fragment=None):
        labels = {r: 2 for r in refs}
        for ref in refs:
            assert ref in corpus, ref
            evidence[ref] = {"english": corpus[ref]["en"], "arabic": corpus[ref]["ar"]}
        cases.append(dict(id=f"CH{len(cases)+1:04}", query=query, intent=intent, language=language,
                          field=field, family=family, judgments=labels, rationale=rationale,
                          provenance=origin, review="model_authored_corpus_checked",
                          evidence_fragment=evidence_fragment, split="public_diagnostic"))
    for c in [json.loads(l) for l in (HERE / "queries.jsonl").read_text(encoding="utf8").splitlines()]:
        refs=list(c["judgments"])
        # Repeated refrain equivalents are all valid for a wording search.
        if c["id"] == "AQ029":
            refs=[r for r,t in corpus.items() if t["en"] == corpus["55:13"]["en"]]
        add(c["query"],c["intent"],c["language"],c["field"],refs,c["group"],
            "Retained seed anchors; review scope and neighboring context in the evidence file.",
            "legacy_seed_audited")
    for line in source["tri"].splitlines():
        refs,en,ar,bn,phrase=line.split("|")
        for lang,query,field in [("en",en,"translation"),("ar",ar,"ayah"),("bn",bn,"bn_tafsir")]:
            add(query,"multi",lang,field,refs.split(","),"verse-"+refs.split(",")[0],
                "Keywords describe the cited passage; word forms may differ from the indexed text.",
                "model_authored",phrase)
    for line in source["main"].splitlines():
        refs,intent,query,fragment=line.split("|")
        add(query,intent,"en","translation",refs.split(","),"verse-"+refs.split(",")[0],
            "The cited passage contains the requested event, wording or concept.",
            "model_authored",fragment)
    for line in source["langs"].splitlines():
        lang,debt,greeting=line.split("|")
        for query,ref,reason in [(debt,"2:280","Postpone repayment for a debtor in difficulty."),
                                 (greeting,"4:86","Return a greeting with a better or equal greeting.")]:
            add(query,"semantic",lang,"translation",[ref],"verse-"+ref,reason,
                "model_authored_cross_language")
    for line in source["extra"].splitlines():
        intent,lang,query,reason,field=line.split("|")
        refs=[] if intent=="no_answer" else re.findall(r"(\d+:\d+)",reason)
        add(query,intent,lang,field,refs,"extra-"+query,reason,"model_authored")
    # These automatic cases measure known-item lexical retrieval, with exact target provenance.
    # Exclude authored targets and select once before inspecting results.
    used={r for c in cases for r in c["judgments"]}
    candidates=[r for r,t in corpus.items() if r not in used and len(re.findall(r"[A-Za-z]+",t["en"]))>=14]
    rng=random.Random(20261122)
    rng.shuffle(candidates)
    stop=set("the a an and or of to in for is are was were that this he she it they you we his her their our your with from not but as by on at be have has will shall all who which".split())
    word_refs=defaultdict(list)
    for r,t in corpus.items():
        for w in set(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",t["en"].lower())):
            word_refs[w].append(r)
    for ref in candidates[:500]:
        text=corpus[ref]["en"]
        words=re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",text)
        content=list(dict.fromkeys(w.lower() for w in words if w.lower() not in stop and len(w)>3))
        if len(content)<3:continue
        # Extract phrases only from uninterrupted alphabetic word runs in source.
        runs=re.findall(r"[A-Za-z]+(?: [A-Za-z]+){3,}",text)
        if not runs:continue
        phrase=" ".join(max(runs,key=len).split()[:5])
        equivalent=[r for r,t in corpus.items() if t["en"]==text]
        for intent,query in [("single",min(content,key=lambda w:len(word_refs[w]))),("multi"," ".join(content[:3])),("phrase",'"'+phrase+'"')]:
            if intent=="single" and len(word_refs[query])>2:
                continue
            add(query,intent,"en","translation",word_refs[query] if intent=="single" else equivalent,"sample-"+ref,
                "Retrieve a known source verse from words extracted from its English translation.",
                "automatic_known_item",phrase)
            cases[-1]["review"]="mechanically_verified_source_anchor"
            cases[-1]["split"]="frozen_public_test" if int(ref.split(":")[0])%5==0 else "dev"
    # Merge identical queries within the same scope instead of treating them as independent tasks.
    dedup={}
    for c in cases:
        key=(c["query"].casefold().strip(),c["field"])
        if key in dedup:
            dedup[key]["judgments"].update(c["judgments"])
        else:dedup[key]=c
    cases=list(dedup.values())
    from audit_relevance import apply
    # Union linked references and parallel variants, then keep each component in one split.
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x: parent[x]=find(parent[x])
        return parent[x]
    def union(a,b): parent[find(a)]=find(b)
    for c in cases:
        for ref in c["judgments"]:union(c["family"],"ref-"+ref)
    public={find(c["family"]) for c in cases if c["split"]=="public_diagnostic"}
    for i,c in enumerate(cases,1):
        c["id"]=f"CH{i:04}"
        c["family"]=find(c["family"])
        if c["family"] in public:c["split"]="public_diagnostic"
        elif c["split"]!="public_diagnostic":
            c["split"]="frozen_public_test" if int(hashlib.sha256(c["family"].encode()).hexdigest(),16)%5==0 else "dev"
    apply(cases, corpus)
    for c in cases:
        for ref in c["judgments"]:
            evidence[ref]={"english":corpus[ref]["en"],"arabic":corpus[ref]["ar"]}
    (HERE/"challenge_v2.jsonl").write_text("".join(json.dumps(c,ensure_ascii=False)+"\n" for c in cases),encoding="utf8")
    write_json(HERE/"challenge_evidence.json",evidence)
    manifest={"queries":len(cases),"families":len({c["family"] for c in cases}),
              "languages":dict(Counter(c["language"] for c in cases)),
              "intents":dict(Counter(c["intent"] for c in cases)),
              "provenance":dict(Counter(c["provenance"] for c in cases)),
              "splits":dict(Counter(c["split"] for c in cases)),
              "query_sha256":hashlib.sha256((HERE/"challenge_v2.jsonl").read_bytes()).hexdigest(),
              "corpus_english_sha256":hashlib.sha256(json.dumps({r:t["en"] for r,t in corpus.items()},sort_keys=True).encode()).hexdigest(),
              "limitations":["Model-authored language review, without independent native-speaker review.",
                             "Anchor relevance is incomplete. Unlisted verses remain unjudged.",
                             "Automatic known-item cases are extracted from source and favor lexical systems.",
                             "Cross-language expansion covers two intent families per added language.",
                             "Public frozen test is visible and is not a private holdout."]}
    write_json(HERE/"challenge_manifest.json",manifest)
    print(json.dumps(manifest,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
