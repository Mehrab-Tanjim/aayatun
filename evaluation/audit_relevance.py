"""Apply the recorded model relevance review and mechanically verify source anchors."""
import hashlib
import json
from pathlib import Path
import re
from collections import Counter

HERE=Path(__file__).resolve().parent
PARTIAL={
    "CH0074":{"15:92":"States that questioning occurs; the subject is in 15:93.",
              "7:6":"Identifies who is questioned, without specifying the questions."},
    "CH0079":{"20:25":"Opening request for assurance, preceding the speech request.",
              "20:26":"Request for ease, preceding the speech request."}
}
PASSAGES={
    "CH0024":[["55:19","55:20"]],
    "CH0030":[["67:1","67:2"]],
    "CH0073":[["55:19","55:20"],["25:53"]],
    "CH0074":[["102:8"],["15:92","15:93"]],
    "CH0079":[["20:27","20:28"]],
    "CH0237":[["18:71","18:79"]],
    "CH0238":[["18:77","18:82"]],
    "CH0278":[["83:2","83:3"]]
}
NOTES={
    "CH0180":"2:259 locates the story and describes the man; the Quran does not name him. Interpret this as story retrieval. A request for his personal name would be unanswerable in this scope.",
    "CH0206":"9:118 locates the three people's experience but does not name them. Interpret this as story retrieval. A request for personal names would need an additional source.",
    "CH0042":"A quoted phrase plus a keyword. The inserted translation word [his] does not invalidate the quoted fragment.",
    "CH0391":"83:3 supports the trade-measure sense even though the exact Arabic noun الميزان is absent.",
    "CH0223":"16:69 supplies the drink and healing description. Read 16:68 to identify the bees.",
    "CH0246":"21:80 describes armor taught to him. The preceding David/Solomon narrative establishes the referent."
}


def words(s):
    return re.findall(r"[a-z]+",s.lower())


def apply(cases, corpus):
    audit=[]
    for c in cases:
        if c["id"]=="CH0029":
            target=words(corpus["55:13"]["en"])
            c["judgments"]={r:2 for r,t in corpus.items() if words(t["en"])==target}
        for ref,reason in PARTIAL.get(c["id"],{}).items():
            c["judgments"][ref]=1
        if c["id"] in PASSAGES:
            c["acceptable_passage_sets"]=PASSAGES[c["id"]]
        c["relevance_review"]={
            "method":"source_token_check" if c["provenance"]=="automatic_known_item" else "model_semantic_review",
            "status":"source_supported",
            "language_review":"native_speaker_review_pending",
            "notes":NOTES.get(c["id"],"")
        }
        if c["provenance"]=="automatic_known_item":
            if c["intent"]=="phrase":
                phrase=c["query"].strip('"')
                if not any(re.search(r"(?<![A-Za-z'])"+re.escape(phrase)+r"(?![A-Za-z'])",corpus[r]["en"],re.I) for r in c["judgments"]):
                    c["relevance_review"]["notes"]="Extracted phrase has an apostrophe or punctuation boundary mismatch. Source anchor exists, but query naturalness needs review."
                    c["relevance_review"]["status"]="query_quality_review"
            for ref in c["judgments"]:
                q=words(c["query"]); t=words(corpus[ref]["en"])
                assert set(q)<=set(t),(c["id"],ref)
                if c["intent"]=="phrase":
                    assert any(t[i:i+len(q)]==q for i in range(len(t)-len(q)+1))
        for ref,grade in c["judgments"].items():
            audit.append({"query_id":c["id"],"verse":ref,"grade":grade,
                          "method":c["relevance_review"]["method"],
                          "decision":"contextual" if grade==1 else "supported_anchor",
                          "reason":PARTIAL.get(c["id"],{}).get(ref,c["rationale"]),
                          "notes":c["relevance_review"]["notes"]})
        for ref in c["judgments"]:
            assert ref in corpus
    (HERE/"relevance_audit.jsonl").write_text("".join(json.dumps(a,ensure_ascii=False)+"\n" for a in audit),encoding="utf8")
    return audit
