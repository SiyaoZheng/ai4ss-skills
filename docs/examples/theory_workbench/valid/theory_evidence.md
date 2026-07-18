## Paper Metadata
- **author**: theory

## Routes
### theory.route_r1
- **question**: What theoretical mechanism could connect digital-government platform exposure to firm green innovation?
- **status**: selected
- **study_type**: theory_mapping
- **unit_of_analysis**: firm-year / city-year
- **inquiry**: effect of city platform exposure on firm green patent count
- **data_strategy**: source-verified rollout records linked to firm innovation outcomes
- **answer_strategy**: theory workbench before analysis or manuscript prose
- **stop_reason**: required gate: mechanism strength and contribution before final prose
- **next_skill_route**: last_skill
- **candidate_concepts**: theory.exposed_unit, theory.high_innovation

## MIDA
### theory.mida_r1_model
- **route**: theory.route_r1
- **component**: model
- **text**: Platform exposure, innovation output, mechanism candidate, rival explanation, and scope condition are declared for theory workbench review.
- **status**: declared
- **concepts**: theory.exposed_unit, theory.high_innovation
- **causal**: theory.exposure_to_innovation
- **bridges**: theory.measurement_exposure, theory.causal_bridge_exposure
- **model**: theory.platform_innovation

## Decisions
### theory.decision_r1_theory_scope
- **route**: theory.route_r1
- **component**: model
- **decision**: Workflow must gate whether the mechanism is a framing hypothesis, tested implication, or broader theoretical contribution.
- **status**: needs_redesign
- **owner**: workflow
- **next_skill_route**: last_skill
- **causal**: theory.exposure_to_innovation

## Attributes
### theory.platform_exposure
- **domain**: binary
- **values**: absent, present
- **description**: whether a unit is exposed to a digital-government platform
- **source**: docs/examples/theory_workbench/valid/literature_theory_synthesis.csv#TS1

### theory.innovation_output
- **domain**: ordinal
- **values**: low, high
- **description**: observed green innovation output category
- **source**: docs/examples/theory_workbench/valid/literature_theory_synthesis.csv#TS2

## Concepts
### theory.exposed_unit
- **parents**: theory.platform_exposure
- **rule**: definitional
- **description**: Unit exposed to the platform in the declared and auditable rollout window.
- **source**: docs/examples/theory_workbench/valid/literature_theory_synthesis.csv#TS1
- **operationalization**: administrative rollout record linked to unit identifiers before outcome measurement

| exposure | outcome | evidence | confidence |
|----------|---------|----------|------------|
| absent   | 0       | no auditable rollout exposure before the outcome window | EXTRACTED |
| present  | 1       | auditable rollout exposure before the outcome window | EXTRACTED |

### theory.high_innovation
- **parents**: theory.innovation_output
- **rule**: definitional
- **description**: Unit with high observed green innovation output under the declared measurement rule.
- **source**: docs/examples/theory_workbench/valid/literature_theory_synthesis.csv#TS2
- **operationalization**: green patent count or validated innovation output category

| innovation | outcome | evidence | confidence |
|------------|---------|----------|------------|
| low        | 0       | low measured green innovation output | EXTRACTED |
| high       | 1       | high measured green innovation output | EXTRACTED |

## Causal Relations
### theory.exposure_to_innovation
- **source**: theory.exposed_unit
- **target**: theory.high_innovation
- **direction**: positive
- **condition**: none
- **mechanism**: city administrative agencies reduce approval and service friction after platform rollout, giving firms more capacity to pursue green innovation outputs
- **textual_support**: INFERRED

## Edges
### theory.edge_exposure_innovation
- **relation**: related
- **source**: theory.exposed_unit
- **target**: theory.high_innovation
- **confidence**: INFERRED
- **source**: docs/examples/theory_workbench/valid/theory_rival_map.csv#RV1

## Bridges
### theory.measurement_exposure
- **type**: measurement
- **concept**: theory.exposed_unit
- **method**: audited rollout date linked to unit identifiers
- **validity**: requires rollout dates and unit linkage before outcome measurement
- **commensurability**: weak
- **note**: scope and mechanism strength remain required gates

### theory.causal_bridge_exposure
- **type**: causal
- **implication**: theory.exposure_to_innovation
- **estimand**: none
- **commensurability**: weak
- **note**: rival baseline city capacity requires methods review before causal language

## Model
### theory.platform_innovation
- **attributes**: theory.platform_exposure, theory.innovation_output
- **concepts**: theory.exposed_unit, theory.high_innovation
- **causal**: theory.exposure_to_innovation
- **bridges**: theory.measurement_exposure, theory.causal_bridge_exposure
