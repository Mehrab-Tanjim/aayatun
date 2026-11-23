# Comparison with Onix deploy before PR #1

Onix's deploy branch was fetched at d9cff5d3f21dc11423465893fb1839dd6c9251c0, also the base of PR #1. The search function at that commit was executed locally against the same search.db, normalized text, query fixture, scopes and limits as PR revision 928ff86. Searchnorm.py is identical between those revisions. OpenSearch rankings are the previously recorded local 3.10.0 runs. The live PythonAnywhere index and deployed commit were not inspected.

| Query slice | Direct-anchor cases | Deploy | PR #1 | OpenSearch lexical | OpenSearch phrase boost |
|---|---:|---:|---:|---:|---:|
| All | 1,547 | 86.0% | 86.4% | 71.4% | 77.5% |
| Single word | 203 | 100.0% | 100.0% | 84.2% | 84.2% |
| Multi-keyword | 607 | 91.8% | 92.8% | 83.2% | 85.3% |
| Phrase | 519 | 97.3% | 97.3% | 71.1% | 86.5% |
| Semantic | 185 | 21.6% | 21.6% | 21.6% | 21.6% |
| Model-authored | 209 | 78.0% | 76.6% | 71.8% | 71.8% |

Paired family-bootstrap confidence interval for PR minus deploy Hit@5 is −0.07 to +0.86 percentage points overall, and −0.17 to +2.20 points for multi-keyword cases. These are exploratory intervals for a synthetic, incompletely judged dataset, not guarantees of real-world performance.

Examples of first-labeled-ayah rank, with 0 meaning outside the top ten:

| Query | Deploy | PR |
|---|---:|---:|
| pledge tree reward | 0 | 1 |
| barrier seas transgress | 5 | 1 |
| light upon light | 2 | 1 |
| moons pilgrimage calendar | 1 | 0 |
| breastfeeding two years weaning | 2 | 9 |
| orphans maturity property witnesses | 1 | 5 |

The latter examples show regressions in the model-authored slice. These are seed judgments, so review the complete ranked lists before calling any unlisted verse irrelevant.

Reproduce with python evaluation/compare_deploy.py from the workspace with dependencies installed and the existing local search index. The generated JSON records all deploy rankings, query hash, revision and per-slice metrics. Previous runs and rationale remain in CHALLENGE_RESULTS.md.
