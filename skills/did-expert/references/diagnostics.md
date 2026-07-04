# DID Diagnostics, Sensitivity, and Assumption Testing

## Identification Assumptions

**1. No Anticipation (NA)**
- Treatment effects are zero in all pre-treatment periods
- Violation: units change behavior before treatment is implemented
- If anticipation is suspected, redefine treatment date earlier

**2. Parallel Trends (PT)**
- Average outcome change would be the same across groups absent treatment
- Untestable (involves counterfactual), but can assess plausibility
- For staggered: must hold for each 2x2 building block

**3. Conditional Parallel Trends (CPT)** — when covariates are used
- PT holds within covariate strata
- Requires strong overlap (common support) assumption

**4. SUTVA / No spillovers**
- Treatment of unit i does not affect outcomes of unit j

## Parallel Trends Assessment

### Pre-trend tests (necessary but not sufficient)

**Critical limitations** (Roth 2022):
1. Pre-trends are NOT the parallel trends assumption (different periods)
2. Failing to reject != parallel trends holds (low power)
3. Conditioning on passing pre-tests can *exacerbate* bias
4. Large pre-trends do not necessarily imply post-treatment bias

### What to do when pre-trends fail
1. **Add covariates**: Switch to conditional PT (CPT)
2. **Sensitivity analysis**: Use HonestDiD to bound violations
3. **Different comparison group**: Try "not yet treated" instead of "never treated"
4. **Switch estimator**: fect (ife/mc) relaxes PT via factor models
5. **Re-examine design**: Consider if DiD is appropriate at all

## Equivalence Test (fect)

Standard pre-trend test: H0: effect = 0 (non-rejection is inconclusive).
Equivalence test: H0: |effect| >= Delta (rejection = positive evidence for PT).

```r
# With proportion of ATT as bound
plot(out, type = "equiv", proportion = 0.3)

# With explicit bounds
plot(out, type = "equiv", equiv.bound = c(-0.5, 0.5))
```

**Interpretation**:
- All CIs within bounds: positive evidence for parallel trends
- Any CI outside bounds: cannot confirm parallel trends

### When fect diagnostics fail

| Failure | Try |
|---------|-----|
| Pre-trends != 0 with `fe` | Switch to `ife` or `mc` (add factors) |
| Pre-trends != 0 with `ife` | Try `mc`; add covariates; check r selection |
| Equivalence test fails | Widen bounds (if defensible); more data; report with caveats |
| Large MSPE | Check outliers; try different method; add covariates |
| Results sensitive to r | Trust CV (`r = 0`); try `mc`; report range |

## Bacon Decomposition

Decomposes TWFE estimate into weighted 2x2 comparisons:
- **Treated vs. never-treated** (good)
- **Early-treated vs. late-treated** (potentially problematic)
- **Late-treated vs. early-treated** (potentially problematic)

**Interpreting results**: If "Earlier vs Later" / "Later vs Earlier" comparisons have large weights OR very different estimates from "Treated vs Untreated," TWFE is unreliable. Solution: modern estimators.

## Covariate Balance

### Normalized differences (Imbens & Rubin 2015)
Rule of thumb: |Norm. Diff.| > 0.25 is problematic.

### What imbalance means for DiD
- **Level imbalance**: PT may fail if covariates predict outcome *trends*
- **Change imbalance in exogenous covariates**: suggests PT violation
- **Change imbalance in endogenous covariates**: may reflect treatment effect (not a problem)
- Key question: is the covariate a *determinant of outcome trends* or a *mechanism*?

### Propensity score overlap (when using IPW/DR)
- Check overlap between treatment groups
- Red flags: PS near 0 or 1, little overlap
- The `did` package trims at 0.995 by default

## HonestDiD Sensitivity

### Two approaches

