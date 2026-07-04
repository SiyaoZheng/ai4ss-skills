# Pre-Analysis: Panel Data Audit for DID

Before choosing any estimator, deeply understand and validate your data. This file covers the full workflow from raw data to analysis-ready panel.

## Workflow Overview

```
1. Panel structure assessment    → What do you actually have?
2. Treatment variable construction → Who is treated, when, and is it clean?
3. Outcome exploration           → What does the outcome look like?
4. Outcome transformation        → Levels, log, asinh, or Poisson?
5. Raw trend visualization       → Does DID even make sense here?
6. Covariate preparation         → What to condition on, and how?
7. Balance & missingness         → Who is missing, and does it matter?
8. Spot checks                   → Verify data against ground truth
9. Sample construction           → Final analytic sample, documented
```

## 1. Panel Structure Assessment

The first thing to do with any panel dataset: understand what you have.

```r
library(tidyverse)

# Basic dimensions
n_units  <- n_distinct(df$unit_id)
n_periods <- n_distinct(df$year)
n_obs    <- nrow(df)
cat("Units:", n_units, " Periods:", n_periods,
    " Obs:", n_obs, " (balanced would be:", n_units * n_periods, ")\n")

# Balance check: how many periods does each unit appear?
unit_coverage <- df %>%
  count(unit_id, name = "n_periods") %>%
  count(n_periods, name = "n_units")
print(unit_coverage)

# Is it balanced?
is_balanced <- (n_obs == n_units * n_periods)

# Period coverage: how many units appear in each period?
period_coverage <- df %>%
  count(year, name = "n_units")
ggplot(period_coverage, aes(x = year, y = n_units)) +
  geom_col() +
  labs(title = "Units Observed per Period", y = "N units") +
  theme_minimal()

# Gaps: which units have non-consecutive observations?
gaps <- df %>%
  arrange(unit_id, year) %>%
  group_by(unit_id) %>%
  mutate(gap = year - lag(year)) %>%
  filter(!is.na(gap), gap > 1)
if (nrow(gaps) > 0) cat("WARNING:", n_distinct(gaps$unit_id), "units have gaps\n")
```

### Key questions to answer

- **What is the unit?** Country, firm, individual, county? Is the unit ID truly unique per entity?
- **What is the time frequency?** Annual, quarterly, monthly? Are there irregular intervals?
- **How balanced?** Perfectly balanced, mildly unbalanced (few gaps), or severely unbalanced (rotating panel)?
- **Time span**: How many pre-treatment periods? Post-treatment periods? (Need sufficient pre-periods for PT assessment)
- **Duplicates**: Any unit-period duplicates? (Must be zero)

```r
# Check for duplicates (must be zero)
dupes <- df %>% count(unit_id, year) %>% filter(n > 1)
stopifnot(nrow(dupes) == 0)
```

### panelView: dedicated panel visualization (Mou, Liu & Xu 2023, JSS)

```r
library(panelView)

# Treatment status heatmap — the first plot you should make
panelview(Y ~ D, data = df, index = c("unit_id", "year"),
          type = "treat", by.timing = TRUE)

# With treatment history collapsed (cleaner for large panels)
panelview(Y ~ D, data = df, index = c("unit_id", "year"),
          type = "treat", collapse.history = TRUE, leave.gap = TRUE)

# Missing data map
panelview(Y ~ D, data = df, index = c("unit_id", "year"),
          type = "missing")

# Outcome trends by treatment cohort
panelview(Y ~ D, data = df, index = c("unit_id", "year"),
          type = "outcome", by.cohort = TRUE)
```

## 2. Treatment Variable Construction

The treatment timing variable (G_i = first treatment period) is the single most important variable in a DID design. Getting it wrong invalidates everything downstream.

### Constructing first_treat

```r
# From a treatment indicator D_it (0/1 per unit-period)
first_treat <- df %>%
  filter(D == 1) %>%
  group_by(unit_id) %>%
  summarize(first_treat = min(year), .groups = "drop")

# Merge back; never-treated units get 0
df <- df %>%
  left_join(first_treat, by = "unit_id") %>%
  mutate(first_treat = replace_na(first_treat, 0L))
```

### Validation checks (all critical)

