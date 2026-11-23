# Local OpenSearch experiment

On 2026-11-22, tested OpenSearch 3.10.0 on Windows with its bundled JDK, bound to loopback. The local cluster has security disabled and is suitable only for isolated testing. The test index holds the 6,236 verses from the Aayatun deploy corpus with Arabic, English, Bengali tafsir, English tafsir, AI and surah name fields. Queries use the native default multi_match and the fixture's selected field. No hybrid inference was used.

| Slice | Cases | SQLite PR Hit@5 | OpenSearch standard | OpenSearch with wasla mapping |
|---|---:|---:|---:|---:|
| Single | 14 | 14 | 10 | 13 |
| Multi-keyword | 18 | 15 | 18 | 18 |
| Phrase | 16 | 16 | 14 | 14 |
| Multilingual | 21 | 15 | 11 | 14 |
| Semantic | 29 | 7 | 7 | 7 |

Hit@5 means at least one grade-2 seed appeared in the first five; unjudged verses are not counted. These small, visible, incompletely judged cases cannot establish a production relevance improvement. The Arabic analyzer maps ordinary `النحل` to `نحل` but the Uthmani `ٱلنَّحْلَ` to `ٱلنحل`. A built-in mapping character filter from ٱ to ا improved the Arabic slice, but phrase and multilingual misses remain. English phrase and semantic regressions also remain. More field-aware analysis and independent review are needed.

Run `opensearch_trial.py` against an isolated empty loopback cluster on port 19200. Run once with no arguments and once with `--normalized-arabic`. Each creates a fixed named index and fails if that index already exists. The experiment performs no provisioning or deployment. It is not a production service configuration.

During the local run the cluster blocked new indexes because the machine exceeded its percentage disk watermark despite about 36 GiB free. Temporary cluster disk thresholds were adjusted to 20/10/5 GiB on the isolated test cluster. Production must use independently chosen resource and disk limits.
