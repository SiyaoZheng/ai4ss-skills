---
name: top-journal-figures
description: >
  R/ggplot2-first top social-science journal figure skill for producing and
  auditing AER, QJE, JPE, APSR, and adjacent publication-grade empirical figures
  from verified social-science outputs. Use for event-study plots, coefficient
  plots, binscatters, RD plots, treatment/control trends, distribution figures,
  maps, mechanism panels, figure captions, source notes, vector exports, and
  visual-integrity checks. Use practical R helpers such as fixest/ggfixest,
  did, marginaleffects, modelsummary, broom, cregg, binsreg, rdrobust, sf,
  patchwork, ggrepel, ggdist, viridis, colorspace, svglite, or ragg when they
  fit the existing project, but make final paper figures explicit ggplot2
  artifacts with a mandatory shared figure style profile. Do not use for dashboards, slide decks, generic
  illustration, or exploratory charts that are not ready to become paper
  figures.
---

# Top Journal Figures

Produce ggplot2 paper figures that can survive top social-science journal scrutiny. The skill turns checked analysis outputs into publication-grade visual evidence, not decorative charts.

## Scholar Workbench

This skill answers: "Which figures belong in the paper, and are they honest enough for a top journal?" Its value is converting model outputs, diagnostics, and descriptive summaries into traceable figures with source notes, uncertainty, and interpretation boundaries.

## Core Rule

A paper figure is a statistical argument artifact. It must preserve the target inquiry, sample, estimand or quantity, uncertainty display, source artifact, code path, and interpretation boundary. For publication-facing social-science figures, the only final plotting carrier is R/ggplot2. Helper packages may estimate, tidy, label, compose, or export, but the final manuscript figure must be a named ggplot2 object saved from R by explicit code. All paper figures in the same manuscript must share one explicit style profile: theme, typography, dimensions, geoms, uncertainty display, scales, color and non-color encodings, legends, panels, annotations, caption/note conventions, and export devices. Never change smoothing, samples, scales, labels, group definitions, uncertainty display, or style exceptions for appearance without recording the change as an author-visible decision.

## Full-Auto Harness Contract

When invoked by an automatic research harness, this skill must not pause for taste choices. It should choose the strongest conservative top-journal figure form and a single conservative style profile for the available evidence, create or repair R/ggplot2 code, export vector files when possible, write captions and notes, and route unresolved method or data problems to the owning skill. It must not invent data, estimates, examples, or visual evidence.

## AI4SS Runtime Gate

Do not build top-journal figures from disconnected files or memory in a research-factory project. Locate `.ai4ss/research_model.aiss`, the selected route, MIDA declarations, checked data artifacts, analysis artifacts, methods diagnostics, and report-boundary declarations before treating a figure as publication-facing.

Figure specifications and figure artifacts must be represented or referenced by `.aiss` `artifact`, `derive`, `observation`, bounded `claim`, visual-integrity `check`, or author `decision` declarations. A PDF, SVG, PNG, or TeX include file is an output artifact, not workflow state.

## Workspace Contract

Follow `docs/research_workspace_contract.md`. Durable workflow state belongs in
`.ai4ss/research_model.aiss`; generated figure files belong under
`output/figures/`; logs belong under `output/logs/`; paper integration happens
through `make all` or the project Makefile path.

## .aiss State Machine

When `.ai4ss/research_model.aiss` exists, run
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` before deciding
the next route. When this skill starts, completes, fails, or observes a
watchdog heartbeat in an automatic harness, record that runtime fact as an
`.aiss` `event` declaration or return a deterministic
`aiss.py transition --event ...` fragment for merge. Events do not replace
semantic updates: if the skill resolves a repair/check status, update the
relevant `route`, `mida`, `decision`, `check`, `artifact`, or claim-support
declaration too.

## Methodology Foundation

This skill sits between the MIDA `Answer strategy`, `Diagnose`, and `Report` layers. It does not choose the final model or claim; it renders declared outputs so the answer strategy, uncertainty, diagnostics, and report boundary are inspectable.

When a figure references a concept, causal implication, bridge, estimate, model, or descriptive quantity, it must preserve relevant `.aiss` ids and `ai4ss_check_status`.

## Workflow Contract

- Upstream inputs: `.ai4ss/research_model.aiss`, analysis scripts, model outputs, tables, diagnostics, data artifacts, row/source provenance, methods-review findings, target journal hints, or existing figures.
- Produces: figure specs, reusable R/ggplot2 plotting code, a shared figure style profile, vector-first figure exports, raster fallbacks when needed, captions, source notes, visual-integrity checks, style-consistency checks, paper include hints, and `.aiss` figure `artifact`, `derive`, `observation`, bounded `claim`, `check`, or `decision` declarations.
- Handoff fields: `route_id`, `target_inquiry`, `design_source`, `data_source`, `analysis_artifact`, `figure_spec`, `figure_path`, `figure_type`, `source_artifact`, `source_note`, `caption`, `sample_note`, `uncertainty_display`, `helper_tools_used`, `helper_tool_transparency_status`, `style_profile_id`, `style_source_path`, `style_consistency_status`, `style_exceptions`, `ggplot_object`, `ggsave_call`, `visual_integrity_status`, `black_white_status`, `vector_export_status`, `analysis_code_transparency_status`, `computational_reproducibility_status`, `replication_package_status`, `interpretation_boundary`, `ai4ss_model_path`, `model_id`, `concept_id`, `causal_id`, `bridge_id`, `ai4ss_check_status`, `next_skill_route`.
- Downstream routes: `methods-reviewer`, `academic-writing-scaffold`, `research-slides-builder`, `research-analysis-runner`, `research-data-builder`, `public-data-sources`, or `none`.

## Routing Boundaries

Use this skill for paper figures after real observed data and analysis outputs exist or can be repaired. Use `research-analysis-runner` when estimates or figure data still need to be computed. Use `methods-reviewer` when the figure exposes identification, inference, sample, or overclaim risk. Use `latex-tables` for tables. Use `research-slides-builder` for presentation decks. Do not use this skill for dashboards, infographic landing pages, or unsupported visual storytelling.

## Workflow

```text
Step -1: Check figure eligibility
-> Read AGENTS.md, `.ai4ss/research_model.aiss`, analysis scripts, model outputs, logs, and existing figures.
-> Confirm the figure traces to real observed public or authorized data and a declared analysis or descriptive quantity.
-> If estimates, figure data, or provenance are missing, repair through research-analysis-runner, research-data-builder, or public-data-sources.

