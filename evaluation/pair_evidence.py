"""Evidence and decisions for the second model relevance review."""
from pathlib import Path
import json
import re

HERE = Path(__file__).resolve().parent
VERSE_REASONS = json.loads((HERE / "verse_reasons.json").read_text(encoding="utf8"))
ADDITIONS = {
    "CH0010": ["16:8"], "CH0011": ["22:23", "35:33", "52:24", "55:22"],
    "CH0055": ["2:83"], "CH0241": ["79:16"], "CH0395": ["29:15"],
}

CONTEXT = {
    ("CH0071", "17:24"): "The verse gives a prayer for one's parents. The instruction about speech addressed to aging parents is in 17:23.",
    ("CH0091", "17:24"): "This is a prayer addressed to Allah for one's parents. The Bengali question asks how to speak to the parents themselves, answered in 17:23.",
    ("CH0073", "55:19"): "Introduces the two seas meeting. Only the following verse supplies the barrier requested in the question.",
    ("CH0079", "20:27"): "The request is to loosen the tongue. Its purpose, being understood, appears explicitly in 20:28.",
    ("CH0278", "83:1"): "Announces a warning against short measure; it takes 83:2–3 to describe both sides of the double standard.",
    ("CH0206", "9:118"): "Describes the distress of the three who were left behind but does not identify the three individuals by name.",
}
NEGATIVES = {
    "CH0099":"Router configuration is a modern technical procedure outside the indexed religious sources.",
    "CH0100":"97:1–3 describes the Night of Decree without assigning a Gregorian date in 2032.",
    "CH0101":"27:18 identifies the speaker as an ant but gives it no personal name.",
    "CH0102":"18:13 describes the youths collectively without supplying their names.",
    "CH0103":"Recovering an email password requires account-provider instructions.",
    "CH0104":"Replacing a phone battery requires hardware instructions.",
    "CH0105":"12:15 places Joseph in the well without specifying his precise age.",
    "CH0106":"11:37 commands building the ark without stating its length in metres.",
    "CH0107":"The question asks for a hadith citation; the selected field contains the Quran translation.",
    "CH0108":"The input has no identifiable request or Quranic reference.",
}

def lexical_support(c, text):
    """Use source offsets so each explanation can be checked against the original spelling."""
    query = c["query"].strip('"')
    pattern = r"[a-zA-Z]+"
    tokens = list(re.finditer(pattern, text))
    values = [m.group().lower() for m in tokens]
    wanted = re.findall(pattern, query.lower())
    if c["intent"] == "phrase":
        start = next(i for i in range(len(tokens)) if values[i:i+len(wanted)] == wanted)
        first, last = tokens[start], tokens[start+len(wanted)-1]
        fragment = text[first.start():last.end()]
        embedded = bool(re.search(r"[A-Za-z]'$", text[:first.start()]) or re.match(r"'[A-Za-z]", text[last.end():]))
        reason = f'The translation contains “{fragment}” in the requested word order.'
        if embedded:
            reason += " A query boundary cuts through an apostrophe-containing source word, so this only verifies the benchmark tokenizer's match."
        return reason, [fragment], embedded
    matches = [tokens[values.index(w)] for w in wanted]
    fragments = [text[max(0,m.start()-20):m.end()+25] for m in matches]
    reason = (f'The translation contains the word “{query}”.' if len(wanted)==1
              else f'The same English ayah contains all requested words ({", ".join(wanted)}).')
    return reason, fragments, False


def explain(c, ref, corpus):
    text = corpus[ref]
    if c["provenance"] == "automatic_known_item":
        reason, fragments, embedded = lexical_support(c, text["en"])
        return reason, {"translation": fragments}, embedded
    if c["id"] == "CH0029":
        reason = "This occurrence of the refrain asks which favors of the Lord the addressees would deny."
    else:
        reason = VERSE_REASONS[ref]
    reason = CONTEXT.get((c["id"],ref), reason)
    fields = {"ayah":["ar"],"translation":["en"],"bn_tafsir":["bn"]}.get(c["field"],["en","ar"])
    if c["field"]=="all" and c["language"]=="mixed" and re.search(r"[\u0980-\u09ff]",c["query"]):
        fields = [*fields,"bn"]
    names={"en":"translation","ar":"ayah","bn":"bn_tafsir"}
    evidence={names[f]:[text[f] if f!="bn" else text[f][:1000]] for f in fields}
    return reason, evidence, False
