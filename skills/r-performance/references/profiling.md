# R 性能分析工具参考

本文档详细介绍 R 语言中常用的性能分析和基准测试工具。

## 目录

- [profvis - 可视化性能分析](#profvis---可视化性能分析)
  - [基本用法](#基本用法)
  - [关键参数详解](#关键参数详解)
  - [火焰图解读](#火焰图解读)
  - [内存分析](#内存分析)
  - [保存结果](#保存结果)
  - [pause() 函数](#pause-函数)
  - [Shiny 应用分析](#shiny-应用分析)
- [bench - 精确基准测试](#bench---精确基准测试)
  - [bench::mark() 基本用法](#benchmark-基本用法)
  - [输出结果解读](#输出结果解读)
  - [关键参数](#关键参数)
  - [bench::press() 参数网格测试](#benchpress-参数网格测试)
  - [可视化](#可视化)
  - [其他实用函数](#其他实用函数)
- [其他工具](#其他工具)
  - [system.time()](#systemtime)
  - [Rprof()](#rprof)
  - [microbenchmark](#microbenchmark)

---

## profvis - 可视化性能分析

`profvis` 是 R 中最强大的可视化性能分析工具，它将 R 的采样分析器输出转换为交互式火焰图。

### 基本用法

```r
library(profvis)

# 最简单的用法：包裹需要分析的代码
profvis({
  # 你的代码
  dat <- data.frame(
    x = rnorm(1e5),
    y = rnorm(1e5)
  )

  # 一些计算
  result <- lm(y ~ x, data = dat)
  summary(result)
})
```

分析已有函数：

```r
# 定义函数
slow_function <- function(n) {
  result <- numeric(n)
  for (i in 1:n) {
    result[i] <- sum(rnorm(1000))
  }
  result
}

# 分析该函数
profvis({
  slow_function(100)
})
```

### 关键参数详解

```r
profvis(
  expr = NULL,             # 要分析的表达式
  interval = 0.01,         # 采样间隔（秒），默认 10ms
  prof_output = NULL,      # 保存原始分析数据的路径
  prof_input = NULL,       # 读取已有的 Rprof 数据文件
  timing = NULL,           # 计时类型："elapsed"（墙钟）或 "cpu"
  split = c("h", "v"),     # 分割方向：水平或垂直
  torture = 0,             # 每 N 次内存分配后触发 GC
  simplify = TRUE,         # 是否简化调用栈
  rerun = FALSE            # 是否重新运行直到获得有效 profile
)
```

**参数说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `interval` | 0.01 | 采样间隔（秒）。小于 0.005 可能导致不准确。减小可获得更精确的结果，但会增加开销 |
| `timing` | NULL | 计时类型。`"elapsed"` 为墙钟时间（包含等待），`"cpu"` 为 CPU 时间。NULL 时在 Windows 或 R >= 4.4.0 使用 elapsed |
| `torture` | 0 | 每 N 次内存分配后触发垃圾回收。有助于更准确地追踪内存分配位置 |
| `simplify` | TRUE | 简化调用栈，移除惰性求值产生的中间帧。等同于 `Rprof()` 的 `filter.callframes` |
| `split` | "h" | 火焰图和代码视图的分割方向。"h" 水平，"v" 垂直 |
| `rerun` | FALSE | 若表达式执行太快没有采样到数据，设为 TRUE 会重复运行直到获得 profile |

**interval 参数的选择：**

```r
# 快速代码（< 1秒）：使用更小的间隔
profvis({
  fast_operation()
}, interval = 0.005)

# 长时间代码（> 10秒）：使用更大的间隔减少开销
profvis({
  long_running_analysis()
}, interval = 0.02)
```

### 火焰图解读

火焰图是理解代码性能的关键工具。

**核心概念：**

1. **顶部 = 实际瓶颈**：火焰图顶部的函数是实际执行计算的地方，是优化的目标
2. **宽度 = 时间占比**：条带越宽，表示该函数（及其调用的函数）占用的时间越长
3. **垂直方向 = 调用栈**：从下到上表示函数调用链

**示例解读：**

```r
profvis({
  # 假设这段代码产生如下火焰图结构：
  #
  # 顶层：   [  mean()  ][sum()][  apply()  ]
  #              ↑                    ↑
  # 中层：   [    sapply()    ][  outer()  ]
  #                    ↑
  # 底层：   [        main_function()         ]

  main_function <- function() {
    x <- matrix(rnorm(1e6), 1000, 1000)
    row_means <- sapply(1:1000, function(i) mean(x[i,]))
    col_sums <- apply(x, 2, sum)
    outer_prod <- outer(row_means, row_means)
  }
  main_function()
})
```

**解读要点：**

- 底部的 `main_function()` 横跨整个宽度，因为所有时间都在它内部消耗
- `sapply()` 和 `apply()` 的宽度表示它们各自占用的时间比例
- 顶部的 `mean()` 和 `sum()` 是实际进行计算的函数
- 如果 `mean()` 的宽度很大，说明计算均值是主要瓶颈

**Data 和 Flame Graph 选项卡：**

- **Flame Graph**：可视化调用栈
- **Data**：表格形式显示每个函数的时间和内存使用

### 内存分析

profvis 可以同时分析 CPU 时间和内存分配。

```r
# 内存密集型代码分析
profvis({
  # 逐步增长向量（内存效率低）
  bad_grow <- function(n) {
    x <- c()
    for (i in 1:n) {
      x <- c(x, i)  # 每次都重新分配内存
    }
    x
  }

  # 预分配向量（内存效率高）
  good_grow <- function(n) {
    x <- numeric(n)
    for (i in 1:n) {
      x[i] <- i
    }
    x
  }

  bad_grow(10000)
  good_grow(10000)
})
```

**内存列解读：**

- 正数：分配的内存
- 负数：垃圾回收释放的内存
- 大量正负交替：频繁的内存分配和回收，可能是性能问题

### 保存结果

```r
# 方法 1：保存为 HTML 文件
p <- profvis({
  # 你的代码
  result <- complex_analysis()
})

# 保存为独立 HTML 文件
htmlwidgets::saveWidget(p, "profile_result.html")

# 方法 2：保存原始数据以便后续分析
profvis({
  result <- complex_analysis()
}, prof_output = "profile_data.prof")

# 后续加载
profvis(prof_input = "profile_data.prof")
```

### pause() 函数

`pause()` 让等待时间在 profiler 中可见，与 `Sys.sleep()` 不同。

```r
# Sys.sleep() 在 profiler 中不会显示时间消耗
# pause() 会显示，适合标记代码段或模拟等待

pause(0.5)  # 暂停 0.5 秒，会出现在 profiler 输出中

# 注意：pause() 会占用 100% CPU，而 Sys.sleep() 不会
```

**使用场景：**

```r
profvis({
  # 使用 pause() 模拟 I/O 等待，让它在火焰图中可见
  pause(0.1)

  # 实际计算
  result <- complex_calculation()

  pause(0.1)  # 另一个标记点
})
```

### Shiny 应用分析

```r
library(shiny)
library(profvis)

# 方法 1：包裹整个应用
profvis({
  shiny::runApp("my_app", launch.browser = FALSE)
})

# 方法 2：使用内置的 Shiny 模块（适合生产环境调试）
# 在 UI 中添加：
ui <- fluidPage(
  profvis_ui("profiler"),
  # ... 其他 UI 元素
)

# 在 server 中添加：
server <- function(input, output, session) {
  callModule(profvis_server, "profiler", dir = ".")
  # ... 其他服务器逻辑
}
```

---

## bench - 精确基准测试

`bench` 包提供了现代化的 R 基准测试工具，具有自动迭代、内存测量和结果验证等功能。

### bench::mark() 基本用法

```r
library(bench)

# 比较多个表达式
results <- bench::mark(
  method_1 = sum(1:1000),
  method_2 = Reduce(`+`, 1:1000),
  method_3 = {
    total <- 0
    for (i in 1:1000) total <- total + i
    total
  }
)

print(results)
```

比较向量操作方法：

```r
x <- rnorm(1e5)

bench::mark(
  "base R" = mean(x),
  "manual" = sum(x) / length(x),
  "collapse" = collapse::fmean(x),
  check = TRUE  # 验证结果一致
)
```

### 输出结果解读

典型输出：

```
# A tibble: 3 × 13
  expression   min   median `itr/sec` mem_alloc `gc/sec` n_itr  n_gc total_time
  <bch:expr> <dbl>   <dbl>     <dbl> <bch:byt>    <dbl> <int> <dbl>   <bch:tm>
1 method_1   1.2µs   1.5µs   650000.        0B        0 10000     0      15.4ms
2 method_2   450µs   480µs     2050.      784B      2.1   978     1       477ms
3 method_3   220µs   235µs     4200.      448B        0  2000     0       470ms
```

**关键列解读：**

| 列名 | 含义 | 重要性 |
|------|------|--------|
| `expression` | 表达式名称 | 标识被测代码 |
| `min` | 最短执行时间 | 代表最佳情况，不受 GC 影响 |
| `median` | 中位执行时间 | **最重要的指标**，代表典型性能 |
| `itr/sec` | 每秒迭代次数 | 便于比较相对速度 |
| `mem_alloc` | 内存分配量 | 显示内存效率（仅 R 堆内存，不含 malloc/new） |
| `gc/sec` | 每秒 GC 次数 | 高值表示内存压力大 |
| `n_itr` | 总迭代次数 | 过滤 GC 后的迭代数（若 filter_gc=TRUE） |
| `n_gc` | GC 总次数 | 所有迭代的 GC 次数总和 |
| `total_time` | 总运行时间 | 完成所有迭代的时间 |

**隐藏的列表列（默认不显示）：**

| 列名 | 含义 |
|------|------|
| `result` | 每个表达式的返回值 |
| `memory` | 详细内存分配（来自 Rprofmem） |
| `time` | 每次迭代的时间向量 |
| `gc` | 每次迭代的 GC 级别（0-2） |

**时间单位说明：**

- `ns`：纳秒（10⁻⁹ 秒）
- `µs`：微秒（10⁻⁶ 秒）
- `ms`：毫秒（10⁻³ 秒）
- `s`：秒

### 关键参数

```r
bench::mark(
  expr1 = method_1(),
  expr2 = method_2(),

  # 时间和迭代控制
  min_time = 0.5,           # 最少运行时间（秒），默认 0.5。设为 Inf 则只用 max_iterations
  iterations = NULL,        # 固定迭代次数（设置后忽略 min/max_iterations）
  min_iterations = 1,       # 最少迭代次数，默认 1
  max_iterations = 10000,   # 最大迭代次数，默认 10000

  # 结果验证
  check = TRUE,             # TRUE: 用 all.equal() 验证；FALSE: 不验证；或自定义函数

  # 内存分析
  memory = capabilities("profmem"),  # 是否测量内存（需要 R 支持 profmem）

  # GC 控制
  filter_gc = TRUE,         # 排除包含 GC 的迭代（若所有迭代都有 GC 则禁用并警告）

  # 输出格式
  relative = FALSE,         # TRUE: 输出相对于最快方法的比率
  time_unit = NULL,         # 时间单位：NULL（自动）或 'ns','us','ms','s','m','h','d','w'

  # 高级选项
  exprs = NULL,             # 表达式列表，覆盖 ... 中的表达式
  env = parent.frame()      # 评估表达式的环境
)
```

**参数使用场景：**

```r
# 快速粗略比较
bench::mark(expr1, expr2, min_time = 0.1)

# 精确测量（固定迭代）
bench::mark(expr1, expr2, iterations = 1000)

# 查看相对性能
bench::mark(expr1, expr2, expr3, relative = TRUE)

# 包含 GC 的真实性能
bench::mark(expr1, expr2, filter_gc = FALSE)

# 验证结果一致性
bench::mark(
  new_implementation(x),
  old_implementation(x),
  check = TRUE  # 如果结果不同会报错
)
```

### bench::press() 参数网格测试

`press()` 用于在参数组合上进行基准测试。

```r
bench::press(
  ...,           # 命名参数定义网格，未命名参数是要运行的表达式
  .grid = NULL,  # 预定义的参数网格（data.frame 或 tibble）
  .quiet = FALSE # TRUE 则不显示进度消息
)
```

**基本用法：**

```r
# 测试不同数据大小和方法的组合
results <- bench::press(
  n = c(100, 1000, 10000),
  method = c("mean", "median"),
  {
    x <- rnorm(n)

    bench::mark(
      result = if (method == "mean") mean(x) else median(x)
    )
  }
)

print(results)
```

**使用预定义网格：**

```r
# 只测试特定组合（而非全部笛卡尔积）
my_grid <- tibble::tibble(
  rows = c(1000, 10000, 100000),
  cols = c(10, 100, 1000)
)

bench::press(.grid = my_grid, {
  dat <- matrix(rnorm(rows * cols), rows, cols)
  bench::mark(colMeans(dat))
})
```

**添加重复实验：**

```r
# 使用虚拟变量 rep 进行重复
bench::press(
  n = c(1000, 10000),
  rep = 1:5,  # 每个 n 重复 5 次
  {
    x <- rnorm(n)
    bench::mark(mean(x))
  }
)
```

更复杂的示例：

```r
# 比较不同包在不同数据大小下的性能
results <- bench::press(
  rows = 10^(3:6),
  cols = c(10, 100),
  {
    dat <- data.frame(
      matrix(rnorm(rows * cols), rows, cols)
    )

    bench::mark(
      base = colMeans(dat),
      dplyr = dplyr::summarise_all(dat, mean),
      data.table = data.table::as.data.table(dat)[, lapply(.SD, mean)],
      check = FALSE,  # 不同包返回格式不同
      min_iterations = 5
    )
  }
)

# 可视化参数影响
library(ggplot2)
autoplot(results)
```

### 可视化

```r
library(ggplot2)

results <- bench::mark(
  method_a = sort(runif(1000)),
  method_b = sort(runif(1000), method = "radix"),
  method_c = sort(runif(1000), method = "quick")
)

# 自动生成可视化
autoplot(results)

# 自定义可视化
autoplot(results, type = "ridge")    # 密度脊线图
autoplot(results, type = "boxplot")  # 箱线图
autoplot(results, type = "violin")   # 小提琴图
autoplot(results, type = "jitter")   # 散点图（默认）
```

### 其他实用函数

**bench::bench_time()** - 简单计时

```r
# 单次执行计时
bench::bench_time({
  result <- complex_analysis()
})

# 返回 process 时间和 real 时间
#> process    real
#>   2.34s   2.41s
```

**bench::bench_memory()** - 内存测量

```r
# 测量单次执行的内存分配
bench::bench_memory({
  big_matrix <- matrix(rnorm(1e6), 1000, 1000)
  result <- svd(big_matrix)
})
```

**bench::workout()** - 逐行分析

```r
# 分析代码块的每一行
results <- bench::workout({
  x <- rnorm(1e5)
  y <- x^2
  z <- cumsum(y)
  mean(z)
})

print(results)
# 显示每行的执行时间和内存分配
```

**bench::workout_expressions()** - 表达式列表分析

```r
# 分析表达式列表
exprs <- list(
  quote(x <- rnorm(1e5)),
  quote(y <- x^2),
  quote(z <- cumsum(y)),
  quote(mean(z))
)

bench::workout_expressions(exprs, env = parent.frame(), description = NULL)

# 从文件读取表达式
bench::workout_expressions(
  as.list(parse(system.file("examples/exprs.R", package = "bench")))
)
```

**bench::bench_process_memory()** - 进程内存

```r
# 获取 R 进程的当前和峰值内存使用
bench::bench_process_memory()
#>   current      max
#>    256 MB   512 MB

# 注意：这包括所有内存（含子进程和 R 堆外分配），与 gc() 报告的不同
```

**bench::bench_load_average()** - 系统负载

```r
# 获取系统 1/5/15 分钟平均负载
bench::bench_load_average()
#>    1min   5min  15min
#>    2.34   1.89   1.45
```

**bench::hires_time()** - 高精度时间戳

```r
# 获取高精度时间戳（用于自定义计时）
start <- bench::hires_time()
# ... 代码 ...
end <- bench::hires_time()
elapsed <- end - start
```

**bench::as_bench_time() / bench::bench_bytes()** - 类型转换

```r
# 人类可读的时间
bench::as_bench_time("1ms")
bench::as_bench_time("100ns") < "1ms"  # TRUE

# 人类可读的内存大小
bench::bench_bytes("1MB")
bench::bench_bytes("1KB") < "1MB"  # TRUE
sum(bench::bench_bytes(c("1MB", "5MB", "500KB")))  # 6.5 MB
```

---

## 其他工具

### system.time()

R 内置的简单计时函数。

```r
# 基本用法
system.time({
  result <- slow_function()
})

#>    user  system elapsed
#>   2.340   0.120   2.480

# 理解输出
# user:    用户 CPU 时间（代码执行）
# system:  系统 CPU 时间（系统调用）
# elapsed: 挂钟时间（实际等待时间）
```

**注意事项：**

- `elapsed > user + system`：等待 I/O 或其他进程
- `user + system > elapsed`：使用了多核（并行计算）

```r
# 测量多次取平均
times <- replicate(10, {
  system.time(slow_function())["elapsed"]
})
mean(times)
```

### Rprof()

R 内置的采样分析器，是 profvis 的底层。

```r
# 开始分析
Rprof("profile.out", interval = 0.01, memory.profiling = TRUE)

# 运行代码
result <- complex_analysis()

# 停止分析
Rprof(NULL)

# 查看结果
summaryRprof("profile.out")

# 详细的内存分析
summaryRprof("profile.out", memory = "both")
```

**输出解读：**

```r
# $by.self - 按函数自身时间排序
#            self.time self.pct total.time total.pct
# "function_a"    5.20    52.0       8.30      83.0
# "function_b"    2.10    21.0       2.10      21.0

# $by.total - 按函数总时间排序（包括调用的函数）
```

**何时使用 Rprof() 而非 profvis：**

- 需要在脚本中程序化分析
- 无法使用图形界面
- 需要更细粒度的控制

### microbenchmark

另一个流行的基准测试包，功能与 bench 类似。

```r
library(microbenchmark)

# 基本用法
results <- microbenchmark(
  method_1 = sum(1:1000),
  method_2 = Reduce(`+`, 1:1000),
  times = 100  # 迭代次数
)

print(results)
# Unit: nanoseconds
#      expr   min    lq  mean median    uq   max neval
#  method_1  1200  1350  1520   1450  1600  2800   100
#  method_2 45000 47000 52000  48000 51000 85000   100

# 可视化
autoplot(results)
```

**bench vs microbenchmark：**

| 特性 | bench | microbenchmark |
|------|-------|----------------|
| 自动迭代次数 | 是 | 否 |
| 内存测量 | 是 | 否 |
| 结果验证 | 是 | 否 |
| GC 过滤 | 是 | 否 |
| 参数网格 | `press()` | 需手动 |
| 依赖 | 较少 | 较少 |

**推荐使用 bench**，因为它更现代且功能更全面。

---

## 最佳实践总结

1. **开发阶段**：使用 `profvis` 进行可视化分析，找出瓶颈
2. **优化验证**：使用 `bench::mark()` 精确比较优化前后的性能
3. **参数调优**：使用 `bench::press()` 测试不同参数组合
4. **快速检查**：使用 `system.time()` 或 `bench::bench_time()` 进行简单计时
5. **代码审查**：使用 `bench::workout()` 分析每行代码的开销

记住：**先测量，再优化**。不要凭直觉优化，让数据说话。
