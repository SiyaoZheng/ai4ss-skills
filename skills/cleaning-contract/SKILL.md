---
name: cleaning-contract
description: >
  Second step of the DDI survey-cleaning harness. Reads `ddi-metadata.yaml`
  (produced by `codebook-parse`) and guides the researcher in declaring all
  recoding decisions as DDI Lifecycle 3.3–compliant metadata in a new
  `cleaning_contract` block — before any data is touched.

  Trigger on any of: "declare my recoding decisions", "write the cleaning
  contract", "set up recodes", "which variables need recoding", "how should I
  handle missing codes", "set up my analysis variables", "I want to recode
  this survey", "configure the cleaning step", "define universe filter",
  "set missing values", or any time the user has `ddi-metadata.yaml` and
  wants to specify how to clean it before running `cleaning-execute`.

  Precondition: `ddi-metadata.yaml` should exist in the working directory.
  In full-auto harness mode, if it does not exist, infer and create it through
  codebook-parse behavior before writing the contract.
---

# cleaning-contract

You are helping the researcher declare all cleaning decisions as
DDI Lifecycle 3.3–compliant metadata in `ddi-metadata.yaml`.
The core promise of the harness is *declare-then-execute*: no data is
touched until every decision is written down. Your job is to produce that
declaration — the `cleaning_contract` block.

**Do not execute any cleaning.** Do not write R code that modifies data.
Only write YAML.

**You are picking up where `codebook-parse` left off.** The YAML already
contains `shared_missing_schemas`, per-variable `missing.codes`, and
`missing.schema_ref` assignments written by `codebook-parse`. Start from
that existing state — do not re-derive or overwrite it.

## Full-Auto Harness Contract

When invoked by an automatic research harness, this skill must not pause for
human choice or return any terminal no-progress state. It must create a complete `cleaning_contract` from DDI metadata, source
labels, codebook text, variable roles, and analysis-plan context. Ambiguous
missing codes, universe filters, weights, derived variables, harmonization, and
analysis variables receive the strongest defensible automatic choice plus an
audit note; they do not wait for external confirmation. The contract must be
ready for `cleaning-execute` and ultimately for a publication-level
`paper/full_draft.pdf`.

## .aiss State Machine

When this DDI harness is invoked from an AI4SS research-factory workspace, locate
`.ai4ss/research_model.aiss` and run
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` before choosing
or returning `next_skill_route`. Starts, completions, failures, and watchdog
heartbeat observations should be recorded as `.aiss` `event` declarations or
returned as deterministic `aiss.py transition --event ...` fragments. Events
do not replace the DDI SSOT: cleaning rules and inferred choices still belong
in the `cleaning_contract` block.

## Reference files — read before acting

| File | When to read |
|---|---|
| `references/contract-schema.md` | Before writing any YAML — full field definitions and operation order |

## Workflow

### 1 · Verify precondition

Check that `ddi-metadata.yaml` exists in the working directory. If it does not,
locate the likely survey/codebook input, generate the DDI metadata using
`codebook-parse` behavior, and then continue.

Read `references/contract-schema.md` now before proceeding.

### 2 · Audit the existing metadata

Run a Python audit of `ddi-metadata.yaml` to understand what
`codebook-parse` already handled and what still needs decisions. Compute:

```python
import yaml
with open("ddi-metadata.yaml") as f:
    d = yaml.safe_load(f)

vars = d["variables"]
shared_schemas = d.get("shared_missing_schemas", {})

total = len(vars)
with_schema_ref = [v for v in vars if v["missing"]["schema_ref"]]
with_explicit_codes = [
    v for v in vars
    if not v["missing"]["schema_ref"] and v["missing"]["codes"]
]
with_missing_codes_inferred = [
    v for v in vars if "missing_codes_inferred" in v.get("_parse_flags", [])
]
no_missing_treatment = [
    v for v in vars
    if not v["missing"]["schema_ref"]
    and not v["missing"]["codes"]
    and "missing_codes_inferred" not in v.get("_parse_flags", [])
]
scale_vars = [v for v in vars if v["representation"]["type"] == "scale"]
weight_vars = [v for v in vars if v.get("is_weight")]
```

Record an audit summary:

```
=== ddi-metadata.yaml audit ===

