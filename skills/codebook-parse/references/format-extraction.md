# Codebook Extraction Guide by Input Format

This reference covers how to extract DDI-compliant metadata from each supported input format.
Read the section matching the user's input, then populate `ddi-metadata.yaml`.

---

## Stata `.dta` (via `haven`)

Stata files carry rich metadata natively: variable labels, value labels, missing value tags.

```r
library(haven)
library(labelled)

df <- haven::read_dta("data.dta")

# Variable labels → variables[].label
var_labels <- labelled::var_label(df)

# Value labels → variables[].representation.codes
val_labels <- labelled::val_labels(df)

# Stata tagged NAs (.a, .b, … .z) → variables[].missing.codes
# haven reads them as NA with a "tag" attribute
tagged <- haven::na_tag(df$varname)   # returns letter tag

# Inspect all at once
labelled::look_for(df)                # nice overview table
```

**Mapping rules:**
- `var_label(df$x)` → `variables[].label`
- `val_labels(df$x)` → `variables[].representation.codes` (non-missing values only)
- Tagged NAs (`.a`–`.z`) → `variables[].missing.codes` (infer type from label)
- Untagged `NA` → `blank_is_missing: true`
- `class(df$x)`:
  - `"haven_labelled"` with codes → `type: code`
  - `"numeric"` no labels → `type: numeric`
  - `"character"` → `type: text`

**Watch for negative missing codes (common in Chinese surveys):**
Codes like `-9`, `-8`, `-3` appear as regular numeric values in Stata. They will NOT be in
`val_labels` if not labelled. Inspect the minimum values:
```r
sapply(df, min, na.rm = TRUE)   # flag variables with negative minimums
```

---

## SPSS `.sav` (via `haven`)

```r
df <- haven::read_sav("data.sav")

# Same API as Stata — var_label(), val_labels() work identically
# SPSS user-missing values are encoded as tagged NAs in haven
```

**Additional SPSS-specific:**
- SPSS system missing (`$sysmis`) → `blank_is_missing: true`
- SPSS user-defined missing values (declared in MISSING VALUES command) → `missing.codes`

---

## SAS `.sas7bdat` (via `haven`)

```r
df <- haven::read_sas("data.sas7bdat", catalog_file = "formats.sas7bcat")
# catalog_file is needed to get value labels — without it, only codes appear
```

**Note:** SAS format catalogs are often separate files. If the user has only the data file,
`representation.codes` will be empty and `_parse_flags` should include `"codes_incomplete"`.

---

## CFPS YAML (China Family Panel Studies)

CFPS distributes data as base64-encoded `.dta` inside a YAML wrapper with codebook metadata.

```yaml
# Structure of CFPS YAML
source_file: "cfps2020person_202306.dta"
source_format: "dta"
content_base64: |
  <base64 encoded DTA file>
```

**Extraction steps:**
```r
library(yaml)
library(base64enc)

cfg <- yaml::read_yaml("cfps2020person_202306.yaml")
raw <- base64enc::base64decode(cfg$content_base64)
tmp <- tempfile(fileext = ".dta")
writeBin(raw, tmp)
df <- haven::read_dta(tmp)
```
Then proceed as with `.dta` above. The embedded DTA carries all labels.