**1. Relative magnitude** (`type = "relative_magnitude"`)
- Bounds PT violations relative to the largest pre-trend
- Mbar = 1: violations no larger than max pre-trend
- Mbar = 2: violations up to 2x max pre-trend
- Most intuitive interpretation

**2. Smoothness** (`type = "smoothness"`)
- Assumes violations of PT change smoothly over time
- M parameter bounds second differences of the bias
- More flexible but harder to interpret

### Reporting
- Report original CI alongside robust CIs for Mbar = {0.5, 1, 1.5, 2}
- If CI excludes 0 at Mbar = 1, result is robust to PT violations as large as the largest pre-trend
- Present as a table or "breakdown" plot
- See implementation.md for the `honest_did()` wrapper function

## fect Sensitivity (fect_sens)

Sensitivity to parallel trends violations via the sensitivity function:
- `proportion`: equivalence bound as fraction of ATT
- `breakdown`: sigma value where conclusion reverses

## Functional Form

PT is scale-dependent: may hold in levels but not logs (or vice versa). Roth & Sant'Anna (2023b): PT is insensitive to functional form only if the outcome distribution is constant between groups or over time (implausible). Recommendation: test the null of functional form insensitivity.

## Anticipation Effects

### Formal Treatment

No anticipation (NA) is a **separate** identifying assumption from parallel trends. If agents foresee treatment, behavioral changes begin *before* official implementation, contaminating pre-treatment periods and the reference period $t = -1$.

### Detection

1. **Event study inspection**: Pre-treatment coefficients trending *toward* the post-treatment effect suggest anticipation
2. **Institutional knowledge**: Was the policy announced before implementation? Could agents forecast treatment?
3. **Sequential testing**: Test $\beta_{-2} = 0$, then $\beta_{-3} = 0$, moving backward until no significance

### Allowing for Anticipation

```r
# Callaway-Sant'Anna: shift treatment date back by k periods
library(did)
att_ant <- att_gt(
  yname = "Y", tname = "year", idname = "id",
  gname = "first_treat", data = df,
  anticipation = 2  # allow 2 periods of anticipation
)
# This redefines g* = g - 2 and uses t = g* - 1 as reference
aggte(att_ant, type = "dynamic")

# fect: placebo test detects anticipation
library(fect)
out <- fect(Y ~ D, data = df, index = c("id", "time"), method = "fe",
            se = TRUE, nboots = 200,
            placeboTest = TRUE, placebo.period = c(-3, -1))
plot(out, stats = c("placebo.p"))
```

### Decision Rule

```
Pre-treatment coefficients significant near t = -1?
├── YES, institutional story supports anticipation
│   → Allow anticipation (did: anticipation = k; or redefine treatment date)
│   → Report results with and without anticipation allowance
├── YES, but no institutional basis
│   → Likely PT violation, not anticipation
│   → Use HonestDiD or fect to address
└── NO
    → Proceed with standard NA assumption
```

**Critical**: Anticipation and PT violations look identical in data. The distinction must come from **institutional knowledge**, not statistics.

---

## SUTVA and Spillover Detection

### What Breaks

SUTVA (Stable Unit Treatment Value Assumption) requires that unit $i$'s outcome depends only on its own treatment, not on others' treatment. Violations:
- **Direct spillovers**: Treated firms affect competitors' outcomes
- **General equilibrium**: Policy changes prices/wages for everyone
- **Network effects**: Information/behavior diffuses across units
- **Composition effects**: Treatment of some units changes the control group's environment

### Detection Strategies

**1. Ring analysis** (geographic spillovers):
```r
library(fixest)

# Create distance-based rings around treated units
df$ring <- case_when(
  df$treated == 1             ~ "treated",
  df$dist_to_treated <= 50    ~ "ring_0_50km",
  df$dist_to_treated <= 100   ~ "ring_50_100km",
  TRUE                        ~ "far_control"
)
df$ring <- relevel(factor(df$ring), ref = "far_control")

# Test: do nearby controls show effects?
feols(Y ~ i(ring, post, ref = "far_control") | unit_id + year,
      data = df, cluster = ~unit_id)
```

