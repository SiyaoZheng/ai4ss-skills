# Empirical Audit Checklist

Use this checklist to review social-science empirical work.

## Data

- Unit of observation is stated and matches the data.
- ID and time variables are unique at the claimed grain.
- Raw data are not overwritten.
- Merge rates and unmatched records are reported.
- Sample restrictions are explicit and reproducible.
- Missingness for core variables is reported.
- Generated variables have documented construction rules.

## Design

- Research question maps to estimand.
- Treatment/exposure definition is visible.
- Timing is well-defined.
- Comparison group is defensible.
- Identification assumption is stated.
- Anticipation, spillovers, selection, and measurement threats are considered when relevant.

## Specification

- Fixed effects match the design and data grain.
- Controls are not post-treatment unless justified.
- Weights are explained.
- Standard errors are clustered at the appropriate level or sensitivity is shown.
- Transformations have interpretable units.

## Diagnostics And Robustness

- Main diagnostics address the identifying assumption.
- Robustness checks vary one meaningful choice at a time.
- Placebo tests have a clear null.
- Multiple outcomes or subgroups are handled transparently.
- Mechanism tests are not presented as proof without design support.

## Reproducibility

- Scripts run in numbered order.
- Outputs are written to stable paths.
- Logs include commands and failures.
- Seeds and package versions are recorded when stochastic steps are used.
- Manuscript tables and figures can be traced to scripts.

## Claims

- Causal language matches design strength.
- Results are not generalized beyond sample and setting.
- Null, mixed, or fragile results are not hidden.
- Policy implications are tied to the estimate and external validity.
