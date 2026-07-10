---
name: top-journal-figures
description: >
  Develop rigorous empirical figures for political-science research and publication. Use when choosing
  how to visualize an estimand, comparison, trend, distribution, event study, RD, coefficient set,
  mechanism, map, uncertainty, or diagnostic; repairing misleading graphics; or turning analysis
  outputs into an inspectable visual argument. Triggers include "paper figure", "event-study plot",
  "coefficient plot", "visualize results", "publication figure", "论文图", "结果可视化",
  "事件研究图", "系数图".
---

# Top Journal Figures

Use visualization as part of empirical reasoning. A figure should make a political pattern,
comparison, uncertainty, or design limitation easier to inspect than it would be in prose or a dense
table.

## Figures and interpretive record

The work should leave:

1. an inspectable figure tied to a clear evidentiary job;
2. reproducible plotting code and the exact plotted data or quantities; and
3. a short **Figure Interpretation Note** explaining what the figure reveals, what it does not establish,
   and whether it changes the analysis or argument.

## Graphical analysis

### 1. Define the figure's evidentiary job

State the one question the figure should help answer. Examples include showing treatment timing and raw
trends, communicating an estimand with uncertainty, revealing heterogeneous effects, comparing
distributions, diagnosing support, or showing geographic scope. Decide whether a figure is better than
a table or sentence.

### 2. Inspect the underlying quantity

Trace plotted values to source data, transformations, samples, models, and interval calculations.
Understand the scale, reference category, weighting, smoothing, binning, bandwidth, aggregation, and
missingness before styling. Recompute a clean plotted-data object when package defaults hide these
choices.

### 3. Explore alternative views

Try the simplest credible encodings and compare them. Use raw-data views, small multiples, direct
labels, distributional displays, meaningful predictions, or coefficient intervals according to the
research question. Let unexpected visual patterns prompt checks of coding, measurement, composition,
or theory.

### 4. Build the figure

Use the project's existing toolchain. R and ggplot2 are preferred when the project uses R, but no
particular plotting library is an epistemic requirement. Keep the final plotted quantities and choices
explicit in code. Prefer vector output for line and text graphics and appropriate raster formats for
raster-native content.

### 5. Audit visual integrity

Check:

- axes, units, baselines, scales, transformations, and truncation;
- sample, groups, reference periods, omitted categories, and event-time composition;
- uncertainty level and what the interval represents;
- smoothing, binning, bandwidth, weighting, and model-based predictions;
- whether color, shape, line type, labels, and panels preserve comparisons accessibly;
- legibility in the actual manuscript size and grayscale when relevant; and
- whether the title, caption, and note overstate the design.

Do not change samples, group definitions, scales, smoothing, or uncertainty merely to make the result
look stronger.

### 6. Interpret and revise

Write the figure interpretation note. If the visual exposes changing composition, poor overlap,
outliers, nonlinearity, unstable timing, measurement artifacts, or a weak comparison, revise the
analysis or claim. A polished figure that hides a research problem is a failure.

## Figure Families

- Raw trends and treatment timing.
- Event studies and dynamic effects.
- Coefficient, marginal-effect, and predicted-quantity plots.
- Distribution, balance, overlap, and missingness views.
- RD and binned-scatter displays with explicit construction choices.
- Maps when geography is substantively relevant.
- Heterogeneity, mechanisms, and uncertainty displays.
- Design and model diagnostics suitable for a main text or appendix.

## Criteria for judgment

- The figure answers one substantive question.
- All plotted quantities are traceable and correctly labeled.
- The visual form makes the key comparison easy and honest.
- Magnitude and uncertainty are readable in meaningful units.
- Style supports the evidence rather than imposing a mandatory house aesthetic.
- Captions describe the quantity and design without claiming more than the evidence.
- The figure can reveal problems and cause research revision.

## Sources on graphical practice

- Kieran Healy, *Data Visualization: A Practical Introduction*: https://socviz.co/
- Jonathan Kastellec, “Practical Advice for Producing Better Graphs”:
  https://jkastellec.scholar.princeton.edu/publications/practical-advice-producing-better-graphs
