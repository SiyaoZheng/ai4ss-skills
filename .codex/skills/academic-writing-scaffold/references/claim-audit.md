# Claim Audit

Use this reference to map evidence to claims and identify writing risks.

## Claim Ledger

| column | meaning |
|---|---|
| `claim_id` | Stable id |
| `claim_text_or_slot` | User claim or planned claim slot |
| `claim_type` | design_fact, estimate, diagnostic, literature_fact, interpretation, speculation |
| `target_inquiry` | Estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question the claim belongs to |
| `evidence_path` | Table, figure, source, note, or matrix row |
| `support_level` | strong, partial, weak, missing |
| `interpretation_boundary` | What this evidence can and cannot support |
| `diagnosed_limit` | Diagnosed design, data, source, inference, or reporting limit |
| `risk` | overclaim, missing citation, wrong estimand, causal language, unsupported mechanism, scale ambiguity |
| `author_action` | revise_target, cite, soften, delete, add_evidence, decide |
| `author_boundary` | scaffold_only, author_draft_audit, needs_author_decision |
| `artifact_kind` | scaffold_only, author_draft_audit, decision_prompt |

## Table-To-Claim Check

Before a result can be written by the author, confirm:

- Dependent variable.
- Target inquiry or estimand.
- Treatment or exposure.
- Preferred model column.
- Fixed effects and clustering.
- Sample and N.
- Unit and scale.
- Confidence interval or standard error.
- Whether the model supports causal language.
- Interpretation boundary from the design or methods review.

## Literature Claim Check

Before a literature claim can be used, confirm:

- Primary source is verified.
- Paper status is clear.
- Identification strategy is actually stated.
- Finding is not taken only from a secondary summary.
- The paper is relevant to the current project, not just keyword-adjacent.

## Risk Language

Flag, do not silently rewrite:

- "proves"
- "confirms"
- "substantially transforms"
- "the literature agrees"
- "causes" when design support is unclear
- "mechanism" when only correlation is shown
- "policy implication" when external validity is not discussed
