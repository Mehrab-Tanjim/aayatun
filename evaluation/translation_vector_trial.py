"""Compare cached multilingual E5 with the recorded lexical rankings, translation field only."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer


HERE = Path(__file__).resolve().parent
MODEL = "intfloat/multilingual-e5-small"
REVISION = "c007d7ef6fd86656326059b28395a7a03a7c5846"


@torch.inference_mode()
def encode(texts, tokenizer, model, device):
    # Batch similar lengths to reduce padding, then restore the original order.
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    batches = []
    for start in range(0, len(order), 32):
        batch = [texts[i] for i in order[start:start + 32]]
        inputs = tokenizer(batch, padding=True, truncation=True, max_length=512,
                           return_tensors="pt").to(device)
        hidden = model(**inputs).last_hidden_state.float()
        mask = inputs.attention_mask.unsqueeze(-1)
        pooled = (hidden * mask).sum(1) / mask.sum(1)
        batches.append(torch.nn.functional.normalize(pooled).cpu().numpy())
    return np.concatenate(batches)[np.argsort(order)]


def fuse(lexical, vector):
    scores = {}
    for ranking in (lexical, vector):
        for rank, ref in enumerate(ranking, 1):
            scores[ref] = scores.get(ref, 0) + 1 / (60 + rank)
    # Stable lexical-first tie break for equal reciprocal ranks.
    return sorted(scores, key=scores.get, reverse=True)[:10]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE / "challenge_manifest.json").read_text())
    fixture = (HERE / "challenge_v2.jsonl").read_bytes()
    assert hashlib.sha256(fixture).hexdigest() == manifest["query_sha256"]
    cases = [json.loads(line) for line in fixture.splitlines()]
    cases = [c for c in cases if c["field"] == "translation"]
    with sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro", uri=True) as db:
        rows = db.execute("SELECT surah, verse, en FROM docs ORDER BY surah, verse").fetchall()
    corpus = {f"{surah}:{verse}": en for surah, verse, en in rows}
    corpus_hash = hashlib.sha256(json.dumps(corpus, sort_keys=True).encode()).hexdigest()
    assert len(corpus) == 6236 and corpus_hash == manifest["corpus_english_sha256"]
    refs = list(corpus)
    old = json.loads((HERE / "deploy_comparison.json").read_text(encoding="utf8"))
    previous = json.loads((HERE / "challenge_results.json").read_text(encoding="utf8"))
    assert old["dataset_sha256"] == previous["dataset_sha256"] == manifest["query_sha256"]
    deploy = {r["id"]: r["results"] for r in old["deploy_rankings"]}
    pr = {r["id"]: r["runs"]["sqlite_pr"] for r in previous["runs"]}
    device = "cuda" if torch.cuda.is_available() else "cpu"
    options = dict(revision=REVISION, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, **options)
    model = AutoModel.from_pretrained(MODEL, **options).eval().to(device)
    print(f"Encoding {len(refs)} verses and {len(cases)} queries on {device}", flush=True)
    passages = encode(["passage: " + t for t in corpus.values()], tokenizer, model, device)
    queries = encode(["query: " + c["query"] for c in cases], tokenizer, model, device)
    rankings = {}
    for case, query in zip(cases, queries):
        key = case["id"]
        neighbors = np.argsort(-(passages @ query), kind="stable")[:10]
        vector = [refs[i] for i in neighbors]
        rankings[key] = {"deploy": deploy[key], "pr": pr[key], "vector": vector,
                         "hybrid": fuse(deploy[key], vector)}
    report = {"model": MODEL, "revision": REVISION, "dataset_sha256": manifest["query_sha256"],
              "corpus_english_sha256": corpus_hash, "device": device, "torch": str(torch.__version__),
              "rankings": rankings}
    args.output.write_text(json.dumps(report, ensure_ascii=False), encoding="utf8")


if __name__ == "__main__":
    main()
