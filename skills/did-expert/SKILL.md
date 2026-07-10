---
name: did-expert
description: >
  Provide deep, study-specific expertise for difference-in-differences and related panel causal
  designs. Use when treatment timing, comparison groups, staggered adoption, heterogeneous effects,
  event studies, treatment reversals, continuous exposure, anticipation, spillovers, parallel trends,
  estimator choice, inference, or sensitivity are central. Triggers include "DID", "difference in
  differences", "event study", "staggered treatment", "parallel trends", "TWFE", "HonestDiD",
  "双重差分", "事件研究", "平行趋势", "分期处理".
---

# DID Expert

Evaluate the DID-specific methodological questions raised by a concrete proposed or implemented study.
The analysis begins with the intervention, exposure process, estimand, and identifying comparisons;
estimator choice follows from those features.

## DID assessment

Set out the assessment in a **DID Methods Memo** covering:

1. the political intervention, exposure process, institutional setting, and treatment timing;
2. the causal estimand and population to which it refers;
3. admissible 2x2 comparisons and the units or periods actually identifying the effect;
4. the relevant parallel-trends and no-anticipation assumptions;
5. spillovers, interference, concurrent policies, attrition, and treatment reversals;
6. treatment-effect heterogeneity and event-time composition;
7. estimator and aggregation choices tied to the estimand;
8. uncertainty and dependence;
9. raw-pattern, diagnostic, falsification, and sensitivity evidence;
10. disagreements across estimators or samples and what causes them; and
11. required design, analysis, or interpretation revisions.

## Evaluating the design

### 1. Begin with the intervention, not the package

Reconstruct who becomes treated, when, why, with what intensity, whether treatment is absorbing, and
which political or administrative process generates timing. Inspect policy text, implementation rules,
institutional history, and contemporaneous events. A treatment indicator is not a design.

### 2. Define the estimand and comparisons

State the potential-outcome contrast of interest: group-time ATT, event-time effect, policy-relevant
aggregate, dose response, switch-on/off effect, or another justified quantity. Identify which cohorts,
periods, and control units contribute. Decide whether never-treated, not-yet-treated, or another group
can plausibly supply the counterfactual.

### 3. Inspect data support

Plot raw outcomes and treatment timing; examine cohort sizes, observation windows, gaps, attrition,
support for covariates, and composition at each event time. Diagnose whether long-run effects are
identified only by early cohorts or a changing sample.

### 4. Assess identifying assumptions substantively

Parallel trends is a claim about untreated potential outcomes, not a passing pre-trend test. Use theory,
institutional facts, raw patterns, covariate behavior, alternative outcomes, and policy timing to assess
its plausibility. Examine anticipation, spillovers, endogenous timing, simultaneous reforms, and
differential measurement.

### 5. Choose estimators by target and design

Use simple DID or TWFE when their assumptions and comparison structure fit. With staggered adoption and
heterogeneous effects, prefer methods that identify transparent group-time or cohort-specific effects
and aggregate them deliberately. For non-absorbing, continuous, repeated-cross-section, imbalanced, or
synthetic-comparison settings, choose methods whose estimands and assumptions match those features.

Do not select an estimator because its package is fashionable. Explain how each choice changes the
target, comparison weights, covariate adjustment, or sample.

### 6. Diagnose and stress-test

Use event studies as descriptive and diagnostic evidence, not proof of parallel trends. Consider
pre-treatment equivalence or sensitivity approaches, placebo outcomes and dates, alternative control
groups or windows, leave-one-cohort or leave-one-cluster checks, treatment-timing falsification,
randomization inference when assignment supports it, and design-appropriate sensitivity bounds.

Match uncertainty to the assignment and dependence structure. Examine the number, size, and leverage of
clusters rather than relying on a mechanical threshold. Address multiple outcomes or subgroup searches
when they affect interpretation.

### 7. Interpret estimator disagreement

When estimates differ, trace the difference to target parameters, comparison sets, weights, cohorts,
time horizons, samples, nuisance models, or assumptions. Do not label agreement as robustness or
disagreement as failure without explaining what each estimator learns.

### 8. Revise the study

Recommend a concrete change to treatment definition, sample, event window, control group, aggregation,
estimator, diagnostic plan, or causal claim. State what remains unidentified.

## Computational practice

Keep implementation subordinate to the estimand, comparisons, and assumptions. Follow the project's
existing R practice and consult current documentation for the selected estimator; software choice
cannot resolve an unidentified or poorly supported comparison.

## Criteria for judgment

- Institutional context justifies treatment and comparison choices.
- The estimand is explicit and matches aggregation.
- Staggered timing and heterogeneous effects are handled transparently.
- Pre-treatment evidence is interpreted with appropriate humility.
- Event-time composition, anticipation, spillovers, and concurrent policies are assessed.
- Inference reflects the actual dependence and effective information.
- Sensitivity analyses target plausible violations.
- The memo changes the design, analysis, or claim rather than merely naming packages.

## Methodological notes

- `references/pre-analysis.md` — DID-specific data and treatment inspection.
- `references/estimators.md` — estimator families and their assumptions.
- `references/diagnostics.md` — diagnostics, falsification, sensitivity, and inference.
- `references/implementation.md` — R implementation patterns after the design is chosen.
