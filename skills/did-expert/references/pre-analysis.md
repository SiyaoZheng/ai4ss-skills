# Examining a Proposed DID Study

A DID analysis begins with the intervention and the panel, not with an estimator. The purpose of this
examination is to determine which comparisons the observed data can support and which causal quantity
those comparisons might identify.

## Intervention and exposure

Reconstruct the political or administrative process that produces treatment. Establish:

- the formal adoption date and the date at which exposure could affect behavior;
- whether announcement, anticipation, partial implementation, or enforcement precedes formal adoption;
- whether exposure is binary, continuous, repeated, reversible, or cumulative;
- whether treatment is assigned at the same level at which outcomes and uncertainty are measured;
- which units remain unexposed, become exposed later, or change exposure more than once; and
- which concurrent policies or shocks follow a similar timing pattern.

Treatment coding should preserve these institutional distinctions. A convenient first-treatment date
can obscure reversals, heterogeneous implementation, or prior exposure.

## Panel support

Describe the unit, time scale, observation window, and treatment histories before estimating effects.
Tabulate cohort sizes and the number of observations available at each relative time. Units treated in
the first observed period have no observed untreated baseline for a standard group-time effect. Late
cohorts may contribute little post-treatment information; early cohorts may dominate long-horizon
aggregates.

Inspect irregular spacing, gaps, entry and exit, changes in reporting, and whether panel imbalance is
related to treatment or outcomes. A balanced-panel restriction changes the population and may select
on post-treatment survival. It requires a substantive justification, not merely an estimator that is
easier to run on balanced data.

## Treatment histories

Verify treatment dates against primary records for cases most capable of changing the result: large or
influential units, boundary dates, ambiguous adopters, small cohorts, and a random set of ordinary
cases. For an absorbing treatment, confirm that observed status does not reverse. When reversals are
real, define an estimand for switchers or exposure histories rather than recoding them away.

Examine how many independent units receive treatment and how concentrated adoption is across places
and periods. Nominal observation counts can greatly overstate the effective information in the design.

## Outcomes and measures

Inspect the outcome distribution, raw trajectories, missingness, reporting changes, and extreme
movements. Compare outcome levels and changes across cohorts before treatment without interpreting
visual similarity as proof of parallel trends. Check transformations against the substantive scale of
the outcome; log, inverse-hyperbolic-sine, count, rate, and level specifications answer different
questions.

Covariates require a temporal interpretation. Baseline predictors may support conditional
parallel-trends arguments or improve precision. Variables affected by treatment, anticipation, or a
common consequence of treatment and outcome should not be introduced as routine controls.

## Comparison groups

List the units and periods that would supply untreated outcomes for each treated cohort. Never-treated
and not-yet-treated units need not represent the same counterfactual. Ask why their untreated outcome
changes should approximate those of the treated cohort and whether that argument varies across time,
place, or institutional setting.

Inspect overlap in baseline outcomes, trends, covariates, geography, and exposure risk. Lack of support
may call for a narrower population, event window, or estimand. It cannot be repaired by estimator choice
alone.

## Sample construction and missingness

Record consequential exclusions and distinguish prior design choices from decisions made after seeing
the data. Trace how each restriction changes treated cohorts, comparison units, event-time support, and
the target population. Compare observed and missing cases, and investigate whether attrition or data
availability changes at treatment.

Validate selected records and aggregates against original sources. Boundary changes, identifier
re-use, mergers, and administrative recoding can create treatment or outcome jumps that resemble policy
effects.

## Feasibility judgment

Summarize whether the study has credible untreated comparisons, enough pre- and post-treatment support
for the proposed dynamic claims, a defensible measure of exposure, and sufficient independent variation
for useful precision. When one of these conditions fails, revise the estimand, sample, period, measure,
or design before selecting software.
