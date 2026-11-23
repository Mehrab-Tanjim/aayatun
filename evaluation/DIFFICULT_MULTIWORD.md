# Additional multi-keyword diagnostics

These 21 model-authored cases supplement the existing benchmark without changing its frozen fixture. The expected verses were checked against the local English or Arabic text. Labels identify plausible anchors, not an exhaustive list of relevant verses. Independent review remains pending.

Ten cases use widely separated words from one translation. All three local implementations ranked the labeled verse first on all ten. Distance alone did not make these cases difficult for this corpus.

Nine cases add paraphrases, inferred concepts and alternative wording. Their labeled-verse ranks are below. Zero means outside the top ten. The mixed-script branch was evaluated at the local branch head, deploy at d9cff5d and PR #1 at 928ff86.

| ID | Deploy | PR #1 | Mixed-script branch |
| --- | ---: | ---: | ---: |
| DM13 | 0 | 0 | 0 |
| DM14 | 0 | 0 | 0 |
| DM15 | 1 | 1 | 1 |
| DM16 | 1 | 1 | 1 |
| DM17 | 0 | 0 | 0 |
| DM18 | 0 | 4 | 4 |
| DM19 | 7 | 2 | 2 |
| DM20 | 3 | 2 | 2 |
| DM21 | 0 | 0 | 0 |

For the requested `luqman حمل` and `luqman حملت` queries, all three implementations placed 31:14 outside the top ten. The input combines a surah name with a prefix of an inflected Arabic word in that surah. These results were measured against the same local index with all fields selected, and do not establish the live server state.

These cases are exploratory and small. They were selected with knowledge of the corpus and are not a statistically representative test.
