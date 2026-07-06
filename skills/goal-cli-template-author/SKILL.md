---
name: goal-cli-template-author
description: Use when adding or maintaining reusable goal-cli templates, artifact recipes, tik oracle scripts, example goal.toml files, or project-type setup guidance.
version: 1.0.0
---

# goal-cli Template Author

Use this skill when maintaining reusable `goal-cli` setup material rather than
configuring one user's project. The audience is future agents and advanced
users who need a reliable recipe for a project family.

Do not use this skill to connect an ordinary target project to `goal-cli`. For
that job, use `goal-cli-project-setup`. This skill only maintains the reusable
material that `llms.txt` and `goal-cli-project-setup` point agents toward.

Template work includes:

- new example `goal.toml` files;
- project-type setup docs;
- deterministic tik oracle scripts;
- producer wrapper templates;
- reusable prompts;
- updates to `llms.txt`, `docs/skills.md`, README links, or skill content.

## Design Principles

- The artifact is the control point. Each template must name one canonical
  artifact shape.
- Producer first. A template is incomplete unless it explains how the artifact
  is rebuilt from source.
- Tik and tok stay separated. Tik reviews the artifact; tok success is measured
  by runtime-audited source changes.
- Defaults should be safe for non-experts: narrow write scopes, protected
  generated dirs, dry-run validation before real heartbeats.
- One-prompt setup material must be usable by an agent that has never seen the
  target project and by a user who cannot debug `goal.toml` by hand.
- Templates must include install/verification steps and a failure path for
  missing commands, failed producers, missing artifacts, and failed doctor
  checks.
- Deterministic checks beat model review when they can reject failures clearly.
- Examples should be runnable from a clean checkout or should state exactly
  which target project files they expect.

## Template Workflow

### 1. Define the Project Family

Write down:

- artifact kind: PDF, site, workbook, report, benchmark, package, model metric;
- expected source directories;
- generated directories;
- likely build tools;
- whether a deterministic tik oracle is possible;
- what the user can inspect directly.

Do not create a generic "agent task" template. Every template must be tied to
an artifact family.

### 2. Specify Producer Discovery

Each template must tell agents how to find or create the producer:

- check `Makefile`, `justfile`, `package.json`, `pyproject.toml`, `README`,
  CI workflows, and `scripts/`;
- prefer an existing stable command;
- otherwise create a wrapper such as `scripts/goal_producer.sh`;
- require the wrapper to verify artifact existence, size, and optionally sha256.

Include one minimal producer wrapper when useful.

### 3. Specify Tik

For `oracle` templates, provide or describe a script that returns a parseable
goal-cli verdict. The script should check the artifact and print a JSON object
with:

```json
{
  "artifact_ready": false
}
```

For `checklist` templates, use the same command-backed contract as `oracle`,
but reserve the provider name for checklist-style reviews that should show up
as `checklist` in tik ledgers and state.

For `codex_file` and `claude_code_file` templates, write a concise
artifact-only prompt. If a slash skill is required, it must be the first line
of the prompt.

For `api` templates, state the OpenAI package plus Packy/OpenAI-compatible API
key requirements. The default model is `claude-fable-5` through PackyAPI, and
credentials may come from `PACKYAPI_API_KEY`, `PACKYCODE_CODEX_KEY`,
`OPENAI_API_KEY`, or `~/.config/goal-cli/api.env`. Keep `store = false` unless
the template explicitly requires stored API responses. If a local skill is
required, set `tik.skill` instead of putting a slash command in the prompt.

### 4. Specify Tok Boundaries

Every template must include:

- recommended audited source `write_dirs`;
- generated dirs to protect;
- source dirs that look tempting but should stay read-only;
- a tok prompt template that references `{tik_review_path}` as the standard to
  meet;
- explicit language requiring tok to make source changes so the next rebuilt
  artifact answers tik's blocking objections;
- a note that tok cannot declare the artifact complete.

### 5. Provide Validation Commands

Every template must include:

```bash
goal-cli validate
goal-cli doctor
goal-cli run --dry-run
```

Add smoke checks when relevant:

```bash
goal-cli doctor --smoke-codex-goal
goal-cli doctor --smoke-codex-app-server
goal-cli doctor --smoke-codex-goal --smoke-codex-file-tik
goal-cli doctor --smoke-codex-app-server --smoke-codex-file-tik
```

If a template includes a tik oracle script, include a direct oracle command and
the expected verdict shape.
If it includes a checklist runner, use `provider = "checklist"` and document
that `goal-cli doctor` checks the command statically.

If a template recommends unattended progress, include the system-level
heartbeat command and state that each tick still runs exactly one heartbeat:

```bash
goal-cli heartbeat install --every-minutes 30 --max-minutes 600
goal-cli heartbeat status
```

## File Locations

Use these repository locations unless a future repository convention replaces
them:

```text
skills/goal-cli-project-setup/SKILL.md
skills/goal-cli-template-author/SKILL.md
docs/skills.md
examples/<project-family>/goal.toml
examples/<project-family>/README.md
scripts/ (only for repository-level tooling)
llms.txt
```

Project-specific producer wrappers should be described in templates, not added
to this repository unless they are examples.

## Example Template Shape

```toml
name = "research-pdf-ready"
state_dir = ".goal"
runs_dir = ".goal/runs"

[artifact]
path = "output/full_paper.pdf"
copy_as = "full_paper.pdf"

[producer]
command = "scripts/goal_producer.sh"

[tik]
provider = "codex_file"
timeout_seconds = 1800
max_file_size_bytes = 25000000
max_output_tokens = 4096

[tik.verdict]
ready_field = "artifact_ready"
required_fields = ["artifact_ready"]

[tok]
provider = "codex_goal"
sandbox = "workspace-write"
write_dirs = ["writing", "src"]
codex_features = ["goals"]

# Use provider = "codex_app_server" for Codex app-server stdio instead of
# codex exec, or provider = "claude_code_goal" for Claude Code.

[safety]
generated_dirs = ["output", "build", "cache"]
max_blocker_repeats = 3
```

## Review Checklist

Before finishing template work, verify:

- frontmatter `name`, `description`, and `version` are present for every skill;
- docs link to new skills from README or `docs/skills.md`;
- `llms.txt` lists the current agent entrypoints;
- one-prompt setup docs explain how to install or verify `goal-cli`;
- non-expert setup docs include exact validation commands and recovery behavior
  when those commands fail;
- no template tells tok to edit generated outputs;
- no runtime prompt asks a human to approve or clarify during the loop;
- examples use current public config fields from `docs/config-schema.md`;
- validation commands are included;
- repository tests still pass or any failure is reported with exact output.

## Definition of Done

- The reusable recipe can be followed by an agent that has never seen the
  project before.
- The recipe explains artifact choice, producer synthesis, tik choice, tok
  write scopes, validation, and first heartbeat.
- Documentation points users to the correct skill for their role.
- The change is committed with the docs and examples needed to use it.
