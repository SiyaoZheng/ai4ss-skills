# Worked Example

## Input

- `docs/study_design_brief.md`: Route R1, firm-year digital-government rollout route.
- `data/analysis/firm_city_patent_panel.csv`.
- Variable dictionary with firm, city, year, green patent count, and rollout year.

## First Loop

Output: feasibility table, not treatment effect.

Rows:

- number of cities with rollout year;
- firm-year observations by pre/post availability;
- missing firm-city linkage;
- rollout-year distribution;
- comparison-unit availability.

## Interpretation Boundary

This output can show whether a causal analysis is feasible. It cannot show that digital-government rollout affected patenting.

## Handoff

Send the manifest, script, feasibility table, and warnings to `methods-reviewer` only after the researcher confirms the causal route remains under consideration.