```r
# 1. Treatment is absorbing (once treated, stays treated)
absorbing <- df %>%
  left_join(first_treat, by = "unit_id") %>%
  filter(first_treat > 0) %>%
  mutate(should_be_treated = (year >= first_treat)) %>%
  filter(D != should_be_treated)
if (nrow(absorbing) > 0) {
  warning("Treatment is NOT absorbing for ", n_distinct(absorbing$unit_id), " units!")
  # This means units switch in and out — standard DID doesn't apply
  # Options: redefine treatment, use methods for non-absorbing (dCDH)
}

# 2. Treatment timing distribution
treat_dist <- df %>%
  distinct(unit_id, first_treat) %>%
  count(first_treat)
print(treat_dist)
# Watch for: too few units per cohort, treatment in first/last period

# 3. No units treated in the very first period (can't estimate ATT)
first_period <- min(df$year)
treated_at_start <- df %>%
  distinct(unit_id, first_treat) %>%
  filter(first_treat == first_period & first_treat > 0)
if (nrow(treated_at_start) > 0) {
  warning(nrow(treated_at_start), " units treated at t=1 — must drop or redefine")
}

# 4. Sufficient never-treated or not-yet-treated controls
n_never <- sum(treat_dist$first_treat == 0)
cat("Never-treated units:", n_never, "/", n_units, "\n")
if (n_never == 0) cat("No never-treated → must use 'notyettreated' control group\n")

# 5. Anticipation check: any outcome jumps BEFORE first_treat?
# (Visual inspection — see Section 5)
```

### Common treatment coding issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Treatment not absorbing | Units flip D=1→0→1 | Redefine as "ever treated since first_treat" or use non-absorbing methods |
| Missing treatment timing | Some units have D=1 but no clear onset | Go back to raw data; this must be resolved before any analysis |
| Treatment = time-varying policy intensity | D is continuous, not 0/1 | Binary DID may not apply; consider dose-response or binarize at a threshold |
| Treatment in first period | No pre-treatment data for these units | Drop them (they contribute nothing) |
| Never-treated coded as NA instead of 0 | `att_gt()` will crash or silently drop | Recode to 0 |
| Calendar date vs fiscal year mismatch | Treatment timing off by months | Align to the same time frequency |

## 3. Outcome Exploration

Before any modeling, understand the outcome variable thoroughly.

```r
# Distribution
summary(df$Y)
ggplot(df, aes(x = Y)) +
  geom_histogram(bins = 50) +
  labs(title = "Outcome Distribution (pooled)") +
  theme_minimal()

# Distribution by treatment status
df %>%
  mutate(ever_treated = first_treat > 0) %>%
  ggplot(aes(x = Y, fill = ever_treated)) +
  geom_histogram(position = "identity", alpha = 0.5, bins = 50) +
  theme_minimal()

# Over time
df %>%
  group_by(year) %>%
  summarize(mean_Y = mean(Y, na.rm = TRUE),
            sd_Y = sd(Y, na.rm = TRUE),
            p10 = quantile(Y, 0.1, na.rm = TRUE),
            p90 = quantile(Y, 0.9, na.rm = TRUE)) %>%
  ggplot(aes(x = year)) +
  geom_line(aes(y = mean_Y)) +
  geom_ribbon(aes(ymin = p10, ymax = p90), alpha = 0.2) +
  labs(title = "Outcome Over Time (mean + 10-90th percentile)") +
  theme_minimal()
```

### What to look for

- **Outliers**: Extreme values that could drive results. Check top/bottom 1%.
- **Zeros and bounded outcomes**: Proportions, counts, binary — may need transformation.
- **Missing values**: How many? Patterned or random?
- **Trends**: Is there a strong secular trend? (Parallel trends is about *relative* trends, but strong trends amplify small violations)
- **Variance changes**: Does outcome variance change over time or across groups? (Affects inference)
- **Scale**: Are levels or logs more appropriate? (PT is scale-dependent — see diagnostics.md)

```r
# Outlier check
df %>%
  summarize(
    p01 = quantile(Y, 0.01, na.rm = TRUE),
    p99 = quantile(Y, 0.99, na.rm = TRUE),
    n_zero = sum(Y == 0, na.rm = TRUE),
    n_na = sum(is.na(Y)),
    pct_na = mean(is.na(Y))
  )

# Log transformation feasibility
if (any(df$Y <= 0, na.rm = TRUE)) {
  cat("Y has non-positive values — log(Y) not directly feasible\n")
  cat("Options: log(Y+1), asinh(Y), or keep in levels\n")
}
```

## 4. Outcome Transformation Decision

