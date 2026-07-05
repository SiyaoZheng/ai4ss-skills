# Community Practice And Tooling

Use this file when choosing implementation patterns for top-journal social-science figures. The sources behind this synthesis include applied economics, political methodology, causal inference, conjoint analysis, model interpretation, and ggplot2 extension work. Do not split decisions by discipline; split them by the figure's evidentiary job.

## Operating Principle

Final paper figures are explicit ggplot2 artifacts. Practical tools may estimate models, compute quantities, tidy outputs, create diagnostics, compose panels, place labels, check accessibility, or choose graphics devices. They do not replace the final contract:

- named plotted data frame
- named `ggplot` object
- shared style profile and style source path
- declared estimate, uncertainty, group, panel, bin, bandwidth, or projection columns
- caption, source note, sample note, and interpretation boundary
- explicit `ggsave()` call to a vector PDF or SVG when possible

Default plots from packages are useful diagnostics. They become manuscript figures only after they are rebuilt or wrapped so the plotted quantities and visual choices are inspectable in code.

## Practical Toolbox

Prefer tools already used by the project. Add a dependency only when it removes real analytical risk or avoids fragile hand extraction.

| Job | Useful R tools | Use for | Guardrail |
|---|---|---|---|
| Core plotting | `ggplot2`, `scales` | all final paper figures, axes, labels, scales, export through `ggsave()` | final manuscript figure must remain a named ggplot2 object |
| Tidy model output | `broom`, `parameters`, `modelsummary::modelplot()` | extracting estimates, confidence intervals, model comparison coefficients | inspect the term mapping; omit intercepts/fixed effects intentionally |
| Fixed effects and event studies | `fixest`, `ggfixest` | fast FE models, coefficient plots, interaction plots, event-study diagnostics | declare reference period, omitted category, clustering, and interval rule |
| Modern DiD | `did`, `did2s`, `HonestDiD` | group-time ATT, dynamic effects, estimator comparisons, sensitivity checks | do not imply parallel trends from a plot alone; route estimator risk to `did-expert` or `methods-reviewer` |
| Marginal effects and predictions | `marginaleffects`, `emmeans` | predictions, comparisons, slopes, adjusted means, quantities of interest | plot meaningful grids or subgroup averages, not raw coefficient scale when the estimand is transformed |
| Conjoint and survey experiments | `cregg`, `cjoint`, `survey` | AMCEs, marginal means, constrained conjoint diagnostics, weighted intervals | show reference categories and design restrictions clearly |
| Binned scatter | `binsreg` | binscatter, covariate-adjusted bins, confidence bands, bin selection | declare binning rule, covariate adjustment, weights, clustering, and fitted line rule |
| Regression discontinuity | `rdrobust`, `rdplot` | RD plots, bandwidth diagnostics, local polynomial fit, cutoff display | declare cutoff, bandwidth, kernel, polynomial order, and whether bins are exploratory |
| Spatial figures | `sf`, `tigris`, `rnaturalearth`, `ggspatial` | maps, projections, geographic joins, missingness displays | declare projection, geographic unit, source/license, and missing geography |
| Uncertainty distributions | `ggdist`, `tidybayes` | interval slabs, posterior or bootstrap distributions, distribution-aware uncertainty | use only when distributions matter; avoid decorative rainclouds for simple coefficients |
| Panel composition | `patchwork`, `cowplot` | multi-panel figures with shared labels and fixed layouts | panel scales and captions must be consistent and declared |
| Direct labels | `ggrepel`, `geomtextpath` | readable line labels, point labels, avoiding legend overload | set seeds when label placement is stochastic; labels must not hide uncertainty |
| Text and annotations | `ggtext`, `latex2exp` | limited rich text, mathematical labels, formatted notes | keep figure text journal-legible; avoid complex styling that breaks PDF/SVG output |
| Accessibility | `viridis`, `viridisLite`, `colorspace`, `colorblindr` | perceptual palettes, colorblind checks, grayscale checks | color cannot be the only grouping signal; add shape, line type, labels, or facets |
| Devices and export | `svglite`, `ragg`, `cairo_pdf`, `systemfonts` | clean SVG, high-quality raster previews, font/device stability | final vector export first; raster only for preview or raster-native content |

## Figure Recipes

### Event Study Or Dynamic DiD