Total variables: {total}
Shared missing schemas defined by codebook-parse: {len(shared_schemas)} schemas,
  covering {len(with_schema_ref)} variables via schema_ref

Already handled by codebook-parse:
  {len(with_schema_ref)} variables — schema_ref assigned (no action needed)
  {len(with_explicit_codes)} variables — explicit missing.codes defined (audit against source labels)

Needs audited defaults:
  {len(with_missing_codes_inferred)} variables — missing_codes_inferred flag
  {len(no_missing_treatment)} variables — no missing treatment of any kind

Other:
  {len(scale_vars)} scale variables (check for reversal needs)
  {len(weight_vars)} weight variable(s): {[v['name'] for v in weight_vars]}
```

If `missing_codes_inferred` count is 0 and `no_missing_treatment` is small,
record that most missing treatment is already resolved.

### 3 · Resolve flagged variables automatically (CRITICAL)

**This is the most dangerous step.** Variables with
`_parse_flags: [missing_codes_inferred]` had their missing codes guessed
by `codebook-parse` without codebook confirmation. Resolve each one using
source labels, response-category language, observed values, and the positive
missing-code trap rules below.

⚠️ **Positive missing code trap**: in Chinese surveys, the same value (e.g.
9) can be missing on one item (9=无回答) and valid data on another
(9=博士, 9=专业技术人员). Always check the full `codes:` block for the
variable before confirming any code as missing. A code is missing ONLY
if its label explicitly signals non-response.

For each `missing_codes_inferred` variable, inspect:

```
var_id: {var_id}   name: {name}
label: {label}
type: {representation.type}
All value labels: {representation.codes}   ← CHECK THESE FIRST
Inferred missing codes: {missing.codes}
```

Automatically classify the inferred codes. Variables where the inferred codes
are wrong need an explicit `variable_contracts` entry with corrected
`missing_treatment` and an audit note explaining the source-label basis.

Variables where the inferred codes are RIGHT need NO `variable_contracts`
entry — the existing `missing.codes` in the YAML will be used by
`cleaning-execute` directly.

### 4 · Check unhandled variables

Inspect the `no_missing_treatment` list. Most will be:
- ID variables, year/wave variables, string variables → no missing codes needed
- Structural skip variables already handled by `schema_ref` in a different run
- Genuinely missing-treatment-free (e.g. weights, panel IDs)

For any that need missing value treatment, infer the codes and types from labels
and observed values, and add to `variable_contracts`.

Skip contract entries if all `no_missing_treatment` variables are IDs, dates, or
weights. Do not create review-only work.

### 5 · Recode maps and scale reversals

Infer from source labels, variable names, codebook sections, and analysis-plan
context:

**5a · Binary and categorical recodes** — use `recode_map` when categories
must be collapsed or recoded for analysis:

```yaml
- var_id: var005       # hukou type
  recode_map:
    1: 0    # agricultural → non-urban
    2: 1    # urban → urban
    3: 1    # blue-stamp → urban
    4: 1    # resident → urban
  rename_to: hukou_urban
```

**5b · Scale reversal** — use `reverse: true` when the scale direction is
inverted relative to the analysis convention (e.g. codebook says
1=most trusted, but analysis convention is 1=least trusted):

```yaml
- var_id: var006
  reverse: true
  rename_to: trust_central_ord
