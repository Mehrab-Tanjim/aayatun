"""Validate references, evidence, labels, duplicate queries and split isolation."""
import argparse
import json
from pathlib import Path
import re
import sqlite3

HERE=Path(__file__).resolve().parent


def validate(repo=None):
    cases=[json.loads(l) for l in (HERE/"challenge_v2.jsonl").read_text(encoding="utf8").splitlines()]
    evidence=json.loads((HERE/"challenge_evidence.json").read_text(encoding="utf8"))
    seen=set()
    families={}
    refs={}
    for c in cases:
        assert c["query"].strip()
        key=(c["query"].casefold().strip(),c["field"])
        assert key not in seen
        seen.add(key)
        assert families.setdefault(c["family"],c["split"])==c["split"]
        assert (c["intent"]=="no_answer")== (not c["judgments"])
        for ref,grade in c["judgments"].items():
            assert ref in evidence and grade in (1,2)
            assert refs.setdefault(ref,c["split"])==c["split"]
        assert c["rationale"] and c["provenance"]
    assert all(sum(c["intent"]=="multi" and c["language"]==lang for c in cases)>=20 for lang in ("en","ar","bn"))
    assert len(cases)>=1500 and len(families)>=300
    print(f"Validated {len(cases)} queries, {len(families)} families and {len(refs)} labeled verses.")
    # Evidence fragments are audit aids, not a substitute for semantic judgment.
    errors=[]
    for c in cases:
        f=c.get("evidence_fragment")
        if f and not any(f.casefold() in evidence[r]["english"].casefold() for r in c["judgments"]):
            errors.append((c["id"],c["query"],f))
    print("Evidence fragments requiring inspection:",errors)
    assert not errors, errors
    pairs={(c["id"], r):(c, grade) for c in cases for r,grade in c["judgments"].items()}
    audit=[json.loads(line) for line in (HERE/"relevance_audit.jsonl").read_text(encoding="utf8").splitlines()]
    assert len(audit)==len(pairs)
    corpus={}
    if repo:
        uri=(repo.resolve()/"db/search.db").as_uri()+"?mode=ro"
        with sqlite3.connect(uri,uri=True) as db:
            corpus={f"{s}:{v}":{"translation":en,"ayah":ar,"bn_tafsir":bn}
                    for s,v,en,ar,bn in db.execute("SELECT surah,verse,en,ar_orig,bn_tafsir FROM docs")}
    for row in audit:
        c,grade=pairs.pop((row["query_id"],row["verse"]))
        assert row["grade"]==grade and row["reason"]==c["verse_rationales"][row["verse"]]
        assert row["query"]==c["query"] and row["scope"]==c["field"]
        assert c["field"]=="all" or set(row["source_evidence"])=={c["field"]}
        assert row["source_evidence"] and row["reason"].strip()
        for field,fragments in row["source_evidence"].items():
            assert fragments and all(fragments)
            if repo:
                assert all(f in corpus[row["verse"]][field] for f in fragments), row["query_id"]
    assert not pairs
    print(f"Verified one rationale and scoped evidence record for each of {len(audit)} labels.")
    return cases


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path)
    validate(parser.parse_args().repo)
