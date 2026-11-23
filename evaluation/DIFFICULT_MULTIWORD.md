# Additional multi-keyword diagnostics

This supplementary set has 79 model-authored or mechanically selected cases. The expected verses were checked against the local English or Arabic text. References are relevance anchors and do not exhaust all valid results. Independent review is pending.

## Leaderboard

The table reports queries with a labeled anchor in the first five results. Each implementation searched the same local SQLite index and field scope.

| Query type | Cases | Deploy | PR #1 | Mixed-script branch | Surah + Arabic candidate |
| --- | ---: | ---: | ---: | ---: | ---: |
| All | 79 | 37 | 40 | 40 | 62 |
| Distant terms | 14 | 14 | 14 | 14 | 14 |
| Paraphrases and implied names | 32 | 18 | 21 | 21 | 21 |
| Surah name plus Arabic | 33 | 5 | 5 | 5 | 27 |
| Newly selected surah and prefix cases | 25 | 3 | 3 | 3 | 22 |

On the 33 surah plus Arabic cases, top-one coverage increased from 2 to 27. The 25 newly selected cases use a mechanically chosen four-character prefix unique within each selected surah. They exercise the implemented search pattern, so their results should not be treated as representative of natural user queries.

On the earlier 54 cases, top-five coverage increased from 37 to 40 and top-one coverage increased from 26 to 29. None of the 54 previously top-five or top-one anchor hits was lost. For the existing 1,566-case challenge, only CH0063, CH0064 and CH0398 meet the new tier's entry conditions, and their top-ten rankings were identical to the mixed-script branch. Other cases do not enter the new tier. This checks the known fixtures and does not establish that every possible query is regression-free.

The requested `luqman حمل` returns 31:14 first. Limitations remain for Arabic proclitics such as `yusuf قميص`, alternate transliterations such as `maidah`, and combining a surah name, Arabic and an additional English term. Such failures are retained in the fixture.

Comparison revisions are deploy d9cff5d, PR #1 928ff86, mixed-script branch 78b9e90, and candidate 7271fdb. The JSON records top-ten rankings, revision hashes and fixture hash. Run `python evaluation/run_difficult_multiword.py --repo ../aayatun-research` from this checkout using the existing indexed corpus.

The set is small, constructed with knowledge of the corpus, and contains repeated ayat and related query families. It cannot establish statistically reliable population performance. It remains separate from the frozen challenger v2 totals. OpenSearch was offline for this trial, and the live deployment was not checked.
