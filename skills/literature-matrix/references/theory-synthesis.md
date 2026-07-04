# Literature To Theory Synthesis

Use this reference when verified literature rows need to inform theory mapping
without writing literature-review prose or claiming theoretical contribution.

This is the literature-side entrypoint for the shared theory engine. It is not a
new skill, a new DSL, or a theory chapter generator. It produces auditable
theory workbench inputs that downstream skills can validate, review, compile
through the existing `compile_evidence.py` path, and hand back to the author.

## Theory Workbench Package

Start with `literature_theory_synthesis.csv` only after `literature_matrix.csv`
exists. For a complete theory workbench handoff, add:

- `theory_rival_map.csv` for competing explanations and discriminating
  observations.
- `theory_scope_map.csv` for who/where/when scope, boundary failure modes, and
  author decisions.
- `theory_evidence.md` as structured evidence markdown consumable by the
  existing `dsl/scripts/compile_evidence.py` compiler.

Do not create a separate concept-extraction table. Candidate graph structure is
derived from `literature_theory_synthesis.csv`, the rival/scope sidecars, and
the compiled `.aiss` output.

## Literature Theory Synthesis Sidecar

`literature_theory_synthesis.csv` is a theory handoff: it groups verified source
rows into candidate concepts, mechanisms, boundary conditions, rival
explanations, observable implications, measurement links, or scope conditions.

Required columns:

| column | meaning |
|---|---|
| `route_id` | Route/design id this theory synthesis serves |
| `design_source` | Path to the design brief or MIDA declaration |
| `target_inquiry` | Declared inquiry, estimand, construct, or synthesis question |
| `synthesis_id` | Stable short id |
| `synthesis_type` | concept_cluster, mechanism, boundary_condition, rival_explanation, observable_implication, measurement_link, scope_condition |
| `source_paper_ids` | Semicolon-separated `literature_matrix.csv` `paper_id` values |
| `source_status_summary` | Verification summary, including verified_primary or verified_local when model handoff is proposed |
| `theory_candidate` | Candidate concept, mechanism, boundary, rival, or implication |
| `rival_or_boundary` | Rival explanation, boundary condition, or `not_applicable:<reason>` |
| `observable_implication` | What should be visible in data, sources, coding, or design diagnostics if the candidate matters |
| `proposed_aiss_object` | Proposed `.aiss` object such as `concept:project.x`, `causal:project.y`, `bridge:project.z`, or `not_applicable:<reason>` |
| `evidence_strength` | strong, mixed, thin, conflicting, or unverified |
| `author_decision_needed` | Researcher decision before model or prose use |
| `next_skill_route` | study-design-builder, academic-writing-scaffold, methods-reviewer, or ask_author |

For `synthesis_type=mechanism`, write `theory_candidate` as four inspectable
parts:

```text
actor: <who acts>; action: <what changes>;
mediating_condition: <condition that carries the mechanism>;
outcome_link: <how it reaches the declared outcome or construct>
```

Mechanisms without these parts are not ready for a model handoff.

## Rival Map Sidecar

`theory_rival_map.csv` preserves rival explanations without turning them into
final theory prose or new schema. Required columns come from the shared
`theory_rival_map` sidecar contract:

| column | meaning |
|---|---|
| `route_id` | Route/design id this rival audit serves |
| `design_source` | Path to the design brief or MIDA declaration |
| `target_inquiry` | Declared inquiry, estimand, construct, or synthesis question |
| `rival_id` | Stable short id |
| `target_synthesis_id` | Matching `synthesis_id` from `literature_theory_synthesis.csv` |
| `target_aiss_object` | Target proposed object or `not_applicable:<reason>` |
| `rival_claim` | Competing explanation or concept framing |
| `explains_well` | What the rival can explain |
| `explains_poorly` | What the rival cannot explain |
| `discriminating_observation` | Observable implication that could distinguish candidate from rival |
| `evidence_needed` | Source, data, diagnostic, or coding evidence needed |
| `status` | ready_for_aiss, needs_author_decision, needs_methods_review, blocked, or not_applicable |
| `next_skill_route` | methods-reviewer, study-design-builder, academic-writing-scaffold, or ask_author |

