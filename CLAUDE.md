## concept-dag

本项目为 ai4ss-skills 的 Phase 2（研究设计 + 执行）开发底层原语：一个社会科学的 machine-readable concept DAG。

### 核心思想

- **attribute** 是原语 — 学者用来组合概念的基本特征
- **concept** 是 typed composition over attributes，带有 composition rule
- 关系使用 SKOS-aligned 封闭词表：`hasAttribute` · `lineageFrom` · `contrastsWith` · `broader` · `narrower` · `related`
- 每个 concept 可挂 `proposed_elsst_label`，后续做 thesaurus 对齐

### 当前产出

| 文件 | 内容 |
|---|---|
| `~/.claude/skills/concept-dag/SKILL.md` | concept-dag skill 定义（含 typed extraction prompt） |
| `concept-dag-out/.cdag_chunk_01.json` | 测试提取得出的 40 concepts · 46 edges（Thomsen et al. 2026 paper） |
| `concept-dag-out/graph.html` | 交互式概念图（打开浏览器即可查看） |
| `concept-dag-out/graph.json` | 完整 graph data |
| `concept-dag-out/elsst-5.rdf` | ELSST 完整 RDF dump（29MB，3,442 concepts，CC-BY-SA） |

### TheSoz thesaurus

TheSoz（GESIS Thesaurus for the Social Sciences）是主要的对齐目标词表：

- 英文 labels 从 GESIS Skosmos REST API 获取：`https://data.gesis.org/cvbrowser/rest/v1/thesoz/`
- topConcepts endpoint 返回 4,572 个英文 label 概念
- children 100% 有英文 label
- license: CC BY-NC-ND（不做商用，可直接用）
- 保存的英文 label 快照：`concept-dag-out/thesoz_top.json`（4,572 top concepts + label + hasChildren flag）

### 架构

```
paper/text ──→ concept-dag subagent ──→ graph.json (typed concept DAG)
                      │                        │
                      │             ┌──────────┘
                      ▼             ▼
              extraction         thesaurus alignment
              prompt            (TheSoz as anchor)
                                agent reads local ELSST RDF
                                + GESIS Skosmos REST API
                                → generates skos:*Match edges
```

底层复用 graphify 的 build/cluster/export HTML 管道。

### 当前进度

- [x] concept-dag skill 安装
- [x] 单篇 paper 测试提取（40 concepts, 46 edges, typed schema）
- [x] ELSST RDF dump 下载
- [x] TheSoz 英文 labels 确认可用（GESIS Skosmos REST）
- [ ] ELSST ↔ TheSoz 词表对齐（retrieval agent → matching agent）
- [ ] paper concept → TheSoz 映射
- [ ] Turtle export（SKOS + aiss namespace）
- [ ] attribute 层正确区分（v0 extraction 把 attribute 全归为 concept 了）
