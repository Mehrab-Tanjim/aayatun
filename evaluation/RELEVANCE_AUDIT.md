# Rapid relevance audit

Reviewed every supplied query–ayah label in challenger v2. The original fixture had 1,762 pairs. After adding missing equivalents, it has 1,769 pairs across 1,566 queries.

- 1,253 generated lexical pairs passed source-token verification, including contiguous-token checks for phrases.
- 516 authored or retained pairs received a model semantic relevance review against the source evidence and intended query. These include translated questions and ambiguity examples.
- All 18 no-answer controls were checked for whether the requested detail is present in the scoped Quran text.
- Native-speaker validation remains pending. Model self-review cannot establish independent multilingual agreement.

## Corrections

CH0029 now accepts all 31 occurrences of the repeated refrain in Surah 55. Seven had a trailing punctuation difference and were missed by exact-string matching.

Four labels changed from grade 2 to grade 1. For CH0074, 15:92 says questioning occurs and 7:6 identifies who is questioned. Neither specifies the subject as directly as 15:93 and 102:8. For CH0079, 20:25 and 20:26 provide the opening prayer context, while 20:27–28 directly express the request about speech.

Eight cases now contain acceptable_passage_sets. These identify alternative reference sets needed for a complete passage answer, including the boat and wall narratives. A first-anchor hit alone can overstate completion for these questions.

CH0180 and CH0206 locate the relevant stories but the Quran does not supply the people's personal names. They remain usable as story-location queries, with that interpretation explicit in their review notes.

Six extracted phrase queries have apostrophe or punctuation boundary issues and are flagged for query-quality review. They still occur as source-token sequences. Their IDs are CH0667, CH0695, CH1001, CH1154, CH1160 and CH1361. These should be excluded from a natural-user-query analysis.

The phrase-plus-keyword case CH0042 is supported by 50:16. A plain substring test would incorrectly reject it because the translation inserts [his] before “jugular vein.”

## Rescoring

The query text and engine rankings were preserved. Scores were recalculated from the saved runs against the corrected labels. Aggregate Hit@5 remains 86.3% for SQLite, 71.4% for OpenSearch lexical and 77.5% for OpenSearch phrase boosting. SQLite MRR@10 changes from 0.77207 to 0.77250. Query hashes and evidence were refreshed.

The per-pair audit is in relevance_audit.jsonl. Rebuild includes the recorded audit using audit_relevance.py. To rescore without rerunning retrieval, use compare_challenge.py --repo PATH --saved-runs. This option assumes IDs and query text still match the saved run, so use it only for label or review-metadata corrections.

Unlisted verses remain unjudged. This audit verifies the supplied anchors and contextual labels. It does not assert that every other retrieved ayah is irrelevant.
