# DID Estimator Theory and Selection

## Comparison Matrix

| Estimator | Design | PT Required | Homogeneity | Never-Treated | Balanced Panel | Covariates | R Package |
|-----------|--------|:-----------:|:-----------:|:-------------:|:--------------:|:----------:|-----------|
| Classical TWFE | 2x2 | Yes | Yes | Yes | No | Optional | `fixest` |
| Callaway & Sant'Anna (2021) | GxT | Yes | No | No | No | DR/IPW/Reg | `did` |
| Sun & Abraham (2021) | GxT | Yes | No | No | No | Limited | `fixest::sunab()` |
| de Chaisemartin & D'Haultfoeuille (2020) | GxT | Yes | No | No | No | Yes | `DIDmultiplegt` |
| Borusyak, Jaravel & Spiess (2024) | GxT | Yes | No | No | No | Yes | `didimputation` |
| Wooldridge (2021) Extended TWFE | GxT | Yes | No | No | No | Yes | `etwfe` / `fixest` |
| Gardner (2021) Two-Stage | GxT | Yes | No | No | No | Yes | `did2s` |
| Synthetic DID (Arkhangelsky et al. 2021) | GxT | **Relaxed** | No | **Yes** | **Yes** | Optional | `synthdid` |
| Augmented SC (Ben-Michael et al. 2021) | GxT | **Relaxed** | No | No | Preferred | Yes | `augsynth` |
| FEct (Liu, Wang & Xu 2024) | GxT | Yes | No | No | No | Yes | `fect` (fe) |
| IFEct (Liu, Wang & Xu 2024) | GxT | **Relaxed** | No | No | No | Yes | `fect` (ife) |
| MC (Liu, Wang & Xu 2024) | GxT | **Relaxed** | No | No | No | Yes | `fect` (mc) |
| Chained DID (Bellego et al. 2025) | GxT | Yes | No | No | **No (native)** | Yes | `cdid` |

## When TWFE Fails

Classical TWFE (`Y ~ D | unit + time`) fails when:

1. **Staggered timing + heterogeneous effects**: Already-treated units serve as implicit controls, creating "forbidden comparisons" (Goodman-Bacon 2021)
2. **Negative weights**: Some 2x2 comparisons receive negative weights, potentially reversing the sign
3. **Dynamic effects**: TWFE conflates effects at different exposure lengths

Bacon decomposition reveals the problem by decomposing TWFE into weighted averages of:
- Treated vs. never-treated (good)
- Early-treated vs. late-treated (potentially problematic)
- Late-treated vs. early-treated (potentially problematic)

## Standard DID Estimators

### Callaway & Sant'Anna (2021)

**Target**: ATT(g,t) = group-time average treatment effects.

Building-block approach: estimates each 2x2 ATT(g,t) separately, then aggregates. Three estimation methods: regression adjustment, IPW, doubly robust (recommended). Supports conditional PT via covariates. Two control groups: "never treated" (default) or "not yet treated". Multiplier bootstrap for simultaneous confidence bands.

**Aggregation types**:
- `type = "simple"`: weighted average (overweights early-treated)
- `type = "dynamic"`: event-study by exposure time (recommended for dynamics)
- `type = "group"`: average by timing group (recommended for overall ATT)
- `type = "calendar"`: average by calendar time

### Sun & Abraham (2021)

Saturate TWFE with cohort-by-relative-time interactions, then aggregate with appropriate weights. Implemented via `fixest::sunab()`.

### Borusyak, Jaravel & Spiess (2024)

Imputation estimator: estimate unit and time FE from untreated observations only, then impute counterfactuals for treated observations.

### Wooldridge (2021) Extended TWFE

Include cohort-by-time interactions in the regression. Under correct specification, TWFE can work. Implemented via `etwfe` package or manually in `fixest`.

## Synthetic Methods

### Synthetic DID (Arkhangelsky et al. 2021)

Combines DID and Synthetic Control:
- **Like DID**: Allows constant pre-treatment level differences (intercept)
- **Like SC**: Reweights units and time periods to match pre-treatment trends

Unit weights (omega) make controls track treated group's pre-treatment trajectory. Time weights (lambda) emphasize pre-treatment periods most similar to post-treatment. This relaxes PT: trends need not be parallel a priori, only after reweighting.

**Requirements**: Balanced panel, never-treated units, no anticipation.

