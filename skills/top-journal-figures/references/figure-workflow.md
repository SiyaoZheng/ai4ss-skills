# Figure Workflow

Use this file when producing or repairing a paper figure in R/ggplot2. The goal is a figure that makes one empirical object easier to inspect without changing the underlying claim.

## Eligibility

A figure is eligible only when all of these are available or repairable:

- selected route and MIDA declarations in `.ai4ss/research_model.aiss`
- real observed public or authorized data provenance
- analysis or descriptive quantity tied to a script, model object, table, or diagnostic output
- sample note and uncertainty rule
- interpretation boundary and downstream review route

If any item is missing, route to the owner instead of inventing a figure.

## Archetypes

Choose the simplest archetype that answers the target inquiry:

- Event-study plot: treatment timing, reference period, point estimates, confidence intervals, pre-period evidence, and estimator note.
- Coefficient plot: selected estimates across outcomes, subgroups, or specifications, with common scale and interval rule.
- RD plot: binned outcome means, fitted lines, cutoff, bandwidth, polynomial or local-linear rule, and density or balance diagnostics when available.
- Binscatter: residualization rule, bin count, fitted line, weights, and sample restrictions.
- Trend comparison: treated/control or group trends with intervention marker, common units, and no unsupported causal title.
- Distribution figure: density, histogram, CDF, or box/violin form with sample sizes and measurement units.
- Map: source projection, geographic unit, legend class rule, missingness, and license or attribution note.
- Mechanism panel: descriptive quantities or diagnostics that support mechanism discussion without overstating causal proof.

## Production Sequence

1. Locate the exact data object, model output, and plotting script.
2. Decide whether the current figure should be main text or appendix.
3. Select or create the shared style profile before final plotting. Reuse an existing `scripts/figure_style.R`, `R/figure_style.R`, or project house style if present; otherwise create a conservative ggplot2 profile.
4. Create or repair script-level figure specs: data path, filters, variables, grouping, estimator or summary rule, intervals, labels, output path, style profile, dimensions, and export device.
5. Select tools for the task, not for style: `broom`/`modelsummary`/`marginaleffects` for model quantities, `ggfixest`/`did` for event-study diagnostics, `cregg` for conjoint outputs, `binsreg`/`rdrobust` for binned and RD designs, `sf` for maps, `ggdist` for uncertainty distributions, `patchwork` for panels, `ggrepel` for direct labels, `viridis`/`colorspace` for accessibility, and `svglite`/`ragg` for devices.
6. Build the final figure as an explicit ggplot object, not as the implicit last plot, and apply the shared style profile.
7. Export vector PDF or SVG first with `ggsave()`. Set width, height, units, background, and device arguments explicitly from the shared style profile. Add PNG only for preview or raster-only content.
8. Render the paper or figure preview when requested.
9. Record `.aiss` artifact/check/decision declarations or a deterministic fragment for the author to merge.

## ggplot2 Defaults

Use these defaults unless the project already has a stronger house style:

- create a named `ggplot` object such as `p_event_study`
- start with `theme_classic()` or `theme_minimal()` and remove only distracting gridlines
- source the shared style profile instead of repeating ad hoc theme, size, scale, legend, and device settings
- use `geom_pointrange()`, `geom_errorbar()`, or `geom_linerange()` for coefficient intervals
- use both color and non-color aesthetics when comparing groups: `linetype`, `shape`, direct labels, or facets
- avoid relying on legend color alone; prefer direct labels for two or three lines
- use `facet_wrap()` or `facet_grid()` for small multiples when one panel would require a busy legend
- use `coord_cartesian()` for zooming without dropping data; do not use scale limits unless dropping observations is intended and declared
- call `ggsave("output/figures/name.pdf", plot = p, device = "pdf", width = ..., height = ..., units = "in")`

## Helper-Package Pattern

When a package produces a plot helper, decide whether it is a diagnostic, a data extractor, or a final ggplot base:

- Diagnostic only: keep the plot for inspection, then recreate the final figure from a declared data frame.
- Data extractor: use the returned estimates, intervals, bins, predictions, or spatial object to build a fresh ggplot.
- Final ggplot base: acceptable only if the script assigns it to a named object, adds journal-ready labels/notes/themes, checks accessibility, and saves it explicitly.

Do not paste screenshots, export plots manually from an IDE, or use non-R plotting tools for final paper figures.

## Figure Spec Fields

Use these fields in handoffs and `.aiss` metadata when possible:

- `figure_id`
- `figure_type`
- `target_inquiry`
- `analysis_artifact`
- `data_source`
- `script_path`
- `figure_path`
- `ggplot_object`
- `ggsave_call`
- `style_profile_id`
- `style_source_path`
- `style_consistency_status`
- `style_exceptions`
- `sample_note`
- `uncertainty_display`
- `source_note`
- `caption`
- `interpretation_boundary`
- `next_skill_route`
