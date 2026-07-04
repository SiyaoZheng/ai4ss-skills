# `cleaning_contract` Schema Extension

This document defines the `cleaning_contract` top-level block added to
`ddi-metadata.yaml` by the `cleaning-contract` skill. It extends DDI Lifecycle 3.3.
Do not invent fields — use only what is defined here.

---

## Full Schema

```yaml
# ─────────────────────────────────────────────────────────────────────────────
# cleaning_contract block — appended to ddi-metadata.yaml by cleaning-contract
# DDI Lifecycle 3.3 compliant
# ─────────────────────────────────────────────────────────────────────────────

cleaning_contract:

  # ── Universe filter (DDI: Universe) ────────────────────────────────────────
  # Which rows to include in the analysis dataset.
  # Leave condition: null to include all observations.
  universe:
    condition: null              # R expression evaluated on raw data frame.
                                 # Examples:
                                 #   "!is.na(f241)"
                                 #   "age >= 18 & region == 1"
                                 #   "S003 == 156 & S020 == 2018"
    description: null            # Plain-language statement for codebook
    n_excluded: null             # Filled by cleaning-execute after applying filter

  # ── Per-variable contracts (DDI: CleaningOperation > RecodeInstruction) ────
  # One entry per variable that requires any decision.
  # Variables not listed pass through unchanged (codes and missing unchanged).
  variable_contracts:
    - var_id: var001             # Must match variables[].id in this YAML

      # Missing value treatment — extends or overrides missing.codes from codebook-parse
      # DDI: MissingCodeRepresentation
      missing_treatment:
        codes: []                # Additional integer codes to mark as NA
                                 # e.g. [97, 98, 99]
        type: refused            # CV: refused | dont_know | inapplicable |
                                 #     missing_data | other_missing
                                 # Applied to ALL codes listed above
        # For heterogeneous codes (different types), use ranges or per-code:
        per_code: {}             # {code: type} overrides for individual codes
                                 # e.g. {97: refused, 98: dont_know, 99: inapplicable}
        ranges: []               # [{low: 97, high: 99, type: refused}]

      # Recode map — value substitution after missing treatment
      # DDI: RecodeInstruction
      recode_map: {}             # {old_value: new_value}
                                 # e.g. {1: 0, 2: 1}  (binary recode)
                                 # Applied AFTER missing codes are set to NA

      # Scale reversal (ordinal/scale variables only)
      # DDI: RecodeInstruction with computed inverse
      reverse: false             # If true, reverses codes within [min, max] range.
                                 # min/max taken from representation.min/max,
                                 # or from observed range if not set.
                                 # new_value = min + max - old_value

      # Output name in clean dataset
      rename_to: null            # String. If null, keeps original variable name.
                                 # Rename happens last (after recode/reverse).

      # Storage type override (DDI: RecommendedDataType)
      coerce_to: null            # integer | float | string | boolean | null
                                 # Overrides representation.storage_type for output.
                                 # Use when source encoding differs from intended type.

      # Include in analysis dataset
      include: true              # false = variable is dropped from clean output.
                                 # Still recorded in processing_events.

      # Human note for codebook / audit trail
      note: null                 # Free text. Included in processing_events description.

  # ── Shared recode operations (DDI: CleaningOperation, reusable) ────────────
  # Define once, reference by name via shared_recode_ref on variable_contracts.
  # Used when the same na/recode pattern applies across many variables.
  shared_recodes:
    {}
    # Example:
    # standard_na_999:
    #   missing_treatment:
    #     codes: [97, 98, 99]
    #     per_code: {97: refused, 98: dont_know, 99: inapplicable}
    #   recode_map: {}
    #   reverse: false

  # ── Derived variables (DDI: DerivedVariable) ───────────────────────────────
  # Variables constructed from existing variables after cleaning.
  # Added to the clean dataset as new columns.
  derived_variables:
    []
    # Example entries:
    #
    # - id: dvar001
    #   name: trad_media          # Output column name
    #   label: "Traditional media consumption index"
    #   derivation_rule: "rowMeans(cbind(tv_freq, newspaper_freq, radio_freq), na.rm=TRUE)"
    #                              # R expression evaluated on CLEAN data frame
    #   source_variables:          # var_id values this depends on
    #     - var010
    #     - var011
    #     - var012
    #   representation:
    #     type: numeric
    #     storage_type: float
    #   missing:
    #     blank_is_missing: true
    #   note: null
    #
    # - id: dvar002
    #   name: occupation           # conditional_map pattern (from demographic_config)
    #   label: "Occupation category"
    #   derivation_rule: |
    #     dplyr::case_when(
    #       emp_status == 4 ~ "retiree",
    #       emp_status == 6 ~ "student",
    #       emp_status %in% c(5, 7) ~ "unemployed",
    #       isco %in% 11:16 ~ "white_collar",
    #       isco %in% 21:25 ~ "white_collar",
    #       isco %in% 31:34 ~ "blue_collar",
    #       isco %in% 41:42 ~ "peasant",
    #       TRUE ~ NA_character_
    #     )
    #   source_variables: [var008, var009]
    #   representation:
    #     type: code
    #     storage_type: string
    #   note: null

  # ── Weight assignment (DDI: WeightingOperation) ────────────────────────────
  weight_assignment:
    weight_var_id: null          # var_id of the survey weight variable, or null
    normalize: false             # If true, divides weight by mean(weight, na.rm=TRUE)
    note: null

  # ── Analysis variable selection ────────────────────────────────────────────
  # Which output variables to carry forward into regression / IRT.
  # If null, all included variables are forwarded.
  # Maps to regression_spec.yaml pattern (vars_in_model).
  analysis_vars: null            # List of output variable names (post-rename).
                                 # e.g. [sex, age, income, edu, occupation, ...]

  # ── Harmonization declaration (SSSOM-informed cross-study alignment) ─────────
  # Declares how variables in this dataset map to variables in another dataset,
  # using SSSOM (Simple Standard for Sharing Ontology Mappings) metadata.
  # Enables reproducible, machine-readable cross-study variable alignment.
  #
  # TWO LEVELS of alignment:
  #   1. Variable-level    — predicate/justification/confidence (SSSOM mapping triple)
  #   2. Code-level        — per-code source→target with per-code predicate
  #
  # Code-level alignment is OPTIONAL but recommended when scales reverse, codes
  # collapse/split, or missing codes need to map to canonical sentinels.
  harmonization_declaration:
    []
    # Each entry maps one variable from this study to a target study variable.
    # Variable-level fields (REQUIRED): source_variable, target_study,
    # target_variable, predicate, justification, confidence.
    # Code-level fields (OPTIONAL): source_codes, code_alignment, na_alignment,
    # canonical_na.
    #
    # Example 1 — variable-level only (codes already aligned):
    #
    # - source_variable: var005           # var_id in this YAML
    #   target_study: "CGSS 2017"         # Human-readable target study name
    #   target_variable: "a3a"            # Variable name in target study
    #   target_label: "Highest education" # Human-readable label in target study
    #   predicate: skos:exactMatch        # SSSOM mapping predicate:
    #                                      #   skos:exactMatch — semantically identical
    #                                      #   skos:closeMatch — similar but not identical
    #                                      #   skos:broadMatch — this is broader than target
    #                                      #   skos:narrowMatch — this is narrower than target
    #                                      #   skos:relatedMatch — related but not equivalent
    #   justification: "Both variables measure highest education level using
    #                    identical ISCED-11 categories across waves."
    #                                      # Human-readable rationale
    #   confidence: 0.95                  # 0.0–1.0 score of alignment confidence
    #   transformation: null              # R expression to harmonize value coding,
    #                                      # or null if codes are already aligned.
    #                                      # e.g. "{1:0, 2:1, 3:2}" to remap categories
    #   note: null                        # Free-text notes on the mapping
    #
    # Example 2 — with per-code alignment (scale reversal + missing sentinels):
    #
    # - source_variable: var020
    #   target_study: "CGSS 2017"
    #   target_variable: "b5"
    #   target_label: "Trust in central government"
    #   predicate: skos:closeMatch
    #   justification: "Both measure political trust on identical 4-point scale,
    #                    but coding direction differs: this study uses 1=most trust,
    #                    target uses 4=most trust."
    #   confidence: 0.90
    #   transformation: null              # NULL when code_alignment fully describes mapping
    #   note: "Reversed scale, codes 9/97/98/99 → canonical missing sentinels."
    #
    #   # Per-code alignment (SSSOM-informed) — see PLAN.md harmonization_declaration
    #   source_codes:                     # Original coding in this wave (subject)
    #     1: "Most trust"
    #     2: "Some trust"
    #     3: "Little trust"
    #     4: "No trust"
    #     9: "Refused"
    #     97: "Don't know"
    #     99: "Inapplicable"
    #
    #   code_alignment:                   # Source code → canonical with per-code predicate
    #     1: {target: 4, predicate: skos:closeMatch, note: "reversed: source 1=most → target 4"}
    #     2: {target: 3, predicate: skos:closeMatch, note: "reversed"}
    #     3: {target: 2, predicate: skos:closeMatch, note: "reversed"}
    #     4: {target: 1, predicate: skos:closeMatch, note: "reversed: source 4=no trust → target 1"}
    #
    #   na_alignment:                     # Source missing code → canonical sentinel
    #     9:  99997                       # refused
    #     97: 99998                       # don't know
    #     99: 99999                       # inapplicable
    #
    #   canonical_na:                     # Project-wide standardized sentinels
    #                                      # (retroharmonize convention)
    #     refused:       99997
    #     dont_know:     99998
    #     inapplicable:  99999
    #     missing_data:  99996
```

