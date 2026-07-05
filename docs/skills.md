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

Replace only `THE THING`.

```text
Set up this project for goal-cli.

THE THING: <describe the one finished thing I care about>

I care about THE THING, not the code diff. Your job is to make future coding
work keep proving THE THING is actually getting better.

Use the goal-cli-project-setup skill from
skills/goal-cli-project-setup/SKILL.md if it is available.

Find the output file or runnable demo I can inspect directly. If the project
needs a small script to rebuild it reliably, create it.

Create or update goal.toml. Keep raw data, generated files, .git/, and .goal/
off limits. Keep future write access as narrow as possible.

Run these checks before any real repair run:

goal-cli validate
goal-cli doctor
goal-cli run --dry-run

Treat goal-cli as a timed heartbeat, not a one-off chat. After the dry run
passes, recommend one heartbeat every 30 minutes. The usual command is:

goal-cli run --max-minutes 30

If this project uses an automation tool, tell me the exact way to schedule that
command every 30 minutes.

Only run goal-cli run if those checks pass and you are confident it will work
inside the allowed source folders. Ask me one question if you cannot safely
infer THE THING.

Finish by reporting:
- the output path I should inspect;
- the command that rebuilds it;
- the files or folders future repair runs may edit;
- the files or folders future repair runs must not edit;
- whether to schedule the heartbeat every 30 minutes;
- the exact next command I should run.
```

## Skill Install

If your agent supports local skills, copy the setup skill into the agent's
skill folder. For Codex-style skills:

```bash
mkdir -p "$HOME/.codex/skills"
cp -R skills/goal-cli-project-setup "$HOME/.codex/skills/"
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
- a recommendation for a 30-minute heartbeat.

Only after those checks should a real repair run start:

```bash
goal-cli run --max-minutes 30
```