**2. Donut specification** (exclude potentially contaminated controls):
```r
# Drop controls within X km of treated units
df_donut <- df[df$treated == 1 | df$dist_to_treated > 100, ]
feols(Y ~ treat | unit_id + year, data = df_donut, cluster = ~unit_id)
```

**3. Direct spillover test** (treatment intensity of neighbors):
```r
# Fraction of neighbors treated as spillover measure
feols(Y ~ treat + neighbor_treat_share | unit_id + year,
      data = df, cluster = ~unit_id)
```

### When Spillovers Are Fatal vs. Manageable

| Situation | Assessment | Response |
|-----------|-----------|----------|
| Ring estimates near zero | Manageable | Report donut as robustness |
| Ring estimates significant, same sign as treatment | Problematic | Attenuates treatment estimate; report bounds |
| Ring estimates significant, opposite sign | Very problematic | May contaminate control group; redesign needed |
| General equilibrium concerns | Potentially fatal | Partial equilibrium caveat; seek unaffected controls |

### References

- Butts (2024). "DID with Spatial Spillovers." arXiv:2105.03737.
- Clarke (2017). "Estimating Difference-in-Differences in the Presence of Spillovers." MPRA.

---

## Power Analysis for DID

### Why It Matters

DID power depends on: (1) number of clusters, (2) outcome variance, (3) within-cluster correlation (ICC), (4) treatment effect size, (5) number of time periods, and (6) serial correlation. Standard power formulas for independent observations do not apply.

### Simulation-Based Approach (Recommended)

```r
library(fixest)

simulate_did_power <- function(
  n_units = 100,     # total units
  n_treated = 50,    # treated units
  n_periods = 10,    # total periods
  treat_period = 6,  # treatment starts
  effect_size = 0.5, # true ATT (SD units)
  icc = 0.3,         # intra-cluster correlation
  rho_ar = 0.5,      # AR(1) serial correlation
  n_sims = 500,
  alpha = 0.05
) {
  reject <- 0
  for (s in seq_len(n_sims)) {
    # Generate panel data with cluster + AR(1) structure
    df <- expand.grid(id = 1:n_units, time = 1:n_periods)
    df$treated <- as.integer(df$id <= n_treated)
    df$post <- as.integer(df$time >= treat_period)
    df$D <- df$treated * df$post

    # Unit FE + time FE + AR(1) errors
    unit_fe <- rnorm(n_units, sd = sqrt(icc))
    time_fe <- rnorm(n_periods, sd = 0.3)
    df$Y <- unit_fe[df$id] + time_fe[df$time] +
      effect_size * df$D + rnorm(nrow(df), sd = sqrt(1 - icc))

    est <- feols(Y ~ D | id + time, data = df, cluster = ~id)
    reject <- reject + (pvalue(est)["D"] < alpha)
  }
  reject / n_sims
}

# MDE curve: power across effect sizes
effects <- seq(0.1, 1.0, by = 0.1)
powers <- sapply(effects, function(e) {
  simulate_did_power(effect_size = e, n_sims = 500)
})
plot(effects, powers, type = "b", xlab = "Effect Size (SD)",
     ylab = "Power", main = "DID Power Curve")
abline(h = 0.8, lty = 2, col = "red")
```

### `DIDdesign` Package

```r
# install.packages("DIDdesign")
library(DIDdesign)

# Power calculation for panel DID
did_power <- panel_estimate(
  df,
  yname = "Y", idname = "id", tname = "time",
  treatment_group = treated_ids,
  pre_window = c(-5, -1), post_window = c(0, 4)
)
```

### Key Considerations

