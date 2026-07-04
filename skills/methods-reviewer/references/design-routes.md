# Design Routes

Choose the audit path by design family. If the design is unclear, start with General Route.

## Contents

- General Route
- OLS / Panel Regression
- DID / Event Study
- IV
- RD
- Synthetic Control / Matching
- RCT / Experiments
- Survey / Weights
- Text-As-Data / LLM Extraction
- Spatial / Network Spillovers
- Robustness And Reporting

## General Route

Ask:

1. What is the unit of observation?
2. What is the estimand or target comparison?
3. What creates variation in treatment or exposure?
4. What are the key outcomes?
5. What sample restrictions matter?
6. What assumptions identify the estimate?
7. What outputs claim to support the conclusion?

Evidence to inspect:

- research design note;
- data construction scripts;
- model scripts;
- logs;
- tables and figures;
- manuscript or slides.

## OLS / Panel Regression

Check:

- outcome scale and transformation;
- treatment/exposure timing;
- whether controls are pre-treatment or post-treatment;
- fixed effects relative to variation of interest;
- clustering level;
- sample selection;
- leverage and influential observations when relevant.

Common issues:

- treatment absorbed by fixed effects;
- standard errors clustered too low;
- post-treatment controls included;
- interpreting association as causation;
- dropping rows with missing controls without reporting.

## DID / Event Study

Route DID-specific deep analysis to `/did-expert` when available.

Minimum review:

- treatment timing and comparison group;
- balanced vs unbalanced panel;
- never-treated vs not-yet-treated controls;
- event-study omitted period;
- pre-treatment coefficients and uncertainty;
- staggered treatment estimator choice;
- clustering and few-cluster concerns;
- anticipation and spillovers.

## IV

Check:

- instrument relevance and first stage;
- exclusion restriction argument;
- monotonicity when LATE is claimed;
- weak instrument diagnostics;
- same sample across first and second stage;
- clustering level;
- whether controls violate the instrument logic.

Red flags:

- strong first stage but no exclusion argument;
- interpreting LATE as ATE;
- multiple instruments without overidentification discussion;
- generated instruments not documented.

Decision route:

- If first-stage evidence is missing, output `status=reporting_gap`, `severity=P1`, and `next_action=add first-stage table and weak-IV diagnostic`.
- If exclusion restriction is only asserted, output `status=needs_author`, `severity=P1`, and ask the author to state the substantive exclusion argument and threats.
- If the manuscript claims ATE from a local instrument, output `status=overclaim`, `severity=P1`, and route the claim to `academic-writing-scaffold` as an estimand wording risk.

## RD

Check:

- running variable and cutoff;
- manipulation or sorting evidence;
- bandwidth choice;
- polynomial order;
- local balance;
- donut or sensitivity checks;
- outcome and covariate continuity;
- graph binning and scale.

Red flags:

- global polynomial as main evidence;
- no density/manipulation check;
- bandwidth chosen after looking at results;
- observations far from cutoff drive result.

Decision route:

- If running variable, cutoff, or bandwidth is absent, output `status=reporting_gap`, `severity=P0`, and stop before result claims.
- If manipulation checks are missing, output `status=serious_risk`, `severity=P1`, and `next_action=add density and covariate-balance diagnostics`.
- If only global polynomial evidence is shown, output `status=serious_risk`, `severity=P1`, and request local-linear sensitivity.

## Synthetic Control / Matrix Completion

Check:

- treated unit count;
- donor pool definition;
- pre-treatment fit;
- predictor balance;
- placebo/permutation inference;
- spillovers to donor pool;
- post-treatment window and shocks;
- missing data handling.

Red flags:

- poor pre-fit but strong causal claim;
- donor pool includes indirectly treated units;
- no placebo distribution;
- outcome scale changes across units.

## Descriptive / Measurement Papers

Check:

- construct validity;
- measurement error;
- source coverage;
- denominator;
- aggregation;
- uncertainty or sampling frame;
- external validity.

Red flags:

- descriptive trend described causally;
- denominator changes over time;
- extracted text variables lack validation.

## Qualitative / Mixed Methods

Check:

- case selection;
- data source provenance;
- coding scheme;
- intercoder or audit process if claimed;
- triangulation;
- negative cases;
- boundary of inference.

Red flags:

- illustrative quotes presented as prevalence evidence;
- AI-coded qualitative categories with no human audit;
- unclear sampling frame.

## RCT / Experiments

Check:

- randomization unit and blocking or stratification;
- balance on pre-treatment covariates;
- attrition by treatment arm;
- noncompliance, take-up, and spillovers;
- pre-registered outcomes or analysis plan when claimed;
- multiple testing adjustments or family definitions;
- clustering when randomization is at group level;
- whether treatment materials and timing are documented.

Red flags:

- analysis ignores clustered randomization;
- attrition differs by arm without bounds or sensitivity checks;
- outcome switching is hidden;
- subgroup findings are presented as primary without pre-specification.

Decision route:

- If randomization unit and analysis clustering differ, output `status=serious_risk`, `severity=P1`, and request cluster-appropriate inference.
- If attrition is arm-specific and unreported, output `status=confirmed_bug` when visible in data, otherwise `status=serious_risk`.
- If outcome switching is suspected, output `status=needs_author` and ask for pre-analysis-plan or registration evidence before any claim wording.

## Survey / Weights

Check:

- sampling frame and response rate;
- design weights, post-stratification, and population targets;
- item nonresponse and imputation rules;
- survey mode and timing;
- whether standard errors account for survey design;
- wording changes across waves;
- construct validity for indices or scales.

Red flags:

- weighted and unweighted estimates are mixed without labels;
- weights are treated as ordinary controls;
- convenience samples are generalized to a target population;
- missingness is silently listwise-deleted for key outcomes.

Decision route:

- If weights are used but target population is unstated, output `status=reporting_gap`, `severity=P2`, and request a weight note.
- If survey design affects inference but SEs ignore it, output `status=serious_risk`, `severity=P1`, and request design-aware SEs or a limitation.
- If convenience samples are generalized, output `status=overclaim`, `severity=P1`, and route wording to `.aiss` bounded claim declarations.

## Text-As-Data / LLM Extraction

Check:

- source corpus provenance and coverage;
- document inclusion/exclusion rules;
- annotation codebook or extraction prompt version;
- train/test split or validation sample;
- human audit rate and adjudication procedure;
- precision, recall, agreement, or calibration metrics;
- leakage from outcome labels, treatment labels, future text, or prompts;
- low-confidence routing and manual-review file.

Red flags:

- LLM-coded variables enter analysis with no validation sample;
- prompts include outcome or treatment information that could leak labels;
- examples are selected after seeing results;
- ambiguous extractions are forced into binary variables;
- no record of model/tool version.

Decision route:

- If no validation sample exists, output `status=serious_risk`, `severity=P1`, and require a human-reviewed validation file before analysis claims.
- If ambiguous extractions are coerced into zero/one labels, output `status=confirmed_bug`, `severity=P0`, and route uncertain rows to `needs_review`.
- If model/tool version or prompt is missing, output `status=reporting_gap`, `severity=P2`, and require provenance before sharing.

## Spatial / Network Spillovers

Check:

- spatial or network unit definition;
- exposure mapping and distance or adjacency rule;
- interference assumptions;
- direct vs indirect treatment separation;
- clustered or spatially robust inference;
- boundary effects and isolated units;
- placebo exposure or permutation checks;
- multiple testing across distance bands or network radii.

Red flags:

- control units plausibly exposed through neighbors;
- spillover claims use only direct-treatment regressions;
- distance bands are chosen after results;
- maps and regressions use inconsistent geographic units.
