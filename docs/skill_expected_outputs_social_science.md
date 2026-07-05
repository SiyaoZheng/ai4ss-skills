# AI4SS Skills：论文生产中的输入文件与输出文件接力表

这是一张面向研究者的文件接力表。重点看每一行的输出文件，是否能成为后续 skill 的输入文件。具体执行契约仍以 `skills/<skill-name>/SKILL.md` 为准；研究工厂项目中的持久状态应进入 `.ai4ss/research_model.aiss`。

最新运行边界：`.aiss` 不只是交接文件，而是 research-factory 的状态机对象。`route`、`mida`、`decision`、source、artifact、check、claim 等声明保存语义研究状态；`event` 声明保存 skill start/completion/failure、heartbeat、watchdog recovery 等运行事实。用 `python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` 投影当前状态，用 `aiss.py transition --event '<json>'` 预览或追加状态转移。`goal-cli` 仍然负责外部 watchdog、timer、lock、heartbeat 和进程恢复；skill 只记录事实和交接，不接管这些进程职责。

| 顺序 | Skill | 具体输入文件/路径 | 具体输出文件/路径 | 输出接给谁 |
|---:|---|---|---|---|
| 1 | `research-starter` | 无硬性输入文件；可读作者笔记、资料目录、种子来源、一句话 idea | `.ai4ss/research_model.aiss`，写入 candidate `route` / `decision` 声明并自动选中最佳 route | `study-design-builder` |
| 2 | `study-design-builder` | route-only `.ai4ss/research_model.aiss`；文献笔记、变量字典、数据预览、政策时间线 | `.ai4ss/research_model.aiss`，写入 selected `route`、七个 `mida`、`decision`、model-layer 声明；`.ai4ss/checks/ai4ss_check_report.txt` | `public-data-sources`、`literature-matrix`、`methods-reviewer` |
| 3 | `public-data-sources` | `.ai4ss/research_model.aiss`；MIDA data strategy；目标单位、时期、地区、变量；来源候选或搜索任务 | 真实观察来源候选与自动选择；`source_access_status`；`official_docs_url`；`request_template`；可缓存 source artifact；来源 provenance | `research-data-builder`，或不可行时回 `study-design-builder` 自动改设计 |
| 4 | `literature-matrix` | `.ai4ss/research_model.aiss`；PDF/Zotero/书目/URL/本地文献文件 | 更新 `.ai4ss/research_model.aiss` 或生成 `.aiss` 片段：`paper`、`source`、`span`、`claim`、`relation`、`check`、`decision` | `study-design-builder`、`methods-reviewer`、`academic-writing-scaffold` |
| 5 | `research-data-builder` | `.ai4ss/research_model.aiss`；`public-data-sources` 交付的真实来源 artifact/request output；变量字典；抽取规则；可选 `ddi-metadata.yaml` | `scripts/*` 数据脚本；`data/raw/`、`data/intermediate/`、`data/processed/`；`row_source_provenance`；更新 `.ai4ss/research_model.aiss` | `research-analysis-runner`、`methods-reviewer` |
| 6 | `research-analysis-runner` | `.ai4ss/research_model.aiss`；`data/processed/`；变量字典；分析计划；`scripts/*` | `scripts/*` 分析脚本；`output/tables/`；`output/figures/`；`output/models/`；`output/logs/`；更新 `.ai4ss/research_model.aiss` | `top-journal-figures`、`methods-reviewer`、`latex-tables`、`analysis-explainer` |
| 7 | `top-journal-figures` | `.ai4ss/research_model.aiss`；`scripts/*.R`；`output/models/`；`output/tables/`；figure data；source artifacts；可选 `fixest`、`did`、`marginaleffects`、`modelsummary`、`cregg`、`binsreg`、`rdrobust` 等 R 输出 | `scripts/figure_style.R` 或项目 house style；`scripts/*figure*.R`；`output/figures/*.pdf|*.svg`；命名 ggplot2 对象；显式 `ggsave()`；caption；source/sample/uncertainty notes；`.aiss` style-consistency/visual-integrity/vector/black-white checks | `methods-reviewer`、`academic-writing-scaffold`、`research-slides-builder` |
| 8 | `did-expert` | DID/面板分析脚本，如 `scripts/*.R`；真实观察面板数据，如 `data/processed/*`；已生成 DID 表图 | 无固定新文件；通常修改或检查 `scripts/*.R`，要求相应诊断表图实际存在于 `output/tables/`、`output/figures/` | `research-analysis-runner`、`top-journal-figures`、`methods-reviewer` |
| 9 | `methods-reviewer` | `.ai4ss/research_model.aiss`；`scripts/*`；`output/logs/`；`output/tables/`；`output/figures/`；`data/processed/`；论文片段 | 更新 `.ai4ss/research_model.aiss` 的 `check`、`decision` 或 bounded claim-support 声明；无默认独立报告文件 | `public-data-sources`、`research-data-builder`、`research-analysis-runner`、`top-journal-figures`、`academic-writing-scaffold` |
| 10 | `latex-tables` | 回归/描述统计/平衡表结果文件，通常来自 `output/tables/` 或软件输出；目标 `.tex` 文件名 | `<stem>.tex`；`<stem>-table-preview.html` | `academic-writing-scaffold`、`analysis-explainer`、`paper/` |
| 11 | `analysis-explainer` | 全部结果文件：`output/figures/*.png|*.pdf`、`output/tables/*.csv|*.docx`、`scripts/*`、`output/logs/*` | 技术说明 Markdown，如 `<analysis>-summary.md`；PDF，如 `<analysis>-summary.pdf` 或命令指定的 `output.pdf` | `academic-writing-scaffold`、`methods-reviewer` |
| 12 | `academic-writing-scaffold` | `.ai4ss/research_model.aiss`；`output/tables/`；`output/figures/`；`output/logs/`；文献证据；作者草稿；表图 caption | 更新 `.ai4ss/research_model.aiss` 的 bounded `claim`、report-boundary `mida`、`decision`；可修改 `paper/*.tex` 并生成 `paper/full_draft.pdf`；必要时更新 `docs/ai_use_ledger.csv` | `reviewer-response`、`research-slides-builder`、`paper/` |
| 13 | `research-slides-builder` | `.ai4ss/research_model.aiss`；已核查 claim；`output/tables/`；`output/figures/`；已有 deck 文件 | 更新 `.ai4ss/research_model.aiss` 的 presentation `artifact` / bounded `claim` / privacy `check`；可输出项目命名的 deck，如 `.pptx`、`.html`、`.pdf` | 汇报材料；`reviewer-response` 可复用 claim 边界 |
| 14 | `reviewer-response` | 编辑信、审稿意见、`paper/*`、appendix、`output/tables/`、`output/figures/`、`.ai4ss/research_model.aiss` | 更新 `.ai4ss/research_model.aiss` 的 reviewer-request `decision`、evidence `artifact`、response-boundary `check`；可修改 response letter 或 `paper/*` | `public-data-sources`、`research-analysis-runner`、`methods-reviewer`、`academic-writing-scaffold` |
| 15 | `codebook-parse` | 调查文件：`.dta`、`.sav`、`.sas7bdat`、DDI `.xml`、CFPS `.yaml`、`.csv`+字典 `.csv/.xlsx`、问卷 `.pdf/.docx` | `ddi-metadata.yaml`；`<stem>-codebook.pdf`；`<stem>-codebook.html` | `cleaning-contract` |
| 16 | `cleaning-contract` | `ddi-metadata.yaml` | 同一个 `ddi-metadata.yaml`，新增或更新 `cleaning_contract` 和 `processing_events`；不生成 clean data | `cleaning-execute` |
| 17 | `cleaning-execute` | 带 `cleaning_contract` 的 `ddi-metadata.yaml`；`study.data_source` 指向的原始数据文件 | `<stem>-clean.csv`；`<stem>-cleaning.R`；更新 `ddi-metadata.yaml` 的 `processing_events` | `research-data-builder` 或 `research-analysis-runner` |
| 18 | `codex` | 目标代码文件/目录；命令 prompt；可选 image；可选 `--output-schema <path>` | 修改后的代码文件；可选 `-o <path>` 最终回答；可选 `--json` JSONL 事件流；Codex session | 代码修复、评审或后续 `codex resume` |
| 19 | `r-performance` | 慢 R 脚本，如 `scripts/*.R`；before/after 对照文件 `before.R`、`after.R`；可选 `perf-summary.json` | 优化后的 R 代码；`perf-report.html`；可选更新 `perf-summary.json` | `research-analysis-runner`、`methods-reviewer` |
| 20 | `sjtu-hpc` | Slurm 模板：`skills/sjtu-hpc/assets/*.slurm`；项目脚本；数据；HPC SSH/config 信息 | 作业脚本 `.slurm`；Slurm 输出如 `slurm-<jobid>.out`；传输/清理命令；配额/计费检查结果 | `research-data-builder`、`research-analysis-runner`、`r-performance` |

核心主链条是：

```text
.ai4ss/research_model.aiss
→ public source artifact / request output
→ data/processed/
→ output/tables/, output/models/, output/logs/
→ shared ggplot2 style profile + figure scripts + output/figures/*.pdf|*.svg
→ paper/*.tex / paper/*.pdf
→ reviewer-response 的 revision state
```

DDI 调查清洗链条是：

```text
survey file
→ ddi-metadata.yaml
→ ddi-metadata.yaml + cleaning_contract
→ <stem>-clean.csv + <stem>-cleaning.R
→ data/processed/ 或 analysis-ready input
```