- **Effective clusters**: Power depends on *treated* cluster count, not total clusters
- **Pre-treatment periods**: More pre-periods increase power (help estimate unit trends)
- **Serial correlation**: Ignoring it dramatically overstates power (Bertrand et al. 2004)
- **ICC**: Higher ICC (more between-unit variance) reduces power for fixed N
- **Report MDE**: "Given our sample, we have 80% power to detect an effect of [X] SD, corresponding to [Y]% of the control mean"

---

## Unbalanced Panel Diagnostics

### Missingness assessment
- Document the pattern of missingness (by treatment group and time)
- Report sample sizes by treatment cohort and period
- Test whether attrition rates differ by treatment status

### Sensitivity to sample composition
- Compare balanced subsample vs full unbalanced results
- Use `fect` with `balance.period` windows of varying width
- Compare `did` modes: `allow_unbalanced_panel=TRUE` vs `panel=FALSE`
- Compare `cdid` methods: `"2-step"` vs `"Identity"`
- If results diverge substantially: missingness matters for identification

### Common mistakes
1. **Silently dropping to balanced panel** without reporting sample loss
2. **Using synthdid with gaps** (requires strictly balanced panel)
3. **Confusing "not yet in sample" with "not yet treated"**: can bias control group
4. **Assuming missingness is exogenous without testing**: compare attrition rates

## Few-Clusters Inference

Standard cluster-robust SEs (CR1) require G → ∞. With few clusters, CR1 **systematically over-rejects**: a nominal 5% test can reject at 10-25% rates.

| G (Clusters) | Assessment | Primary Method |
|---|---|---|
| < 10 | Very problematic | Permutation inference; Webb weights in WCB |
| 10-30 | Problematic | Wild cluster bootstrap (WCR, Rademacher) |
| 30-50 | Borderline | WCB as robustness; CR1 may be roughly adequate |
| 50+ | Generally adequate | Standard CR1 |

**Critical nuance**: These thresholds depend on the *effective* number of clusters. When only a few clusters are treated (e.g., 5 states out of 50), inference on the treatment coefficient effectively depends on only the treated clusters.

### Wild Cluster Bootstrap: `fwildclusterboot`

```r
library(fixest)
library(fwildclusterboot)

mod <- feols(Y ~ treat | unit_id + year, data = df, cluster = ~state)

boot_res <- boottest(
  mod,
  param = "treat",
  clustid = "state",
  B = 99999,
  type = "rademacher",   # use "webb" if G < 12
  impose_null = TRUE,    # WCR (recommended)
  fe = "unit_id",        # project out FE for speed
  conf_int = TRUE,
  nthreads = 4
)
summary(boot_res)
```

| Parameter | Recommendation |
|-----------|---------------|
| `type` | `"rademacher"` (default); `"webb"` if G < 12 |
| `impose_null` | `TRUE` (WCR) — better size control |
| `B` | >= 9,999 for publication; 99,999 if feasible |

### Interaction with `did` / `fect`

The `did` package uses a multiplier bootstrap with the same few-cluster problem as CR1. **Workaround**: estimate via `fixest` (Sun-Abraham or stacked DID) and apply `boottest()`. `fect` similarly requires the fixest workaround for WCB inference.

### Reporting Template

> "Our baseline specification clusters standard errors at the [unit] level. Because the number of clusters is modest (G = [number]), we additionally report p-values from a wild cluster bootstrap with Rademacher weights and 99,999 replications (Cameron et al. 2008). The bootstrap p-value for our main estimate is [value]."

---

## Multiple Testing Corrections

### When Correction Matters

| Situation | Correction Expected? | Method |
|-----------|---------------------|--------|
| Multiple primary outcomes, same family | **Yes** | Romano-Wolf or Anderson Index |
| Multiple secondary outcomes | **Yes**, or label exploratory | Romano-Wolf or Holm |
| Subgroup heterogeneity (pre-specified) | **Yes** | Romano-Wolf or Holm |
| Subgroup heterogeneity (exploratory) | **Optional**, label clearly | BH-FDR if applied |
| Robustness checks / alt specifications | **No** | Specification curve instead |
| Event-study coefficients | **Implicit** | Simultaneous (sup-t) bands |

