# Prompt Pack

## Readiness Check

```text
Use $research-analysis-runner.

Inputs:
<study_design_brief.md>
<study_design_declaration.csv>
<research_model.aiss if present>
<analysis_plan_scaffold.md>
<analysis-ready data or source output>
<sample_flow.csv / merge_audit.csv / variable_provenance.csv if data were transformed>
<variable dictionary if available>

First requested output:
<descriptive table / baseline model / figure shell / coding summary>

First, create or validate analysis_readiness_check.csv. If design source, data source, unit, required variables, sample/audit paths, .aiss bridge alignment, or output path are missing, stop and route back.
```

## First Analysis Loop

```text
Run one analysis loop only.

Use the design source and data source below:
<paths>

Proceed only if analysis_readiness_check.csv is ready or explicitly warn.
Produce the requested output, a log, and analysis_run_manifest.csv with readiness_check_path and readiness_status.
Do not select preferred results, write result prose, or make causal claims.
```

## Review Handoff

```text
Hand off these outputs to $methods-reviewer.

Carry forward analysis_run_manifest.csv, scripts, logs, tables/figures, design source, sample notes, warnings, and interpretation boundaries.
Include analysis_readiness_check.csv so the reviewer can inspect whether the data entered execution through a valid gate.
Do not add new claims.
```
