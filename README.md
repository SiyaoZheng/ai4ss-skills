# AI4SS Skills

面向社会科学研究者的 Agent Skills，可在 Claude Code、Cursor 等 AI 编程工具中使用。

**Author**: Siyao Zheng
**Release**: 2026-02-05 · AI4SS Online Lecture

---

## 什么是 Agent Skills？

Skills 是一种可复用的知识包，能让 AI 获得特定领域的专业能力。与普通的 prompt 不同，Skills：

- **按需加载**：AI 根据任务自动判断是否需要调用
- **结构化知识**：包含决策树、检查清单、代码模板等
- **跨工具通用**：同一个 Skill 可在多个 AI 工具中使用

---

## 本仓库包含的 Skills

### 1. latex-tables

生成符合学术期刊规范的 LaTeX 回归表格。

| 功能 | 说明 |
|------|------|
| booktabs 三线表 | 自动使用 `\toprule` / `\midrule` / `\bottomrule` |
| 期刊格式支持 | AEA、APSR、QJE 等主流期刊 |
| 显著性标记 | 星号位置、标准误括号、小数位数 |

**触发方式**：
- 「把这个回归结果转成 LaTeX 表格」
- 「按 AEA 格式做一个 summary statistics」

### 2. analysis-explainer

将统计分析结果转化为面向合作者的技术文档。

| 功能 | 说明 |
|------|------|
| 方法参数记录 | seed、迭代次数、收敛标准等 |
| 图表自动嵌入 | 引用项目中的所有相关图表 |
| 学术写作规范 | 避免 AI 腔，输出专业文档 |

**触发方式**：
- 「帮我解释这些分析结果」
- 「写一份技术说明给合作者」

### 3. r-performance

R 代码性能诊断与优化指南。

| 功能 | 说明 |
|------|------|
| 瓶颈定位 | 使用 profvis 识别慢代码 |
| 优化策略 | 向量化、预分配、并行化决策 |
| HPC 支持 | Slurm / SGE / PBS 集群配置 |

**触发方式**：
- 「这段代码跑得太慢了」
- 「如何在 HPC 上并行运行」

### 4. codex

将任务委托给 OpenAI Codex CLI（GPT-5.3-codex），获取第二意见或利用 Codex 的沙箱执行能力。