PT is scale-dependent (Roth & Sant'Anna 2023, *Econometrica*): it may hold in levels but not logs, or vice versa. This is not a nuisance — it reflects a substantive choice about the treatment effect you're estimating.

### The Chen & Roth (2024, QJE) trilemma: "Logs with Zeros?"

You cannot simultaneously have: (1) individual-level ATEs, (2) unit invariance (results don't depend on measurement units), and (3) point identification. Must choose.

### Decision flowchart

```
Does Y have zeros or negatives?
├── No, Y > 0 always
│   ├── Want percentage effects → log(Y)
│   └── Want level effects → Y in levels
│
└── Yes, Y has zeros
    ├── Y is a count → Poisson regression (fepois in fixest)
    │   Interpretation: exp(β) = multiplicative effect on E[Y]
    │   Advantage: scale-invariant (Chen & Roth 2024)
    │
    ├── Want percentage effects → Poisson, or estimate margins separately
    │
    ├── asinh(Y) as variance stabilizer → acceptable BUT:
    │   ⚠️ NOT scale-invariant (results change with measurement units)
    │   ⚠️ Coefficients have no direct interpretation (Bellemare & Wichman 2020)
    │   ⚠️ Must retransform for marginal effects (Duan's smearing)
    │   Only use as robustness check, not primary specification
    │
    └── log(Y + 1) or log(Y + c) → ad hoc, results depend on c
        Avoid as primary specification
```

### Sensitivity: compare transformations

```r
library(fixest)
est_level   <- feols(Y ~ D | unit_id + year, data = df, cluster = ~unit_id)
est_log     <- feols(log(Y) ~ D | unit_id + year,
                     data = df %>% filter(Y > 0), cluster = ~unit_id)
est_poisson <- fepois(Y ~ D | unit_id + year, data = df, cluster = ~unit_id)
est_asinh   <- feols(asinh(Y) ~ D | unit_id + year, data = df, cluster = ~unit_id)
etable(est_level, est_log, est_poisson, est_asinh)

# Formal test: Roth & Sant'Anna functional form sensitivity
# install.packages("didFF")  # or devtools::install_github("jonathandroth/didFF")
```

### What to report

- State the primary specification's transformation and justify it
- Report at least one alternative transformation as robustness
- If results are sensitive to transformation → PT assumption is fragile (flag this)

## 5. Raw Trend Visualization

**This is the single most important diagnostic plot in any DID analysis.** Plot raw outcome trends by treatment group BEFORE running any model.

### Group-level trends (the essential plot)

```r
# Mean outcome by treatment status over time
trend_data <- df %>%
  mutate(group = case_when(
    first_treat == 0 ~ "Never Treated",
    TRUE ~ paste0("Treated (g=", first_treat, ")")
  )) %>%
  group_by(group, year) %>%
  summarize(mean_Y = mean(Y, na.rm = TRUE),
            se_Y = sd(Y, na.rm = TRUE) / sqrt(n()),
            .groups = "drop")

ggplot(trend_data, aes(x = year, y = mean_Y, color = group)) +
  geom_line() + geom_point() +
  geom_ribbon(aes(ymin = mean_Y - 1.96*se_Y,
                  ymax = mean_Y + 1.96*se_Y,
                  fill = group), alpha = 0.1, color = NA) +
  labs(title = "Raw Outcome Trends by Treatment Cohort",
       x = "", y = "Mean Outcome") +
  theme_minimal()
```

### Simplified: treated vs control

```r
trend_simple <- df %>%
  mutate(ever_treated = factor(first_treat > 0,
                               labels = c("Control", "Treated"))) %>%
  group_by(ever_treated, year) %>%
  summarize(mean_Y = mean(Y, na.rm = TRUE), .groups = "drop")

ggplot(trend_simple, aes(x = year, y = mean_Y, color = ever_treated)) +
  geom_line(linewidth = 1) + geom_point() +
  labs(title = "Raw Outcome: Treated vs Control",
       subtitle = "Do pre-treatment trends look parallel?",
       x = "", y = "Mean Outcome", color = "") +
  theme_minimal()
```

### What to look for in raw trends

- **Pre-treatment parallelism**: Do treated and control groups trend similarly before treatment? This is your first (informal) PT check.
- **Level differences**: DID allows constant level differences — that's fine. Worry about *trend* differences.
- **Anticipation**: Does the treated group start diverging *before* the treatment date?
- **Treatment effect visibility**: Can you "see" the effect in the raw data? If not, it may be small or absent.
- **Confounding events**: Any common shocks (recessions, policy changes) at the treatment date?

### Unit-level trajectories (spaghetti plot)

```r
# Sample of units to avoid overplotting
set.seed(123)
sample_ids <- df %>%
  distinct(unit_id, first_treat) %>%
  group_by(first_treat > 0) %>%
  slice_sample(n = min(20, n())) %>%
  pull(unit_id)

df %>%
  filter(unit_id %in% sample_ids) %>%
  mutate(ever_treated = first_treat > 0) %>%
  ggplot(aes(x = year, y = Y, group = unit_id, color = ever_treated)) +
  geom_line(alpha = 0.3) +
  labs(title = "Unit-Level Trajectories (sample)",
       subtitle = "Check for outlier units driving results") +
  theme_minimal()
```

## 6. Covariate Preparation

### Time-invariant vs time-varying

```r
# Classify covariates: does X vary within unit?
covar_cols <- c("X1", "X2", "X3", "X4")

covar_variation <- df %>%
  group_by(unit_id) %>%
  summarize(across(all_of(covar_cols), ~ n_distinct(.x)), .groups = "drop") %>%
  summarize(across(all_of(covar_cols), ~ mean(.x > 1)))
print(covar_variation)
# Values near 0 = time-invariant; near 1 = time-varying
```

### Baseline covariate extraction

For the `did` package with balanced panels, covariates are automatically set to base-period values. For unbalanced panels or manual analysis:

```r
# Extract baseline (pre-treatment) covariates
baseline_covars <- df %>%
  filter(year < first_treat | first_treat == 0) %>%
  group_by(unit_id) %>%
  # Use first available pre-treatment observation
  # Or: mean of all pre-treatment observations
  summarize(across(all_of(covar_cols), ~ first(.x[!is.na(.x)])),
            .groups = "drop")
```

### Covariate balance table

```r
# Compare treated vs control on baseline covariates
balance <- df %>%
  filter(year == min(year)) %>%  # or any pre-treatment period
  mutate(treated = first_treat > 0) %>%
  group_by(treated) %>%
  summarize(across(all_of(covar_cols),
                   list(mean = mean, sd = sd),
                   .names = "{.col}_{.fn}"),
            n = n(), .groups = "drop")

# Normalized differences
norm_diff <- function(m1, m0, s1, s0) {
  (m1 - m0) / sqrt((s1^2 + s0^2) / 2)
}
# |Norm. Diff.| > 0.25 is problematic (Imbens & Rubin 2015)
```

### Which covariates to include?

| Include | Exclude |
|---------|---------|
| Pre-treatment predictors of outcome trends | Post-treatment outcomes (bad controls) |
| Time-invariant confounders | Variables affected by treatment (mechanisms) |
| Baseline characteristics that predict selection | Covariates with no variation |

**Key principle**: Covariates should predict *trends* (not just levels) to be useful for conditional PT. A covariate that predicts levels but not trends adds noise without helping identification.

## 7. Balance and Missingness

### Missingness map

```r
# Visual: which unit-periods are observed?
df %>%
  mutate(observed = 1) %>%
  complete(unit_id, year, fill = list(observed = 0)) %>%
  ggplot(aes(x = year, y = factor(unit_id), fill = factor(observed))) +
  geom_tile() +
  scale_fill_manual(values = c("0" = "white", "1" = "steelblue")) +
  labs(title = "Panel Observation Map", y = "Unit", fill = "Observed") +
  theme_minimal() +
  theme(axis.text.y = element_blank())

# Summary: missingness by treatment group
missing_by_group <- df %>%
  complete(unit_id, year) %>%
  left_join(df %>% distinct(unit_id, first_treat), by = "unit_id") %>%
  mutate(treated = first_treat > 0,
         missing = is.na(Y)) %>%
  group_by(treated, year) %>%
  summarize(pct_missing = mean(missing), .groups = "drop")

ggplot(missing_by_group, aes(x = year, y = pct_missing, color = treated)) +
  geom_line() + geom_point() +
  scale_y_continuous(labels = scales::percent) +
  labs(title = "Missingness Rate by Treatment Status",
       subtitle = "Differential missingness suggests endogenous attrition") +
  theme_minimal()
```

### Attrition test

```r
# Is attrition correlated with treatment?
# Simple test: regress "observed in period t" on treatment status
attrition_test <- df %>%
  complete(unit_id, year) %>%
  left_join(df %>% distinct(unit_id, first_treat), by = "unit_id") %>%
  mutate(observed = !is.na(Y),
         treated = first_treat > 0)

# Per period
attrition_results <- attrition_test %>%
  group_by(year) %>%
  summarize(
    obs_treated = mean(observed[treated]),
    obs_control = mean(observed[!treated]),
    diff = obs_treated - obs_control,
    .groups = "drop"
  )
# Large differential attrition → endogenous → see diagnostics.md
```

### Sample composition over time

```r
# Do observable characteristics of the sample change over time?
# (Relevant for unbalanced panels)
composition <- df %>%
  group_by(year) %>%
  summarize(across(all_of(covar_cols), mean, na.rm = TRUE),
            n = n(), .groups = "drop")
# If covariate means shift substantially → compositional changes
```

## 8. Spot Checks

Before running any estimator, verify your data against ground truth. Spot checks catch data construction errors that no statistical test can detect.

### Unit-level deep dives

```r
# Pick 3-5 random units from each group and manually trace their data
set.seed(42)
spot_units <- df_final %>%
  distinct(unit_id, first_treat) %>%
  mutate(group = ifelse(first_treat == 0, "control", "treated")) %>%
  group_by(group) %>%
  slice_sample(n = 3) %>%
  pull(unit_id)

# Print full panel for each unit — read every row
spot_data <- df_final %>%
  filter(unit_id %in% spot_units) %>%
  arrange(unit_id, year) %>%
  select(unit_id, year, first_treat, D, Y, everything())
print(spot_data, n = Inf)
```

**What to verify for each unit**:
- Does treatment timing (`first_treat`, `D`) match what you know from the original source?
- Does the outcome trajectory make sense substantively? (e.g., GDP shouldn't jump 10x)
- Are covariate values plausible and stable where they should be?
- Any suspicious patterns: identical values across years, sudden jumps, implausible zeros?

### Treatment timing verification

```r
# Cross-reference treatment dates against original source documents
# This catches the most consequential errors in DID
treat_units <- df_final %>%
  filter(first_treat > 0) %>%
  distinct(unit_id, first_treat) %>%
  arrange(first_treat)

# For a manageable number of treated units, verify ALL of them
# For many: sample at least 10% or 20 units, whichever is larger
n_verify <- max(ceiling(nrow(treat_units) * 0.1), min(20, nrow(treat_units)))
verify_sample <- treat_units %>% slice_sample(n = n_verify)
cat("Verify these", nrow(verify_sample), "treatment dates against source:\n")
print(verify_sample)
```

### Known events check

```r
# Do known external events show up in your data?
# Example: if a recession happened in 2008, do you see it?
df_final %>%
  group_by(year) %>%
  summarize(mean_Y = mean(Y, na.rm = TRUE), .groups = "drop") %>%
  print(n = Inf)
# If 2008 doesn't show a dip when it should → data problem

# Example: if a specific unit experienced a known shock, does it appear?
# df_final %>% filter(unit_id == "known_unit") %>% select(year, Y)
```

### Aggregate validation

```r
# Compare your data aggregates against published statistics
# Example: do your state-level totals match Census/BLS published numbers?
agg_check <- df_final %>%
  group_by(year) %>%
  summarize(
    total_Y = sum(Y, na.rm = TRUE),
    mean_Y = mean(Y, na.rm = TRUE),
    n = n(),
    .groups = "drop"
  )
# Compare these against external published aggregates
# Large discrepancies → sample construction or data cleaning error
```

### Boundary case inspection

```r
# Check units at the extremes — these often drive results
extremes <- df_final %>%
  group_by(unit_id) %>%
  summarize(mean_Y = mean(Y, na.rm = TRUE),
            sd_Y = sd(Y, na.rm = TRUE),
            max_change = max(diff(Y), na.rm = TRUE),
            .groups = "drop")

# Units with largest outcome levels
cat("--- Top 5 by mean outcome ---\n")
extremes %>% slice_max(mean_Y, n = 5) %>% print()

# Units with largest period-to-period changes
cat("--- Top 5 by max single-period change ---\n")
extremes %>% slice_max(max_change, n = 5) %>% print()

# Units with highest variance (most volatile)
cat("--- Top 5 by outcome volatility ---\n")
extremes %>% slice_max(sd_Y, n = 5) %>% print()

# Investigate these units: are they real or data errors?
```

### Coding consistency

```r
# Check that categorical variables are consistently coded
# Example: state FIPS codes, industry codes, etc.
df_final %>%
  group_by(unit_id) %>%
  summarize(n_unique_state = n_distinct(state_code), .groups = "drop") %>%
  filter(n_unique_state > 1)
# Any unit with changing "fixed" attributes → data merge error
```

## 9. Sample Construction

### Decision log (document everything)

Every sample restriction should be explicitly documented as an ex ante decision (fixed before seeing results).

```r
# Start from raw data and document each step
cat("Raw data:", nrow(df_raw), "obs,", n_distinct(df_raw$unit_id), "units\n")

# Step 1: Drop units with no valid outcome
df1 <- df_raw %>% filter(!is.na(Y))
cat("After dropping missing Y:", nrow(df1), "obs,", n_distinct(df1$unit_id), "units\n")

# Step 2: Drop units treated before sample period
df2 <- df1 %>% filter(first_treat == 0 | first_treat >= min(year))
cat("After dropping already-treated:", nrow(df2), "obs,", n_distinct(df2$unit_id), "units\n")

# Step 3: Restrict to relevant time window (if applicable)
df3 <- df2 %>% filter(between(year, start_year, end_year))
cat("After time restriction:", nrow(df3), "obs,", n_distinct(df3$unit_id), "units\n")

# Step 4: Drop outliers (must justify threshold ex ante)
# df4 <- df3 %>% filter(Y < quantile(Y, 0.99))

# Step 5: Balance panel (if required by estimator)
# df_balanced <- df3 %>%
#   group_by(unit_id) %>%
#   filter(n() == n_distinct(df3$year)) %>%
#   ungroup()
# cat("Balanced panel:", nrow(df_balanced), "obs,", n_distinct(df_balanced$unit_id), "units\n")

# Final analytic sample
df_final <- df3
```

### Pre-analysis summary table

```r
# This table should appear in your paper
summary_table <- df_final %>%
  mutate(group = case_when(
    first_treat == 0 ~ "Never Treated",
    TRUE ~ paste0("g=", first_treat)
  )) %>%
  group_by(group) %>%
  summarize(
    n_units = n_distinct(unit_id),
    n_obs = n(),
    across(c(Y, all_of(covar_cols)),
           list(mean = ~ mean(.x, na.rm = TRUE),
                sd = ~ sd(.x, na.rm = TRUE)),
           .names = "{.col}_{.fn}"),
    .groups = "drop"
  )
```

## Checklist: Data Preparation Complete?

### Panel structure
- [ ] Unit ID is truly unique per entity (no duplicates)
- [ ] Time variable has no unexpected gaps or irregularities
- [ ] Panel balance documented (balanced, mildly unbalanced, severely unbalanced)
- [ ] Sufficient pre-treatment periods (at least 3-4 for event study)

### Treatment variable
- [ ] first_treat correctly identifies onset for every treated unit
- [ ] Treatment is absorbing (or non-absorbing case documented)
- [ ] Never-treated coded as 0 (not NA)
- [ ] No units treated in the very first period
- [ ] Treatment timing distribution examined (no tiny cohorts)

### Outcome
- [ ] Distribution examined (outliers, zeros, bounds)
- [ ] Missing outcome pattern documented
- [ ] Transformation decision made and justified (levels, log, Poisson, asinh)
- [ ] Alternative transformations compared as robustness
- [ ] If Y has zeros: Poisson or justified alternative (not ad hoc log(Y+1))

### Raw trends
- [ ] **Plotted raw outcome trends by treatment group** (the essential plot)
- [ ] Pre-treatment trends visually assessed for parallelism
- [ ] No obvious anticipation effects
- [ ] No confounding events at treatment date identified

### Covariates
- [ ] Classified as time-varying vs time-invariant
- [ ] Baseline values extracted
- [ ] Balance table computed (normalized differences)
- [ ] Covariate selection justified (predictors of trends, not mechanisms)

### Missingness
- [ ] Missingness pattern mapped
- [ ] Differential attrition tested
- [ ] Sample composition stability checked

### Spot checks
- [ ] Random units inspected end-to-end (treatment timing, outcome trajectory, covariates)
- [ ] Treatment dates verified against original source for a sample of units
- [ ] Known external events visible in the data (recessions, policy changes)
- [ ] Aggregates compared against published statistics where possible
- [ ] Extreme observations investigated (not just trimmed without inspection)
- [ ] Categorical variable coding consistent within units across time

### Sample
- [ ] Every sample restriction documented with observation counts
- [ ] Restrictions are ex ante decisions (not outcome-driven)
- [ ] Summary statistics table prepared
