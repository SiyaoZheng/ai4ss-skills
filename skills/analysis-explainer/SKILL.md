---
name: analysis-explainer
description: |
  Transform statistical analysis results into detailed technical documentation for methodologist collaborators. Generates comprehensive Markdown summaries with full methodological specifications, suitable for co-authors who need to understand every technical decision.

  **Use this skill proactively** when the user:
  - Says "explain my analysis results" or "explain these results"
  - Says "write up the findings" or "summarize the analysis"
  - Says "create a summary for collaborators"
  - Says "解释分析结果", "撰写结果说明", "写一下分析结果"
  - Has analysis outputs (figures, tables, regression results) and needs documentation
---

# Analysis Explainer

## Overview

This skill generates detailed technical documentation of statistical analysis results. The output is designed for **methodologist collaborators** who need to understand the analysis thoroughly.

## Full-Auto Harness Contract

When invoked by an automatic research harness, this skill must not pause for
human choice or return any terminal no-progress state. It must gather all available outputs, explain them in precise
social-science language, and produce Markdown/PDF material that can feed a
publication-level `paper/full_draft.pdf`. Missing figures, tables, or logs
trigger automatic search/rerun requests to upstream analysis skills rather than
a conservative summary.

Only explain empirical outputs that trace to real observed public or authorized
data. If tables, figures, estimates, or model inputs are synthetic, simulated,
hypothetical, illustrative, generated, DGP-created, random-draw,
benchmark-calibrated, or literature-parameter-imputed, do not summarize them as
findings. Route to `public-data-sources`, `research-data-builder`,
`research-analysis-runner`, or `methods-reviewer` for repair.

## .aiss State Machine

When invoked from an AI4SS research-factory workspace, locate
`.ai4ss/research_model.aiss` and run
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` before choosing
or returning `next_skill_route`. Starts, completions, failures, and watchdog
heartbeat observations should be recorded as `.aiss` `event` declarations or
returned as deterministic `aiss.py transition --event ...` fragments. Events
do not replace semantic updates: result explanations that change claims or
limits must still update the relevant `claim`, `check`, `decision`, or
`artifact` declarations.

## Core Principle: Complete Results First

**The documentation must contain ALL results from the analysis—every figure, every table, every key statistic.**

The primary goal is to present results comprehensively. Technical details explain the methodology; they do not replace the results themselves.

## Audience

- **Methodologists** who will scrutinize technical choices
- **Co-authors** who need to understand and discuss findings
- **Reviewers** who want to see complete results with methodological transparency

Assume readers are experts. Focus on *what was found* and *how it was computed*, not on explaining basic statistical concepts.

## Workflow

### Step 1: Collect ALL Analysis Outputs

Gather every output file:

1. **Figures**: Read ALL image files (PNG, PDF) — these must be embedded in the final document
2. **Tables**: Read all generated tables (CSV, DOCX) — reproduce them in full
3. **Code**: Read the analysis script to understand method specifications
4. **Logs**: Check for any logged statistics or diagnostics
5. **Source status**: Confirm data provenance and observed-data-only status when
   the outputs will feed a manuscript or PDF.

### Step 2: Embed Results

**Every figure and table must appear in the document.** Use markdown image syntax:

```markdown
![Figure caption](path/to/figure.png)
```

For tables from DOCX or CSV, convert them to markdown tables and include ALL rows/columns.

### Step 3: Add Technical Details

For each method used, document:

- What method was used (name, variant)
- Key parameters (e.g., number of bootstrap iterations, random seed)
- Why this method (brief justification if non-obvious)
- Validation checks performed

**Do NOT include raw code.** Describe methods in prose with specific parameter values.

**Good**: "Bootstrap 95% CIs computed using 200 resamples with percentile method (seed=123)."

**Bad**: Pasting the actual R/Python code.

### Step 4: Write the Document

Structure:

```markdown
# [Analysis Name]: Technical Summary

## Overview
[1-2 sentences]

## Data
- Sample size, sources, key restrictions
- Variable definitions (concise table format)

## Methods
[Prose description of each method with key parameters]

## Results

### [Section 1]
[Text describing findings]

![Figure 1 caption](figure1.png)

[Table with complete data]

### [Section 2]
[Continue with all results...]

## Technical Notes
[Assumptions, limitations, validation checks]
```

### Step 5: Convert to PDF

Use pandoc with image embedding:

```bash
pandoc input.md -o output.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V mainfont="Times New Roman" \
  -V fontsize=11pt \
  --resource-path=/path/to/images
```

**For wide tables**: Use landscape orientation or smaller font for tables that might overflow.

## Output Specifications

### Completeness Checklist

Before finalizing, verify:
- [ ] Every figure from the analysis is embedded
- [ ] Every table is included with all rows and columns
- [ ] All key statistics are reported (coefficients, SEs, CIs, p-values, R², N)
- [ ] Method parameters are specified (iterations, seeds, thresholds)

### Language
- **Always write in English**
- Technical terminology should be precise

### Length
No constraints. Include everything needed for complete results presentation.

## Formatting Guidelines

### Tables
- Use concise column headers
- Align numbers properly
- For wide tables with many columns, consider splitting or using abbreviations
- Always include sample size (N) and fit statistics (R², AIC, etc.)

### Figures
- Always embed with `![caption](path)`
- Provide informative captions explaining what to look for
- Reference figures in the text

### Numbers
- Coefficients/effect sizes: 3 decimal places (e.g., 0.247)
- Standard errors: 3 decimal places in parentheses
- R²: 3 decimal places
- P-values: report exact or use thresholds (p < 0.001)
- Sample sizes: integers with commas (177,807)

## Example Structure

```markdown
# Treatment Effect Analysis: Technical Summary

## Overview
This analysis estimates the causal effect of a policy intervention on economic outcomes.

## Data
N = 50,000 from administrative records (2015-2022). Sample restricted to eligible individuals.

| Variable | Type | Description |
|----------|------|-------------|
| treatment | Binary | Policy exposure (0/1) |
| outcome | Continuous | Log earnings |
| ... | ... | ... |

## Methods

### Difference-in-Differences
Two-way fixed effects with unit and time FE. Clustered SEs at unit level. Pre-trend test: joint F-test on leads.

### Robustness
Event study specification with 4 leads and 6 lags. Bacon decomposition for heterogeneity diagnostics.

## Results

### Main Effects

The policy increased earnings by 8.5% on average.

![Event study coefficients](event_study.png)

| Specification | Estimate | SE | 95% CI | N |
|---------------|----------|-----|--------|---|
| Baseline | 0.085 | 0.021 | [0.044, 0.126] | 50,000 |
| With controls | 0.079 | 0.019 | [0.042, 0.116] | 48,500 |

### Heterogeneity

[Subgroup analysis table]

![Heterogeneous effects by age](heterogeneity_age.png)

## Technical Notes
- Pre-trends: F(4, 999) = 1.23, p = 0.29
- Parallel trends assumption supported by visual inspection
```

## Resources

- `references/style-guide.md` - Writing style guidelines
