# Verse-by-verse relevance verification

The second review covers 1,777 labeled pairs. Each query now carries a rationale keyed by ayah. Each row in [the detailed audit](relevance_audit.jsonl) also includes the query, selected field, grade, and verbatim source evidence. Arabic and Bengali searches include supporting text from their own field. Generated lexical cases include the actual matched wording and distinguish apostrophe-split matches.

Added eight confirmed anchors, including 79:16 for Tuwa and 2:83 for the Arabic wording about kindness to parents. Six further labels moved to contextual credit. For example, 17:23 instructs a person how to speak to aging parents, while 17:24 supplies a prayer for them. For the question asking which three people were left behind, 9:118 locates the story but does not give their names. That case is excluded from direct-answer scoring. The phrase in 2:71 begins after an opening quotation mark and is valid; the other five apostrophe-split extracts still need natural-query review.

The final counts are 1,767 grade-2 retrieval anchors and 10 grade-1 contextual labels. A grade-2 anchor can be one explicitly requested part of a multi-verse answer. The passage sets identify questions requiring more than one part. The 1,253 extracted lexical pairs were mechanically checked, and 524 authored pairs have model-reviewed reasons. Additional relevant references may exist. Independent native-language assessment remains outstanding.

Validate against the local production corpus with `python evaluation/validate_challenge.py --repo PATH_TO_APP`. The validator checks one-to-one coverage, scope, grade, and the presence of every evidence excerpt in the cited verse. See [updated scores](CHALLENGE_RESULTS.md).

## First review (historical counts)


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