Step 0: Choose the figure form
-> Match the evidence to a top-journal figure archetype: event study, coefficient plot, RD plot, binscatter, trend comparison, distribution, map, mechanism panel, or diagnostic panel.
-> Prefer the simplest figure that answers one inquiry.
-> Select practical helpers only for their substantive role: model tidying, design-specific estimands, interval extraction, panel composition, label collision repair, uncertainty display, accessibility, or device export.
-> Select or create the manuscript's shared style profile before final plotting. If no project style exists, create a conservative ggplot2 style file and use it for every final paper figure.

Step 1: Produce or repair code
-> Generate or edit reusable R/ggplot2 plotting code.
-> Source the shared style profile instead of copying ad hoc theme, scale, size, font, legend, or export settings into each figure.
-> If using a helper plot from fixest/ggfixest, did, marginaleffects, modelsummary, cregg, binsreg, rdrobust, or similar packages, inspect the returned object or extracted data and rebuild/wrap the final figure so all plotted quantities and notes are declared.
-> Save with `ggsave()` to PDF or SVG where possible, with fixed width, height, units, and device when needed; add PNG/TIFF only for preview or raster-only content.
-> Preserve deterministic data filters, seeds, model objects, and axis choices in code.

Step 2: Audit visual integrity
-> Check labels, units, confidence intervals, sample notes, source notes, black-and-white readability, colorblind safety, panel consistency, axis scales, and whether captions match the data.
-> Check style consistency across all final paper figures: dimensions, base theme, typography, line widths, point sizes, interval geoms, palette, linetype/shape maps, legends, facet strips, panel tags, margins, axis breaks, note style, output device, and filename pattern.
-> Record figure checks or decisions in `.aiss`.

Step 3: Hand off
-> Return figure paths, caption/note text, validation commands, `.aiss` ids touched, unresolved risks, and next_skill_route.
```

## Default Outputs

- Updated `.ai4ss/research_model.aiss` or deterministic `.aiss` fragment with figure artifacts, style-consistency checks, visual-integrity checks, and author-visible decisions.
- Shared R/ggplot2 style profile, usually `scripts/figure_style.R` or an existing project style file.
- R/ggplot2 plotting script changes or new plotting scripts that source the style profile.
- Publication-facing figure files under `output/figures/`, preferably vector PDF or SVG.
- Caption and source-note text suitable for paper integration.
- A concise audit of style consistency, helper-tool transparency, black-and-white readability, uncertainty display, source/provenance, sample note, and interpretation boundary.

## Script Utilities

- Run project-specific plotting scripts from a clean process after edits.
- Prefer `Rscript --vanilla` for durable figure generation and explicit `ggsave()` calls for final files.
- Prefer a project-level style file such as `scripts/figure_style.R` defining `theme_ai4ss_figure()`, named palettes, shape/linetype maps, geometry constants, column dimensions, and export helpers. Reuse an existing house style if the project already has one.
- Run `scripts/validate_ai4ss_model.py .ai4ss/research_model.aiss` when figure declarations are added or changed.
- Run project render or paper build commands to verify that the figure appears in the draft when integration is requested.

## Reference Files

| File | Content | Read when |
|---|---|---|
| [figure-workflow.md](references/figure-workflow.md) | Figure archetypes, evidence mapping, and production sequence | Producing or repairing a paper figure |
| [style-gates.md](references/style-gates.md) | Top-journal visual integrity gates and source-note rules | Auditing figures for AER/QJE/JPE/APSR-style use |
| [style-contract.md](references/style-contract.md) | Mandatory cross-figure style profile elements and consistency rules | Creating or auditing multiple manuscript figures |
| [community-practice.md](references/community-practice.md) | Economics and political-science ggplot2 packages, blogs, and replication practices | Choosing an implementation pattern or avoiding weak defaults |
| [prompt-pack.md](references/prompt-pack.md) | Copy-ready prompts for figure production and audit handoff | Turning analysis outputs into a figure task |
| [worked-example.md](references/worked-example.md) | Example event-study figure handoff | Teaching or demonstrating the skill |
