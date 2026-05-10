# Extraction Protocol v0.1

> 从社会科学论文到 aiss DSL 的确定性翻译规则。
> 配套 `dsl-spec.md`。每条规则附带判定依据（linguistic cue / structural cue）。

## 核心原则

1. **每个 DSL 字段必须有文本证据**——不能凭空生成
2. **证据 = 具体引用**（页/段/句），不是模糊定位
3. **判定规则优先于 LLM 判断**——规则能决定的，不由 agent 决定
4. **不确定 → INFERRED，不丢弃**——宁可疑似保留，不能静默删除

---

## Phase 1: Segment — 找边界

### R1. 章节分类

| 匹配词（累计计分） | 分类 |
|---|---|
| research design, method, data, sample, treatment, measure, estimation, variable, procedure, experiment, survey, empirical, operational | methods |
| finding, result, discussion, robustness, conclusion, limit, implication | findings |
| introduction, background, literature, framework, theory, conceptual, hypothesis, model, prior work, context | theory |

**R1a. 位置启发式**：关键词不明确时，前 25% 论文 → theory，后 75% → findings。

**R1b. Abstract**：第一个章节标题之前的所有内容。

**R1c. References/Appendix**：归入 findings。

### R2. 切分执行

```
python3 scripts/segment_paper.py PAPER_TXT WORK_DIR \
  --abstract-end N1 --theory-end N2 --methods-end N3
```

---

## Phase 2: Attribute vs. Concept — 判定

### R3. Attribute 判定

X 是 attribute，当且仅当：
- X 可以指向数据集中的**单一列**
- X 的值域可以枚举（binary / ordinal / categorical / continuous）
- 不需要组合规则——X 的值就是 X 的测量

**Linguistic cues**："measured as"、"coded as"、"取值"、"0/1"、"scale from 1 to N"

### R4. Concept 判定

X 是 concept，当且仅当：
- X 需要**组合多个 measurement + 一个规则**才能成立
- 无法指向数据集中单一列

**Linguistic cues**："defined as"、"consists of"、"composed of"、"由...构成"、"综合...指标"、"index of"

### R5. Ambiguous 默认规则

不确定 attribute 还是 concept → `concept` + `composition_rule: "undecomposed"`。

---

## Phase 3: θ 提取

### R6. θ 表格填充

对于 concept C，已确定其 parent attributes A₁...Aₙ：

**Step 1**: 列出所有属性值组合（笛卡尔积）

**Step 2**: 对每个组合，判定 C 是否成立：
- 文本直接陈述 → EXTRACTED，填入
- 可从定义合理推导 → INFERRED，填入，标注推理依据
- 文本未涉及 → INFERRED（基于 composition rule 的模式补全），标注"未在文本中明确讨论"

**Step 3**: 记录证据：
```
| capacity | scrutiny | outcome | evidence |
| low      | low      | inert   | "when both are low, the state is inert" (Ch.1, p.35) |
```

### R7. Composition Rule 判定

| Rule | Linguistic Cues | θ 约束 |
|---|---|---|
| `definitional` | "is"、"就是"、"定义为"、唯一标识性表述 | Count(outcome=1) = 1 |
| `necessary_conjunction` | "and"、"all"、"同时满足"、"缺一不可"、"必须同时" | Count(outcome=1) = 1 |
| `sufficient_conjunction` | "or"、"either"、"任一"、"只要" | Count(outcome=1) ≥ 1 |
| `aggregative` | "average"、"sum"、"index"、"综合"、"加总"、"平均" | outcome monotonic |
| `threshold` | "at least"、"above"、"超过"、"达到...以上" | ∃k: outcome=1 ⟺ Σ ≥ k |
| `family_resemblance` | "most of"、"majority"、"多数"、"大部分" | majority(parents satisfied) → 1 |
| `undecomposed` | 无分解线索 | θ = {"none": 1} |
| `exhaustive_typology` | 2×2/多维交叉表、"typology"、"分类"、"四种类型" | 所有输出互异 |

### R8. θ 完备性检查

θ 的行数必须 = Π|Dᵢ|（全部 parent 值域的笛卡尔积）。
不完整时：
- 缺失行在文本中有线索 → 提取
- 缺失行文本未讨论 → INFERRED，基于 composition_rule 的模式补全，标注 "text does not discuss this combination"

---

## Phase 4: 关系提取

### R9. hasAttribute 判定

从 concept C 到 X 的 hasAttribute edge 成立，当且仅当：
- X 是 attribute
- θ_C 包含 X 作为 parent
- 文本表明 C 由 X 构成

**composition_value**: C 成立时 X 必须取的值。如果 θ_C 的 C=1 行中 X 取多个不同值 → composition_value 为 `*`（任意值）。

### R10. causes 判定

从 concept C₁ 到 C₂ 的 causes edge 成立，当且仅当：
- 文本断言改变 C₁ 会导致 C₂ 改变（all else equal）
- 不是"相关"而是"导致"——文本必须有因果语言

**Linguistic cues**："leads to"、"causes"、"increases/decreases"、"affects"、"effect of"、"导致"、"引起"、"降低"、"提高"、"作用"、"影响"、"because"

**反例**（不是 causes）：
- "is associated with"、"correlated with"、"相关"、"有关" → `related`
- "X is a component of Y" → `hasAttribute`
- "X is broader than Y" → `broader`

