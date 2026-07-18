# Scholar Workbenches

This note reframes the local skill universe around the scholar's actual sequence of work: first make a research object exist, then make its evidence chain inspectable.

## Big Picture

The skill universe has two layers.

| layer | scholar problem | local skill | minimum artifact | success criterion |
|---|---|---|---|---|
| First-order production | 这个研究怎么先动起来？ | `research-starter` | `.aiss` candidate `route` declarations, `research_starter_packet.md`, route cards, minimum viable study, handoff prompt | A feasible first research loop exists, with a stop reason and researcher decision point |
| First-order production | 这个路线怎样落成可执行设计？ | `study-design-builder` | selected `.aiss` `route`, seven `mida` declarations, `decision` declarations, design sidecars | Unit, constructs, comparison, evidence needs, and first analysis plan are explicit |
| First-order production | 第一批可检查结果怎么跑出来？ | `research-analysis-runner` | `analysis_readiness_check.csv`, scripts, logs, tables/figures, `analysis_run_manifest.csv` | Outputs pass a readiness gate and keep sample notes and interpretation boundaries |
| Second-order audit | 这个研究对象是否站得住、说得清、可追溯？ | Evidence and review skills | Validated ledgers, matrices, audit tables, revision traces | The generated evidence chain can be inspected, corrected, and approved |

The first layer is not a shortcut to paper writing. It is a way to turn a loose idea, source pile, dataset folder, or policy phenomenon into a route that can be tried. The second layer should not be forced before there is something to audit.

## Computable Research Object

The workbench should not rely only on conversation memory. Once a route becomes
a design, the project should have one computable representation plus readable
projections:

| representation | purpose |
|---|---|
| `.aiss` research object | Machine-checkable route, MIDA declaration, required gates, source spans, attributes, concepts, theta rules, causal implications, empirical bridges, and diagnostics |
| Sidecar projections | Human-readable route cards, design declarations, decision registers, data/literature audits, analysis manifests, and claim ledgers |

This is the difference between asking Codex to analyze and building an
autonomous research factory. Codex can reason in prose. A factory needs stable
objects that survive context reset, can be checked, compiled, audited, and
handed to the next skill without semantic drift.

## Methodology Spine

The workbenches share one research-design spine:

```text
Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims
```

`MIDA` means `Model`, `Inquiry`, `Data strategy`, and `Answer strategy`. `Estimand` is one possible form of `Inquiry`, not the whole design. This matters for ordinary scholars because the agent should not merely say "estimate X on Y"; it must help make unit, construct, source, measurement, answer procedure, failure signal, and required gate visible.

| spine element | where it appears in the local workflow |
|---|---|
| Pre-declare possible routes | `research-starter` `.aiss` route declarations, mirrored as route cards |
| Declare MIDA | `study-design-builder` selected `.aiss` route plus seven `mida` declarations |
| Realize Data strategy | `research-data-builder`, `literature-matrix`, deterministic literature evidence compilation when sources update `.aiss` |
| Execute Answer strategy | `research-analysis-runner` |
| Diagnose and redesign | `methods-reviewer`, `reviewer-response` |
| Report bounded claims | `academic-writing-scaffold`, `research-slides-builder`, `reviewer-response` |

## First-Order Workbench

| scholar question | workbench | local skill | minimum artifact | stop gate |
|---|---|---|---|---|
| 这个研究怎么先动起来？ | Research starter workbench | `research-starter` | candidate `.aiss` route declarations, `research_starter_packet.md`, `research_route_cards.csv` when useful | `stop_reason`, `required_gate`, `next_skill_route` |
| 这个路线怎样落成可执行设计？ | Study design workbench | `study-design-builder` | selected `.aiss` route, seven `mida` declarations, `study_design_brief.md`, `design_decision_register.csv` | unresolved required gates and downstream route |
| 第一批可检查结果怎么跑出来？ | Analysis runner workbench | `research-analysis-runner` | `analysis_readiness_check.csv`, scripts, outputs, logs, `analysis_run_manifest.csv` | readiness status, interpretation boundary, and methods-review route |

The starter workbench should answer practical questions:

- What are 2-4 feasible research routes from this rough topic?
- What materials already exist, and what is missing?
- What is the smallest study that can teach us whether to continue?
- What one action can an agent do next without crossing authorship or confidentiality boundaries?
- Which downstream skill should take over after that action?
- What design choice or first analysis should be attempted only after researcher confirmation?

## Second-Order Workbenches

| scholar question | workbench | local skills | minimum artifact | validation gate |
|---|---|---|---|---|
| 数据怎么来的，样本怎么变的？ | Data provenance workbench | `research-data-builder` | `sample_flow.csv`, `merge_audit.csv`, `variable_provenance.csv`, logs | `validate_data_audits.py` |
| 文献证据是不是一手来源？ | Literature evidence workbench | `literature-matrix` | `literature_matrix.csv`, `literature_candidate_discovery.csv`, compiled evidence `.aiss` when model elements are affected, screening log, source locators | `validate_literature_matrix.py`, `validate_literature_discovery.py`, `validate_literature_evidence_compile.py` |
| 结果解释有没有说过头？ | Claim discipline workbench | `methods-reviewer`, `academic-writing-scaffold` | issue table, claim ledger, required gate questions | `validate_issue_table.py`, `validate_claim_ledger.py` |
| 返修有没有证据链？ | Revision trace workbench | `reviewer-response`, plus upstream evidence skills | `revision_matrix.csv`, `revision_trace/`, open gates | `validate_revision_matrix.py` |

