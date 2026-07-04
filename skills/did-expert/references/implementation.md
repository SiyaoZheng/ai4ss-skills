# R Implementation Patterns

## Package Ecosystem

```r
# Core estimators
library(did)          # Callaway & Sant'Anna (2021)
library(fixest)       # Fast TWFE, Sun & Abraham via sunab()
library(synthdid)     # Synthetic DID (Arkhangelsky et al. 2021)
library(augsynth)     # Augmented SC + multisynth for staggered
library(fect)         # Factor-model counterfactuals (FEct/IFEct/MC)
library(cdid)         # Chained DID for unbalanced panels

# Sensitivity & diagnostics
library(HonestDiD)    # Rambachan & Roth (2023) sensitivity
library(bacondecomp)  # Goodman-Bacon (2021) decomposition
library(DRDID)        # Doubly-robust 2x2 DiD (used internally by did)

# Visualization & tables
library(ggplot2)
library(modelsummary)
```

## Data Preparation

```r
# did package requires LONG format with:
# - id (numeric), time (numeric), group (numeric: first treat period, 0=never), outcome
panel_data <- panel_data %>%
  mutate(
    unit_id = as.numeric(unit_id),
    treat_year = if_else(is.na(treat_year) | treat_year > max_year, 0L, treat_year)
  )

# Check panel balance
panel_data %>% count(unit_id) %>% count(n, name = "n_units")

# Check treatment timing distribution
panel_data %>% distinct(unit_id, treat_year) %>% count(treat_year)

# Verify no units treated in first period
stopifnot(all(panel_data$treat_year != min(panel_data$year) | panel_data$treat_year == 0))
```

## Classical DID (fixest)

```r
# 2x2: Interaction (most transparent)
mod1 <- feols(Y ~ Treat * Post, data = short_data, cluster = ~unit_id)

# 2x2: TWFE (numerically identical)
mod2 <- feols(Y ~ Treat:Post | unit_id + year, data = short_data, cluster = ~unit_id)

# 2xT: Event study for single treatment group
mod_es <- feols(Y ~ i(rel_time, ref = -1) | unit_id + year,
                data = panel_data %>% filter(treat_year == g | treat_year == 0),
                cluster = ~unit_id)
iplot(mod_es, main = "Event Study")

# With population weights
mod_w <- feols(Y ~ Treat * Post, data = short_data,
               weights = ~pop_weight, cluster = ~unit_id)

# Stacked DID: manually avoid forbidden comparisons under staggered adoption
# (CS/SA do this internally; use when you want transparent TWFE on clean data)
library(data.table)
dt <- as.data.table(df)
cohorts <- sort(unique(dt[first_treat > 0, first_treat]))
stack_list <- lapply(seq_along(cohorts), function(k) {
  g <- cohorts[k]
  sub <- dt[(first_treat == g | first_treat == 0) & year >= g - 5 & year <= g + 5]
  sub[, `:=`(stack_id = k, rel_time = year - g,
             stack_unit = paste0(k, "_", id), stack_year = paste0(k, "_", year),
             treated = as.integer(first_treat == g & year >= g))]
  sub
})
stacked_dt <- rbindlist(stack_list)
est_stack <- feols(Y ~ treated | stack_unit + stack_year, data = stacked_dt, vcov = ~id)
```

## Callaway & Sant'Anna (did)

### ATT(g,t) Estimation

```r
set.seed(123)  # for reproducible bootstrap
out <- att_gt(
  yname      = "Y",
  tname      = "year",
  idname     = "unit_id",
  gname      = "treat_year",      # 0 for never-treated
  xformla    = ~1,                 # ~X1 + X2 for conditional PT
  data       = panel_data,
  panel      = TRUE,
  control_group = "nevertreated",  # or "notyettreated"
  est_method = "dr",               # "dr" (default), "reg", "ipw"
  bstrap     = TRUE,
  cband      = TRUE,
  biters     = 10000,
  base_period = "universal",       # required for HonestDiD
  weightsname = NULL               # column name for sampling weights
)
summary(out)
```

### Aggregation

```r
# Event study (dynamics)
agg_es <- aggte(out, type = "dynamic", min_e = -5, max_e = 5, biters = 10000)

# Overall ATT by group (recommended)
agg_group <- aggte(out, type = "group", biters = 10000)

# Simple average (overweights early-treated — use cautiously)
agg_simple <- aggte(out, type = "simple", biters = 10000)

# Calendar time
agg_cal <- aggte(out, type = "calendar", biters = 10000)

# Balanced event study (same composition across event times)
agg_balanced <- aggte(out, type = "dynamic", balance_e = 3, biters = 10000)
```

