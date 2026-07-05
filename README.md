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
  <a href="#name-the-thing">The Thing</a>
  &nbsp;/&nbsp;
  <a href="#what-it-does">What It Does</a>
  &nbsp;/&nbsp;
  <a href="#the-science-behind-it">Science</a>
  &nbsp;/&nbsp;
  <a href="#technical-details">Details</a>
</p>

<p align="center">
  <img alt="One prompt" src="https://img.shields.io/badge/one%20prompt-THE%20THING-43d17a?style=for-the-badge&amp;labelColor=07110c" />
  <img alt="Thirty minute heartbeat" src="https://img.shields.io/badge/heartbeat-every%2030%20min-f4c542?style=for-the-badge&amp;labelColor=171204" />
  <img alt="PDFs sites reports apps" src="https://img.shields.io/badge/works%20for-PDFs%20%7C%20sites%20%7C%20reports%20%7C%20apps-6aa9ff?style=for-the-badge&amp;labelColor=07101f" />
  <img alt="No code review required" src="https://img.shields.io/badge/no%20code%20review%20required-check%20the%20thing-f07a5f?style=for-the-badge&amp;labelColor=1b0905" />
</p>

<details open>
<summary><strong>English</strong></summary>

Coding agents love code.

You want the thing.

Not a diff.

Not a status update.

Not "almost done."

The thing.

The PDF.

The website.

The report.

The chart pack.

The app demo.

`goal-cli` keeps the thing in the center.

It rebuilds the thing.

It checks the thing.

If the thing is not good enough, the agent gets another work pass.

Chat confidence does not count.

The thing does.

## Quick Start

Paste one sentence into your coding agent.

```text
Hi, read https://github.com/SiyaoZheng/goal-cli/blob/master/llms.txt and do what it says.
```

That is it.

The details live in [`llms.txt`](llms.txt).

The agent reads them.

You judge the thing.

## Name The Thing

<p align="center">
  <img src=".github/assets/goal-cli-personas-human.png" alt="Scholars, designers, hobbyists, accountants, and analysts each holding the thing they need a coding agent to finish" width="100%" />
</p>

Different people.

Different things.

Same rule.

Name it.

Make the agent come back to it.

| Who | What they say |
| --- | --- |
| <img alt="Scholar" src="https://img.shields.io/badge/scholar-34d399?style=flat-square&amp;labelColor=062014" /> | "Show me the PDF." |
| <img alt="Designer" src="https://img.shields.io/badge/designer-f59e0b?style=flat-square&amp;labelColor=241504" /> | "Show me the poster." |
| <img alt="Hobbyist" src="https://img.shields.io/badge/hobbyist-60a5fa?style=flat-square&amp;labelColor=071426" /> | "Does my app run?" |
| <img alt="Accountant" src="https://img.shields.io/badge/accountant-a78bfa?style=flat-square&amp;labelColor=160d24" /> | "Do the numbers tie?" |
| <img alt="Analyst" src="https://img.shields.io/badge/analyst-f87171?style=flat-square&amp;labelColor=240909" /> | "Does the chart move?" |

## What It Does

One prompt.

One thing.

One heartbeat every 30 minutes.

| Step | What happens |
| --- | --- |
| <img alt="Rebuild" src="https://img.shields.io/badge/1-rebuild-22c55e?style=flat-square&amp;labelColor=052e16" /> | Rebuild the thing. |
| <img alt="Check" src="https://img.shields.io/badge/2-check-eab308?style=flat-square&amp;labelColor=332600" /> | Check the thing. |
| <img alt="Repair" src="https://img.shields.io/badge/3-repair-3b82f6?style=flat-square&amp;labelColor=082f49" /> | Repair only allowed source files. |
| <img alt="Repeat" src="https://img.shields.io/badge/4-repeat-ef4444?style=flat-square&amp;labelColor=3b0909" /> | Try again on the next heartbeat. |

The question is not:

"Did the agent change code?"

The question is:

"Is the thing better?"

| You care about | The agent must prove |
| --- | --- |
| A paper | The PDF is rebuilt and worth reading. |
| A website | The built page opens and looks right. |
| A report | The numbers and narrative are inspectable. |
| A chart pack | The exported charts are current. |
| A demo app | The app runs in the expected state. |

## The Science Behind It

