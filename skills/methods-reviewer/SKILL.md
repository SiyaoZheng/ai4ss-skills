---
name: methods-reviewer
description: >
  Empirical methods review skill for auditing social-science research designs, data work,
  analysis outputs, and claim boundaries. Use when reviewing identification, inference,
  robustness, diagnostics, reproducibility, overclaiming, or method-risk issues before
  writing or presentation. Triggers: "methods review", "audit results", "overclaim",
  "identification risk", "robustness", "inference check", "方法审查", "结果解释", "因果识别".
---

# Methods Reviewer

Review evidence for methodological risk before anyone treats results as scholarly claims.

## Scholar Workbench

This skill answers: "结果解释有没有说过头？" Its value is not producing a paper-ready critique; it is turning evidence, scripts, outputs, and declared design elements into actionable diagnostic checks and author decisions.

## Core Rule

Find bugs, risks, missing evidence, and author decisions first. Do not invent robustness results, rewrite the design silently, or convert diagnostic findings into no-AI or direct-submission-ready manuscript text.

## AI4SS Runtime Gate

Do not review research-factory outputs as disconnected files. Locate `research_model.aiss`, selected route, MIDA declarations, and recent `scripts/validate_ai4ss_model.py` output before judging claims. If the AI4SS object is missing or invalid, make that the first blocker and route to `research-starter`, `study-design-builder`, `research-data-builder`, or `research-analysis-runner`.

Methods findings must become `.aiss` diagnostic `check`, redesign `decision`, or bounded claim-support declarations. A prose table in the chat is only a display surface; it is not workflow state.

## Methodology Foundation

This skill owns `Diagnose` and `Redesign` in the MIDA spine. It compares declared `Model`, `Inquiry`, `Data strategy`, and `Answer strategy` against the actual data pipeline, scripts, outputs, tables, figures, and proposed claims.

The review must preserve `ai4ss_model_path`, model ids, concept ids, causal ids, bridge ids, `ai4ss_check_status`, and `commensurability_status` when they exist. It can recommend redesign, but scholarly judgment remains human-accountable.

## Workflow Contract

- Upstream inputs: `research_model.aiss`, selected route and MIDA declarations, AI4SS check output, scripts, logs, tables, figures, data artifacts, literature evidence, manuscript snippets, slide claims, or reviewer comments.
- Produces: diagnostic findings, method-risk notes, recommended checks, open author decisions, validation commands run, reproducibility and deviation-log findings, and `.aiss` `check`, `decision`, or bounded claim-support declarations.
- Handoff fields: `route_id`, `design_source`, `target_inquiry`, `mida_component`, `analysis_outputs`, `severity`, `evidence`, `next_action`, `computational_reproducibility_status`, `deviation_log_status`, `author_decisions`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `commensurability_status`, `next_skill_route`.
- Downstream routes: `research-data-builder`, `research-analysis-runner`, `study-design-builder`, `academic-writing-scaffold`, `reviewer-response`, `research-slides-builder`, `did-expert`, or `ask_author`.

## Routing Boundaries

Use this skill to audit evidence for identification validity, result-claim fit, robustness, inference, transparency-standard fit, preregistration or analysis-plan deviations, and reproducibility. Do not use it to build data pipelines; hand data construction to `research-data-builder`. Do not use it as the first executor of an analysis plan; hand execution to `research-analysis-runner`. For AI-disclosed manuscript or response working text, hand evidence-ready material to `academic-writing-scaffold` or `reviewer-response`.

## Workflow

```text
Step -1: Orient
-> Read AGENTS.md, research_model.aiss, research design notes, scripts, logs, tables, figures, and output text.
-> Identify the design family: descriptive, OLS, DID, IV, RD, RCT, synthetic control, panel, qualitative, mixed methods.
-> For DID/event-study as the central task, invoke $did-expert first when available; use this skill to wrap its findings into `.aiss` diagnostics.

Step 0: Build audit scope
-> Data construction, model specification, preregistration or protocol deviations, inference, diagnostics, robustness, reporting, reproducibility, and claims.

Step 1: Inspect evidence
-> Compare stated design against actual scripts and outputs.
-> Check whether tables/figures expose sample, variables, FE, clustering, and uncertainty.
-> Trace suspicious numbers back to scripts or logs.
-> Compare `.aiss` concepts, causal implications, and bridges against design declarations, data artifacts, and analysis artifacts.
-> Audit rival explanations, scope rows, mechanism parts, source-status support, and observable implications against the declared design.

Step 2: Produce findings
-> Use severity and confidence.
-> Separate confirmed bugs from risks, missing evidence, and author decisions.
-> Give exact file paths and lines where possible.
-> Record durable findings as `.aiss` checks or decisions when the project is in the research factory.

Step 3: Recommend next actions
-> Suggest minimal checks or analyses.
-> Do not invent robustness results.
-> If implementation is requested, make focused changes and rerun relevant commands.
```

## Output Shape

Return findings first with severity, issue, evidence, why it matters, next action, and status. Then include open author decisions, `.aiss` ids touched, and test commands run.

For research-factory work, durable diagnostic state belongs in `research_model.aiss` as `check`, `decision`, or bounded claim-support declarations.

## Script Utilities

- When output freshness, missing dependencies, missing columns, or duplicate keys are in scope, run `research-analysis-runner/scripts/check_runtime_contract.py --cwd <project> ...` or inspect its JSON report before reviewing result claims.
- Run `scripts/validate_ai4ss_model.py <path-to-research_model.aiss>` when a model-linked issue is in scope.
- Use method-specialist skills such as `did-expert` for central designs that need specialist diagnostics.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [audit-checklist.md](references/audit-checklist.md) | General empirical audit checklist across data, design, inference, outputs, and claims | Running a review |
| [reporting-standards.md](references/reporting-standards.md) | What tables, figures, and result text must expose | Reviewing outputs or presentation materials |
| [design-routes.md](references/design-routes.md) | Review routes for OLS/panel, DID, IV, RD, synthetic control, descriptive, and qualitative designs | Choosing the right audit path |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for script review, table audit, result-claim audit, and reproducibility checks | Turning a review need into an agent task |
| [issue-examples.md](references/issue-examples.md) | Example findings, severities, evidence standards, and false-positive controls | Calibrating review output |