## Why This Matters

The first-order layer is useful only if it creates a usable research object:

- It turns a rough theme into `.aiss` route declarations with data, source, method, and failure signals.
- It makes feasibility visible before the researcher spends weeks on an impossible topic.
- It gives ordinary scholars a first executable action instead of a methodology lecture.
- It stops at required gate points instead of writing the paper.

The second-order layer is useful only when it reduces scholarly risk:

- It makes row loss, merge ambiguity, and variable construction visible before a result is interpreted.
- It keeps literature synthesis tied to verified primary or local sources rather than model memory.
- It can turn verified source rows into deterministic `.aiss` evidence fragments when a model element is affected.
- It separates evidence-supported claims from interpretation, mechanism speculation, and author judgment.
- It turns reviewer comments into auditable actions before the author writes final response prose.

## Teaching Rule

Teach the sequence before the tool names:

1. First, make one research loop exist: `.aiss` route, material, first action, stop reason.
2. Turn the selected `.aiss` route into a design brief and seven `mida` declarations: unit, constructs, comparison, evidence needs, and first analysis plan.
3. Execute one analysis loop only after `analysis_readiness_check.csv` validates the design source, data source, required variables, sample/audit paths, and `.aiss` bridge alignment where applicable.
4. Then, when the route produces evidence, use the second-order workbenches to inspect it.

Do not present AI as a writing shortcut. Present the agent as a research workbench that creates intermediate objects the researcher can inspect, revise, reject, and approve.

## Factory-Level Evaluation

Use the factory-level structural package when the question is whether the whole
`.aiss` workflow turns a rough topic into a checked research pipeline:

```bash
python3 scripts/run_factory_level_eval.py --clean
```

The package in `docs/factory_level_eval/` contains a protocol, blinded packets,
a gate matrix, a hidden condition mapping, a human grading sheet, deterministic
rule-based scores, and an unblinded report. It scores the full chain:

```text
rough topic -> .aiss route declarations -> .aiss MIDA declarations ->
.aiss model/check ->
literature/data gates -> analysis readiness -> analysis manifest ->
bounded claim handoff
```

This is the right classroom artifact for explaining why the workbench is more
than direct Codex analysis. Its claim is still narrow: it verifies that the
factory contract is evaluable and reproducible, not that live agents will always
use it correctly.

## Skill-Use Evaluation

Use the live package when you want evidence closer to actual agent behavior. It uses agent-generated outputs, anonymized packets, a hidden condition mapping, frozen grader CSVs, and an unblinded report:

```bash
python3 scripts/run_live_blind_skill_use_eval.py package --clean
python3 scripts/run_live_blind_skill_use_eval.py report
```

For a new evaluation, run `package` before grading. After grades are frozen, do not repackage with a fresh seed. To reproduce the current mapping, use the disclosed private seed:

```bash
python3 scripts/run_live_blind_skill_use_eval.py package --clean --seed "$(cat docs/live_blind_skill_use_eval/_private/randomization_seed.txt)"
python3 scripts/run_live_blind_skill_use_eval.py report
```

Give graders only `docs/live_blind_skill_use_eval/grader_brief.md`, `docs/live_blind_skill_use_eval/packets/`, and `docs/live_blind_skill_use_eval/human_grading_sheet.csv`. Keep `docs/live_blind_skill_use_eval/_private/private_mapping.csv` hidden until scores are frozen.

Use the structural simulation package only when you need a deterministic classroom demo:

Regenerate the condition-blinded package with:

```bash
python3 scripts/run_blind_skill_use_eval.py --clean
```

The older non-blinded demonstration can still be regenerated with:

```bash
python3 scripts/simulate_skill_use_eval.py --output docs/skill_use_eval.simulated_report.md
```

Both simulations check output structure, not model intelligence. Their teaching claim is narrow: skills are useful only when they make canonical artifacts, validation gates, and workflow-gated decisions appear in the workflow. A true double-blind evaluation would still require independently generated live outputs, concealed condition assignment, independent human graders, and inter-rater reliability checks.

The live package is condition-blinded for scoring, not fully double-blind. Generators know their assigned condition, and packet style can still reveal clues. Its appropriate claim is narrower: in these controlled tasks, skill-guided agents can be compared against careful generic agents on traceability, boundary discipline, validation gates, and required gate visibility.

## Improvement From Live Evaluation

The live evaluation found that `literature_evidence` did not improve under the first skill-guided run. The gap was not source grounding in principle; it was search richness. The generic packet offered more seed sources and a clearer source-status ledger, while the skill-guided packet leaned too heavily on schema discipline.

The `literature-matrix` skill now requires an open-ended literature task to start with `literature_candidate_discovery.csv` before extraction. That discovery ledger records search strata, exact queries or seed sources, source type, source status, next verification action, relevance axis, and snowballing targets. The validator `validate_literature_discovery.py` checks this stage separately from `validate_literature_matrix.py`.
