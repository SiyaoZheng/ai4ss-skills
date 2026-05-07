# aiss DSL — Core Specification v0.2

> 一个表达社会科学理论的外部 DSL。
> 数学基础：FCA（形式概念分析）+ SCM（结构因果模型）+ Description Logic。
> 设计参考：Alloy 的原语分离 · Z 的 schema 组合 · LinkML 的 schema-first · DeclareDesign 的设计即数据。

## 0. 设计原则

1. **外部语法** — 独立语言，不嵌入 Python/R。有 parser，有 AST。
2. **数学基础不必发明** — FCA 处理概念定义（θ），SCM 处理因果关系，DL 处理概念层次。
3. **定义与验证分离** — 像 Alloy：先定义结构（attribute/concept/causal），再检查属性（check/derive）。
4. **分层表达** — 像 OWL：Layer 0-1 可判定，Layer 2 半可判定，Layer 3 需人类判断。
5. **Schema-first** — 像 LinkML：schema 是数据，数据是 schema 的实例。

---

## 1. Formal Context (from FCA)

本 DSL 的数学基础是形式概念分析。每一个 concept 定义等价于 FCA 中的一个形式概念。

### 1.1 FCA 基本定义（Ganter & Wille 1999）

**形式上下文** K = (G, M, I)，其中 G 是对象集，M 是属性集，I ⊆ G × M 是关联关系。

**导出算子** (derivation operators)：
- A↑ = { m ∈ M | ∀g ∈ A : (g,m) ∈ I }  — A 中所有对象共享的属性
- B↓ = { g ∈ G | ∀m ∈ B : (g,m) ∈ I }  — 拥有 B 中所有属性的对象

**形式概念** = (A, B) 满足 A↑ = B 且 B↓ = A。A = 外延 (extent)，B = 内涵 (intent)。

**属性蕴涵** A → B 在 K 中有效，当 A↓ ⊆ B↓。

### 1.2 映射到本 DSL

| FCA | aiss DSL |
|---|---|
| 形式上下文 K | 所有 attribute × 所有可能的 attribute value 组合 |
| 属性 m ∈ M | 一个 attribute = value 对，如 `state_capacity=low` |
| 对象 g ∈ G | 一个观测/案例（论文中通常隐式） |
| 形式概念 (A, B) | 一个 concept，其 intent = θ 中输出为 1/Category 的 attribute 组合 |
| 属性蕴涵 A → B | hasAttribute edge：拥有 attribute A → 拥有 concept C |
| 概念格 | broader/narrower 关系（基于外延包含） |

**θ 即 Intent**：一个 concept 的 θ 真值表就是 FCA 中该形式概念的内涵（intent）的直接表达。

---

## 2. Language Syntax

### 2.1 Lexical

```
ID        = [a-z][a-z0-9_]*
QUALID    = ID "." ID               -- author.concept_name
STRING    = "\"" ([^"\\] | "\\" .)* "\""   -- supports \" \\ \n \t escapes
NUMBER    = [0-9]+ ( "." [0-9]+ )?
BOOL      = "0" | "1"
VALUE     = STRING | NUMBER | BOOL
COMMENT   = "//" ... end-of-line
```

### 2.2 Top-Level Constructs

```
program = (attribute | concept | causal | bridge | model | fact | check | derive)*
```

**没有 order 依赖**——可以 forward-reference。像 Alloy，声明顺序不影响语义。

### 2.3 Attribute

```
attribute ding.state_capacity {
  domain: ordinal
  values: ["low", "high"]
  description: "logistical and political capacity of a bureaucratic unit"
}
```

**Fields**:
- `domain` (required): `binary | ordinal | categorical | continuous`
- `values` (required for binary/ordinal/categorical): 允许的值列表
- `description` (optional): 自然语言定义
- `source` (optional): 文本证据引用

### 2.4 Concept

