"""Run a local OpenSearch lexical comparison; requires a loopback test cluster."""
import json
import os
from pathlib import Path
import sys
import urllib.request
from statistics import mean

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent / "aayatun-research"
BASE = "http://127.0.0.1:19200"
INDEX = "aayatun-eval-normalized" if "--normalized-arabic" in sys.argv else "aayatun-eval"


def request(method, path, body=None, content_type="application/json"):
    data = None if body is None else body.encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": content_type})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def main():
    os.chdir(REPO)
    sys.path.insert(0, str(REPO))
    import build_search
    fields = {"ar": "arabic", "en": "english", "bn_tafsir": "bengali",
              "en_tafsir": "english", "ai": "english", "surah_name": "english"}
    settings = {"number_of_shards": 1, "number_of_replicas": 0}
    if "--normalized-arabic" in sys.argv:
        fields["ar"] = "quran_arabic"
        settings["analysis"] = {
            "char_filter": {"alef_wasla": {"type": "mapping", "mappings": ["ٱ => ا"]}},
            "analyzer": {"quran_arabic": {
                "tokenizer": "standard", "char_filter": ["alef_wasla"],
                "filter": ["lowercase", "decimal_digit", "arabic_normalization", "arabic_stem"]
            }}
        }
    mapping = {"settings": settings,
               "mappings": {"properties": {key: {"type": "text", "analyzer": analyzer}
                                            for key, analyzer in fields.items()}}}
    request("PUT", "/" + INDEX, json.dumps(mapping))
    lines = []
    for row in build_search.load_rows():
        ref = f"{row['surah']}:{row['verse']}"
        doc = {k: row.get(k, "") for k in fields}
        doc["ar"] = row["ar_raw"]
        lines.extend((json.dumps({"index": {"_index": INDEX, "_id": ref}}),
                      json.dumps(doc, ensure_ascii=False)))
    result = request("POST", "/_bulk?refresh=true", "\n".join(lines) + "\n",
                     "application/x-ndjson")
    if result["errors"]:
        raise RuntimeError("Bulk indexing failed")
    print("Indexed", len(lines) // 2, "verses", flush=True)
    fieldmap = {"ayah": ["ar"], "translation": ["en"], "bn_tafsir": ["bn_tafsir"],
                "en_tafsir": ["en_tafsir"], "ai": ["ai"], "all": list(fields)}
    cases = [json.loads(line) for line in (ROOT / "queries.jsonl").read_text(
        encoding="utf-8").splitlines()]
    out = []
    for case in cases:
        query = {"size": 10, "query": {"multi_match": {
            "query": case["query"], "fields": fieldmap[case["field"]]}}}
        hits = request("POST", "/" + INDEX + "/_search", json.dumps(query))["hits"]["hits"]
        refs = [hit["_id"] for hit in hits]
        anchors = {ref for ref, grade in case["judgments"].items() if grade == 2}
        rank = next((i for i, ref in enumerate(refs, 1) if ref in anchors), 0)
        out.append({"id": case["id"], "intent": case["intent"], "query": case["query"],
                    "results": refs, "rank": rank})
    filename = "opensearch-normalized-trial.json" if "--normalized-arabic" in sys.argv else "opensearch-trial.json"
    (ROOT / filename).write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    multi = [x for x in out if x["intent"] == "multi"]
    print("Multi keyword hit@5", sum(0 < x["rank"] <= 5 for x in multi),
          "/", len(multi), "MRR", round(mean(1/x["rank"] if x["rank"] else 0
                                              for x in multi), 3))


if __name__ == "__main__":
    main()
