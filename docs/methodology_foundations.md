# Methodology Foundations

This document answers the hard question: whether the AI4SS skillpack is grounded in a serious social-science research-design framework or only in agent workflow conventions.

## Judgment

The earlier workflow was stronger on artifact discipline than on methodology. It had useful ledgers, validators, and handoffs, but the foundation could still look like a list of separate method articles. That is not enough.

The skillpack should now be read as an operationalization of one research-design spine:

```text
Declare MIDA -> Diagnose -> Redesign -> Report with bounded claims
```

This is a no-dead-end workflow. If a route cannot support the original claim,
the workflow must redesign to a weaker, narrower, or different feasible inquiry
and complete that inquiry. Missing evidence is not a final result. It is a
diagnostic signal that changes the design, data strategy, answer strategy, or
claim boundary until the current run can be completed.

The sources listed below are anchors for this spine. They are not a substitute for the spine.

## Research-Design Spine

The common language is adapted from the MIDA and declare-diagnose-redesign framework in `Research Design in the Social Sciences` and DeclareDesign. Every empirical project should be describable through four declared elements, then diagnosed and redesigned when the declaration is weak.

| element | working meaning in this skillpack | required question |
|---|---|---|
| Model | The stipulated view of how the world could produce the phenomenon, including units, constructs, mechanisms, scope conditions, and assumptions | What kind of world would make this research question meaningful? |
| Inquiry | The target of inference: causal estimand, descriptive quantity, classification target, measurement target, process-tracing claim, or synthesis question | What exactly is the study trying to learn? |
| Data strategy | Sampling, source selection, measurement, treatment/exposure timing, text extraction, linkage, missingness handling, and source-screening rules | What data or evidence would make the inquiry observable? |
| Answer strategy | Estimator, coding procedure, synthesis rule, diagnostic comparison, table/figure shell, or qualitative inference procedure | How will the evidence be converted into an answer? |
| Diagnose | Bias, precision, power, coverage, measurement risk, source-screening risk, linkage loss, reproducibility status, and claim-support mismatch | What can go wrong, and how would we know before overclaiming? |
| Redesign | Neighboring feasible designs, smaller first loops, added data, revised measures, changed estimators, or abandoned routes | What should change when the current design is too weak? |
| Report | Claim ledger, source map, AI-use ledger, required gate points, and public communication boundaries | What can be said, by whom, and with what evidence? |

`Estimand` is important, but it is not the whole framework. In this pack it lives inside `Inquiry`. A causal project should name the target comparison, population, outcome, exposure/treatment, time window, and scale. A descriptive, text, qualitative, or literature-synthesis project should name its target quantity, construct, classification, sequence, or synthesis claim with the same precision.

## Theory Workbench Boundary

The shared theory engine is a workflow layer across existing skills, not a new
top-level skill. Literature evidence enters through `literature_matrix.csv` and
`literature_theory_synthesis.csv`; rival explanations and scope conditions are
kept in `theory_rival_map.csv` and `theory_scope_map.csv`; model-ready objects
are compiled from `theory_evidence.md` through the existing
`dsl/scripts/compile_evidence.py` path.

The methodology role is narrow: make candidate concepts, mechanisms, observable
implications, rivals, and scope conditions inspectable before the author writes.
Validated `ready_for_aiss` objects can support `.aiss` `concept`, `claim`,
`relation`, `causal`, `bridge`, and `model` declarations. Novelty, theoretical
contribution, mechanism strength, scope framing, and rival prioritization
remain workflow-gated `decision` declarations or Gate Workbench questions.

## Skill Assignment

