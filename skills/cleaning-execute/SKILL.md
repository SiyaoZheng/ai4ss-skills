---
name: cleaning-execute
description: >
  Third step of the DDI survey-cleaning harness. Reads `ddi-metadata.yaml`
  (with a `cleaning_contract` block written by `cleaning-contract`) and
  executes it mechanically: produces a clean `<stem>-clean.csv`, a
  reproducible `<stem>-cleaning.R` script, and appends a full audit trail
  to `processing_events`.

  Trigger on any of: "execute the cleaning contract", "run the cleaning",
  "produce the clean dataset", "generate the cleaned CSV", "apply my
  recoding decisions", "execute cleaning_contract", "build the analysis
  dataset", "run cleaning-execute", or any time the user has a
  `ddi-metadata.yaml` with a `cleaning_contract` block and wants the
  cleaned data + R script.

  Precondition: `ddi-metadata.yaml` must exist AND contain a non-empty
  `cleaning_contract` block. If it does not, tell the user to run
  `cleaning-contract` first.
---

# cleaning-execute

You are executing a researcher's `cleaning_contract` mechanically against
the raw data file. The core promise of the harness is *declare-then-execute*:
every decision was already written down by `cleaning-contract`. Your job
is to apply those decisions in the exact order the contract specifies,
produce a reproducible R script as the audit trail, and append a
`processing_events` entry documenting what happened.

**Do not invent new cleaning decisions.** If the contract is missing a
decision (e.g., a variable with `_needs_review: true` and no
`missing_treatment`), stop and tell the user to update the contract first.

**You are picking up where `cleaning-contract` left off.** The YAML
contains `cleaning_contract.universe`, `variable_contracts[]`,
`shared_recodes`, `derived_variables[]`, `weight_assignment`, and possibly
`harmonization_declaration[]`. Read these — do not re-derive them.

## Reference files — read before acting

| File | When to read |
|---|---|
| `references/execution-schema.md` | Before generating R — operation order, R idioms, edge cases |

## Workflow

### 1 · Verify preconditions

Check three things in order:

1. `ddi-metadata.yaml` exists in the working directory
2. It has a non-empty `cleaning_contract` block (`cleaning_contract` key with at least one `variable_contracts` entry, or a `universe.condition`, or `derived_variables`)
3. The raw data file referenced in `study.data_source` exists

If any is missing, stop and tell the user what to fix:

> "Run `cleaning-contract` first — `ddi-metadata.yaml` has no `cleaning_contract` block."
>
> "The raw data file `<path>` referenced in `study.data_source` is missing. Update `study.data_source` or restore the file."

Read `references/execution-schema.md` now before proceeding.

### 2 · Audit the contract for completeness

Run a Python audit to confirm every required decision is declared:

```python
import yaml
y = yaml.safe_load(open("ddi-metadata.yaml"))

contract = y.get("cleaning_contract", {})
variables = {v["id"]: v for v in y.get("variables", [])}

# Variables marked _needs_review must have a contract entry
needs_review = [v["id"] for v in y["variables"] if v.get("_needs_review")]
declared = {vc["var_id"] for vc in contract.get("variable_contracts", [])}
unhandled = [vid for vid in needs_review if vid not in declared]

if unhandled:
    print(f"STOP: {len(unhandled)} variables flagged _needs_review have no contract:")
    for vid in unhandled[:5]:
        print(f"  - {vid}: {variables[vid]['name']}")
```

If any `_needs_review` variable lacks a contract, stop and tell the user
to run `cleaning-contract` for those variables.

### 3 · Plan the execution

Print a one-screen execution plan to the user before generating any R:

