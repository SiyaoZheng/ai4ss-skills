# Templates & Default Properties

> **Table of contents:** [1. Bug Report](#1-bug-report) · [2. Data Pipeline](#2-data-pipeline) · [3. Statistical Analysis](#3-statistical-analysis) · [4. Paper / Writing](#4-paper--writing) · [5. Literature Review](#5-literature-review) · [6. Infra / DevOps](#6-infra--devops) · [CLI field mapping](#cli-field-mapping) · [Label inventory](#label-inventory)

Templates are filled via `linearis issues create`. Use the markdown bodies below. **Every section must be filled** — if the user didn't provide enough context, infer what you can and mark uncertain parts with `[TO CONFIRM]`. Never leave a section as a bare placeholder.

## CLI field mapping

| Template field | `linearis` flag |
|---------------|-----------------|
| Priority | `--priority <1-4>` (1=Urgent 2=High 3=Medium 4=Low) |
| Estimate | `--estimate <n>` (1=XS 2=S 3=M 5=L 8=XL 13=XXL) |
| Labels | `--labels "label1,label2"` |
| Project | `--project "<name>"` |
| Assignee | `--assignee me` |
| Due date | `--due-date YYYY-MM-DD` |
| Status | `--status "<name>"` |
| Parent issue | `--parent-ticket TA-xxx` |
| Description | `--description "$(...)"` |

## Label inventory

| Label | Use |
|-------|-----|
| `bug` | Bug reports |
| `critical` | Critical severity |
| `data` | Data pipeline / ETL |
| `analysis` | Statistical modeling |
| `methodology` | Method design |
| `robustness` | Robustness / sensitivity |
| `writing` | Paper writing |
| `publication` | Publication logistics |
| `review` | R&R / revision |
| `reading` | Literature review |
| `R` | R code |
| `Python` | Python code |
| `infra` | CI/CD / DevOps / tooling |
| `Feature` | New feature |
| `Improvement` | Enhancement |

---

## 1. Bug Report

**Flags:** `--priority 2 --estimate 2 --labels "bug,critical"`

**Required:** Summary, Steps to Reproduce, Severity, Checklist

```markdown
## Summary
<!-- REQUIRED — one sentence: what broke, where, since when -->

## Impact
- What downstream work is blocked or corrupted?
- How many rows/files/users affected?
- Is this a regression (was it working before)? If so, when did it break?

## Steps to Reproduce
<!-- REQUIRED — numbered, each step reproducible by someone else -->
1.
2.
3.

## Expected Behavior
<!-- What should happen -->

## Actual Behavior
<!-- What actually happens. Include error messages, stack traces, screenshots -->

## Root Cause (if known)
<!-- Hypothesis or confirmed cause -->

## Environment
- Branch / commit:
- Data version / snapshot date:
- Python / R version:
- OS:

## Severity
<!-- REQUIRED — pick one -->
- [ ] Critical — blocks downstream pipeline or produces incorrect published results
- [ ] High — incorrect results but workaround exists
- [ ] Medium — degraded but non-blocking
- [ ] Low — cosmetic / edge case

## Proposed Fix
<!-- Brief approach if obvious -->

## Affected Components
- [ ] Data pipeline (Python)
- [ ] Analysis (R / Stata)
- [ ] Infra / CLI
- [ ] Docs

## Suggested Change Scope
<!-- Fill in actual repo paths. These are the files and downstream consumers to check. -->
- **Bug location** (file + function): `src/path/to/offending_file.py:function_name`
- **Tests to run before/after**: `pytest tests/test_xxx.py`, `Rscript tests/test_xxx.R`
- **Downstream stages that consume this output**: (list dependent pipeline steps or analysis scripts)
- **Docs to update**: `README.md`, `CHANGELOG.md`, inline docstrings

## Checklist
<!-- REQUIRED — concrete, verifiable items. Each item must be specific enough that someone can check it off -->
- [ ] Reproduce the bug on current data
- [ ] Identify root cause (code, data, or environment)
- [ ] Implement fix
- [ ] Verify fix on affected data / edge cases
- [ ] Add regression test to prevent recurrence
- [ ] Update downstream outputs if results changed
- [ ] Document the fix in commit message or changelog
```
---

## 2. Data Pipeline

**Flags:** `--priority 3 --estimate 5 --labels "data,Python"`

**Required:** Objective, Input source, Output destination, Checklist

```markdown
## Objective
<!-- REQUIRED — what does this pipeline step accomplish? Why is it needed? -->

## Background
<!-- Context: what problem does this solve, what came before it -->

## Input
- Source: <!-- REQUIRED — file path, DB table, API endpoint -->
- Format / size: (e.g., parquet, 2.5M rows, 45 columns)
- Key variables: (list the columns that matter most)
- Schema / data dictionary reference:

## Processing Steps
<!-- Numbered, each step described in enough detail for someone else to implement -->
1.
2.
3.

## Edge Cases & Error Handling
- What happens if input is empty or missing?
- What happens on malformed rows (encoding, nulls, outliers)?
- Are there known data quality issues to handle?

## Output
- Format: (parquet, CSV, RData, etc.)
- Destination path: <!-- REQUIRED -->
- Schema: (list output columns and types)
- Expected row count:
- Downstream dependencies: (what breaks if this output is wrong?)

## Performance
- Expected runtime:
- Memory requirements:
- Any parallelization or chunking needed?

## Suggested Change Scope
<!-- Fill in actual repo paths. Define what needs changing and what must NOT be touched. -->
- **Scripts to modify**: `src/python/stages/<stage_name>.py`, `src/python/data_loader.py`
- **New scripts to create** (if any):
- **Do NOT touch**: (list stages or utils that must remain unchanged)
- **Tests to run before/after**: `pytest tests/test_<stage>.py`
- **Downstream stages to re-run**: (list dependent pipeline steps in order)
- **Output files to regenerate**: `output/<dataset>.parquet`, `output/tables/<table>.csv`
- **Docs to update**: `README.md`, pipeline diagram, data dictionary

## Validation Checklist
<!-- REQUIRED — concrete, verifiable items -->
- [ ] Row count matches expectation (report N before/after)
- [ ] Column schema complete (all expected columns present, correct types)
- [ ] Key variables non-null rate >= threshold
- [ ] No silent truncation, encoding issues, or type coercion
- [ ] SHA256 / checksum verified (if applicable)
- [ ] Spot-check 5-10 rows manually against source
- [ ] Edge cases handled (empty input, malformed data, boundary values)
- [ ] Downstream pipeline stages still consume output correctly
```
---

## 3. Statistical Analysis

**Flags:** `--priority 3 --estimate 8 --labels "analysis,methodology,R"`

**Required:** Research Question, Checklist

```markdown
## Research Question
<!-- REQUIRED — the specific hypothesis or estimand -->

## Motivation
<!-- Why this analysis? What prior work or exploratory finding motivates it? -->

## Data
- Dataset: (name and version/date)
- Unit of analysis: (individual, paper, country-year, etc.)
- N: (sample size)
- Time range:
- Key inclusion/exclusion criteria:

## Method
- Model: (hIRT, fixed effects, DID, RDD, etc.)
- Identification strategy: (what variation is being exploited?)
- Estimator / package: (e.g., `lme4::lmer`, `fixest::feols`, `mirt::mirt`)

## Variables
- DV: (dependent variable — operationalization, source, range)
- IV: (independent variable of interest)
- Controls: (list each and why it's included)
- Fixed effects / clustering:
- Weights: (if any)

## Robustness Checks
- [ ] Alternative specifications:
- [ ] Sensitivity to outliers / influential observations
- [ ] Subgroup heterogeneity:
- [ ] Placebo / falsification test:

## Expected Output
- Tables: (specify which tables, e.g., Table 2 main results, Table A3 robustness)
- Figures: (specify which figures)
- Model objects to save: (`.rds` paths)

## Software & Reproducibility
- R/Python version:
- Key packages and versions:
- Script entry point:
- Random seed:

## Suggested Change Scope
<!-- Fill in actual repo paths. Define what needs changing and what must NOT be touched. -->
- **Analysis script**: `src/R/<analysis_name>.R` or `analysis/<notebook>.Rmd`
- **Data prep dependency**: `src/python/stages/<stage>.py` (re-run if input data changed)
- **Do NOT touch**: (list other analysis scripts that should remain unchanged)
- **Tests to run before/after**: `Rscript tests/test_<analysis>.R`
- **Output files to regenerate**: `output/tables/<table>.tex`, `output/figures/<figure>.png`
- **Bib / references to update**: `writing/refs.bib`
- **Docs to update**: `README.md`, methods section of manuscript

## Publication Status
- Target journal:
- Current stage: [ ] Exploratory [ ] Draft [ ] Submitted [ ] R&R [ ] Accepted

## Checklist
<!-- REQUIRED — concrete, verifiable items. Each item must correspond to an actual step in the analysis -->
- [ ] Prepare analysis dataset (apply inclusion/exclusion, handle missingness)
- [ ] Run descriptive statistics (summary table, distributions)
- [ ] Run main model specification
- [ ] Check convergence / diagnostics
- [ ] Generate main results table
- [ ] Run robustness checks (list each)
- [ ] Generate robustness tables/figures
- [ ] Write interpretation of results
- [ ] Commit script and output to repo
- [ ] Update manuscript text with new results
```
---

## 4. Paper / Writing

**Flags:** `--priority 3 --estimate 13 --labels "writing,publication"`

**Required:** Task Type, Target Journal, Checklist

```markdown
## Task Type
<!-- REQUIRED — pick one or more -->
- [ ] First draft
- [ ] Revision / R&R response
- [ ] Figures & tables
- [ ] Appendix / supplementary materials
- [ ] Formatting for submission
- [ ] Proofreading / language editing

## Target Journal & Requirements
<!-- REQUIRED -->
- Journal name:
- Word limit:
- Figure/table limit:
- Reference style:
- Submission format: (LaTeX, Word, etc.)
- Special requirements: (data availability, ethics statement, etc.)

## Authors
- Lead:
- Co-authors:
- Who needs to review before submission?

## Scope
- Sections to write/modify:
- Figures to create/update:
- Tables to create/update:
- Appendix sections:

## Current Status
<!-- What's done, what's remaining -->

## Related Issues
<!-- Link to analysis tasks, data tasks, lit review tasks that feed into this -->

## Suggested Change Scope
<!-- Fill in actual repo paths. Define what needs changing and what must NOT be touched. -->
- **Manuscript file**: `writing/<manuscript>.tex` or `.docx` or `.Rmd`
- **Figure scripts to re-run** (if updating figures): `src/R/fig_<name>.R`
- **Table scripts to re-run** (if updating tables): `src/R/tab_<name>.R`
- **Do NOT change**: (list sections/figures/tables that are locked)
- **Reference file**: `writing/refs.bib`
- **Style / template file**: `writing/<journal>.cls` or `.csl`
- **Cover letter**: `writing/cover_letter.tex` or `.docx`

## Deadline
- Internal draft deadline:
- Submission deadline:

## Checklist
<!-- REQUIRED — concrete, verifiable items -->
- [ ] Outline/structure approved
- [ ] [Section 1] drafted
- [ ] [Section 2] drafted
- [ ] [Section N] drafted
- [ ] All figures finalized (list each)
- [ ] All tables finalized (list each)
- [ ] References formatted
- [ ] Appendix complete
- [ ] Word count within journal limit
- [ ] Format check against journal guidelines
- [ ] Co-author review
- [ ] Final proofread
- [ ] Data availability statement written
- [ ] Cover letter drafted (if submission)
- [ ] Submitted / uploaded
```
---

## 5. Literature Review

**Flags:** `--priority 4 --estimate 3 --labels "reading"`

**Required:** Topic / Keywords, Checklist

```markdown
## Topic / Keywords
<!-- REQUIRED — the specific research area or question being surveyed -->

## Purpose
<!-- Why this lit review? Gap identification, positioning a paper, course prep, etc. -->

## Search Strategy
- Databases: [ ] arXiv [ ] Google Scholar [ ] PubMed [ ] Wanfang [ ] CNKI [ ] Web of Science [ ] Scopus
- Date range:
- Query / search string:
- Inclusion criteria:
- Exclusion criteria:

## Reading Log
<!-- Each paper gets a row. Fill as you go. -->
| # | Paper (APA) | Key Finding | Method | Sample | Relevance (1-5) | Notes |
|---|------------|------------|--------|--------|-----------------|-------|
| 1 |            |            |        |        |                 |       |

## Thematic Map
<!-- As you read, cluster papers into themes -->
### Theme 1:
- Papers:
- Core argument:

### Theme 2:
- Papers:
- Core argument:

## Synthesis
- What's the consensus?
- What's contested?
- Gap this work fills:
- How this work differs from closest papers:

## Key Papers to Cite
<!-- Final list of must-cite references -->

## Suggested Change Scope
<!-- Fill in actual repo paths. Define what needs changing and what must NOT be touched. -->
- **Bibliography file**: `writing/refs.bib`
- **Reading notes location**: `reading/<topic>/` or Zotero collection
- **Manuscript sections to update**: (which sections will incorporate this lit review)
- **Do NOT change**: (existing citations that are settled)
- **Lit review output doc**: `writing/lit_review_<topic>.md` (if writing a standalone review)

## Checklist
<!-- REQUIRED — concrete, verifiable items -->
- [ ] Define search query and run in all target databases
- [ ] Screen titles/abstracts (report N retained / N excluded)
- [ ] Read and annotate retained papers
- [ ] Populate reading log with all retained papers
- [ ] Identify and name thematic clusters
- [ ] Write synthesis (gap, contribution, positioning)
- [ ] Extract must-cite reference list
- [ ] Update manuscript bibliography
```
---

## 6. Infra / DevOps

**Flags:** `--priority 3 --estimate 5 --labels "infra"`

**Required:** Context/Problem, Affected Components, Checklist

```markdown
## Context
<!-- REQUIRED — what's the problem or need? Why now? -->

## Proposed Approach
<!-- What change are we making? What's the alternative considered and rejected? -->

## Affected Components
<!-- REQUIRED — check all that apply -->
- [ ] CI/CD (GitHub Actions, build pipeline)
- [ ] Environment / dependencies (Python, R, system packages)
- [ ] Data storage (file paths, DB, S3/OSS)
- [ ] CLI / scripts (entry points, automation)
- [ ] Documentation (README, CLAUDE.md, wiki)
- [ ] Monitoring / logging
- [ ] Security / access control

## Scope & Non-Scope
- In scope:
- Out of scope (for this issue):

## Migration / Rollout Plan
- [ ] Backward compatible? (yes / no — if no, what's the migration path?)
- [ ] Affected downstream repos or pipelines:
- [ ] Rollback strategy if it breaks:

## Dependencies
- Prerequisite issues / PRs:
- External dependencies (new packages, API keys, service accounts):

## Suggested Change Scope
<!-- Fill in actual repo paths. Define what needs changing and what must NOT be touched. -->
- **Config files to modify**: `.github/workflows/<name>.yml`, `pyproject.toml`, `renv.lock`, `package.json`
- **Scripts to modify**: `scripts/<name>.sh`, `Makefile`, CLI entry points
- **Do NOT touch**: (list configs or scripts that must remain unchanged)
- **Affected repos** (if cross-repo): `repo-a`, `repo-b`
- **Tests to run before/after**: `pytest`, `npm test`, `Rscript test-*.R`
- **Docs to update**: `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.env.example`

## Verification
<!-- REQUIRED — concrete, verifiable items -->
- [ ] Tests pass (`pytest` / `Rscript test-*.R` / etc.)
- [ ] Documentation updated (README, inline comments, changelog)
- [ ] Existing pipelines / workflows unaffected (verified by running)
- [ ] Backward compatible (old scripts still work) OR migration guide written
- [ ] New behavior verified end-to-end on a test case
- [ ] Peer reviewed (another person signed off)
```
