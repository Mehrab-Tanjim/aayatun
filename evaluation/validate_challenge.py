"""Validate references, evidence, labels, duplicate queries and split isolation."""
from collections import Counter
import json
from pathlib import Path
import re
import sqlite3

HERE=Path(__file__).resolve().parent


def validate():
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
    return cases


if __name__=="__main__":
    validate()
