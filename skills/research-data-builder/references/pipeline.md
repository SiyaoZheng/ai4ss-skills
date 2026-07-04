# Data Pipeline Pattern

Use this reference when building or repairing a social-science data workflow.

## 1. Orientation

Read these before changing files:

- `AGENTS.md` or project instructions.
- `docs/research_design.*`.
- `docs/variable_dictionary.*`.
- Existing scripts in execution order.
- Existing logs and prior audit outputs.

If the project has no clear file layout, propose one:

```
data/raw/          # immutable source files
data/interim/      # cleaned but not final
data/analysis/     # model-ready samples
scripts/           # numbered, runnable steps
output/audit/      # sample flow, merge, missingness, provenance
output/tables/
output/figures/
output/logs/
docs/changelog.md
```

## 2. Stage Pattern

For each stage, record:

- Inputs: exact paths and file hashes if feasible.
- Operation: join, filter, reshape, variable construction, extraction, or validation.
- Outputs: exact paths.
- Row counts before and after.
- Unique unit counts before and after.
- New variables and their construction rules.
- Known unresolved issues.

Recommended stages:

1. `00_setup`: environment, packages, project paths.
2. `10_ingest`: read raw files and normalize names/types without changing meaning.
3. `20_clean`: recode variables, handle duplicates, apply explicit filters.
4. `30_merge`: join sources and write merge audit.
5. `40_construct`: build treatment, outcomes, controls, and sample flags.
6. `50_export_analysis`: write analysis sample and final audit report.

## 3. Validation Checks

Minimum checks:

- Observation unit matches the research design.
- ID and time variables are nonmissing where required.
- Duplicate keys are explained before merging.
- Merge rates are reported by source and key.
- Missingness is reported for core variables.
- Sample restrictions are visible as named flags.
- Treatment timing is internally consistent.
- Analysis sample has stable sorting and documented columns.

## 4. Text-to-Structure Extraction

When extracting from annual reports, policy documents, filings, or web pages:

- Save raw source path or URL, document id, page/section, and extraction timestamp.
- Define the extraction target before running the model.
- Keep source snippets for extracted values.
- Add `confidence`, `rule_or_prompt_version`, and `needs_review`.
- Exclude low-confidence rows from primary analysis unless explicitly approved.

## 5. Failure Handling

When a script fails:

1. Copy the error message into the log.
2. Inspect the smallest failing input and relevant column names.
3. Make the smallest code change that addresses the observed failure.
4. Rerun the failing step.
5. Append the cause, change, command, and validation result to `docs/changelog.md`.