| workflow stage | skill | methodology role | must declare or preserve |
|---|---|---|---|
| Route discovery | `research-starter` | Pre-declaration: write candidate `.aiss` `route` declarations before committing | rough Model, candidate Inquiry, possible Data strategy, possible Answer strategy, diagnosability, failure signal |
| Design | `study-design-builder` | Primary declaration: turn a selected `.aiss` `route` into seven `mida` declarations and workflow-gated `decision` declarations | Model, Inquiry, Data strategy, Answer strategy, diagnosands, required gates |
| Data | `research-data-builder` | Data strategy realization and audit | sample/source rule, measurement, extraction, linkage, transformations, row loss, missingness, provenance |
| Literature | `literature-matrix` | Evidence-as-data strategy for literature claims | source scope, search strata, screening rule, source status, extraction fields, synthesis eligibility, optional theory workbench handoff |
| Analysis | `research-analysis-runner` | Answer strategy execution | design source, data source, code path, output path, sample note, uncertainty/diagnostic output, interpretation boundary |
| Methods review | `methods-reviewer` | Diagnose and redesign | design-output-claim alignment, diagnosands, rival/scope/mechanism risks, method-specific risks, recommended redesigns |
| Writing scaffold | `academic-writing-scaffold` | Reporting discipline | target inquiry, evidence source, support level, citation/source gap, theory workbench questions, required gate, AI-writing boundary |
| Slides | `research-slides-builder` | Public communication from declared evidence | claim slot, source artifact, sample/scope, uncertainty or caveat, privacy status |
| Revision | `reviewer-response` | Redesign and reconciliation under peer review | reviewer request, MIDA element affected, evidence action, manuscript location, confidentiality, required gate |

## Required Declaration Fields

These fields are the minimum cross-skill vocabulary. A skill does not need to fill every field, but it must preserve fields supplied upstream and mark missing fields explicitly when they matter.

The hard design object is `research_model.aiss`: a selected `.aiss` `route`, seven `mida` declarations, and workflow-gated `decision` declarations. `study_design_brief.md`, `research_route_cards.csv`, `study_design_declaration.csv`, and `design_decision_register.csv` are readable projections of that object for humans and validators.

| field | why it matters |
|---|---|
| `route_id` | Keeps alternative designs from collapsing into one vague project |
| `route_decl_id` | Points route sidecars to the matching `.aiss` `route` declaration |
| `mida_id` | Points design-declaration rows to the matching `.aiss` `mida` declaration |
| `decision_decl_id` | Points decision-register rows to the matching `.aiss` `decision` declaration |
| `model_scope` | Names population, unit, place/time, construct, mechanism, and assumptions |
| `inquiry` | Names the target estimand, descriptive quantity, measurement target, classification target, or synthesis question |
| `data_strategy` | Names source selection, sampling, measurement, extraction, linkage, and missingness rules |
| `answer_strategy` | Names estimator, coding rule, synthesis rule, or output procedure |
| `diagnosands_or_gates` | Names what will be checked: bias, precision, power, source status, row loss, reproducibility, claim support |
| `redesign_options` | Names feasible changes if the current design fails |
| `interpretation_boundary` | States what the artifact can and cannot support |
| `required_gates` | Makes researcher judgment explicit instead of laundering it through the agent |

## Computable DSL Layer

The methodology spine now has an implementation layer: the `.aiss` DSL in
`SiyaoZheng/ai4ss-skills`. This is not another methods citation. It is a
computable representation for workflow state, source grounding, model structure,
and deterministic diagnostics in one language.

Use `.aiss` for:

- route status, route handoff, selected route, MIDA declarations, and author
  decisions
- source, span, claim, relation, empirical, observation, coupling, artifact, and
  adapter records
- attributes and allowed domains
- concepts, parent attributes, theta tables, construction rules, sources, and
  operationalizations
- causal implications, mechanisms, scope conditions, and textual-support status
- empirical bridges connecting concepts or implications to methods, validity
  claims, estimands, and commensurability status
- static checks and derived diagnostics

Do not use `.aiss` as a replacement for:

- full data strategy, including sampling, cleaning, linkage, extraction, and
  missingness sidecars
- full answer strategy, including estimator/coding/synthesis scripts
- ethics/confidentiality checks, AI-use disclosure, and final manuscript prose

In factory terms: MIDA tells the scholar what kind of research object they are
building. `.aiss` makes the workflow, evidence, and model portions of that
object durable and checkable.

## What This Changes In Practice

- A skill cannot claim methodology grounding by citing methods papers alone. It must state which part of the research-design spine it operates.
- `study-design-builder` becomes the central declaration skill. It selects a `.aiss` route, declares MIDA, and records decisions; estimand or target quantity belongs there only alongside Model, Data strategy, Answer strategy, and diagnosands.
- `research-starter` may propose routes, but those `.aiss` routes are provisional MIDA sketches, not valid designs.
- `research-data-builder`, `literature-matrix`, and `research-analysis-runner` are not generic productivity skills. They realize the Data strategy and Answer strategy in auditable artifacts.
- Theory mapping is not a prose generator. It is a validated handoff from
  verified literature rows to existing `.aiss` model declarations and bounded
  required gates.
