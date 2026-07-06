# Style Contract

Use this file whenever a manuscript has more than one final paper figure, or when a single figure is likely to become part of a figure set. The style contract is mandatory. It prevents a paper from looking like figures were assembled from unrelated scripts, defaults, or software.

## Non-Negotiable Rule

All final manuscript figures must share one style profile. A style profile is code, not prose. Prefer a project-level R file such as `scripts/figure_style.R` that is sourced by every final figure script.

Acceptable alternatives:

- an existing project R package or `R/figure_style.R`
- a documented house-style script already used by the paper
- a single plotting script that defines shared style constants before creating all final figures

Unacceptable:

- copied ad hoc `theme()` calls that drift across figures
- manual edits in Illustrator, PowerPoint, Preview, or an IDE export pane
- screenshot, dashboard, or notebook-rendered final figures
- package-default plots that use inconsistent themes, legends, fonts, or geoms

## Mandatory Style Elements

The style profile must define or preserve these elements:

| Element | Required decision |
|---|---|
| `style_profile_id` | short stable name such as `ai4ss_journal_v1` or project-specific house style |
| Base theme | one complete ggplot2 base, usually restrained `theme_classic()` or `theme_minimal()` |
| Font family | one publication-safe family; use device-safe fonts and avoid per-figure font changes |
| Font hierarchy | base size, axis title size, axis text size, strip text size, legend text size, panel-tag size |
| Figure dimensions | standard single-column, double-column, and panel dimensions in inches |
| Aspect ratios | allowed ratios for coefficient/event-study, trend, distribution, map, and multi-panel figures |
| Margins and spacing | plot margins, panel spacing, legend spacing, and facet strip spacing |
| Axis style | axis title placement, tick length, tick text, break density, units, percent/number format |
| Grid/background | panel background, major/minor grid rules, border rules, and zero/reference line style |
| Point geometry | default point size, shape set, stroke width, dodge width, jitter rule if used |
| Line geometry | default line width, linetype set, smoothing/fitted-line style, intervention/reference markers |
| Interval geometry | default CI geom, line width, cap width, alpha, and 90/95 percent interval convention |
| Color palette | named palette with semantic mapping; color cannot be the only group indicator |
| Non-color encodings | shape, linetype, facet, direct label, or pattern mapping for all grouped figures |
| Legend contract | position, order, title style, key size, collected-guide rule, or direct-label replacement |
| Facet/panel contract | panel tags, strip labels, shared/free scale rules, panel order, panel captions if needed |
| Annotation style | annotation font, arrows, treatment/cutoff markers, label placement, and allowed emphasis |
| Caption/note convention | what belongs in the figure object versus the manuscript caption/source note |
| Export contract | device, width, height, units, background, DPI for raster preview, and vector-first rule |
| File naming | stable lowercase figure filenames with figure number and semantic stem |
| Reproducibility | seed rules, package/device version notes when relevant, and `Rscript --vanilla` command |

## Default AI4SS Journal Profile

When no style exists, create a conservative profile equivalent to:

```r
AI4SS_FIGURE_STYLE <- list(
  profile_id = "ai4ss_journal_v1",
  base_family = "Helvetica",
  base_size = 10,
  axis_title_size = 10,
  axis_text_size = 9,
  strip_text_size = 9,
  legend_text_size = 9,
  caption_size = 8,
  linewidth = 0.45,
  point_size = 1.8,
  interval_linewidth = 0.35,
  interval_width = 0.12,
  single_col_width = 3.25,
  double_col_width = 6.5,
  standard_height = 4.0,
  panel_height = 3.2
)

theme_ai4ss_figure <- function(base_size = AI4SS_FIGURE_STYLE$base_size,
                               base_family = AI4SS_FIGURE_STYLE$base_family) {
  ggplot2::theme_classic(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      plot.title = ggplot2::element_blank(),
      plot.subtitle = ggplot2::element_blank(),
      axis.title = ggplot2::element_text(size = AI4SS_FIGURE_STYLE$axis_title_size),
      axis.text = ggplot2::element_text(size = AI4SS_FIGURE_STYLE$axis_text_size),
      strip.text = ggplot2::element_text(size = AI4SS_FIGURE_STYLE$strip_text_size),
      legend.title = ggplot2::element_blank(),
      legend.text = ggplot2::element_text(size = AI4SS_FIGURE_STYLE$legend_text_size),
      legend.position = "bottom",
      panel.spacing = grid::unit(0.8, "lines"),
      plot.margin = ggplot2::margin(5.5, 5.5, 5.5, 5.5)
    )
}

ai4ss_palette <- c(
  "primary" = "#1B4E77",
  "secondary" = "#8C2D04",
  "tertiary" = "#2E6F40",
  "neutral" = "#4D4D4D"
)

ai4ss_linetypes <- c("solid", "dashed", "dotdash", "dotted")
ai4ss_shapes <- c(16, 17, 15, 1)
```

This is a starting point, not a license to ignore journal requirements. If a target journal or paper already has a stronger style, preserve that profile and record the choice.

## Consistency Checklist

A figure set passes style consistency only when:

- every final figure script sources the same style file or defines the same style object once
- all final figures use the same base theme, font family, font hierarchy, margins, legend convention, and export device family
- repeated semantic groups use the same color, shape, and linetype mappings across figures
- coefficient and event-study plots use the same point/interval geometry unless a declared figure type requires otherwise
- treatment, cutoff, zero, and reference markers use the same visual language across figures
- panels use consistent tags, strip labels, spacing, and shared/free scale decisions
- all axes use comparable number formatting and units for comparable quantities
- source notes, sample notes, and uncertainty notes follow one sentence pattern
- exceptions are few, substantive, and recorded as `style_exceptions`

## Required Handoff Status

Return these fields:

```text
style_profile_id:
style_source_path:
style_consistency_status: passed | repaired | blocked
style_exceptions:
```

Use `blocked` only when the figure cannot be made consistent without changing evidence, scale, estimand, or journal constraints. Otherwise repair automatically.
