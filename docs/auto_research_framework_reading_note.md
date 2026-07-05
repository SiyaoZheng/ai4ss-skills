# Victor Chen Deli AutoResearch Framework 阅读心得

阅读日期：2026-07-05

主要来源：

- Deli_AutoResearch framework page: https://victorchen96.github.io/auto_research/framework.html
- Deli AutoResearch papers/statistics page: https://victorchen96.github.io/auto_research/paper.html
- AutoResearch survey context: https://arxiv.org/html/2605.23204v1
- Specialist-agent empirical-loop paper: https://arxiv.org/abs/2605.05724
- ResearchArena quality-audit paper: https://arxiv.org/abs/2605.19156

## 一句话理解

Victor Chen 的 Deli AutoResearch 核心不是“写一个更聪明的研究 agent”，而是把长周期 agent 工作当作一个需要工程治理的运行系统：模型只是 worker，真正的能力来自状态外置、循环保活、停滞检测、强制换方向、独立验证和权限分离。

这和 AI4SS 的基本判断高度一致：agent 不能只靠对话记忆、提示词热情和一次性总结来做研究。可用的研究自动化必须把过程变成可检查的对象、日志、路线、证据和边界。

## 它要解决的真正问题

这套框架从三个常见失败出发。

第一是认知循环。agent 连续几轮看似在努力，但实际上总是在同一类方向里微调，产出的边际信息越来越少。问题不只是模型不够聪明，而是系统没有强制记录“已经试过什么”和“下一轮必须怎样不同”。

第二是停滞。agent 完成一段工作后总结几句，然后等用户确认。外部看 session 还活着，但工作已经停止。Deli 把这看作比崩溃更常见的失败，因为它没有明显错误，却会让长任务在最需要连续推进时静默死亡。

第三是运行脆弱性。上下文压缩、会话关闭、计时器寄生在当前 session、回调没有 first action 心跳更新，都会让循环断掉。Deli 的判断是：长周期任务不能把“活着”寄托在聊天窗口里。

## 最重要的设计原则

### 1. 状态必须在文件里，而不是在对话里

Deli 要求每个任务维护自己的 `state/` 和 `logs/`。`task_spec.md` 写目标、里程碑和成功标准；`progress.json` 写迭代状态和 stale count；`findings.jsonl` 追加发现；`directions_tried.json` 记录已试方向；`iteration_log.jsonl` 记录每轮摘要。

这背后的思想非常强：conversation 是运行时缓存，不是 workflow state。上下文会膨胀、压缩、丢失和污染。长任务真正可恢复，必须靠可读、可 diff、可注入的新鲜状态文件。

对应到 AI4SS，`.aiss` 应继续承担研究对象和工作流状态的核心角色。Deli 的 `progress.json`、`directions_tried.json`、`iteration_log.jsonl` 更适合成为运行控制层，而不是替代 `.aiss`。简言之：`.aiss` 管研究含义，Deli 式 state 管 agent 运行生命体征。

### 2. 每轮用新 session，而不是 resume

Deli 明确偏好 fresh session。理由是 resume 会继承上下文惯性，容易放大认知循环。新 session 只注入 curated state，让 agent 带着必要事实重新开始，而不是把上一轮的思维轨迹原封不动延续下去。

这点对研究工作很关键。研究 agent 的最大风险不是忘了一句话，而是把上一轮错误框架继续合理化。新 session 加结构化 state，可以把“记住事实”和“摆脱路径依赖”分开。

### 3. 执行和评价分离

Deli 的 orchestrator 监控状态、判断停滞、注入新方向；worker 负责做任务；heartbeat 负责保活和重启。worker 不应独自判断自己是否真的有进展。

这对应研究里的一个基本原则：生产证据的人不能仅凭自我叙述完成质量判定。AI4SS 已经有 methods-reviewer、manuscript-reviewer、validators、LLM-as-judge evals 等机制；Deli 的贡献是把这种 separation of duties 进一步扩展到运行层。

### 4. 停滞后换结构，不是调参数

Deli 的 stall 规则很有价值：如果一轮没有新 findings 或指标下降，就增加 stale count；连续停滞后，改变结构性约束，而不是继续调 tactic。所谓结构性改变，可以是换假设、换相似案例域、换数据源、换评价方式、换任务分解，而不是把同一条路再走得更努力。

