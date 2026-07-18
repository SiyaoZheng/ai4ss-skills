# Factory Relay Deterministic Handoff Audit

This report checks whether `.aiss` remains the single workflow state across a multi-skill relay.

| case | expected | actual | score | primary error codes |
| --- | --- | --- | ---: | --- |
| `valid_relay` | pass | pass | 1.0000 | - |
| `missing_report_boundary` | fail | fail | 0.9314 | mida_incomplete, missing_report_boundary |
| `data_repair_misrouted` | fail | fail | 0.8778 | status_route_mismatch, data_repair_misrouted |
| `parallel_markdown_state` | fail | fail | 0.9600 | parallel_workflow_state |
| `selected_route_lacks_consumer` | fail | fail | 0.9600 | selected_route_has_no_downstream_consumer |
| `empirical_artifact_link_dropped` | fail | fail | 0.9750 | empirical_without_artifact |
| `mida_route_drift` | fail | fail | 0.9029 | AISS-REF-001, aiss_lint_failed, mida_incomplete, mida_route_mismatch |
| `synthetic_fallback_analysis` | fail | fail | 0.9600 | forbidden_fallback_analysis |

## Dimensions

- `handoff_preservation`: selected `route_decl_id`, seven MIDA rows, decision-route continuity, and valid `next_skill_route`.
- `downstream_consumability`: strict `.aiss` lint, usable downstream route, automation decisions, and model/check availability.
- `stage_ownership`: no sidecar workflow state and no direct-submission overclaim.
- `repair_routing_quality`: repair/check rows route to the owning skill, not to execution.
- `artifact_binding`: source/span/claim/check/artifact continuity and empirical artifact links.
- `forbidden_fallback_analysis`: synthetic, simulated, toy, placeholder, or demo analysis cannot substitute for real evidence.
