---
name: did-expert
description: >
  DID and panel causal inference guide. Covers modern estimators (CS, SA, BJS, fect, synthdid, augsynth),
  TWFE pitfalls, parallel trends, event study, HonestDiD, wild cluster bootstrap, multiple testing,
  placebo tests, and writing up results.
  Triggers: "DID", "event study", "staggered treatment", "parallel trends", "TWFE", "HonestDiD",
  "synthdid", "fect", "panel data", "wild cluster bootstrap", "placebo test", "DDD",
  "Romano-Wolf", "writing up DID".
---

# DID Expert

Guide for applying Difference-in-Differences methods in applied research, grounded in Baker, Callaway, Cunningham, Goodman-Bacon & Sant'Anna (2025, JEL) and the Callaway & Sant'Anna (2021) R `did` package.

## Full-Auto Harness Contract

When invoked by an automatic research harness, this skill must not pause for
human choice or return any terminal no-progress state. It must inspect panel structure, choose the strongest defensible DID or
panel estimator automatically, implement diagnostics, rerun code, and write
bounded identification language for a publication-level `paper/full_draft.pdf`.
If DID is not credible, select the nearest defensible panel/descriptive design
and state the limitation in the draft-facing claim boundary.

Synthetic-control-family estimators are methods, not permission to create
synthetic empirical rows. The panel, treatment timing, outcomes, covariates, and
analysis inputs must come from real observed public or authorized data. If the
panel cannot be acquired or verified, route to `public-data-sources` or
`study-design-builder` rather than fabricating a panel.

## .aiss State Machine

When invoked from an AI4SS research-factory workspace, locate
`.ai4ss/research_model.aiss` and run
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` before choosing
or returning `next_skill_route`. Starts, completions, failures, and watchdog
heartbeat observations should be recorded as `.aiss` `event` declarations or
returned as deterministic `aiss.py transition --event ...` fragments. Events
do not replace semantic updates: DID diagnostics, estimator choices, repairs,
and bounded-identification language must still update the relevant `mida`,
`check`, `decision`, `artifact`, or `claim` declarations.

## Implementation Gate

Before diagnosing DID results, make the analysis script rerunnable from a clean process. Use `Rscript --vanilla`, load every required package explicitly, create output directories in code, and define every plot/table object before use. Errors such as `object '<plot>' not found`, missing package functions, or stale figure files are implementation repairs to complete before DID diagnostics.

After editing DID plotting or estimation code, rerun the full script and assert that every declared diagnostic table and figure exists. If the script fails, fix that failure before interpreting pre-trends, placebo tests, or estimator differences.

## Core Principle: 2x2 Building Blocks

All DID designs are aggregations of 2x2 comparisons. Each building block has:
1. A **target parameter** (ATT)
2. A **parallel trends assumption** for identification
3. An **estimation approach** (sample means, regression, DR, IPW)

## Unified Decision Tree

```
Step -1: Understand your data (see pre-analysis.md)
→ Panel structure, treatment variable, raw trends, covariates, missingness
→ This is 90% of the work. Do NOT skip to estimator selection.

Step 0: Is your panel balanced?
├── YES → Step 1
├── NO — Mild imbalance, PT plausible
│   ├── Primary: cdid (est_method = "2-step")
│   ├── Alternative: did (allow_unbalanced_panel = TRUE)
│   └── Then proceed to Step 1 for estimator choice
├── NO — Severe imbalance / rotating panel
│   ├── Primary: cdid (est_method = "Identity")
│   ├── Alternative: did (panel = FALSE, treat as RCS)
│   └── fect (mc) handles sparse data natively
├── NO — PT questionable + imbalance
│   └── fect (ife or mc) — relaxes PT + handles gaps
├── NO — Endogenous attrition (missingness correlated with treatment)
│   └── Bounds: Rathnayake et al. (2024); fect balance.period sensitivity
└── Repeated cross-sections (no unit tracking)
    └── did (panel = FALSE)

