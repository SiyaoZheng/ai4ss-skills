# AISS DSL — Core Specification v0.3

> A discourse-native, deterministic DSL for representing the theory, empirics,
> and asserted coupling structure of social-science texts.
>
> Status: normative design specification. The current Python scripts under
> `dsl/scripts/` are v0.2 legacy prototypes and do not yet fully implement this
> v0.3 specification.

## 0. Purpose

AISS is a DSL for compiling a social-science text into a machine-readable
Paper AST. The AST is designed so deterministic programs can lint, run, diff,
and write from it.

AISS is not a method DSL. It does not assume that the text is causal, empirical
in a narrow statistical sense, or organized as a modern journal article. It is
for social-science work broadly understood: theory, description, fieldwork,
historical comparison, interpretive analysis, data-driven empirical research,
and mixed forms.

AISS is also not an Agent Harness. An Agent Harness may help produce candidate
`.aiss` files, propose edits, ask questions, or decide which tool to call next.
But the formal chain below must be deterministic program output:

```text
compile(source) -> canonical PaperAST
lint(PaperAST) -> deterministic diagnostics
run(PaperAST, data, adapters) -> deterministic evidence/code/support outputs
diff(PaperAST_A, PaperAST_B) -> deterministic structural diff
write(PaperAST, template) -> deterministic manuscript/report
```

No operation in this formal chain may call an LLM, use wall-clock time, depend on
random ordering, depend on machine-specific absolute paths, or silently consult
network resources.

### 0.1 Requirements traceability

This section records the design requirements that v0.3 must satisfy.

| Requirement | Spec commitment |
|---|---|
| The DSL is below an Agent Harness. | AISS defines source, AST, and deterministic tool outputs. Harness behavior is outside the formal chain. |
| Focus on theory, empirics, and their coupling, not methods. | Core AST regions are Theory, Empirical, and Coupling. Method-specific work is adapter-level. |
| Compile a social-science text into code-capable structure. | `compile` emits canonical Paper AST; `emit-code` maps AST plus deterministic adapters to generated code. |
| Lint internal incoherence. | `lint` emits deterministic diagnostics over references, provenance, concepts, claims, empirical objects, coupling, and formal determinism. |
| Run whether evidence supports theory. | `run` emits deterministic coupling assessments when explicit rules or adapters are available; otherwise it emits `not_assessable`, not an agent judgment. |
| Compare two papers' ASTs. | `diff` compares canonical ASTs by ID and structural path without fuzzy matching. |
| Compile and writing must be deterministic. | `compile`, `write`, generated code, and canonical JSON have fixed ordering, hashes, and no LLM calls. |
| Do not assume sections. | Source is discourse-native; sections are optional locator metadata only. |
| `gap` and diagnostics are not primitives. | Analyzer verdicts are forbidden in source and appear only as derived artifacts. |
| The DSL must be usable for theory, description, and fieldwork. | Minimal valid sources do not require estimands, causal graphs, regression models, or sectioned article structure. |

## 1. Design Commitments

### 1.1 Discourse-native, not section-native

AISS treats a text as an ordered discourse object grounded in source spans. A
source may be a sectioned article, a book, a dialogue, an interview transcript,
a fieldnote archive, a table, a figure, a dataset, or a code file.

Sections are optional locator metadata. They are not ontology.

The DSL MUST NOT require constructs such as `introduction`, `theory_section`,
`methods_section`, or `results_section`. AISS must be able to represent a text
such as Plato's *Republic*, a continuous interview transcript, or a fieldnote
corpus without first forcing it into modern article sections.

### 1.2 Theory, empirics, and coupling

The core AST has three conceptual regions:

```text
Theory AST
  concepts, claims, theoretical relations, mechanisms, scope claims

Empirical AST
  empirical materials, observations, results, artifacts, source objects

Coupling AST
  author-asserted or annotator-declared links between theory objects and
  empirical objects
```

The DSL source expresses what the text or annotator asserts. It does not express
the analyzer's verdict about those assertions.

### 1.3 Analyzer outputs are not source primitives

The following are forbidden as source primitives:

