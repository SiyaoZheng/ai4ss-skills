# Design Workflow

The design builder sits between starter and execution. It turns a provisional `.aiss` `route` into a selected route, seven `.aiss` `mida` declarations, a design brief, and model-layer declarations when needed.

## MIDA Design Brief

Use these headings:

```markdown
# Study Design Brief

## Route
route_id, working title, source starter packet, and rejected alternatives.

## Model
Population, unit of analysis, setting, time period, constructs, mechanism candidates, assumptions, and scope conditions.

## Inquiry
Causal estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question. For causal work, name target comparison, population, outcome, exposure/treatment, time window, and scale.

## Data Strategy
Sampling, source selection, measurement, extraction, linkage, missingness, permissions, and unavailable material.

## Answer Strategy
Estimator, coding rule, synthesis rule, diagnostic comparison, table/figure shell, or qualitative inference procedure.

## Diagnose
Bias, precision, power, measurement risk, source-status risk, row loss, reproducibility, and claim-support checks.

## Redesign
Smaller first loop, revised measure, added source, changed comparison, changed estimator, or abandon condition.

## Report Boundary
What the first output can and cannot support, and which claims remain author decisions.

## First Analysis Plan
The smallest table, figure, model, coding exercise, or source matrix needed next.

## Handoff
next_skill_route, inputs, outputs expected, validation command if available.
```

Mirror the brief in `study_design_declaration.csv` whenever the design will be reused by downstream skills. The CSV mirrors `.aiss` `mida` declarations and must preserve `mida_id`; it is not a second canonical design language. Mirror unresolved author choices in `design_decision_register.csv` with `decision_decl_id` values from `.aiss` `decision` declarations.

## Stop Rules

Stop before:

- claiming novelty;
- declaring identification credible;
- choosing a final estimand when the author has not approved it;
- running models without an analysis-ready dataset and a design source;
- writing final prose.

## Design Types

| design type | first design question |
|---|---|
| descriptive | What population, measure, and time window are being described? |
| causal | What comparison identifies the effect, and what assumption would make it credible? |
| prediction | What target and validation split prevent leakage? |
| text_analysis | What corpus and coding unit define the observation? |
| qualitative | What cases, source boundaries, and consent constraints apply? |
| mixed_methods | What quantitative pattern and qualitative material answer different parts of the question? |
| theory_mapping | What concept, mechanism, and observable implication are being mapped? |
