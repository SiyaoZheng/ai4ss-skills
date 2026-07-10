# Diagnosing a DID Design

Diagnostics do not certify a DID design. They reveal how the result depends on comparisons,
pre-treatment evidence, timing, measurement, and assumptions, and they can show when the original
causal claim should be revised.

## Parallel trends and pre-treatment evidence

Parallel trends concerns untreated potential outcomes after treatment. Observed pre-treatment paths
can make the assumption more or less credible, but cannot establish it. Examine raw cohort trajectories,
event-time estimates, and institutionally important pre-periods. Interpret both point estimates and
their uncertainty; failure to reject a joint pre-trend test is not affirmative evidence of parallel
trends.

Pre-trend testing can have low power, and selecting a specification because it passes a pre-test can
worsen bias. Equivalence tests may rule out pre-treatment deviations larger than a substantively chosen
bound, but the bound requires an application-specific rationale. Apparent pre-trends may reflect
anticipation, changing composition, miscoded timing, or a different untreated trajectory; the data alone
do not distinguish these explanations.

## Anticipation and timing

Use policy announcements, legislative stages, implementation rules, enforcement dates, and behavioral
responses to define plausible anticipation windows. Re-estimating with earlier exposure dates or
excluding the ambiguous interval is informative when those choices correspond to the institution.
Arbitrary lead dropping can conceal a timing problem.

## Comparison support and composition

Report which cohorts and comparison units identify each effect and how support changes across event
time. Examine cohort leverage, overlap, sample entry and exit, and whether not-yet-treated units become
less comparable as adoption proceeds. Re-estimate balanced-horizon or leave-one-cohort summaries when
they clarify composition; interpret the changed target explicitly.

## Sensitivity to violations

Sensitivity analysis should address a plausible violation. Rambachan and Roth's approach asks how much
post-treatment deviation from parallel trends can be tolerated under restrictions related to observed
pre-treatment deviations. The resulting identified set is useful only when the restriction and scale
are substantively interpretable. Alternative comparison groups, time windows, and outcome definitions
can also be informative when each corresponds to a defensible counterfactual.

## Placebos and falsification

A placebo outcome is informative when treatment should not affect it but the confounding process should.
An outcome unrelated to both treatment and the suspected confounder has little diagnostic value. A
placebo date is useful only if it creates a meaningful untreated comparison and does not overlap genuine
anticipation. Randomization inference requires a defensible assignment mechanism; permuting labels by
convenience does not create one.

Negative controls, unaffected populations, or policy-ineligible units can be powerful when the political
process justifies the exclusion. Their relevance should be argued rather than inferred from a null
coefficient.

## Spillovers and interference

Map plausible channels through which treatment of one unit can affect another: geographic diffusion,
policy competition, migration, markets, media, administrative hierarchy, and general equilibrium. A
contaminated comparison group usually changes the estimand and may attenuate, amplify, or reverse the
contrast. Distance bands, exposure networks, alternative comparison sets, or partial-identification
bounds are useful only when they correspond to a credible transmission process.

## Inference and effective information

Cluster uncertainty at the level at which treatment shocks or assignment are shared, while examining
cross-sectional and serial dependence that may operate at other levels. The number, size, leverage, and
treatment balance of clusters matter more than a universal cutoff. With few or highly unequal clusters,
consider small-sample corrections, wild-cluster bootstrap, randomization-based procedures, or a more
modest claim, depending on the assignment process.

For event-time profiles, simultaneous intervals address the joint path more directly than a sequence of
pointwise tests. Multiple outcomes and subgroup searches require an explicit account of the family of
claims and the role of exploration.

## Missingness and panel imbalance

Compare attrition, observation windows, and missing outcomes across treatment histories and time.
Contrast the full available sample with substantively justified stable samples, noting that the latter
change the population. Missingness induced by treatment is itself an outcome or selection process and
cannot be repaired by routine complete-case analysis.

## Precision and feasibility

Formal prospective power calculations are often weakly grounded in observational DID studies because
the effect distribution, serial correlation, treatment timing, attrition, and effective number of
assignment units are uncertain. Assess feasibility from the treated and comparison clusters, cohort
sizes, observation windows, outcome variation, dependence, and the scale of a substantively meaningful
effect.

Simulation or an MDE calculation is useful when its inputs come from defensible pilot data, a close prior
study, or a clearly specified data-generating process. Vary uncertain inputs and reproduce the actual
assignment, timing, estimator, and missingness structure. For completed studies, interpret confidence
intervals against substantively meaningful effects rather than using post hoc power as an explanation
for a null result.

## Interpreting disagreement

Differences across estimators or samples should be traced to the target parameter, comparison set,
weights, cohorts, horizon, covariates, missingness, or assumptions. Agreement is not a validation test,
and disagreement is not automatically a failure. The diagnostic task is to identify what each estimate
learns and whether any of those quantities answer the political question.

Key methodological sources include Roth (2022) on pre-testing, Rambachan and Roth (2023) on sensitivity,
Bertrand, Duflo, and Mullainathan (2004) on serial correlation, and contemporary work on placebo outcomes
and spillovers.