```text
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

These are deterministic outputs produced by tools after comparing AST objects.
They MUST NOT be written as first-class DSL declarations in `.aiss` source.

### 1.4 Progressive specificity

AISS supports light and heavy encodings.

A minimal valid source may declare only a source, spans, a few concepts, claims,
empirical materials, and author-asserted coupling links. More formal work may
add concept composition, value domains, executable artifacts, data manifests,
and method adapters.

The DSL SHOULD require more detail only when the source itself makes a stronger
or more specific claim. A theoretical essay should not be forced to declare an
estimand. A fieldwork account should not be forced to declare a regression
model. A causal research design may declare those details through later adapter
layers.

### 1.5 Determinism first

The same `.aiss` source, source objects, data artifacts, templates, adapter
versions, and AISS compiler version MUST produce the same canonical outputs on
different machines.

The determinism target is canonical JSON equality. Byte-for-byte equality is
required for normalized JSON, generated code, and deterministic writer output.

## 2. Terminology

| Term | Meaning |
|---|---|
| `.aiss source` | Human-editable DSL file. May be drafted by an agent, but is not trusted until compiled. |
| Source object | External object being represented: PDF text, transcript, book, dataset, code, table, figure, note. |
| Source span | Stable locator into a source object. A span is not necessarily a section. |
| Paper AST | Canonical compiled representation of the text's theory, empirics, and coupling. |
| Theory object | Concept, claim, theoretical relation, mechanism, or scope claim. |
| Empirical object | Material, observation, result, table, figure, case, quote, dataset, or code artifact. |
| Coupling object | Declared link that says how an empirical object is used for a theoretical object. |
| Derived artifact | Output produced by compile, lint, run, diff, or write. Not source. |
| Adapter | Deterministic plugin that maps selected AST objects into executable code or checks. |

## 3. Source File Model

### 3.1 File encoding

`.aiss` source files MUST be UTF-8. Newlines MUST normalize to LF during
compilation. The compiler MUST reject invalid UTF-8.

### 3.2 Comments

Line comments begin with `//` and continue to end of line. Block comments begin
with `/*` and end with `*/`. Comments are discarded during compilation and MUST
NOT affect canonical output.

### 3.3 Declaration order

Declaration order is not semantic. Forward references are allowed. The compiler
MUST canonicalize output by deterministic ordering rules, not source order.

The only order that may carry meaning is an explicit ordered field, such as
`spans: [...]` or `sequence: [...]`.

### 3.4 IDs

IDs MUST be stable and globally qualified within the source file.

```text
ID      = [a-z][a-z0-9_]*
QUALID  = ID "." ID ("." ID)*
```

Recommended pattern:

```text
<namespace>.<object_kind>_<short_name>
```

Examples:

```text
ding.concept_performative_governance
ding.claim_lc_hs_performative
plato.claim_justice_truth_debt
```

IDs MUST NOT encode line numbers, timestamps, random UUIDs, or machine paths.

### 3.5 Values

```text
STRING    = JSON string syntax
NUMBER    = decimal literal, parsed as decimal not binary float
BOOL      = true | false
NULL      = null
LIST      = [VALUE, ...]
MAP       = { key: VALUE, ... }
```

Numbers in canonical JSON MUST be rendered using decimal canonical form. If a
number cannot be represented deterministically, source SHOULD encode it as a
string and the adapter may parse it later.

## 4. Top-level Grammar

This grammar defines the canonical v0.3 source surface. It is intentionally
block-based to remain close to v0.2 while changing the ontology.

```text
program =
  version_decl
  (paper_decl
   | source_decl
   | span_decl
   | concept_decl
   | claim_decl
   | relation_decl
   | empirical_decl
   | observation_decl
   | coupling_decl
   | artifact_decl
   | adapter_decl)*

version_decl = "aiss" "version" STRING
```

Required first declaration:

```aiss
aiss version "0.3"
```

The compiler MUST reject files without a version declaration. It MUST reject a
v0.3 file that uses v0.2-only top-level keywords as formal declarations, unless
the compiler is explicitly invoked in legacy migration mode.

## 5. Provenance Layer

The provenance layer grounds all theory, empirical, and coupling objects in
source spans.

### 5.1 `paper`

`paper` declares the represented intellectual object. It is metadata, not a
section tree.

```aiss
paper ding.performative_state {
  title: "The Performative State"
  authors: ["Iza Ding"]
  year: "2022"
  language: "en"
  kind: "book"
  sources: [ding.src_book]
}
```

Fields:

| Field | Required | Type | Meaning |
|---|---:|---|---|
| `title` | yes | string | Canonical title. |
| `authors` | no | list[string] | Author names as text. |
| `year` | no | string | Publication year or known date string. |
| `language` | no | string | BCP-47 code when known. |
| `kind` | yes | string | `article`, `book`, `dialogue`, `transcript`, `fieldnotes`, `report`, `dataset`, or project-specific value. |
| `sources` | yes | list[id] | Source objects used by this paper. |
| `notes` | no | string | Non-semantic note. |

### 5.2 `source`

`source` declares an external object that spans can locate into.

```aiss
source ding.src_book {
  kind: "book_text"
  uri: "sources/ding_performative_state.txt"
  media_type: "text/plain"
  checksum: "sha256:..."
  locator_scheme: "char"
  canonicalization: "utf8_lf"
}
```