Step 1: Choose estimator (see estimators.md)
├── Binary absorbing treatment, staggered?
│   ├── PT plausible → did (DR), sunab, didimputation
│   ├── PT questionable → fect (ife/mc), augsynth, synthdid
│   └── Not staggered → Classical TWFE or did (single group)
│
├── Need within-unit placebo group? → DDD (triplediff if staggered)
├── Treatment continuous / multi-valued? → contdid or did_multiplegt_stat
├── Treatment switches on and off? → DIDmultiplegtDYN or fect
│
├── Control group:
│   ├── Never-treated available → Use as default
│   └── All eventually treated → "not yet treated"
│
└── Aggregation:
    ├── Event study → aggte(type = "dynamic")
    ├── Overall ATT → aggte(type = "group") [recommended]
    └── Calendar time → aggte(type = "calendar")

Step 2: Validate (see diagnostics.md)
├── Sensitivity: HonestDiD, fect equivalence test, Bacon decomposition
├── Inference: few clusters → WCB; multiple outcomes → Romano-Wolf
├── Falsification: placebo outcomes, placebo timing, randomization inference
└── Pre-submission checklist
```

## Critical Pitfalls

**1. Naive TWFE with staggered timing**: Can produce wrong sign. Always use modern estimators or verify with Bacon decomposition first.

**2. Confusing "no pre-trends" with "parallel trends holds"**: Pre-trend tests have low power (Roth 2022). Use HonestDiD to assess what the pre-trends actually tell you.

**3. Bad controls in TWFE with covariates**: Time-varying covariates in TWFE drop out due to unit FE. Must use baseline covariate values or `X_baseline x Post` interactions.

**4. Weighted != unweighted**: These target different parameters. Population-weighted ATT = "effect on average person"; unweighted ATT = "effect on average unit."

**5. Simple aggregation overweights early-treated**: Use `aggte(type="group")` for overall ATT.

**6. Event study composition changes**: At longer horizons, only early-treated groups contribute. Use `balance_e` or report group-specific event studies.

**7. synthdid requires balanced panel**: Will fail or produce wrong results with gaps. Use `fect(mc)` or `cdid` for unbalanced data.

**8. Few-clusters inference ignored**: With G < 50 clusters, standard CR1 over-rejects at 10-25%. Must use wild cluster bootstrap (`fwildclusterboot`).

**9. No multiple testing correction**: Testing 10 outcomes and reporting the 2 that are significant is p-hacking. Use Romano-Wolf or Anderson ICW index.

**10. No placebo/falsification tests**: A DID paper without placebo outcomes or randomization inference will be asked for them in R1. Plan these ex ante.

**11. Binarizing continuous treatment**: Discarding dose variation throws away power. Use `contdid` or `did_multiplegt_stat`.

**12. TWFE DDD under staggering**: Contaminated by double-differences (Strezhnev 2023). Use `triplediff` instead.

## Reference Files

| File | Content | Read when |
|------|---------|-----------|
| [pre-analysis.md](references/pre-analysis.md) | Panel structure, treatment construction, outcome EDA, transformation, raw trends, covariates, missingness, spot checks | Starting a DID analysis, exploring data |
| [estimators.md](references/estimators.md) | Estimator comparison, TWFE failure, synthetic methods, fect, cdid, DDD, continuous treatment, non-absorbing treatment | Choosing a method |
| [implementation.md](references/implementation.md) | R code: did, fixest, synthdid, augsynth, fect, cdid, HonestDiD, Bacon, plots, tables | Writing or debugging R code |
| [diagnostics.md](references/diagnostics.md) | Assumptions, PT testing, HonestDiD, covariate balance, anticipation, SUTVA, power, few-clusters inference, multiple testing, placebo tests, checklist | Validating results or preparing for submission |
| [writing.md](references/writing.md) | Identification strategy structure, discussing PT, event study plot standards, reviewer response templates, reporting checklist | Writing up results |