```
Execution plan for <stem>-clean.csv:

  Source:               <study.data_source> (<n_rows> rows × <n_cols> cols)
  Universe filter:      <universe.condition or "(none)">
  Variable contracts:   <count>
  Shared recodes:       <count> patterns
  Derived variables:    <count>
  Weight column:        <weight_var or "(none)">
  Harmonization:        <count> SSSOM mappings <"with per-code alignment" or "">
  Final column count:   <est_cols>

Operation order:
  1. Read <data_source> with haven (preserves labels)
  2. Apply universe filter           → keeps <est_n> rows
  3. Apply missing_treatment         → NA assignment (per variable)
  4. Apply recode_map                → value substitution
  5. Apply reverse                   → scale flips
  6. Apply coerce_to                 → type casts
  7. Apply harmonization (code_alignment + na_alignment) — if any
  8. Apply rename_to
  9. Build derived_variables
  10. Attach weight column
  11. Drop include=false columns
  12. Select analysis_vars

Output:
  - <stem>-clean.csv     (analysis-ready)
  - <stem>-cleaning.R    (reproducible script)
  - ddi-metadata.yaml    (with new processing_events entry)
```

If the user confirms, proceed to step 4.

### 4 · Generate the R cleaning script

Write `<stem>-cleaning.R`. The script must be **standalone, reproducible,
and idempotent**. Anyone with the raw data file and `<stem>-cleaning.R`
must be able to reproduce `<stem>-clean.csv` exactly.

Required structure (see `references/execution-schema.md` for full template):

```r
# <stem>-cleaning.R
# Generated by cleaning-execute on <ISO8601 date>
# Source contract: ddi-metadata.yaml
# Source data:    <study.data_source>

library(haven)      # read_dta / read_sav with label preservation
library(dplyr)      # filter, mutate, recode
library(labelled)   # set_value_labels, val_labels

# 1. Read raw data
df <- haven::read_<dta|sav>("<study.data_source>")

# 2. Universe filter (skip if condition is null)
df <- df |> dplyr::filter(<universe.condition>)

# 3-11: Per-variable operations in operation order
# (one block per variable_contract)

# 8. Rename columns

# 9. Build derived_variables

# 10. Attach weight column

# 11. Drop include=false columns

# 12. Select analysis_vars (if not null)

# 13. Write output
readr::write_csv(df, "<stem>-clean.csv")
```

**Critical rules for R generation:**

1. **Preserve operation order.** Universe filter ALWAYS first. Missing
   treatment ALWAYS before recode (so missing codes don't get recoded
   into valid values). Reverse ALWAYS after recode. Harmonize before
   derived variables, and rename before derivation so rules can use
   post-rename analysis names. See `references/execution-schema.md`.

2. **Use `dplyr::filter`, `dplyr::mutate`, never `df$col <- ...`** —
   pipeline form preserves labels and is auditable.

3. **NA assignment via `dplyr::na_if` or `dplyr::case_when`,** never
   silent coercion. Each NA assignment must be visible in the script.

4. **Recode via `dplyr::recode` with explicit `.default = NA_real_`** —
   never let unmapped values pass through silently.

5. **Reverse scale**: `n + 1 - x` where `n = max(codes)`. Compute `n`
   from the variable's `representation.codes`, do not hardcode.

6. **Derived variables**: paste the `derivation_rule` R expression
   verbatim into a `mutate()` call after `rename_to` has been applied.
   Use post-rename names because the contract is authored against the
   post-rename analysis namespace.

7. **Harmonization with per-code alignment** (TA-129):
   - `na_alignment`: `dplyr::na_if(col, source_na_code)` then assign canonical sentinel via `dplyr::if_else`
   - `code_alignment`: `dplyr::recode` source codes to target codes
   - `canonical_na`: write the project sentinels (99996/99997/99998/99999) as labelled values via `labelled::set_value_labels`

8. **No `setwd()`, no `library(tidyverse)`,** no global state. Use
   absolute paths from `study.data_source` if present, otherwise relative
   to the YAML's location.

### 5 · Execute the R script

Run the generated R script with `Rscript <stem>-cleaning.R`. Capture:

- Stdout / stderr (any warnings, errors, row count messages)
- Final row count and column count (compare against the plan)
- The output `<stem>-clean.csv` checksum (SHA256)

If the script fails, do NOT proceed. Surface the error to the user with:
- The exact R error
- The line number in the script
- The variable / operation that triggered it
- A suggested fix

Do not patch the script silently — the contract or the script template
is wrong, and the user needs to know.

### 6 · Append `processing_events` entry

Append (do not overwrite) one new entry to `processing_events[]`:

```yaml
processing_events:
  - event_id: evt<N+1>           # Increment from current max
    type: CleaningOperation       # DDI CV
    timestamp: <ISO8601 UTC>
    agent: cleaning-execute
    contract_ref: cleaning_contract  # Points to the contract block executed
    inputs:
      data: <study.data_source>
      contract_yaml: ddi-metadata.yaml
    outputs:
      clean_csv: <stem>-clean.csv
      r_script: <stem>-cleaning.R
      sha256: <checksum>
    summary:
      input_rows: <n_in>
      output_rows: <n_out>
      excluded_by_universe: <n_excluded>
      variables_in: <count>
      variables_out: <count>
      derived_count: <count>
      harmonized_count: <count>
    notes: null                   # Optional free-text
```

**Append only.** Never overwrite or restructure existing
`processing_events[]` entries. The `event_id` is `max(existing event_ids) + 1`.

### 7 · Final report

Print a final summary to the user:

```
✓ Cleaning execution complete

  Input:                <data_source> (<n_in> rows)
  Output:               <stem>-clean.csv (<n_out> rows × <n_cols> cols)
  R script:             <stem>-cleaning.R (<n_lines> lines)
  Excluded by universe: <n_excluded> rows
  Derived variables:    <count>
  Harmonized variables: <count> (<n with per-code alignment>)
  Audit event:          evt<N+1> appended to processing_events

The cleaned dataset is ready for analysis.
Next: run `regression-ready` to validate against your analysis plan
(or use the CSV directly).
```

## Quality checklist

Before declaring done:
- [ ] Every `variable_contracts[]` entry was applied (none silently skipped)
- [ ] Operation order in the R script matches `references/execution-schema.md` exactly
- [ ] Universe filter applied BEFORE missing_treatment (otherwise excluded rows can change NA counts)
- [ ] Missing_treatment applied BEFORE recode_map (otherwise missing codes get recoded into valid values)
- [ ] Reverse applied AFTER recode_map (otherwise reverse computes against wrong scale)
- [ ] Every `derived_variables[]` rule uses post-rename output names
- [ ] `weight_var_id` column exists in output (if `weight_assignment` was set)
- [ ] `include: false` columns are NOT in the output CSV
- [ ] `rename_to` renames are reflected in CSV column headers
- [ ] If `harmonization_declaration[]` has `code_alignment`: per-code recodes applied
- [ ] If `harmonization_declaration[]` has `na_alignment`: canonical sentinels (99996–99999) appear in output
- [ ] R script is reproducible: `Rscript <stem>-cleaning.R` produces byte-identical CSV
- [ ] `processing_events[]` entry has correct `event_id` (max + 1) and DDI CV `type`
- [ ] Output CSV row count matches `processing_events.summary.output_rows`
- [ ] No existing keys in `ddi-metadata.yaml` were overwritten

## When to stop and ask

Stop and ask the user before doing any of these:

1. The contract is incomplete (any `_needs_review: true` without a
   `variable_contracts` entry)
2. The raw data file is missing or differs from the SHA recorded in
   `study.data_source` (if present)
3. The R script fails with a non-recoverable error (e.g., missing
   variable, type mismatch, parse error in `derivation_rule`)
4. `weight_var_id` references a variable not in the dataset
5. Two `derived_variables[]` rules have the same `output_name` (collision)
6. Output row count is 0 (universe filter excluded everything — likely a bug)

Never silently fix these. The whole point of declare-then-execute is
that the user owns every cleaning decision.
