# Writing Up DID Results for Top Journals

## 1. Identification Strategy Section Structure

### Four-Part Organization

**Part A: Institutional Background** (most important for credibility)
> "In [year], [jurisdiction] implemented [policy], which affected [treatment group] but not [control group]. The timing was determined by [exogenous factor], rather than [endogenous factor]. We exploit this variation using a difference-in-differences design."

**Part B: Treatment Description**
- Binary, multi-valued, or continuous
- Staggered or simultaneous
- Anticipation concerns

**Part C: Identifying Assumptions**
State PT formally and intuitively:
> "The identifying assumption requires that, absent treatment, treated units would have evolved along the same trajectory as controls. This would be violated if [specific threat 1] or [specific threat 2]."

**Part D: Estimation Approach**
> "Recent work shows that TWFE may be biased under heterogeneous effects with staggered adoption (Goodman-Bacon 2021). We therefore use [chosen estimator], which estimates group-time ATTs under [stated assumptions]. Results are robust to alternative estimators (Appendix X)."

### Journal-Specific Norms

| Feature | Econ (AER/QJE) | PolSci (APSR/AJPS/JOP) |
|---------|----------------|------------------------|
| Formal notation | Extensive (3-5 equations) | Moderate (1-2 equations) |
| Institutional narrative | Required but concise | Extensive, often primary |
| HonestDiD | Becoming standard | Early adopter advantage |
| Wild bootstrap | Expected with few clusters | Less common but valued |
| Appendix | Can exceed 50 pages | Moderate (20-40 pages) |

---

## 2. Discussing Parallel Trends

### Three-Layer Argument

1. **Institutional narrative** (primary): Why treatment timing is unrelated to outcome trends
2. **Visual + statistical evidence** (supporting): Event study, pre-trend tests
3. **Robustness to violations** (decisive): HonestDiD, equivalence tests

### Citing Roth (2022) -- Now Expected

> "The absence of statistically significant pre-trends, while reassuring, does not constitute proof of the parallel trends assumption (Roth 2022). Pre-trend tests have limited power against violations that are economically meaningful. We therefore supplement visual evidence with a formal sensitivity analysis."

This sentence (or a variant) now appears in virtually all well-crafted DID papers. Omitting it signals unawareness of the post-2020 literature.

### Presenting HonestDiD

**Relative magnitudes** (preferred):
> "Following Rambachan and Roth (2023), we assess sensitivity to parallel trends violations. Our results remain significant for Mbar <= [value], implying robustness unless post-treatment trend deviations exceed [value] times the largest pre-treatment deviation."

**Smoothness restriction**:
> "Under a smoothness restriction allowing the trend slope to change by at most M per period, our estimate remains significant for M up to [value]."

### Useful Hedging Language

- "consistent with, but not proof of, the parallel trends assumption"
- "we find no evidence of differential pre-trends, though we acknowledge limited power"
- "the institutional context provides the primary basis for identification"
- "we cannot rule out all confounders, but [alternatives] are unlikely because [reason]"

---

## 3. Event Study Plot Best Practices

### Design Elements

| Element | Standard |
|---------|----------|
| Reference period | $t = -1$, shown explicitly as zero |
| CIs | Vertical bars (pointwise) or shaded bands (simultaneous) |
| Zero line | Horizontal, thin gray |
| Treatment onset | Vertical dashed line at $t = 0$ |
| X-axis | "Periods Relative to Treatment" or "Event Time" |
| Y-axis | Describe outcome and units ("Effect on Log Earnings") |
| Endpoint binning | Bin $k \leq -6$ and $k \geq 6$ if tails are noisy |

### Pointwise vs. Simultaneous CIs

**Current best practice**: Report pointwise CIs as primary. Mention simultaneous bands (sup-t) in text or as supplementary figure.

Template figure note:
> "Notes: Estimated coefficients from equation [X] with 95% pointwise confidence intervals. Standard errors clustered at the [unit] level. Reference period is $t = -1$."

If reporting both:
> "Shaded bands: 95% pointwise CIs. Dashed lines: 95% simultaneous sup-t bands."

### Balanced Composition

> "To ensure composition changes across cohorts do not drive the pattern, we restrict the event window to $[k_{min}, k_{max}]$ where all cohorts are observed. Results are similar with a wider window (Appendix Figure X)."

### Common Mistakes

1. Not showing the zero at $t = -1$
2. Connecting pointwise CIs with bands (implies joint coverage)
3. Omitting N contributing to each estimate for staggered designs
4. Not binning noisy endpoints
5. Overlaying 4+ specifications on one plot

---

## 4. Main Text vs. Appendix

### Main Text (4-6 tables, 3-5 figures)

