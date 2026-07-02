# Methodology Foundation Audit

Audit date: 2026-06-26

## Verdict

The methodology foundation is now strong enough for the workshop workflow, with one important boundary: it is a methodology-enforcing cross-skill scaffold, not a universal specialist-methods system.

The framework choice is defensible: `Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims` is a coherent research-design spine, and it is much stronger than a loose bundle of methods citations. The earlier weakness was implementation: the spine was visible in docs and every `SKILL.md`, but not consistently forced by canonical artifact schemas and validators. That gap has now been remediated by moving MIDA fields into sidecar schemas, validators, valid examples, and the cross-skill methodology validator.

Practical judgment:

| dimension | audit judgment |
|---|---|
| External framework | Strong |
| Cross-skill workflow | Strong |
| Skill-level methodology statements | Strong |
| Artifact schema enforcement | Strong for the workflow spine |
| Validator enforcement | Strong for schema-level MIDA preservation |
| Specialist method depth | Partial by design |
| Overall readiness | Methodology-hardened teaching workflow, not a complete specialist-methods research agent |

## Remediation Status

The audit findings below are retained because they record the failure mode. The implementation has been hardened as follows:

| original issue | status | concrete remediation |
|---|---|---|
| `study-design-builder` did not force a MIDA-shaped design brief | Remediated | Added `study_design_declaration.csv`, `declaration-schema.md`, `validate_study_design_declaration.py`, and valid examples requiring `model`, `inquiry`, `data_strategy`, `answer_strategy`, `diagnose`, `redesign`, and `report_boundary` rows |
| Validators could create false confidence by checking prose rather than schemas | Remediated | Upgraded `scripts/validate_methodology_foundations.py` to check skill-local schema references, validator scripts, and valid examples for required MIDA fields |
| Reporting and revision schemas lost declared methodology fields | Remediated | Added `target_inquiry`, `interpretation_boundary`, `diagnosed_limit`, `sample_or_scope`, `uncertainty_or_caveat`, `privacy_status`, and `mida_element_affected` to downstream schemas and validators |
| Route cards were useful but not true pre-declarations | Remediated | Added `model_scope`, `candidate_inquiry`, `possible_data_strategy`, and `possible_answer_strategy` to route-card schema, examples, and validator |
| Data and literature provenance were not always tethered to design | Remediated | Added `route_id`, `design_source`, and `target_inquiry` to data, literature, analysis, and methods sidecars where design tethering matters |
| Specialist methods remain incomplete | Watchlist | Kept DID delegated to `$did-expert`; other specialist methods should become new skills only when course cases require them |

## Evidence Checked

Local checks passed:

```bash
python3 scripts/validate_methodology_foundations.py docs/methodology_source_matrix.csv
python3 scripts/validate_skillpack_workflow.py
python3 scripts/validate_ai_use_ledger.py docs/ai_use_ledger.csv
```

All valid example sidecars for the nine local skills also passed their local validators.

External source check:

- DeclareDesign and `Research Design in the Social Sciences` use the MIDA vocabulary and declaration-diagnosis-redesign logic.
- The APSR article `Declaring and Diagnosing Research Designs` supports the idea that research designs can be declared and diagnosed rather than only narrated.

## Findings

### P1. The central design skill does not yet force a MIDA-shaped design brief

`docs/methodology_foundations.md` defines the required spine and required declaration fields, and `docs/methodology_source_matrix.csv` marks `study-design-builder` as the primary design declaration skill. But `study-design-builder`'s design brief template still uses generic headings: route, question, scope, constructs, evidence needs, candidate design, first analysis plan, risks, and handoff.

That template is reasonable, but it does not force the author or agent to explicitly declare:

- `Model`
- `Inquiry`
- `Data strategy`
- `Answer strategy`
- `Diagnose`
- `Redesign`
- `Report boundary`

The `design_decision_register.csv` schema is also generic decision tracking. It has `design_component`, `current_choice`, `status`, and routing fields, but no controlled MIDA component field and no explicit `inquiry`, `data_strategy`, `answer_strategy`, or `diagnosand` fields.

Impact: the most important skill can pass validation while producing a design object that is adjacent to MIDA but not formally declared in MIDA terms.

### P1. The validators can create false confidence

`scripts/validate_skillpack_workflow.py` checks whether each `SKILL.md` contains `## Methodology Foundation`, the word `MIDA`, and at least one framework component. That is useful for presence, but it does not check whether the corresponding artifact schema carries the framework.

`scripts/validate_methodology_foundations.py` checks the matrix row text, not the actual skill schemas. A row can pass because it contains `data_strategy` or `answer_strategy` in prose, while the skill's CSV schema never requires those fields.

Impact: current PASS means "the documentation names the framework", not "the workflow output is methodologically declared."

### P1. Reporting and revision schemas do not preserve all declared methodology fields

