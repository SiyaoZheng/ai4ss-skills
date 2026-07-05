# Prompt Pack

Use these prompts as internal task frames. Do not copy them into the final paper.

## Produce A Main Figure

```text
Use $top-journal-figures to produce the strongest main-text ggplot2 figure from these verified outputs.

Inputs:
- AI4SS model: .ai4ss/research_model.aiss
- data/model artifact:
- R script or plotting file:
- target journal style:
- desired figure type if known:

Requirements:
- preserve real observed data provenance
- use practical R helpers when appropriate, but make the final figure a named ggplot2 object
- create or reuse one shared ggplot2 style profile and apply it to every final paper figure
- expose estimates, intervals, bins, bandwidths, marginal-effect grids, or projection data used by the figure
- export vector PDF or SVG under output/figures/ using explicit ggsave()
- write caption, source note, sample note, uncertainty note, and interpretation boundary
- update or draft .aiss artifact/check/decision declarations
- route unresolved method or data issues through next_skill_route
```

## Audit Existing Figures

```text
Use $top-journal-figures to audit existing paper figures for top social-science journal readiness.

Check:
- vector export status
- style profile id, style source path, style consistency status, and style exceptions
- source note and sample note
- uncertainty display
- black-and-white readability
- axis integrity
- caption-claim alignment
- script reproducibility
- named ggplot object and explicit ggsave() call
- helper-package defaults and whether they hide reference periods, binning, bandwidths, projection, or interval rules
- .aiss linkage and next_skill_route
```

## Repair A Figure After Review

```text
Use $top-journal-figures to repair the figure issue below without changing the underlying result.

Issue:
Affected figure:
Source script:
Model/data artifact:

Return:
- changed files
- validation commands
- Rscript --vanilla command used
- package helpers used and why
- style profile used and any repaired style drift
- caption/note updates
- remaining interpretation boundary
- next_skill_route
```
