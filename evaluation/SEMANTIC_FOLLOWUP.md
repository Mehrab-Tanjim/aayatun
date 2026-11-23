# Semantic search follow-up

This comparison uses the exact head of Onix PR #1, `bc755b9`, as the keyword baseline. That baseline ran before implementation. We retained the original challenge and added 34 translation-scoped questions, including 24 English questions and 10 in Arabic, Bangla, French, Indonesian, and Spanish. The new file records an expected ayah and a reason for each question. Labels were checked against the translation text.

The full original keyword baseline found an expected ayah among the first five results for 40 of 185 scored semantic queries at their original field settings. The comparison below uses the same English translation corpus on both sides. Success means at least one expected ayah appeared in the first five results.

| Search queries | Queries | PR #1 keyword search | Search by meaning |
| --- | ---: | ---: | ---: |
| Existing English questions | 62 | 32 | **37** |
| New English questions | 24 | 1 | **5** |
| Existing questions in other languages | 90 | 1 | **6** |
| New questions in other languages | 10 | 0 | **2** |

The 90 existing non-English queries are translations of two topics. The new multilingual questions also include a few parallel prompts. These are constructed, incompletely judged cases, and the new topics await independent review. The small multilingual samples measure this fixture. Absolute success on the harder questions remains low.

The candidate uses cosine similarity over quantized, prebuilt verse embeddings and runs the pinned multilingual E5 int8 ONNX query model in a browser worker. It was tested in Chromium on all 186 translation-scoped questions. The first request with public model assets took about 50 seconds on the test machine. Subsequent queries in the same worker had a 48 ms median and 70 ms 95th percentile. These latter numbers exclude loading a new results page or reinitializing its worker. The experiment used a desktop machine. Phone timings and production hosting remain unmeasured.

A separate mobile-size Chromium test used the recorded static model files, submitted through the normal search dialog, and rendered 24:27 first for a question about entering someone's home. Switching to keyword search returned 24:35 first for `light upon light`. Eleven Flask tests passed.

## Reproduce

Run `python evaluation/semantic_baseline.py` from the benchmark checkout. This requires the existing search database in the neighboring Aayatun checkout and the pinned keyword commit.

Start the candidate Flask app on port 19201. With Playwright available to Node, run `node evaluation/evaluate_browser_meaning.cjs`. Set `AAYATUN_CHROME` to an installed Chromium path if Playwright Chromium is unavailable. Set `AAYATUN_TEST_URL` to use another port. If using the documented static model mirror, set `AAYATUN_LOCAL_MEANING_MODEL=1` for the benchmark.

The saved baseline and browser rankings contain fixture hashes for alignment.