### Covariates

```r
# Doubly robust (recommended)
out_dr <- att_gt(..., xformla = ~X1 + X2, est_method = "dr")

# Regression adjustment
out_reg <- att_gt(..., xformla = ~X1 + X2, est_method = "reg")

# IPW
out_ipw <- att_gt(..., xformla = ~X1 + X2, est_method = "ipw")

# Note: did sets time-varying covariates to base-period value
```

## Sun & Abraham (fixest::sunab)

```r
mod_sa <- feols(Y ~ sunab(treat_year, year) | unit_id + year,
                data = panel_data, cluster = ~unit_id)
summary(mod_sa, agg = "ATT")       # overall ATT
summary(mod_sa, agg = "cohort")    # by cohort
iplot(mod_sa)                       # event study
```

## Synthetic DID (synthdid)

```r
# Data must be N×T matrix: rows 1:N0 = control, (N0+1):N = treated
# Columns 1:T0 = pre-treatment, (T0+1):T = post-treatment
setup <- panel.matrices(california_prop99)

# Three estimators
tau_sdid <- synthdid_estimate(setup$Y, setup$N0, setup$T0)
tau_sc   <- sc_estimate(setup$Y, setup$N0, setup$T0)
tau_did  <- did_estimate(setup$Y, setup$N0, setup$T0)

# Inference
se_sdid <- sqrt(vcov(tau_sdid, method = "placebo"))   # default
se_boot <- sqrt(vcov(tau_sdid, method = "bootstrap"))
se_jack <- sqrt(vcov(tau_sdid, method = "jackknife"))

# Visualization
plot(tau_sdid)
plot(tau_sdid, tau_sc, tau_did)  # comparison

# Inspect weights
omega  <- attr(tau_sdid, 'weights')$omega   # unit weights
lambda <- attr(tau_sdid, 'weights')$lambda  # time weights
sum(omega > 1e-6)   # non-zero unit weights
sum(lambda > 1e-6)  # non-zero time weights

# With covariates (X must be N×T×C array)
tau_cov <- synthdid_estimate(setup$Y, setup$N0, setup$T0, X = X_array)
```

### Converting Long Panel to Matrix

```r
library(tidyr)
Y_wide <- panel_data %>%
  select(unit_id, year, Y) %>%
  pivot_wider(names_from = year, values_from = Y) %>%
  arrange(treat_year == 0) %>%  # controls first
  select(-unit_id) %>%
  as.matrix()

N0 <- sum(panel_data %>% distinct(unit_id, treat_year) %>% pull(treat_year) == 0)
T0 <- sum(sort(unique(panel_data$year)) < min_treat_year)
tau <- synthdid_estimate(Y_wide, N0, T0)
```

## Augmented Synthetic Control (augsynth)

```r
# Single treated unit
asyn <- augsynth(
  Y ~ treat, unit = unit_id, time = year,
  data = panel_data,
  progfunc = "Ridge",   # "Ridge", "GSYN", "MCP", "EN", "none"
  scm = TRUE            # TRUE = augmented SC; FALSE = pure ridge
)
summary(asyn)
plot(asyn)

# Staggered adoption (multisynth)
msyn <- multisynth(
  Y ~ treat, unit = unit_id, time = year,
  data = panel_data,
  n_leads = 5, n_lags = 3
)
summary(msyn)
plot(msyn)                         # event-study by cohort
plot(msyn, levels = "Average")     # overall average
```

## Counterfactual Estimators (fect)

### Basic Usage

```r
# Formula: Y ~ D + covariates | unit | time
out <- fect(Y ~ D + X1 + X2 | unit_id | year,
            data = panel_data,
            method = "ife",       # "fe", "ife", "mc", "polynomial", "gsynth"
            r = 0,                # 0 = auto-select via CV
            CV = TRUE, k = 10,
            se = TRUE,
            nboots = 200,         # 500+ for publication
            inference = "nonparametric",
            parallel = TRUE, cores = 4,
            seed = 123)

# Alternative variable interface
out <- fect(Y = "outcome", D = "treatment",
            X = c("covar1", "covar2"),
            index = c("unit_id", "year"),
            data = panel_data, method = "ife")
```

### With Full Diagnostics

```r
out <- fect(Y ~ D | unit_id | year,
            data = panel_data,
            method = "ife", r = 0, CV = TRUE,
            placeboTest = TRUE,
            placebo.period = c(-4, -1),
            carryoverTest = TRUE,
            carryover.period = c(1, 5),
            se = TRUE, nboots = 500, seed = 123)
```