### Romano-Wolf via `wildrwolf`

```r
library(wildrwolf)
library(fixest)

fit <- feols(
  c(Y1, Y2, Y3, Y4) ~ D | unit_id + year,
  data = df, cluster = ~cluster_id
)

set.seed(42)
rw <- rwolf(models = fit, param = "D", B = 9999, p_val_type = "two-tailed")
print(rw)
```

### Anderson (2008) Summary Index (ICW)

Construct a single weighted index of standardized outcomes, eliminating the multiple testing problem entirely.

```r
anderson_icw_index <- function(df, outcome_vars, standardize_group = NULL) {
  Y <- as.matrix(df[, outcome_vars, drop = FALSE])
  n <- nrow(Y); k <- ncol(Y)
  if (is.null(standardize_group)) standardize_group <- rep(TRUE, n)
  Y_std <- Y
  for (j in seq_len(k)) {
    ref_mean <- mean(Y[standardize_group, j], na.rm = TRUE)
    ref_sd   <- sd(Y[standardize_group, j], na.rm = TRUE)
    Y_std[, j] <- (Y[, j] - ref_mean) / ref_sd
  }
  Sx <- cov(Y_std[complete.cases(Y_std), ])
  Sx_inv <- solve(Sx)
  ones <- matrix(1, nrow = k, ncol = 1)
  weights <- as.numeric(solve(t(ones) %*% Sx_inv %*% ones) %*% t(ones) %*% Sx_inv)
  names(weights) <- outcome_vars
  list(index = as.numeric(Y_std %*% weights), weights = weights)
}

result <- anderson_icw_index(df, c("Y1", "Y2", "Y3", "Y4"),
                              standardize_group = df$treated == 0)
df$support_index <- result$index
feols(support_index ~ D | unit_id + year, data = df, cluster = ~cluster_id)
```

### BH-FDR and Holm

```r
pvals <- sapply(list(mod1, mod2, mod3, mod4), function(m) pvalue(m)["D"])
p.adjust(pvals, method = "holm")   # controls FWER
p.adjust(pvals, method = "BH")     # controls FDR
```

---

## Placebo and Falsification Tests

### Placebo Outcomes

Run DID on an outcome that treatment **should not** affect. A placebo outcome must be: (1) unaffected by treatment, and (2) responsive to the same confounders that threaten the main outcome. An outcome unaffected by both treatment *and* confounders has no power to detect problems (Eggers, Tunon & Dafoe 2024).

```r
library(fixest)

# Multi-LHS: main outcome + placebos in one call
multi <- feols(
  c(Y_main, Y_placebo1, Y_placebo2) ~ treat | unit_id + year,
  data = df, cluster = ~unit_id
)
etable(multi, headers = c("Main DV", "Placebo 1", "Placebo 2"), keep = "treat")
```

### Placebo Treatment Timing

Assign a **fake treatment date** in the pre-treatment period, estimate DID on pre-treatment data only:

```r
pre_data <- df[df$year < T0, ]
candidate_dates <- sort(unique(pre_data$year))[2:(length(unique(pre_data$year)) - 1)]

results <- lapply(candidate_dates, function(ft) {
  pre_data$fake_post <- as.integer(pre_data$year >= ft)
  pre_data$fake_treat <- pre_data$treated * pre_data$fake_post
  est <- feols(Y ~ fake_treat | unit_id + year, data = pre_data, cluster = ~unit_id)
  data.frame(fake_date = ft, estimate = coef(est)["fake_treat"],
             se = se(est)["fake_treat"], pvalue = pvalue(est)["fake_treat"])
})
placebo_df <- do.call(rbind, results)
```

### Permutation / Randomization Inference

