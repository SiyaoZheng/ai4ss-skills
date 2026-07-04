# Prompt Pack

Use these prompts as task starters. Replace bracketed fields before use.

## Project Intake

```text
Use $research-data-builder.

Task: inspect this research data project before changing anything.

Please read:
- AGENTS.md
- docs/research_design.md
- docs/variable_dictionary.* if present
- scripts/ directory
- data/ directory tree only, not full raw confidential files unless needed

Return:
1. observed project structure;
2. claimed unit of observation;
3. raw/interim/analysis/output boundaries;
4. existing data pipeline steps;
5. missing documentation;
6. proposed next action.

Do not edit files yet.
```

## Build An Analysis Sample

```text
Use $research-data-builder to build an auditable analysis sample.

Research design:
- unit: [city_id x year]
- period: [2012-2023]
- outcome: [ln_patent]
- treatment group: [treat_city]
- treatment timing: [first_policy_year]
- controls: [ln_gdp_pc, fiscal_pressure, population_density]

Inputs:
- raw outcome data: [path]
- policy list: [path]
- controls: [path]
- variable dictionary: [path]

Requirements:
1. write scripts under scripts/ with numbered filenames;
2. never overwrite data/raw/;
3. write the model-ready sample to data/analysis/;
4. write sample_flow.csv, merge_audit.csv, variable_provenance.csv, and a run log;
5. stop and report if duplicate keys or ambiguous treatment timing appear.
```

## Merge Repair

```text
Use $research-data-builder to diagnose a merge problem.

Problem: [brief description or error message]

Inspect:
- the merge script;
- the left and right key columns;
- duplicate keys;
- unmatched records;
- existing merge audit outputs.

Return a table with:
- root cause;
- evidence;
- candidate fix;
- risk of each fix;
- exact files that would change.

Do not edit files until I approve the fix.
```

## Text-To-Structure Extraction

```text
Use $research-data-builder for text-to-structure extraction.

Goal: extract [AI investment / policy target / R&D measure] from [annual reports / policy documents].

For each source document, output:
- document_id;
- source_path or URL;
- page or section;
- extracted_value;
- source_snippet;
- extraction_rule_or_prompt_version;
- confidence;
- needs_review;
- notes.

Rules:
- do not invent values absent from the text;
- keep low-confidence rows out of the primary analysis sample;
- write a manual review file for ambiguous cases;
- preserve enough source text for spot checks.
```

## Pipeline Debugging

```text
Use $research-data-builder to debug the failing pipeline step.

Command that failed:
`[command]`

Error:
```text
[paste exact error]
```

Please:
1. identify the smallest failing script or input;
2. inspect only the relevant columns and logs first;
3. explain the root cause using observed evidence;
4. propose the minimum code change;
5. after approval, rerun the failing step and update the changelog.
```

## Delivery Review

```text
Use $research-data-builder to review whether this analysis sample is ready.

Check:
- unit of observation;
- duplicate IDs;
- year range;
- treatment timing;
- merge rates;
- missingness in core variables;
- sample restrictions;
- variable provenance;
- audit files and logs.

Return: PASS / WARN / FAIL with evidence paths and concrete next actions.
```

## Classroom Trace

```text
Bad prompt:
把这些原始数据合并好，直接给我可回归的数据。

Improved prompt:
Use $research-data-builder to build an auditable sample. Never overwrite data/raw/.
Produce sample_flow.csv, merge_audit.csv, variable_provenance.csv, and logs.
Validate every CSV sidecar with validate_data_audits.py.

Expected behavior:
Inspect project rules -> identify unit and keys -> check duplicates before merging ->
write staged scripts -> produce audits -> fail if merge counts, review_path, or provenance
are missing.
```
