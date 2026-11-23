# Challenger v2 comparison results

Anchor Hit@5 is the fraction of answerable questions with a supplied grade-2 reference in the first five. All engines used the same frozen questions and scopes. SQLite is pinned to the upstream PR revision 928ff86. OpenSearch 3.10.0 used the same existing normalized index in both runs. English and Arabic source text were verified equal for all 6,236 IDs.

| Slice | Cases | SQLite PR | OpenSearch lexical | OpenSearch phrase boost |
|---|---:|---:|---:|---:|
| all | 1547 | 86.4% | 71.4% | 77.5% |
| intent=single | 203 | 100.0% | 84.2% | 84.2% |
| intent=multi | 607 | 92.8% | 83.2% | 85.3% |
| intent=phrase | 519 | 97.3% | 71.1% | 86.5% |
| intent=semantic | 185 | 21.6% | 21.6% | 21.6% |
| intent=ambiguous | 12 | 75.0% | 41.7% | 41.7% |
| provenance=automatic_known_item | 1150 | 96.0% | 77.2% | 85.2% |
| provenance=model_authored | 209 | 76.6% | 71.8% | 71.8% |
| provenance=model_authored_cross_language | 90 | 1.1% | 0.0% | 0.0% |
| split=frozen_public_test | 252 | 96.8% | 77.8% | 86.1% |

Phrase boost increased aggregate Hit@5 by 6.08 percentage points. The family-clustered 2,000-resample 95% interval is [4.76, 7.50] percentage points. The frozen public test increase is 8.33 points with interval [4.88, 11.90]. These intervals describe this constructed dataset. The gain is concentrated in extracted wording cases. Authored and cross-language slices showed zero Hit@5 gain. Multiple slices are exploratory.

The shuffled review pool contains 4846 candidate query–verse pairs from the authored and legacy diagnostic queries. Human grades are null. The evidence file supports supplied anchors. Additional unlisted candidates require judgment before precision, exhaustive recall or nDCG claims.

sqlite_pr returned results for 12/18 no-answer cases. This measures retrieval behavior, not whether an answer was asserted.
os_lexical returned results for 10/18 no-answer cases. This measures retrieval behavior, not whether an answer was asserted.
os_phrase returned results for 10/18 no-answer cases. This measures retrieval behavior, not whether an answer was asserted.

See RELEVANCE_AUDIT.md for the subsequent pair-by-pair label audit and corrections.

The direct-answer scores exclude the 18 negative controls and one identity question with only contextual evidence (CH0206).

For the separate 54-query difficult multiword diagnostic and its deploy, PR #1 and mixed-script leaderboard, see [DIFFICULT_MULTIWORD.md](DIFFICULT_MULTIWORD.md). These cases are excluded from the frozen challenger totals above.
