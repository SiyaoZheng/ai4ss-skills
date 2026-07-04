---
name: codebook-parse
description: >
  First step of the DDI survey-cleaning harness. Reads a survey dataset or codebook
  file and produces `ddi-metadata.yaml` — a DDI Lifecycle 3.3–compliant Single Source
  of Truth (SSOT) that all downstream skills consume.

  Trigger on any of: "parse this dataset", "generate codebook metadata", "extract
  variable labels", "create the DDI YAML", "start the cleaning workflow", "document
  this survey file", "what variables does this dataset have", "parse this questionnaire
  PDF", "read the codebook Word file", or any time a user provides a survey file and
  wants to begin cleaning, labelling, or reproducible analysis. Supported inputs:
  Stata .dta, SPSS .sav, SAS .sas7bdat, CFPS YAML wrapper, DDI Codebook 2.5 XML,
  CSV with a companion data dictionary, PDF questionnaire or codebook, Word .docx
  variable documentation.
---

# codebook-parse

You are extracting survey metadata from a source file and writing it into
`ddi-metadata.yaml`, a DDI Lifecycle 3.3–compliant SSOT. Every downstream skill
in the harness reads this file. The core promise of the harness is
*declare-then-execute*: all cleaning choices are written as DDI-compliant metadata
before any data is touched. Your job is to produce that declaration.

Flag uncertainty liberally with `_parse_flags` rather than guessing quietly —
mistakes here propagate silently into every downstream step.

## Reference files — read before acting

| File | When to read |
|---|---|
| `references/format-extraction.md` | Before writing any R code — read the section matching the user's input format |
| `references/ddi-ssot-schema.md` | Before populating the YAML — full field definitions and controlled vocabulary |

## Workflow

### 1 · Identify the input format

Infer from file extension or ask the user:

| Extension / content | Format | Extraction mode |
|---|---|---|
| `.dta` | Stata | Structured (R) |
| `.sav` | SPSS | Structured (R) |
| `.sas7bdat` | SAS | Structured (R) |
| `.yaml` with `content_base64` | CFPS YAML wrapper | Structured (R, decode first) |
| `.xml` with DDI namespace | DDI Codebook 2.5 XML | Structured (R `xml2`) |
| `.csv` + dictionary `.csv` / `.xlsx` | CSV + data dictionary | Structured (R `readr`/`readxl`) |
| `.pdf` | Questionnaire or codebook PDF | **LLM-assisted** (extract text, parse yourself) |
| `.docx` | Word codebook | **LLM-assisted** (R `officer`, then parse) |

**Two extraction modes:**
- **Structured**: R reads schema directly → mechanical YAML population → fewer flags
- **LLM-assisted**: you read the extracted text and map it → more `_parse_flags` expected,
  especially `no_concept`, `type_uncertain`, `codes_incomplete`

When both a PDF/Word codebook *and* a `.dta`/`.sav` file are available, parse the data
file first for variable names and storage types, then use the document to enrich labels
and codes.

Read the matching section in `references/format-extraction.md` now.

### 2 · Extract metadata with R

Write an R script that extracts the following for every variable:

```r
library(haven)
library(labelled)

df <- haven::read_dta("data.dta")   # adjust for format

extraction <- lapply(names(df), function(vname) {
  x <- df[[vname]]
  list(
    name         = vname,
    label        = labelled::var_label(x),
    val_labels   = labelled::val_labels(x),   # NULL if none
    r_class      = class(x)[1],
    r_typeof     = typeof(x),
    n_missing    = sum(is.na(x)),
    min_val      = if (is.numeric(x)) min(x, na.rm = TRUE) else NA,
    max_val      = if (is.numeric(x)) max(x, na.rm = TRUE) else NA
  )
})
```

Run this via Bash and capture the output. Before running, verify the package is
installed: `Rscript -e "library(haven)"`.

For large files (>100k rows), pass `n_max = 0` to `read_dta()` to read schema only.

Watch for negative missing codes — common in Chinese surveys (CFPS, CGSS, CLDS):
```r
sapply(df, min, na.rm = TRUE)   # flag variables with negative minimums
```
These will NOT appear in `val_labels` if they were not explicitly labelled.

### 3 · Map extraction output to SSOT fields

Read `references/ddi-ssot-schema.md` for the full field definitions. Key mappings:

| Extracted value | SSOT field |
|---|---|
| `var_label(df$x)` | `variables[].label` |
| `val_labels(df$x)` (non-missing values) | `variables[].representation.codes` |
| Tagged NAs / user-defined missing | `variables[].missing.codes` |
| Negative codes (inferred missing) | `variables[].missing.codes` + `_parse_flags: [missing_codes_inferred]` |
| `class` = `"haven_labelled"` with codes | `representation.type: code` |
| `class` = `"numeric"` / `"double"`, no labels | `representation.type: numeric` |
| `class` = `"character"` | `representation.type: text` |
| `typeof` = `"integer"` | `representation.storage_type: integer` |
| `typeof` = `"double"` | `representation.storage_type: float` |
| `typeof` = `"character"` | `representation.storage_type: string` |

**Every variable needs these fields populated** (no blanks unless truly absent):
- `id` — sequential: `var001`, `var002`, …
- `name` — exact name from the dataset
- `label` — from source; `null` only if genuinely absent
- `representation.type` — `code | numeric | scale | text | datetime | geographic`
- `representation.storage_type` — `integer | float | string | boolean`
- `missing.blank_is_missing` — default `true`

**Coded variables (`type: code`) also need:**
- `representation.codes` — integer keys, string values
- `representation.classification_level` — `nominal` or `ordinal`
  (default `nominal` if unsure; add `type_uncertain` flag)

Do not invent `concept` or `unit_type` — leave `null`. The researcher fills these.

**Positive missing codes — classify per variable, never globally.**
The most dangerous trap in Chinese survey data: a code like `9` or `88` may be
*valid data* on one variable and *missing* on another. You must check
`val_labels(df$x)` for each variable individually before deciding.

Concrete example from Dickson (2014) / `pgrs_2014.dta`:

| Variable | Code `9` means | Classification |
|---|---|---|
| A3A (`最高学历`) | `9 = 研究生` (postgraduate) | **valid data** → `representation.codes` |
| K6 (`职业类别`) | `9 = 专业技术人员` (professional) | **valid data** → `representation.codes` |
| Q23 (Likert trust items) | `9 = 无回答` (refused) | **missing** → `missing.codes` |
| Any variable | `88 = 不知道` | **always missing** → `missing.codes` |

Rule: A code belongs in `missing.codes` **only** when its label in `val_labels()`
is unambiguously a non-response indicator (refused, don't know, inapplicable,
not applicable, skipped, etc.). If the label is a substantive category, it
belongs in `representation.codes`. When in doubt, set `_parse_flags:
[missing_codes_inferred]` and leave it in `representation.codes` for the
researcher to decide.

Never treat any positive integer code as globally missing across all variables.

### 4 · Look for shared schemas to avoid repetition

Before writing per-variable fields, scan for patterns repeated across 3+ variables:

- **Shared missing codes** (e.g., `-9: refused, -8: dont_know, -1: inapplicable`
  appearing on dozens of variables): define once in `shared_missing_schemas` and
  set `missing.schema_ref` on those variables.

- **Shared response scales** (e.g., same 5-point Likert across attitude items):
  define once in `shared_category_schemes` and set
  `representation.category_scheme_ref` on those variables.

This keeps the YAML maintainable and makes downstream diffs meaningful.

### 5 · Set parse flags

Be generous — flags are prompts for the researcher, not errors:

| Condition | Flag |
|---|---|
| Negative values assumed missing (not labelled) | `missing_codes_inferred` |
| `type` ambiguous (numeric vs ordinal code) | `type_uncertain` |
| Observed values without labels | `codes_incomplete` |
| Source label truncated at 255 chars | `label_truncated` |
| Could not map to a ConceptualVariable | `no_concept` |

**`_needs_review` flag:** Set `_needs_review: true` when the AI confidence in
one or more fields is below threshold. Unlike `_parse_flags` (which categorizes
*what* is uncertain), `_needs_review: true` signals *that a human must verify this
variable before proceeding*. Common triggers:
- `variable.universe` inferred from ambiguous skip logic
- `concept` mapping is a best-guess match
- Multiple `_parse_flags` on the same variable (compound uncertainty)
- Any single field where you're less than ~70% confident in the inference

### 6 · Fill study-level metadata

Populate from the filename, documentation the user provides, or ask:
- `study.name` — dataset name / wave (e.g., "CGSS 2021")
- `study.analysis_unit` — `Person | Household | Organization | Other`
- `study.data_source` — original file path

Leave `study.id`, `study.agency`, `study.wave` as `null`.

For `study.universe`: if the questionnaire PDF or codebook contains a clear
universe statement (e.g., "aged 18 and above", "all registered residents"), set it.
Otherwise leave as `null` — it can be inferred per-variable in the next step.

### 6a · Infer per-variable universe (LLM-assisted, PDF/Word inputs only)