### Extracting Results

```r
out$att.avg             # Overall ATT point estimate
out$est.avg             # Data frame: ATT, SE, CI, p-value
out$est.att             # Period-specific ATT
out$Y.ct                # Estimated Y(0) matrix (unit × time)
out$eff                 # Treatment effects matrix (unit × time)
out$r.cv                # CV-selected number of factors
out$factor              # Estimated time factors (T × r)
out$lambda              # Estimated unit loadings (N × r)
out$beta                # Covariate coefficients
```

### Plot Types

```r
plot(out, type = "gap")       # ATT over time (main result)
plot(out, type = "equiv",     # Equivalence test
     proportion = 0.3)
plot(out, type = "status")    # Treatment status heatmap
plot(out, type = "ct",        # Counterfactual vs actual
     id = c(1, 5, 10))
plot(out, type = "exit")      # Carryover/exit effects
plot(out, type = "factors")   # Factor loadings (ife/mc only)
plot(out, type = "box")       # ATT distribution across units
```

### Sensitivity

```r
sens <- fect_sens(out, proportion = 0.3, ngrid = 100)
plot(sens)
sens$breakdown  # Sigma where conclusion reverses
```

### Common Issues

```r
# Convergence: tighten tolerance, more iterations
out <- fect(..., tol = 1e-6, max.iteration = 2000)

# Large SEs: try jackknife for small N
out <- fect(..., inference = "jackknife")

# CV selects r=0: no factors needed; consider method="fe"
```

## Chained DID (cdid)

```r
library(cdid)
library(did)

# Drop-in replacement for att_gt()
result <- att_gt_cdid(
  yname = "Y",
  tname = "year",
  idname = "unit_id",
  gname = "first_treat",    # 0 for never-treated
  est_method = "2-step",    # or "Identity" for severe imbalance
  data = panel_data
)

# Standard did aggregation works directly
agg_es <- aggte(result, type = "dynamic")
agg_group <- aggte(result, type = "group")
ggdid(agg_es)

# With covariates
result <- att_gt_cdid(..., xformla = ~ X1 + X2, est_method = "Identity")
```

## Unbalanced Panel Settings

### did package: Three modes

```r
# Mode 1: Balanced (default — drops incomplete units)
out <- att_gt(..., panel = TRUE, allow_unbalanced_panel = FALSE)

# Mode 2: Unbalanced (retains incomplete units)
out <- att_gt(..., panel = TRUE, allow_unbalanced_panel = TRUE)

# Mode 3: Repeated cross-sections (no unit tracking)
out <- att_gt(..., panel = FALSE)

# Always compare all three as robustness check
# They produce numerically different results — different estimands
```

### fect with incomplete data

```r
out <- fect(Y ~ D + X1 + X2 | unit_id | year,
            data = panel_data,
            method = "mc",          # matrix completion: best for sparse data
            min.T0 = 5,             # min control-period obs per unit
            na.rm = FALSE,          # FALSE retains obs with missing Y/X
            proportion = 0.3,
            balance.period = NULL,  # e.g., c(-3, 3) for sensitivity
            se = TRUE, nboots = 200, seed = 123)

# Sensitivity: compare across min.T0 thresholds
for (m in c(3, 5, 7, 10)) {
  out <- fect(..., min.T0 = m)
  cat("min.T0 =", m, ": ATT =", out$att.avg, "\n")
}
```

### Other estimators with unbalanced data

```r
# didimputation: first stage uses only untreated obs
library(didimputation)
out <- did_imputation(data = panel_data, yname = "Y", gname = "first_treat",
                      tname = "year", idname = "unit_id",
                      first_stage = ~ 0 | unit_id + year)

# etwfe: pooled saturated regression handles missing cells
library(etwfe)
mod <- etwfe(fml = Y ~ X1, tvar = year, gvar = first_treat,
             data = panel_data, vcov = ~unit_id)
emfx(mod, type = "event")
```

## Bacon Decomposition

```r
library(bacondecomp)
bacon_out <- bacon(Y ~ D, data = panel_data,
                   id_var = "unit_id", time_var = "year")

# Component summary
bacon_out %>%
  group_by(type) %>%
  summarize(avg_estimate = weighted.mean(estimate, weight),
            total_weight = sum(weight))

# Plot
ggplot(bacon_out, aes(x = weight, y = estimate, color = type)) +
  geom_point() +
  geom_hline(yintercept = 0, linetype = "dashed") +
  labs(x = "Weight", y = "2x2 DiD Estimate") +
  theme_minimal()
```