```

**Shared recodes** — if the SAME pattern (same codes + same recode_map +
same reversal) applies to 3 or more variables, define it once in
`shared_recodes` and use `shared_recode_ref`. Distinguish these from
`shared_missing_schemas` already in the YAML (which handle missing codes
only — `shared_recodes` can handle the full operation including recode_map
and reverse).

Example — CGSS trust block, 5 items with identical 97/98/99 missing and
same reversal:

```yaml
shared_recodes:
  cgss_trust_recode:
    missing_treatment:
      per_code: {97: refused, 98: dont_know, 99: inapplicable}
    recode_map: {}
    reverse: false

variable_contracts:
  - var_id: var020
    shared_recode_ref: cgss_trust_recode
    reverse: true           # per-variable override
    rename_to: trust_central_ord
```

Do NOT duplicate a `shared_recode_ref` missing pattern that is already
covered by the variable's `missing.schema_ref`. If the variable already
has `schema_ref: cgss_standard_99`, only add a `variable_contracts` entry
if you need to add `recode_map`, `reverse`, or `rename_to`.

### 6 · Universe filter

Infer from context:

> "Who should be included in the analysis? Provide an R expression
> evaluated on the raw data frame, or 'all' to include everyone."

Common patterns to recognize and suggest:
- Country filter in comparative surveys: `S003 == 156` (China in WVS)
- Wave filter: `S020 == 2018`
- Non-respondent exclusion: `!is.na(f241)`
- ABS Wave 5 China subsample: `Country == 840` ← check the actual country code in this dataset
- Age restriction: `age >= 18`

Write:
```yaml
cleaning_contract:
  universe:
    condition: "<R expression or null>"
    description: "<plain-language statement>"
    n_excluded: null    # filled by cleaning-execute
```

### 7 · Derived variables

Infer derived variable definitions from the route/design/analysis plan. If no
derived variable is required for the declared inquiry, set `derived_variables:
[]`.

**Required information for each derived variable**:
- Output name (`name`)
- R expression evaluated on the CLEAN data frame (`derivation_rule`)
- Which source variables it depends on (`source_variables`)
- Representation type

**Important**: all names in `derivation_rule` refer to POST-RENAME names
(i.e., `rename_to` values if set, otherwise original variable names).

Common patterns:

**Row-mean index**:
```yaml
- id: dvar001
  name: trad_media
  label: "Traditional media consumption index"
  derivation_rule: "rowMeans(cbind(tv_freq, newspaper_freq, radio_freq), na.rm=TRUE)"
  source_variables: [var010, var011, var012]
  representation:
    type: numeric
    storage_type: float
```

**Conditional category (case_when)**:
```yaml
- id: dvar002
  name: occupation
  label: "Occupation category"
  derivation_rule: |
    dplyr::case_when(
      emp_status == 4 ~ "retiree",
      emp_status == 6 ~ "student",
      emp_status %in% c(5, 7) ~ "unemployed",
      isco %in% 11:25 ~ "white_collar",
      isco %in% 31:34 ~ "blue_collar",
      isco %in% 41:42 ~ "peasant",
      TRUE ~ NA_character_
    )
  source_variables: [var_emp_status, var_isco]
  representation:
    type: code
    storage_type: string
```

### 8 · Weight assignment

The audit in Step 2 already identified weight variables (`is_weight: true`).
Use the detected weight variable when exactly one plausible weight exists. Use
the analysis-plan or survey documentation to decide normalization; otherwise set
`normalize: false` and record the assumption.

```yaml
weight_assignment:
  weight_var_id: var695    # or null
  normalize: false
  note: null
```

If `is_weight: true` is not set on any variable, infer likely weights from names
and labels (`weight`, `wt`, `wgt`, `pweight`, `sample weight`). If none are
credible, set `weight_var_id: null`.

### 9 · Analysis variable selection

Infer from `regression_spec.yaml`, `.aiss` design declarations, analysis-plan
files, variable roles, and derived-variable dependencies:

```yaml
analysis_vars:
  - idnum
  - sex
  - age
  - edu
  - income
  - occupation
  - trust_central_ord
  - ...