The `academic-writing-scaffold` methodology section says it preserves inquiry or estimand, evidence source, support level, uncertainty, diagnosed limits, and author decisions. Its `claim_ledger.csv` schema does not require `target_inquiry`, `interpretation_boundary`, `uncertainty`, or `diagnosed_limit`.

The `research-slides-builder` methodology section says slide claims should preserve inquiry or estimand, sample/scope, source artifact, uncertainty/caveat, privacy status, and interpretation boundary. Its `slide_map.csv` schema only requires `slide_id`, `role`, `claim`, `source_artifact`, `visual`, `risk`, and `action`.

The `reviewer-response` methodology section says every reviewer request should map to the affected MIDA element. Its `revision_matrix.csv` schema does not require a `mida_element_affected` column.

Impact: downstream reporting skills may keep source links while losing the design object they are supposed to report or redesign.

### P2. Route cards are useful but not yet true pre-declarations

`research-starter` route cards currently require question, phenomenon, study type, unit, materials, first action, failure signal, feasibility, stop reason, decision, and next route. This is a good first-loop structure.

But the schema does not require provisional `model_scope`, `candidate_inquiry`, `possible_data_strategy`, or `possible_answer_strategy`, even though the methodology matrix says route discovery should sketch those components.

Impact: the starter can create feasible route cards without giving the design builder enough structured material to declare MIDA cleanly.

### P2. Data and literature provenance are strong, but design tethering is uneven

`research-data-builder` has strong sample-flow, merge-audit, and variable-provenance schemas. `literature-matrix` has a strong candidate-discovery and source-verification package.

The weakness is not provenance. The weakness is that these outputs are not always forced to retain their relation to the current `Inquiry` or design source. The analysis manifest does this better because it requires `design_source`, `data_source`, and `interpretation_boundary`.

Impact: data and literature work can be reproducible without being tightly connected to the declared research question.

### P2. Specialist methods are honestly watchlisted, not solved

The current pack has a general methods-reviewer and routes DID/event-study to `$did-expert`. It includes general guidance for IV, RD, RCT, survey, text, spatial, and network designs, but these are audit checklists, not deep specialist methodology skills.

Impact: the framework is suitable for workshop-level routing and first-pass review, but it should not be marketed as methodologically complete for every empirical design.

### P3. The external methodology spine is solid enough for this use case

MIDA is a good unifying framework because it covers both first-order production and second-order audit. It does not force every project into causal inference, and it gives the skillpack a vocabulary that works for descriptive, causal, text, qualitative, and synthesis tasks.

This is better than using `estimand` alone. `Estimand` is necessary for causal work, but it cannot cover data strategy, answer strategy, diagnosis, redesign, reporting, or non-causal inquiry by itself.

Impact: the selected foundation is sound; the remaining problem is operational enforcement.

## Required Improvements

1. Make `study-design-builder` produce an explicit MIDA design brief.
   - Add headings for `Model`, `Inquiry`, `Data strategy`, `Answer strategy`, `Diagnose`, `Redesign`, and `Report boundary`.
   - Update `design_decision_register.csv` to include `mida_component` or create a separate `study_design_declaration.csv`.

2. Add a method-declaration validator.
   - It should validate actual design artifacts, not only the methodology matrix.
   - It should fail when causal projects lack an estimand-like inquiry, non-causal projects lack a target quantity/construct/classification/synthesis question, or any project lacks data and answer strategy.

3. Thread methodology fields into downstream schemas.
   - `claim_ledger.csv`: add `target_inquiry`, `interpretation_boundary`, `diagnosed_limit`.
   - `slide_map.csv`: add `sample_or_scope`, `uncertainty_or_caveat`, `privacy_status`, `interpretation_boundary`.
   - `revision_matrix.csv`: add `mida_element_affected`.

4. Strengthen route cards as pre-declarations.
   - Add provisional `model_scope`, `candidate_inquiry`, `possible_data_strategy`, and `possible_answer_strategy`.

5. Treat specialist methods honestly.
   - Keep DID delegated to `$did-expert`.
   - Add IV/RD/RCT/survey/network/spatial/ML specialist skills only when course cases require them.

## Bottom Line

The skillpack is no longer just agent monologue. It has a credible methodology spine and real workflow structure.

After remediation, MIDA has moved from prose into schemas, validators, examples, and the cross-skill contract. The correct claim is now:

> This is a coherent methodology-enforcing teaching workflow for moving a research project from route discovery to design, data/literature, analysis, diagnosis, reporting, and revision. It is not a complete specialist-methods system for every empirical design.

## Sources

- DeclareDesign: https://declaredesign.org/
- `Research Design in the Social Sciences`: https://book.declaredesign.org/
- Declaring designs chapter: https://book.declaredesign.org/declaration-diagnosis-redesign/declaring-designs.html
- APSR article page, `Declaring and Diagnosing Research Designs`: https://www.cambridge.org/core/journals/american-political-science-review/article/declaring-and-diagnosing-research-designs/3CB0C0BB0810AEF8FF65446B3E2E4926