**Required sub-fields**:
- `direction`: positive / negative / null / nonlinear（从文本中直接提取方向词）
- `condition`: 因果关系的范围条件（如无，null）
- `mechanism`: 因果路径（从文本中提取 mechanism language："through"、"via"、"by"、"通过"、"机制"、"途径"）

### R11. Commensurability 判定

| Level | 判定条件 |
|---|---|
| `strong` | 理论蕴涵 + 研究设计可信地估计了同样的 all-else-equal 关系 |
| `weak` | 估计的是相关性或 reduced form，但论文解释为因果 |
| `unchecked` | 断言了因果关系但没有连接任何实证估计 |

**Linguistic cues for strong**："identify causal effect"、"exogenous variation"、"random assignment"、"natural experiment"、"IV"、"DiD"、"RDD"
**Linguistic cues for weak**："control for"、"conditional on"、"adjust for"、"association"、"correlation"（在标题中声称因果，在稳健性部分称相关）
**Linguistic cues for unchecked**：理论部分有因果语言但实证部分没有对应的估计

### R12. contrastsWith 判定

C₁ 和 C₂ 之间存在 contrastsWith edge，当且仅当：
- 论文**显式对比**两个概念
- "X vs. Y"、"unlike X, Y..."、"in contrast to"、"区别于"、"不同于"、"相对"、"对比"

### R13. broader / narrower 判定

C₁ → C₂ 是 broader，当且仅当：
- C₁ 是 C₂ 的上位概念（更一般）
- "including"、"such as"、"例如"、"包括"、"分为"、"是一种"

### R14. related 判定

作为兜底关系——C₁ 和 C₂ 之间有联系但不是上述任何一种：
- 相关但不清晰是因果还是构成
- 同一概念在不同测量下的两个版本
- "is associated with"、"involves"、"涉及"、"有关"

---

## Phase 5: Confidence 标定

### R15. EXTRACTED (1.0)

- 文本中有**直接引用**可支持
- 字段内容与文本表述**逐字对应或近乎逐字对应**
- 不需要推理跳跃

### R16. INFERRED (0.6–0.9)

- 文本中有暗示但非直接陈述 → 0.8–0.9
- 需要一步推理 → 0.7–0.8
- 缺失 θ 行基于 composition rule 模式补全 → 0.6–0.7

### R17. AMBIGUOUS (0.1–0.3)

- 文本有多重解读 → 0.3
- 只有一个词暗示了关系 → 0.1–0.2

### R18. INFERRED 比例目标

目标 15-25% edges 为 INFERRED。低于 10% → 过于保守（错过了隐含信息）。高于 30% → 过于激进（猜测太多）。

---

## Phase 6: 证据表格式

每个 concept 的输出必须先填写证据表，再编译为 DSL JSON：

```markdown
## Concept: governance_mode
- **ID**: ding.governance_mode
- **Parents**: state_capacity {low, high} × public_scrutiny {low, high}
- **Composition Rule**: exhaustive_typology
- **Evidence**: typology defined in Ch.1, pp.35-36

| capacity | scrutiny | outcome | confidence | evidence |
|----------|----------|---------|------------|----------|
| low      | low      | inert   | EXTRACTED  | "when both are low, the state neither has the capacity nor feels the pressure to respond — it is inert" (p.35) |
| high     | low      | paternalistic | EXTRACTED | "high capacity, low scrutiny → paternalistic governance" (p.36) |
| low      | high     | performative | EXTRACTED | "low state capacity and high public scrutiny... performative governance" (p.7) |
| high     | high     | substantive | EXTRACTED | "ideal case... substantive governance" (p.36) |
```

证据表 → aiss DSL 的编译由 `dsl/scripts/compile_evidence.py` 机械执行。
该脚本已实现，并被 `dsl/scripts/test_conformance.py` 覆盖；运行方式：

```bash
python3 dsl/scripts/compile_evidence.py dsl/scripts/test_fixtures/ding_evidence.md
```

---

## 提取流程总图

```
                     Extraction Protocol (本文件)
                            ↓ 约束每一步
Paper.txt → [Pass 0: Segment] → section files
                ↓
         [Pass 1-3: Evidence Tables]
          每格有 text span 引用
                ↓
         [机械编译] → DSL JSON
                ↓
         [T1-T8 自动验证]
                ↓
         验证通过 → 产出 / 验证失败 → 标记人工审核
```

---

## Inter-Extractor Reliability（两个 Agent 之间的校准）

### IER1. 双提取

同一篇论文被两个独立 agent 提取（不同 LLM call）。

### IER2. 比对

- 概念列表差异 → 标记为 `concept_disagreement`
- θ 表格差异 → 逐行比较，标记为 `theta_disagreement`
- 关系差异 → 逐边比较，标记为 `relation_disagreement`
- Textual support / confidence 差异 → 标记但通常不裁决（它们本质上是证据强度判断）

### IER3. 裁决

- EXTRACTED vs. EXTRACTED 但值不同 → **回到原文裁决**（哪个有更好的文本证据？）
- EXTRACTED vs. AMBIGUOUS → 保留 EXTRACTED
- INFERRED vs. INFERRED 但值不同 → 两个都保留，标记分歧