```
concept ding.governance_mode {
  parents: [ding.state_capacity, ding.public_scrutiny]
  theta: {
    "[\"low\",  \"low\"]"  : "inert"
    "[\"high\", \"low\"]"  : "paternalistic"
    "[\"low\",  \"high\"]" : "performative"
    "[\"high\", \"high\"]" : "substantive"
  }
  theta_domain: categorical
  rule: exhaustive_typology
  description: "2x2 typology: state capacity × public scrutiny → 4 governance modes"
  source: "Ch.1, pp.35-36"
  operationalization: "ethnographic observation at municipal EPB"
  elsst_label: "governance"
}
```

**Fields**:
- `parents` (required): 父属性列表，顺序与 θ 键中的值顺序对应
- `theta` (required): 真值表。键 = parent values 的 JSON 数组字符串，值 = 0/1（binary concept）或 string（categorical/nominal concept）
- `theta_domain` (optional): `binary | categorical | continuous`。缺省时由 θ 输出值推断
- `rule` (required): composition rule
- `description` (optional)
- `source` (optional): 文本证据
- `operationalization` (optional): 如何测量
- `elsst_label` (optional): ELSST/TheSoz 对齐标签

**θ 键的排序**：θ 键中 value 的顺序 == parents 列表中 attribute 的顺序。

**hasAttribute 隐式生成**：`concept.parents` 字段在编译时自动生成对应的 `hasAttribute` edge（从 concept 到每个 parent attribute）。

### 2.5 Composition Rules

| Rule | θ Pattern | FCA 对应 |
|---|---|---|
| `definitional` | Exactly 1 row → 1（binary θ） | 单例 intent |
| `necessary_conjunction` | All parents at designated values → 1 | 精确匹配 intent |
| `sufficient_conjunction` | Any parent at designated value → 1 | 析取 intent |
| `aggregative` | Outcome monotonic in sum of parent values | 加性闭合 |
| `threshold` | Σ ≥ k → 1 | 阈值分割 |
| `family_resemblance` | Majority(parents satisfied) → 1 | 多数投票 |
| `undecomposed` | θ = `{"none": 1}` | 原子概念（无属性分解） |
| `exhaustive_typology` | All outcomes distinct nominal categories | 多值分区；不强行解释为 binary FCA membership |

### 2.6 Causal Relation

```
causal ding.lc_hs_to_performative {
  source: ding.low_capacity_high_scrutiny
  target: ding.performative_governance
  direction: positive
  condition: none
  mechanism: "beleaguered bureaucracy — bureaucrats cannot fix the problem, so they fix the perception"
  textual_support: EXTRACTED
}
```

**Fields**:
- `source` (required): 原因 concept ID
- `target` (required): 结果 concept ID
- `direction` (required): `positive | negative | null | nonlinear`
- `condition` (optional): 范围条件/调节变量
- `mechanism` (optional): 因果路径
- `textual_support` (required): `EXTRACTED | INFERRED | AMBIGUOUS`。这里只表示论文文本是否清楚提出该理论因果声称；不表示实证识别强度

**语义边界**：`causal` 表达理论声称。理论上的因果性不等于实证上已经观察到因果关系；实证相关、事实观察、民族志证据或估计量是否与该理论声称可公度，由 `bridge` 表达。

### 2.7 Bridge

```
bridge ding.measurement_pg {
  type: measurement
  concept: ding.performative_governance
  method: participant_observation
  validity: "observed bureaucratic actions coded as targeting problem vs. perception"
  commensurability: strong
}

bridge ding.causal_bridge_1 {
  type: causal
  implication: ding.lc_hs_to_performative
  estimand: none
  commensurability: weak
  note: "ethnographic evidence, no quantitative causal identification"
}
```

**Fields**:
- `type` (required): `measurement | causal`
- For measurement bridge:
  - `concept` (required): 被测量的 concept
  - `method` (required): 测量方法
  - `validity` (optional): 效度说明
