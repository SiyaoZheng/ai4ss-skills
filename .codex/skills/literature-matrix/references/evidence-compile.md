# Literature Evidence To AI4SS Compile

Use deterministic evidence compilation only when a verified source row creates,
supports, challenges, or revises a `.aiss` model element. The ordinary
literature matrix remains the screening and extraction table; the structured
evidence markdown is the compiler input.

## Compiler Contract

The local wrapper must call the repository `compile_evidence.py` script. Do not
fork a second compiler.

```bash
python3 .codex/skills/literature-matrix/scripts/compile_literature_evidence.py \
  docs/literature_evidence.md \
  docs/literature_evidence.aiss
```

Then validate the matrix-level linkage:

```bash
python3 scripts/validate_literature_evidence_compile.py docs/literature_matrix.csv
```

The validator recompiles `evidence_table_path`, compares the generated output
byte-for-byte with `compiled_ai4ss_path`, and checks the compiled file with
`aiss.py compile` and `aiss.py lint`.

## Matrix Fields

For rows that affect model elements, fill:

- `evidence_table_path`
- `compiled_ai4ss_path`
- `evidence_compile_status`
- `evidence_compile_command`

Use `not_applicable:<reason>` when a source row is bibliographic context, a
negative screen, or not intended to affect the research model.

## Boundary

Compiled evidence is not a literature-review paragraph and not an identification
certification. It is a stable research-model fragment that downstream skills can
check, diagnose, merge, reject, or route back to the author.