### Per-code alignment field reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_codes` | `{int: str}` | optional | Original code → label in this wave (subject side). Documents what each source code means before harmonization. |
| `code_alignment` | `{int: {target: int, predicate: str, note: str\|null}}` | optional | Per-code source → target mapping with per-code SSSOM predicate. Captures scale reversal, code collapse, code split, etc. |
| `na_alignment` | `{int: int}` | optional | Source missing code → canonical sentinel. Use `canonical_na` values as targets. |
| `canonical_na` | `{refused: int, dont_know: int, inapplicable: int, missing_data: int}` | optional | Project-wide standardized missing sentinels. retroharmonize convention: 99997 / 99998 / 99999 / 99996. Set once per study; reused across all variables. |

**When to use per-code alignment vs. `transformation`:**

- **`code_alignment`**: declarative, machine-readable, auditable. Use when each code has a clear semantic target. Required when missing codes map to canonical sentinels.
- **`transformation`**: imperative R expression. Use when the mapping cannot be expressed as a simple code→code dict (e.g., conditional on another variable, fuzzy text matching, derived computation).

If both are provided, `cleaning-execute` applies `code_alignment` first, then `transformation` on the result.

---

## Operation Order (enforced by cleaning-execute)

```
1.  Read raw data with haven        → preserves variable + value labels
2.  Apply universe filter           → removes excluded rows
3.  Apply missing_treatment         → sets specified codes to NA (per variable)
4.  Apply recode_map                → substitutes values (on non-NA only)
5.  Apply reverse                   → flips scale (on non-NA only)
6.  Apply coerce_to                 → casts storage type
7.  Apply harmonization             → applies code_alignment + na_alignment, if any
8.  Apply rename_to                 → exposes post-rename analysis names
9.  Build derived_variables         → evaluated on cleaned + harmonized frame
10. Apply weight_assignment         → attaches / normalizes weight column
11. Apply include=false drops       → removes excluded columns
12. Select analysis_vars            → final column subset (if not null)
13. Write output CSV
```