Fields:

| Field | Required | Type | Meaning |
|---|---:|---|---|
| `kind` | yes | string | `pdf_text`, `book_text`, `transcript`, `dataset`, `table`, `figure`, `code`, etc. |
| `uri` | yes | string | Relative project path or stable external URI. Relative paths are resolved against the `.aiss` file directory. |
| `media_type` | yes | string | MIME-like media type. |
| `checksum` | required for formal runs | string | `sha256:<hex>` hash of canonical source bytes. |
| `locator_scheme` | yes | string | `char`, `line`, `page`, `paragraph`, `stephanus`, `table_cell`, `figure_region`, `turn`, etc. |
| `canonicalization` | no | string | How bytes/text are normalized before hashing. |

Source objects MUST NOT use machine-specific absolute paths in formal fixtures.
Local absolute paths MAY be used in scratch authoring but MUST be rejected by
`aiss compile --strict`.

### 5.3 `span`

`span` declares a stable locator into a source object.

```aiss
span ding.s_intro_001 {
  source: ding.src_book
  locator: "char:1024-1350"
  kind: "paragraph"
  quote_hash: "sha256:..."
}
```

For a sectionless text:

```aiss
span plato.s_331c {
  source: plato.src_republic
  locator: "stephanus:331c-331d"
  kind: "dialogue_turn"
  quote_hash: "sha256:..."
}
```

Fields:

| Field | Required | Type | Meaning |
|---|---:|---|---|
| `source` | yes | id | Source object. |
| `locator` | yes | string | Stable locator under the source's locator scheme. |
| `kind` | no | string | `paragraph`, `dialogue_turn`, `table_cell`, `figure_caption`, `footnote`, etc. |
| `quote` | no | string | Short excerpt for human review. Not trusted as source of truth. |
| `quote_hash` | formal recommended | string | Hash of the canonical bytes/text covered by the locator. |

The compiler MUST treat `locator` as opaque unless the source's locator adapter
knows how to resolve it. Unknown locator schemes are allowed for compile but
MUST produce a deterministic warning in strict validation.

## 6. Theory AST Source Primitives

Theory primitives represent what the text says conceptually or theoretically.
They do not declare whether the text is correct.

### 6.1 `concept`

`concept` declares a term, category, construct, ideal type, mechanism component,
or conceptual object.

```aiss
concept ding.concept_performative_governance {
  term: "performative governance"
  definition: "governance action directed at producing the appearance of responsiveness"
  spans: [ding.s_intro_001]
  variants: ["performance", "performative state behavior"]
}
```

Fields:

| Field | Required | Type | Meaning |
|---|---:|---|---|
| `term` | yes | string | Canonical label. |
| `definition` | no | string | Source-grounded definition or concise encoding. |
| `spans` | yes | list[id] | Source spans grounding the concept declaration. |
| `variants` | no | list[string] | Surface forms used in the source. |
| `domain` | no | string | Substantive domain or population, not a value domain. |
| `attributes` | no | list[id] | Other concepts or empirical descriptors used in a decomposition. |
| `theta` | no | map | Optional formal composition table. |
| `theta_kind` | no | string | `binary`, `categorical`, `ordinal`, or project-specific. |
| `composition_rule` | no | string | `definition`, `typology`, `conjunction`, `threshold`, `family_resemblance`, etc. |

`theta` is optional. Many theoretical concepts are intentionally not decomposed
into a complete truth table. The absence of `theta` is not an error.

When `theta` is present, the compiler MUST canonicalize it but MUST NOT infer
missing rows unless a deterministic composition adapter is explicitly invoked.

### 6.2 `claim`

`claim` declares a proposition made, reported, questioned, or reconstructed in
the text.

```aiss
claim ding.claim_lc_hs_performative {
  kind: "theoretical"
  text: "Low capacity combined with high scrutiny produces pressure toward performative governance."
  concepts: [
    ding.concept_performative_governance,
    ding.concept_state_capacity,
    ding.concept_public_scrutiny
  ]
  modality: "asserted"
  spans: [ding.s_theory_014]
}
```

Fields:

| Field | Required | Type | Meaning |
|---|---:|---|---|
| `kind` | yes | string | `theoretical`, `descriptive`, `interpretive`, `empirical`, `mechanism`, `scope`, `normative`, `counterclaim`, etc. |
| `text` | yes | string | Canonical encoding of the claim. |
| `concepts` | no | list[id] | Referenced concepts. |
| `modality` | no | string | `asserted`, `tentative`, `questioned`, `reported`, `rejected`. |
| `spans` | yes | list[id] | Source spans grounding the claim. |
| `scope` | no | list[id] | Scope claims or concepts limiting applicability. |
| `subject` | no | id | Optional structured proposition subject; must reference a concept. |
| `predicate` | no | string | Optional structured proposition predicate such as `affects`, `requires`, `is_part_of`. |
| `object` | no | id | Optional structured proposition object; must reference a concept. |
| `polarity` | no | string | Optional structured polarity: `positive`, `negative`, `null`, `present`, or `absent`. |

