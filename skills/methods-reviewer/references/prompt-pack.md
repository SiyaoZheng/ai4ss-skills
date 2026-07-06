# Prompt Pack

Use these prompts to run bounded reviews.

## Full Methods Audit

```text
Use $methods-reviewer.

Please audit this empirical project before submission.

Read:
- AGENTS.md
- docs/research_design.md
- data audit outputs
- scripts for data construction and estimation
- output tables and figures
- manuscript or slide result claims if present

Return findings first as:
severity | issue | evidence | why_it_matters | next_action | status

Do not edit files.
Separate confirmed bugs from risks, repairs, and assumptions to disclose.
```

## Classroom Trace

```text
Bad prompt:
这张回归表靠谱吗？帮我润色结论。

Improved prompt:
Use $methods-reviewer to audit the table, script, research design, and claimed result.
Return a CSV-ready issue table with severity, issue, evidence, why_it_matters,
next_action, and status. Do not present rewritten text as no-AI or
direct-submission ready.

Expected behavior:
Read design and output -> trace table notes to scripts -> identify confirmed bugs,
risks, and assumptions to disclose -> route DID-specific details to /did-expert if central
-> run validate_ai4ss_model.py on the .aiss declaration set.
```

## Regression Table Audit

```text
Use $methods-reviewer to audit this regression table and the script that produced it.

Inputs:
- table: [path]
- script: [path]
- research design: [path]

Check:
- outcome and treatment labels;
- sample and N;
- fixed effects;
- controls;
- clustering;
- transformations;
- model notes;
- whether table supports the claimed interpretation.

Do not rerun or edit unless needed for evidence.
```

## Result Claim Audit

```text
Use $methods-reviewer to audit these result claims.

Claims: [paste or path]
Evidence: [tables/figures/logs]

For each claim, classify:
- supported;
- overclaim;
- wrong estimand;
- missing uncertainty;
- missing evidence;
- needs claim narrowing or evidence expansion.

Provide issue notes and, when useful, AI-assisted working revision targets.
Do not present rewritten text as no-AI or direct-submission ready.
```

## Reproducibility Audit

```text
Use $methods-reviewer to check reproducibility.

Please inspect:
- script order;
- hard-coded paths;
- output paths;
- logs;
- random seeds;
- package/version records;
- whether tables and figures can be traced to scripts.

Return PASS/WARN/FAIL for each area and exact fixes.
```

## DID Escalation Prompt

```text
This appears to be a DID or event-study design.

First use $methods-reviewer for the general audit. Then, if DID-specific decisions are central, use /did-expert for:
- estimator choice;
- staggered adoption concerns;
- pre-trend interpretation;
- event-study aggregation;
- HonestDiD or other sensitivity checks.
```

## Implementation Follow-Up

```text
Based on the audit, implement only P0/P1 fixes that are confirmed bugs.

Before editing:
- list exact files to change;
- explain why each change is necessary;
- state validation command.

After editing:
- rerun the smallest relevant command;
- report output paths and remaining risks.
```
