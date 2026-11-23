"""Apply the recorded model relevance review and mechanically verify source anchors."""
from pair_evidence import ADDITIONS, CONTEXT, NEGATIVES, explain
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
        for ref in ADDITIONS.get(c["id"], []):
            c["judgments"][ref] = 2
        for ref in c["judgments"]:
            if (c["id"], ref) in CONTEXT:
                c["judgments"][ref] = 1
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
        c["verse_rationales"] = {}
        if not c["judgments"]:
            c["rationale"] = NEGATIVES.get(c["id"], c["rationale"])
            c["relevance_review"]["status"] = "no_direct_answer"
        for ref, grade in c["judgments"].items():
            reason, evidence, embedded = explain(c, ref, corpus)
            reason = PARTIAL.get(c["id"], {}).get(ref, reason)
            if embedded:
                c["relevance_review"]["notes"] = "The tokenizer splits a source word at an apostrophe."
                c["relevance_review"]["status"] = "query_quality_review"
            c["verse_rationales"][ref] = reason
            audit.append({"query_id":c["id"], "query":c["query"], "scope":c["field"],
                          "verse":ref, "grade":grade, "method":c["relevance_review"]["method"],
                          "decision":"contextual" if grade==1 else "supported_anchor",
                          "reason":reason, "source_evidence":evidence,
                          "notes":c["relevance_review"]["notes"]})
        if c["verse_rationales"]:
            c["rationale"] = " ".join(f"{ref} — {reason}" for ref, reason in c["verse_rationales"].items())
    (HERE/"relevance_audit.jsonl").write_text("".join(json.dumps(a,ensure_ascii=False)+"\n" for a in audit),encoding="utf8")
    return audit
