# Did adding questions improve search?

**Result: no improvement in this small test.** Both versions found an expected verse in the first five results for **8 out of 34 questions**. That is 23.5% for each, a difference of **zero percentage points**.

| Search tested | Questions with an expected verse in the first five | Result |
| --- | ---: | --- |
| Current meaning search | 8 / 34 (23.5%) | Starting point |
| Search with added questions | 8 / 34 (23.5%) | No gain |

The added questions changed the first five results for nine searches, but they did not increase the number of searches that found an expected verse. For example, a question about sellers giving customers less than they demand for themselves brought verse 2:286 into the first five after the change. That verse was not among the expected answers for that question. A reviewer would need to judge it before drawing conclusions about that individual result.

## Why the result is limited

The Quran index contains 6,236 verses. This trial added a question to just **10 verses**, so most verses had no added question to help them. We do not yet know if covering every verse would work better. The questions were also written after earlier work on the benchmark, and the benchmark does not list every possible relevant verse.

This was a local test of the same underlying model, using a slightly different version from the one in the browser. It compares both search versions under the same local conditions, but its scores should not be treated as exact browser PR scores.

The next test needs questions for the whole collection and a fresh set of searches with independently reviewed answers. Until then, the question-index idea has **not demonstrated an improvement**, and the next experiment remains on hold.

[Code and questions used](question_index_pilot.py) · [Results for each search](question_index_pilot_results.json) · [Full experiment plan](SEMANTIC_EXPERIMENT_PLAN.md)