---

## DDI Concept Mapping

| `cleaning_contract` field | DDI Lifecycle 3.3 element |
|---|---|
| `universe.condition` | `Universe` |
| `variable_contracts[].missing_treatment` | `CleaningOperation` > `MissingCodeRepresentation` |
| `variable_contracts[].recode_map` | `CleaningOperation` > `RecodeInstruction` |
| `variable_contracts[].reverse` | `CleaningOperation` > `RecodeInstruction` (computed) |
| `variable_contracts[].coerce_to` | `CleaningOperation` > `RecommendedDataType` override |
| `shared_recodes` | `CleaningOperation` (reusable, by reference) |
| `derived_variables[]` | `DerivedVariable` |
| `derived_variables[].derivation_rule` | `GenerationInstruction` |
| `derived_variables[].source_variables` | `SourceVariableReference` |
| `weight_assignment` | `WeightingOperation` |
| `harmonization_declaration[]` | SSSOM `Mapping` — cross-study variable alignment |
| `harmonization_declaration[].predicate` | SSSOM `predicate_id` (SKOS mapping predicate) |
| `harmonization_declaration[].confidence` | SSSOM `confidence` (0.0–1.0) |
| `harmonization_declaration[].justification` | SSSOM `mapping_justification` |
| `harmonization_declaration[].source_codes` | DDI `CategoryScheme` (source-side, per wave) |
| `harmonization_declaration[].code_alignment` | SSSOM per-code `Mapping` (with per-code `predicate_id`) |
| `harmonization_declaration[].na_alignment` | DDI `MissingValuesRepresentation` cross-walk |
| `harmonization_declaration[].canonical_na` | DDI `ManagedMissingValuesRepresentation` (project sentinels) |

---

## Missing Value Type CV

| type | Meaning |
|---|---|
| `refused` | Respondent refused (e.g. 97, 77) |
| `dont_know` | Respondent did not know (e.g. 98, 88) |
| `inapplicable` | Skip logic / structural (e.g. 99, -1) |
| `missing_data` | Data lost or uncollected |
| `other_missing` | Unspecified missingness |

---

## SSSOM Mapping Predicate CV

Use only these SKOS mapping predicates for `harmonization_declaration[].predicate`:

| predicate | Meaning | Use when |
|-----------|---------|----------|
| `skos:exactMatch` | Semantically identical | Variables measure the same construct with identical categories/scale |
| `skos:closeMatch` | Similar but not identical | Variables measure the same construct but differ in scale, wording, or categories |
| `skos:broadMatch` | This variable is broader | This study's variable covers more concepts than the target |
| `skos:narrowMatch` | This variable is narrower | This study's variable covers fewer concepts than the target |
| `skos:relatedMatch` | Related but not equivalent | Variables are conceptually related but measure different constructs |

---

## Shared Recodes Pattern

When the same na-coding pattern applies to many variables (common in Chinese surveys
where 97/98/99 appear on dozens of attitude items), define once in `shared_recodes`
and reference on each variable:

```yaml
shared_recodes:
  cgss_attitude_na:
    missing_treatment:
      per_code: {97: refused, 98: dont_know, 99: inapplicable}
    recode_map: {}
    reverse: false

variable_contracts:
  - var_id: var010
    shared_recode_ref: cgss_attitude_na   # inherits missing_treatment + recode_map
    reverse: true                          # field-level override still applies
    rename_to: majority_leader_implement_ord
```

Field-level values always override `shared_recode_ref`.
