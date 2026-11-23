# Aayatun challenger benchmark v2

This benchmark contains 1,566 queries in 646 connected families. It combines 416 authored or retained diagnostic cases and 1,150 automatically constructed known-item lexical cases. The source corpus has 6,236 verses. The SQLite target is upstream PR revision d39f74c. The manifest records fixture and English-corpus hashes.

| Primary intent | Queries |
|---|---:|
| Single word | 203 |
| Multiple keywords | 607 |
| Phrase | 519 |
| Sentence or semantic question | 186 |
| Multilingual legacy diagnostics | 21 |
| Ambiguous | 12 |
| No direct answer | 18 |

## Coverage and construction

English, Arabic and Bengali have native-script examples. Each has at least 20 multi-keyword cases. There are seven mixed-script cases. Another 45 language varieties have two cross-language questions each, about debt relief and returning greetings. These include Spanish, French, Mandarin, Hindi, Urdu, Portuguese, Russian, Indonesian, German, Japanese, Punjabi, Marathi, Telugu, Turkish, Tamil, Vietnamese, Korean, Persian, Swahili, Hausa, Malay, Italian, Filipino, Gujarati, Kannada, Malayalam, Thai, Burmese, Polish, Ukrainian, Dutch, Uzbek, Pashto, Somali, Amharic, Yoruba, Javanese, Cantonese, Egyptian Arabic, Sundanese, Romanian, Odia, Igbo, Swedish and Nepali. The manifest contains the exact tags and counts. This is a broad language smoke test with shallow topic coverage in those additional languages. It does not establish comprehensive coverage of every major language.

The model authored queries and proposed references using domain knowledge, then checked proposed passages against local English and Arabic Quran text. English, Arabic and Bengali keyword families include selected displayed Bengali tafsir checks. The evidence file records the underlying source passages. Evidence fragments are cues for audit. In CH0273, the evidence cue “turned yellow” matches the wording of 57:20.

Questions cover narrative events, ethics, worship, family relations, spending, trade, nature imagery, direct wording, inflections, misspellings, and short underspecified searches. Ambiguous cases record representative interpretations in their rationales. Multi-verse cases retain all supplied anchors. The repeated refrain in Surah 55 now includes every identical English occurrence for its wording query.

The automatic set uses 500 reproducibly sampled verse targets before engine rankings are inspected. Rare single words have all exact-token source matches labeled. Multiword and phrase queries are extracted from the actual English translation. Exact duplicate translation targets are accepted. These cases test lexical known-item recovery and favor systems that match source wording. Their scores must be reported separately from authored semantic questions.

## Labels and scope

Grade 2 denotes a model-proposed direct relevance anchor. Unlisted verse pairs are unjudged. The fixture does not pretend to provide exhaustive relevance judgments. Single-word and ambiguous queries can have many additional valid results. Evidence supports the references, while inference and question interpretation remain judgments. No independent human or native-speaker validation has occurred.

The corpus contains Arabic Quran text, English translation, and Bengali and English tafsir. Other-language questions against the translation scope explicitly test cross-language retrieval. A lexical failure there can reflect lack of translation or embedding support.

No-answer cases distinguish absent names and measurements from useful surrounding context. Returning related verses does not by itself imply that an engine asserted a false answer. Passage questions should be evaluated for coverage of the required references, not just one-hit success.

## Reproducibility and split isolation

From the workspace root run with the existing app Python environment.

    python aayatun-benchmark/evaluation/build_challenge.py --repo aayatun-research
    python aayatun-benchmark/evaluation/validate_challenge.py
    python aayatun-benchmark/evaluation/compare_challenge.py --repo aayatun-research

The comparison requires the existing loopback OpenSearch test cluster and aayatun-eval-normalized index. It loads searchtool.py from trusted Git revision d39f74c, including normal app formatting and fallback paths. The phrase configuration adds a native phrase query with weight 3 to the same baseline query, fields and index. The weight was fixed before looking at this fixture's scores. Explicit outer quotes are removed in both OpenSearch modes so the phrase option is the changed variable.

There are 428 public diagnostic cases, 886 development cases and 252 frozen public test cases. Connected families, parallel questions, duplicate queries and shared labeled verses stay in one split. The public test set is visible and was frozen before this comparison. It should not be called a private holdout, and future tuning should use development data. Connected components do not guarantee that all related theological topics have been isolated.

## Statistical interpretation

Report anchor Hit@5 and MRR@10 with denominators, intent, provenance and split. Avoid calling these precision or exhaustive nDCG because missing judgments are unknown. Report no-answer behavior separately. For ambiguous questions and required multi-verse passages, inspect anchor coverage in addition to the first match.

Use a paired bootstrap over connected families, with 2,000 resamples and a fixed random seed, to estimate the Hit@5 difference. Translations and extracted variants remain in the same family. The 646 family components make the comparison larger than the original 108-query seed, but dataset size alone cannot guarantee statistical significance or representative production performance. Treat slice comparisons as exploratory and do not declare a universal winner based on the aggregate.

The extra 45 languages share only two scenarios. No statistically reliable per-language claim follows from those rows. A larger natural-user semantic sample and independent multilingual review would improve external validity. The model's authored query and self-check are two stages of one model-assisted workflow.

## Review and provenance

challenge_v2.jsonl stores questions, scope, family, split, references, rationales, origin and review status. challenge_evidence.json stores local English and Arabic source evidence for labeled verses. challenge_manifest.json records counts, hashes and limitations. CHALLENGE_PREVIEW.md offers a readable preview.

Questions added here are original model-authored text or mechanically extracted known-item queries. Existing seeds are retained from this repository. No Daleel questions or external benchmark rows were imported. Source translation and Quran text retain their existing source attribution in the app repository. This benchmark does not grant additional rights to the underlying corpus.

See RELEVANCE_AUDIT.md for the subsequent pair-by-pair label audit and corrections.

Each labeled ref now has a verse-specific explanation under `verse_rationales`. See [the second relevance review](RELEVANCE_AUDIT.md) for scope, grade changes and limitations.
