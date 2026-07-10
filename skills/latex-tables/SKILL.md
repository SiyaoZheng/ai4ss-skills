---
name: latex-tables
description: >
  Design and produce honest, readable LaTeX tables for empirical political-science research. Use for
  descriptive, balance, measurement, regression, causal-estimate, heterogeneity, mechanism, robustness,
  and model-comparison tables; converting verified outputs to LaTeX; repairing misleading or unreadable
  tables; and integrating tables into a paper. Triggers include "LaTeX table", "regression table",
  "summary statistics", "publication table", "回归表", "描述性统计表", "论文表格".
---

# LaTeX Tables

Construct tables as compact empirical arguments. Selection and ordering of quantities should make the
relevant comparison, estimand, sample, and uncertainty available for scrutiny.

## Tables and interpretive record

The work should leave:

1. a verified `.tex` table tied to the actual statistical output;
2. reproducible table-generation code when the project supports it;
3. a compiled or HTML-rendered preview; and
4. a short **Table Interpretation Note** explaining the table's evidentiary job, important comparisons,
   sample or estimand changes, and interpretation limits.

## Constructing the table

### 1. Establish the table's job

Determine whether the table describes the sample, validates a measure, assesses balance, presents a
primary estimand, compares theoretically meaningful heterogeneity, investigates mechanisms, or examines
a specific vulnerability. Prefer one coherent job over a kitchen-sink table.

### 2. Trace every displayed quantity

Read the code and model output. Verify coefficients or quantities, uncertainty, outcome scale, sample,
weights, fixed effects, clustering, reference categories, omitted periods, transformations, and model
fit. Do not transcribe numbers from screenshots or invent absent statistics.

### 3. Choose rows and columns substantively

Order specifications to show a reasoned comparison. Make changes in sample, estimand, treatment,
outcome, controls, fixed effects, weights, or uncertainty visible. Do not imply that columns estimate the
same quantity when they do not. Do not select models by significance or hide inconvenient estimates.

### 4. Design for reading

Use `booktabs`, clear grouping, meaningful labels, aligned numbers, whitespace, and concise notes. Put
units in labels or headings. Prefer confidence intervals or standard errors appropriate to the field and
design; significance stars may be included when expected, but they must not carry the argument.

Avoid vertical rules, decorative complexity, tiny type, unexplained abbreviations, and excessively wide
tables. Split a table when different panels serve different questions.

### 5. Write an informative caption and notes

State what is estimated, for whom, and over what period. Notes should disclose uncertainty, clustering,
weights, fixed effects, sample restrictions, transformations, reference categories, and multiple-testing
adjustments when these matter. Do not use notes to bury a changed sample or estimand.

### 6. Render and verify

Compile the containing document when possible. The bundled preview can provide a fast first check:

```bash
python3 <skill-dir>/scripts/table_html.py <table>.tex
```

Inspect alignment, headers, notes, width, symbols, escaping, and legibility. Compare rendered values with
the source output and, when requested, verify that the manuscript references the correct table.

### 7. Interpret and revise

Write the table interpretation note. If the layout reveals incomparable models, unstable samples,
opaque estimands, selective reporting, or an argument that depends only on stars, revise the table or
analysis rather than polishing around the problem.

## Criteria for judgment

- Every value is traceable to verified output.
- Rows and columns express a substantive comparison.
- The estimand, sample, scale, and uncertainty are visible.
- Model changes are transparent.
- The table remains readable at manuscript size.
- Captions and notes support scrutiny without overclaiming.
- Rendering is verified, not assumed from raw LaTeX.

Follow the project's existing R, Python, Stata, and LaTeX practice. Discuss software only when it affects
the reported quantities or the integrity of the table.
