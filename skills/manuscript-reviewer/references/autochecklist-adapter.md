# AutoChecklist and PackyAPI Adapter

AutoChecklist is not an AI4SS skill. It supplies the fixed checklist data model
and the default CLI scorer path. The default `manuscript-reviewer` run calls
`autochecklist score`; PackyAPI Fable is the AutoChecklist CLI's LLM backend.
A local OpenAI-compatible shim is used only because PackyAPI Fable expects the
system prompt at the top level and rejects AutoChecklist's default
`temperature` and structured-output transport parameters.

## Dependency

Install AutoChecklist in the runtime that will execute the scorer:

```bash
python3 -m pip install autochecklist
```

The default scorer calls:

```bash
autochecklist score \
  --checklist checklist.json \
  --data data.jsonl \
  --output scores.jsonl \
  --overwrite \
  --scorer item \
  --scorer-model claude-fable-5 \
  --provider openai \
  --base-url <local-packyapi-fable-shim> \
  --api-format chat \
  --scorer-prompt scorer_prompt.md \
  --input-key input \
  --target-key target
```

The optional package API fallback imports:

```python
from autochecklist import Checklist, ChecklistItem, ChecklistScorer
```

It uses a fixed checklist:

```python
Checklist(
    items=[ChecklistItem(id=item_id, question=question, category=suite_code)],
    source_method="dp16276_tdd_fixed",
    generation_level="corpus",
)
```

Then it calls:

```python
score = ChecklistScorer(...).score(checklist, target=manuscript_text, input=metadata)
```

For PackyAPI, pass the provider key by environment variable name instead of
hard-coding secrets. The default AI4SS CLI path is AutoChecklist CLI plus
PackyAPI Fable:

```bash
manuscript-reviewer review \
  --manuscript draft.md \
  --outdir review
```

The default backend is `cli`, the default model is `claude-fable-5`, the
configured provider base URL is `https://www.packyapi.com/v1`, and the default
key variable is `PACKYCODE_CODEX_KEY`. At runtime, the wrapper starts a local
shim and passes that shim as AutoChecklist CLI's temporary `--base-url`; the
shim forwards to PackyAPI Fable. The snapshot records the variable name and
whether it was set, never the key.

## Prompt Policy

The scorer prompt is evidence constrained:

- answer from the manuscript text and explicit metadata only
- ignore conversation history, memory, and prior project knowledge
- answer `YES` only when the criterion is visible enough in the manuscript
- answer `NO` when absent, merely implied, ambiguous, or contradicted
- do not score reader-test items unless reader evidence is supplied

## Scoring Modes

The default is `--scorer-mode item`, which makes AutoChecklist score each
checklist item in a separate LLM call. This is the correct full-review setting
for the fixed 302-item manuscript checklist because the batch scorer must fit
all selected items in one model response. Use `--scorer-mode batch` only for
cheap, explicitly scoped drafting probes such as `--suites TITLE,ABS`. Use
`--backend api` only when testing the upstream AutoChecklist package API
directly with a provider that accepts its request shape.

## Limitations

The scorer provides yes/no observations and optional reasoning. It does not own
AI4SS workflow state, `.aiss` declarations, reader-test evidence, or repair
execution. Those remain the responsibility of the skill wrapper and downstream
AI4SS skills.
