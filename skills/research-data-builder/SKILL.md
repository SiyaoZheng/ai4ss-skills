---
name: research-data-builder
description: >
  Social-science data engineering skill for turning raw files into auditable analysis samples.
  Use when building or repairing data pipelines, panel datasets, merges, variable construction,
  sample-flow reports, missingness audits, text-to-structure extraction, or reproducible scripts
  for empirical research. Triggers: "build analysis sample", "data cleaning", "merge diagnostics",
  "panel construction", "row loss", "variable dictionary", "raw to analysis", "text extraction",
  "do not overwrite raw data", "reproducible data pipeline", "数据清洗", "样本构造", "合并检查",
  "变量构造", "样本流".
---

# Research Data Builder

Build research datasets as an auditable workflow, not as one-off data wrangling. The default result is a runnable pipeline plus row-count, merge, missingness, and provenance evidence that another researcher can inspect through the governing `.aiss` model.

## Scholar Workbench

This skill answers: "数据怎么来的，样本怎么变的？" Its value is not cleaning data faster; it is making row loss, merge ambiguity, variable construction, and extraction uncertainty visible before any result is interpreted.

## Core Rule

Never overwrite raw data. Read project instructions first, write scripts and derived data to explicit output paths, and make every sample-size change explainable.

## Real Observed Data Only

Every empirical row, cell, document code, event, unit, outcome, treatment,
covariate, and estimate feeding a manuscript-facing analysis must trace to a
real observed public or authorized source. Synthetic, simulated, hypothetical,
illustrative, generated, benchmark-calibrated, DGP-created, random-draw, or
literature-parameter-imputed data are not valid data artifacts. Published
coefficients, parameter benchmarks, and summary statistics may inform theory,
measurement discussion, priors, or power reasoning; they must not be converted
into analysis rows or substitute datasets.

## Full-Auto Harness Contract

When invoked by an automatic research harness, this skill must not pause for
human choice or return any terminal no-progress state. Missing data requirements
become automatic file discovery, source-acquisition handoff to
`public-data-sources`, schema inspection, DDI parsing/cleaning, source
extraction from acquired artifacts, route redesign, or measurement repair. If
one source artifact is unavailable or invalid, route to `public-data-sources`
to switch to another real observed public or authorized source, unit, geography,
time period, measure, or route that can support a publication-level
`paper/full_draft.pdf`. Do not fill the gap with synthetic or
benchmark-calibrated data.

## AI4SS Runtime Gate

Do not run this skill as a generic data-cleaning helper inside the research factory. Before producing derived data, cleaning scripts, analysis samples, or downstream handoffs, locate the governing `.ai4ss/research_model.aiss` with a selected route and MIDA declarations.

Every production data artifact must be represented or referenced by `.aiss` declarations and must preserve `ai4ss_model_path`. If the model is missing, route-only, invalid, or lacks the relevant design source, create or repair the route/design declarations automatically; do not create a parallel workflow record to bypass AI4SS.

## Workspace Contract

Follow `docs/research_workspace_contract.md`. Durable workflow state belongs in
`.ai4ss/research_model.aiss`; generated data, output, logs, and PDFs must be
produced through `make` targets, with `make all` as the final orchestration path.

## .aiss State Machine

When `.ai4ss/research_model.aiss` exists, run
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` before deciding
the next route. When this skill starts, completes, fails, or observes a
watchdog heartbeat in an automatic harness, record that runtime fact as an
`.aiss` `event` declaration or return a deterministic
`aiss.py transition --event ...` fragment for merge. Events do not replace
semantic updates: if the skill resolves a repair/check status, update the
relevant `route`, `mida`, `decision`, `check`, `artifact`, or claim-support
declaration too.

## Runtime Failure Guardrails

- Discover files with `Path.exists()`, `Path.glob()`, `rg --files`, or quoted shell patterns before reading them. Run `scripts/check_runtime_contract.py` for path/glob checks; do not let unquoted zsh globs decide whether data exists.
- Run dependency preflights before long data work: import required Python modules and load required R packages in the same interpreter that will run the pipeline.
- Inspect schemas before selecting or renaming columns. If a requested variable is absent, record the missing-column finding as an `.aiss` `check` or `decision`, search for substitutes or repair the construction rule, and continue.
- Run project scripts from the project root or set their source path explicitly so local imports such as `config` resolve correctly.
- Every nonzero command exit is a pipeline finding. Record command, error, root cause, fix, and rerun status before saying the data are ready.

## Methodology Foundation

This skill realizes the `Data strategy` part of the MIDA spine. It makes sampling, source selection, measurement, extraction, linkage, transformation, missingness, and provenance inspectable before any answer strategy or claim depends on the data.

The skill must preserve upstream `Model` and `Inquiry` fields when present, but it does not choose the estimand, target quantity, or identification strategy.

When an upstream `.aiss` model exists, data artifacts must preserve `ai4ss_model_path`, relevant concept or bridge ids, and check status. Data work can repair empirical bridge evidence, but it must not silently rewrite the model.

## Workflow Contract

- Upstream inputs: `.ai4ss/research_model.aiss`, selected route declarations, seven MIDA declarations, verified real observed source artifacts, raw data, source files, variable dictionaries, extraction rules, DDI metadata, or an analysis plan's data requirements.
- Produces: derived real-observed data, runnable scripts, row-count logs, merge diagnostics, missingness diagnostics, variable-construction evidence, row/cell source-provenance evidence, DDI cleaning artifacts when routed through `ai4ss-skills`, materials/data transparency status, FAIR metadata status, replication-package data components, and `.aiss` `source`, `artifact`, `empirical`, `observation`, `coupling`, `bridge`, `check`, or `decision` declarations that reference those files.
- Handoff fields: `route_id`, `design_source`, `target_inquiry`, `source_access_status`, `observed_data_only_status`, `data_source`, `unit_of_analysis`, `sample_restrictions`, `constructed_variables`, `row_source_provenance`, `known_data_gaps`, `materials_transparency_status`, `data_transparency_status`, `fair_metadata_status`, `replication_package_status`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `validation_commands`, `next_skill_route`.
- Downstream routes: `research-analysis-runner`, `methods-reviewer`, `academic-writing-scaffold`, `research-slides-builder`, `public-data-sources`, or `study-design-builder`.

## Routing Boundaries

Use this skill for confirmed real observed data and pipeline work. Do not use it
to acquire or verify empirical sources; hand that to `public-data-sources`. Do
not use it to choose the research design; hand ambiguous design choices to
`study-design-builder`. Do not use it to run the first analysis package unless
the task is only data feasibility; hand analysis execution to
`research-analysis-runner`. Do not use it to certify empirical identification
or result claims; hand those checks to `methods-reviewer`. Do not use it to
write paper text; hand verified artifacts to `academic-writing-scaffold`.

## Workflow

```text
Step -1: Orient
-> Read AGENTS.md, README, design notes, variable dictionaries, and the file tree.
-> Identify raw, intermediate, processed, scripts, output, and log directories.
-> Locate `.ai4ss/research_model.aiss`, selected route, and MIDA declarations before production data work.
-> If the `.aiss` object is absent or invalid, create or repair the route/design declarations and keep the data workflow attached to that model.

