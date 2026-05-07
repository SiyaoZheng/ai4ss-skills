# Skill Benchmark: cleaning-contract

**Model**: <model-name>
**Date**: 2026-04-28T10:54:45Z
**Evals**: 1, 2, 3 (1 run per (eval × config); 3 evals × 2 configs = 6 runs total)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% | 53% ± 26% | +0.47 |
| Time | 482.6s ± 172.4s | 386.5s ± 128.9s | +96.1s |
| Tokens | 91708 ± 16881 | 69397 ± 4663 | +22311 |

`±` values are population standard deviation across the **3 evals** (n=3),
not within-eval run-to-run variance. Multi-run within-eval benchmarking
with proper run-level stddev is future work.

## Per-eval results

| Eval | Dataset | with-skill | without-skill |
|------|---------|-----------|---------------|
| 1 | CGSS 2021 (shared recodes, reversal, weight) | 6/6 (100%) | 1/6 (17%) |
| 2 | Dickson 2014 (positive missing trap: A3A vs Q23) | 6/6 (100%) | 4/6 (67%) |
| 3 | ABS W5 (structural inapplicables, universe, weight) | 4/4 (100%) | 3/4 (75%) |

## Methodology note (TA-132, 2026-05-07)

The original `benchmark.md` claimed "3 runs each per configuration" but only
1 run per (eval × config) was executed. The per-eval results above are the
ground truth; the summary stddevs reflect between-eval variance computed from
those 3 observations.
