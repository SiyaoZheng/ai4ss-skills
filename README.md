<!-- markdownlint-disable MD013 MD033 MD041 -->

<p align="center">
  <img src=".github/assets/goal-cli-mark-generated.png" alt="goal-cli terminal wink logo" width="112" />
</p>

<h1 align="center">goal-cli</h1>

<p align="center">
  <strong>Make coding agents finish the thing you asked for, not just keep editing code.</strong>
</p>

<p align="center">
  <a href="#quick-start"><strong>Quick Start</strong></a>
  &nbsp;/&nbsp;
  <a href="#what-it-does">What It Does</a>
  &nbsp;/&nbsp;
  <a href="#the-science-behind-it">Science</a>
  &nbsp;/&nbsp;
  <a href="#technical-details">Details</a>
</p>

Coding agents are good at coding. That is also the problem.

They can spend a whole session changing files while drifting away from the
thing you actually wanted: the PDF, the website, the report, the chart pack,
the app demo, or whatever else you will judge at the end.

`goal-cli` keeps that thing in the center. It rebuilds the thing, checks the
thing, and only lets the agent keep changing code when the thing is still not
good enough. Chat confidence does not count. The thing does.

## Quick Start

You do not need to learn `goal-cli` first. Paste this into the coding agent
that already has access to your project.

Replace only `THE THING` with the one thing you want finished.

```text
Set up this project for goal-cli.

THE THING: <describe the one finished thing I care about>

I care about THE THING, not the code diff. Your job is to make future coding
work keep proving THE THING is actually getting better.

First, make sure goal-cli runs. Use Python 3.11 or newer. If goal-cli is not
already installed, clone it from:

https://github.com/SiyaoZheng/goal-cli

Install it in a virtual environment outside my project unless this repository
already has a preferred Python environment.

Use commands like these, adjusted only for the actual folder you choose:

git clone https://github.com/SiyaoZheng/goal-cli.git
cd goal-cli
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e '.[openai]'
goal-cli --help

Then configure this project around THE THING. Find the output file or runnable
demo I can inspect directly. If the project needs a small script to rebuild it
reliably, create it.

If the goal-cli checkout includes llms.txt, read it. If
skills/goal-cli-project-setup/SKILL.md is available, use it as the setup guide.
Keep THE THING from this prompt as the one source of truth.

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
infer the final output.

Finish by reporting:
- the output path I should inspect;
- the command that rebuilds it;
- the files or folders future repair runs may edit;
- the files or folders future repair runs must not edit;
- whether to schedule the heartbeat every 30 minutes;
- the exact next command I should run.
```

That is the intended first experience: name the thing once, give the prompt to
your agent, and judge the finished output it names.

## What It Does

`goal-cli` gives a coding agent a stricter job:

1. Rebuild the finished output.
2. Check that output against your standard.
3. If the output is not good enough, let the agent edit only the allowed source
   files.
4. Rebuild and check again on the next run.

This is useful when the real question is not "did the agent change code?" but:

| You care about | The agent must prove |
| --- | --- |
| A paper | The PDF is rebuilt and worth reading. |
| A website | The built page opens and looks right. |
| A report | The numbers and narrative are inspectable. |
| A chart pack | The exported charts are current. |
| A demo app | The app runs in the expected state. |

## The Science Behind It

