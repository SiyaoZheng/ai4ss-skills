---
name: research-data-builder
description: >
  Social-science data engineering skill for turning raw files into auditable analysis samples.
  Use when building or repairing data pipelines, panel datasets, merges, variable construction,
  sample-flow reports, missingness audits, text-to-structure extraction, or reproducible scripts
  for empirical research. Triggers: "build analysis sample", "data cleaning", "merge audit",
  "panel construction", "sample flow", "variable dictionary", "raw to analysis", "text extraction",
  "do not overwrite raw data", "reproducible data pipeline", "数据清洗", "样本构造", "合并检查",
  "变量构造", "样本流".
---

# Research Data Builder

Build research datasets as an auditable workflow, not as one-off data wrangling. The default output is a runnable pipeline plus row-count, merge, missingness, and provenance evidence that another researcher can inspect.

## Scholar Workbench

This skill answers: "数据怎么来的，样本怎么变的？" Its value is not cleaning data faster; it is making row loss, merge ambiguity, variable construction, and extraction uncertainty visible before any result is interpreted.

## Core Rule

Never overwrite raw data. Read project instructions first, write scripts and derived data to explicit output paths, and make every sample-size change explainable.

## Runtime Failure Guardrails

- Discover files with `Path.exists()`, `Path.glob()`, `rg --files`, or quoted shell patterns before reading them. Run `scripts/check_runtime_contract.py` for path/glob checks; do not let unquoted zsh globs decide whether data exists.
- Run dependency preflights before long data work: import required Python modules and load required R packages in the same interpreter that will run the pipeline.
- Inspect schemas before selecting or renaming columns. If a requested variable is absent, write the missing-column result into the audit artifact and stop or repair the data step.
- Run project scripts from the project root or set their source path explicitly so local imports such as `config` resolve correctly.
- Every nonzero command exit is a pipeline finding. Record command, error, root cause, fix, and rerun status before saying the data are ready.

## Methodology Foundation

This skill realizes the `Data strategy` part of the MIDA spine. It makes sampling, source selection, measurement, extraction, linkage, transformation, missingness, and provenance inspectable before any answer strategy or claim depends on the data.

The skill must preserve upstream `Model` and `Inquiry` fields when present, but it does not choose the estimand, target quantity, or identification strategy.

When an upstream `.aiss` model exists, data artifacts must preserve `ai4ss_model_path`, relevant concept or bridge ids, and check status. Data work can repair the empirical bridge evidence, but it must not silently rewrite the model.

## Workflow Contract

- Upstream inputs: `study_design_brief.md`, `study_design_declaration.csv`, `research_model.aiss`, route cards, raw data, source files, variable dictionaries, extraction rules, DDI metadata, or an analysis plan's data requirements.
- Produces: derived data, runnable scripts, logs, `sample_flow.csv`, `merge_audit.csv`, and `variable_provenance.csv` when applicable; for survey cleaning, `ddi-metadata.yaml`, `cleaning_contract`, clean data, cleaning script, and processing event audit when routed through `ai4ss-skills`.
- Handoff fields: `route_id`, `design_source`, `target_inquiry`, `data_source`, `unit_of_analysis`, `sample_restrictions`, `constructed_variables`, `known_data_gaps`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `validation_commands`, `next_skill_route`.
- Downstream routes: `research-analysis-runner`, `methods-reviewer`, `academic-writing-scaffold`, `research-slides-builder`, `study-design-builder`, or `ask_author`.

## Routing Boundaries

Use this skill for confirmed data and pipeline work. Do not use it to choose the research design; hand ambiguous design choices to `study-design-builder`. Do not use it to run the first analysis package unless the task is only data feasibility; hand analysis execution to `research-analysis-runner`. Do not use it to certify empirical identification or result claims; hand those checks to `methods-reviewer`. Do not use it to write paper text; hand verified audit artifacts to `academic-writing-scaffold`.

## Workflow