`claim.kind` does not prescribe method. A descriptive claim is not weaker than a
causal claim; it simply belongs to a different semantic class.

The `subject`/`predicate`/`object`/`polarity` fields are an optional deterministic
claim-logic layer. They are not inferred from `text` by the compiler. When any
of these fields is present, all four SHOULD be present. A linter may then check
theory-level inconsistency mechanically. For example, two asserted claims with
the same `(subject, predicate, object, scope)` signature but contradictory
polarities such as `positive` vs. `null` or `present` vs. `absent` are
deterministically inconsistent. Claims with `modality: "reported"`,
`"questioned"`, or `"rejected"` are not treated as asserted commitments for this
rule.

Example:

```aiss
claim example.claim_scrutiny_increases_performance {
  kind: "theoretical"
  text: "Public scrutiny increases performative governance."
  concepts: [example.concept_public_scrutiny, example.concept_performative_governance]
  subject: example.concept_public_scrutiny
  predicate: "affects"
  object: example.concept_performative_governance
  polarity: "positive"
  modality: "asserted"
  spans: [example.s_theory]
}
```

### 6.3 `relation`

`relation` declares a source-grounded relationship among theory objects.

```aiss
relation ding.rel_performative_contrasts_substantive {
  type: "contrasts_with"
  from: ding.concept_performative_governance
  to: ding.concept_substantive_governance
  text: "Performative governance is contrasted with substantive governance."
  spans: [ding.s_typology_004]
}
```

Common `type` values:

| Type | Meaning |
|---|---|
| `defines` | One object defines or specifies another. |
| `subtype_of` | More specific concept under a broader concept. |
| `part_of` | Component relation. |
| `contrasts_with` | Explicit contrast or opposition. |
| `elaborates` | One claim elaborates another. |
| `entails` | One claim implies another in the author's argument. |
| `mechanism_for` | Mechanism claim connects to an outcome claim. |
| `scope_of` | A scope claim limits another claim. |
| `predicts` | Theory claim states an expected empirical pattern. |
| `responds_to` | Claim answers, rebuts, or modifies another claim. |

Fields:

| Field | Required | Type | Meaning |
|---|---:|---|---|
| `type` | yes | string | Relation type. |
| `from` | yes | id | Source object ID. |
| `to` | yes | id | Target object ID. |
| `text` | no | string | Canonical explanation. |
| `spans` | yes | list[id] | Source spans grounding the relation. |

A causal relation, when needed, is represented as a `claim` and/or `relation`
with an appropriate type such as `mechanism_for` or `predicts`. Causal inference
details are adapter-level concerns, not the default ontology.

## 7. Empirical AST Source Primitives

Empirical primitives represent what empirical material the text uses or reports.
They are intentionally broader than statistical data.

### 7.1 `empirical`

`empirical` declares a material object, case, dataset, passage, episode, table,
figure, quote set, field site, or archive.

```aiss
empirical ding.emp_field_observations {
  kind: "field_observation_set"
  label: "municipal environmental protection observations"
  description: "Field observations used as empirical material for performative governance."
  spans: [ding.s_methods_002, ding.s_case_011]
  artifacts: []
}
```

Fields:

| Field | Required | Type | Meaning |
|---|---:|---|---|
| `kind` | yes | string | `case`, `interview`, `field_observation_set`, `dataset`, `table`, `figure`, `archive`, `quote`, `document`, etc. |
| `label` | yes | string | Human-readable label. |
| `description` | no | string | Concise description. |
| `spans` | yes | list[id] | Source spans grounding the empirical object. |
| `artifacts` | no | list[id] | Data/code/table artifacts linked to this object. |

### 7.2 `observation`

`observation` declares an empirical pattern, result, quoted statement, table
entry, contrast, event, count, or reported finding.

```aiss
observation ding.obs_night_inspections {
  kind: "field_pattern"
  text: "Officials perform visible night inspections during public scrutiny."
  about: [ding.emp_field_observations]
  concepts: [ding.concept_performative_governance]
  spans: [ding.s_case_011]
}
```

Fields:

