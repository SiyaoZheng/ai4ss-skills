---
name: latex-tables
description: |
  Generate publication-ready regression tables in LaTeX using booktabs style.
  Use when: (1) converting regression output to LaTeX, (2) formatting summary statistics,
  (3) standardizing table style for journal submission (AEA, APSR, etc.).
---

# LaTeX Tables

## Purpose

This skill creates clean, publication-ready tables in LaTeX for regression results and summary statistics, using standard academic formatting.

## When to Use

- Converting model output into LaTeX tables
- Standardizing table style across a paper
- Adding notes, significance stars, and labels

## Instructions

Follow these steps to complete the task:

### Step 1: Understand the Context

Before generating any code, ask the user:

- What type of table is needed (regression, summary stats, balance)?
- What software produced the results (Stata, R, Python)?
- Which formatting style is required (journal-specific, AEA, etc.)?

### Step 2: Generate the Output

Based on the context, generate LaTeX code that:

1. **Uses `booktabs`** for clean horizontal rules
2. **Includes labels and captions** for referencing in the paper
3. **Adds notes** for standard errors and significance
4. **Aligns numeric columns** for readability

### Step 3: Verify and Explain

After generating output:

- Explain how to compile the table
- Highlight any assumptions in the formatting
- Suggest refinements for journal submission

### Step 4: Generate HTML preview

After writing the `.tex` file, run the bundled HTML preview generator so the
researcher can sanity-check the table without compiling LaTeX:

```bash
python3 <skill-dir>/scripts/table_html.py <stem>.tex
```

This produces `<stem>-table-preview.html` in the same directory — a
single-file rendering of the table (HTML + booktabs-style CSS, no external
deps). The preview surfaces formatting bugs that are invisible in raw .tex
(e.g., missing column alignment, broken header rows, misaligned significance
stars) before you spend time on a full LaTeX compile.

Tell the user the preview path. If the table looks wrong in the preview,
fix the .tex source before sharing or compiling.

## Example Prompts

- "Create a regression table with three models in LaTeX"
- "Format summary statistics with mean and sd columns"
- "Add significance stars and standard error notes"

## Example Output

```latex
% ============================================
% Regression Table
% ============================================
\begin{table}[htbp]\centering
\caption{Effect of Treatment on Outcome}
\label{tab:main_results}
\begin{tabular}{lccc}
\toprule
 & (1) & (2) & (3) \\
\midrule
Treatment & 0.125*** & 0.118*** & 0.102** \\
 & (0.041) & (0.039) & (0.046) \\
Controls & No & Yes & Yes \\
Fixed Effects & No & Yes & Yes \\
\midrule
Observations & 2,145 & 2,145 & 2,145 \\
R-squared & 0.18 & 0.24 & 0.31 \\
\bottomrule
\end{tabular}
\begin{tablenotes}
\small
\item Notes: Standard errors in parentheses. * p<0.10, ** p<0.05, *** p<0.01.
\end{tablenotes}
\end{table}
```

## Requirements

### Software

- LaTeX distribution (TeX Live or MikTeX)

### Packages

- `booktabs`
- `threeparttable` (optional for notes)

## Best Practices

1. **Keep tables compact** and readable
2. **Use consistent notation** for standard errors and stars
3. **Provide clear captions and labels**

## Common Pitfalls

- Overly wide tables that do not fit the page
- Missing notes for standard errors
- Inconsistent labeling across tables

## References

- [LaTeX booktabs documentation](https://ctan.org/pkg/booktabs)
- [AEA Author Guidelines](https://www.aeaweb.org/journals/policies/author-instructions)
