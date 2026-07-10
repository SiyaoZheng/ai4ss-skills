---
name: research-data-builder
description: >
  Turn raw political and social data into substantively defensible, analysis-ready research data.
  Use for cleaning, harmonization, panel construction, record linkage, sample construction, variable
  operationalization, survey preparation, text-to-structure extraction, missing-data assessment,
  measurement validation, and reproducible construction of analytical data. Triggers include "build analysis data",
  "clean data", "merge panel", "construct variables", "sample construction", "数据清洗",
  "样本构造", "变量构造", "面板数据", "数据合并".
---

# Research Data Builder

Build analysis-ready data whose observations, links, sample, and variables correspond to the inquiry.
Coding and file management serve those substantive decisions.

## Dataset and construction record

The work should leave:

1. an analysis-ready dataset or other usable empirical object;
2. reproducible code that rebuilds it from preserved source materials; and
3. a **Data Construction Memo** explaining the unit, sample, linkage, operationalization,
   measurement evidence, missingness, important exclusions, validation findings, and design changes.

Sample-flow, merge, missingness, and provenance tables may be used when they clarify consequential
construction choices.

## Principles

- Never overwrite raw data.
- Inspect file structures, codebooks, labels, units, encodings, and source documentation before transforming.
- Keep source, interim, and analysis data distinguishable.
- Make consequential transformations deterministic and rerunnable.
- Protect confidential or restricted data and honor source terms.
- Treat row loss, unmatched records, and changed variable meanings as research findings.

## Building the data

### 1. Reconstruct the intended empirical object

Read the research question, design memo, source documentation, and existing scripts. State the unit of
observation, target population, time and geographic scope, key constructs, and required linkage. Check
whether the requested data object can actually represent them.

### 2. Profile source materials

Inspect files and tables directly. Establish row counts, keys, duplicates, coverage, distributions,
missingness, coding changes, and suspicious values. Compare codebook definitions with observed data.
Use spot checks against original records or official aggregates when possible.

### 3. Define the sample

Make inclusion, exclusion, temporal, geographic, and complete-case decisions explicit. Examine how
each decision changes the population represented by the data. Preserve excluded and ambiguous cases
when they are useful for diagnosis.

### 4. Harmonize and link

Standardize identifiers, units, categories, dates, boundaries, and definitions while retaining the
source values needed to audit the transformation. Diagnose duplicate keys and many-to-many matches.
Study matched and unmatched records substantively; do not report only a match rate.

### 5. Operationalize constructs

Build variables from theoretical definitions rather than convenient columns. Document source fields,
coding rules, aggregation, timing, transformations, and expected direction. Examine face, content,
construct, convergent, discriminant, or predictive validity as appropriate. Check whether measurement
quality differs across groups, places, or periods.

### 6. Treat missingness and extraction uncertainty as evidence

Describe where and why values are absent. Compare observed and missing cases, investigate whether
missingness is related to treatment, outcome, institution, or time, and preserve uncertainty flags for
record linkage or text extraction. Do not silently convert unknown values into zeros.

### 7. Validate the finished data

Rebuild from a clean process. Check keys, ranges, sample counts, coverage, impossible combinations,
known benchmarks, constructed-variable logic, and selected source records. Compare the finished sample
with the population and design it is meant to represent.

### 8. Revise the research design when necessary

If measurement, coverage, linkage, or selection problems undermine the proposed study, state how the
question, estimand, sample, comparison, or interpretation must change. Do not declare data ready merely
because the code runs without error.

## Lessons from practice

- Trace at least one decisive reported quantity from the original source through parsing, joins,
  recodes, exclusions, and aggregation. A reproducible final script is not enough if that chain is
  substantively wrong.
- Inspect unmatched records, boundary changes, duplicate links, influential units, and ambiguous codes
  because consequential errors are rarely distributed uniformly.
- When the source cannot support the intended construct, preserve the source's actual meaning and
  revise the measure or claim instead of filling the gap with convenient data engineering.

Source on research practice:

- R. Michael Alvarez and Simon Heuberger, “How (Not) to Reproduce”:
  https://www.cambridge.org/core/product/identifier/S1049096521001062/type/journal_article

## Criteria for judgment

A defensible dataset:

- can be rebuilt without manual hidden steps;
- preserves raw materials and consequential decisions;
- has a defensible unit and sample;
- makes linkage failures and row loss interpretable;
- ties variables to political-science constructs;
- investigates measurement validity and missingness;
- exposes rather than smooths over ambiguous cases; and
- leaves the researcher with usable data and a revised understanding of what can be learned.

Follow the project's existing R or Python practice. Discuss technical details only where they bear on
the validity, provenance, or reproducibility of the research data.
