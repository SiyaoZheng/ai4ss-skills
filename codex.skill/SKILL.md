---
name: codex
description: Run OpenAI Codex CLI to delegate coding tasks to GPT-5.3-codex. Use when the user says "codex", "/codex", "codex resume", or wants a second AI opinion on code. Also trigger when the user asks to run, resume, or fork a Codex session, or wants to use GPT models for code analysis, refactoring, or automated editing. Do NOT trigger for general coding tasks that Claude should handle directly.
---

# Codex CLI Skill

Codex CLI is OpenAI's terminal-based coding agent. This skill delegates tasks to it via `codex exec` (non-interactive mode), where Claude constructs the command and summarizes the result.

> **Attribution**: This skill builds upon the original [codex skill](https://github.com/davila7/claude-code-templates/tree/main/cli-tool/components/skills/development/codex) by [@davila7](https://github.com/davila7). Key additions: updated model table (GPT-5.3-codex), streamlined interaction (no AskUserQuestion overhead), additional CLI flags documentation, and bilingual trigger support.

## When To Use

- **Second opinion**: User wants a different model's take on code quality, architecture, or bugs
- **Codex-specific features**: Sandboxed execution, session resume/fork, structured JSON output
- **User explicitly asks**: "codex", "use codex", "resume codex session"

## Running a Task

1. Pick the sandbox mode the task requires (read-only is the safe default):

| Task | Sandbox | Command Pattern |
|------|---------|----------------|
| Analysis / review | `read-only` | `codex exec --skip-git-repo-check -s read-only "prompt" 2>/dev/null` |
| Apply edits | `workspace-write` | `codex exec --skip-git-repo-check --full-auto "prompt" 2>/dev/null` |
| Network / broad access | `danger-full-access` | `codex exec --skip-git-repo-check -s danger-full-access --full-auto "prompt" 2>/dev/null` |

2. Always include `--skip-git-repo-check` — Codex normally requires a git repo, but we're running it from within Claude Code's working directory where this check can fail.

3. Always append `2>/dev/null` — Codex streams thinking/progress tokens to stderr. Suppressing stderr keeps Claude's output clean. Only show stderr when debugging.

4. Use `--full-auto` when the task involves edits — it enables workspace-write sandbox with automatic approval for file changes. Without it, Codex pauses for approval that nobody can give in non-interactive mode.

5. Default model: `gpt-5.3-codex` with `xhigh` reasoning effort. Override with `-m <model>` or `--config model_reasoning_effort="<level>"`.

### Complete Example

```bash
codex exec --skip-git-repo-check \
  -m gpt-5.3-codex \
  --config model_reasoning_effort="xhigh" \
  -s read-only \
  "Review code/R/processing.R for potential bugs and edge cases" \
  2>/dev/null
```

### Changing Working Directory

Use `-C <DIR>` to run Codex in a different directory:

```bash
codex exec --skip-git-repo-check -C /path/to/project --full-auto "fix the failing tests" 2>/dev/null
```

## Resuming a Session

Codex persists sessions. To continue a previous one:

```bash
# Pass prompt as argument (preferred):
codex exec --skip-git-repo-check resume --last "now fix the edge cases you found" 2>/dev/null

# Or pipe via stdin:
echo "now fix the edge cases" | codex exec --skip-git-repo-check resume --last 2>/dev/null
```

- `--last` resumes the most recent session in the current directory. Add `--all` to search across directories.
- Resumed sessions inherit their original model, sandbox, and reasoning effort — do not pass config flags unless the user explicitly wants to override.
- All flags go between `exec` and `resume`.
- After Codex completes, remind the user they can say "codex resume" to continue.

## Models

| Model ID | Role | API Pricing (input/output per 1M tokens) |
|----------|------|------------------------------------------|
| `gpt-5.3-codex` | Flagship — best agentic coding | $1.75 / $14.00 |
| `gpt-5.3-codex-spark` | Near-instant realtime (Pro only) | — |
| `gpt-5.2-codex` | Previous gen, still capable | $1.75 / $14.00 |
| `gpt-5.1-codex-max` | Extended reasoning | $1.25 / $10.00 |
| `gpt-5.1-codex` | Older flagship | $1.25 / $10.00 |

All models support 400K context. Cached input gets 90% discount ($0.175/M for 5.3-codex).

**Reasoning effort**: `--config model_reasoning_effort="<level>"`
- `xhigh` — deep analysis (default)
- `high` — refactoring, architecture
- `medium` — standard feature work
- `low` — formatting, docs, quick fixes

## Useful Flags

| Flag | Purpose |
|------|---------|
| `--json` | JSONL event stream — useful for parsing Codex output programmatically |
| `-o <path>` | Write final assistant message to a file |
| `--output-schema <path>` | Constrain response to a JSON Schema |
| `-i <image>` | Attach image(s) to prompt |
| `--search` | Enable live web search |
| `--ephemeral` | Don't persist session (one-off tasks) |
| `--add-dir <path>` | Grant write access to additional directories beyond workspace |

## Error Handling

- If `codex exec` exits non-zero, report the error and ask for direction — do not retry automatically.
- Before using `--full-auto` or `danger-full-access`, confirm with the user unless they already granted permission.
- If output contains warnings or partial results, summarize and ask how to proceed.