- `methods-reviewer` is the diagnostic layer. It should ask whether the declared design, executed outputs, and claims line up.
- Writing, slides, and reviewer response are reporting/redesign layers. They must preserve the declared inquiry and diagnosed limits rather than create new scholarly claims.

## Source Anchors

| source | role in the framework |
|---|---|
| Blair, Coppock, and Humphreys, `Research Design in the Social Sciences` / DeclareDesign | Main framework: MIDA, declare-diagnose-redesign, diagnosands, and design lifecycle from planning through integration |
| Blair, Coppock, and Humphreys, `Declaring and Diagnosing Research Designs` | Formal anchor for declaring Model, Inquiry, Data strategy, and Answer strategy, and diagnosing design properties |
| King, Keohane, and Verba, `Designing Social Inquiry` | General social-science logic for observable implications, descriptive inference, causal inference, and research-design discipline |
| Imbens and Rubin / Imbens causal-inference overview | Potential-outcomes and causal estimand discipline for causal projects |
| Collier, `Understanding Process Tracing` | Qualitative and case-based reminder that diagnostic evidence, sequence, and alternative explanations matter |
| PRISMA 2020 and PRISMA-ScR | Reporting and screening discipline for systematic and scoping literature evidence |
| Grimmer, Roberts, and Stewart, `Text as Data` | Text-as-data anchor for corpus construction, measurement, prediction, discovery, and causal questions |
| COS TOP Guidelines and preregistration guidance | Transparency, protocol, analysis-plan, material, data, code, reporting, and reproducibility norms |
| AEA Data and Code Availability Policy and AEA Data and Code Repository | Data/code deposit, documentation, and reproducibility norms for economics and adjacent social science |
| Goodman, Fanelli, and Ioannidis, `What does research reproducibility mean?` | Conceptual guardrail: reproducibility is not the same as truth |
| ICMJE AI-use guidance | Authorship and disclosure guardrail: AI tools cannot be authors and humans remain responsible |

## Remaining Weak Spots

| weak spot | implication | current status |
|---|---|---|
| Ethics and confidentiality | Human subjects, restricted administrative data, reviewer confidentiality, and collaborator permissions are only partially handled through ledgers and routing rules | Watchlist for a future `research-integrity-ledger` or `ethics-confidentiality-reviewer` skill |
| Qualitative/interview analysis | Current tools do not fully cover interview protocols, consent, coding reliability, positionality, or interpretive validity | Watchlist for a future qualitative-analysis skill if the workshop adds such cases |
| Specialist methods | DID is covered by global `$did-expert`, but IV, RD, RCT, survey, network, spatial, and ML evaluation are only generally routed | Add specialist skills only when course cases require them |
| First-order skill evaluation | Existing live evaluation is stronger for audit/scaffold tasks than for route-discovery and design-declaration tasks | Add first-order tasks to the next blinded skill-use evaluation |
| Design simulation | The local skills currently declare and audit design objects but do not run full DeclareDesign-style Monte Carlo diagnosis | Treat simulation only as an optional diagnostic for a declared design, never as a fabricated fallback for a missing dataset |

## Source URLs Checked

- https://declaredesign.org/
- https://book.declaredesign.org/
- https://book.declaredesign.org/introduction/what-is-a-research-design.html
- https://book.declaredesign.org/declaration-diagnosis-redesign/declaring-designs.html
- https://declaredesign.org/paper.pdf
- https://www.cambridge.org/core/journals/american-political-science-review/article/declaring-and-diagnosing-research-designs/3CB0C0BB0810AEF8FF65446B3E2E4926
- https://gking.harvard.edu/kkv/
- https://polisci.berkeley.edu/sites/default/files/people/u3827/2011%20Collier-Understanding%20Process%20Tracing%20with%20Addendum.pdf
- https://www.annualreviews.org/content/journals/10.1146/annurev-statistics-033121-114601
- https://www.aeaweb.org/articles?id=10.1257/jel.20251650
- https://www.prisma-statement.org/
- https://www.prisma-statement.org/scoping
- https://politicalscience.stanford.edu/publications/text-data-new-framework-machine-learning-social-sciences
- https://www.cos.io/initiatives/top-guidelines
- https://www.cos.io/initiatives/prereg
- https://www.aeaweb.org/journals/data/data-code-policy
- https://www.icpsr.umich.edu/sites/aea/home
- https://pubmed.ncbi.nlm.nih.gov/27252173/
- https://www.icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-authors.html
