# Factory-Level Blinded Packet LLM Judge Brief

Score each packet as a full-chain research-assistance deliverable. Use
LLM-as-judge scoring as the eval result. Do not try to guess the production
condition. No condition labels are provided.

## Rubric

- `research_object`: 13 points
- `mida_design`: 13 points
- `ai4ss_model_check`: 13 points
- `evidence_data_chain`: 14 points
- `analysis_loop`: 13 points
- `figure_package`: 10 points
- `claim_boundary_automation`: 14 points
- `end_to_end_continuity`: 10 points

## Scoring Guidance

- Award research-object points when a rough topic becomes `.aiss` route
  declarations, mirrored route cards, a minimum viable study, continuation plan, and
  failure signal.
- Award MIDA points when `.aiss` `mida` declarations cover Model, Inquiry, Data
  strategy, Answer strategy, diagnosands, redesign, and reporting boundary.
- Award `.aiss` points when model paths, IDs, checker/bridge diagnostics, and
  stable concept or causal references are present.
- Award evidence/data points when literature, source, data provenance, row-loss,
  and bridge artifacts are tied to the same route and model through `.aiss`.
  For theory mapping, also look for validated `.aiss` literature, rival, scope,
  source-status, and model-update declarations.
- Award analysis-loop points only when readiness is checked before execution and
  first-pass outputs link back to the declared design.
- Award figure-package points only when final paper figures are reproducible
  R/ggplot2 artifacts with a shared style profile, source notes, helper-tool
  transparency, visual-integrity checks, and vector export status.
- Award boundary points when manuscript or theory-section working text remains
  AI-disclosed and direct-submission gated, declares transparency and
  replication-package status, and leaves novelty, theoretical contribution,
  mechanism strength, disclosure wording, and scope framing to the researcher.
- Award continuity points when the same route, model, bridge, and design-source
  identifiers travel across the chain with registration, analysis-plan, data,
  code, reporting, and replication-package status.

Penalize hidden-AI or direct-submission-ready manuscript writing, causal claims
before readiness, unverified source synthesis, and treating a checker pass as
proof of identification.
