# AISS DSL Core Specification v0.4

Status: normative local specification for the AI4SS research-factory skillpack.

## Purpose

AISS v0.4 is a deterministic, source-grounded research DSL for social-science
workflows. It fuses the prior source/span PaperAST idea and the research-model
DSL into one `.aiss` language and one compiled AST:

```text
aiss.unified_ast.v0.4
```

The formal chain is deterministic:

```text
aiss.py compile(.aiss) -> canonical unified AST
aiss.py lint(AST) -> deterministic diagnostics
aiss.py run(AST) -> deterministic coupling and model diagnostics
aiss.py diff(AST_A, AST_B) -> deterministic structural diff
aiss.py write(AST, template) -> deterministic text artifact
```

No formal operation may call an LLM, depend on random ordering, use wall-clock
time, or silently consult network resources.

## File Model

Files use UTF-8 and begin with:

```aiss
aiss version "0.4"
```

Version `0.4` is the only supported workflow version. The former local
research-model extension is not valid.

Comments:

- `// line comment`
- `/* block comment */`

Declaration order is not semantic. IDs must be stable qualified IDs:

```text
namespace.local_id
```

Recommended pattern:

```text
<project>.<object_kind>_<short_name>
```

## Top-Level Grammar

The source surface is block-based:

```text
program =
  "aiss" "version" "0.4"
  declaration*

declaration =
  paper | source | span |
  route | mida | decision |
  concept | claim | relation | empirical | observation | coupling |
  artifact | adapter |
  attribute | causal | bridge | edge | model | check | derive
```

Values are JSON-like:

```text
STRING, NUMBER, true, false, null, [VALUE, ...], { key: VALUE, ... }, bare_id
```

## Unified AST Regions

| region | declarations | purpose |
|---|---|---|
| Provenance | `paper`, `source`, `span` | Grounds the research object in stable source locators |
| Workflow | `route`, `mida`, `decision` | Represents candidate/selected routes, declared MIDA components, handoff decisions, and author-owned stops |
| Theory/discourse | `concept`, `claim`, `relation` | Represents constructs, asserted claims, and theoretical relations |
| Empirical | `empirical`, `observation`, `artifact`, `adapter` | Represents data, cases, observations, code, tables, figures, and deterministic adapters |
| Coupling | `coupling`, `bridge` | Links theory/model objects to empirical material |
| Research model | `attribute`, `concept`, `causal`, `edge`, `model`, `check`, `derive` | Encodes MIDA-facing model structure and requested diagnostics |

`concept` is intentionally shared: it is both a theory object and a model
object. A concept must be source-grounded and may also carry parents, theta
rules, operationalization, and rule metadata.

The workflow declarations are the bridge between the appserver-observed skill
behavior and the deterministic DSL. `research-starter` may produce candidate
`route` declarations without pretending they are designs. `study-design-builder`
selects a route and adds the seven `mida` declarations. Later skills attach
sources, artifacts, claims, concepts, bridges, and diagnostics to the same
research object. Sidecar CSV/Markdown files may remain useful views, but they
are not a second DSL; route cards must preserve `route_decl_id`, MIDA
declaration rows must preserve `mida_id`, and decision registers must preserve
`decision_decl_id` when they mirror workflow state.

## Required Fields

| declaration | required fields |
|---|---|
| `paper` | `title`, `kind`, `sources` |
| `source` | `kind`, `uri`, `media_type`, `locator_scheme` |
| `span` | `source`, `locator` |
| `route` | `question`, `status`, `study_type`, `unit_of_analysis`, `inquiry`, `data_strategy`, `answer_strategy`, `stop_reason`, `next_skill_route` |
| `mida` | `route`, `component`, `text`, `status` |
| `decision` | `route`, `component`, `decision`, `status`, `owner`, `next_skill_route` |
| `concept` | `term`, `spans` |
| `claim` | `kind`, `text`, `spans` |
| `relation` | `type`, `from`, `to`, `spans` |
| `empirical` | `kind`, `label`, `spans` |
| `observation` | `kind`, `text`, `about`, `spans` |
| `coupling` | `type`, `theory`, `empirical`, `asserted_by`, `spans` |
| `artifact` | `kind`, `uri`, `media_type` |
| `adapter` | `version`, `consumes`, `produces` |
| `attribute` | `domain`, `values` |
| `causal` | `source`, `target`, `direction` |
| `edge` | `type`, `source`, `target` |
| `bridge` | `type` |
| `model` | none, but production models should list `attributes`, `concepts`, `causal`, and `bridges` |
| `check` | `type`, `on` |
| `derive` | `type`, `from` |