Rival rows diagnose theory risk. They normally route to `methods-reviewer` or
`ask_author`; they must not be treated as final theory claims.

## Scope Map Sidecar

`theory_scope_map.csv` records scope conditions before the author writes a
scope or contribution claim. Required columns come from the shared
`theory_scope_map` sidecar contract:

| column | meaning |
|---|---|
| `route_id` | Route/design id this scope decision serves |
| `design_source` | Path to the design brief or MIDA declaration |
| `target_inquiry` | Declared inquiry, estimand, construct, or synthesis question |
| `scope_id` | Stable short id |
| `target_synthesis_id` | Matching `synthesis_id` from `literature_theory_synthesis.csv` |
| `target_aiss_object` | Target proposed object or `not_applicable:<reason>` |
| `who_where_when` | Population, setting, time, source base, or case boundary |
| `scope_logic` | Why the candidate should be bounded there |
| `boundary_failure_mode` | How the claim fails outside the scope |
| `observable_implication` | What the scope implies for data, source, or review diagnostics |
| `source_ids` | Semicolon-separated source ids or `not_applicable:<reason>` |
| `author_decision_needed` | Researcher choice before prose or broad claim use |
| `status` | ready_for_aiss, needs_author_decision, needs_methods_review, blocked, or not_applicable |
| `next_skill_route` | methods-reviewer, study-design-builder, academic-writing-scaffold, or ask_author |

## Structured Evidence Markdown

When a validated theory workbench should update `.aiss`, write
`theory_evidence.md` using the existing structured evidence headings consumed by
`dsl/scripts/compile_evidence.py`: `Paper Metadata`, optional `Routes`, optional
`MIDA`, optional `Decisions`, `Attributes`, `Concepts`, `Causal Relations`,
`Bridges`, and `Model`.

Only rows that pass `scripts/validate_theory_workbench.py` and are suitable for
`status=ready_for_aiss` may become model-layer declarations. Unresolved novelty,
theoretical contribution, scope choice, rival choice, and mechanism strength
must become `.aiss` `decision` declarations or author workbench questions.

## Rules

- Only `verified_primary` or `verified_local` literature rows may support
  `proposed_aiss_object`.
- `evidence_strength=unverified` must route to `ask_author` and must set
  `proposed_aiss_object=not_applicable:<reason>`.
- Every row must preserve at least one `source_paper_ids` value from the
  literature matrix.
- Every theory candidate needs either a rival/boundary statement or a concrete
  `not_applicable:<reason>`.
- A model-linked row must route to `study-design-builder`; the design builder
  owns creation or update of `.aiss` `concept`, `claim`, `relation`, `causal`,
  `bridge`, and `model` declarations.
- Rival explanations can route to `methods-reviewer` when they mainly diagnose
  design risk, or to `ask_author` when the researcher must choose the framing.
- Every nontrivial candidate needs a rival row or a concrete
  `not_applicable:<reason>`.
- Every rival row needs a discriminating observable implication.
- Every scope row needs who/where/when, boundary failure mode, observable
  implication, and author decision.
- Do not automatically resolve novelty, theoretical contribution, mechanism
  strength, scope choice, or rival choice.

## Validation

Run these checks before handoff:

```bash
python3 skills/literature-matrix/scripts/validate_literature_theory_synthesis.py docs/literature_theory_synthesis.csv --literature-matrix docs/literature_matrix.csv
python3 scripts/validate_theory_workbench.py docs/theory_workbench
python3 dsl/scripts/compile_evidence.py docs/theory_workbench/theory_evidence.md > docs/theory_workbench_output.aiss
python3 scripts/validate_ai4ss_model.py docs/theory_workbench_output.aiss
```

## Boundary

This sidecar is not a theory section and not a novelty claim. It records
candidate theoretical objects, visible support, rival or boundary concerns,
observable implications, and author decisions. The researcher owns theoretical
contribution, mechanism strength, and final prose.