| Field | Required | Type | Meaning |
|---|---:|---|---|
| `kind` | yes | string | `field_pattern`, `quote`, `statistic`, `table_result`, `case_event`, `comparison`, `model_result`, etc. |
| `text` | yes | string | Canonical statement of the observation/result. |
| `about` | yes | list[id] | Empirical objects or artifacts this observation is about. |
| `concepts` | no | list[id] | Concepts the source associates with the observation. |
| `value` | no | value | Deterministic value when the result is structured. |
| `spans` | yes | list[id] | Source spans grounding the observation. |

`observation` is not a verdict. It records a reported empirical object or
pattern. Whether it supports a theory claim is handled through declared
coupling and later analysis.

### 7.3 `artifact`

`artifact` declares an external machine object used by empirical or runnable
analysis.

```aiss
artifact ding.art_table2_csv {
  kind: "data"
  uri: "data/table2.csv"
  media_type: "text/csv"
  checksum: "sha256:..."
  role: "input"
}
```

Fields:

| Field | Required | Type | Meaning |
|---|---:|---|---|
| `kind` | yes | string | `data`, `code`, `table`, `figure`, `model_output`, `appendix`, `template`. |
| `uri` | yes | string | Relative path or stable URI. |
| `media_type` | yes | string | MIME-like type. |
| `checksum` | required for formal runs | string | `sha256:<hex>`. |
| `role` | no | string | `input`, `declared_output`, `reference`, `template`. |

Artifacts are source inputs to deterministic operations. They are not generated
outputs unless declared as reference artifacts for comparison.

## 8. Coupling AST Source Primitives

Coupling primitives record asserted links between theory and empirics. They do
not declare the analyzer's assessment of the link.

### 8.1 `coupling`

```aiss
coupling ding.coup_obs_supports_claim {
  type: "supports"
  theory: ding.claim_lc_hs_performative
  empirical: ding.obs_night_inspections
  text: "The paper uses visible inspections as evidence for performative governance under scrutiny."
  asserted_by: "paper"
  spans: [ding.s_case_011, ding.s_discussion_003]
}
```

Fields:

| Field | Required | Type | Meaning |
|---|---:|---|---|
| `type` | yes | string | Role asserted for the link. |
| `theory` | yes | id | Claim, concept, or theory relation. |
| `empirical` | yes | id | Observation, empirical object, or artifact. |
| `text` | no | string | Canonical explanation of the asserted link. |
| `asserted_by` | yes | string | `paper`, `annotator`, `dataset_manifest`, `adapter`. |
| `spans` | yes | list[id] | Source spans grounding the coupling declaration. |

Common `type` values:

| Type | Meaning |
|---|---|
| `supports` | The source presents empirical material as supporting a theory claim. |
| `illustrates` | The material is presented as an example or illustration. |
| `operationalizes` | The material or observation is used as an empirical expression of a concept. |
| `tests` | The material/result is presented as testing a claim. |
| `motivates` | The material motivates a theory object. |
| `qualifies` | The material limits or qualifies a theory claim. |
| `contrasts` | The material is used to contrast with a theory claim or concept. |

The compiler MUST preserve `asserted_by`. A linter may later distinguish paper
assertions from annotator-added coupling, but that distinction is output, not a
source verdict.

## 9. Adapter Boundary

Specific methods are not core DSL primitives. They are deterministic adapters
that consume subsets of Paper AST.

Examples:

```text
regression_adapter(PaperAST, artifacts) -> generated R/Python code + results
interview_table_adapter(PaperAST, artifacts) -> coded quote table
case_trace_adapter(PaperAST, artifacts) -> process-trace matrix
concept_lattice_adapter(PaperAST) -> concept lattice output
```

Adapter requirements:

1. MUST declare an adapter ID and semantic version.
2. MUST declare which AST object types and artifact media types it consumes.
3. MUST produce canonical output with stable hashes.
4. MUST NOT call an LLM during formal execution.
5. MUST fail or skip deterministically when required inputs are missing.

### 9.1 `adapter`

An `.aiss` source may declare which deterministic adapters are allowed for
formal `run` or `emit-code`.

```aiss
adapter aiss.adapter_concept_lattice {
  version: "0.3.0"
  consumes: ["concept", "relation"]
  produces: ["code", "report"]
}
```

Declaring an adapter does not execute it. It only restricts what the formal run
is allowed to use.

## 10. Canonical Paper AST

`compile` converts `.aiss` source into canonical JSON. The exact JSON schema is
versioned as `aiss.paper_ast.v0.3`.

### 10.1 Required top-level JSON shape

```json
{
  "schema": "aiss.paper_ast.v0.3",
  "compiler": {
    "name": "aiss",
    "version": "0.3.0"
  },
  "input": {
    "source_hash": "sha256:...",
    "strict": true
  },
  "paper": {},
  "sources": [],
  "spans": [],
  "objects": [],
  "relations": [],
  "indices": {
    "theory": [],
    "empirical": [],
    "coupling": []
  }
}
```

