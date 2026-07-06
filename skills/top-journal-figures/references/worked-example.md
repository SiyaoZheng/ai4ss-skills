# Worked Example

## Input

The project has a selected `.ai4ss/research_model.aiss`, a processed panel, and event-study estimates from a clean R script. The author wants a main-text ggplot2 figure for an AER-style empirical paper.

## Action

1. Confirm the event-study estimates trace to real observed data and the declared treatment timing.
2. Source or create `scripts/figure_style.R` and set `style_profile_id: ai4ss_journal_v1`.
3. Use `fixest`/`ggfixest` or `did` helper output only to recover the event-time estimates and intervals; rebuild the final paper figure as a named ggplot2 object.
4. Choose an event-study coefficient plot with point estimates and 95 percent confidence intervals using the shared point and interval geometry.
5. Use a common y-axis, a visible reference period, a zero line, and a treatment-period marker matching the shared style profile.
6. Export `output/figures/figure1_event_study.pdf` with an explicit `ggsave()` call using dimensions from the shared style profile.
7. Write a caption that states what is plotted and a note that states sample, estimator, fixed effects, clustering, and source.
8. Record style-consistency and visual-integrity status and route to `methods-reviewer` if pre-period patterns or estimator choice need review.

## Example Handoff

```text
figure_path: output/figures/figure1_event_study.pdf
figure_type: event-study coefficient plot
ggsave_call: ggsave("output/figures/figure1_event_study.pdf", plot = p_event_study, device = "pdf", width = 6.5, height = 4.0, units = "in")
style_profile_id: ai4ss_journal_v1
style_source_path: scripts/figure_style.R
style_consistency_status: passed
style_exceptions: none
source_note: Source: project processed panel built from the declared public data artifacts.
sample_note: Unit is neighborhood-year; sample excludes rows without verified treatment timing or outcome.
uncertainty_display: Points show coefficients; bars show 95 percent confidence intervals clustered at the neighborhood level.
helper_tools: fixest estimated the event-study model; final output was rebuilt as p_event_study with ggplot2 and saved by ggsave().
interpretation_boundary: The figure visualizes dynamic association under the declared event-study design; causal interpretation remains subject to methods-review diagnostics.
next_skill_route: methods-reviewer
```
