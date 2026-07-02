# AI4SS DSL Factory Integration

This note records how the AI4SS local skillpack should use the explicit DSL in
`SiyaoZheng/ai4ss-skills`, instead of treating the workflow contract as an
implicit language.

Remote reference inspected on 2026-07-01:

- Repository: `https://github.com/SiyaoZheng/ai4ss-skills`
- HEAD: `087cff2ef275be3762db4b229430cb2fae8f2f0c`
- Relevant paths: `dsl/scripts/`, `dsl/scripts/test_fixtures/`,
  `codebook-parse.skill`, `cleaning-contract.skill`, `cleaning-execute.skill`

## Naming Rule

Use `AI4SS DSL` and the `.aiss` extension as the local architecture name and
artifact contract. The current GitHub implementation still uses `aiss_*` script
names. Those names are legacy tool names, not the local research-model
extension.

```text
.aiss research DSL == current ai4ss-skills parser/checker/compiler semantics
```

Do not create a second incompatible DSL. Local files must use `.aiss` and must
compile through the same parser/checker/compiler semantics as the upstream
toolchain.

## Toolchain Resolution

Local wrappers should not vendor a fork of the DSL unless the upstream repository
changes incompatibly. They should resolve the current `ai4ss-skills` toolchain in
this order:

1. `AI4SS_SKILLS_DIR`
2. the current repository when it contains `dsl/scripts`
3. project-local `ai4ss-skills`
4. sibling `../ai4ss-skills`
5. project-local `.external/ai4ss-skills`
6. temporary inspection clone `/tmp/ai4ss-skills-inspect`

This keeps `.aiss` as the local artifact extension while reusing the upstream
parser/checker/compiler semantics. If validation fails because the toolchain is
missing, clone `https://github.com/SiyaoZheng/ai4ss-skills` to one of those
locations or set `AI4SS_SKILLS_DIR`.

## Judgment

`ai4ss-skills` contains two different languages.

| layer | form | role |
|---|---|---|
| Skill package language | `.skill/SKILL.md` with YAML frontmatter, references, scripts | Installs reusable domain skills and controls agent triggering |
| Research model DSL | `.aiss` files parsed by upstream `aiss_parser.py`, checked by `aiss_checker.py`, compiled by `aiss_compiler.py` | Represents concepts, attributes, causal implications, empirical bridges, checks, and derived research-model diagnostics |

The second layer is the important one for an autonomous research factory. It
turns a research object into a computable intermediate representation. Direct
Codex analysis can summarize, critique, or propose. The AI4SS DSL gives the agent a
state object that can be parsed, checked, compiled, diagnosed, and handed across
skills.

## What The DSL Expresses

The current upstream fixture `ding_performative_state.aiss` shows the core
vocabulary. Local fixtures and handoffs should use `.aiss`, for example
`docs/examples/research_model.aiss`.

| construct | meaning in research workflow |
|---|---|
| `attribute` | Declared dimensions or primitives, with domain and allowed values |
| `concept` | Construct definition, parent attributes, theta table, rule, source, and operationalization |
| `causal` | Directed theoretical implication between concepts, with direction, condition, mechanism, and textual support |
| `edge` | Non-causal conceptual relation, such as broader/narrower |
| `bridge` | Link from concept or causal implication to empirical method, validity claim, estimand, and commensurability |
| `model` | Named bundle of attributes, concepts, causal claims, and bridges |
| `check` / `derive` | Requested static checks and derived diagnostics |

The toolchain already supports:

- parser: `.aiss` text to typed AST through the current upstream parser
- checker: static checks such as theta completeness, reference integrity,
  relation domain, self-loop detection, orphan concepts, bridge coverage, and
  layer warnings
- compiler: graph-compatible JSON
- FCA: concept extent, closure, and subsumption diagnostics for decidable
  descriptive layers
- bridge diagnosands through `aiss_bridge.py`: commensurability coverage,
  missing bridge detection, and evidence-strength mismatch warnings
- evidence compiler: deterministic evidence table to `.aiss`-compatible model text

## Relation To MIDA

`MIDA` remains the methodology spine. The AI4SS DSL should not replace it.

| MIDA element | AI4SS DSL coverage | remaining non-DSL artifact |
|---|---|---|
| Model | Strong: attributes, concepts, theta, conceptual relations, assumptions through descriptions and source fields | Human-readable design brief and scope notes |
| Inquiry | Partial: causal implications, target concepts, estimand field in bridges | Full target quantity, population, time window, comparison, and answerable question in `study_design_declaration.csv` |
| Data strategy | Partial: empirical bridge method and validity | Dataset/codebook, source selection, sampling, cleaning, extraction, linkage, missingness, and provenance sidecars |
| Answer strategy | Weak to partial: bridge and derivation hints | Estimator/coding/synthesis plan, scripts, analysis run manifest |
| Diagnose | Strong for concept/causal/bridge structure; partial for empirical design diagnosands | Methods-review issue table, simulation or robustness outputs |
| Redesign | Not yet first-class | Design decision register and revision/redesign log |
| Report | Not first-class | Claim ledger, AI-use ledger, slides, reviewer response scaffolds |

Therefore the factory should use the AI4SS DSL as the computable research-model IR
inside the broader MIDA workflow.

## Local Skillpack Integration