### 10.2 Canonical ordering

Canonical JSON MUST use:

1. UTF-8.
2. LF newlines.
3. Two-space indentation.
4. No trailing spaces.
5. Object keys in schema-defined order, not insertion order.
6. Declaration arrays sorted by `id`, except fields whose names end with
   `_sequence`, which preserve explicit source order.
7. Diagnostics sorted by `(severity_rank, code, primary_id, message)`.
8. Diff operations sorted by `(path, op, id)`.

The compiler MUST NOT preserve arbitrary source declaration order.

### 10.3 Hashes

The compiler MUST compute:

| Hash | Input |
|---|---|
| `source_hash` | Normalized `.aiss` source after UTF-8/LF normalization and comment removal. |
| `ast_hash` | Canonical Paper AST excluding volatile tool metadata. |
| `artifact_hash` | Canonical bytes of each referenced artifact after declared canonicalization. |
| `writer_hash` | Canonical writer output bytes. |

Timestamps MUST NOT be embedded in canonical outputs.

## 11. Formal Operations

### 11.1 `compile`

```text
aiss compile input.aiss --json > build/paper.ast.json
```

Inputs:

```text
.aiss source
referenced source objects if --strict
referenced artifacts if --strict
compiler version
```

Output:

```text
canonical PaperAST JSON
```

Compile MUST:

1. Parse source.
2. Resolve all IDs.
3. Validate required fields.
4. Validate forbidden source primitives.
5. Canonicalize all objects.
6. Build theory, empirical, and coupling indices.
7. Emit canonical JSON or deterministic errors.

Compile MUST NOT:

1. Infer missing claims.
2. Judge support strength.
3. Create gap objects.
4. Call an LLM.
5. Depend on document section names.

### 11.2 `lint`

```text
aiss lint build/paper.ast.json --json > build/lint.json
```

Lint consumes Paper AST and emits deterministic diagnostics.

Diagnostic JSON shape:

```json
{
  "schema": "aiss.lint_report.v0.3",
  "ast_hash": "sha256:...",
  "diagnostics": [
    {
      "code": "AISS-REF-001",
      "severity": "error",
      "primary_id": "ding.coup_obs_supports_claim",
      "message": "Coupling references a missing empirical object.",
      "related_ids": []
    }
  ]
}
```

Lint diagnostics are derived artifacts. They are not `.aiss` source primitives.

Initial required diagnostic families:

| Family | Example |
|---|---|
| `AISS-SYN-*` | Syntax and parse errors. |
| `AISS-REF-*` | Missing or invalid references. |
| `AISS-PROV-*` | Missing source span or unresolved locator. |
| `AISS-CONCEPT-*` | Concept term drift, duplicate definitions, undeclared variants. |
| `AISS-CLAIM-*` | Claim conflicts, unscoped universal claims, ambiguous modality. |
| `AISS-EMP-*` | Empirical object lacks source grounding or artifact checksum. |
| `AISS-COUP-*` | Coupling link points to incompatible object classes or lacks source grounding. |
| `AISS-FORMAL-*` | Determinism contract violations. |

Lint MAY flag overclaim or unsupported coupling, but only through deterministic
rules over the AST. It MUST NOT use an LLM to decide those results.

### 11.3 `run`

```text
aiss run build/paper.ast.json --adapters adapters.lock --out build/run
```

`run` executes deterministic adapters over the AST and declared artifacts. It
also produces deterministic coupling assessments for declared theory-empirical
links when an explicit adapter or rule can evaluate the link.

Run output MUST include:

```json
{
  "schema": "aiss.run_report.v0.3",
  "ast_hash": "sha256:...",
  "adapter_lock_hash": "sha256:...",
  "units": [
    {
      "adapter": "aiss.adapter_concept_lattice",
      "version": "0.3.0",
      "status": "executed",
      "inputs": [],
      "outputs": []
    }
  ],
  "coupling_assessments": [
    {
      "coupling_id": "ding.coup_obs_supports_claim",
      "status": "not_assessable",
      "rule": null,
      "basis": [],
      "message": "No deterministic adapter is available for this coupling type."
    }
  ]
}
```

Allowed statuses:

```text
executed
skipped_missing_input
skipped_no_adapter
failed_deterministic
```

Allowed coupling assessment statuses:

```text
supported
partially_supported
not_supported
contradicted
not_assessable
skipped_missing_input
failed_deterministic
```

Coupling assessments are derived artifacts. They MUST NOT be declared in `.aiss`
source. A support status is valid only when produced by a deterministic rule or
adapter whose version is recorded in the run report. If no deterministic rule is
available, the correct output is `not_assessable`.

