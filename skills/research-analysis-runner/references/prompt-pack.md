# Prompt Pack

## Readiness Check

```text
Use $research-analysis-runner.

Inputs:
<study_design_brief.md>
<.aiss MIDA declarations>
<.ai4ss/research_model.aiss if present>
<.aiss analysis-plan declarations or analysis plan source>
<analysis-ready data or source output>
<.aiss row-loss checks / .aiss merge checks / .aiss variable-provenance observations if data were transformed>
<variable dictionary if available>

First requested output:
<descriptive table / baseline model / figure shell / coding summary>

First, create or validate .aiss readiness checks. If design source, data source, unit, required variables, sample/audit paths, .aiss bridge alignment, or output path are missing, repair the missing piece or route to the skill that can repair it, then return to execution.
```

## First Analysis Loop

```text
Run one analysis loop only.

Use the design source and data source below:
<paths>

Proceed only if .aiss readiness checks is ready or explicitly warn.
Produce the requested output, a log, and .aiss analysis artifact declarations with readiness_check_path and readiness_status.
Do not select preferred results, write result prose, or make causal claims.
```

## Review Handoff

```text
Hand off these outputs to $methods-reviewer.

Carry forward .aiss analysis artifact declarations, scripts, logs, tables/figures, design source, sample notes, warnings, and interpretation boundaries.
Include .aiss readiness checks so the reviewer can inspect whether the data entered execution through a valid gate.
Do not add new claims.
```
