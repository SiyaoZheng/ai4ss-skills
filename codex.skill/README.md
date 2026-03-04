# Codex Integration for Claude Code

Enable Claude Code to invoke the OpenAI Codex CLI (`codex exec` and session resumes) for automated code analysis, refactoring, and editing workflows.

## Attribution

This skill is based on the original [codex skill](https://github.com/davila7/claude-code-templates/tree/main/cli-tool/components/skills/development/codex) by [@davila7](https://github.com/davila7) from the [claude-code-templates](https://github.com/davila7/claude-code-templates) project.

Key changes in this version:
- Updated model table (GPT-5.3-codex family)
- Streamlined interaction — no `AskUserQuestion` overhead per invocation
- Additional CLI flags documentation (`--json`, `-o`, `--search`, `--ephemeral`, etc.)
- Direct execution without per-call effort/model prompts

## Prerequisites

- `codex` CLI installed and available on `PATH`
- Codex configured with valid credentials
- Verify: `codex --version`

## Installation

```bash
# Copy to Claude Code skills directory
cp -r codex.skill ~/.claude/skills/codex
```

## Usage

In Claude Code, say:
- `codex review this file for bugs`
- `/codex analyze the test coverage`
- `codex resume` (to continue a previous session)

See `SKILL.md` for complete operational instructions.