Step 0: Classify the task
-> New analysis sample: build a reproducible raw-to-derived pipeline.
-> Merge or matching repair: inspect keys, duplicates, unmatched records, and review paths.
-> Text-to-structure extraction: require source snippets, extraction rules, confidence flags, and manual-review outputs.
-> Survey/codebook cleaning: when `.dta`, `.sav`, codebook PDF/docx, or `ddi-metadata.yaml` is central, route through `codebook-parse` -> `cleaning-contract` -> `cleaning-execute`.

Step 1: Inspect and preflight
-> List source files and schemas before code changes.
-> Check package availability and write permissions.
-> Record source, measurement, linkage, and transformation assumptions as `.aiss` declarations.
-> Verify that the candidate data are real observed data and that row/cell provenance can be shown in the draft PDF.

Step 2: Build or repair
-> Write focused scripts.
-> Never edit raw files.
-> Keep row counts, unmatched keys, constructed variables, and missingness findings linked to the same `.aiss` route.
-> Reject any script path that generates analysis rows from random draws, DGPs, parameter benchmarks, or literature coefficients; redesign the data route instead.

Step 3: Validate
-> Rerun scripts from a clean process.
-> Confirm output existence, freshness, row counts, schema, and failed-command history.
-> Confirm every analysis-facing dataset has real observed source provenance and no synthetic-data markers.
-> Add `.aiss` `check` or `decision` declarations for unresolved data gaps.
-> Record materials/data availability, access limits, checksum or locator status, and FAIR metadata readiness before handing off to analysis or writing.

Step 4: Hand off
-> Return the script paths, output paths, validation commands, and `.aiss` ids touched.
-> Set `next_skill_route` to the next research-factory stage.
```

## Default Outputs

- Updated `.ai4ss/research_model.aiss` or deterministic `.aiss` fragment containing the data `source`, `artifact`, `empirical`, `observation`, `coupling`, `bridge`, `check`, and `decision` declarations touched by the data work.
- Runnable scripts or notebooks for the derived data step.
- Derived data files and diagnostics referenced from `.aiss`.
- Materials/data transparency and FAIR metadata status for any eventual replication package.
- Command logs or runtime reports referenced from `.aiss`.
- Automatic route/design repair plus a concrete downstream handoff when AI4SS declarations are missing or insufficient.

## Script Utilities

- Run `scripts/check_runtime_contract.py` before long execution when paths, required packages, required columns, or output directories are in scope.
- Run `scripts/validate_ai4ss_model.py .ai4ss/research_model.aiss` after data declarations are added or changed.
- Use the DDI harness skills `codebook-parse`, `cleaning-contract`, and `cleaning-execute` for survey cleaning tasks instead of recreating their contracts here.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [pipeline.md](references/pipeline.md) | Pipeline layout, raw/intermediate/processed boundaries, reproducibility checklist | Building a new data pipeline |
| [real-observed-data-contract.md](references/real-observed-data-contract.md) | Only-real-data rule, forbidden generated-data patterns, and allowed observed-source substitutions | Any automatic harness or manuscript-facing data build |
| [audit-schema.md](references/audit-schema.md) | Legacy audit-field vocabulary; translate any useful fields into `.aiss` checks and artifacts | Maintaining older projects that already have audit exports |
| [quality-gates.md](references/quality-gates.md) | Runtime checks for row counts, merge ambiguity, missingness, and reproducibility | Before saying data are analysis-ready |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for data-pipeline repair and extraction tasks | Turning a data need into an agent task |
| [worked-example.md](references/worked-example.md) | Example city panel pipeline and audit reasoning | Teaching or demonstrating the skill |