Run MUST NOT silently invent data, code, parameters, support criteria, or method
choices.

### 11.4 `emit-code`

```text
aiss emit-code build/paper.ast.json --target python --out build/code
```

`emit-code` generates deterministic code from the AST and adapter set. Generated
code is a derived artifact.

Code generation MUST:

1. Include a header with AISS version, adapter versions, AST hash, and target.
2. Use stable file names.
3. Use stable ordering of generated functions and checks.
4. Include no timestamps.
5. Include no machine-specific absolute paths.

If no adapter can generate runnable code for an object, the generator MUST emit
a deterministic manifest explaining the skip. It MUST NOT ask an agent to fill
in the missing method.

### 11.5 `diff`

```text
aiss diff paper_a.ast.json paper_b.ast.json --json > build/diff.json
```

Diff compares canonical ASTs.

Diff output shape:

```json
{
  "schema": "aiss.diff_report.v0.3",
  "left_ast_hash": "sha256:...",
  "right_ast_hash": "sha256:...",
  "operations": [
    {
      "op": "changed",
      "path": "/objects/ding.claim_lc_hs_performative/text",
      "left": "...",
      "right": "..."
    }
  ]
}
```

Matching rules:

1. Match by stable ID first.
2. If IDs differ and `same_as` metadata exists in both ASTs, match by `same_as`.
3. Otherwise report add/remove; do not use fuzzy semantic matching in formal diff.

Optional fuzzy or embedding-based comparison may exist as an Agent Harness tool,
but it is not `aiss diff`.

### 11.6 `write`

```text
aiss write build/paper.ast.json --template templates/reviewer_report.md \
  > build/report.md
```

`write` is deterministic rendering from AST plus template. It is not freeform
LLM writing.

Template language MUST be deliberately small:

```text
literal text
field interpolation
for loops over canonical arrays
if/else over explicit booleans or nonempty arrays
include by relative path with checksum
```

Template language MUST NOT include:

```text
LLM calls
network calls
random functions
current time/date
filesystem glob order without sorting
arbitrary shell execution
```

Writer output is a derived artifact. A later Agent Harness may polish it, but
that polished draft is outside the formal deterministic `write` operation unless
the edits are committed back into deterministic source/templates.

## 12. Validation Rules

### 12.1 Source-level validation

The compiler MUST reject:

1. Duplicate IDs.
2. Missing required fields.
3. References to undeclared IDs.
4. Top-level derived-output keywords such as `gap` or `diagnostic`.
5. Invalid UTF-8.
6. v0.2 declarations in v0.3 mode without explicit migration mode.

The compiler SHOULD warn:

1. Objects without source spans.
2. Source spans without `quote_hash`.
3. Source objects without checksums in non-strict mode.
4. Absolute local paths.
5. Unknown locator schemes.

### 12.2 AST-level lint rules

Initial v0.3 lint rules:

| Code | Severity | Rule |
|---|---|---|
| `AISS-REF-001` | error | Referenced ID does not exist. |
| `AISS-PROV-001` | warning/error in strict | Object lacks source spans. |
| `AISS-PROV-002` | warning | Span locator cannot be resolved by available locator adapter. |
| `AISS-CONCEPT-001` | warning | Same term declared in multiple concepts without relation. |
| `AISS-CONCEPT-002` | warning | Same concept has conflicting definitions. |
| `AISS-CLAIM-001` | warning | Claim references a concept not otherwise grounded. |
| `AISS-CLAIM-002` | warning | Claim partially uses structured proposition fields but omits one of `subject`, `predicate`, `object`, `polarity`. |
| `AISS-CLAIM-003` | warning | Structured claim polarity is outside the deterministic polarity vocabulary. |
| `AISS-CLAIM-010` | error | Two asserted structured claims share the same `(subject, predicate, object, scope)` signature with contradictory polarity. |
| `AISS-EMP-001` | warning | Empirical object has no artifact or observation linked to it. |
| `AISS-EMP-002` | error in strict run | Runnable artifact lacks checksum. |
| `AISS-COUP-001` | error | Coupling theory endpoint is not a theory object. |
| `AISS-COUP-002` | error | Coupling empirical endpoint is not an empirical object. |
| `AISS-COUP-003` | warning | Claim has empirical concepts but no declared coupling. |
| `AISS-FORMAL-001` | error | Canonical JSON cannot be reproduced from the same input. |

Support-strength diagnostics MAY be added later, but they must be defined as
deterministic comparisons over explicit AST fields.

## 13. Migration from v0.2

v0.2 constructs are not formal aliases in v0.3.