People are starting to call this
[loop engineering](https://addyosmani.com/blog/loop-engineering/): instead of
writing one perfect prompt, you design a repeatable loop that keeps an agent
working, checking, and trying again.

That is the trend. The useful part is simpler:

1. The agent should not decide success by reading its own code diff.
2. The work should be checked against the thing you actually asked for.
3. The loop should run on a timer, so progress does not depend on you typing
   the next prompt.

LangChain describes the basic agent pattern as a model calling tools until the
job is done, then adds that stronger systems stack more loops around that
basic loop. Industry coverage of loop engineering says the same thing in plainer
terms: teams are moving from one-off prompts toward repeatable agent workflows
that build, test, revise, and continue with less hand-holding.

`goal-cli` is the boring, practical version of that idea. Every heartbeat asks:
is the thing better yet? If not, the agent gets another bounded work pass.

Sources: [Addy Osmani](https://addyosmani.com/blog/loop-engineering/),
[LangChain](https://www.langchain.com/blog/the-art-of-loop-engineering/),
[ADTMAG](https://adtmag.com/articles/2026/07/01/loop-engineering-emerges-as-developers-put-ai-coding-agents-on-repeat.aspx).

<details id="technical-details">
<summary><strong>Technical Details</strong></summary>

### How It Works

The setup file is `goal.toml`. It answers four plain questions:

| Question | In `goal.toml` |
| --- | --- |
| What finished output should I inspect? | `[artifact].path` |
| How do I rebuild it? | `[producer].command` |
| How should it be checked? | `[tik]` |
| Where may the coding agent edit source files? | `[tok].write_dirs` |

You may see these short names in the config and deeper docs:

| Name | Plain meaning |
| --- | --- |
| `artifact` | The finished output you can inspect. |
| `producer` | The command that rebuilds that output. |
| `tik` | The reviewer that rejects weak output. |
| `tok` | The coding agent that repairs source files. |
| `.goal/` | The folder where runs, reviews, and state are recorded. |

Example:

```toml
name = "paper-ready"
state_dir = ".goal"
runs_dir = ".goal/runs"

[artifact]
path = "outputs/writing/full_paper.pdf"
copy_as = "full_paper.pdf"

[producer]
command = "python3 scripts/orchestrator.py --full"

[tik]
provider = "codex_file"
timeout_seconds = 1800
max_file_size_bytes = 25000000
max_output_tokens = 4096

[tok]
provider = "codex_goal"
write_dirs = ["writing", "src"]
sandbox = "workspace-write"
codex_features = ["goals"]

[safety]
generated_dirs = ["outputs", "build", ".goal"]
max_blocker_repeats = 3
```

The important boundary is simple: the fixing agent edits source, but the final
result has to be rebuilt and checked before the work counts as done.

### Installing From This Checkout

If you are working inside the `goal-cli` repository itself:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e '.[openai]'
goal-cli --help
```

Use the basic install without OpenAI support when you only need local checks:

```bash
python3 -m pip install -e .
```

### Commands

| Command | What it does |
| --- | --- |
| `goal-cli init` | Create a starter `goal.toml`. |
| `goal-cli validate` | Check that the config is shaped correctly. |
| `goal-cli doctor` | Check whether the local setup is ready to run. |
| `goal-cli run --dry-run` | Render the prompts and run folder without calling repair agents. |
| `goal-cli run --max-minutes 30` | Run one bounded work pass. |
| `goal-cli tik` | Rebuild and review the output without running a repair pass. |
| `goal-cli state` | Show the current saved state. |
| `goal-cli cleanup` | Clear stale locks after an interrupted run. |
| `goal-cli reset` | Remove saved state while keeping run records. |

### Agent Skills

If your coding agent supports skills, install the setup skill:

```bash
mkdir -p "$HOME/.codex/skills"
cp -R skills/goal-cli-project-setup "$HOME/.codex/skills/"
```

Use [`goal-cli-project-setup`](skills/goal-cli-project-setup/SKILL.md) for real
projects. Use
[`goal-cli-template-author`](skills/goal-cli-template-author/SKILL.md) only when
you are improving reusable examples or docs in this repository.

### Docs

| Document | Use it when |
| --- | --- |
| [Installing goal-cli](docs/installation.md) | You need more install details. |
| [CLI reference](docs/cli-reference.md) | You want the full command help. |
| [goal.toml schema](docs/config-schema.md) | You are editing config by hand. |
| [goal-cli Skills](docs/skills.md) | You want agent-facing setup instructions. |
| [Artifact notes](docs/artifact-goal-notes.md) | You want the design rationale. |
| [Codex implementation report](docs/codex-goal-openai-implementation-report.md) | You want the Codex `/goal` integration details. |
| [PDF-first example](examples/scientificity/goal.toml) | You want a research-paper example. |

### Status

`goal-cli` is early local tooling, currently version `0.1.0`.

No license file is included yet. Add one before accepting external
contributions or using this as a dependency in another public project.

</details>