| Item | Typical Position |
|------|-----------------|
| Summary statistics | Table 1 |
| Main event study | Figure 1 |
| Main DID estimates | Table 2 (3-5 columns) |
| Key heterogeneity | Table 3 or Figure 2 |
| Mechanism evidence | Table 4 or Figure 3 |
| Key robustness | Table 4/5 |

### Appendix

| Item | Rationale |
|------|-----------|
| Bacon decomposition | Transparency, not central |
| Alternative estimators | CS vs SA vs dCDH comparison |
| Alternative SEs | Wild bootstrap, different clustering |
| Placebo outcomes | Falsification |
| Placebo treatment dates | Falsification |
| Full covariate results | Main text shows key variables only |
| Alternative transformations | Log vs level vs Poisson |
| Balance tables | Pre-treatment covariate balance |
| Extended event study | Wider window |
| HonestDiD plots | Main text or appendix depending on centrality |
| Attrition/composition | Entry/exit of units |

**Rule**: If a result **changes your conclusion** → main text. If it **defends against a specific objection** → appendix.

---

## 5. Common Reviewer Demands and Standard Responses

### "Show pre-trends are flat"

> "We address this in three ways. First, Figure X shows no significant pre-treatment coefficients. Second, a joint F-test fails to reject joint insignificance ($F = [val]$, $p = [val]$). Third, following Roth (2022), we conduct HonestDiD sensitivity analysis (Appendix Figure X) showing significance at Mbar up to [value]."

### "Why not use [alternative estimator]?"

> "Appendix Table X presents estimates from [TWFE, CS, SA, BJS, dCDH]. Point estimates range from [min] to [max]. Consistency across estimators is expected given [feature of design]."

### "What about anticipation?"

> "Anticipation is unlikely because [institutional reason]. Nonetheless, our event study shows no effects at $t = -2, -3$. We additionally allow for [k] periods of anticipation (Appendix Table X); results are unchanged."

### "Cluster at higher level"

> "Our baseline clusters at the [unit] level (treatment assignment level). Appendix Table X shows robustness to clustering at [higher level]. Because G = [number] is modest, we also report wild cluster bootstrap p-values (Cameron et al. 2008) with 99,999 replications."

### "Treatment timing may be endogenous"

> "We address this on several fronts. First, [institutional argument]. Second, pre-treatment levels and trends of [covariates] do not predict treatment timing in a hazard model (Appendix Table X). Third, results are similar using [subset with plausibly exogenous timing]."

### "Could [confounder] explain results?"

**Placebo outcome response:**
> "If [confounder] drove our results, we would expect effects on [placebo outcome]. Appendix Table X shows small, insignificant estimates, inconsistent with [confounder] as an explanation."

**DDD response:**
> "To isolate the treatment effect from [confounder], we employ a triple-differences design exploiting variation in [third dimension]. Table X reports these estimates; conclusions are unchanged."

---

## 6. Reporting Checklist

### Required Numerical Results

| Item | Where | Format |
|------|-------|--------|
| Point estimate | Table | 3 decimal places + stars |
| Standard error | Table | Parentheses below coefficient |
| Confidence interval | Text (main result) | "95% CI: [lower, upper]" |
| N (observations) | Table | With comma separators |
| N treated units | Text or notes | |
| N control units | Text or notes | |
| N clusters | Table notes | |
| T (periods) | Text | "spans [T] [periods] from [start] to [end]" |
| Treatment timing distribution | Text or table | For staggered designs |
| $R^2$ | Table | 3 decimal places |

### Bootstrap Reporting

> "p-values computed via wild cluster bootstrap with 99,999 Rademacher draws (Cameron et al. 2008), implemented using fwildclusterboot."

### Effect Size Contextualization

Always contextualize: relative to mean, SD, or policy-relevant threshold.
> "The estimated effect of 0.234 corresponds to a [X]% change relative to the control group mean of [value], or approximately [Y] standard deviations."

### Sensitivity Analysis Reporting

**HonestDiD:**
> "Figure X shows robust 95% CIs at each Mbar. Our estimate remains significant for Mbar up to [value], indicating that violations would need to be [value] times larger than any pre-treatment deviation to overturn results."

**Bacon decomposition:**
> "Appendix Figure X shows [share]% of the TWFE estimate is driven by [type of comparison]. [No negative weights / negative weights are small]."

## References

- Roth, Sant'Anna, Bilinski & Poe (2023). "What's Trending in DID?" *JoE*.
- Roth (2022). "Pretest with Caution." *AER: Insights*.
- Rambachan & Roth (2023). "A More Credible Approach to Parallel Trends." *REStud*.
- Cameron, Gelbach & Miller (2008). "Bootstrap-Based Improvements." *RESTAT*.
- de Chaisemartin & D'Haultfoeuille (2023). "TWFE and DID: A Survey." *Econometrics Journal*.
