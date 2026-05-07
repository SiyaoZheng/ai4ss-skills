# Survey Data Harmonization: Tools, Patterns, and Relevance to Our Pipeline

Research report — 2026-04-30

---

## 1. retroharmonize (R package)

**Source**: [retroharmonize.dataobservatory.eu](https://retroharmonize.dataobservatory.eu/) | [GitHub](https://github.com/dataobservatory-eu/retroharmonize) | CRAN v0.2.0

### What it is

retroharmonize is an R package for **retrospective (ex-post) survey data harmonization** — making already-collected surveys from different sources, waves, or organizations comparable. Developed by Daniel Antal under rOpenGov, primarily targeting Eurobarometer, Afrobarometer, and similar cross-national repeated surveys.

### Core data model

retroharmonize introduces two custom S3 classes that extend the `haven` ecosystem:

1. **`survey`** — a data frame (tibble) that carries metadata attributes from the source file: original filename, wave identifier, row-level unique IDs. Think of it as a metadata-enriched tibble.

2. **`labelled_spss_survey`** — extends `haven::labelled_spss`. Unlike the parent class, it preserves:
   - Variable labels
   - Value labels (named integer codes)
   - User-defined missing value ranges (`na_range`)
   - User-defined missing values (`na_values`)
   - **Origin tracking**: original variable name, original value codes, original labels, survey ID

   This class is the key innovation. Standard `haven::labelled` allows inconsistent missing value handling across vectors, making concatenation unsafe. `labelled_spss_survey` enforces consistency, so vectors from different surveys can be safely bound by row.

### Harmonization workflow

The package follows a **metadata-first, imperative execution** pattern:

```
Import → Metadata extraction → Crosswalk table → Harmonize names → Harmonize values → Merge → Document
```

**Step 1 — Import**: `read_surveys()` / `read_spss()` / `read_dta()` / `read_csv()` load files into `survey` objects with full metadata.

**Step 2 — Metadata extraction**: `metadata_create()` builds an inventory table from all surveys: variable names, labels, value codes, missing ranges, types. This is the "mental map" for planning.

**Step 3 — Crosswalk table**: `crosswalk_table_create()` generates an initial crosswalk from the metadata. Researchers edit this table to declare variable name mappings, value label harmonization targets, and type conversions. The crosswalk is the central planning artifact.

**Step 4 — Variable name harmonization**: `harmonize_var_names(survey_list, metadata)` renames variables across all surveys using a metadata mapping table (`old` → `new` column names).

**Step 5 — Value harmonization**: `harmonize_values()` is the core function. For a single vector, it:
   - Takes a `harmonize_labels` specification: `from` (regex patterns matching original labels), `to` (canonical label names), `numeric_values` (target codes)
   - Takes `na_values`: named vector mapping canonical missing labels to sentinel codes (e.g., `do_not_know = 99997`, `inap = 99999`)
   - Produces a `labelled_spss_survey` vector with harmonized coding, preserving original coding as metadata attributes

   Example:
   ```r
   harmonize_values(var1,
     harmonize_labels = list(
       from = c("^tend\\sto|^trust", "^tend\\snot|not\\strust", "^dk|^don", "^inap"),
       to = c("trust", "not_trust", "do_not_know", "inap"),
       numeric_values = c(1, 0, 99997, 99999)
     ),
     na_values = c(do_not_know = 99997, inap = 99999)
   )
   ```

**Step 6 — Bulk harmonization**: `harmonize_survey_values(survey_list, .f)` applies a user-supplied function `.f` to every `labelled_spss_survey` variable across all surveys, then row-binds them into a single data frame. Missing variables across surveys are filled with appropriate NA values.

**Step 7 — Documentation**: `document_survey_item()` produces a provenance record showing: current and historic coding, value labels, variable name history, survey ID history. `document_surveys()` / `create_codebook()` / `codebook_waves_create()` generate full codebooks.

### How it handles key problems

| Problem | retroharmonize approach |
|---------|------------------------|
| **Variable name differences** | Metadata mapping table + `harmonize_var_names()` |
| **Value label mismatch** | Regex-based label matching in `harmonize_values()` — `from` patterns match multiple spellings |
| **Missing code alignment** | Standardized sentinel codes (99997=DK, 99998=declined, 99999=inap) via `na_values` parameter |
| **Missing ranges vs discrete missing** | `na_range_to_values()` converts SPSS-style ranges to discrete `na_values` |
| **Type inconsistency** | `as_numeric()` / `as_factor()` / `as_character()` converters |
| **Concatenation safety** | `labelled_spss_survey` class enforces metadata match before binding |
| **Crosswalk planning** | `crosswalk_table_create()` + `crosswalk_surveys()` / `crosswalk()` for end-to-end execution |
| **Reproducibility** | Original coding preserved as metadata attributes on every harmonized vector |

### Strengths and limitations

**Strengths**:
- Metadata is never discarded — every harmonized vector carries its pre-harmonization state
- Regex-based label matching handles real-world label inconsistencies gracefully
- Crosswalk table pattern separates planning from execution
- Well-integrated with the `haven`/`labelled` ecosystem

**Limitations**:
- **Imperative, not declarative** — harmonization logic is R code (functions), not data (YAML/JSON). This makes it harder for non-R users and harder to validate programmatically.
- **No concept of "structurally inapplicable" vs "don't know"** — the `na_values` mechanism distinguishes types by sentinel code value, not by semantic category. The user must manually assign 99997/99998/99999.
- **No cross-wave variable mapping** — designed for cross-survey (different studies) rather than cross-wave (same study, different timepoints) harmonization. Variable name changes across waves must be handled manually.
- **Single function per vector** — `harmonize_values()` applies one harmonization function per vector. Complex multi-step recodes require chaining.

---

## 2. Other Harmonization Tools and Approaches

### 2.1 psHarmonize (R package)

**Source**: [CRAN](https://cran.r-project.org/package=psHarmonize) | [GitHub](https://github.com/nudacc/psharmonize)

An R package for multi-cohort data harmonization, designed for clinical/epidemiological research (NUDACC project). Key design pattern: **spreadsheet-driven harmonization**.

- **Harmonization sheet** — an Excel spreadsheet or data.frame that serves as the single source of truth for all recoding instructions. Columns: `id_var`, `item` (output name), `study`, `domain`, `source_dataset`, `source_item`, `visit`, `code_type` ("recode category" or "function"), `code1` (the actual recode), `coding_notes`, `possible_range`.
- **Two operation types**: `recode category` (explicit value mapping like `1 = Yes`) and `function` (arbitrary R expression using `x` as input).
- **Multi-variable input**: `source_item` can list multiple variables separated by semicolons, referenced as `x1`, `x2` in the function.
- **Multi-step variables**: can reference previously harmonized variables via `source_dataset: "previous_dataset"`.
- **Output**: harmonized long-format and wide-format datasets, plus error logs and summary reports.

**Relevance to us**: The harmonization-sheet pattern is essentially what our `cleaning_contract` YAML does — a declarative instruction set that drives execution. psHarmonize validates the "spreadsheet as contract" approach.

### 2.2 CharmStats / QuickCharmStats (GESIS)

**Source**: [PLOS ONE paper (Winters & Netscher, 2016)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0147795) | GESIS

Desktop software developed at GESIS — Leibniz Institute for the Social Sciences. Java-based, open-source, stores metadata in MySQL.

- **Concept-first workflow**: starts with the measured concept, moves to operationalization of target and source variables, facilitates recoding, generates SPSS/Stata syntax.
- **Metadata captured**: variable name, label, definition, response option values and labels, level of measurement, question wording, source study info, literature references, coding decision notes.
- **DDI-native**: built on DDI metadata standards. Stores metadata on variables, categories, and classification schemes.
- **Peer-reviewable output**: generates reports with DOI assignment at GESIS, making harmonization decisions citable and auditable.
- **Scale**: used to manage 21,500+ variables in the IntermediaPlus longitudinal dataset.

**Relevance to us**: CharmStats demonstrates that **metadata-first, documentation-as-output** is a viable and valuable pattern. Our `processing_events` audit trail and codebook generation follow the same philosophy. The concept-first approach (start from what you're measuring, not from what variables exist) is worth adopting.

### 2.3 DDI-Based Variable Crosswalks

**Source**: [DDI Alliance](https://ddialliance.org/comparison-crosswalk) | DDI Lifecycle 3.3

DDI Lifecycle provides native support for variable-level comparison and harmonization:

- **Comparison module**: allows pairwise comparison of variables across datasets, recording semantically meaningful relationships (equivalent, derived, subset, etc.).
- **Variable cascade**: a DDI concept where a conceptual variable (what you want to measure) maps to a represented variable (how it's measured in a specific study), enabling cross-study comparison at the conceptual level.
- **Colectica**: commercial tool that implements DDI-Lifecycle variable harmonization, using the `RepresentedVariable` item type to document harmonized variables.

**DDI-CDI (Cross-Domain Integration)**: the newest DDI specification, designed for cross-domain data integration. Covers Wide, Long, Multi-Dimensional, and Key-Value data structures. Used by the European Social Survey for cross-domain integration processing.

### 2.4 CESSDA Tools

**Source**: [CESSDA](https://cessda.eu) | [Metadata Office](https://cessda.eu/Metadata-Office)

- **CESSDA Metadata Validator (CMV)**: validates DDI metadata records against DDI Profiles — machine-actionable XML constraints specifying which DDI fields are required.
- **CESSDA Data Catalogue**: harvests DDI 2.5/3.2 metadata via OAI-PMH, enabling cross-archive discovery.
- **European Question Bank (EQB)**: question-level metadata across European surveys.

### 2.5 SDTL (Structured Data Transformation Language)

**Source**: [DDI Alliance Products](https://ddialliance.org/products)

An independent intermediate language for representing data transformation commands. Designed to be tool-agnostic: captures what a transformation does (recode, merge, filter) in a standardized format regardless of whether the execution happens in R, Stata, SPSS, or Python. This is the closest existing standard to a "declarative cleaning instruction" format.

---

## 3. Design Patterns in Survey Harmonization

### 3.1 Declarative vs Imperative

| Approach | Examples | Pros | Cons |
|----------|----------|------|------|
| **Imperative** (R/Python code) | retroharmonize `.f` functions | Flexible, handles edge cases | Hard to audit, not portable, requires programming skill |
| **Declarative** (YAML/sheet) | psHarmonize harmonization sheet, our `cleaning_contract` | Auditable, portable, LLM-writable | Limited expressiveness for complex transforms |
| **Hybrid** | CharmStats (declarative metadata → generated syntax) | Best of both worlds | More complex tooling |

**Industry consensus**: Declarative-first with escape hatches for complex logic. psHarmonize's `code_type: function` allows arbitrary R expressions. Our `derivation_rule` field follows the same pattern. The key insight is that 80% of harmonization operations are simple recodes that should be declarative; the remaining 20% need code.

### 3.2 Metadata-First vs Code-First

All serious frameworks are **metadata-first**: you describe what the variable is and what it should become before writing any transformation code. retroharmonize's `metadata_create()` → `crosswalk_table` → `harmonize` sequence is the canonical pattern. CharmStats goes further by starting from the **concept** level (what are we trying to measure?) before touching variables.

### 3.3 Missing Value Taxonomy

The most important design decision in survey harmonization is how to classify missing values. The frameworks converge on a taxonomy:

| Type | retroharmonize | psHarmonize | Our contract | LIS Data Center |
|------|---------------|-------------|--------------|-----------------|
| Refused | `na_values["declined"]` = 99998 | `NA` | `refused` | System missing |
| Don't know | `na_values["do_not_know"]` = 99997 | `NA` | `dont_know` | System missing |
| Structurally inapplicable | `na_values["inap"]` = 99999 | `NA` | `inapplicable` | Not applicable (universe) |
| Missing by skip logic | (not distinguished from inap) | `NA` | `inapplicable` | Skip pattern |
| Data lost/uncollected | (not distinguished) | `NA` | `missing_data` | System missing |

**Critical distinction**: "structurally inapplicable" (this person can never have a valid value — e.g., "age at menarche" for males) vs "missing by skip logic" (this person could have answered but wasn't asked due to routing) vs "don't know" (asked but respondent couldn't answer). retroharmonize handles all three through `na_values` sentinel codes but doesn't enforce semantic distinction. Our `cleaning_contract` schema uses `per_code` type mapping, which is more precise.

The **positive missing code trap** (identified in our cleaning-contract skill) is a real problem in Chinese surveys where the same integer can be a valid code on one variable and a missing code on another. This is why per-variable missing treatment (not global) is essential.

### 3.4 Crosswalk Tables

The crosswalk table is the universal planning artifact across all frameworks:

- **retroharmonize**: `crosswalk_table` data frame with columns for original/harmonized names, codes, labels
- **DDI Lifecycle**: Comparison module with pairwise variable comparisons
- **psHarmonize**: harmonization sheet with source→target mappings
- **CharmStats**: MySQL-backed crosswalk with full provenance

A crosswalk table is essentially a **variable-level concordance** — it declares "this code in this survey means the same thing as that code in that survey."

---

## 4. Relevance to Our Pipeline

### 4.1 Current State: cleaning-contract + cleaning-execute

Our existing pipeline (`cleaning-contract` skill + contract-schema.md) already implements many of the best practices found in the literature:

- **Declarative YAML** for cleaning decisions (like psHarmonize's harmonization sheet)
- **DDI Lifecycle 3.3 mapping** for every field (like CharmStats' DDI-native approach)
- **Shared recodes** for repeated patterns (like retroharmonize's bulk harmonization)
- **Processing events audit trail** (like CharmStats' report generation)
- **Operation order enforcement** (10-step pipeline in contract-schema.md)

### 4.2 What's Missing: Harmonization Declarations

Our current `cleaning_contract` operates on a **single survey at a time**. It handles:
- Missing value treatment
- Recode maps
- Scale reversals
- Derived variables
- Universe filters

But it does NOT handle **cross-wave or cross-survey harmonization** — the problem of making variables from different sources comparable. This is what retroharmonize and CharmStats are designed for.

**Recommendation**: Extend the SSOT to include a `harmonization_declaration` block that covers:

```yaml
harmonization_declaration:
  # Cross-wave variable mapping: same concept, different names across waves
  variable_mappings:
    - concept: "trust_in_central_government"
      label: "Trust in central government (ordinal)"
      mappings:
        - wave: 2010
          var_id: var020
          original_name: "a3a"
        - wave: 2013
          var_id: var045
          original_name: "a3_a"
        - wave: 2017
          var_id: var062
          original_name: "Q28a"

  # Cross-wave value label alignment
  value_label_crosswalks:
    - concept: "trust_institutional_5pt"
      canonical_codes: {1: "very_trust", 2: "trust", 3: "neutral", 4: "distrust", 5: "very_distrust"}
      canonical_na: {97: refused, 98: dont_know, 99: inapplicable}
      wave_variants:
        - wave: 2010
          source_codes: {1: "Very much trust", 2: "Trust", 3: "Neither", 4: "Not trust", 5: "Not at all", 97: "Refused", 98: "DK", 99: "NA"}
        - wave: 2017
          source_codes: {1: "非常信任", 2: "比较信任", 3: "一般", 4: "不太信任", 5: "完全不信任", 97: "拒绝回答", 98: "不知道", 99: "不适用"}
```

### 4.3 Cross-Wave Variable Mapping

The key challenge is that the same concept may be measured with different:
- Variable names (CGSS 2010: `a3a` vs CGSS 2017: `Q28a`)
- Value labels (English vs Chinese, different abbreviations)
- Code assignments (1=most trust in one wave, 5=most trust in another)
- Missing code conventions (97/98/99 in some waves, 77/88/99 in others)

**Recommendation**: The `harmonization_declaration` should be a **wave-agnostic concept map** — it declares what the concept is and how each wave measures it, independent of any single wave's cleaning contract. Each wave's `cleaning_contract` then references the harmonization declaration to ensure consistency.

### 4.4 Right Abstraction Level for Recode Maps

Our current `recode_map` in `variable_contracts` is a simple `{old: new}` integer mapping. This works for single-variable recodes but doesn't scale to cross-wave harmonization where:
- The same concept has different source codes per wave
- The target coding must be consistent across all waves
- Missing codes must be aligned globally

**Recommendation**: Keep the current `recode_map` for within-wave recodes (it's simple and works). Add a separate `value_label_crosswalks` section for cross-wave alignment that references multiple waves' source codes and maps them to a single canonical coding. The cleaning-execute skill would then consult both: within-wave recodes from `variable_contracts` and cross-wave alignment from `harmonization_declaration`.

### 4.5 Should SSOT Include Harmonization Declarations?

**Yes**, but as a separate top-level block, not inside `cleaning_contract`. Reason:

1. `cleaning_contract` is **wave-specific** — it declares what to do with one wave's data
2. Harmonization declarations are **wave-spanning** — they define the target state across all waves
3. The two have different lifecycles: a cleaning contract is written once per wave; a harmonization declaration evolves as new waves are added

Proposed structure:

```yaml
ddi-metadata.yaml:
  variables: [...]                    # from codebook-parse
  shared_missing_schemas: {...}       # from codebook-parse
  cleaning_contract: {...}            # from cleaning-contract (wave-specific)
  harmonization_declaration: {...}    # NEW — cross-wave, wave-spanning
  processing_events: [...]            # append-only audit trail
```

---

## 5. Concrete Recommendations

### 5.1 Add `harmonization_declaration` block to ddi-metadata.yaml

Schema sketch:

```yaml
harmonization_declaration:
  # Target coding for cross-wave variables
  target_variables:
    - concept_id: trust_central
      label: "Trust in central government"
      measurement_level: ordinal
      canonical_codes: {1: very_trust, 2: trust, 3: neutral, 4: distrust, 5: very_distrust}
      canonical_na: {97: refused, 98: dont_know, 99: inapplicable}
      reverse_if_needed: true   # some waves may code 1=most trust, others 5=most trust

  # Wave-level bindings
  wave_bindings:
    - wave_id: cgss_2010
      bindings:
        - concept_id: trust_central
          source_var_id: var020
          source_codes: {1: "非常信任", 2: "信任", ...}
          code_alignment: identity  # or {1:5, 2:4, 3:3, 4:2, 5:1} if reversed
          na_alignment: {97: 97, 98: 98, 99: 99}
```

### 5.2 Adopt the Crosswalk Table Pattern

retroharmonize's `crosswalk_table` is the right planning artifact. Before writing any cleaning contract, generate a crosswalk table that inventories:
- All variables across all waves
- Their original names, labels, codes, missing conventions
- Proposed canonical names and codings

This should be an intermediate output of the `codebook-parse` skill when processing multiple waves.

### 5.3 Standardize Missing Value Sentinels

Adopt a project-wide convention aligned with retroharmonize's defaults but with semantic typing:

```yaml
project_na_sentinels:
  refused: 99997
  dont_know: 99998
  inapplicable: 99999
  missing_data: 99996
  other_missing: 99995
```

Use these sentinels in harmonized output. Source-wave missing codes (97/98/99, 77/88/99, etc.) are mapped to these sentinels by the cleaning contract.

### 5.4 Document-as-You-Go (from CharmStats)

Every harmonization decision should produce a provenance record. Our `processing_events` already does this for cleaning operations. Extend it to record harmonization decisions:

```yaml
processing_events:
  - event_id: evt010
    type: HarmonizationDecision
    timestamp: "2026-04-30T10:00:00Z"
    description: "Aligned trust_central coding across waves 2010-2017: canonical 1=very_trust..5=very_distrust, waves 2010/2013 reversed (source 1=most trust)"
    affected_concepts: [trust_central]
    affected_waves: [cgss_2010, cgss_2013, cgss_2017]
```

### 5.5 Separate Within-Wave from Cross-Wave Operations

| Operation | Scope | Where declared | When executed |
|-----------|-------|----------------|---------------|
| Missing value treatment | Single wave | `cleaning_contract.variable_contracts` | `cleaning-execute` per wave |
| Recode map | Single wave | `cleaning_contract.variable_contracts` | `cleaning-execute` per wave |
| Scale reversal | Single wave | `cleaning_contract.variable_contracts` | `cleaning-execute` per wave |
| Variable renaming | Single wave | `cleaning_contract.variable_contracts` | `cleaning-execute` per wave |
| Cross-wave name alignment | All waves | `harmonization_declaration` | Post-cleaning merge step |
| Cross-wave code alignment | All waves | `harmonization_declaration` | Post-cleaning merge step |
| Cross-wave missing alignment | All waves | `harmonization_declaration` | Post-cleaning merge step |

---

## 6. Summary of Sources

| Source | Type | Key Takeaway |
|--------|------|--------------|
| [retroharmonize](https://retroharmonize.dataobservatory.eu/) | R package | Regex-based label matching, `labelled_spss_survey` class, crosswalk tables |
| [psHarmonize](https://cran.r-project.org/package=psHarmonize) | R package | Spreadsheet-driven declarative harmonization, two operation types |
| [CharmStats](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0147795) | Desktop software | Concept-first, DDI-native, peer-reviewable harmonization documentation |
| [DDI Alliance](https://ddialliance.org/comparison-crosswalk) | Standard | Variable comparison module, crosswalk/concordance support |
| [DDI-CDI](https://ddialliance.org/ddi-cdi) | Standard | Cross-domain integration, model-driven, syntax-agnostic |
| [CESSDA](https://cessda.eu/Metadata-Office) | Infrastructure | DDI Profiles, Metadata Validator, OAI-PMH harvesting |
| [LIS Data Center](https://www.lisdatacenter.org/techdoc/lis_missing.pdf) | Documentation | Three-type missing taxonomy (refused, inapplicable, skip pattern) |
| [Winters & Netscher 2016](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0147795) | Paper | Proposed standards for harmonization documentation |