## Minimal Unified Example

```aiss
aiss version "0.4"

paper demo.platform_innovation_paper {
  title: "City Platform Exposure and Green Innovation"
  kind: "teaching_fixture"
  sources: [demo.src_design]
}

source demo.src_design {
  kind: "design_brief"
  uri: "docs/examples/research_model.aiss"
  media_type: "text/aiss"
  locator_scheme: "line"
}

span demo.span_platform_exposure {
  source: demo.src_design
  locator: "concept:platform_exposure"
}

span demo.span_route_r1 {
  source: demo.src_design
  locator: "route:R1"
}

route demo.route_r1 {
  question: "Does city platform exposure change firm green innovation?"
  status: selected
  study_type: causal
  unit_of_analysis: "firm-year / city-year"
  inquiry: "average effect of platform exposure on high innovation"
  data_strategy: "source-verified rollout records linked to firm outcomes"
  answer_strategy: "readiness checks before estimation"
  stop_reason: "author must approve identification and claim strength"
  next_skill_route: research-data-builder
  spans: [demo.span_route_r1]
}

mida demo.mida_r1_model {
  route: demo.route_r1
  component: model
  text: "Declare the exposure and innovation constructs before data work."
  status: declared
  spans: [demo.span_route_r1]
}

decision demo.decision_r1_identification {
  route: demo.route_r1
  component: inquiry
  decision: "Author must decide whether the causal route is worth pursuing."
  status: needs_author_decision
  owner: author
  next_skill_route: ask_author
  spans: [demo.span_route_r1]
}

attribute demo.platform_exposure {
  domain: binary
  values: ["absent", "present"]
  spans: [demo.span_platform_exposure]
}

concept demo.exposed_unit {
  term: "exposed unit"
  definition: "Unit exposed to the platform in the declared time window."
  spans: [demo.span_platform_exposure]
  parents: [demo.platform_exposure]
  theta: {
    "[\"absent\"]": 0
    "[\"present\"]": 1
  }
  rule: definitional
}

model demo.platform_innovation {
  attributes: [demo.platform_exposure]
  concepts: [demo.exposed_unit]
}

check demo.check_reference_integrity {
  type: reference_integrity
  on: demo.platform_innovation
}
```

## Forbidden Source Primitives

Analyzer outputs are not source declarations. The parser rejects:

```text
fact
gap
diagnostic
support_score
unsupported_claim
overclaim
next_action
review_comment
critique
lint_result
```

These belong in lint/run reports, methods-review issue tables, claim ledgers, or
author decision registers.

## Deterministic Outputs

`compile` emits:

- `paper`
- `sources`
- `spans`
- `workflow`
- `objects`
- `relations`
- `models`
- `checks`
- `derives`
- `indices`
- deterministic hashes

`lint` checks missing references, invalid endpoint types, missing provenance,
concept conflicts, structured-claim contradictions, and empirical objects that
are not linked to artifacts or observations.

`run` emits:

- deterministic adapter skip records when no adapter is registered
- coupling assessments with `not_assessable` instead of guessed support
- workflow diagnostics, including selected routes, MIDA coverage, and open author decisions
- model diagnostics, including bridge coverage and commensurability signals

`diff` compares canonical AST structures by path. `write` renders deterministic
templates from the AST.

## Research Boundary

AISS can represent checked claims, model structure, evidence links, and
diagnostics. It must not be used to generate final manuscript prose, final
reviewer-response prose, or final scholarly claims. Those remain author
decisions mediated through claim ledgers, source maps, review tables, and
bounded scaffolds.
