# future 并行生态系统完整指南

> 基于 Henrik Bengtsson 的 future 包论文 (R Journal, 2021) 及官方 vignettes

## 目录

1. [核心概念](#1-核心概念)
   - [什么是 Future](#11-什么是-future)
   - [三个核心函数](#12-三个核心函数)
   - [plan() 后端切换](#13-plan-后端切换)
2. [本地并行](#2-本地并行)
   - [multisession 后端](#21-multisession-后端推荐)
   - [multicore 后端](#22-multicore-后端仅-unixmac)
   - [multicore vs multisession 对比](#23-multicore-vs-multisession-对比)
   - [显式与隐式 Futures](#24-显式与隐式-futures)
   - [使用 listenv 处理多个并行任务](#25-使用-listenv-处理多个并行任务)
3. [HPC 集群并行](#3-hpc-集群并行)
   - [future.batchtools 后端](#31-futurebatchtools-后端)
   - [Slurm 配置示例](#32-slurm-配置示例)
   - [模板文件示例](#33-模板文件示例)
   - [crew 作为现代替代方案](#34-crew-作为现代替代方案)
   - [嵌套并行](#35-嵌套并行两级-plan)
4. [高级 API](#4-高级-api)
   - [future.apply 包](#41-futureapply-包)
   - [furrr 包](#42-furrr-包)
   - [并行随机数生成](#43-并行随机数生成)
5. [常见问题与解决方案](#5-常见问题与解决方案)
   - [全局变量未导出](#51-全局变量未导出)
   - [包未在 worker 中加载](#52-包未在-worker-中加载)
   - [不可导出对象](#53-不可导出对象external-pointers)
   - [内存问题](#54-内存问题)
6. [与其他包集成](#6-与其他包集成)
   - [mice 包集成](#61-mice-包futuremice)
   - [targets 工作流](#62-targets-工作流)
   - [foreach 适配器](#63-foreach-适配器dofuture)
   - [恢复顺序执行](#64-恢复顺序执行)

---

## 1. 核心概念

### 1.1 什么是 Future

**Future** 是一个用于表示"未来某时刻可用的值"的编程抽象。当我们创建一个 future 时，R 表达式被封装起来，可以在当前进程或其他进程中异步求值。

```r
# 普通赋值
v <- expr

# 使用 future 的等价形式
f <- future(expr)
v <- value(f)
```

Future 的核心设计理念：

1. **开发者专注于"并行什么"** - 编写 future 代码
2. **用户决定"如何并行"** - 通过 `plan()` 选择后端
3. **代码与后端分离** - 同样的代码可以在不同后端运行

### 1.2 三个核心函数

```r
library(future)

# 1. future() - 创建一个 future（非阻塞，如果可能）
f <- future({
  slow_fcn(x)
})

# 2. value() - 获取 future 的值（阻塞直到完成）
v <- value(f)

# 3. resolved() - 检查 future 是否已完成（非阻塞）
if (resolved(f)) {
  v <- value(f)
}
```

**关键特性：**

- `future()` 会捕获表达式中使用的所有全局变量
- 变量在创建 future 时被"冻结"，之后的修改不影响 future
- `value()` 会转发 future 中产生的错误、警告和输出（中继机制）

**输出和条件中继（Relay）机制：**

future 捕获并中继以下内容：

1. **标准输出（stdout）**：`cat()`、`print()` 输出
2. **条件（conditions）**：`message()`、`warning()` 信号
3. **错误**：在调用 `value()` 时重新抛出

```r
f <- future({
  cat("Hello world\n")
  message("This is a message")
  warning("This is a warning", call. = FALSE)
  42
})

v <- value(f)
# Hello world
# This is a message
# Warning message:
# This is a warning
```

中继顺序：先输出所有 stdout，再按原顺序中继 conditions。

**immediateCondition 类型：**

标记为 `immediateCondition` 的条件可以尽快中继（不必等到 `value()` 调用）：
- 适用于进度更新
- `progressr` 包使用此机制实现跨 worker 的进度条
- 中继时机取决于后端支持

**注意：** 标准错误（stderr）无法可靠捕获（R 的限制），`message()` 的输出通过条件机制捕获，而非 stderr。

```r
x <- 1
f <- future({ slow_fcn(x) })
x <- 2  # 不影响 future，因为 x=1 已被捕获
v <- value(f)  # 使用 x=1 计算
```

### 1.3 plan() 后端切换

`plan()` 函数用于设置 future 的求值策略：

```r
# 顺序执行（默认）
plan(sequential)

# 本地多会话并行
plan(multisession)
plan(multisession, workers = 4)

# 本地多核并行（仅 Unix/Mac）
plan(multicore)

# 远程集群
plan(cluster, workers = c("n1", "n2", "n3"))

# HPC 作业调度器
plan(future.batchtools::batchtools_slurm)
```

---

## 2. 本地并行

### 2.1 multisession 后端（推荐）

`multisession` 通过在后台启动独立的 R 会话来实现并行，适用于**所有平台**（包括 Windows）。

```r
library(future)
plan(multisession, workers = 4)

# 创建多个 futures
xs <- 1:10
fs <- lapply(xs, function(x) {
  future({ slow_fcn(x) })
})

# 收集结果
vs <- lapply(fs, value)
```

**工作原理：**
- 启动指定数量的后台 R 会话（PSOCK 集群）
- 通过 socket 连接传输数据
- 全局变量自动导出到 workers
- 包自动在 workers 中加载

**workers 数量：**

```r
# 默认使用 availableCores() 返回的核心数
plan(multisession)

# 手动指定
plan(multisession, workers = 4)

# availableCores() 会自动识别：
# - mc.cores 选项
# - 环境变量 (SLURM_CPUS_PER_TASK 等)
# - 系统可用核心数
availableCores()
```

### 2.2 multicore 后端（仅 Unix/Mac）

`multicore` 通过进程 fork 实现并行，利用写时复制（copy-on-write）共享内存。

```r
# 仅在 Unix/Mac 上有效
plan(multicore)
plan(multicore, workers = 4)
```

**优势：**
- 启动更快（无需复制数据到 workers）
- 内存效率更高（共享只读内存）
- 全局变量自动继承

**限制：**
- Windows 不支持
- 在 RStudio 中默认禁用（可能导致崩溃）
- fork 后的共享内存是只读的

### 2.3 multicore vs multisession 对比

| 特性 | multicore | multisession |
|------|-----------|--------------|
| **平台支持** | Unix/Mac only | 所有平台 |
| **实现方式** | 进程 fork | 独立 R 会话 |
| **内存模型** | 写时复制共享 | 完全独立 |
| **启动速度** | 快 | 较慢 |
| **大对象处理** | 高效（共享） | 需要导出 |
| **RStudio 兼容** | 不推荐 | 完全兼容 |
| **稳定性** | 可能不稳定 | 稳定 |
| **推荐使用** | 脚本中的 Unix/Mac | 通用场景 |

**选择建议：**

```r
# 通用推荐（适用于所有场景）
plan(multisession)

# 仅当你在 Unix/Mac 终端中运行，且需要处理大对象时
if (.Platform$OS.type == "unix" &&
    !interactive() &&  # 非交互模式
    Sys.getenv("RSTUDIO") == "") {  # 不在 RStudio 中
  plan(multicore)
}
```

### 2.4 显式与隐式 Futures

**显式 futures（推荐用于复杂场景）：**

```r
# 显式创建和获取值
f <- future({ expr })
v <- value(f)

# 可以存储在任何地方
fs <- list()
for (i in 1:10) {
  fs[[i]] <- future({ slow_fcn(i) })
}
vs <- lapply(fs, value)
```

**隐式 futures（语法更简洁）：**

```r
# 使用 %<-% 操作符
v %<-% { expr }

# 注意：隐式 futures 只能赋值给环境，不能赋值给列表
# 错误示例：
# vs[[i]] %<-% { expr }  # 不工作！

# 正确方法：使用 listenv
library(listenv)
vs <- listenv()
for (i in 1:10) {
  vs[[i]] %<-% { slow_fcn(i) }
}
vs <- as.list(vs)
```

### 2.5 使用 listenv 处理多个并行任务

`listenv` 包提供了类似列表的环境，支持隐式 futures。

**为什么需要 listenv：**

隐式 future 赋值 `%<-%` 使用 R 的 promise 机制，而 promise 只能赋值给环境（不能赋值给列表元素）。`listenv` 创建的"列表环境"在技术上是环境，但支持列表风格的索引操作。

```r
library(future)
library(listenv)
plan(multisession)

# 创建 list environment
results <- listenv()

# 使用数字索引
for (i in 1:10) {
  results[[i]] %<-% {
    Sys.sleep(1)
    i^2
  }
}

# 转换为普通列表（会阻塞直到所有 futures 完成）
results <- as.list(results)
print(results)
```

**与显式 futures 的对比：**

```r
# 显式 futures（推荐用于包开发）
fs <- list()
for (i in 1:10) {
  fs[[i]] <- future({ slow_fcn(i) })
}
vs <- lapply(fs, value)

# 隐式 futures + listenv（更简洁的语法）
library(listenv)
vs <- listenv()
for (i in 1:10) {
  vs[[i]] %<-% slow_fcn(i)
}
vs <- as.list(vs)
```

---

## 3. HPC 集群并行

### 3.1 future.batchtools 后端

`future.batchtools` 包支持多种 HPC 作业调度器：

```r
library(future.batchtools)

# Slurm
plan(batchtools_slurm)

# SGE (Sun Grid Engine)
plan(batchtools_sge)

# TORQUE/PBS
plan(batchtools_torque)

# LSF (Load Sharing Facility)
plan(batchtools_lsf)

# OpenLava
plan(batchtools_openlava)
```

**特点：**
- 每个 future 作为独立作业提交到调度器
- 适合长时间运行的任务
- 高延迟（作业调度开销）
- 支持资源配置（内存、时间限制等）

### 3.2 Slurm 配置示例

```r
library(future)
library(future.batchtools)

# 基础配置
plan(batchtools_slurm)

# 带资源限制的配置
plan(batchtools_slurm,
     resources = list(
       ncpus = 4,           # 每个作业的 CPU 核心数
       memory = "8G",       # 内存限制
       walltime = "02:00:00" # 运行时间限制
     ))

# 创建 futures（每个作为 Slurm 作业提交）
fs <- lapply(1:10, function(i) {
  future({
    # 在集群节点上运行的代码
    result <- expensive_computation(i)
    result
  })
})

# 等待所有作业完成
results <- lapply(fs, value)
```

### 3.3 模板文件示例

创建 `~/.batchtools.slurm.tmpl`：

```bash
#!/bin/bash

## Job name
#SBATCH --job-name=<%= job.name %>

## Output files
#SBATCH --output=<%= log.file %>
#SBATCH --error=<%= log.file %>

## Resources
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=<%= resources$ncpus %>
#SBATCH --mem=<%= resources$memory %>
#SBATCH --time=<%= resources$walltime %>

## Partition/queue
<% if (!is.null(resources$partition)) { -%>
#SBATCH --partition=<%= resources$partition %>
<% } -%>

## Load R module (根据你的集群配置修改)
module load R/4.2.0

## Run R script
Rscript -e 'batchtools::doJobCollection("<%= uri %>")'
```

**在 R 中使用：**

```r
library(future.batchtools)

# 使用默认模板
plan(batchtools_slurm,
     resources = list(
       ncpus = 4,
       memory = "16G",
       walltime = "04:00:00",
       partition = "normal"
     ))

# 或指定自定义模板
plan(batchtools_slurm,
     template = "~/.batchtools.slurm.tmpl",
     resources = list(...))
```

### 3.4 crew 作为现代替代方案

`crew` 是一个现代的任务调度框架，可作为 `future.batchtools` 的替代方案：

```r
library(crew)
library(crew.cluster)  # 用于 HPC 集群

# 创建 Slurm 控制器
controller <- crew_controller_slurm(
  name = "my_slurm_controller",
  workers = 10,
  seconds_idle = 300,  # worker 空闲 5 分钟后自动关闭
  slurm_memory_gigabytes_per_cpu = 4,
  slurm_cpus_per_task = 2,
  slurm_time_minutes = 60
)

# 启动控制器
controller$start()

# 推送任务
controller$push(
  command = expensive_computation(x),
  data = list(x = 1)
)

# 收集结果
result <- controller$pop()

# 关闭控制器
controller$terminate()
```

**与 targets 集成：**

```r
# _targets.R
library(targets)
library(crew.cluster)

tar_option_set(
  controller = crew_controller_slurm(
    workers = 20,
    slurm_memory_gigabytes_per_cpu = 8
  )
)
```

### 3.5 嵌套并行（两级 plan）

对于需要两级并行的场景（如：节点间 + 节点内），可以使用嵌套 plan：

```r
library(future)

# 两级并行：集群节点 -> 每个节点的多核
plan(list(
  tweak(cluster, workers = c("n1", "n2", "n3")),  # 第一层：3个节点
  multisession  # 第二层：每个节点上的多会话
))
```

**HPC 常见配置：**

```r
# 作业提交到 Slurm，每个作业内部多核并行
plan(list(
  future.batchtools::batchtools_slurm,
  multisession  # 使用 SLURM_CPUS_PER_TASK 指定的核心数
))
```

**手动控制每层的 workers 数量：**

```r
# 明确指定每层的 workers
plan(list(
  tweak(multisession, workers = 2),      # 第一层：2 个进程
  tweak(multisession, workers = I(4))    # 第二层：每个进程中 4 个子进程
))
# 注意：第二层使用 I() 来覆盖默认保护机制
```

**嵌套并行保护：**

```r
# 默认情况下，嵌套的 multisession 会降级为 sequential
plan(list(multisession, multisession))
# 等价于：
plan(list(multisession, sequential))

# 这是为了防止意外创建过多进程（N^2 问题）
```

---

## 4. 高级 API

### 4.1 future.apply 包

`future.apply` 提供了 `base::apply` 家族函数的并行版本：

```r
library(future)
library(future.apply)
plan(multisession)

# future_lapply - lapply 的并行版本
results <- future_lapply(1:10, function(x) {
  Sys.sleep(1)
  x^2
})

# future_sapply - sapply 的并行版本
results <- future_sapply(1:10, function(x) x^2)

# future_vapply - vapply 的并行版本（推荐，类型安全）
results <- future_vapply(1:10, function(x) x^2,
                         FUN.VALUE = numeric(1))

# future_mapply - mapply 的并行版本
results <- future_mapply(function(x, y) x + y,
                         x = 1:5, y = 6:10)

# future_apply - apply 的并行版本
mat <- matrix(1:20, nrow = 5)
row_sums <- future_apply(mat, MARGIN = 1, FUN = sum)
```

**所有函数：**

| 函数 | 对应 base 函数 | 说明 |
|------|---------------|------|
| `future_lapply` | `lapply` | 对列表/向量应用函数 |
| `future_sapply` | `sapply` | 简化版 lapply |
| `future_vapply` | `vapply` | 类型安全的 sapply |
| `future_mapply` | `mapply` | 多参数版本 |
| `future_Map` | `Map` | mapply 的简化版 |
| `future_apply` | `apply` | 对数组边际应用函数 |
| `future_tapply` | `tapply` | 分组应用函数 |
| `future_by` | `by` | 按因子分组应用 |
| `future_replicate` | `replicate` | 重复执行表达式 |

### 4.2 furrr 包

`furrr` 是 `purrr::map` 家族函数的 future 并行版本：

```r
library(future)
library(furrr)
plan(multisession)

# future_map - map 的并行版本
results <- future_map(1:10, function(x) {
  Sys.sleep(1)
  x^2
})

# future_map_dbl - 返回数值向量
results <- future_map_dbl(1:10, ~ .x^2)

# future_map2 - 双参数版本
results <- future_map2(1:5, 6:10, ~ .x + .y)

# future_pmap - 多参数版本
params <- list(
  a = 1:3,
  b = 4:6,
  c = 7:9
)
results <- future_pmap(params, function(a, b, c) a + b + c)

# 带进度条（需要 progressr 包）
library(progressr)
with_progress({
  p <- progressor(steps = 10)
  results <- future_map(1:10, function(x) {
    p()
    Sys.sleep(1)
    x^2
  })
})
```

**furrr 函数家族：**

| furrr 函数 | purrr 对应 | 返回类型 |
|-----------|-----------|---------|
| `future_map` | `map` | list |
| `future_map_chr` | `map_chr` | character |
| `future_map_dbl` | `map_dbl` | double |
| `future_map_int` | `map_int` | integer |
| `future_map_lgl` | `map_lgl` | logical |
| `future_map_dfr` | `map_dfr` | data.frame (row-bind) |
| `future_map_dfc` | `map_dfc` | data.frame (col-bind) |
| `future_map2` | `map2` | list (2 inputs) |
| `future_pmap` | `pmap` | list (n inputs) |
| `future_walk` | `walk` | invisible (side effects) |
| `future_imap` | `imap` | list (with index) |

### 4.3 并行随机数生成

并行计算中的随机数生成需要特殊处理，以确保结果可重复且统计有效：

```r
library(future)
library(future.apply)
plan(multisession)

# 方法 1：使用 future.seed = TRUE（推荐）
results <- future_lapply(1:5, function(i) {
  rnorm(3)
}, future.seed = TRUE)

# 方法 2：显式设置种子
results <- future_lapply(1:5, function(i) {
  rnorm(3)
}, future.seed = 123)  # 可重复

# 显式 future 中使用 seed
set.seed(123)
f <- future({ rnorm(3) }, seed = TRUE)
v <- value(f)
```

**重要说明：**

1. `future.seed = TRUE` 使用 **L'Ecuyer-CMRG** 并行随机数生成器
   - 默认的 Mersenne-Twister RNG 不适合并行（可能产生相关随机数）
   - L'Ecuyer-CMRG 由 `parallel` 包实现，专为并行设计
   - 能够设置多个独立的 RNG 流
2. 结果在不同后端和 workers 数量下是一致的
3. `seed = TRUE` 会引入额外开销，因此默认为 `seed = FALSE`
4. 如果 future 中使用了 RNG 但没有设置 seed，会收到警告：

```r
# 警告示例
results <- future_lapply(1:5, rnorm)
# Warning: UNRELIABLE VALUE: Future ('future_lapply-1') unexpectedly
# generated random numbers without declaring so.
```

**解决方案：**

```r
# 总是使用 future.seed
results <- future_lapply(1:5, rnorm, future.seed = TRUE)

# 或设置全局选项使其成为错误
options(future.rng.onMisuse = "error")
```

---

## 5. 常见问题与解决方案

### 5.1 全局变量未导出

**问题：** 使用 `get()` 或条件赋值时，变量无法被自动识别

```r
# 问题示例 1：使用 get()
a <- 1:3
my_sum <- function(var) { sum(get(var)) }
f <- future(my_sum("a"))
value(f)
# Error: object 'a' not found

# 问题示例 2：条件赋值
reset <- FALSE
x <- 1
y %<-% { if (reset) x <- 0; x + 1 }
y
# Error: object 'x' not found
```

**解决方案：**

```r
# 方案 1：在表达式开头引用变量
f <- future({ a; my_sum("a") })

# 方案 2：使用 globals 参数显式指定
f <- future(my_sum("a"), globals = structure(TRUE, add = "a"))

# 方案 3：使用 globals 参数指定变量列表
f <- future(my_sum("a"), globals = list(a = a, my_sum = my_sum))
```

### 5.2 包未在 worker 中加载

**问题：** S3 方法分派失败，因为包未加载

```r
library(data.table)
DT <- data.table(a = LETTERS[1:3], b = 1:3)
y %<-% DT[, sum(b)]
y
# Error: object 'b' not found
# 原因：worker 中 data.table 未加载，使用了 [.data.frame
```

**解决方案：**

```r
# 方案 1：使用 packages 参数（推荐）
y %<-% DT[, sum(b)] %packages% "data.table"

# 或显式 future
f <- future(DT[, sum(b)], packages = "data.table")

# 方案 2：在表达式中显式加载包
y %<-% { library(data.table); DT[, sum(b)] }

# 注意：不要使用 library() 作为解决方案，应使用 packages 参数
```

### 5.3 不可导出对象（External Pointers）

某些 R 对象包含外部指针，无法在进程间传输。

**常见不可导出对象：**

| 包 | 对象类型 |
|---|---------|
| base | connection (file, socket) |
| DBI | DBIConnection |
| xml2 | xml_document |
| arrow | Table |
| terra | SpatRaster, SpatVector |
| keras | keras models |
| Rcpp/cpp11 | 编译的函数 |
| parallel | cluster objects |

**检测问题：**

```r
# 启用外部指针检测
options(future.globals.onReference = "error")

library(xml2)
doc <- read_xml("<body></body>")
f <- future(xml_children(doc))
# Error: Detected a non-exportable reference ('externalptr')
# in one of the globals ('doc' of class 'xml_document')
```

**解决方案：**

```r
# 方案 1：使用包提供的序列化函数
library(xml2)
doc <- read_xml("<body></body>")
.doc <- xml_serialize(doc, connection = NULL)  # 序列化

f <- future({
  doc <- xml_unserialize(.doc)  # 反序列化
  xml_children(doc)
})
result <- value(f)

# 方案 2：在 worker 中创建对象
f <- future({
  doc <- read_xml("<body></body>")
  xml_children(doc)
})

# 方案 3 (terra 包)：使用 wrap/unwrap
library(terra)
r <- rast("file.tif")
.r <- wrap(r)  # 序列化
f <- future({
  r <- unwrap(.r)  # 反序列化
  dim(r)
})
```

**假阳性（可以导出的外部指针）：**

- `data.table` 对象可以安全导出
- `rstan` 的 stanfit 对象可以安全导出

```r
# data.table 是安全的
options(future.globals.onReference = "ignore")  # 或 NULL
```

### 5.4 内存问题

**问题 1：全局变量太大**

```r
# 错误：全局变量超过限制
# Error: The total size of the X globals exported is Y bytes,
# which exceeds the maximum allowed size of Z bytes.
```

**解决方案：**

```r
# 增加限制（临时）
oopts <- options(future.globals.maxSize = 1.0 * 1e9)  # 1 GB
on.exit(options(oopts))
f <- future({ expr })

# 更好的方案：减少数据传输
# 1. 只传输需要的数据子集
# 2. 在 worker 中读取数据
# 3. 使用共享文件系统
```

**问题 2：workers 内存不足**

```r
# 使用分块处理
library(future.apply)
plan(multisession, workers = 4)

# 分块而不是一次性处理
results <- future_lapply(
  1:1000,
  function(x) process(x),
  future.chunk.size = 100  # 每个 worker 一次处理 100 个
)
```

**问题 3：嵌套并行内存爆炸**

```r
# 错误的做法
plan(list(multisession, multisession))  # 可能创建 N^2 个进程

# 正确的做法
plan(list(
  tweak(multisession, workers = 2),
  tweak(multisession, workers = I(4))
))  # 最多 2 * 4 = 8 个进程
```

---

## 6. 与其他包集成

### 6.1 mice 包（futuremice）

`mice` 包的多重插补可以通过 `futuremice` 函数并行化：

```r
library(mice)
library(future)
plan(multisession)

# 使用 futuremice 替代 mice
# 注意：需要 mice >= 3.16.0
imp <- futuremice(
  data = nhanes,
  m = 10,      # 插补数据集数量
  maxit = 20,  # 迭代次数
  seed = 123,
  n.core = 4   # 并行 worker 数量
)

# 或直接使用 future
library(mice)
library(furrr)
plan(multisession, workers = 4)

# 并行运行多个插补
imputations <- future_map(1:10, function(i) {
  mice(nhanes, m = 1, maxit = 20, seed = i, printFlag = FALSE)
}, .options = furrr_options(seed = TRUE))

# 合并结果
imp <- ibind(imputations)
```

### 6.2 targets 工作流

`targets` 是一个 make-like 的管道工具，原生支持 futures：

```r
# _targets.R
library(targets)
library(future)
library(future.batchtools)

# 使用 future 后端
tar_option_set(
  # 本地并行
  controller = crew_controller_local(workers = 4)

  # 或 HPC 集群
  # controller = crew_controller_slurm(workers = 20)
)

# 定义目标
list(
  tar_target(data, read_data("input.csv")),
  tar_target(
    model,
    fit_model(data),
    # 这个目标可以并行运行
    deployment = "worker"
  ),
  tar_target(results, summarize(model))
)
```

**运行管道：**

```r
# 设置并行后端
library(future)
plan(multisession)

# 运行管道
targets::tar_make()

# 或使用 tar_make_future()（老版本）
targets::tar_make_future(workers = 4)
```

### 6.3 foreach 适配器（doFuture）

`doFuture` 将 `foreach` 与 future 后端连接：

```r
library(foreach)
library(doFuture)
library(future)

# 注册 doFuture 适配器
registerDoFuture()

# 设置 future 后端
plan(multisession)

# 使用 foreach（现在使用 future 后端）
results <- foreach(i = 1:10, .combine = c) %dopar% {
  sqrt(i)
}

# 所有 future 后端都可用
plan(future.batchtools::batchtools_slurm)
results <- foreach(i = 1:100) %dopar% {
  expensive_computation(i)
}
```

**优势：**
- 不需要修改现有的 foreach 代码
- 自动处理全局变量和包
- 可以使用任何 future 后端

**迁移现有代码：**

```r
# 原来使用 doParallel
library(doParallel)
cl <- makeCluster(4)
registerDoParallel(cl)

# 改为使用 doFuture
library(doFuture)
registerDoFuture()
plan(multisession, workers = 4)

# foreach 代码无需修改
results <- foreach(i = 1:10) %dopar% { ... }
```

### 6.4 恢复顺序执行

在完成并行处理后，恢复顺序执行：

```r
library(future)

# 启动并行处理
plan(multisession, workers = 4)
results <- future_lapply(1:100, expensive_function)

# 恢复顺序执行（关闭 workers）
plan(sequential)
```

**重要：** 在以下场景必须调用 `plan(sequential)`：

1. 包示例结束时
2. 包 vignettes 结束时
3. 包测试结束时
4. 交互式会话结束前

```r
# 示例结构
example_function <- function() {
  library(future)
  plan(multisession)

  results <- future_lapply(1:10, sqrt)

  # 清理！
  plan(sequential)

  results
}
```

**在 R 包中的最佳实践：**

```r
#' @examples
#' library(future)
#' plan(multisession)
#'
#' result <- my_parallel_function(data)
#'
#' # 清理 workers
#' plan(sequential)
```

---

## 附录：快速参考

### 常用 plan 配置

```r
# 本地顺序执行
plan(sequential)

# 本地并行（推荐）
plan(multisession)
plan(multisession, workers = 4)

# Unix/Mac fork
plan(multicore)

# 远程集群
plan(cluster, workers = c("n1", "n2", "n3"))

# HPC Slurm
plan(future.batchtools::batchtools_slurm)

# 嵌套并行
plan(list(
  tweak(cluster, workers = c("n1", "n2")),
  multisession
))
```

### 常用选项

```r
# 全局变量大小限制（默认 500MB）
options(future.globals.maxSize = 1e9)  # 1GB

# 外部指针检测
options(future.globals.onReference = "error")  # 严格模式
options(future.globals.onReference = "warning")  # 警告模式

# 随机数警告
options(future.rng.onMisuse = "error")  # 严格模式

# 默认后端
Sys.setenv(R_FUTURE_PLAN = "multisession")
```

### availableCores() 详解

`parallelly::availableCores()` 是智能的核心数检测函数，**应始终使用它而非 `parallel::detectCores()`**：

```r
# 检查可用核心数
parallelly::availableCores()
#> mc.cores
#>        2
```

**检测优先级（从高到低）：**

1. R 选项 `mc.cores`
2. 环境变量：
   - `R_PARALLELLY_AVAILABLECORES_FALLBACK`
   - `MC_CORES`
   - HPC 调度器变量（`SLURM_CPUS_PER_TASK`, `PBS_NUM_PPN`, `SGE_NSLOTS` 等）
   - cgroups 限制（容器环境）
3. `parallel::detectCores()`

**为什么不用 detectCores()：**

```r
# detectCores() 返回所有物理核心，可能导致资源过度使用
parallel::detectCores()  # 64

# availableCores() 尊重各种限制
availableCores()  # 8（如果 mc.cores = 8）
```

**在嵌套并行中的行为：**

当 future 设置嵌套保护时，内层 worker 的 `availableCores()` 返回 1，这是保护机制的一部分。

### 调试技巧

```r
# 检查当前 plan
plan()

# 检查可用核心数
parallelly::availableCores()

# 检查全局变量
globals::globalsOf(expr)

# 详细输出
options(future.debug = TRUE)
```