**Limitations**: No dynamic/event-study effects (single average only), simultaneous adoption only (limited staggered support), no built-in covariate balancing.

```
                Standard DID          Synthetic Control        Synthetic DID
                ───────────           ─────────────────        ─────────────
Unit weights:   Uniform (1/N0)        Optimized (sparse)       Optimized (sparse)
Time weights:   Uniform (1/T0)        None (all pre-periods)   Optimized (sparse)
Intercept:      Yes (unit FE)         No                       Yes (unit FE)
PT assumption:  Required              Not required             Relaxed (via reweighting)
Best when:      Many similar units    Few treated, many ctrl   Intermediate
```

### Augmented Synthetic Control (Ben-Michael et al. 2021)

Improves on standard SC by adding ridge regression augmentation that corrects for imperfect pre-treatment fit. Provides valid inference even when SC weights don't perfectly match.

**Key features**: Automatic bias correction (ridge), staggered adoption via `multisynth()`, event-study output (unlike SDID), conformal inference.

| Feature | `synthdid` | `augsynth` |
|---------|:---:|:---:|
| Reweights time periods | Yes | No |
| Bias correction | No | Yes (Ridge) |
| Dynamic effects | No | Yes (`multisynth`) |
| Staggered adoption | Limited | Yes |
| Balanced panel required | Yes | Preferred |

## Factor Model / Counterfactual Estimators (fect)

Standard DID assumes: $Y_{it}(0) = \alpha_i + \xi_t + X'\beta + \varepsilon$

IFEct relaxes this to: $Y_{it}(0) = \alpha_i + \xi_t + \lambda_i' f_t + X'\beta + \varepsilon$

The interactive term $\lambda_i' f_t$ allows units to have differential exposure to common shocks, relaxing PT.

### Method Selection

| Method | Model for Y(0) | Key Tuning | Best When |
|--------|----------------|------------|-----------|
| `fe` | α_i + ξ_t + X'β | — | PT holds; want diagnostics |
| `ife` | α_i + ξ_t + λ_i'f_t + X'β | r (factors, CV) | Factor structure suspected |
| `mc` | Low-rank L + X'β | λ (nuclear norm, CV) | Uncertain about structure |
| `polynomial` | α_i + Σγ_ip t^p + X'β | degree (1-3) | Unit-specific trends |
| `gsynth` | Same as ife | r (CV) | Few treated units |

### When to Prefer fect

- PT questionable and factor structure suspected
- Want built-in diagnostics (placebo, equivalence, carryover tests)
- Need period-by-period effects but PT may not hold
- Staggered treatment with potential time-varying confounders

### When Other Methods Are Better

- **`did`**: PT plausible, want group-time ATT(g,t), need HonestDiD sensitivity
- **`synthdid`**: Few treated units, balanced panel, want SDID-specific reweighting
- **`augsynth`**: Bias-corrected SC with staggered support
- **`fixest`**: Simple 2x2 or Sun-Abraham event study

## Unbalanced Panel Methods

### The Problem

Standard DID assumes balanced panels. Unbalanced panels create:
1. **Composition changes**: Which units are observed shifts over time
2. **Estimand ambiguity**: "Unit-average ATT" vs "observation-average ATT" diverge
3. **Covariate handling changes**: Balanced uses baseline covariates; unbalanced uses period-specific

**Critical distinction**: "Not yet in sample" (data problem) vs "not yet treated" (design feature). Confusing these biases estimates if missingness correlates with potential outcomes.

### Chained DID (Bellego, Benatia & Dortet-Bernadet, 2025)

Purpose-built for unbalanced panels:
1. Identifies overlapping segments in incomplete panel
2. Estimates short-term (adjacent-period) effects on each segment
3. "Chains" these together to recover longer-term effects
4. Aggregates using optimal or identity weights

**Key assumption**: Trends are missing at random conditional on treatment assignment.

| Method | Best For |
|--------|----------|
| `"2-step"` | Large data, few missing values (optimal GMM weighting) |
| `"Identity"` | Small data, rotating panels, many gaps (more robust to sparse overlap) |

**Rule of thumb**: If > 30% of unit-period cells are missing, start with `"Identity"`.

| Feature | `att_gt()` | `att_gt_cdid()` |
|---------|:---:|:---:|
| Balanced panel | Native | Native |
| Unbalanced panel | `allow_unbalanced_panel=TRUE` (RCS internally) | Native (exploits overlap) |
| Efficiency with serial correlation | Lower | Higher |
| Aggregation | `aggte()` | Same `aggte()` |

