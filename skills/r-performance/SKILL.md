---
name: r-performance
description: |
  R 代码性能诊断与优化指南。帮助识别性能瓶颈、理解 R 底层机制、选择优化策略。

  **触发场景：**
  - "这段代码跑得太慢了"
  - "帮我优化这个函数/循环的性能"
  - "如何加速这个包的某个函数"
  - "为什么这段 R 代码这么慢"
  - "如何在 HPC 上并行运行"
  - 用户询问 profvis、bench、future、并行计算相关问题
---

# R 代码性能优化

## 核心工作流

```
1. 定位瓶颈 → 2. 诊断原因 → 3. 选择策略 → 4. 实施优化
   (profvis)    (理解机制)    (决策树)      (代码修改)
```

## Full-Auto Harness Contract

在自动 harness 中，本 skill 不得暂停等待人工选择，也不得返回无进展的终止状态。必须自动定位瓶颈、选择不会改变结果的优化、
修改代码、重跑验证，并保留 before/after 证据。若服务 research-factory，优化目标是让
`make all` 更快且结果不变，最终支撑发表级 `paper/full_draft.pdf`。

## .aiss State Machine

当从 AI4SS research-factory workspace 调用时，先定位
`.ai4ss/research_model.aiss` 并运行
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss`，再决定或返回
`next_skill_route`。启动、完成、失败和 watchdog heartbeat 观察应记录为
`.aiss` `event` declaration，或返回可合并的
`aiss.py transition --event ...` deterministic fragment。event 不能替代语义更新：
性能优化、等价性检查和 rerun 证据仍要落到相应 `check`、`decision`、
`artifact` 或日志声明。

## 正确性硬门槛

- 先确认目标脚本可以从干净会话运行：优先用 `Rscript --vanilla <script.R>`，不要依赖交互式环境里残留的对象。
- 优化不能改变结果。优化前后必须比较关键输出：行数、列名、样本量、估计系数、图表文件清单，必要时比较文件 hash 或数值容差。
- 任何非零退出都先按 bug 处理；不要在失败脚本上做性能报告，也不要用旧输出证明优化成功。
- 图表或表格优化必须落回生成代码，不能只手工改输出文件。

## 第一步：定位瓶颈

**永远先 profile，不要猜测！**

```r
# 方法1：profvis 可视化（推荐）
library(profvis)
profvis({
  # 你的代码
  result <- slow_function(data)
})

# 方法2：bench 精确测量
library(bench)
bench::mark(
  method_a = function_a(x),
  method_b = function_b(x),
  check = FALSE  # 如果结果不完全相同
)
```

**profvis 输出解读：**
- 火焰图顶部 = 实际执行的函数（瓶颈所在）
- 宽度 = 时间占比
- 内存列 = 内存分配情况

详细用法见 [references/profiling.md](references/profiling.md)

## 第二步：诊断原因

找到瓶颈后，判断属于哪类问题：

| 症状 | 可能原因 | 解决方向 |
|------|----------|----------|
| 循环内大量内存分配 | Growing objects | 预分配 + 向量化 |
| 简单操作却很慢 | Copy-on-modify | 避免不必要的复制 |
| CPU 单核 100% | 单线程瓶颈 | 并行化 |
| 大量重复计算 | 缺少缓存 | Memoization |
| 外部 I/O 等待 | I/O 瓶颈 | 异步/批量处理 |

R 底层机制详解见 [references/r-internals.md](references/r-internals.md)

## 第三步：优化决策树

```
代码慢？
│
├─ 是否可向量化？
│  ├─ 是 → 用向量化操作替代循环
│  └─ 否 → 继续判断
│
├─ 迭代之间是否独立？
│  ├─ 是 → 并行化（future 生态）
│  │       ├─ 本地多核 → plan(multisession)
│  │       └─ HPC 集群 → plan(batchtools_slurm)
│  └─ 否 → 继续判断
│
├─ 是否有大量内存分配？
│  ├─ 是 → 预分配 + 避免 copy-on-modify
│  └─ 否 → 继续判断
│
└─ 是否是计算密集型？
   ├─ 是 → 考虑算法优化或使用已优化的包
   └─ 否 → 检查 I/O 和外部调用
