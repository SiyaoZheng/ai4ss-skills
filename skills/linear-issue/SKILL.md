---
name: linear-issue
description: USE PROACTIVELY — any time the user wants to log, track, file, or plan work, create a Linear issue. Trigger on ANY mention of creating/managing tasks, bugs, issues, pipelines, analyses, papers, infrastructure work, or follow-ups. Even if the user doesn't say "Linear" or "issue", if they describe work that should be tracked, create it. Trigger phrases: "file a bug", "create a task", "log this", "track this", "make an issue", "what's the status of", "find issues", "update the issue", "comment on TA-", "link this to", "I need to", "we should", "let's do".
---

# Linear is SSOT — Never Touch GitHub Issues

**Linear is the single source of truth for issue tracking.** All issue operations (create, read, update, delete, comment) go through Linear. GitHub Issues exist only as a mirror for PR/code review convenience — sync between them is handled automatically by the system. **Never use `gh issue` commands. Never create/edit/close GitHub Issues directly.**

All Linear operations go through the **`linearis`** CLI at `/opt/homebrew/bin/linearis`. It outputs JSON. Never call `mcp__linear-server__*` tools.

When unsure about any command, run `linearis <domain> usage` (e.g. `linearis issues usage`).

## Team

**Team Adrian** (key: `TA`). Always pass `--team "Team Adrian"` when creating or searching issues.

---

## Creating an issue

### 1. Match a template

Read `assets/templates.md`. Pick the best-fit template. Each template specifies default `--priority`, `--estimate`, and `--labels`.

If the user's intent is ambiguous between two templates, ask.

### 2. Build a detailed description

Fill every field in the template. When the user gives a one-liner, expand it — infer what you can from context, mark truly unknown parts with `[TO CONFIRM]`.

**Every issue must end with a `## Checklist` section.** Checklist items must be concrete and verifiable — someone reading the issue should be able to check each one off without asking what it means.

### 3. Create

```bash
linearis issues create "<title>" \
  --team "Team Adrian" \
  --description "$(cat <<'MD'
<filled template>
MD
)" \
  --priority <1-4> \
  --labels "<label1>,<label2>" \
  --estimate <n> \
  --project "<project-name>"
```

Report back: issue ID, URL, template, labels.

---

## Batch creation

When the user drops a list of tasks:

```
<project-name>
1. <task one>
2. <task two>
```

**Workflow:**

1. Parse project name and numbered items
2. Match each item to a template
3. Show a confirmation table with title, type, priority, estimate, labels, and planned checklist items
4. After user confirms, create **sequentially** — one `linearis issues create` call at a time, no `&` parallelization. This way the user sees each result and any error immediately
5. Report all results

Titles should be concise and descriptive. No `[TPL]` prefix — that's only for template issues. Use template defaults for any property the user didn't specify.

---

## Read / search / update / comment

Use `linearis <domain> usage` to discover available commands. The domains you'll use most:

| Need | Domain | Example |
|------|--------|---------|
| Look up an issue | `issues read` | `linearis issues read TA-123 --with-comments` |
| Find issues | `issues list` / `issues search` | `linearis issues list --project "scientificity" --label "critical"` |
| My issues | `issues list --assignee me` | |
| Update status/labels/assignee | `issues update` | `linearis issues update TA-123 --status "In Progress" --assignee me` |
| Add a comment | `issues discuss` | `linearis issues discuss TA-123 --body "markdown"` |
| Read comments | `issues discussions` | `linearis issues discussions TA-123` |
| List projects/labels/users | `projects list` / `labels list` / `users list` | |
| Create GitHub mirror | `bash scripts/linear-attach.sh mirror --issue TA-xxx --repo owner/repo --title "..."` | |
| Close GitHub mirror | `bash scripts/linear-attach.sh close --issue TA-xxx` | |

Run `linearis <domain> usage` for full flag reference.

---

## Creating GitHub mirrors

Linear is SSOT. When creating a Linear issue, create a GitHub mirror so it's ready for PR/Code Review. Use the bundled script's `mirror` operation:

```bash
# Create Linear issue (via linearis), then mirror to GitHub:
bash scripts/linear-attach.sh mirror \
  --issue TA-83 \
  --repo SiyaoZheng/<repo-name> \
  --title "Fix filter_non_papers" \
  --body "$(cat <<'MD'
<full issue body>
MD
)" \
  --labels "bug"
```

This calls `gh issue create` + `attachmentLinkGitHubIssue` in one step. The GitHub issue URL is attached to the Linear issue so the official sync can propagate future updates.

## Closing GitHub mirrors

When a Linear issue is completed/canceled, close its GitHub mirror:

```bash
bash scripts/linear-attach.sh close --issue TA-83
```

This finds the linked GitHub issue from the Linear attachment and closes it via `gh issue close`.

## Linking existing URLs

For linking a pre-existing GitHub issue, PR, or any URL:

```bash
bash scripts/linear-attach.sh link github-issue --issue TA-75 --url https://github.com/SiyaoZheng/...
bash scripts/linear-attach.sh link github-pr    --issue TA-75 --url https://github.com/SiyaoZheng/...
bash scripts/linear-attach.sh link url          --issue TA-80 --url https://arxiv.org/abs/...
```

Auth is read from `~/.linearis/token` and GitHub CLI (`gh auth`) automatically.

---

## Project matching

The user's Linear projects mirror their GitHub repos. When they mention a repo name, pass it as `--project`. List available projects with `linearis projects list`.

---

## When in doubt, ask

If template, project, priority, or scope is unclear, ask one clarifying question before creating. A wrongly-scoped issue in the wrong project creates more cleanup work than a quick question avoids.