## HonestDiD Sensitivity

### Wrapper for did + HonestDiD

```r
# Requires: base_period = "universal" in att_gt()
honest_did <- function(es, e = 0, type = c("smoothness", "relative_magnitude"),
                       gridPoints = 100, ...) {
  type <- match.arg(type)
  stopifnot(es$type == "dynamic")
  stopifnot(es$DIDparams$base_period == "universal")

  es_inf_func <- es$inf.function$dynamic.inf.func.e
  n <- nrow(es_inf_func)
  V <- t(es_inf_func) %*% es_inf_func / n / n

  referencePeriod <- -1
  hasRef <- any(es$egt == referencePeriod)
  if (hasRef) {
    idx <- which(es$egt == referencePeriod)
    V    <- V[-idx, -idx]
    beta <- es$att.egt[-idx]
  } else {
    beta <- es$att.egt
  }

  nperiods <- nrow(V)
  npre     <- sum(es$egt < referencePeriod)
  npost    <- nperiods - npre
  baseVec1 <- matrix(rep(1/npost, npost))

  orig_ci <- HonestDiD::constructOriginalCS(
    betahat = beta, sigma = V,
    numPrePeriods = npre, numPostPeriods = npost,
    l_vec = baseVec1
  )

  if (type == "relative_magnitude") {
    robust_ci <- HonestDiD::createSensitivityResults_relativeMagnitudes(
      betahat = beta, sigma = V,
      numPrePeriods = npre, numPostPeriods = npost,
      l_vec = baseVec1, gridPoints = gridPoints,
      Mbarvec = c(0, 0.5, 1, 1.5, 2), ...
    )
  } else {
    robust_ci <- HonestDiD::createSensitivityResults(
      betahat = beta, sigma = V,
      numPrePeriods = npre, numPostPeriods = npost,
      l_vec = baseVec1, ...
    )
  }

  list(robust_ci = robust_ci, orig_ci = orig_ci, type = type)
}
```

### Usage

```r
out <- att_gt(..., base_period = "universal")
es <- aggte(out, type = "dynamic", biters = 10000)

# Relative magnitude: how large can PT violations be relative to pre-trends?
sens_rm <- honest_did(es, type = "relative_magnitude")

# Smoothness: violations bounded by M parameter
sens_sm <- honest_did(es, type = "smoothness")

# If CI excludes 0 at Mbar = 1, results are robust
```

## Event Study Plots

### ggplot2 with did output

```r
plot_data <- aggte(out, type = "dynamic", biters = 10000) %>%
  broom::tidy(conf.int = TRUE)

ggplot(plot_data %>% filter(between(event.time, -5, 5)),
       aes(x = event.time, y = estimate)) +
  geom_linerange(aes(ymin = conf.low, ymax = conf.high), color = "darkred") +
  geom_linerange(aes(ymin = point.conf.low, ymax = point.conf.high)) +
  geom_point() +
  geom_vline(xintercept = -1, linetype = "dashed") +
  geom_hline(yintercept = 0, linetype = "dashed") +
  scale_x_continuous(breaks = -5:5) +
  labs(x = "Event Time", y = "Treatment Effect") +
  theme_minimal()
```

### ATT(g,t) by group

```r
out %>%
  broom::tidy(conf.int = TRUE) %>%
  mutate(group = as.character(group)) %>%
  ggplot(aes(x = time, y = estimate, color = group)) +
  geom_point() + geom_line() +
  geom_linerange(aes(ymin = conf.low, ymax = conf.high)) +
  facet_wrap(~group) +
  labs(x = "", y = "ATT(g,t)") +
  theme_minimal()
```

## Publication-Ready Output

### fixest::etable

```r
etable(mod1, mod2, mod3,
       dict = c("Treat:Post" = "Treatment Effect"),
       digits = "r3", digits.stats = "r3",
       signif.code = c('*' = 0.1, '**' = 0.05, '***' = 0.01),
       coefstat = "se", fitstat = NA,
       style.tex = style.tex("aer"),
       file = "table.tex", replace = TRUE)
```

### modelsummary

```r
modelsummary(
  list("(1)" = mod1, "(2)" = mod2),
  fmt = 3,
  estimate = "{estimate}{stars}",
  statistic = "({std.error})",
  stars = c('*' = 0.1, '**' = 0.05, '***' = 0.01),
  gof_map = c("nobs", "r.squared"),
  output = "latex"
)
```