Use `fixest`/`ggfixest` when the project estimates event studies with `feols()` and `i()` terms. Use `did::aggte(..., type = "dynamic")` and `ggdid()` when group-time ATT is the design. Use `did2s` when the design explicitly relies on two-stage DiD helpers. Treat all package plots as diagnostics unless the script exposes the plotted event-time data.

Final ggplot2 pattern:

- event time on x-axis; estimate on y-axis
- points plus vertical intervals, usually not only ribbons
- horizontal zero line and reference-period/treatment marker
- visible omitted period or reference category
- estimator, fixed effects, clustering, treatment timing, and sample in the note
- pre-period interpretation bounded as evidence relevant to, not proof of, parallel trends

### Coefficient, AMCE, And Marginal-Effect Plots

Use `broom`, `modelsummary::modelplot()`, `marginaleffects`, or `cregg` to create tidy estimates. The final figure should usually be a horizontal point-interval plot sorted by the substantive comparison, not by p-value.

Final ggplot2 pattern:

- one row per estimand or comparison
- x-axis in meaningful units, percent points, probabilities, or transformed scale
- point estimates with 90/95 percent intervals as appropriate
- clear reference categories and omitted terms
- facets or small multiples for outcomes/specifications instead of cluttered legends

### Binscatter And RD

Use `binsreg` for binned scatter logic and `rdrobust`/`rdplot` for RD-specific bandwidth and cutoff diagnostics. If package output is not a plain ggplot object, extract the plotted data or recreate the summary data deterministically.

Final ggplot2 pattern:

- raw or binned points plus fitted line only when the fitting rule is declared
- bin count or selector, bandwidth, polynomial/local-linear rule, weights, and covariate adjustment in the note
- cutoff line for RD and separate fits on each side
- no visual smoothing that is absent from the analysis plan

### Trends, Distributions, And Mechanisms

Use plain `dplyr`/`data.table` summaries and ggplot2 geoms first. Use `ggdist` only when uncertainty distributions, posterior draws, or bootstrap distributions are central to the claim. Use direct labels or facets before multi-color legends.

Final ggplot2 pattern:

- trends: common units, intervention markers, no unsupported causal title
- distributions: sample sizes, measurement units, and binwidth/bandwidth choices
- mechanisms: descriptive or diagnostic labels that do not overstate causal proof

### Maps

Use `sf` with `geom_sf()` and explicit projection handling. Keep maps analytical: geographic unit, classification rule, missingness, and source attribution matter more than decorative basemaps.

Final ggplot2 pattern:

- projection and geographic unit declared
- legend classes or continuous scale explained
- missing or suppressed units visibly handled
- source/license note included
- colorblind and grayscale readability checked

## Style And Reproducibility Defaults

- Create or source one style profile before producing the final figure set. Do not let helper-package defaults set inconsistent fonts, legends, line widths, or palettes.
- Use `theme_classic()` or restrained `theme_minimal()` unless the paper has a documented house theme.
- Use large enough base font for journal columns; do not rely on the manuscript caption to fix illegible axis text.
- Prefer direct labels for two or three series.
- Add non-color encodings: shape, linetype, facet, or label.
- Use `coord_cartesian()` for visual zooming; use scale limits only when dropping data is intended and documented.
- Set seeds for stochastic label placement, sampling, bootstrapping, simulation-based intervals, or jitter.
- Keep final scripts runnable with `Rscript --vanilla`.
- Record package versions or `sessionInfo()` when figure output is sensitive to package/device behavior.

## Sources To Learn From

- AEA and APSA style guidance for vector files, source notes, interpretable black-and-white figures, and consistent graphics.
- Jonathan Kastellec and related political-science graph advice: readable labels, direct labeling, small multiples, line types and shapes, and graphs as substitutes for opaque coefficient tables.
- Grant McDermott's `ggfixest` and Data Science for Economists materials: ggplot2-compatible model and spatial workflows.
- Brantly Callaway's `did` package and DID workshop materials: dynamic effects and group-time ATT plotting.
- Vincent Arel-Bundock's `modelsummary`/`modelplot` and `marginaleffects`: model-to-quantity-to-plot workflows.
- Thomas Leeper's `cregg`: conjoint analysis and ggplot2-based AMCE/marginal-mean visualization.
- Andrew Heiss's social-science ggplot2 materials: reproducible ggplot2 conceptual and empirical figures.
- Pablo Barbera's social-science ggplot2 workshop materials: line plots, coefficient plots, maps, and social-science use cases.