| local skill | relationship to the AI4SS DSL |
|---|---|
| `research-starter` | May propose candidate concepts, units, relations, and failure signals, but should treat them as provisional route cards rather than final DSL files |
| `study-design-builder` | Primary owner of `research_model.aiss`, `ai4ss_check_report.txt`, and the mapping from MIDA declaration to `.aiss` model elements |
| `literature-matrix` | Supplies source-grounded evidence tables and source-status fields; when rows affect model elements, records `evidence_table_path`, `compiled_ai4ss_path`, and deterministic `compile_evidence.py` validation status |
| `research-data-builder` | For survey/data cleaning work, should route to `ai4ss-skills` executors: `codebook-parse`, `cleaning-contract`, `cleaning-execute`; then preserve DDI and cleaning-audit paths in data sidecars |
| `research-analysis-runner` | Reads `study_design_declaration.csv`, `research_model.aiss`, cleaned data/audit paths, validates `analysis_readiness_check.csv`, and writes outputs linked to `model_id`, `concept_id`, `causal_id`, or `bridge_id` when applicable |
| `methods-reviewer` | Runs or requests `.aiss` checks, bridge coverage review, commensurability diagnostics, and claim-support alignment |
| `academic-writing-scaffold` | Builds claim ledgers from checked model elements; never turns unchecked `.aiss` claims into manuscript prose |
| `research-slides-builder` | Uses checked concepts, bridges, and diagnosed limits as slide source map entries |
| `reviewer-response` | Maps reviewer requests to MIDA elements and, when relevant, `.aiss` concept/causal/bridge IDs |

## Factory Gates

For autonomous research-factory behavior, the agent should not treat a research
route as production-ready until these gates are explicit.

| gate | required artifact | failure signal |
|---|---|---|
| G1 Research object exists | `research_starter_packet.md` and route cards | Only topic prose, no unit/construct/evidence route |
| G2 Design declared | `study_design_declaration.csv` and `research_model.aiss` when conceptual/causal structure matters | No MIDA declaration, no model IDs |
| G3 Model checks run | `ai4ss_check_report.txt` or logged checker output | Parser/checker errors, missing references, unchecked layer warnings ignored |
| G4 Empirical bridge declared | bridge rows or equivalent design fields | Causal or measurement claim has no empirical bridge |
| G5 Literature evidence compiled when it changes the model | `evidence_table_path`, `compiled_ai4ss_path`, `evidence_compile_status`, and `validate_literature_evidence_compile.py` | Source rows revise model elements only in prose or saved `.aiss` differs from deterministic compiler output |
| G6 Data contract exists when data are transformed | DDI metadata, cleaning contract, cleaning execution audit, sample flow | Raw-to-analysis data path depends on agent memory or undocumented recodes |
| G7 Analysis readiness passed | `analysis_readiness_check.csv` with required variables, sample/audit paths, row count, readiness status, and bridge alignment | Clean data do not match declared inquiry, required variables are missing, or bridge alignment is unchecked |
| G8 Analysis links back to design | analysis manifest with design source, readiness gate, and model/claim references | Tables or figures cannot be traced to declared inquiry and bridge |
| G9 Reporting bounded | claim ledger and AI-use ledger where required | Prose or slides assert unchecked causal/measurement claims |

## Difference From Direct Codex Analysis

Direct Codex analysis is useful for one-off reasoning, but it is not a research
factory by itself.

| direct Codex analysis | AI4SS DSL plus skillpack workflow |
|---|---|
| Answer lives in the current conversation | Research object lives in files that survive context resets |
| Reasoning is hard to replay exactly | Parser/checker/compiler outputs can be rerun |
| Agent may silently change concepts across turns | Concept IDs, theta rules, causal IDs, and bridge IDs stay stable |
| Critique depends on prompt discipline | Static checks expose missing bridge, orphan concept, invalid relation, or layer warning |
| Downstream skills receive prose summaries | Downstream skills receive model IDs, design paths, audit paths, and claim references |
| Evaluation mostly judges final answer quality | Evaluation can inspect artifacts, gates, and failure modes |

## Closed And Remaining Pieces

The local skillpack now has a usable `.aiss` factory spine, but not every
future factory capability is implemented.

| status | item | note |
|---|---|
| closed | Local DSL owner | `study-design-builder` owns `research_model.aiss`, `ai4ss_check_report.txt`, and model identifiers in the MIDA declaration sidecar |
| closed | Data cleaning harness route | `research-data-builder` routes survey/codebook tasks through `codebook-parse`, `cleaning-contract`, and `cleaning-execute` when appropriate |
| closed | Model IDs in downstream artifacts | Data audits, literature matrices, analysis manifests, issue tables, and claim ledgers now carry `ai4ss_model_path`, model ids, and check status |
| closed | Local validator gate | `scripts/validate_ai4ss_model.py` enforces `.aiss` extension while reusing upstream parser/checker/bridge semantics |
| closed | Regression-readiness gate | `analysis_readiness_check.csv` and `scripts/validate_analysis_readiness.py` validate clean data against the declared plan before analysis execution |
| closed | Evidence compiler integration | `literature-matrix` rows now carry evidence markdown and compiled `.aiss` paths; `validate_literature_evidence_compile.py` recompiles with upstream `compile_evidence.py`, compares output, and runs the checker |
| closed | Factory-level structural evaluation | `scripts/run_factory_level_eval.py --clean` regenerates `docs/factory_level_eval/`, a condition-blinded structural package scoring the full rough-topic -> route cards -> MIDA -> `.aiss` -> evidence/data -> readiness -> analysis manifest -> bounded-claim chain |
| open | Live independent factory evaluation | Replace deterministic packets with independently generated live outputs and independent human expert graders before claiming field-level effectiveness |

The important design decision: do not invent a separate `research_job.yaml` as
the main research language. If orchestration metadata is needed, keep it thin
and point it to `research_model.aiss`, MIDA declarations, data contracts, and
analysis manifests.