- For causal bridge:
  - `implication` (required): causal edge ID
  - `estimand` (required or `none`): 实证估计量
- `commensurability` (required): `strong | weak | unchecked`

### 2.8 Model

```
model ding.performative_state {
  attributes: [
    ding.state_capacity
    ding.public_scrutiny
  ]
  concepts: [
    ding.governance_mode
    ding.performative_governance
    ding.substantive_governance
    ding.inert_governance
    ding.paternalistic_governance
    ding.perceived_responsiveness
    ding.performative_breakdown
  ]
  causal: [
    ding.lc_hs_to_performative
  ]
  bridges: [
    ding.measurement_pg
    ding.causal_bridge_1
  ]
}
```

### 2.9 Relation Edges (broader/narrower/contrastsWith/related)

```
edge broader: ding.governance_mode -> ding.performative_governance {
  confidence: EXTRACTED
  source: "Ch.1, p.36"
}
```

### 2.10 Facts — Static Constraints (Alloy-inspired)

Facts 是必须始终成立的约束。相当于 T1-T8 验证规则的声明形式。

```
fact theta_completeness {
  all c: concept where c.parents != [] {
    // definitional concepts: sparse θ OK — only C=1 rows need be listed
    if c.rule == "definitional" {
      count(v in c.theta.values where v == 1 or v == "1") == 1
        and |c.theta| <= product(|p.values| for p in c.parents)
    } else {
      |c.theta| == product(|p.values| for p in c.parents)
    }
  }
}

fact no_self_loop {
  no e: edge where e.source == e.target
}

fact hasAttribute_domain {
  all e: edge where e.relation == "hasAttribute" {
    typeof(e.source) == concept and typeof(e.target) == attribute
  }
}

fact causes_domain {
  all e: edge where e.relation == "causes" {
    typeof(e.source) == concept and typeof(e.target) == concept
  }
}

fact id_format {
  all id: ID where id is QUALID {
    id matches /^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$/
  }
}

fact no_orphan_concepts {
  all c: concept {
    c in edges.source or c in edges.target or c.rule == "undecomposed"
  }
}
```

### 2.11 Check — 验证命令 (Alloy-inspired)

```
check theta_completeness on ding.performative_state
check rule_consistency on ding.performative_state
check reference_integrity on ding.performative_state
```

### 2.12 Derive — 推导命令

```
derive implications from ding.performative_state
derive transitive_closure from ding.performative_state
derive ibe_profile from ding.performative_state
```

---

## 3. Complete Example: Ding (2022)

