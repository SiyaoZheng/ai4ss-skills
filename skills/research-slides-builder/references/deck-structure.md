# Deck Structure

Use this reference when planning a research presentation.

## Slide Map Schema

| column | meaning |
|---|---|
| `slide_id` | Stable slide number or id |
| `role` | title, agenda, motivation, question, data, design, result, mechanism, robustness, limitation, discussion, boundary |
| `claim` | One claim or task for the slide |
| `source_artifact` | Table, figure, matrix row, audit output, or author note |
| `visual` | Chart, table, diagram, quote, workflow, or blank |
| `risk` | unsupported claim, overclaim, overload, privacy, unclear unit |
| `action` | create, revise, split, delete, verify |

Use `not_applicable` rather than blank `source_artifact` for title, agenda, and discussion slides. All other slide roles need a concrete table, figure, log, matrix row, or author note.

## Research Talk Pattern

1. Title and question.
2. Why the question matters in one concrete setting.
3. What is hard to identify or measure.
4. Data and sample.
5. Design or workflow.
6. Main result visual.
7. Diagnostics and robustness.
8. Mechanism or interpretation boundary.
9. Contribution.
10. Limitations and next step.

## Teaching Demo Pattern

1. Problem researchers recognize.
2. Agent/task setup or research workflow.
3. Input prompt or data artifact.
4. Tool/action trace.
5. Output artifact.
6. Error or uncertainty.
7. Verification checkpoint.
8. What students should reuse.

## One-Claim Rule

Each slide should have one main claim. If a slide needs two claims, split it or make one a footnote.

Examples:

- Good: "The analysis sample retains 285 cities after policy-list matching."
- Too broad: "The data are clean and support the analysis."
