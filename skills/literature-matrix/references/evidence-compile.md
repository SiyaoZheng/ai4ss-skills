# Literature Evidence Declarations

Use deterministic evidence compilation only when a verified source row creates,
supports, challenges, or revises a `.aiss` model element. The ordinary
evidence declarations remain the screening, extraction, and source-status
record. Derived Markdown is not workflow state and must not be used as a handoff
contract.

## Declaration Contract

Write model-affecting source evidence directly into `.aiss` declarations:

- `paper`
- `source`
- `span`
- `claim`
- `relation`
- `concept`
- `causal`
- `bridge`
- `check`
- `decision`

Then validate the updated research object:

```bash
python3 scripts/validate_ai4ss_model.py .ai4ss/research_model.aiss
```

The validator checks the `.aiss` file through `aiss.py compile`, `aiss.py lint`,
and `aiss.py run`. It does not validate CSV or Markdown projections.

## Evidence Fields

For source evidence that affects model elements, preserve:

- stable source ids;
- exact source locators;
- span ids and quote hashes when available;
- target model, concept, causal, or bridge ids;
- source-status checks;
- assumption or claim-boundary declarations when interpretation is unresolved.

Use `not_applicable:<reason>` only inside `.aiss` declaration fields when a
source is bibliographic context, a negative screen, or not intended to affect the
research model.

## Boundary

Compiled evidence is not a literature-review paragraph and not an identification
certification. It is a stable research-model fragment that downstream skills can
check, diagnose, merge, reject, or route to source/design repair.