> 基于 [@davila7](https://github.com/davila7) 的 [原始 codex skill](https://github.com/davila7/claude-code-templates/tree/main/cli-tool/components/skills/development/codex) 改进。

| 功能 | 说明 |
|------|------|
| 代码审查 | 只读沙箱分析，获取 GPT-5.3 的第二意见 |
| 自动编辑 | workspace-write 沙箱，自动应用修改 |
| 会话恢复 | `codex resume` 继续上次的分析 |

**触发方式**：
- `codex review this file`
- `/codex analyze test coverage`
- `codex resume`

**前置要求**：需安装 [Codex CLI](https://github.com/openai/codex) 并配置凭据。

---

## 安装指南

### Claude Code

Claude Code 是 Anthropic 官方的命令行 AI 工具。Skills 通过目录结构自动发现。

**1. 创建 skills 目录**

```bash
mkdir -p ~/.claude/skills
```

**2. 复制 skill 文件夹**

将本仓库的 skill 文件夹复制到 `~/.claude/skills/`：

```bash
# 克隆仓库
git clone https://github.com/SiyaoZheng/ai4ss-skills.git

# 复制到 Claude Code skills 目录
cp -r ai4ss-skills/latex-tables.skill ~/.claude/skills/latex-tables
cp -r ai4ss-skills/analysis-explainer.skill ~/.claude/skills/analysis-explainer
cp -r ai4ss-skills/r-performance.skill ~/.claude/skills/r-performance
cp -r ai4ss-skills/codex.skill ~/.claude/skills/codex
```

**3. 目录结构**

安装后的目录结构应该是：

```
~/.claude/
└── skills/
    ├── latex-tables/
    │   └── SKILL.md
    ├── analysis-explainer/
    │   └── SKILL.md
    ├── r-performance/
    │   ├── SKILL.md
    │   └── references/
    │       ├── profiling.md
    │       ├── r-internals.md
    │       └── ...
    └── codex/
        └── SKILL.md
```

**4. 验证安装**

在 Claude Code 中输入 `/` 查看可用的 skills，或直接使用：

```bash
claude "把这个回归结果转成 LaTeX 表格"
```

如果 AI 自动应用了 `latex-tables` skill，说明安装成功。

### Cursor

Cursor 支持 Agent Skills 和 Rules 系统。

**方法 A：使用 .cursor/rules/ 目录（推荐）**

Cursor 2026 版本支持模块化 rules。将 skill 内容放入项目的 `.cursor/rules/` 目录：

```bash
# 在项目根目录创建 rules 目录
mkdir -p .cursor/rules

# 复制 skill 内容（需要转换为 .md 格式）
cp ai4ss-skills/latex-tables/SKILL.md .cursor/rules/latex-tables.md
cp ai4ss-skills/r-performance/SKILL.md .cursor/rules/r-performance.md
```

**方法 B：使用全局 skills 目录**

如果 Cursor 支持全局 skills（取决于版本）：

```bash
mkdir -p ~/.cursor/skills
cp -r ai4ss-skills/* ~/.cursor/skills/
```

**方法 C：直接粘贴到 .cursorrules**

对于旧版本 Cursor，可以将 SKILL.md 的内容直接粘贴到项目根目录的 `.cursorrules` 文件中。

### 其他支持 Agent Skills 的工具

以下工具也支持类似的 skill 格式：

| 工具 | Skills 目录 | 备注 |
|------|-------------|------|
| GitHub Copilot | `.github/copilot/` | 需要 Copilot Business |
| Windsurf | `~/.windsurf/skills/` | Codeium 出品 |
| Cline | `~/.cline/skills/` | VS Code 插件 |
| Aider | 通过 `--read` 参数 | 命令行工具 |

具体配置请参考各工具的官方文档。

---

## Skill 文件格式说明

每个 skill 包含一个 `SKILL.md` 文件，由两部分组成：

### 1. YAML Frontmatter（元数据）

```yaml
---
name: latex-tables
description: |
  生成符合学术期刊规范的 LaTeX 回归表格。
  Use when: 回归表格、LaTeX、期刊格式
---
```

| 字段 | 作用 |
|------|------|
| `name` | Skill 名称，用于 `/skill-name` 调用 |
| `description` | 描述，AI 据此判断是否自动加载 |

### 2. Markdown 正文（指令内容）

正文包含：
- 核心指令和决策树
- 检查清单
- 代码模板
- 常见错误和解决方案

AI 会在需要时读取这些内容。

### 支持的高级特性

**引用外部文件**：
```markdown
详细的 profiling 指南见 @references/profiling.md
```

**动态参数**：
```markdown
分析用户提供的文件：$ARGUMENTS
```

---

## 自定义和扩展

欢迎 fork 本仓库并根据自己的需求修改：

1. **调整期刊格式**：修改 `latex-tables` 中的格式规范
2. **添加方法论**：在 `r-performance` 中添加新的优化模式
3. **创建新 skill**：参考现有结构创建自己的领域知识包

---

## 常见问题

**Q: Skill 没有被自动调用？**

检查 `description` 字段是否包含足够的触发词。AI 根据描述判断何时加载 skill。

**Q: 如何手动调用 skill？**

在 Claude Code 中使用 `/skill-name`，如 `/latex-tables`。

**Q: 能否在多个项目中共享 skill？**

可以。放在 `~/.claude/skills/`（全局）而非 `.claude/skills/`（项目级）。

**Q: Skill 和 AGENTS.md 有什么区别？**

| | AGENTS.md | Skills |
|---|-----------|--------|
| 作用域 | 特定项目 | 跨项目通用 |
| 内容 | 项目规则、已知陷阱 | 领域知识、方法论 |
| 加载时机 | 始终加载 | 按需加载 |

---

## 许可

MIT License. 欢迎修改和再分发。

---

## 参考资源

- [Claude Code Skills 官方文档](https://docs.anthropic.com/en/docs/claude-code/skills)
- [Cursor Rules 配置指南](https://cursor.com/docs)
- [Agent Skills 开放标准](https://agentskills.io)

---

*Released at AI4SS Online Lecture 2026*
