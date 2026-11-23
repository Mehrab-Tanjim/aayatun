# Integrated search evaluation

The combined lexical implementation at bc755b9 was run against the original Onix PR revision 928ff86 using the same local index, queries, scopes and limits. Both implementations were re-executed for all 1,566 original queries and all 79 supplementary difficult queries. Results below count supplied relevant anchors in the first five results.

| Fixture | Scored cases | Original PR | Combined search | OpenSearch lexical | OpenSearch phrase boost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original challenger | 1,547 | 1,336 (86.4%) | 1,336 (86.4%) | 1,105 (71.4%) | 1,199 (77.5%) |
| Difficult multiword | 79 | 40 (50.6%) | 62 (78.5%) | 35 (44.3%) | 35 (44.3%) |
| Surah name plus Arabic | 33 | 5 (15.2%) | 27 (81.8%) | 2 (6.1%) | 2 (6.1%) |

The original 1,547 scored cases had identical aggregate first-place hits, top-five hits and MRR@10. No supplied anchor that ranked in the original PR's top ten received a lower rank on either fixture. On the 79 supplementary cases, first-place hits rose from 26 to 51 and MRR@10 rose from 0.392 to 0.695.

The complete original fixture includes 18 no-answer cases and one contextual-only case. They were executed and retained in the raw runs, with direct-answer score denominators excluding them.

OpenSearch 3.10.0 was restarted locally and both lexical configurations were re-run on both fixtures. The existing normalized index has 6,236 verse IDs. English and Arabic text were checked equal against SQLite for every ID. These are lexical comparisons using the recorded configurations, without vectors or reranking. This report does not establish a universal engine winner.

The nine lexical Flask/search tests passed, including root lookup, common surah spelling variants, field restrictions, root-index rollback and retry. The local root index matched all 48,549 distinct annotated root/verse/word entries in the source metadata.

## Reproduction

Run from this benchmark checkout using the existing application environment and local index.

```text
python evaluation/compare_integrated.py
python evaluation/compare_integrated_opensearch.py
python evaluation/validate_challenge.py --repo ../aayatun-research
```

The OpenSearch command expects the loopback cluster at port 19200 with the existing aayatun-eval-normalized index. integrated_results.json and integrated_opensearch_results.json record complete per-query rankings and fixture hashes.

## Limits

This is a constructed, incompletely judged benchmark. Most original multiword queries were extracted from the answer translation. Twenty-five of the new surah-prefix cases were mechanically selected to exercise the feature. Several questions share verses or intents, and independent review remains pending. The observed absence of anchor regressions applies to these fixtures. PythonAnywhere performance and the live deployment were not tested.

## Semantic follow-up

The pinned multilingual E5-small trial was re-run on all 6,236 translations and 1,441 translation-scoped queries. translation_vector_trial.py and translation_vector_results.json record the model revision, corpus hash and per-query results. On 62 model-authored English questions, lexical search found an anchor in the top five for 32, vector search for 37, and deploy-plus-vector reciprocal rank fusion for 40. The same fusion reduced multi-keyword coverage, supporting an explicit meaning-search mode.

A separate fork follow-up implements an optional local inference service and Search by meaning control. Deployment still requires validation against the actual hosting resources.

The actual meaning-search UI was tested through Flask and the live local inference service on all 62 English translation questions. It reproduced 40/62 top-five anchor hits. Full results are in meaning_e2e_results.json. Eleven lexical, root and semantic-boundary tests passed. The service is an optional local prototype, with production hosting validation pending.
