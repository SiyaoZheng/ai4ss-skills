# AI4SS Skills Release

**Author**: Siyao Zheng
**Release Date**: 2026-02-05

三个面向社会科学研究者的 Agent Skills，可在 Claude Code、Cursor、Codex 等支持 Agent Skills 的 AI 工具中使用。

---

## 1. latex-tables

**用途**：生成符合学术期刊规范的 LaTeX 回归表格

- 使用 booktabs 样式（三线表）
- 支持 AEA、APSR 等期刊格式
- 自动添加显著性标记和标准误注释

**触发场景**：
- 将回归结果转换为 LaTeX
- 格式化描述统计表
- 投稿前统一表格风格

---

## 2. analysis-explainer

**用途**：将统计分析结果转化为技术文档

- 面向方法论专家和合作者
- 自动嵌入所有图表
- 遵循学术写作规范，避免 AI 腔

**触发场景**：
- 「帮我解释分析结果」
- 「写一下 findings 给合作者看」
- 需要为论文准备技术附录

---

## 3. r-performance

**用途**：R 代码性能诊断与优化

- 定位瓶颈（profvis）→ 诊断原因 → 选择策略 → 实施优化
- 涵盖向量化、预分配、并行化等常见模式
- 支持 HPC 集群配置（Slurm/SGE/PBS）

**触发场景**：
- 「这段代码跑得太慢了」
- 「如何在 HPC 上并行运行」
- 「帮我优化这个循环」

---

## 安装方法

将 `.skill` 文件放入：
- **Claude Code**: `~/.claude/skills/`
- **Cursor**: `~/.cursor/skills/`
- 其他工具：参考各工具的 Agent Skills 文档

---

## 许可

MIT License. 欢迎修改和再分发。

---

*Released at AI4SS Online Lecture 2026*