```
Step -1: Orient
-> Read AGENTS.md, README, docs/research_design.*, variable dictionaries, and the file tree.
-> Identify raw, interim, analysis, scripts, output, and log directories.
-> If boundaries conflict, stop and ask for the project source of truth.

Step 0: Classify the task
-> New analysis sample: follow references/pipeline.md.
-> Merge or matching repair: follow references/audit-schema.md before changing code.
-> Text-to-structure extraction: require source snippets, extraction rules, confidence flags, and manual-review outputs.
-> Survey/codebook cleaning: when `.dta`, `.sav`, codebook PDF/docx, or `ddi-metadata.yaml` is central, route through the `ai4ss-skills` DDI harness: `codebook-parse` -> `cleaning-contract` -> `cleaning-execute`.
-> Existing pipeline bug: inspect logs, data columns, and the smallest failing step before editing.

Step 1: Plan before edits
-> List files to read, files to modify, expected outputs, and validation checks.
-> Do not touch raw files, credentials, or confidential folders.
-> Run `scripts/check_runtime_contract.py --cwd <project> --path <input-or-quoted-glob> --data <input-data> --required-columns <cols> --key-columns <keys> --python-import <module> --r-package <pkg>` for the checks that match the pipeline step.

Step 2: Build in stages
-> Preserve raw -> interim -> analysis separation.
-> Add deterministic scripts under scripts/.
-> Put tables, figures, logs, and audits under output/ or docs/.

Step 3: Validate
-> Report row counts, unique IDs, year ranges, duplicates, missingness, merge rates, and constructed-variable rules.
-> Save audit artifacts, not only chat summaries.
-> Re-run the exact data-building command from a clean shell after code changes; do not validate stale derived files.
-> Update an AI-use ledger when AI-assisted extraction or transformation affects a manuscript, shared dataset, or teaching artifact.
```

## Required Outputs

For a full pipeline, produce or update:

- A runnable script such as `scripts/10_build_panel.R` or `scripts/merge_panel.py`.
- A derived data file under `data/interim/` or `data/analysis/`.
- `output/logs/<step>.log` with command, timestamp, package versions when relevant, and success or failure.
- A failure log entry for every nonzero run that affected the current data state.
- `output/audit/sample_flow.csv` or `.md`.
- `output/audit/merge_audit.csv` when any merge or match occurs.
- `docs/changelog.md` entry when files change.
- For survey cleaning through `ai4ss-skills`: `ddi-metadata.yaml`, the declared `cleaning_contract`, `<stem>-cleaning.R`, `<stem>-clean.csv`, and a processing event audit.

## Script Utilities

- Run `scripts/check_runtime_contract.py --cwd <project> ...` to check files/globs, Python imports, R packages, data schema, duplicate CSV keys, expected outputs, and output freshness. Quote shell globs.
- Run `scripts/validate_data_audits.py sample_flow <path>` to check sample-flow columns.
- Run `scripts/validate_data_audits.py merge_audit <path>` to check merge-audit columns.
- Run `scripts/validate_data_audits.py variable_provenance <path>` to check provenance columns.
- Run `scripts/validate_ai4ss_model.py <path-to-research_model.aiss>` when data artifacts depend on a declared AI4SS model.

## Quality Bar

- State the unit of observation before constructing variables.
- Make treatment timing, post indicators, and sample restrictions visible.
- Keep unmatched records and low-confidence extracted records in separate review files.
- Treat row loss as a finding to explain, not as cleanup noise.
- Prefer scripts that can be rerun from a clean checkout.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [pipeline.md](references/pipeline.md) | Stage-by-stage data pipeline pattern, file layout, and validation checks | Starting or reorganizing a data workflow |
| [audit-schema.md](references/audit-schema.md) | Schemas for sample flow, merge audit, variable provenance, and changelog entries | Designing outputs or reviewing whether evidence is sufficient |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for project intake, merge repair, text extraction, and pipeline debugging | Turning a user request into an agent task |
| [quality-gates.md](references/quality-gates.md) | Stop/go checks, failure modes, and minimum evidence for each data stage | Deciding whether a pipeline output is trustworthy |
| [worked-example.md](references/worked-example.md) | City-year policy panel example with inputs, outputs, logs, and audit artifacts | Teaching or demonstrating the skill |