```

## 快速优化模式

### 模式 1：向量化替代循环

```r
# 慢 ❌
result <- c()
for (i in 1:n) {
  result <- c(result, x[i] * 2)  # 每次都复制整个向量！
}

# 快 ✓
result <- x * 2  # 向量化操作
```

### 模式 2：预分配内存

```r
# 慢 ❌
result <- c()
for (i in 1:n) {
  result <- c(result, compute(i))
}

# 快 ✓
result <- vector("list", n)  # 预分配
for (i in 1:n) {
  result[[i]] <- compute(i)
}
# 或使用 lapply
result <- lapply(1:n, compute)
```

### 模式 3：避免 Copy-on-Modify

```r
# 慢 ❌ - 每次修改都会复制
for (i in 1:n) {
  df$new_col[i] <- compute(df$x[i])
}

# 快 ✓ - 向量化赋值
df$new_col <- sapply(df$x, compute)
# 或
df$new_col <- purrr::map_dbl(df$x, compute)
```

### 模式 4：本地并行化

```r
library(future)
library(future.apply)

# 设置并行后端
plan(multisession, workers = parallelly::availableCores() - 1)

# 并行 lapply
result <- future_lapply(1:n, function(i) {
  slow_computation(i)
})

# 完成后恢复顺序执行
plan(sequential)
```

### 模式 5：与包函数集成（如 futuremice）

```r
library(future)
library(mice)

# 设置并行后端
plan(multisession, workers = 4)

# futuremice 自动利用 future 后端
imp <- futuremice(data, m = 20, parallelseed = 123)

plan(sequential)
```

## 第五步：生成性能对比报告

完成优化后，**总是**生成一个 HTML 性能对比报告，方便研究者审查改动并向合作者展示效果。

```bash
python3 <skill-dir>/scripts/perf_html.py before.R after.R [perf-summary.json] [output.html]
```

输入：
- `before.R` — 优化前的 R 代码（可以是单个函数、一段 pipeline、或完整脚本）
- `after.R` — 优化后的 R 代码
- `perf-summary.json` *(可选)* — 性能指标摘要：

```json
{
  "runtime_before": "4.2s",
  "runtime_after":  "0.34s",
  "speedup":        "12.4",
  "memory_before":  "812 MB",
  "memory_after":   "94 MB",
  "mem_reduction":  "88",
  "note":           "Vectorized inner loop; eliminated redundant join"
}
```

输出 `perf-report.html`（默认）— 单文件 HTML，无外部依赖：
- 顶部 speedup 横幅（X 倍加速）
- 运行时 / 内存对比指标卡
- before/after 代码 diff
- 优化说明（来自 `note` 字段）

何时生成报告：
- ✅ 完成具体的优化任务（用户问 "帮我优化这段代码"）后
- ✅ profvis 显示明确的 before/after 测量结果时
- ❌ 仅讨论性能而未实际优化代码时跳过

研究者通常想把这个 HTML 直接发给合作者，**不要让用户自己去找脚本路径** —
默认就跑，输出路径告诉用户。

## 参考文档

根据需要查阅：

- **[profiling.md](references/profiling.md)** - profvis 和 bench 详细用法
- **[r-internals.md](references/r-internals.md)** - R 底层机制（copy-on-modify、向量化原理、内存管理）
- **[future-ecosystem.md](references/future-ecosystem.md)** - future 并行生态系统（本地 + HPC 基础）
- **[hpc-configuration.md](references/hpc-configuration.md)** - **HPC 集群详细配置**（Slurm/SGE/PBS 模板、crew.cluster、troubleshooting）
- **[common-patterns.md](references/common-patterns.md)** - 更多优化模式和陷阱
