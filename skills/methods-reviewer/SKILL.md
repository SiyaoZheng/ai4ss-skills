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

This skill answers: "结果解释有没有说过头？" Its value is turning evidence, scripts, outputs, and declared design elements into actionable diagnostic checks, repairs, and bounded draft-PDF claims.

## Core Rule

Find bugs, risks, missing evidence, and claim-boundary problems first. Do not invent robustness results or rewrite the design silently; when implementation is possible, repair or trigger the concrete next analysis/design/data/writing step.

## Full-Auto Harness Contract

When invoked by an automatic research harness, this skill must not pause for
human choice or return any terminal no-progress state. A finding must map to an automatic next action: repair code, rerun a
diagnostic, narrow a claim, expand evidence, redesign the analysis, or update
draft-PDF text. The target artifact is a publication-level `paper/full_draft.pdf`
whose methods limits are visible, not a standalone critique.

## AI4SS Runtime Gate

Do not review research-factory outputs as disconnected files. Locate `.ai4ss/research_model.aiss`, selected route, MIDA declarations, and recent `scripts/validate_ai4ss_model.py` output before judging claims. If the AI4SS object is missing or invalid, create or repair the first valid route/design/data/analysis linkage before judging claims.

Methods findings must become `.aiss` diagnostic `check`, redesign `decision`, or bounded claim-support declarations. A prose table in the chat is only a display surface; it is not workflow state.

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

## Methodology Foundation

This skill owns `Diagnose` and `Redesign` in the MIDA spine. It compares declared `Model`, `Inquiry`, `Data strategy`, and `Answer strategy` against the actual data pipeline, scripts, outputs, tables, figures, and proposed claims.

The review must preserve `ai4ss_model_path`, model ids, concept ids, causal ids, bridge ids, `ai4ss_check_status`, and `commensurability_status` when they exist. It can recommend or execute redesign actions when they are needed for the draft PDF.

## Workflow Contract

- Upstream inputs: `.ai4ss/research_model.aiss`, selected route and MIDA declarations, AI4SS check output, scripts, logs, tables, figures, data artifacts, literature evidence, manuscript snippets, slide claims, or reviewer comments.
- Produces: diagnostic findings, method-risk notes, executed or queued checks, automatic next actions, validation commands run, reproducibility and deviation-log findings, and `.aiss` `check`, `decision`, or bounded claim-support declarations.
- Handoff fields: `route_id`, `design_source`, `target_inquiry`, `mida_component`, `source_access_status`, `observed_data_only_status`, `row_source_provenance`, `analysis_outputs`, `severity`, `evidence`, `next_action`, `computational_reproducibility_status`, `deviation_log_status`, `assumptions_to_disclose`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `commensurability_status`, `next_skill_route`.
- Downstream routes: `public-data-sources`, `research-data-builder`, `research-analysis-runner`, `study-design-builder`, `academic-writing-scaffold`, `reviewer-response`, `research-slides-builder`, or `did-expert`.

## Routing Boundaries

Use this skill to audit evidence for identification validity, result-claim fit, robustness, inference, transparency-standard fit, preregistration or analysis-plan deviations, source authenticity, observed-data-only compliance, and reproducibility. Do not use it to acquire sources or build data pipelines; hand source acquisition to `public-data-sources` and sample construction to `research-data-builder`. Do not use it as the first executor of an analysis plan; hand execution to `research-analysis-runner`. For AI-disclosed manuscript or response working text, hand evidence-ready material to `academic-writing-scaffold` or `reviewer-response`.

## Workflow

```text
Step -1: Orient
-> Read AGENTS.md, `.ai4ss/research_model.aiss`, research design notes, scripts, logs, tables, figures, and output text.
-> Identify the design family: descriptive, OLS, DID, IV, RD, RCT, synthetic control, panel, qualitative, mixed methods.
-> For DID/event-study as the central task, invoke $did-expert first when available; use this skill to wrap its findings into `.aiss` diagnostics.

Step 0: Build audit scope
-> Real observed source acquisition, data construction, model specification, preregistration or protocol deviations, inference, diagnostics, robustness, reporting, reproducibility, and claims.

Step 1: Inspect evidence
-> Compare stated design against actual scripts and outputs.
-> Verify empirical rows, tables, figures, and estimates trace to real observed
   public or authorized sources. Synthetic, simulated, hypothetical,
   illustrative, generated, DGP-created, random-draw, benchmark-calibrated, or
   literature-parameter-imputed empirical evidence is a fatal methods finding
   routed to `public-data-sources` or design redesign.
-> Check whether tables/figures expose sample, variables, FE, clustering, and uncertainty.
-> Trace suspicious numbers back to scripts or logs.
-> Compare `.aiss` concepts, causal implications, and bridges against design declarations, data artifacts, and analysis artifacts.
-> Audit rival explanations, scope rows, mechanism parts, source-status support, and observable implications against the declared design.

Step 2: Produce findings
-> Use severity and confidence.
-> Separate confirmed bugs from risks, missing evidence, and assumptions to disclose.
-> Give exact file paths and lines where possible.
-> Record durable findings as `.aiss` checks or decisions when the project is in the research factory.

Step 3: Recommend next actions
-> Suggest minimal checks or analyses.
-> Do not invent robustness results.
-> If implementation is requested, make focused changes and rerun relevant commands.
```

## Output Shape

Return findings first with severity, issue, evidence, why it matters, next action, and status. Then include assumptions to disclose, `.aiss` ids touched, and test commands run.

For research-factory work, durable diagnostic state belongs in `.ai4ss/research_model.aiss` as `check`, `decision`, or bounded claim-support declarations.

## Script Utilities

- When output freshness, missing dependencies, missing columns, or duplicate keys are in scope, run `research-analysis-runner/scripts/check_runtime_contract.py --cwd <project> ...` or inspect its JSON report before reviewing result claims.
- Run `scripts/validate_ai4ss_model.py .ai4ss/research_model.aiss` when a model-linked issue is in scope.
- Use method-specialist skills such as `did-expert` for central designs that need specialist diagnostics.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [audit-checklist.md](references/audit-checklist.md) | General empirical audit checklist across data, design, inference, outputs, and claims | Running a review |
| [reporting-standards.md](references/reporting-standards.md) | What tables, figures, and result text must expose | Reviewing outputs or presentation materials |
| [design-routes.md](references/design-routes.md) | Review routes for OLS/panel, DID, IV, RD, synthetic control, descriptive, and qualitative designs | Choosing the right audit path |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for script review, table audit, result-claim audit, and reproducibility checks | Turning a review need into an agent task |
| [issue-examples.md](references/issue-examples.md) | Example findings, severities, evidence standards, and false-positive controls | Calibrating review output |