```

If no narrower analysis set is defensible, set `analysis_vars: null` to keep all
variables.

### 9a · Harmonization declaration (cross-study alignment)

If the design implies pooling, cross-wave comparison, or external validation,
create SSSOM-informed variable alignment declarations. Skip this step if the
analysis is single-study.

**When to offer this step:**
- Researcher mentions comparing results with a previous wave (e.g., "compare
  CGSS 2021 with CGSS 2017")
- Researcher mentions harmonizing variables across datasets
- Researcher uses words like "pool", "combine", "cross-walk", "align", "map"

For each variable that needs alignment, infer **variable-level fields** (REQUIRED):

1. **Target study** — name of the dataset to align with
2. **Target variable** — variable name in the target study
3. **Target label** — human-readable label in the target study
4. **Predicate** — SSSOM mapping predicate from the CV:
   - `skos:exactMatch` — semantically identical
   - `skos:closeMatch` — similar but not identical
   - `skos:broadMatch` — this variable is broader
   - `skos:narrowMatch` — this variable is narrower
   - `skos:relatedMatch` — related but not equivalent
5. **Justification** — plain-language rationale for the mapping
6. **Confidence** — 0.0–1.0 score
7. **Transformation** — R expression to remap value codes (or null if aligned)

Then collect **per-code alignment fields** (OPTIONAL but recommended when codes
differ across waves):

8. **Source codes** (`source_codes`) — original `{int: label}` in this wave.
   Copy from `variable.representation.codes`.
9. **Code alignment** (`code_alignment`) — per-code `{source: {target, predicate, note}}`.
   Required when scales reverse, codes collapse/split, or sentinel codes need remapping.
10. **NA alignment** (`na_alignment`) — `{source_missing_code: canonical_sentinel}`.
    Required when source uses non-canonical missing codes (e.g., 9, 97, 99) and
    you want to standardize to project-wide sentinels.
11. **Canonical NA** (`canonical_na`) — project-wide sentinels. Set ONCE per study
    using retroharmonize convention: `{refused: 99997, dont_know: 99998,
    inapplicable: 99999, missing_data: 99996}`.

**When to offer per-code alignment:**
- Scale direction differs (e.g., 1=most trust vs. 4=most trust)
- Code count differs (e.g., 4-point vs. 5-point scale)
- Source missing codes need to map to canonical sentinels
- Skip if `predicate: skos:exactMatch` AND codes already aligned

Write to `harmonization_declaration`:

```yaml
harmonization_declaration:
  # Example 1 — variable-level only (codes already aligned)
  - source_variable: var005
    target_study: "CGSS 2017"
    target_variable: "a3a"
    target_label: "Highest education level"
    predicate: skos:exactMatch
    justification: "Both variables measure highest education level using
                     identical ISCED-11 categories across waves."
    confidence: 0.95
    transformation: null
    note: null

  # Example 2 — with per-code alignment (scale reversal + missing sentinels)
  - source_variable: var020
    target_study: "CGSS 2017"
    target_variable: "b5"
    target_label: "Trust in central government"
    predicate: skos:closeMatch
    justification: "Both measure political trust on identical 4-point scale,
                     but coding direction differs."
    confidence: 0.90
    transformation: null
    note: "Reversed scale, missing codes mapped to canonical sentinels."

    source_codes:
      1: "Most trust"
      2: "Some trust"
      3: "Little trust"
      4: "No trust"
      9: "Refused"
      97: "Don't know"
      99: "Inapplicable"

    code_alignment:
      1: {target: 4, predicate: skos:closeMatch, note: "reversed: source 1=most → target 4"}
      2: {target: 3, predicate: skos:closeMatch, note: "reversed"}
      3: {target: 2, predicate: skos:closeMatch, note: "reversed"}
      4: {target: 1, predicate: skos:closeMatch, note: "reversed"}

    na_alignment:
      9:  99997  # refused
      97: 99998  # dont_know
      99: 99999  # inapplicable

    canonical_na:
      refused:      99997
      dont_know:    99998
      inapplicable: 99999
      missing_data: 99996
