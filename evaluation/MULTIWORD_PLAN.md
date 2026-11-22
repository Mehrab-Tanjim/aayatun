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

## Implementation sequence

1. **Freeze the evaluation before tuning.** Collect consented, anonymized real searches and author near misses with fluent reviewers. Include reordered terms, changed suffixes, gaps, mixed scripts, rare plus common terms, repetitions, wrong-source answers and unanswerable details. Keep related queries and known verse families in one split. Pool old, new and semantic candidates for independent graded judgments. Score repeated phrases by valid verse or equivalence group; score passage questions for supporting-verse coverage as well as first hit.
2. **Separate retrieval from rendering.** Keep the existing `/search/` request, reference redirects and field selection. Parse once into query text, explicit syntax, requested scope and bounded candidate count. A retriever accepts that request and returns ordered verse IDs, matched source fields and the evidence type (literal, stem, proximity or semantic). The coordinator validates IDs, deduplicates and hands the selected verses to the existing local formatter. A semantic match should display the source text and its label without manufacturing a literal highlight. Start with SQLite; add another provider through this same contract when its benchmark warrants it.
3. **Deliver the SQLite candidate behind a flag.** Build a versioned, read-only English translation side index offline. Publish it atomically after checking corpus fingerprint, tokenizer support, row count and unique canonical IDs. A missing or stale artifact selects the current lexical path. Compare PR-only, stemmed all-term retrieval and stemmed retrieval with a bounded proximity boost. In all-fields mode, trial English translation candidates alongside original Arabic, Bengali, and tafsir candidates. Preserve explicit phrase/Boolean semantics and keep field filters strict. Estimate the benefit of each signal independently. Reserve multi-verse context and cross-language expansion for their own tests. [SQLite FTS5](https://sqlite.org/fts5.html)
4. **Benchmark a hosted OpenSearch alternative.** Index the same corpus by canonical verse ID in separate analyzed and literal fields. Compare exact phrases, per-language stemming, proximity and minimum term coverage to the best local candidate. Add offline multilingual vectors and rank fusion as a separate experiment after establishing the lexical baseline. Keep inference off the Flask worker. Check PythonAnywhere HTTPS reachability, cost, timeouts and fallback. Deploy versioned indices via alias only if measured benefits justify operating them. [Language analyzers](https://docs.opensearch.org/latest/analyzers/language-analyzers/index/) · [Hybrid search](https://docs.opensearch.org/latest/search-plugins/hybrid-search/)
5. **Release gates and rollback.** Proposed gates, to freeze before running the private holdout: improve graded multi-keyword nDCG@10 by at least 0.03 absolute with the lower paired 95% bootstrap bound above zero (resample topic families); preserve all reviewed exact-reference and strict-field regression tests; investigate any language slice dropping over 0.02. Report denominators and uncertainty for small slices. Track empty results, no-answer behavior, and literal-query regressions separately. On staging, benchmark warm and cold runs at actual worker concurrency, p50/p95, worker memory, disk and build time. Target warm p95 within baseline +100 ms, and document the owner's actual resource limits. Simulate missing index and remote timeout. Enable the flag on staging first, reload the worker, run browser smoke tests, then opt into production after review. Disable the flag and reload to roll back.