### Compositional Changes (Sant'Anna & Xu, 2023/2025)

When unbalanced panels are treated as repeated cross-sections, the population sampled can shift. This is distinct from standard PT issues. They derive semiparametric efficiency bounds and propose DR estimators. Practical test: compare balanced subsample ATT vs unbalanced ATT — large divergence suggests compositional changes matter.

### Endogenous Attrition (Rathnayake et al., 2024)

If attrition correlates with treatment (e.g., treated firms exit the market), standard DID is biased even with correct PT. Approach: Lee-type bounds on ATT under different selection assumptions.

## Triple Differences (DDD)

DDD introduces a **third differencing dimension**: a subgroup within each unit that is **unaffected by treatment** (a "placebo stratum"). DDD = DID_Eligible − DID_Placebo.

**Identifying assumption** (weaker than DID): The *difference* in trends between eligible and ineligible subgroups is the same across treated and control states.

### TWFE DDD with `fixest`

```r
# Saturated FE specification
m_ddd_fe <- feols(Y ~ treat:post:elig |
                  unit_group + time_group + unit_time,
                  data = df, cluster = ~state)
# unit_group = unit x eligibility FE; time_group = time x eligibility FE; unit_time = unit x time FE
```

### Modern DDD with Staggered Treatment: `triplediff`

**Warning**: TWFE DDD under staggering is contaminated by double-differences (Strezhnev 2023).

```r
library(triplediff)

att_ddd <- ddd(
  yname = "Y", tname = "year", idname = "id",
  gname = "treatment_cohort", pname = "eligible",
  xformla = ~ X1 + X2, data = df,
  est_method = "dr", control_group = "notyettreated", panel = TRUE
)
summary(att_ddd)
es <- agg_ddd(att_ddd, type = "event_study")
plot(es)
```

### When DDD Does Not Help

- Spillovers to the placebo group (policy affects ineligible workers too)
- Non-parallel "differences in differences" (compositional shifts)
- Insufficient within-cell variation (few ineligible in treated states)

---

## Continuous / Multi-Valued Treatment

### Two Frameworks

| Feature | CGBS (`contdid`) | dCDH (`did_multiplegt_stat`) |
|---------|-------------------|------------------------------|
| Treatment timing | Staggered, dose fixed at adoption | Continuously varying each period |
| Target parameter | ATT(d,t), ACRT(d,t) | AS, WAS (slopes) |
| Comparison group | Not-yet-treated / never-treated | Stayers (same dose) |
| Multi-period | Yes, event study | Two-period (applied per pair) |

### `contdid` (dose fixed at adoption)

```r
library(contdid)

res_att <- cont_did(
  yname = "Y", tname = "time", idname = "id",
  dname = "dose", gname = "first_treated", data = df,
  target_parameter = "level", aggregation = "dose",
  treatment_type = "continuous", control_group = "notyettreated",
  num_knots = 1, degree = 3, biters = 1000
)
summary(res_att)
ggcont_did(res_att)
```

### `did_multiplegt_stat` (dose varies each period)

```r
library(did_multiplegt_stat)

res <- did_multiplegt_stat(
  df = df, Y = "outcome", ID = "id", Time = "year", D = "tax_rate",
  estimator = "was", estimation_method = "dr",
  order = 2, placebo = TRUE, noextrapolation = TRUE
)
summary(res)
```

### Decision Tree

```
Is dose fixed at adoption?
├── YES → contdid (level, slope, or eventstudy aggregation)
└── NO, varies each period → did_multiplegt_stat (was/iv-was)
```

---

## Non-Absorbing / Reversible Treatment

Standard DID estimators assume absorbing treatment. When treatment switches on and off: group definition collapses, event time is ambiguous, and carryover effects may persist.

### `DIDmultiplegtDYN`

```r
library(DIDmultiplegtDYN)

result <- did_multiplegt_dyn(
  df = df, outcome = "Y", group = "id", time = "time", treatment = "D",
  effects = 5, placebo = 3, cluster = "id",
  switchers = "in"        # or "out" for treatment removal
)
summary(result)
print(result$plot)
```

### `fect` for Switching Treatment

`fect` naturally accommodates treatment switching. Use `carryoverTest` to check if effects persist after treatment removal:

```r
library(fect)
out <- fect(Y ~ D, data = df, index = c("id", "time"), method = "fe",
            se = TRUE, nboots = 200)
out_carry <- fect(Y ~ D, data = df, index = c("id", "time"), method = "fe",
                  se = TRUE, nboots = 200,
                  carryoverTest = TRUE, carryover.period = c(1, 3))
plot(out_carry, stats = "carryover.p")
```

| Feature | `DIDmultiplegtDYN` | `fect` |
|---------|-------------------|--------|
| Switchers-in/out distinction | Yes | No (pooled) |
| Carryover test | Via placebo | Explicit `carryoverTest` |
| Speed | Fast (analytic) | Slower (bootstrap) |
| Non-binary treatment | Yes | No |

---

## References

### Foundational
- Baker, Callaway, Cunningham, Goodman-Bacon & Sant'Anna (2025). "Difference-in-Differences Designs." *JEL*.
- Callaway & Sant'Anna (2021). "Difference-in-Differences with Multiple Time Periods." *J. Econometrics*.
- Goodman-Bacon (2021). "Difference-in-Differences with Variation in Treatment Timing." *Econometrica*.

### Modern Estimators
- Sun & Abraham (2021). "Estimating Dynamic Treatment Effects in Event Studies with Heterogeneous Treatment Effects." *J. Econometrics*.
- Borusyak, Jaravel & Spiess (2024). "Revisiting Event Study Designs." *REStud*.
- de Chaisemartin & D'Haultfoeuille (2020). "Two-Way Fixed Effects Estimators with Heterogeneous Treatment Effects." *AER*.

### Synthetic Methods
- Arkhangelsky, Athey, Hirshberg, Imbens & Wager (2021). "Synthetic Difference-in-Differences." *AER*.
- Ben-Michael, Feller & Rothstein (2021). "The Augmented Synthetic Control Method." *JASA*.
- Ben-Michael, Feller & Rothstein (2022). "Synthetic Controls with Staggered Adoption." *JRSS-B*.
- Abadie (2021). "Using Synthetic Controls." *JEL*.

### Counterfactual / Factor Models
- Liu, Wang & Xu (2024). "A Practical Guide to Counterfactual Estimators." *AJPS*.
- Xu (2017). "Generalized Synthetic Control Method." *Political Analysis*.

### Unbalanced Panels
- Bellego, Benatia & Dortet-Bernadet (2025). "The Chained Difference-in-Differences." *J. Econometrics*, 248.
- Sant'Anna & Xu (2023/2025). "Difference-in-Differences with Compositional Changes." *J. Econometrics*.
- Rathnayake, Negi, Bartalotti & Zhao (2024). "DID with Sample Selection." arXiv:2411.09221.
- Baker, Larcker & Wang (2022). "How Much Should We Trust Staggered DID Estimates?" *JFE*, 144(2).

### Extensions
- Gruber (1994). "The Incidence of Mandated Maternity Benefits." *AER*.
- Olden & Moen (2022). "The Triple Difference Estimator." *Econometrics Journal*.
- Strezhnev (2023). "Decomposing Triple-Differences Regression under Staggered Adoption." arXiv:2307.02735.
- Ortiz-Villavicencio & Sant'Anna (2025). "Better Understanding Triple Differences Estimators." arXiv:2505.09942.
- Callaway, Goodman-Bacon & Sant'Anna (2024). "DID with a Continuous Treatment." NBER WP 32117.
- de Chaisemartin, D'Haultfoeuille, Pasquier, Sow & Vazquez-Bare (2022/2025). arXiv:2201.06898.
- Cengiz, Dube, Lindner & Zipperer (2019). "The Effect of Minimum Wages on Low-Wage Jobs." *QJE*.
- Wing, Freedman & Hollingsworth (2024). "Stacked Difference-in-Differences." NBER WP 32054.
- de Chaisemartin & D'Haultfoeuille (2024). "DID Estimators of Intertemporal Treatment Effects." arXiv:2510.19426.

### Diagnostics & Sensitivity
- Rambachan & Roth (2023). "A More Credible Approach to Parallel Trends." *REStud*.
- Roth (2022). "Pretest with Caution." *AER: Insights*.
- Roth, Sant'Anna, Bilinski & Poe (2023). "What's Trending in Difference-in-Differences?" *J. Econometrics*.