When you have a questionnaire PDF or codebook document, extract skip-logic
patterns to infer `variable.universe` for each variable. This is narrower than
`study.universe` — it describes the subpopulation that was actually asked each
question.

**How to infer:**
1. Scan the questionnaire for skip instructions (e.g., "if employed, go to Q42",
   "only for married respondents", "aged 18–65")
2. Trace the skip chain for each variable — which filter conditions must be
   satisfied for a respondent to reach this question
3. Write the universe as a plain-language statement: e.g., "employed respondents",
   "married women aged 18–49", "all respondents" (no filter)

**Confidence:**
- High confidence: skip logic is explicit in the PDF text → set
  `_needs_review: false`
- Low confidence: ambiguous branching, unclear age filters, or skip logic
  inferred from question wording rather than explicit instructions → set
  `_needs_review: true`

**For structured inputs (.dta, .sav):** skip this step — leave
`variable.universe: null` and `_needs_review: false` on all variables. Per-variable
universe inference requires a questionnaire document.

**Variable ordering:** When the PDF contains skip logic, variables that appear
after a branching point inherit the branch condition as their universe.

### 7 · Write `ddi-metadata.yaml`

Write the file to the user's working directory. Append a processing event:

```yaml
processing_events:
  - event_id: evt001
    type: CleaningOperation
    timestamp: "2026-04-28T00:00:00Z"   # use actual ISO 8601 timestamp
    skill_version: "1.0"
    description: "Initial metadata extraction from source codebook"
    inputs: ["<source file path>"]
    outputs: ["ddi-metadata.yaml"]
    operator: null
```

### 8 · Generate human-readable PDF codebook

After writing `ddi-metadata.yaml`, run the bundled PDF generator:

```bash
python3 <skill-dir>/scripts/generate_pdf_report.py ddi-metadata.yaml
```

This produces `<stem>-codebook.pdf` in the same directory. The PDF contains:
- Cover page with study name, variable count, and data source
- Study metadata section (analysis unit, weight var, observations)
- Full variable reference table (name · label · type · codes · missing · flags)
- Shared category schemes and missing schemas appendix
- Parse flags summary (which variables need manual review)
- Processing events log

Tell the user the PDF path so they can open it directly. The PDF is designed for
sharing with collaborators or students — it replaces ad-hoc codebook printouts.

If `reportlab` is not installed, install it first:
```bash
pip3 install --break-system-packages reportlab
```

### 9 · Generate interactive HTML codebook browser

After the PDF is built, run the HTML browser generator:

```bash
python3 <skill-dir>/scripts/codebook_html.py ddi-metadata.yaml
```

This produces `<stem>-codebook.html` in the same directory — a single-file
interactive browser (no external dependencies, opens in any modern browser).
Useful when collaborators want to filter / search variables instead of
scrolling a static PDF. The HTML includes:

- Search box (filter by variable name, label, or concept)
- Type / role filter chips (code, scale, numeric, text, datetime, geographic; weight, temporal, geographic)
- `_needs_review` flag toggle (surface low-confidence inferences)
- Per-variable detail panel with codes, missing, universe, parse flags
- Shared schemes and processing events accordions

Tell the user both paths (PDF for sharing, HTML for interactive review).
If only one is needed, ask which they prefer — but generating both costs
~1 second and gives the researcher a choice.

## Output quality checklist

Before declaring done:
- [ ] Every variable has `id`, `name`, `label`, `representation.type`, `storage_type`
- [ ] Every coded variable has `codes` populated (or `category_scheme_ref` set)
- [ ] Every missing code entry has a `type` from the CV (`refused | dont_know | inapplicable | missing_data | other_missing`)
- [ ] `_parse_flags` set wherever inference was uncertain
- [ ] `_needs_review: true` set on variables with low-confidence inferences
- [ ] `variable.universe` populated for PDF/Word inputs where skip logic is clear
- [ ] Shared missing schemas defined where the same pattern repeats across variables
- [ ] `processing_events` entry appended
- [ ] PDF codebook generated and path reported to researcher
- [ ] HTML codebook browser generated and path reported to researcher

## Brief to the researcher

After writing the file, give a short summary:
- Total variables parsed; how many are fully labelled vs. flagged
- How many have `_needs_review: true` (require manual verification)
- How many have `variable.universe` inferred vs. left null
- Most common flag and what it means
- What to fill in manually before running `cleaning-contract` (concept, unit_type,
  study.universe, any `_needs_review: true` variables)

Then say: "Review flagged variables in `ddi-metadata.yaml`, fill the `null` fields you
know, then run `cleaning-contract` to declare your recoding decisions."
