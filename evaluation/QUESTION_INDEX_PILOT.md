# Question-expanded index pilot

This exploratory test adds one manually written question each for ten familiar ayat to the existing 6,236-verse index. It encodes questions as E5 passages and uses the highest cosine score per verse. Both conditions use the same cached float32 E5 query model and the existing int8 verse vectors. The browser PR uses an int8 query model, so this is a matched local comparison rather than a reproduction of its browser scores.

| Measure on 34 existing follow-up questions | Translation index | Expanded index |
| --- | ---: | ---: |
| A labeled ayah in top five | 8 | 8 |
| A labeled ayah in top ten | 8 | 8 |

Nine queries had a change in the top-five ordering. For example, the added question for 2:286 brought that verse into the top five for a question about customers receiving less than the seller demands, although the fixture's expected verse is different. This is a signal to review precision, and the existing labels do not exhaustively judge all other relevant results.

The ten additions cover only a tiny fraction of the corpus, and the author had previously seen the evaluation work. This experiment cannot estimate the effect of indexing questions for every verse or establish an improvement. It does not satisfy the promotion criteria in the experiment plan. Continue experiment 1 with evenly generated and reviewed questions, held-out intents, pooled relevance judgments and browser/device measurements before starting experiment 2.

Reproduce with the offline E5-small checkpoint, PyTorch, Transformers and NumPy by running `python evaluation/question_index_pilot.py`. The inputs and per-query rankings are in [the script](question_index_pilot.py) and [results](question_index_pilot_results.json).