这是它最值得 AI4SS 吸收的地方之一。社会科学研究里，很多失败不是模型没跑好，而是问题设定、数据可得性、测量桥、识别策略或 claim 边界错了。AI4SS 的 `next_skill_route` 正好可以承担这种结构性 pivot：数据不行就回 public-data-sources 或 research-data-builder，识别不行就回 study-design-builder 或 did-expert，claim 不行就回 methods-reviewer 或 academic-writing-scaffold。

### 5. “Ready means execute” 是自动化纪律，但必须有边界

Deli 反复强调：准备完成后不要问“是否提交”，准备就是为了执行。这解决了 agent 长任务里最隐蔽的假自动化问题：agent 把所有前置工作做完，却在关键动作前停住。

我认为这个原则在 AI4SS 中应该被有条件采用。

可以直接自动执行的包括：跑验证、重新编译、重新抓取公开页面、生成派生表、重跑可复现分析、启动非破坏性监控、修复失败脚本并重试。

不能无条件自动执行的包括：发送邮件、提交论文、公开发布、付费调用、删除数据、覆盖原始资料、使用敏感凭据、改变研究伦理边界。这里应保留 AI4SS 的 human accountability 和 disclosure gate。

因此，AI4SS 可以把原则改写为：在授权边界内，ready means execute；越过授权边界时，ready means produce a bounded decision packet。

## 架构图式

Deli 的运行图式可以概括为：

```text
orchestrator / durable scheduler
  -> read state files
  -> detect stalls and liveness failures
  -> choose a direction different from history
  -> launch fresh worker sessions
  -> trigger verification or nudge

worker session
  -> read task_spec and curated state
  -> produce verifiable findings or artifacts
  -> append logs and update progress
  -> stop only after state is written

heartbeat watchdog
  -> maintain last_seen
  -> restart dead loops
  -> nudge stalled loops
  -> avoid reading or editing worker-owned research state
```

它特别强调 guardian / worker separation。守护进程只能做 liveness check、restart、nudge，不能越权读取任务数据、修改任务状态、替 worker 汇报。这一点很现实：守护层本来是为了防停滞，如果它开始代替 worker 做研究判断，就会制造上下文污染和并发写入风险。

## 它对 AutoResearch 的定位

从 AutoResearch survey 的语境看，Deli 更像是 L2 到 L3 之间的运行协议，而不是成熟的科学自治本身。它提高的是 workflow continuity、execution reliability、evidence checking cadence 和 unattended operation，而不是直接解决科学有效性。

这个区分很重要。最近的 specialist-agent 训练配方工作把 auto research 做成可度量的 closed empirical loop：每次 trial 有假设、代码修改、外部 evaluator 结果和失败标签，最终产物是可审计 trajectory，而不只是论文或 checkpoint。Deli 的方向与此相通：让 agent 的工作留下可恢复、可验证、可继续的轨迹。

同时，ResearchArena 一类质量审计提醒我们：能写出完整论文，不等于研究质量过关。只看 manuscript 的评分会过于乐观；artifact-aware review 和人工审计会暴露实验不足、结果和工件不一致、引用伪造等问题。因此 Deli 的 self-rated papers 和页面统计只能说明它在自己协议内跑通了长任务，不能被当作外部学术质量证明。

## 对 AI4SS 的直接启发

### 1. 给 research-factory 增加运行控制层

AI4SS 现在强在研究对象、方法论 spine、技能路由、`.aiss` 验证和 disclosure boundary。Deli 暴露出的短板是运行层：长任务怎样保活、怎样发现 agent 已经停在原地、怎样自动换结构、怎样从上下文压缩后恢复。

建议把 Deli 式 task state 作为 `.aiss` 之外的 runtime companion：

```text
research_model.aiss          # 研究语义和工作流状态
runtime/state/task_spec.md   # 本次长任务目标和成功标准
runtime/state/progress.json  # 迭代数、状态、stale_count、last_seen
runtime/state/directions_tried.json
runtime/state/findings.jsonl
runtime/logs/work.jsonl
runtime/logs/orchestrator.jsonl
runtime/logs/heartbeat.jsonl
```

### 2. 把 `next_skill_route` 用作结构性 pivot

AI4SS 的技能路由表已经要求每个 skill 发出或保留 `next_skill_route`。Deli 提醒我们，这不应只是流程串联字段，而应承担 anti-loop 功能。

如果同一路线连续失败，系统不该只是“再跑一次 research-analysis-runner”。它应该根据 stale 原因换 owning skill：

- 数据源不存在：回 `public-data-sources`
- 样本无法构造：回 `research-data-builder`
- 识别逻辑不成立：回 `study-design-builder` 或 `did-expert`
- 结果支持不了 claim：回 `methods-reviewer`
- 文献证据薄弱：回 `literature-matrix`
- 写作看似完整但 PDF 不可信：回 `manuscript-reviewer` 或前置证据 skill

