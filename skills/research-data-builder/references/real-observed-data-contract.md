# Real Observed Data Contract

Use this reference whenever a data build feeds an automatic harness, manuscript
draft, table, figure, or claim.

## Only Valid Empirical Inputs

Valid empirical data must be real observed records from public or authorized
sources:

- survey microdata, codebooks, extracts, or published aggregate tables;
- administrative records, registries, gazetteers, facility lists, budgets,
  election returns, census or ACS tables, and official statistics;
- web pages, PDFs, reports, filings, policy texts, press releases, and archive
  documents when coded with source locator, snippet, access date, and rule;
- verified secondary datasets with documented source lineage.

Every analysis-facing row or coded cell must preserve enough provenance for a
reader to understand where it came from: source name, URL or path, access date,
table/page/section when applicable, extraction or merge rule, and exclusions.

## Forbidden Substitutes

Do not create empirical rows, units, cells, outcomes, exposures, covariates,
tables, figures, or estimates from:

- synthetic, simulated, hypothetical, illustrative, toy, or generated data;
- random draws, Monte Carlo data, DGPs, calibrated pseudo-populations, or
  benchmark-generated microdata;
- published coefficients, parameter benchmarks, correlations, effect sizes, or
  literature summary statistics converted into substitute observations;
- LLM-imagined cases, estimated counts without source records, or example rows.

Published parameters can be used only for theory, measurement discussion,
sample-size or power reasoning, and comparison against real observed estimates.
They cannot become the analysis sample.

## Automatic Repair Rule

When the planned source cannot be acquired, the harness must automatically
switch to another real observed route rather than generate substitute data.
Allowed repairs include:

- change the unit of analysis to an observed aggregate source;
- change geography or period to match available public data;
- replace unavailable microdata with public aggregate tables that still answer a
  bounded version of the inquiry;
- hand-code observed facts from public pages with locators;
- narrow the claim to what the real observed data can support.

If no real observed data route supports the original exact inquiry, select the
nearest route that still supports a publication-level draft PDF and disclose the
route change. Do not produce a synthetic fallback.

## Handoff Evidence

Before handing to analysis, provide:

- `data_source`: source dataset, URL, or file path;
- `row_source_provenance`: columns or side artifacts that link rows/cells to
  observed sources;
- `data_transparency_status`: open, restricted, confidential, unavailable, or
  requires_author_disclosure;
- `forbidden_substitute_check`: pass only when scripts and outputs contain no
  generated-data substitutes;
- `next_skill_route`: usually `research-analysis-runner`.
