# Multi-keyword search evaluation and delivery plan

## Decision and evidence

Treat upstream [PR #1](https://github.com/OnixHoque/aayatun/pull/1) as a phrase-ranking change. The earlier 16 phrase queries placed a direct seed first on all 16 after the change (13 before). For the separate multi-keyword test we reran all 18 English queries labeled `multi` against the PR base `d9cff5d` and head `2cc15b3`, using the same SQLite index, query scopes and top ten cutoff. A hit means at least one grade-2 seed verse appeared in the first five. MRR@10 averages the reciprocal rank of the first such verse, counting a miss as zero.

| System | Seed Hit@5 | Seed MRR@10 |
|---|---:|---:|
| Base | 15/18 | 0.723 |
| Phrase-first PR | 15/18 | 0.723 |
| PR plus experimental English stemming | 17/18 | 0.856 |

Base and PR had identical first-seed rank on all 18 queries and identical top-ten lists on 17. “Hardship ease” reordered verses while retaining a direct seed at rank one. “Pledge tree reward” missed 48:18 in both lists. Its translation uses “pledged” and “rewarded,” which the added phrase tier cannot match to the typed forms.

The trial built an in-memory FTS5 index over the 6,236 English translations with the Porter tokenizer. For English translation-scoped queries it retrieved up to ten BM25-ranked verses containing **all stemmed terms**, then appended the PR results and deduplicated by verse. Other scopes used the PR ranking. “Pledge tree reward” rose from outside ten to first, “fasting decreed” moved from second to first, and “favors Lord deny” moved the first labeled verse from ninth to first. The last gain needs adjudication because several earlier hits already contain the same refrain. “Kingdom death life deeds” still missed its seeds: the query combines vocabulary and context from adjacent verses. The 18 cases were visible during diagnosis, the seed labels are incomplete, and this trial provides no deployment latency or non-English quality estimate.

## Reproduce

The experiment folder includes the query fixture, both recorded top-ten lists for each case, the SQLite index fingerprint, and the stemming trial. Install the app dependencies, build the search index from the repo root with `python build_search.py` if needed, and use search code matching PR head. From the repo root run:

```text
python evaluation/run_eval.py --repo . --baseline-ref d9cff5d3f21dc11423465893fb1839dd6c9251c0 --intent multi --output evaluation/pr1-multiword-replay.json
python evaluation/porter_trial.py .
```

The trial uses the recorded PR rankings in `pr1-multiword.json`. Compare the replay's result IDs to the recorded ones before attributing differences to ranking. Keep the seed fixture for diagnosis and regression tests. Use a new blinded set for deciding what to ship.

## Delivery decision

Use **OpenSearch as the first advanced-search candidate**. Aayatun already owns a working SQLite fallback. The Porter trial illustrates the value of analyzing word forms; the measured gain belongs to that prototype. Shipping its Python list-merging policy would add a second ranking system to maintain. Keep the phrase-first PR as an independently reviewable, narrow change. Implement advanced ranking through versioned OpenSearch mappings, query templates and native search pipelines.

1. **Establish feasibility and the baseline.** Pin an OpenSearch distribution/version and compatible `opensearch-py` client. Use a disposable local cluster for evaluation. Before choosing a hosted endpoint, test verified HTTPS from the actual PythonAnywhere web worker (including proxy compatibility), and price the service at expected traffic and storage. Free accounts use an outbound allowlist. If hosting is infeasible, keep existing SQLite search and consider only built-in FTS5 configuration for local lexical improvements. [PythonAnywhere network policy](https://help.pythonanywhere.com/pages/403ForbiddenError/) · [Python client](https://docs.opensearch.org/latest/clients/python-low-level/) · [SQLite FTS5](https://sqlite.org/fts5.html)
2. **Build one reproducible index.** Bulk-load one document per canonical verse ID. Keep the Arabic verse, English translation, Bengali and English tafsir, surah name and AI explanation in labeled fields. Assign language analyzers by the known field language, and use an unstemmed text subfield with positions for phrase queries. Test tokenizer output with the engine's analyze API for Arabic vowel marks, Bengali combining marks and English inflections. Verify all 6,236 IDs against the source and swap a versioned index behind an alias. [Language analyzers](https://docs.opensearch.org/latest/analyzers/language-analyzers/index/)
3. **Benchmark engine defaults before tuning.** Begin with native BM25 using a field-scoped `match` query or `multi_match` across the allowed fields. Then test one configuration change at a time: language analysis, minimum term coverage, a phrase clause on the unstemmed field, and limited phrase slop. Test the effect of requiring multiple words within one field on mixed-script searches. Pass escaped user text as values in structured queries. Retain explicit syntax on the existing path until parity tests cover its behavior. Version each mapping and template alongside the engine version. Compare the returned order directly. [Multi-match queries](https://docs.opensearch.org/latest/query-dsl/full-text/multi-match/)
4. **Keep application code small.** Flask handles reference redirects, field selection, authentication to the search service, and request deadlines. Send the query through the official client, read ordered verse IDs and matched fields, then render the canonical text and source labels from Aayatun. Select one backend per request. On timeout, index mismatch or outage, run the existing SQLite query. An environment setting and worker reload should be sufficient to roll back.
5. **Evaluate semantic retrieval as a second milestone.** Language analyzers handle word forms within a language. For cross-language meaning, pin a multilingual embedding model, encode corpus and queries with its matching settings outside Flask, and use native vector search. Compare lexical-only against OpenSearch's hybrid query with a supported built-in fusion method, such as reciprocal rank fusion. Verify the pinned service offers those features. Trial an explicit meaning-search mode and evaluate cross-language and no-answer cases before considering automatic routing. [Native hybrid search](https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/)
6. **Decide on evidence.** Freeze the private challenge set before tuning. Have two fluent reviewers judge pooled results, including repeated verses and possible answers spanning adjacent verses. Proposed lexical release gates: a multi-keyword nDCG@10 gain of at least 0.03 over the existing backend, lower paired 95% confidence bound above zero when resampling topic families, passing reference and field-scope checks, and investigation of language slices that drop more than 0.02. Measure p50/p95 on the actual hosting plan and worker concurrency, using baseline +100 ms as the initial warm p95 budget. Report denominators, query volume, monthly cost, rebuild time and fallback tests. Evaluate hybrid with its own semantic slice and cost. Adopt only after meeting agreed quality and operating limits.
