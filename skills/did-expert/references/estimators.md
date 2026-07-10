# Estimands, Comparisons, and Estimators in DID

Estimator choice follows from the causal quantity, treatment histories, and admissible comparisons.
Different modern DID estimators often disagree because they estimate different aggregates from
different units and periods, not because one is universally correct.

## The canonical comparison

In the two-group, two-period design, DID compares the treated group's outcome change with the untreated
group's change. Identification requires the treated group's untreated potential outcome to have changed
like the comparison group's outcome, together with a treatment definition that rules out relevant
anticipation and interference.

With more periods, the design can describe dynamics and examine pre-treatment evidence, but additional
periods do not make the identifying assumption testable. With multiple adoption cohorts, there is no
single DID comparison until the researcher specifies which group-time effects and aggregation define
the target.

## Staggered adoption

Let ATT(g,t) denote the average effect for units first treated in cohort g at time t. Group-time methods
estimate these effects using never-treated or not-yet-treated comparison units, then aggregate them.
The credibility of each component depends on the relevant cohort and period; a comparison that is
plausible for early adopters may be weak for late adopters.

Callaway and Sant'Anna estimate group-time effects and make the comparison group and aggregation
explicit. Sun and Abraham use cohort-by-event-time interactions to avoid contamination of conventional
event-study coefficients by treatment-effect heterogeneity. Borusyak, Jaravel, and Spiess impute
untreated outcomes from untreated observations. De Chaisemartin and D'Haultfoeuille develop estimators
for heterogeneous and, in extensions, non-absorbing treatment paths. These approaches differ in
target, nuisance estimation, sample use, and aggregation.

Conventional two-way fixed effects can combine already-treated and later-treated units with negative or
otherwise opaque weights when timing and effects vary. A decomposition can describe that estimand; it
does not by itself supply a better causal comparison.

## Aggregation

An overall ATT, cohort average, calendar-time average, and event-time profile answer different
questions. Event-time averages also change cohort composition across horizons unless the support is
held fixed. State which cohorts and periods receive weight, whether the weights represent the study
population or another policy-relevant population, and how the result changes under balanced event-time
support.

Dynamic effects require a choice about anticipation, reference periods, and the maximum horizon that
has credible support. Binning distant leads or lags changes the target and should be justified by the
political process, not by a cleaner graph.

## Covariates and conditional parallel trends

Regression adjustment, weighting, and doubly robust procedures can identify effects under conditional
parallel trends when overlap and nuisance-model conditions are credible. Covariates should predict
untreated outcome changes or define comparable strata. Conditioning on post-treatment variables or
poorly supported propensity scores creates new problems rather than strengthening the design.

## Repeated cross-sections

Repeated cross-sectional DID identifies population-level changes under stable sampling and composition
conditions; it does not follow the same individuals over time. Clarify whether the target is a change in
the population distribution or an individual-level effect, and examine treatment-related changes in
who enters the sample.

## Non-absorbing and continuous treatment

For treatment reversals, repeated switches, or dose changes, first define the causal contrast: the
effect of switching on, switching off, increasing dose, or following a treatment history. Binary
first-adoption coding generally discards this information. Continuous-treatment DID also requires care
because comparisons across dose changes can combine selection into dose with heterogeneous responses.

## Synthetic and latent-factor comparisons

Synthetic DID, augmented synthetic control, interactive fixed-effects, and matrix-completion methods
construct counterfactuals under assumptions different from standard parallel trends. Their value lies
in whether weighted or latent-factor comparisons are credible in the application. Agreement with a
standard DID estimate is informative only after the distinct targets and assumptions are reconciled.

## Choosing among approaches

The methods memo should explain:

- the causal quantity and population;
- the treatment histories that enter;
- the untreated units and periods used for comparison;
- the identifying assumption for those comparisons;
- the aggregation and event-time support;
- the handling of covariates, missingness, and treatment reversals; and
- why the estimator's uncertainty calculation matches the assignment and dependence structure.

Useful methodological anchors include Callaway and Sant'Anna (2021), Sun and Abraham (2021),
Goodman-Bacon (2021), Borusyak, Jaravel, and Spiess (2024), and de Chaisemartin and
D'Haultfoeuille (2020 and subsequent work).
