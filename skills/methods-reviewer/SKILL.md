---
name: methods-reviewer
description: >
  Empirical methods review skill for auditing social-science research designs, scripts, model outputs,
  tables, figures, robustness checks, and reproducibility evidence. Use before submission, presentation,
  replication release, or reviewer response when the task is to find design, data, code, inference,
  reporting, or overclaiming issues. It reviews and structures problems; it does not decide substantive
  identification validity for the author. Triggers: "methods review", "audit empirical design",
  "review regression output", "check fixed effects", "cluster standard errors", "robustness audit",
  "reproducibility review", "submission checklist", "计量审查", "方法审查", "结果审查", "稳健性检查".
---

# Methods Reviewer

Audit empirical work before it becomes a paper, talk, or response. The default output is an issue table with evidence, severity, and concrete next actions.

## Scholar Workbench

This skill answers: "结果解释有没有说过头？" Its value is not replacing methodological judgment; it is exposing whether the script, model object, table, figure, and written claim actually support the same interpretation.

## Core Rule

Review first, edit second. User permission may authorize focused code, table, or figure fixes after the review, but manuscript claims must remain claim-ledger rows, risk labels, and author revision targets. Do not provide replacement manuscript wording.

## Methodology Foundation

This skill is the `Diagnose` and `Redesign` layer of the MIDA spine. It checks whether declared `Model`, `Inquiry`, `Data strategy`, `Answer strategy`, executed outputs, and public claims still refer to the same research design.

The review must name diagnosands or gates such as wrong estimand, weak comparison, measurement mismatch, inference mismatch, reproducibility failure, source-status risk, or overclaiming. Redesign recommendations remain author decisions unless the user explicitly asks for implementation.

When a `.aiss` model is present, reviewing the model is part of the methods audit: `aiss.py compile/lint/run` errors, missing bridges, unchecked commensurability, and model-to-output mismatch are reportable issues. When a theory workbench is present, rival explanations, scope drift, vague mechanisms, non-discriminating observable implications, weak source status, and theory overclaim are issue-table rows, not a separate theory-review schema.

## Workflow Contract

- Upstream inputs: `study_design_brief.md`, `study_design_declaration.csv`, `research_model.aiss`, `ai4ss_check_report.txt`, `analysis_run_manifest.csv`, scripts, logs, tables, figures, data audit outputs, literature matrices, `literature_theory_synthesis.csv`, `theory_rival_map.csv`, `theory_scope_map.csv`, manuscript snippets, or reviewer comments.
- Produces: issue table, method-risk notes, recommended checks, open author decisions, and validation commands run.
- Handoff fields: `route_id`, `design_source`, `target_inquiry`, `mida_component`, `analysis_outputs`, `issue_table`, `severity`, `evidence`, `next_action`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `commensurability_status`, `next_skill_route`.
- Downstream routes: `research-data-builder`, `research-analysis-runner`, `study-design-builder`, `academic-writing-scaffold`, `reviewer-response`, `research-slides-builder`, `did-expert`, or `ask_author`.

## Routing Boundaries

Use this skill to audit evidence for identification validity, result-claim fit, robustness, inference, and reproducibility. Final scholarly judgment remains with the author. Do not use it to build data pipelines; hand data construction to `research-data-builder`. Do not use it as the first executor of an analysis plan; hand execution to `research-analysis-runner`. Do not use it to write manuscript prose or response letters; hand evidence-ready scaffolds to `academic-writing-scaffold` or `reviewer-response`.

## Workflow

```
Step -1: Orient
-> Read AGENTS.md, research design notes, scripts, logs, tables, figures, and manuscript/output text.
-> Identify the design family: descriptive, OLS, DID, IV, RD, RCT, synthetic control, panel, qualitative, mixed methods.
-> For DID/event-study as the central task, invoke $did-expert first when available; use this skill to wrap its findings into the general issue table.
-> If `research_model.aiss` is present, run or inspect `scripts/validate_ai4ss_model.py` output before judging claims.

Step 0: Build audit scope
-> Data construction, model specification, inference, diagnostics, robustness, reporting, reproducibility, writing claims.

Step 1: Inspect evidence
-> Compare stated design against actual scripts and outputs.
-> Check whether tables/figures expose sample, variables, FE, clustering, and uncertainty.
-> Trace suspicious numbers back to scripts or logs.
-> Compare `.aiss` concepts, causal implications, and bridges against design declarations, data audits, and analysis manifests.
-> If a theory workbench is present, audit rival explanations, scope rows, mechanism parts, source-status support, and observable implications against the declared design.

Step 2: Produce issue table
-> Use severity and confidence.
-> Separate confirmed bugs from risks, missing evidence, and author decisions.
-> Give exact file paths and lines where possible.

Step 3: Recommend next actions
-> Suggest minimal checks or analyses.
-> Do not invent robustness results.
-> If implementation is requested, make focused changes and rerun relevant commands.
```

## Issue Categories

- Data: sample construction, merges, duplicates, missingness, unit mismatch.
- Design: estimand, treatment timing, control group, identification assumption.
- Specification: fixed effects, controls, transformations, weights, clustering.
- Inference: few clusters, multiple testing, serial correlation, uncertainty display.
- Diagnostics: balance, pre-trends, placebo, sensitivity, robustness.
- Reporting: table labels, figure axes, omitted periods, N, sample notes.
- Reproducibility: runnable scripts, paths, logs, seeds, package versions.
- Claims: causal language, mechanism claims, external validity, policy implications.
- Theory: vague mechanisms, missing rival explanation, scope drift, non-discriminating observable implication, weak source status, theory overclaim.

## Output Shape

Return findings first:

| severity | issue | evidence | why_it_matters | next_action | status |
|---|---|---|---|---|---|

Then include open author decisions and any test commands run. If a `.aiss`
model is in scope, include model identifiers and check status in the CSV sidecar.

If a Markdown issue table is shown to the user, keep a CSV sidecar with these exact snake_case columns for validation.

## Script Utilities

- Run `scripts/validate_issue_table.py <path>` to check the issue-table schema and severity labels.
- Run `scripts/validate_ai4ss_model.py <path-to-research_model.aiss>` when a model-linked issue is in scope.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [audit-checklist.md](references/audit-checklist.md) | General empirical audit checklist across data, design, inference, outputs, and claims | Running a review |
| [reporting-standards.md](references/reporting-standards.md) | What tables, figures, and result text must expose | Reviewing outputs or presentation materials |
| [design-routes.md](references/design-routes.md) | Review routes for OLS/panel, DID, IV, RD, synthetic control, descriptive, and qualitative designs | Choosing the right audit path |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for script review, table audit, result-claim audit, and reproducibility checks | Turning a review need into an agent task |
| [issue-examples.md](references/issue-examples.md) | Example findings, severities, evidence standards, and false-positive controls | Calibrating review output |
