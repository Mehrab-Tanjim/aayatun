"""Exploratory question-index pilot; this is not a held-out evaluation."""
import json
import sqlite3
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

HERE = Path(__file__).resolve().parent
APP = HERE.parent.parent / "aayatun-research"
MODEL = "intfloat/multilingual-e5-small"
REVISION = "c007d7ef6fd86656326059b28395a7a03a7c5846"

# Manually written for a small set of familiar verses after earlier benchmark work.
QUESTIONS = {
    "1:1": "How does the Quran begin in the name of God?",
    "2:255": "What does the Quran say about God's knowledge and authority?",
    "2:286": "Does God ask a person to bear more than they can manage?",
    "4:36": "How should people treat their parents and neighbours?",
    "5:32": "What does the Quran say about saving a human life?",
    "17:23": "How should children speak to their parents?",
    "24:27": "What should people do before entering another person's home?",
    "31:14": "What hardship does a mother endure carrying her child?",
    "49:13": "What makes people from different nations equal before God?",
    "94:5": "Is there relief alongside hardship?",
}


def main():
    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, local_files_only=True)
    model = AutoModel.from_pretrained(MODEL, revision=REVISION, local_files_only=True).eval()

    def encode(texts, prefix):
        result = []
        with torch.inference_mode():
            for start in range(0, len(texts), 16):
                tokens = tokenizer([prefix + text for text in texts[start:start + 16]],
                                   padding=True, truncation=True, max_length=512, return_tensors="pt")
                hidden = model(**tokens).last_hidden_state
                mask = tokens.attention_mask.unsqueeze(-1)
                pooled = (hidden * mask).sum(1) / mask.sum(1)
                result.append(torch.nn.functional.normalize(pooled, dim=1).numpy())
        return np.concatenate(result)

    index = APP / "static" / "meaning"
    manifest = json.loads((index / "index.json").read_text(encoding="utf8"))
    vectors = np.fromfile(index / manifest["file"], dtype=np.int8).reshape(-1, 384).astype(np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    refs = manifest["refs"]
    with sqlite3.connect(APP / "db" / "search.db") as conn:
        texts = {f"{s}:{v}": text for s, v, text in conn.execute("select surah, verse, en from docs")}
    assert all(ref in texts for ref in QUESTIONS)
    cases = [json.loads(line) for line in (HERE / "semantic_followup.jsonl").read_text(encoding="utf8").splitlines()]
    query_vectors = encode([row["query"] for row in cases], "query: ")
    additions = encode(list(QUESTIONS.values()), "passage: ")
    runs = {}
    for row, vector in zip(cases, query_vectors):
        baseline = vectors @ vector
        expanded = baseline.copy()
        for ref, score in zip(QUESTIONS, additions @ vector):
            position = refs.index(ref)
            expanded[position] = max(expanded[position], score)
        runs[row["id"]] = {
            "baseline": [refs[i] for i in np.argsort(-baseline)[:10]],
            "expanded": [refs[i] for i in np.argsort(-expanded)[:10]],
        }
    output = {"model": MODEL, "revision": REVISION, "questions": QUESTIONS, "runs": runs}
    (HERE / "question_index_pilot_results.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    for label in ("baseline", "expanded"):
        print(label, sum(bool(set(row["expected"]) & set(runs[row["id"]][label][:5])) for row in cases), "/", len(cases))


if __name__ == "__main__":
    main()
