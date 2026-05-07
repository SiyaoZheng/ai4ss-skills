## Paper Metadata
- **author**: ding

## Attributes
### ding.state_capacity
- **domain**: ordinal
- **values**: low, high
- **description**: logistical and political capacity of a bureaucratic unit to deliver on governance goals
- **source**: Ch.1, pp.25-35

### ding.public_scrutiny
- **domain**: ordinal
- **values**: low, high
- **description**: degree to which public is attuned to an issue and exerting pressure on the state
- **source**: Ch.1, pp.25-35

## Concepts
### ding.governance_mode
- **parents**: ding.state_capacity, ding.public_scrutiny
- **rule**: exhaustive_typology
- **description**: typology of state-bureaucratic behavior along two dimensions
- **source**: Ch.1, pp.35-36
- **elsst_label**: governance

| capacity | scrutiny | outcome | evidence | confidence |
|----------|----------|---------|----------|------------|
| low | low | inert | "when both are low, the state is inert" (p.35) | EXTRACTED |
| high | low | paternalistic | "high capacity, low scrutiny → paternalistic" (p.36) | EXTRACTED |
| low | high | performative | "low capacity + high scrutiny → performative" (p.7) | EXTRACTED |
| high | high | substantive | "ideal case: substantive governance" (p.36) | EXTRACTED |

### ding.performative_governance
- **parents**: ding.state_capacity, ding.public_scrutiny
- **rule**: definitional
- **description**: deployment of visual, verbal, and gestural symbols of good governance
- **source**: Introduction, p.7
- **operationalization**: ethnographic coding of bureaucratic action

| capacity | scrutiny | outcome | evidence | confidence |
|----------|----------|---------|----------|------------|
| low | high | 1 | "low state capacity and high public scrutiny... performative governance" (p.7) | EXTRACTED |

### ding.low_capacity_high_scrutiny
- **parents**: ding.state_capacity, ding.public_scrutiny
- **rule**: definitional
- **description**: under-resourced yet under intense public pressure
- **source**: Ch.1, pp.35-36

| capacity | scrutiny | outcome | evidence | confidence |
|----------|----------|---------|----------|------------|
| low | high | 1 | "low state capacity and high public scrutiny" (p.35) | EXTRACTED |

## Causal Relations
### ding.lc_hs_to_performative
- **source**: ding.low_capacity_high_scrutiny
- **target**: ding.performative_governance
- **direction**: positive
- **condition**: none
- **mechanism**: beleaguered bureaucracy
- **commensurability**: weak
- **evidence**: 5-month participant observation at Lakeville EPB
- **confidence**: EXTRACTED

## Edges
### broader: governance_mode → performative_governance
- **relation**: broader
- **source**: ding.governance_mode
- **target**: ding.performative_governance
- **confidence**: EXTRACTED
- **source**: typology structure, Ch.1

## Bridges
### ding.measurement_pg
- **type**: measurement
- **concept**: ding.performative_governance
- **method**: participant_observation
- **validity**: key observable implications: night inspections, dress behavior, emotional management
- **commensurability**: strong

### ding.causal_bridge_1
- **type**: causal
- **implication**: ding.lc_hs_to_performative
- **estimand**: none
- **commensurability**: weak
- **note**: ethnographic evidence, no quantitative causal identification

## Model
### ding.performative_state
- **attributes**: ding.state_capacity, ding.public_scrutiny
- **concepts**: ding.governance_mode, ding.low_capacity_high_scrutiny, ding.performative_governance
- **causal**: ding.lc_hs_to_performative
- **bridges**: ding.measurement_pg, ding.causal_bridge_1
