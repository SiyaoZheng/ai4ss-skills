# AI-Use Ledger Schema

Canonical path for shared or manuscript-adjacent artifacts: `docs/ai_use_ledger.csv`.

Validate with:

```bash
python3 scripts/validate_ai_use_ledger.py docs/ai_use_ledger.csv
```

| column | meaning |
|---|---|
| `tool_model` | Tool, model, skill, or agent used |
| `task` | Bounded task performed |
| `inputs` | Files, snippets, or sources supplied |
| `outputs` | Files or tables produced |
| `human_review` | What the researcher checked or changed |
| `disclosure_location` | manuscript_note, appendix, cover_letter, classroom_note, or not_applicable |
| `confidentiality_approval_status` | cleared, redacted, needs_approval, or do_not_share |

Validation is a readiness gate. Rows with `needs_approval` or `do_not_share` are not ready for external sharing or submission.
