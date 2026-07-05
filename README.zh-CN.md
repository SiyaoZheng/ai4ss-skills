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
  <a href="#先说清楚要什么">要什么</a>
  &nbsp;/&nbsp;
  <a href="#怎么跑">怎么跑</a>
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

Coding agent 最爱干什么？

改代码。

但你真正要的，不是“我改了 12 个文件”。

你要的是成品。

能打开的 PDF。

能看的网页。

能交的报告。

能刷新的图表。

能跑起来的 demo。

`goal-cli` 做一件事：

把 agent 拉回 THE THING。

先重建成品。

再验收成品。

不过关，再让它改源码。

嘴上说“差不多了”不算。

成品真的变好，才算。

## 快速开始

把这一句粘给你的 coding agent。

```text
Hi, read https://github.com/SiyaoZheng/goal-cli/blob/master/llms.txt and do what it says.
```

就这一句。

细节在 [`llms.txt`](llms.txt)。

让 agent 自己读。

你只看结果。

## 先说清楚要什么

<p align="center">
  <img src=".github/assets/goal-cli-personas-human.png" alt="不同用户拿着自己要让 coding agent 做完的那个东西" width="100%" />
</p>

每个人要的都不一样。

但规矩一样。

先把要交付的东西说清楚。

然后让 agent 一直回到它。

| 你是谁 | 直接这么说 |
| --- | --- |
| 学者 <img alt="Scholar" src="https://img.shields.io/badge/scholar-34d399?style=flat-square&amp;labelColor=062014" /> | “先别讲代码，给我看 PDF。” |
| 设计师 <img alt="Designer" src="https://img.shields.io/badge/designer-f59e0b?style=flat-square&amp;labelColor=241504" /> | “给我看海报成品。” |
| 玩家 <img alt="Hobbyist" src="https://img.shields.io/badge/hobbyist-60a5fa?style=flat-square&amp;labelColor=071426" /> | “这个 app 能点开跑吗？” |
| 会计 <img alt="Accountant" src="https://img.shields.io/badge/accountant-a78bfa?style=flat-square&amp;labelColor=160d24" /> | “数字对得上吗？” |
| 分析师 <img alt="Analyst" src="https://img.shields.io/badge/analyst-f87171?style=flat-square&amp;labelColor=240909" /> | “图是不是新的？” |

## 怎么跑

一句 prompt。

一个交付物。

每 30 分钟一次心跳。

| 动作 | 发生什么 |
| --- | --- |
| <img alt="Rebuild" src="https://img.shields.io/badge/rebuild-22c55e?style=flat-square&amp;labelColor=052e16" /> | 重建交付物。 |
| <img alt="Check" src="https://img.shields.io/badge/check-eab308?style=flat-square&amp;labelColor=332600" /> | 验收交付物。 |
| <img alt="Source" src="https://img.shields.io/badge/source-3b82f6?style=flat-square&amp;labelColor=082f49" /> | 只改允许改的源码。 |
| <img alt="Repeat" src="https://img.shields.io/badge/repeat-ef4444?style=flat-square&amp;labelColor=3b0909" /> | 半小时后再验一次。 |

别问：

“它改代码了吗？”

要问：

“我要的东西，真的变好了吗？”

| 你在乎 | Agent 必须证明 |
| --- | --- |
| 论文 | PDF 重新生成了，读起来更像能交的稿子。 |
| 网站 | 页面能打开，第一眼是对的。 |
| 报告 | 数字、口径、叙事都能查。 |
| 图表包 | 导出的图是新的，不是旧图冒充。 |
| Demo app | App 在你要的状态里跑起来。 |

## 背后的科学

现在圈里把这事叫
[loop engineering](https://addyosmani.com/blog/loop-engineering/)。

说白了：

别指望一个神 prompt 管到底。

你要设计一个循环。

跑一轮。

验一轮。

不过关，再来一轮。

`goal-cli` 是这套思路的家用版。

每半小时只问一个问题：

东西变好了吗？

好，停。

不好，回去改源码，下一次心跳再验。

来源：[Addy Osmani](https://addyosmani.com/blog/loop-engineering/)、
[LangChain](https://www.langchain.com/blog/the-art-of-loop-engineering/)、
[ADTMAG](https://adtmag.com/articles/2026/07/01/loop-engineering-emerges-as-developers-put-ai-coding-agents-on-repeat.aspx)。

<details id="technical-details">
<summary><strong>技术细节</strong></summary>

配置文件叫 `goal.toml`。

只写清楚四件事：

| 问题 | 配置 |
| --- | --- |
| 我要验收哪个成品？ | `[artifact].path` |
| 怎么重建它？ | `[producer].command` |
| 怎么验收它？ | `[tik]` |
| Agent 可以改哪些目录？ | `[tok].write_dirs` |

常用命令：

| 命令 | 用途 |
| --- | --- |
| `goal-cli init` | 生成一份起步用的 `goal.toml`。 |
| `goal-cli validate` | 检查配置有没有写歪。 |
| `goal-cli doctor` | 检查本机能不能跑。 |
| `goal-cli run --dry-run` | 预演一遍，不让 agent 真改。 |
| `goal-cli run --max-minutes 30` | 跑一轮 30 分钟心跳。 |
| `goal-cli heartbeat install --every-minutes 60 --max-minutes 30` | 安装系统级定时心跳；每次 tick 仍然只跑一轮。 |

完整配置说明见 [docs/config-schema.md](docs/config-schema.md)。

完整命令说明见 [docs/cli-reference.md](docs/cli-reference.md)。

</details>