```
// ============================================================
// Model: The Performative State
// Source: Ding, Iza. 2022. The Performative State.
//         Cornell University Press.
// ============================================================

// ---- Attributes (FCA: 这是 M —— 属性集) ----

attribute ding.state_capacity {
  domain: ordinal
  values: ["low", "high"]
  description: "logistical and political capacity of a bureaucratic unit to deliver on governance goals"
  source: "Ch.1, pp.25-35"
}

attribute ding.public_scrutiny {
  domain: ordinal
  values: ["low", "high"]
  description: "degree to which public is attuned to an issue and exerting pressure on the state"
  source: "Ch.1, pp.25-35"
}

// ---- Concepts (FCA: 这是形式概念) ----

// 2×2 typology — composite concept
concept ding.governance_mode {
  parents: [ding.state_capacity, ding.public_scrutiny]
  theta: {
    "[\"low\",  \"low\"]"  : "inert"
    "[\"high\", \"low\"]"  : "paternalistic"
    "[\"low\",  \"high\"]" : "performative"
    "[\"high\", \"high\"]" : "substantive"
  }
  rule: exhaustive_typology
  description: "typology of state-bureaucratic behavior along two dimensions"
  source: "Ch.1, pp.35-36"
  elsst_label: "governance"
}

// Individual governance modes — derived from the typology
// Each has a 1-row θ (definitional) because it IS a specific cell of the typology
concept ding.performative_governance {
  parents: [ding.state_capacity, ding.public_scrutiny]
  theta: {
    "[\"low\", \"high\"]": 1
  }
  rule: definitional
  description: "deployment of visual, verbal, and gestural symbols of good governance"
  source: "Introduction, p.7"
  operationalization: "ethnographic coding: does bureaucratic action target problem substance or public perception?"
  elsst_label: "governance"
}

concept ding.substantive_governance {
  parents: [ding.state_capacity, ding.public_scrutiny]
  theta: {
    "[\"high\", \"high\"]": 1
  }
  rule: definitional
  description: "governance geared towards delivering effective results"
  source: "Ch.1, p.36"
}

concept ding.inert_governance {
  parents: [ding.state_capacity, ding.public_scrutiny]
  theta: {
    "[\"low\", \"low\"]": 1
  }
  rule: definitional
  description: "state neither has capacity nor faces pressure — inert"
  source: "Ch.1, p.35"
}

concept ding.paternalistic_governance {
  parents: [ding.state_capacity, ding.public_scrutiny]
  theta: {
    "[\"high\", \"low\"]": 1
  }
  rule: definitional
  description: "high capacity, low scrutiny — paternalistic (predatory or developmental)"
  source: "Ch.1, p.36"
}

// The conjunction condition: low capacity + high scrutiny
// Ding's theory: THIS specific combination causes performative governance
concept ding.low_capacity_high_scrutiny {
  parents: [ding.state_capacity, ding.public_scrutiny]
  theta: {
    "[\"low\", \"high\"]": 1
  }
  rule: definitional
  description: "the condition of being under-resourced yet under intense public pressure"
  source: "Ch.1, pp.35-36"
}

// Audience-side concepts
concept ding.perceived_responsiveness {
  parents: []
  theta: {
    "\"none\"": 1
  }
  rule: undecomposed
  description: "citizens' perception that the government is responsive to their concerns"
  operationalization: "citizen surveys and interviews"
}

concept ding.performative_breakdown {
  parents: []
  theta: {
    "\"none\"": 1
  }
  rule: undecomposed
  description: "when performative governance ceases to occur or fails to work"
  source: "Ch.5, p.135"
}

concept ding.audience_cynicism {
  parents: []
  theta: {
    "\"none\"": 1
  }
  rule: undecomposed
  description: "citizens learn to see through the performance"
  source: "Ch.5"
}

// ---- Causal Relations (SCM: 因果 DAG) ----

causal ding.lc_hs_to_performative {
  source: ding.low_capacity_high_scrutiny
  target: ding.performative_governance
  direction: positive
  condition: none
  mechanism: "beleaguered bureaucracy"
  textual_support: EXTRACTED
}

causal ding.performative_to_perception {
  source: ding.performative_governance
  target: ding.perceived_responsiveness
  direction: positive
  condition: "audience not cynical"
  mechanism: "impression management — appearing responsive, benevolent, humble"
  textual_support: EXTRACTED
}

causal ding.cynicism_to_breakdown {
  source: ding.audience_cynicism
  target: ding.performative_breakdown
  direction: positive
  condition: none
  mechanism: "audience learns to see through performance → performance loses effect"
  textual_support: INFERRED
}

// ---- Edges ----

edge broader: ding.governance_mode -> ding.performative_governance {
  confidence: EXTRACTED
  source: "typology structure, Ch.1"
}

edge broader: ding.governance_mode -> ding.substantive_governance {
  confidence: EXTRACTED
  source: "typology structure, Ch.1"
}

edge broader: ding.governance_mode -> ding.inert_governance {
  confidence: EXTRACTED
  source: "typology structure, Ch.1"
}

edge broader: ding.governance_mode -> ding.paternalistic_governance {
  confidence: EXTRACTED
  source: "typology structure, Ch.1"
}

// ---- Bridges ----

bridge ding.measurement_pg {
  type: measurement
  concept: ding.performative_governance
  method: participant_observation
  validity: "key observable implications: night inspections, dress/consumption behavior in public, emotional management toward citizens"
  commensurability: strong
}

bridge ding.causal_bridge_1 {
  type: causal
  implication: ding.lc_hs_to_performative
  estimand: none
  commensurability: weak
  note: "no quantitative causal identification; ethnographic plausibility probe"
}

// ---- Model ----

model ding.performative_state {
  attributes: [
    ding.state_capacity
    ding.public_scrutiny
  ]
  concepts: [
    ding.governance_mode
    ding.low_capacity_high_scrutiny
    ding.performative_governance
    ding.substantive_governance
    ding.inert_governance
    ding.paternalistic_governance
    ding.perceived_responsiveness
    ding.performative_breakdown
    ding.audience_cynicism
  ]
  causal: [
    ding.lc_hs_to_performative
    ding.performative_to_perception
    ding.cynicism_to_breakdown
  ]
  bridges: [
    ding.measurement_pg
    ding.causal_bridge_1
  ]
}

// ---- Verification ----

check theta_completeness on ding.performative_state
  // ✓ governance_mode: 4/4 rows (exhaustive_typology)
  // ✓ performative_governance: 1 row (definitional, sparse θ valid)
  // ✓ substantive_governance: 1 row (definitional, sparse θ valid)
  // ✓ inert_governance: 1 row (definitional, sparse θ valid)
  // ✓ paternalistic_governance: 1 row (definitional, sparse θ valid)
  // ✓ undecomposed concepts: {"none": 1}

check rule_consistency on ding.performative_state
  // ✓ governance_mode: exhaustive_typology → 4 unique outcomes
  // ✓ performative_governance: definitional → 1 row = 1

check reference_integrity on ding.performative_state
  // ✓ all edge targets resolve to nodes

derive implications from ding.performative_state
  // → 3 causal implications derived

derive ibe_profile from ding.performative_state
  // → has_explanations: true (3 causal edges)
  // → has_facts: true (9 concepts, 2 attributes)
  // → has_bridge: weak (1 measurement bridge strong, 1 causal bridge weak)
  // → contribution_type: explanation_with_weak_evidence
```