Essential when few units/clusters are treated. **Critical**: Permute at the **cluster level**, not individual level.

```r
library(ritest)
library(fixest)

est <- feols(Y ~ treat_post | unit_id + year, vcov = ~state, data = df)
ri_result <- ritest(est, resampvar = "treat_post", cluster = "state",
                    reps = 5000L, seed = 12345L)
print(ri_result)
```

### `fect` Built-in Placebo and Carry-Over Tests

```r
library(fect)

# Placebo test
out <- fect(Y ~ D, data = df, index = c("id", "time"), method = "fe",
            se = TRUE, nboots = 200,
            placeboTest = TRUE, placebo.period = c(-3, -1))
plot(out, stats = c("placebo.p", "equiv.p"))

# Carry-over test (for non-absorbing treatment)
out_carry <- fect(Y ~ D, data = df, index = c("id", "time"), method = "fe",
                  se = TRUE, nboots = 200,
                  carryoverTest = TRUE, carryover.period = c(1, 3))
plot(out_carry, stats = "carryover.p")
```

### Presenting Falsification Results

| Test | Main Text | Appendix |
|------|-----------|----------|
| Placebo outcomes (1-2 key ones) | Table or event study figure | Full table with all placebos |
| Placebo treatment timing | Brief mention | Figure with multiple fake dates |
| Randomization inference | Fisher p alongside parametric p | Distribution plot |

---

## Pre-Submission Checklist

### Design
- [ ] Treatment timing clearly defined
- [ ] No anticipation justified (institutional argument, not just stats)
- [ ] Anticipation allowance tested if policy was pre-announced
- [ ] Control group choice justified (never-treated vs. not-yet-treated)
- [ ] Staggered timing handled with modern estimator (not naive TWFE)
- [ ] SUTVA discussed; spillover risk assessed

### Parallel Trends
- [ ] Event study plot with pre-treatment estimates
- [ ] Both pointwise and simultaneous confidence bands
- [ ] Wald pre-test reported
- [ ] Roth (2022) limitation acknowledged
- [ ] Covariate balance table (levels AND changes)
- [ ] Institutional argument for why PT is plausible

### Estimation
- [ ] Modern estimator for staggered designs
- [ ] Weighting choice discussed (different target parameters)
- [ ] Standard errors clustered at treatment assignment level
- [ ] Few-clusters check: if G < 50, wild cluster bootstrap reported
- [ ] Multiple testing adjustment for event study (simultaneous bands)
- [ ] Multiple testing correction for multiple outcomes/subgroups

### Robustness
- [ ] HonestDiD or fect equivalence test
- [ ] Results with and without covariates compared
- [ ] Alternative control groups tested
- [ ] Functional form sensitivity discussed
- [ ] Bacon decomposition (if TWFE reported for comparison)

### Falsification
- [ ] Placebo outcomes (2-4, well-chosen with clear rationale)
- [ ] Placebo treatment timing (at least 2 fake dates)
- [ ] Randomization inference if few treated clusters (Fisher p-value)

### Unbalanced panels (if applicable)
- [ ] Missingness pattern documented
- [ ] Stated whether missingness assumed random or endogenous
- [ ] Balanced vs unbalanced results compared
- [ ] Estimand stated ("unit-average ATT" vs "observation-average ATT")
- [ ] min.T0 sensitivity (if using fect)

### Power (if pre-analysis or null result)
- [ ] MDE reported relative to control mean and SD
- [ ] Simulation-based power accounting for clustering and serial correlation
- [ ] Effective cluster count (treated clusters) noted

### Reporting
- [ ] Target parameter clearly stated
- [ ] Aggregation method stated
- [ ] N treated/control, N clusters, and T reported
- [ ] Bootstrap iterations >= 10,000 for final results
- [ ] Effect size contextualized (% of mean, SD units)
- [ ] Identification strategy follows 4-part structure (see writing.md)
