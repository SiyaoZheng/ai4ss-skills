# goal-cli Skills

`goal-cli` ships two agent-facing skills. Use them when you want a coding agent
to keep working toward the thing you will actually inspect, not just keep
changing code.

## Which Skill to Use

| Skill | Use it when |
| --- | --- |
| [`goal-cli-project-setup`](../skills/goal-cli-project-setup/SKILL.md) | You want to connect an existing project to `goal-cli`. |
| [`goal-cli-template-author`](../skills/goal-cli-template-author/SKILL.md) | You are improving reusable examples, checks, or docs in this repository. |

Most users should start with `goal-cli-project-setup`.

## One Prompt

Paste this into the agent that has access to the project.

```text
Hi, read https://github.com/SiyaoZheng/goal-cli/blob/master/llms.txt and do what it says.
```

## Skill Install

If your agent supports local skills, copy the setup skill into the agent's
skill folder. For Codex-style skills:

```bash
mkdir -p "$HOME/.codex/skills"
cp -R skills/goal-cli-project-setup "$HOME/.codex/skills/"
```

For Claude Code:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/goal-cli-project-setup "$HOME/.claude/skills/"
```

Install the template-author skill only when you are maintaining this repository:

```bash
cp -R skills/goal-cli-template-author "$HOME/.codex/skills/"
```

## What Good Setup Produces

After setup, the project should have:

- one thing to inspect;
- one command that rebuilds it;
- a `goal.toml` file;
- clear folders that future repair runs may edit;
- clear folders that future repair runs must not edit;
- passing `goal-cli validate`;
- a useful `goal-cli doctor` result;
- a dry run from `goal-cli run --dry-run`.
- a recommendation for either a manual heartbeat or a system-level timed
  heartbeat.

Only after those checks should a real repair run start:

```bash
goal-cli run --max-minutes 30
```

For unattended progress, install the per-user OS timer instead of leaving a
foreground loop running:

```bash
goal-cli heartbeat install --every-minutes 30 --max-minutes 30
```
