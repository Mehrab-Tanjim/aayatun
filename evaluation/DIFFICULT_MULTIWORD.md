# Additional multi-keyword diagnostics

This supplementary set has 54 model-authored cases. The expected verses were checked against the local English or Arabic text. The supplied references are relevance anchors and do not exhaust all valid results. Independent review is pending.

## Leaderboard

The table reports the number of queries with a labeled anchor among the first five results. Each implementation searched the same local SQLite index with the case's specified field scope.

| Query type | Cases | Deploy | PR #1 | Mixed-script branch |
| --- | ---: | ---: | ---: | ---: |
| All | 54 | 34 (63.0%) | 37 (68.5%) | 37 (68.5%) |
| Distant terms | 14 | 14 (100%) | 14 (100%) | 14 (100%) |
| Paraphrases and implied names | 32 | 18 (56.3%) | 21 (65.6%) | 21 (65.6%) |
| Surah name plus Arabic | 8 | 2 (25.0%) | 2 (25.0%) | 2 (25.0%) |

For the same four groups, top-one results were 29/54, 14/14, 13/32 and 2/8 for deploy, and 26/54, 14/14, 10/32 and 2/8 for both PR #1 and the mixed-script branch. On paraphrases, PR #1 improved top-five coverage while reducing top-one coverage in this sample. Distance alone did not make the literal cases difficult.

The user-requested `luqman حمل` and `luqman حملت` both placed 31:14 outside the top ten in all three versions. The input joins the name of a surah with the beginning of an inflected Arabic word. These measurements were taken locally. The live deployment was not checked.

The comparisons use deploy d9cff5d, PR #1 928ff86 and mixed-script branch 78b9e90. Per-query top-ten rankings, full revision hashes and the fixture hash are in `difficult_multiword_results.json`. Run `python evaluation/run_difficult_multiword.py --repo ../aayatun-research` from this checkout using the existing indexed corpus.

These queries were constructed with knowledge of the corpus, several reuse the same ayat or intents, and they are too few for reliable population-level or statistical claims. This supplementary set has not been included in the frozen challenger v2 totals. OpenSearch was offline during this run, so no OpenSearch score is reported for these 54 queries.
