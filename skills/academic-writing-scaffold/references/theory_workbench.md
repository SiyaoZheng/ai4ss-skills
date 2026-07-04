# Theory Workbench Template

Use this template when validated literature-to-theory sidecars need author
review before any theory-section prose is written.

## Inputs

- `literature_theory_synthesis.csv`
- `theory_rival_map.csv`
- `theory_scope_map.csv`
- `theory_evidence.md`
- compiled `.aiss` output from `dsl/scripts/compile_evidence.py`, when present
- methods issue table rows touching Model, Diagnose, Redesign, or Report

Run or require:

```bash
python3 scripts/validate_theory_workbench.py <workbench-dir>
python3 scripts/validate_ai4ss_model.py <compiled-theory-output.aiss>
```

## Candidate Object Review

| synthesis_id | proposed_aiss_object | evidence slot | rival or boundary | author task |
|---|---|---|---|---|
| TS1 | concept:<id> | source rows, source status, observable implication | rival_id or scope_id | decide whether this is the paper's construct |
| TS2 | causal:<id> | mechanism parts and source support | rival_id or scope_id | decide mechanism strength and prose boundary |

The agent may fill `evidence slot` and `rival or boundary`. The author fills or
approves `author task`.

## Rival Review

| rival_id | target_synthesis_id | rival claim | discriminating observation | author task |
|---|---|---|---|---|
| RV1 | TS2 | competing explanation | diagnostic, source, or coding evidence needed | decide whether the rival changes the design or claim |

## Scope Review

| scope_id | target_synthesis_id | who/where/when | boundary failure mode | author task |
|---|---|---|---|---|
| SC1 | TS1 | population, setting, and time | how the claim fails outside scope | decide whether this is theoretical scope or data limit |

## Paragraph Skeleton

| paragraph | evidence and claim slot | author task |
|---|---|---|
| Theory P1 | concept slot; source ids; `.aiss` concept id if validated | write the construct framing in own voice |
| Theory P2 | mechanism slot; actor/action/mediating condition/outcome link | decide framing hypothesis vs tested implication |
| Theory P3 | rival slot; discriminating observable implication; issue table link | decide whether to foreground rival or boundary |
| Theory P4 | scope slot; who/where/when; failure mode | write scope boundary in own voice |
| Theory P5 | unresolved contribution slot; decision ids | decide novelty and contribution language |

## Hard Boundary

Author must write final prose. The workbench can expose evidence, source ids,
`.aiss` ids, issue rows, and author decision questions; it cannot establish
novelty, theoretical contribution, final mechanism strength, or final
literature-review prose.
