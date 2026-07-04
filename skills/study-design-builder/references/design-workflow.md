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

## Theory Mapping From Literature

When the input includes `literature_theory_synthesis.csv`, consume it as a
theory-mapping handoff rather than as prose. If the handoff also includes
`theory_rival_map.csv`, `theory_scope_map.csv`, and `theory_evidence.md`, treat
the directory as a full theory workbench and run or require:

```bash
python3 scripts/validate_theory_workbench.py <workbench-dir>
```

Use `literature_theory_synthesis.csv` for candidate concepts, mechanisms,
observable implications, measurement links, and `proposed_aiss_object` values. Use
`theory_rival_map.csv` to diagnose rival explanations, missing discriminating
observations, and design risks. Use `theory_scope_map.csv` to preserve
who/where/when scope, boundary failure modes, and author decisions. Use
`theory_evidence.md` only through the existing `dsl/scripts/compile_evidence.py`
path; do not create a new compiler or declaration kind.

Only validated objects with `status=ready_for_aiss` may update or propose
existing `.aiss` model-layer declarations: `concept`, `claim`, `relation`,
`causal`, `bridge`, and `model`. `evidence_strength=unverified`, unresolved
rival choice, unresolved scope choice, novelty, theoretical contribution, and
mechanism strength must stay out of model facts. Record those items in
`design_decision_register.csv` and mirror them as author-owned `.aiss`
`decision` declarations.

Record the sidecar path in the affected `study_design_declaration.csv`
`evidence_source` cells. Do not add new declaration columns and do not create a
new DSL declaration kind. Rows with unresolved novelty, mechanism strength,
scope conditions, or rival-explanation choices should create or preserve
author-owned `decision` declarations instead of becoming final theory claims.

Recommended sequence:

1. Validate `literature_theory_synthesis.csv` against the source matrix.
2. Validate the full workbench when rival/scope/evidence files are present.
3. Compile `theory_evidence.md` through `dsl/scripts/compile_evidence.py`.
4. Run `scripts/validate_ai4ss_model.py` on the resulting `.aiss`.
5. Update `study_design_declaration.csv` `evidence_source` values and
   `design_decision_register.csv` decision rows.

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
