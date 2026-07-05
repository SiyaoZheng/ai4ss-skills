# Literature To Theory Synthesis

Use this reference when verified literature rows need to inform theory mapping,
AI-disclosed literature-review working prose, or theoretical contribution checks.

This is the literature-side entrypoint for the shared theory engine. It is not a
new skill, a new DSL, or a theory chapter generator. It produces auditable
theory workbench inputs that downstream skills can validate, review, and carry
forward through checked `.aiss` declarations.

## Theory Workbench Package

Start with `.aiss theory synthesis declarations` only after `.aiss literature evidence declarations`
exists. For a complete theory workbench handoff, add:

- `.aiss rival-check declarations` for competing explanations and discriminating
  observations.
- `.aiss scope-check declarations` for who/where/when scope, boundary failure modes, and
  assumptions to disclose.
- checked `.aiss` source, span, claim, relation, check, and decision
  declarations for model-affecting evidence.

Do not create a separate concept-extraction table. Candidate graph structure is
derived from `.aiss theory synthesis declarations`, the rival/scope .aiss projections, and
the checked `.aiss` output.

## Literature Theory Synthesis Declarations

`.aiss theory synthesis declarations` is a theory handoff: it groups verified source
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
| `source_paper_ids` | Semicolon-separated `.aiss literature evidence declarations` `paper_id` values |
| `source_status_summary` | Verification summary, including verified_primary or verified_local when model handoff is proposed |
| `theory_candidate` | Candidate concept, mechanism, boundary, rival, or implication |
| `rival_or_boundary` | Rival explanation, boundary condition, or `not_applicable:<reason>` |
| `observable_implication` | What should be visible in data, sources, coding, or design diagnostics if the candidate matters |
| `proposed_aiss_object` | Proposed `.aiss` object such as `concept:project.x`, `causal:project.y`, `bridge:project.z`, or `not_applicable:<reason>` |
| `evidence_strength` | strong, mixed, thin, conflicting, or unverified |
| `assumptions_to_disclose` | Assumption before model or prose use |
| `next_skill_route` | study-design-builder, academic-writing-scaffold, or methods-reviewer |

For `synthesis_type=mechanism`, write `theory_candidate` as four inspectable
parts:

```text
actor: <who acts>; action: <what changes>;
mediating_condition: <condition that carries the mechanism>;
outcome_link: <how it reaches the declared outcome or construct>
```

Mechanisms without these parts are not ready for a model handoff.

## Rival Check Declarations

`.aiss rival-check declarations` preserves rival explanations without turning them into
final theory prose or new schema. Required columns come from the shared
`theory_rival_map` .aiss projection contract:

| column | meaning |
|---|---|
| `route_id` | Route/design id this rival audit serves |
| `design_source` | Path to the design brief or MIDA declaration |
| `target_inquiry` | Declared inquiry, estimand, construct, or synthesis question |
| `rival_id` | Stable short id |
| `target_synthesis_id` | Matching `synthesis_id` from `.aiss theory synthesis declarations` |
| `target_aiss_object` | Target proposed object or `not_applicable:<reason>` |
| `rival_claim` | Competing explanation or concept framing |
| `explains_well` | What the rival can explain |
| `explains_poorly` | What the rival cannot explain |
| `discriminating_observation` | Observable implication that could distinguish candidate from rival |
| `evidence_needed` | Source, data, diagnostic, or coding evidence needed |
| `status` | ready_for_aiss, needs_methods_review, needs_source_expansion, needs_design_repair, or not_applicable |
| `next_skill_route` | methods-reviewer, study-design-builder, academic-writing-scaffold, or literature-matrix |

Rival rows diagnose theory risk. They normally route to `methods-reviewer` or
source/design repair; they must not be treated as final theory claims.

## Scope Check Declarations

`.aiss scope-check declarations` records scope conditions before a scope or
contribution claim is marked direct-submission ready. Required columns come from the shared
`theory_scope_map` .aiss projection contract:

| column | meaning |
|---|---|
| `route_id` | Route/design id this scope decision serves |
| `design_source` | Path to the design brief or MIDA declaration |
| `target_inquiry` | Declared inquiry, estimand, construct, or synthesis question |
| `scope_id` | Stable short id |
| `target_synthesis_id` | Matching `synthesis_id` from `.aiss theory synthesis declarations` |
| `target_aiss_object` | Target proposed object or `not_applicable:<reason>` |
| `who_where_when` | Population, setting, time, source base, or case boundary |
| `scope_logic` | Why the candidate should be bounded there |
| `boundary_failure_mode` | How the claim fails outside the scope |
| `observable_implication` | What the scope implies for data, source, or review diagnostics |
| `source_ids` | Semicolon-separated source ids or `not_applicable:<reason>` |
| `assumptions_to_disclose` | Scope assumption before prose or broad claim use |
| `status` | ready_for_aiss, needs_methods_review, needs_source_expansion, needs_design_repair, or not_applicable |
| `next_skill_route` | methods-reviewer, study-design-builder, academic-writing-scaffold, or literature-matrix |

## Checked Evidence Declarations

When a validated theory workbench should update `.aiss`, write checked `paper`,
`source`, `span`, `claim`, `relation`, `concept`, `causal`, `bridge`, `check`,
and `decision` declarations directly into the research object.

Only rows that pass `scripts/validate_ai4ss_model.py` and are suitable for
`status=ready_for_aiss` may become model-layer declarations. Unresolved novelty,
theoretical contribution, scope choice, rival choice, and mechanism strength
must become `.aiss` `decision` declarations or assumptions to disclose.

## Rules

- Only `verified_primary` or `verified_local` literature rows may support
  `proposed_aiss_object`.
- `evidence_strength=unverified` must route to source expansion and must set
  `proposed_aiss_object=not_applicable:<reason>`.
- Every row must preserve at least one `source_paper_ids` value from the
  `.aiss` literature evidence declarations.
- Every theory candidate needs either a rival/boundary statement or a concrete
  `not_applicable:<reason>`.
- A model-linked row must route to `study-design-builder`; the design builder
  owns creation or update of `.aiss` `concept`, `claim`, `relation`, `causal`,
  `bridge`, and `model` declarations.
- Rival explanations can route to `methods-reviewer` when they mainly diagnose
  design risk, or to `study-design-builder` when the framing changes the design.
- Every nontrivial candidate needs a rival row or a concrete
  `not_applicable:<reason>`.
- Every rival row needs a discriminating observable implication.
- Every scope row needs who/where/when, boundary failure mode, observable
  implication, and assumptions to disclose.
- Resolve novelty, theoretical contribution, mechanism strength, scope choice,
  and rival choice to the strongest defensible claim boundary; preserve the
  uncertainty as evidence needs and draft-PDF limitations.

## Validation

Run these checks before handoff:

```bash
python3 scripts/validate_ai4ss_model.py .ai4ss/research_model.aiss
```

## Boundary

This `.aiss` projection should not be marked direct-submission ready by itself.
It records candidate theoretical objects, visible support, rival or boundary
concerns, observable implications, assumptions to disclose, and disclosure status for
any AI-assisted working prose.