```

If the researcher is not doing cross-study work, set `harmonization_declaration: []`.

### 10 · Write `cleaning_contract` to `ddi-metadata.yaml`

**Append only.** Preserve all existing content — `variables`,
`shared_missing_schemas`, `shared_category_schemes`, `processing_events`,
etc. Never overwrite or restructure existing top-level keys.

Structure to append:

```yaml
cleaning_contract:
  universe:
    condition: ...
    description: ...
    n_excluded: null
  variable_contracts:
    - ...           # one entry per variable needing changes;
                    # omit variables already fully handled by schema_ref
  shared_recodes:
    {}              # or named entries if repeated patterns exist
  derived_variables:
    []              # or list of dvar entries
  weight_assignment:
    weight_var_id: ...
    normalize: false
    note: null
  analysis_vars: null   # or list of names
  harmonization_declaration:
    []              # or list of SSSOM mapping entries
```

Then append to `processing_events`:

```yaml
processing_events:
  - event_id: evt002        # increment: find max event_id in existing events + 1
    type: CleaningOperation
    timestamp: "<ISO 8601 now>"
    skill_version: "1.0"
    description: "Researcher declared cleaning contract: universe=<filter or all>, <N> variable contracts, <M> derived variables, weight=<var_name or none>"
    inputs: ["ddi-metadata.yaml"]
    outputs: ["ddi-metadata.yaml"]
    operator: null
```

### 11 · Brief the researcher

After writing, give a compact summary:

```
Cleaning contract written to ddi-metadata.yaml.

  Universe:             <condition or "all observations">
  Variable contracts:   <N> (schema_ref covers <K> more automatically)
  Shared recodes:       <M> patterns defined
  Derived variables:    <P>
  Harmonization maps:   <H> SSSOM alignments declared
  Weight:               <var_name or none>
  Analysis vars:        <count or "all">

Run `cleaning-execute` to produce:
  - <stem>-clean.csv        analysis-ready dataset
  - <stem>-cleaning.R       reproducible R script
  - Updated processing_events audit trail in ddi-metadata.yaml
```

## Quality checklist

Before declaring done:
- [ ] Did NOT re-declare missing treatment for variables with `schema_ref` already set (unless overriding)
- [ ] Every `_parse_flags: [missing_codes_inferred]` variable has been automatically resolved or carried with an audit note
- [ ] No code marked as missing without checking `representation.codes` for that specific variable
- [ ] Positive missing trap: variables like A3A (9=doctorate) and K6 (9=professional) have 9 NOT in `missing_treatment`
- [ ] Every `reverse: true` variable is actually a scale item (`representation.type: scale`)
- [ ] All `derivation_rule` expressions use post-rename output names
- [ ] `weight_var_id` matches an `id` in `variables[]`
- [ ] `event_id` in new `processing_events` entry is max(existing event_ids) + 1
- [ ] `n_excluded` left as null
- [ ] Every `harmonization_declaration` entry has a valid SSSOM `predicate` from the CV
- [ ] Every `harmonization_declaration` entry has a non-empty `justification`
- [ ] `harmonization_declaration[].confidence` is between 0.0 and 1.0
- [ ] If `code_alignment` is present: every source code key exists in `source_codes` (or matches a missing code from `na_alignment`)
- [ ] If `code_alignment` is present: every per-code `predicate` is from the SSSOM CV (skos:exactMatch | closeMatch | broadMatch | narrowMatch | relatedMatch)
- [ ] If `na_alignment` is present: every target value matches a value in `canonical_na`
- [ ] If `canonical_na` is set: uses retroharmonize convention (refused=99997, dont_know=99998, inapplicable=99999, missing_data=99996)
- [ ] Only APPENDED to `ddi-metadata.yaml` — no existing keys overwritten
