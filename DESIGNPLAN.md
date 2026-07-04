# README Design Plan

This plan supersedes the earlier abstract `gpt-image-2` asset plan.

The first generated README images were removed because they did not carry
enough project-specific meaning. The homepage should use visuals only when they
are auditable from the repository itself: exact Markdown tables, Mermaid
diagrams when they clarify structure, badges, code blocks, links to real
reports, and committed SVG brand assets with literal project semantics.

## Goal

The README should make the project legible as a methodology-enforcing AI4SS
research factory:

- skills are the operator interface,
- `.aiss` is the computable research object,
- validators, eval packets, and ledgers are the trust layer,
- the output is inspectable research state, not final scholarly prose.

The homepage should look intentional. Its design should come from information
architecture and a small number of meaningful brand assets, not decorative
images.

## Visual Policy

Use a logo and header image when they are exact, semantic, and committed as
editable SVG. Do not use generated bitmap illustrations for the README unless
the image is specific, inspectable, and materially clearer than text.

Avoid:

- abstract AI-generated factory scenes,
- fake dashboards with non-auditable marks,
- icons or illustrations that merely decorate a section,
- generated text inside images,
- local image assets that repeat what a table already says.

Prefer:

- a stable SVG logo that encodes the `.aiss` research-object kernel,
- a semantic SVG header that shows the real factory pipeline,
- compact comparison tables,
- Mermaid diagrams with exact labels,
- short code blocks for `.aiss` and validation commands,
- `<details>` blocks for secondary skill lists,
- links to actual eval reports and fixtures,
- screenshots only when they show a real rendered artifact or tool output.

## Layout

Keep the README organized around the reader's decision path.

1. **Top definition**
   - Show the committed SVG logo above the title.
   - Name the repository.
   - State the promise: turn agent conversations into computable
     social-science research objects.
   - Link to the main sections.
   - Add the committed SVG header immediately after the badge/nav block.

2. **From Chat Output To Research State**
   - Use the two-column transformation table.
   - Make clear that the system produces inspectable state before prose.

3. **Choose Your Path**
   - Give three entrypoints: try, understand, audit.
   - Keep this section short enough to scan on the first screen.

4. **Factory Architecture**
   - Explain the three layers: skills, `.aiss`, validation/trust.
   - Use prose and tables unless a Mermaid diagram adds real clarity.

5. **Research Workflow**
   - Show the stage table from rough topic to bounded handoff.
   - Keep every stage tied to a primary skill, canonical artifact, and gate.

6. **The `.aiss` Research Object**
   - Show the minimal `.aiss` skeleton.
   - Name `compile`, `lint`, and `run` as the deterministic entrypoints.
   - Explain sidecars as projections, not a second workflow language.

7. **Start**
   - Keep install commands and first prompts close to the top.

8. **Skills**
   - Show the factory chain first.
   - Put specialist and utility skills in `<details>`.

9. **Evidence**
   - Keep exact numbers in Markdown.
   - Link to the real reports.
   - State that evaluations measure structure and boundary discipline, not
     empirical truth or expert-review replacement.

10. **Validate, Boundaries, Repository Layout, Contributing, Cite, License**
    - Keep these sections textual and exact.

## Brand Assets

The README has two committed SVG assets:

```text
docs/assets/readme/ai4ss-logo.svg
docs/assets/readme/ai4ss-header.svg
```

The logo should stay compact and recognizable at small sizes. It represents a
`.aiss` research object connected to skills, validators, decisions, and bounded
claims.

The header should act as the README head image. It should show the real
research-factory path:

```text
inputs -> skills -> .aiss -> validators -> bounded handoff
```

Both assets must remain truthful diagrams, not atmospheric art. If their labels
or architecture become stale, update the SVG instead of replacing it with a
generic generated image.

## README Asset Rule

`docs/assets/readme/` should contain only assets that pass all of these checks:

1. It shows a real repository object, report, rendered artifact, or exact
   diagram that cannot be expressed better in Markdown.
2. It has no fake claims, fake metrics, fake UI labels, or generated tiny text.
3. It can be regenerated or audited from committed sources.
4. It improves comprehension for a first-time reader.

If an asset fails any check, remove it and express the idea with Markdown.

## Validation Checklist

Before publishing README changes:

```bash
python3 scripts/validate_skillpack_workflow.py
python3 scripts/validate_methodology_foundations.py docs/methodology_source_matrix.csv
python3 scripts/validate_ai_use_ledger.py docs/ai_use_ledger.csv
python3 scripts/validate_ai4ss_model.py docs/examples/research_model.aiss
python3 scripts/validate_literature_evidence_compile.py skills/literature-matrix/examples/valid_literature_matrix.csv
python3 scripts/validate_analysis_readiness.py skills/research-analysis-runner/examples/valid_analysis_readiness_check.csv
python3 scripts/run_factory_level_eval.py --clean
```

Also check:

- README local links resolve,
- no deleted assets remain referenced,
- `git diff --check` is clean,
- unrelated concurrent work is not staged accidentally.