| v0.2 | v0.3 migration |
|---|---|
| `attribute` | Usually `concept` attribute metadata or empirical descriptor; not a top-level default primitive. |
| `concept` with `theta` | `concept` with optional `theta`, `theta_kind`, and `composition_rule`. |
| `causal` | `claim` plus `relation` such as `mechanism_for` or `predicts`; method details go to adapters. |
| `bridge` | `coupling` when it records author-asserted theory-empirical linkage; analyzer verdicts become lint/run outputs. |
| `model` | `paper` plus compiler-generated Paper AST indices. |
| `check` and `derive` | CLI operations, not source declarations. |

Migration mode MAY read v0.2 files and emit v0.3 candidate source. Migration
output MUST be treated as a generated patch requiring review before formal
compile.

## 14. Examples

### 14.1 Minimal sectionless theory text

This example is illustrative only. It shows that the source is grounded in
spans, not article sections.

```aiss
aiss version "0.3"

paper plato.republic {
  title: "Republic"
  authors: ["Plato"]
  year: "unknown"
  language: "grc"
  kind: "dialogue"
  sources: [plato.src_republic]
}

source plato.src_republic {
  kind: "dialogue_text"
  uri: "sources/republic.txt"
  media_type: "text/plain"
  checksum: "sha256:..."
  locator_scheme: "stephanus"
}

span plato.s_331c {
  source: plato.src_republic
  locator: "stephanus:331c-331d"
  kind: "dialogue_turn"
  quote_hash: "sha256:..."
}

concept plato.concept_justice {
  term: "justice"
  spans: [plato.s_331c]
}

claim plato.claim_justice_definition_candidate {
  kind: "theoretical"
  text: "Justice is considered through a candidate definition in the dialogue."
  concepts: [plato.concept_justice]
  modality: "reported"
  spans: [plato.s_331c]
}
```

### 14.2 Theory, empirics, and coupling

```aiss
aiss version "0.3"

paper example.paper {
  title: "Example Paper"
  authors: ["Example Author"]
  year: "2026"
  language: "en"
  kind: "article"
  sources: [example.src_text]
}

source example.src_text {
  kind: "article_text"
  uri: "sources/example.txt"
  media_type: "text/plain"
  checksum: "sha256:..."
  locator_scheme: "char"
}

span example.s_theory {
  source: example.src_text
  locator: "char:100-260"
  kind: "paragraph"
  quote_hash: "sha256:..."
}

span example.s_empirical {
  source: example.src_text
  locator: "char:800-980"
  kind: "paragraph"
  quote_hash: "sha256:..."
}

concept example.concept_public_scrutiny {
  term: "public scrutiny"
  definition: "Public attention and pressure directed at state action."
  spans: [example.s_theory]
}

claim example.claim_scrutiny_changes_behavior {
  kind: "theoretical"
  text: "Public scrutiny changes bureaucratic behavior."
  concepts: [example.concept_public_scrutiny]
  modality: "asserted"
  spans: [example.s_theory]
}

empirical example.emp_case_material {
  kind: "case"
  label: "case material"
  description: "Empirical material presented in the example paper."
  spans: [example.s_empirical]
}

observation example.obs_visible_action {
  kind: "case_event"
  text: "Officials shifted toward visible public actions during scrutiny."
  about: [example.emp_case_material]
  concepts: [example.concept_public_scrutiny]
  spans: [example.s_empirical]
}

coupling example.coup_case_supports_claim {
  type: "supports"
  theory: example.claim_scrutiny_changes_behavior
  empirical: example.obs_visible_action
  text: "The paper presents the case event as support for the scrutiny claim."
  asserted_by: "paper"
  spans: [example.s_empirical]
}
```

## 15. Non-goals for v0.3

The following are intentionally out of core scope:

1. Full method ontology.
2. Causal identification language.
3. Statistical model specification.
4. LLM extraction protocol.
5. Agent Harness orchestration.
6. Peer-review style judgment by model.
7. Section-classification pipeline.

These may be separate adapters, skills, or Harness workflows. They must not
become assumptions in the core DSL.

## 16. Implementation Checklist

A v0.3 implementation is conformant only if it can:

1. Parse `.aiss` v0.3 source.
2. Reject forbidden derived-output primitives in source.
3. Compile to canonical Paper AST JSON.
4. Produce the same canonical JSON across machines given the same inputs.
5. Lint with deterministic diagnostic codes.
6. Run deterministic adapters and emit `not_assessable` rather than guessing
   when evidence support cannot be evaluated by code.
7. Emit deterministic code or a deterministic skip manifest.
8. Diff two ASTs without fuzzy matching.
9. Write deterministic reports from templates.
10. Treat section headings as optional locator metadata.
11. Keep method-specific execution behind deterministic adapters.
12. Keep LLM/Agent behavior outside compile, lint, run, diff, and write.