People are calling this
[loop engineering](https://addyosmani.com/blog/loop-engineering/).

The hype says:

Do not write one perfect prompt.

Build a loop.

Make it run.

Make it check.

Make it try again.

`goal-cli` is that idea for normal people.

Every heartbeat asks:

Did the thing get better?

If yes, stop.

If no, repair source and come back in 30 minutes.

Sources: [Addy Osmani](https://addyosmani.com/blog/loop-engineering/),
[LangChain](https://www.langchain.com/blog/the-art-of-loop-engineering/),
[ADTMAG](https://adtmag.com/articles/2026/07/01/loop-engineering-emerges-as-developers-put-ai-coding-agents-on-repeat.aspx).

</details>

<details>
<summary><strong>中文</strong></summary>

Coding agent 很爱写代码。

但你要的不是代码。

你要的是那个东西。

不是 diff。

不是进度汇报。

不是“快好了”。

是那个东西。

PDF。

网站。

报告。

图表包。

App demo。

`goal-cli` 把那个东西放在中间。

它重建那个东西。

它检查那个东西。

如果那个东西还不够好，agent 才继续改源码。

聊天里的自信不算数。

那个东西算数。

## 快速开始

只复制这一句话给你的 coding agent。

```text
Hi, read https://github.com/SiyaoZheng/goal-cli/blob/master/llms.txt and do what it says.
```

就这样。

细节在 [`llms.txt`](llms.txt)。

Agent 去读。

你只看那个东西。

## 先说那个东西

<p align="center">
  <img src=".github/assets/goal-cli-personas-human.png" alt="不同用户拿着自己要让 coding agent 做完的那个东西" width="100%" />
</p>

人不一样。

东西不一样。

规则一样。

先说清楚那个东西。

让 agent 一直回到它。

| 谁 | 人话 |
| --- | --- |
| 学者 <img alt="Scholar" src="https://img.shields.io/badge/scholar-34d399?style=flat-square&amp;labelColor=062014" /> | “给我看 PDF。” |
| 设计师 <img alt="Designer" src="https://img.shields.io/badge/designer-f59e0b?style=flat-square&amp;labelColor=241504" /> | “给我看海报。” |
| 玩家 <img alt="Hobbyist" src="https://img.shields.io/badge/hobbyist-60a5fa?style=flat-square&amp;labelColor=071426" /> | “我的 app 跑起来了吗？” |
| 会计 <img alt="Accountant" src="https://img.shields.io/badge/accountant-a78bfa?style=flat-square&amp;labelColor=160d24" /> | “数字对得上吗？” |
| 分析师 <img alt="Analyst" src="https://img.shields.io/badge/analyst-f87171?style=flat-square&amp;labelColor=240909" /> | “图动了吗？” |

## 它做什么

一句 prompt。

一个东西。

每 30 分钟一次心跳。

| 步骤 | 发生什么 |
| --- | --- |
| <img alt="Rebuild" src="https://img.shields.io/badge/1-rebuild-22c55e?style=flat-square&amp;labelColor=052e16" /> | 重建那个东西。 |
| <img alt="Check" src="https://img.shields.io/badge/2-check-eab308?style=flat-square&amp;labelColor=332600" /> | 检查那个东西。 |
| <img alt="Repair" src="https://img.shields.io/badge/3-repair-3b82f6?style=flat-square&amp;labelColor=082f49" /> | 只修允许改的源码。 |
| <img alt="Repeat" src="https://img.shields.io/badge/4-repeat-ef4444?style=flat-square&amp;labelColor=3b0909" /> | 下一次心跳再看。 |

问题不是：

“它改代码了吗？”

问题是：

“那个东西变好了吗？”

| 你在乎 | Agent 必须证明 |
| --- | --- |
| 论文 | PDF 重新生成了，而且值得读。 |
| 网站 | 页面能打开，而且看起来对。 |
| 报告 | 数字和叙事都能检查。 |
| 图表包 | 导出的图是新的。 |
| Demo app | App 跑在你要的状态。 |

## 背后的科学

现在大家叫它
[loop engineering](https://addyosmani.com/blog/loop-engineering/)。

热点说法是：

别写一个神奇 prompt。

设计一个循环。

让它运行。

让它检查。

让它再来。

`goal-cli` 是给普通人用的版本。

每次心跳只问一句：

那个东西变好了吗？

好了，就停。

没好，就修源码，30 分钟后再回来。

来源：[Addy Osmani](https://addyosmani.com/blog/loop-engineering/)、
[LangChain](https://www.langchain.com/blog/the-art-of-loop-engineering/)、
[ADTMAG](https://adtmag.com/articles/2026/07/01/loop-engineering-emerges-as-developers-put-ai-coding-agents-on-repeat.aspx)。

</details>

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
