---
name: study-design-builder
description: >
  Build and revise executable study designs for quantitative empirical political science. Use when
  translating a research problem and theory into a descriptive, associational, predictive, or causal
  design; defining population and sample; operationalizing constructs; choosing an estimand or target;
  developing a comparison and identification strategy; planning estimation, diagnostics, robustness,
  and scope; or assessing whether a proposed design is feasible. Triggers include "study design",
  "research design", "identification strategy", "pre-analysis plan", "研究设计", "识别策略",
  "变量测量", "实证策略".
---

# Study Design Builder

Turn a political-science question and theoretical argument into an executable empirical design. The
design should specify what will be learned, from which population and comparison, with which measures,
and under which assumptions. Contemporary causal inference is appropriate when the question and
evidence support it; many important studies remain descriptive, associational, predictive, or
measurement-oriented.

## Design memo

Set out the proposed study in a **Research Design Memo** or **Pre-Analysis Memo** that specifies:

1. research question, theoretical argument, mechanisms, rivals, and testable expectations;
2. inferential purpose: description, association, prediction, measurement, or causation;
3. target population, sampling frame, sample, unit of analysis, time, and setting;
4. constructs, operational measures, and evidence for measurement validity;
5. estimand or other target quantity;
6. treatment, exposure, outcome, comparison, and assignment or selection process when relevant;
7. identification assumptions and the institutional facts that make them plausible or doubtful;
8. data sources, linkage needs, missingness risks, and design feasibility;
9. estimator or analytic strategy, uncertainty, clustering or dependence, and weighting;
10. planned descriptive evidence and diagnostics;
11. heterogeneity, mechanisms, multiple outcomes, and exploratory analyses;
12. falsification, placebo, robustness, and sensitivity analyses;
13. principal threats, rival interpretations, scope conditions, and bounded claims; and
14. the design revisions made during the assessment.

## Developing the design

### 1. Reconstruct the inquiry

Read the concept memo, literature, institutional material, data descriptions, and prior analysis.
Clarify what the study wants to learn before discussing estimators. If the proposed outcome or
treatment does not match the theoretical construct, repair the question or measurement first.

### 2. Choose the inferential purpose

Decide whether the study's actual contribution is descriptive, associational, predictive,
measurement-oriented, or causal. Do not force every worthwhile political-science study into a causal
design. When the question is causal, define the relevant potential-outcome estimand and comparison;
a DAG is not required.

### 3. Build the design from political institutions and data generation

Describe how cases enter the sample, how exposure occurs, how outcomes are observed, and which
political processes could confound, mediate, anticipate, or spill over. Use institutional knowledge
to judge the comparison rather than choosing a design from its label.

### 4. Make measurement choices

Connect each construct to observable indicators. Examine content, construct, convergent,
discriminant, and predictive validity as appropriate. Discuss coding decisions, aggregation,
measurement error, differential reporting, and whether the measure behaves differently across
groups or time.

### 5. Specify analysis and learning strategy

Choose analyses that answer the stated target. Begin with sample and measurement descriptions, raw
patterns, and design diagnostics. Then specify estimation, uncertainty, heterogeneity, mechanisms,
and falsification or sensitivity checks. Separate prespecified tests from exploratory learning.

When a design family has substantial specialist knowledge, such as DID, state which design-specific
assumptions, comparisons, diagnostics, and sensitivity questions require deeper treatment instead of
compressing those questions into a general design memo.

### 6. Assess feasibility softly

For most observational research, judge feasibility from data coverage, relevant variation,
measurement quality, comparison support, timing, dependence, attrition, plausible precision, and the
number of informative cases or clusters. Formal power calculations or simulations are optional and
should be used only when their assumptions and design make them defensible.

### 7. Diagnose and revise

Identify the assumptions and threats most likely to change the answer. Redesign the sample,
measurement, comparison, outcome, time window, or claim when the evidence cannot sustain the initial
plan. State the chosen design and rejected alternatives with reasons.

## Lessons from practice

- Pilot the link most capable of killing the study—such as treatment timing, comparison support, or a
  disputed measure—before building the full analysis.
- When the available comparison cannot identify the original causal target, narrow the target,
  population, or claim before adding controls and complexity.
- Treat a failed diagnostic as information about the design. Revise the comparison, timing, measure,
  or question rather than accumulating nominal robustness checks.

Sources on research practice:

- Chris Blattman, “How to Pick a Dissertation Project”:
  https://chrisblattman.com/blog/2013/02/12/how-to-pick-a-dissertation-project-and-why-it-should-not-be-a-field-experiment/
- Andrew Gelman et al., “Bayesian Workflow”:
  https://sites.stat.columbia.edu/gelman/research/unpublished/Bayesian_Workflow_article.pdf

## Criteria for judgment

A defensible design:

- begins from a political question and theory rather than a fashionable estimator;
- aligns population, unit, measures, target, comparison, and claims;
- makes identifying assumptions concrete and institutionally interpretable;
- plans evidence capable of distinguishing mechanisms and rivals;
- treats descriptive evidence and measurement as part of inference;
- distinguishes prespecified and exploratory analyses;
- takes uncertainty, dependence, attrition, and multiple testing seriously;
- uses robustness and sensitivity to learn, not to accumulate check marks; and
- narrows the claim when the design cannot support the original ambition.