---

## 4. 分层语义

| Layer | 原语 | 可判定性 | 数学基础 |
|---|---|---|---|
| 0 | attribute, concept, θ | Decidable | FCA |
| 1 | broader, narrower, contrastsWith, related | Decidable | Description Logic (subsumption) |
| 2 | causal, direction, condition, mechanism | Semi-decidable | SCM (DAG-based identification) |
| 3 | bridge, commensurability | Undecidable | 需人类判断 |

一个 model 可以只使用 Layer 0（纯描述），或 Layer 0-1（概念分类学），或 Layer 0-2（因果理论），或全部四层（完整的研究设计评估）。

---

## 5. 与 JSON Schema 的关系

外部语法 (.aiss) 是**人类可读的源文件**。JSON 是**机器可处理的编译输出**。

```
.aiss 文件 (human authoring)
    ↓ parser
  AST (typed, verifiable)
    ↓ compiler
  JSON (schema conforming, for graphify/toolchain)
```

Compiler：`aiss compile model.aiss → graph.json`（待实现）。

Parser：`aiss parse model.aiss → AST + check results`（待实现）。

---

## 6. 提取管道集成

```
paper.txt → [extraction protocol] → evidence table → [compiler] → .aiss file
                                                                      ↓
                                                                 [aiss parser]
                                                                      ↓
                                                                   JSON
                                                                      ↓
                                                                 [graphify]
```

提取协议（extraction-protocol.md）定义 agent 如何从论文填写证据表。编译器机械编译证据表 → .aiss。Parser 验证 .aiss → JSON。整个管道中，只有证据表填写依赖 LLM agent 的判断，其余步骤是确定性的。
