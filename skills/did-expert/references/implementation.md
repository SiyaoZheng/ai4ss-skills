# Implementing a DID Analysis

Implementation should make the estimand, comparison set, treatment timing, and aggregation visible.
Software defaults are not methodological decisions.

## Before estimation

Construct and inspect the treatment history, cohort sizes, raw outcomes, event-time support, missingness,
and comparison groups. Preserve the code that defines treatment, the analytical sample, and every
reported aggregate. Re-estimate the analysis from the current data and code, and investigate warnings
or omitted observations that could affect the result.

## Estimation

Choose an estimator only after defining the target quantity and the comparisons that identify it.
Consult the methodological paper and current software documentation. Verify, in particular:

- how never-treated, not-yet-treated, and already-treated observations are coded;
- whether repeated cross-sections, unbalanced panels, reversals, or continuous treatment are supported;
- the default aggregation and weighting;
- the reference period and anticipation setting;
- the clustering or bootstrap procedure;
- whether confidence bands are pointwise or simultaneous; and
- which observations are silently omitted.

## Comparing implementations

When two implementations disagree, examine the component group-time or cohort-event estimates and align
their samples, comparison groups, weights, horizons, and nuisance models. Matching package syntax is not
enough; matching the estimand and identifying comparisons is the relevant test.

The final code should reproduce the reported numbers and figures from preserved inputs, while the methods
memo explains why those numbers answer the stated question.