**CFPS missing code conventions:**
| Code | Meaning | type |
|------|---------|------|
| -8 | 不知道 (don't know) | `dont_know` |
| -9 | 拒绝回答 (refused) | `refused` |
| -1 | 不适用 (not applicable) | `inapplicable` |
| -2 | 缺失 (missing) | `missing_data` |

---

## DDI Codebook 2.5 XML (via `xml2` or `rddi`)

```r
library(xml2)

doc <- xml2::read_xml("codebook.xml")
ns <- c(ddi = "ddi:codebook:2_5")

# Variable labels
vars <- xml2::xml_find_all(doc, "//ddi:var", ns)
for (v in vars) {
  name  <- xml2::xml_attr(v, "name")
  label <- xml2::xml_text(xml2::xml_find_first(v, "ddi:labl", ns))
  # value labels
  cats  <- xml2::xml_find_all(v, "ddi:catgry", ns)
}
```

**Using `rddi` (DDI Codebook 2.5 R interface):**
```r
# rddi provides typed DDI element constructors — useful for output, less for input
# For reading, xml2 is more direct
```

---

## CSV with companion data dictionary

Some datasets ship as `data.csv` + `codebook.csv` (or Excel).
Common column names in the dictionary file:

| Column | Maps to |
|--------|---------|
| `variable` / `name` | `variables[].name` |
| `label` / `description` | `variables[].label` |
| `type` | `variables[].representation.type` |
| `values` / `codes` | `variables[].representation.codes` |
| `missing` | `variables[].missing.codes` |

Parse with `readr::read_csv()` or `readxl::read_excel()`, then map column by column.

---

## PDF Questionnaire or Codebook

Survey questionnaires and variable codebooks distributed as PDF are the dominant format
for Chinese datasets (CGSS, CFPS, CLDS, CHFS) and many international ones. Unlike
`.dta`/`.sav` files, PDFs have no machine-readable schema — extraction is **LLM-assisted**:
extract the text, then read it yourself and map to the SSOT schema.

### Step 1: Extract text with R

```r
library(pdftools)

# Raw text (one string per page)
pages <- pdftools::pdf_text("questionnaire.pdf")
full_text <- paste(pages, collapse = "\n--- PAGE BREAK ---\n")
cat(full_text)

# For PDFs with tables, position-aware extraction gives better column alignment
page_data <- pdftools::pdf_data("questionnaire.pdf")   # returns list of data frames
```

If `pdftools` is not available: `install.packages("pdftools")` (needs `poppler` system lib).
On macOS: `brew install poppler` first.

Alternatively, read the PDF directly with the `Read` tool — Claude can parse the
visual layout of a PDF page.

### Step 2: Parse the extracted text

Read the extracted text and identify the following for each question / variable:

| What to find in the PDF | Maps to |
|---|---|
| Variable name in brackets, e.g. `[Variable: educ]` | `variables[].name` |
| Question text / item label | `variables[].label` |
| Numeric response option table (Code → Label) | `variables[].representation.codes` |
| Scale anchor labels (e.g. 1=Strongly disagree … 5=Strongly agree) | `representation.type: scale` with `anchors` |
| Free-text answer | `representation.type: text` |
| Numeric / continuous answer with range stated | `representation.type: numeric` with `min`, `max` |
| Special codes listed below the scale (e.g. -9=Refused) | `variables[].missing.codes` |
| Topcode note (e.g. "9,999,997 or more") | `representation.topcode` |
| Skip instruction ("If No, skip to Q12") | note in `derivation_rule` as plain text |

**Repeated scales**: if many consecutive items share the same scale and the same missing
codes (common in attitude batteries), extract the scale once into `shared_category_schemes`
and the missing codes into `shared_missing_schemas`, then reference them.

### Step 3: Cross-validate with the data file (if available)

When both a PDF codebook and a `.dta`/`.sav` file are available:
1. Parse the data file first (get variable names, observed value ranges, storage types)
2. Use the PDF to fill or enrich `label`, `codes`, `missing.codes`
3. Flag discrepancies: if PDF lists code `97 = Other` but the variable has no observed
   value 97, add `codes_incomplete`

### Flags for PDF-derived variables

PDF extraction is inherently uncertain — flag liberally:

```yaml
_parse_flags:
  - no_concept           # Always: PDFs rarely carry explicit conceptual metadata
  - type_uncertain       # If the response format is ambiguous (scale vs code vs numeric)
  - codes_incomplete     # If you could not find the full response list in the PDF
  - label_truncated      # If the question text was very long (>255 chars)
  - missing_codes_inferred  # If you inferred missing codes from context, not explicit listing
```

---

## Word Document Codebook (`.docx`)

Some studies distribute variable documentation as Word files. Use the `officer` package:

```r
library(officer)

doc     <- officer::read_docx("codebook.docx")
content <- officer::docx_summary(doc)

# content is a data frame with columns: content_type, text, ...
# Text paragraphs:
paragraphs <- content[content$content_type == "paragraph", "text"]

# Tables (most codebooks embed variable × description tables):
tables <- content[content$content_type == "table cell", ]
# Columns: text, row_id, cell_id  — reconstruct table with reshape
```

**Parsing strategy**: reconstruct each Word table into a data.frame, then map columns
to SSOT fields using the same heuristic as the CSV dictionary (column name matching table
in the CSV section below). If the document uses running prose instead of tables, treat
it like a PDF: extract text and parse with LLM assistance.

---

## What to flag with `_parse_flags`

After extraction, set flags on variables where automated inference is uncertain:

```yaml
_parse_flags:
  - missing_codes_inferred   # Negative values assumed missing — researcher must verify
  - type_uncertain           # Could be ordinal or nominal — check classification_level
  - codes_incomplete         # Some observed values have no label
  - label_truncated          # Source label was longer than 255 chars
  - no_concept               # Could not map to a ConceptualVariable — fill manually
```

These flags are **not errors** — they are prompts for the researcher to review. The
`audit-verify` skill will check that no flags remain before signing off.
