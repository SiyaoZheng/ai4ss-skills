---
name: research-analysis-runner
description: >
  Conduct iterative quantitative empirical analysis for political-science research. Use when
  exploring analysis-ready data, producing descriptive evidence, estimating primary models,
  diagnosing designs, examining robustness, heterogeneity, or mechanisms, reconciling conflicting
  results, and deciding what the evidence changes. Triggers include "run the analysis", "baseline
  model", "descriptive analysis", "robustness", "heterogeneity", "mechanism analysis", "实证分析",
  "基准回归", "描述性统计", "稳健性检验", "异质性分析".
---

# Research Analysis Runner

Use empirical analysis to assess the substantive question, the proposed explanation, and the principal
rivals. Estimation, diagnostics, and sensitivity analysis should reveal what the evidence supports and
where the design or interpretation requires revision.

## Analysis record

The work should leave:

1. reproducible analysis code;
2. inspectable statistical outputs and exploratory diagnostics; and
3. an **Empirical Analysis Memo** explaining what was learned, what changed, what remains uncertain,
   and which analyses or design revisions follow.

The memo is a provisional account for collaborators and remains distinct from a polished manuscript
results section.

## Conducting the analysis

### 1. Reconstruct the research logic

Read the question, theory, design, data-construction memo, codebook, prior code, and relevant method
notes. State the target quantity, population, comparison, main expectations, serious rivals, and the
evidence that would alter the argument. Do not run a conventional regression merely because the data
are rectangular.

### 2. Inspect the analytical sample

Verify the unit, keys, sample restrictions, time and geographic coverage, missingness, treatment or
exposure variation, outcome distributions, weights, and dependence structure. Reconcile the estimation
sample with the intended population and document consequential sample loss.

### 3. Learn from descriptive evidence

Examine distributions, cross-tabs, raw trends, maps, group comparisons, and measurement behavior before
fitting the main model. Use these results to detect coding errors, weak support, non-overlap, unusual
cases, temporal changes, or theoretical patterns the initial plan missed.

### 4. Estimate the primary analysis

Implement the design's target quantity and uncertainty rule. Report effect sizes or quantities in
substantively interpretable units, not only coefficients and p-values. Preserve the planned analysis
when it remains appropriate and explain deviations when the data reveal a better-founded choice.

For specialist designs such as DID, identify the design-specific assumptions, comparisons,
estimators, diagnostics, and sensitivity questions that need deeper treatment rather than reproducing
all design-specific details in the general analysis.

### 5. Diagnose, compare, and revise

Investigate the vulnerabilities most likely to change the conclusion: measurement alternatives,
sample support, functional form, dependence, influential cases, comparison definitions, timing,
missingness, multiplicity, and design-specific assumptions. Compare specifications because they answer
a reasoned question, not to find a favorable estimate.

When results disagree, determine whether the difference comes from a changed estimand, sample,
weighting, measurement, identifying assumption, or chance. Revise the analysis or narrow the claim.

### 6. Examine heterogeneity and mechanisms with discipline

Analyze heterogeneity when theory, design, or policy relevance gives it a reason. Distinguish planned
from exploratory subgroups and account for multiplicity. Treat mechanism evidence as a separate
inferential problem; an intermediate-outcome coefficient does not by itself establish a mechanism.

### 7. Synthesize the evidence

Judge how the full pattern bears on the theory and rivals, including null, anomalous, and inconvenient
results. State magnitude, uncertainty, robustness boundaries, external scope, and what cannot be
learned from the design. End with concrete revisions to the question, theory, measurement, design, or
next analysis.

## Confirmatory and Exploratory Work

Exploration is part of real research, not a failure. Label it honestly. Keep a visible distinction
between prespecified tests, justified deviations, exploratory discoveries, and post hoc explanations.
Do not suppress failed models or null results that materially affect interpretation.

## Computational practice

Use the project's established statistical language and conventions. Run the analysis afresh, inspect
warnings, and verify that reported results come from the current data and code. Discuss software only
when its behavior changes the inference.

## Lessons from practice

- When an estimate surprises, first inspect coding, sample composition, raw outcomes, and comparison
  support; only then consider a new substantive interpretation.
- When reasonable analyses disagree, trace the disagreement to estimands, samples, weights, periods,
  outcome scales, or assumptions instead of selecting the preferred coefficient.
- Let model checks change the analysis. A failed fit or predictive pattern is a reason to understand
  the data-generating process and revise, not merely a footnote to the original model.

Source on research practice:

- Andrew Gelman et al., “Bayesian Workflow”:
  https://sites.stat.columbia.edu/gelman/research/unpublished/Bayesian_Workflow_article.pdf

## Criteria for judgment

A persuasive analysis:

- is tied to a target quantity and substantive political question;
- begins with sample, measurement, and descriptive understanding;
- reports magnitude and uncertainty in interpretable terms;
- uses diagnostics to learn and revise;
- distinguishes estimand changes from robustness;
- separates confirmatory and exploratory evidence;
- retains null, conflicting, and anomalous results;
- examines mechanisms and heterogeneity only with a reasoned basis; and
- ends with bounded conclusions and a changed research judgment.
