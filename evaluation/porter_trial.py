"""Exploratory English stemming trial. Run from anywhere after building db/search.db."""
import json
from pathlib import Path
import re
import sqlite3
import statistics
import sys

folder = Path(__file__).resolve().parent
repo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else folder.parent / "aayatun-research"
report = json.loads((folder / "pr1-multiword.json").read_text(encoding="utf-8"))
db = sqlite3.connect(":memory:")
db.execute("CREATE VIRTUAL TABLE english USING fts5(text, ref UNINDEXED, tokenize='porter unicode61')")
with sqlite3.connect((repo / "db/en_quran.db").as_uri() + "?mode=ro", uri=True) as corpus:
    db.executemany("INSERT INTO english VALUES (?, ?)", (
        (text, f"{s}:{v}") for s, v, text in corpus.execute("SELECT sura,ayah,text FROM verses")
    ))

rows = []
for row in report["queries"]:
    case = row["case"]
    runs = row["runs"]
    pr_hits = runs["pr" if "pr" in runs else "current"]["results"]
    stems = []
    if case["field"] == "translation" and case["language"] == "en":
        tokens = re.findall("[a-z]+", case["query"].lower())
        expr = " AND ".join(f'"{word}"' for word in tokens)
        stems = [ref for (ref,) in db.execute(
            "SELECT ref FROM english WHERE english MATCH ? ORDER BY bm25(english), rowid LIMIT 10", (expr,)
        )]
    trial = list(dict.fromkeys(stems + pr_hits))[:10]
    def rank(refs):
        return next((i for i, ref in enumerate(refs, 1) if case["judgments"].get(ref) == 2), 0)
    rows.append({"id": case["id"], "query": case["query"], "pr_rank": rank(pr_hits),
                 "trial_rank": rank(trial), "trial_top10": trial})
for key in ("pr_rank", "trial_rank"):
    print(key, "hit@5", sum(0 < r[key] <= 5 for r in rows),
          "MRR@10", round(statistics.mean(1/r[key] if r[key] else 0 for r in rows), 3))
for row in rows:
    if row["pr_rank"] != row["trial_rank"]:
        print(row["query"], row["pr_rank"], "->", row["trial_rank"])
(folder / "porter-trial.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
