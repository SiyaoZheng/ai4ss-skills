## Paper Metadata
- **author**: demo

## Attributes
### demo.platform_exposure
- **domain**: binary
- **values**: unexposed, exposed
- **description**: whether a firm-year is exposed to a city digital-government platform rollout
- **source**: literature_matrix row smith_2024_city_ai

### demo.green_patenting
- **domain**: ordinal
- **values**: low, high
- **description**: observed green patenting intensity in a firm-year
- **source**: literature_matrix row smith_2024_city_ai

## Concepts
### demo.exposed_unit
- **parents**: demo.platform_exposure
- **rule**: definitional
- **description**: firm-year observation exposed to platform rollout
- **source**: literature_matrix row smith_2024_city_ai
- **operationalization**: city-year rollout status linked to firm-year panel

| exposure | outcome | evidence | confidence |
|----------|---------|----------|------------|
| unexposed | 0 | "non-rollout observations are not exposed" | EXTRACTED |
| exposed | 1 | "pilot designation defines exposed observations" | EXTRACTED |

### demo.high_innovation
- **parents**: demo.green_patenting
- **rule**: threshold
- **description**: high green patenting relative to the analysis scale
- **source**: literature_matrix row smith_2024_city_ai
- **operationalization**: green patent count by firm-year

| patenting | outcome | evidence | confidence |
|-----------|---------|----------|------------|
| low | 0 | "lower patent counts fall below the high-innovation threshold" | INFERRED |
| high | 1 | "patent count is the outcome measure" | EXTRACTED |

## Causal Relations
### demo.exposure_to_innovation
- **source**: demo.exposed_unit
- **target**: demo.high_innovation
- **direction**: positive
- **condition**: none
- **mechanism**: reduced administrative frictions
- **textual_support**: INFERRED

## Bridges
### demo.measurement_exposure
- **type**: measurement
- **concept**: demo.exposed_unit
- **method**: city_rollout_linked_panel
- **validity**: requires audited city-year linkage and timing checks
- **commensurability**: weak

### demo.causal_bridge_exposure
- **type**: causal
- **implication**: demo.exposure_to_innovation
- **estimand**: platform_exposure_effect_on_green_patents
- **commensurability**: weak
- **note**: literature row supports the design route but does not certify identification

## Model
### demo.platform_innovation
- **attributes**: demo.platform_exposure, demo.green_patenting
- **concepts**: demo.exposed_unit, demo.high_innovation
- **causal**: demo.exposure_to_innovation
- **bridges**: demo.measurement_exposure, demo.causal_bridge_exposure
