<!-- markdownlint-disable MD013 MD033 MD041 -->

<p align="center">
  <img src=".github/assets/goal-cli-mark-generated.png" alt="goal-cli terminal wink logo" width="112" />
</p>

<h1 align="center">goal-cli</h1>

<p align="center">
  <strong>Make agents finish THE THING.</strong>
</p>

<p align="center">
  <a href="#快速开始"><strong>快速开始</strong></a>
  &nbsp;/&nbsp;
  <a href="#先说那个东西">那个东西</a>
  &nbsp;/&nbsp;
  <a href="#它做什么">它做什么</a>
  &nbsp;/&nbsp;
  <a href="#背后的科学">科学</a>
  &nbsp;/&nbsp;
  <a href="#technical-details">细节</a>
</p>

<p align="center">
  <a href="README.md">English</a>
  &nbsp;/&nbsp;
  <strong>中文</strong>
</p>

<p align="center">
  <img alt="One prompt" src="https://img.shields.io/badge/one%20prompt-THE%20THING-43d17a?style=for-the-badge&amp;labelColor=07110c" />
  <img alt="Thirty minute heartbeat" src="https://img.shields.io/badge/heartbeat-every%2030%20min-f4c542?style=for-the-badge&amp;labelColor=171204" />
  <img alt="PDFs sites reports apps" src="https://img.shields.io/badge/works%20for-PDFs%20%7C%20sites%20%7C%20reports%20%7C%20apps-6aa9ff?style=for-the-badge&amp;labelColor=07101f" />
  <img alt="No code review required" src="https://img.shields.io/badge/no%20code%20review%20required-check%20the%20thing-f07a5f?style=for-the-badge&amp;labelColor=1b0905" />
</p>

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

| 动作 | 发生什么 |
| --- | --- |
| <img alt="Rebuild" src="https://img.shields.io/badge/rebuild-22c55e?style=flat-square&amp;labelColor=052e16" /> | 重建那个东西。 |
| <img alt="Check" src="https://img.shields.io/badge/check-eab308?style=flat-square&amp;labelColor=332600" /> | 检查那个东西。 |
| <img alt="Repair" src="https://img.shields.io/badge/repair-3b82f6?style=flat-square&amp;labelColor=082f49" /> | 只修允许改的源码。 |
| <img alt="Repeat" src="https://img.shields.io/badge/repeat-ef4444?style=flat-square&amp;labelColor=3b0909" /> | 下一次心跳再看。 |

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

<details id="technical-details">
<summary><strong>技术细节</strong></summary>

配置文件是 `goal.toml`。

它只回答四个问题：

| 问题 | 配置 |
| --- | --- |
| 我要检查哪个成品？ | `[artifact].path` |
| 怎么重建它？ | `[producer].command` |
| 怎么检查它？ | `[tik]` |
| Agent 允许改哪里？ | `[tok].write_dirs` |

常用命令：

| 命令 | 用途 |
| --- | --- |
| `goal-cli init` | 创建 starter `goal.toml`。 |
| `goal-cli validate` | 检查配置。 |
| `goal-cli doctor` | 检查本地环境能不能跑。 |
| `goal-cli run --dry-run` | 先预演，不真的修。 |
| `goal-cli run --max-minutes 30` | 跑一次 30 分钟心跳。 |

完整配置说明见 [docs/config-schema.md](docs/config-schema.md)。

完整命令说明见 [docs/cli-reference.md](docs/cli-reference.md)。

</details>