### 3. 给 eval harness 明确 heartbeat 和 stale rules

APSR PDF harness、factory relay eval、DDI harness 都适合借鉴 Deli 的运行纪律。特别是长时间 model-backed CLI agents，很容易“输出总结然后停止”。harness 不应只等进程结束，而应记录：

- 最近一次 artifact 更新是什么时候
- 最近一次 PDF 或输出指标有没有实质变化
- 最近一次失败是环境错误、数据错误、方法错误还是写作错误
- 是否连续两轮没有新增证据或改进
- 下一轮是否真的改变了结构性条件

这比只看最后生成物更能解释 agent 为什么失败。

### 4. citation-like 内容必须小批量验证

Deli 提到 citation-like content 不应大批量最后验证，而应每 20 条左右验证一次。对 AI4SS 来说，这一点应该扩大为“source-like claims small-batch verification”：

- 文献条目
- 官方数据源链接
- 政策文件来源
- 变量定义和 codebook 摘要
- 表格脚注里的数据说明
- PDF 里出现的 empirical claim

社会科学的风险不是最后忘了补 references，而是中间几十条 claim 已经被虚假来源带偏。

## 不能直接照搬的地方

第一，Deli 是协议框架，不提供执行代码。它说明了该怎么组织状态和守护层，但真正的可靠性取决于 adopters 能否实现调度、锁、日志、权限和验证。

第二，zero interaction 不能覆盖所有研究行为。对于社会科学，数据授权、伦理、隐私、投稿、公开传播、经费和人类受试者相关决策，不能用“自动继续”一笔带过。AI4SS 应保留研究者责任边界。

第三，self-rating 不能替代外部评价。页面上的 paper 数、页数、citation 数和 in-framework review score 只能作为运行案例，不是学术有效性的证据。AI4SS 的 eval 仍应坚持 LLM-as-judge 与 deterministic gates 的区分，并尽量引入 artifact-aware review。

第四，Markdown state 不能替代 `.aiss`。Deli 的 state file 简洁有效，但 AI4SS 需要更强的研究语义：MIDA、source、artifact、empirical、claim、check、decision、disclosure。运行状态可以轻，研究状态不能退回散文日志。

## 我的核心心得

这篇 framework 最有价值的地方，是把“agent 长任务失败”从模型哲学问题改写成操作系统问题。

它不迷信模型会自我纠错，而是默认 agent 会循环、会停住、会越权、会忘记、会被上下文污染。于是它把可持续工作所需的东西都外置出来：状态、方向历史、心跳、停滞计数、验证 cadence、守护层权限、fresh session handoff。

这对 AI4SS 很有启发。AI4SS 的目标不是做一个会写论文的聊天机器人，而是做一套能让计算社会科学工作被接续、被检查、被拒绝、被修复、被披露的研究基础设施。Deli 的工程思想可以补上“长任务运行生命体征”这一层。

但也要保持清醒：对社会科学来说，AutoResearch 的真正瓶颈不是连续运行 72 小时，而是证据是否真实、数据是否可得、测量是否成立、识别是否支持 claim、AI 参与是否披露、作者是否承担责任。Deli 能让 agent 不停下来，不等于它能让研究变真。

因此，最好的吸收方式不是把 Deli 变成 AI4SS 的新中心，而是把它降格为 runtime governance layer：它负责让工作不断、换向、保活、留痕；AI4SS 的 `.aiss`、MIDA、source gates、methods review 和 disclosure gate 继续负责研究是否站得住。

## 可执行检查表

以后凡是 AI4SS 里预计超过 30 分钟、超过一个 skill、或需要 unattended execution 的任务，都应检查：

- 是否有明确 `task_spec.md` 或等价任务说明
- 是否有唯一研究状态对象，优先是 `research_model.aiss`
- 是否有运行状态：iteration、status、stale_count、last_seen
- 是否记录已试方向，且下一轮方向能证明不同
- 是否把 worker、reviewer、heartbeat 的权限分开
- 是否每轮之后运行测试、编译、lint、validator 或 artifact-aware review
- 是否小批量验证 source-like claims
- 是否连续停滞后进行结构性 pivot，而不是同一路线重试
- 是否在授权边界内自动执行，在授权边界外生成 decision packet
- 是否把 AI 参与和外部分享状态写入 ledger 或 disclosure artifact
