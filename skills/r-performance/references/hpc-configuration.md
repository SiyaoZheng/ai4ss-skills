# HPC 集群配置完整指南

> 本文档详细介绍如何在高性能计算集群（如 Slurm、SGE、PBS）上运行 R 并行任务。

---

## 目录

1. [概述：方案选择](#1-概述方案选择)
2. [future.batchtools 详解](#2-futurebatchtools-详解)
   - [安装与基础配置](#21-安装与基础配置)
   - [Slurm resources 参数详解](#22-slurm-resources-参数详解)
   - [模板文件编写](#23-模板文件编写)
   - [SGE/PBS/LSF 配置](#24-sgepbslsf-配置)
3. [batchtools 直接使用](#3-batchtools-直接使用)
   - [Registry 工作流](#31-registry-工作流)
   - [配置文件](#32-配置文件)
   - [ExperimentRegistry 实验管理](#33-experimentregistry-实验管理)
4. [crew.cluster 现代方案](#4-crewcluster-现代方案)
   - [与 future 的对比](#41-与-future-的对比)
   - [Slurm 控制器配置](#42-slurm-控制器配置)
   - [自动扩缩容](#43-自动扩缩容)
   - [与 targets 集成](#44-与-targets-集成)
5. [常见问题排查](#5-常见问题排查)
   - [作业不启动](#51-作业不启动)
   - [R 包找不到](#52-r-包找不到)
   - [内存不足](#53-内存不足)
   - [作业超时](#54-作业超时)
6. [资源估算与优化](#6-资源估算与优化)
7. [完整示例](#7-完整示例)

---

## 1. 概述：方案选择

在 HPC 集群上运行 R 任务有三种主要方案：

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **future.batchtools** | 统一的 future API、与 future 生态无缝集成 | 每个 future 一个作业，开销大 | 少量长时间任务 |
| **batchtools** | 细粒度控制、实验管理、作业数组 | 学习曲线陡峭 | 大规模参数扫描实验 |
| **crew.cluster** | 现代化 API、自动扩缩容、低延迟 | 较新，文档较少 | targets 工作流、需要动态调度 |

**快速选择指南：**

```
需要并行化 R 代码？
│
├─ 使用 targets 工作流？
│   └─ 是 → crew.cluster（推荐）
│
├─ 已有 future 代码？
│   └─ 是 → future.batchtools
│
├─ 需要精细控制每个作业？
│   └─ 是 → batchtools
│
└─ 简单并行任务？
    └─ future.batchtools（最简单）
```

---

## 2. future.batchtools 详解

### 2.1 安装与基础配置

```r
# 安装
install.packages("future.batchtools")

# 基本使用
library(future)
library(future.batchtools)

# 设置 Slurm 后端
plan(batchtools_slurm)

# 创建 future（作为 Slurm 作业提交）
f <- future({
  # 在集群节点上运行的代码
  Sys.info()[["nodename"]]
})

# 获取结果
value(f)
```

### 2.2 Slurm resources 参数详解

`resources` 参数用于指定作业资源需求，直接映射到 Slurm 的 `#SBATCH` 指令：

```r
plan(batchtools_slurm, resources = list(
  # ===== 时间限制 =====
  time = "04:00:00",      # 墙钟时间（walltime），格式 HH:MM:SS 或分钟数
  # 或
  walltime = 14400,       # 秒数（batchtools 风格）

  # ===== CPU 配置 =====
  ncpus = 4,              # 每个任务的 CPU 核心数（--cpus-per-task）
  ntasks = 1,             # 任务数（--ntasks），通常为 1
  nodes = 1,              # 节点数（--nodes）

  # ===== 内存配置 =====
  memory = 8000,          # 每 CPU 内存（MB）（--mem-per-cpu）
  # 或
  mem = "32G",            # 总内存（--mem）

  # ===== 分区/队列 =====
  partition = "normal",   # 分区名（--partition）
  # 或
  queue = "batch",        # 某些系统用 queue

  # ===== 环境模块 =====
  modules = c("R/4.3.0", "gcc/11.2"),  # 自动添加 module load

  # ===== 环境变量 =====
  envs = c(
    OMP_NUM_THREADS = "4",
    R_LIBS_USER = "/home/user/R/libs"
  ),

  # ===== 自定义 Rscript =====
  rscript = "/opt/R/4.3.0/bin/Rscript",
  rscript_args = c("--vanilla"),

  # ===== 高级选项 =====
  details = TRUE,         # 在日志中显示作业详情
  startup = "source ~/.bashrc",  # 作业开始时执行的 shell 命令
  shutdown = "echo 'Job finished'",  # 作业结束时执行

  # ===== 原始 SBATCH 指令 =====
  asis = c(
    "--exclusive",        # 独占节点
    "--gres=gpu:1",       # 请求 GPU
    "--constraint=haswell"  # 节点约束
  )
))
```

**常用 resources 组合示例：**

```r
# 场景 1：快速小任务
resources_fast <- list(
  time = "00:30:00",
  ncpus = 1,
  memory = 2000,
  partition = "short"
)

# 场景 2：内存密集型
resources_highmem <- list(
  time = "24:00:00",
  ncpus = 1,
  mem = "128G",
  partition = "highmem"
)

# 场景 3：多核并行
resources_multicore <- list(
  time = "04:00:00",
  ncpus = 8,
  memory = 4000,  # 每核 4GB，总共 32GB
  partition = "normal"
)

# 场景 4：GPU 任务
resources_gpu <- list(
  time = "12:00:00",
  ncpus = 4,
  memory = 8000,
  partition = "gpu",
  asis = "--gres=gpu:1"
)
```

### 2.3 模板文件编写

模板文件定义了如何生成 Slurm 作业脚本。使用 `brew` 语法（`<%= expr %>` 和 `<% code %>`）。

**默认模板位置：**

```r
# 查看内置模板
system.file("templates", "slurm.tmpl", package = "future.batchtools")
```

**自定义模板示例（~/.batchtools.slurm.tmpl）：**

```bash
#!/bin/bash
######################################################################
# 自定义 Slurm 模板
######################################################################

## 基本设置
#SBATCH --job-name=<%= job.name %>
#SBATCH --output=<%= log.file %>
#SBATCH --error=<%= log.file %>

## 资源配置
<%
# 处理各种 resources 参数
if (!is.null(resources$time)) {
  cat(sprintf("#SBATCH --time=%s\n", resources$time))
}
if (!is.null(resources$ncpus)) {
  cat(sprintf("#SBATCH --cpus-per-task=%d\n", resources$ncpus))
}
if (!is.null(resources$memory)) {
  cat(sprintf("#SBATCH --mem-per-cpu=%dM\n", resources$memory))
}
if (!is.null(resources$mem)) {
  cat(sprintf("#SBATCH --mem=%s\n", resources$mem))
}
if (!is.null(resources$partition)) {
  cat(sprintf("#SBATCH --partition=%s\n", resources$partition))
}
if (!is.null(resources$asis)) {
  for (opt in resources$asis) {
    cat(sprintf("#SBATCH %s\n", opt))
  }
}
%>

## 错误处理
set -e
set -o pipefail

## 加载环境模块
<% if (length(resources$modules) > 0) { %>
module purge
module load <%= paste(resources$modules, collapse = " ") %>
module list
<% } %>

## 设置环境变量
<% if (length(resources$envs) > 0) { %>
<% for (i in seq_along(resources$envs)) { %>
export <%= names(resources$envs)[i] %>=<%= shQuote(resources$envs[i]) %>
<% } %>
<% } %>

## 显示作业信息
echo "=========================================="
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo "Working directory: $(pwd)"
echo "=========================================="

## 运行 R 作业
<%= if (!is.null(resources$rscript)) resources$rscript else "Rscript" %> \
  -e 'batchtools::doJobCollection("<%= uri %>")'

echo "End time: $(date)"
```

**使用自定义模板：**

```r
plan(batchtools_slurm,
     template = "~/.batchtools.slurm.tmpl",
     resources = list(...))
```

### 2.4 SGE/PBS/LSF 配置

**Sun Grid Engine (SGE)：**

```r
plan(batchtools_sge, resources = list(
  h_rt = "04:00:00",      # 运行时间（SGE 格式）
  h_vmem = "8G",          # 虚拟内存
  pe = "smp 4",           # 并行环境
  q = "all.q"             # 队列
))
```

**TORQUE/PBS：**

```r
plan(batchtools_torque, resources = list(
  walltime = "04:00:00",
  nodes = "1:ppn=4",      # PBS 格式：1 节点，4 核
  mem = "32gb",
  queue = "batch"
))
```

**LSF：**

```r
plan(batchtools_lsf, resources = list(
  walltime = 14400,       # 秒
  ncpus = 4,
  memory = 8000,
  queue = "normal"
))
```

---

## 3. batchtools 直接使用

### 3.1 Registry 工作流

batchtools 使用 Registry 管理作业状态和结果：

```r
library(batchtools)

# 创建 Registry（持久化到磁盘）
reg <- makeRegistry(
  file.dir = "my_experiment",  # 存储目录
  seed = 123,                   # 随机种子
  packages = c("dplyr", "ggplot2")  # 需要加载的包
)

# 或创建临时 Registry
reg <- makeRegistry(file.dir = NA, seed = 123)

# 定义作业
batchMap(
  fun = function(x, y) {
    Sys.sleep(10)
    x + y
  },
  x = 1:100,
  y = 101:200
)

# 查看作业
getJobTable()

# 测试单个作业
testJob(id = 1)

# 提交作业
submitJobs(
  ids = 1:100,
  resources = list(
    walltime = 3600,
    memory = 2000,
    ncpus = 1
  )
)

# 监控状态
getStatus()

# 等待完成
waitForJobs()

# 收集结果
results <- reduceResultsList()  # 返回 list
# 或
results <- reduceResultsDataTable()  # 返回 data.table
```

### 3.2 配置文件

创建 `~/.batchtools.conf.R` 进行全局配置：

```r
# ~/.batchtools.conf.R

# 设置默认 cluster functions
cluster.functions <- makeClusterFunctionsSlurm(
  template = "~/.batchtools.slurm.tmpl",
  array.jobs = TRUE,  # 启用作业数组
  nodename = "localhost"
)

# 默认资源
default.resources <- list(
  walltime = 3600,
  memory = 4000,
  ncpus = 1,
  partition = "normal"
)

# 默认加载的包
packages <- c("data.table")

# 调试模式
debug <- FALSE
```

**每个项目可以有自己的配置文件（当前目录的 `.batchtools.conf.R`）：**

```r
# .batchtools.conf.R（项目目录）
cluster.functions <- makeClusterFunctionsSlurm(
  template = "slurm.tmpl"  # 项目特定模板
)

default.resources <- list(
  walltime = 86400,  # 24 小时
  memory = 16000,
  partition = "long"
)
```

### 3.3 ExperimentRegistry 实验管理

对于参数扫描实验，使用 ExperimentRegistry：

```r
library(batchtools)

# 创建实验 Registry
reg <- makeExperimentRegistry(
  file.dir = "ml_experiment",
  seed = 42
)

# 定义问题（数据）
addProblem(
  name = "iris",
  data = iris,
  fun = function(data, job, ratio = 0.8, ...) {
    n <- nrow(data)
    train_idx <- sample(n, floor(n * ratio))
    list(train = train_idx, test = setdiff(1:n, train_idx))
  },
  seed = 123
)

# 定义算法
addAlgorithm(
  name = "rf",
  fun = function(data, job, instance, ntree = 100, ...) {
    library(randomForest)
    train_data <- data[instance$train, ]
    test_data <- data[instance$test, ]

    model <- randomForest(Species ~ ., data = train_data, ntree = ntree)
    pred <- predict(model, newdata = test_data)

    list(
      accuracy = mean(pred == test_data$Species),
      confusion = table(pred, test_data$Species)
    )
  }
)

addAlgorithm(
  name = "svm",
  fun = function(data, job, instance, kernel = "radial", ...) {
    library(e1071)
    train_data <- data[instance$train, ]
    test_data <- data[instance$test, ]

    model <- svm(Species ~ ., data = train_data, kernel = kernel)
    pred <- predict(model, newdata = test_data)

    list(
      accuracy = mean(pred == test_data$Species),
      confusion = table(pred, test_data$Species)
    )
  }
)

# 定义参数网格
prob_design <- list(
  iris = data.table::CJ(ratio = c(0.6, 0.7, 0.8))
)

algo_design <- list(
  rf = data.table::CJ(ntree = c(100, 500, 1000)),
  svm = data.table::CJ(kernel = c("linear", "radial", "polynomial"))
)

# 添加实验（3 × 3 × 5 = 45 个组合，每个重复 10 次 = 450 个作业）
addExperiments(
  prob.designs = prob_design,
  algo.designs = algo_design,
  repls = 10
)

# 查看实验概要
summarizeExperiments()
summarizeExperiments(by = c("problem", "algorithm", "ratio"))

# 提交作业
submitJobs(resources = list(walltime = 600, memory = 2000))

# 等待完成
waitForJobs()

# 收集结果
results <- reduceResultsDataTable(
  fun = function(res) list(accuracy = res$accuracy)
)

# 合并参数
pars <- unwrap(getJobPars())
tab <- ijoin(pars, results)

# 分析结果
tab[, .(mean_acc = mean(accuracy), sd_acc = sd(accuracy)),
    by = .(algorithm, ntree, kernel)]
```

---

## 4. crew.cluster 现代方案

### 4.1 与 future 的对比

| 特性 | future.batchtools | crew.cluster |
|------|-------------------|--------------|
| 作业模型 | 每个 future 一个作业 | 持久 workers 处理多任务 |
| 启动延迟 | 高（等待调度器） | 低（worker 预热后） |
| 资源效率 | 低 | 高（worker 复用） |
| 自动扩缩容 | 无 | 有 |
| 错误恢复 | 手动 | 自动重试 |
| 与 targets | 通过 future | 原生集成 |

### 4.2 Slurm 控制器配置

```r
# 安装
install.packages("crew")
install.packages("crew.cluster")

library(crew)
library(crew.cluster)

# 创建 Slurm 控制器
controller <- crew_controller_slurm(
  name = "my_slurm_controller",

  # Worker 配置
  workers = 20,              # 最大 worker 数
  seconds_idle = 300,        # 空闲 5 分钟后关闭 worker
  tasks_max = 100,           # 每个 worker 最多处理 100 个任务后重启

  # Slurm 资源配置
  slurm_time_minutes = 60,   # 作业时间限制
  slurm_memory_gigabytes_per_cpu = 4,
  slurm_cpus_per_task = 2,
  slurm_partition = "normal",

  # 高级配置
  slurm_log_output = "/tmp/crew_slurm_%j.log",
  slurm_log_error = "/tmp/crew_slurm_%j.err",

  # 环境模块
  script_lines = c(
    "module load R/4.3.0",
    "module load gcc/11.2",
    "export OMP_NUM_THREADS=2"
  )
)

# 启动控制器
controller$start()

# 提交任务
controller$push(
  name = "task_1",
  command = {
    Sys.sleep(5)
    Sys.info()[["nodename"]]
  }
)

# 批量提交
for (i in 1:100) {
  controller$push(
    name = paste0("task_", i),
    command = slow_function(x),
    data = list(x = i)
  )
}

# 等待所有任务完成
controller$wait(mode = "all")

# 收集结果
results <- controller$collect()
print(results)

# 关闭控制器
controller$terminate()
```

### 4.3 自动扩缩容

crew 根据任务负载自动调整 worker 数量：

```r
controller <- crew_controller_slurm(
  name = "autoscale_demo",
  workers = 50,              # 最大 workers

  # 扩缩容参数
  seconds_idle = 120,        # 空闲 2 分钟后关闭
  tasks_max = 50,            # 每 worker 处理 50 个任务后重启
  seconds_wall = 3600,       # 软墙钟时间（1小时后优雅退出）

  # Slurm 配置
  slurm_time_minutes = 120,  # 硬墙钟时间
  slurm_memory_gigabytes_per_cpu = 2,
  slurm_cpus_per_task = 1
)

controller$start()

# 模拟工作负载波动
# 阶段 1：大量任务 → 多 workers 启动
for (i in 1:200) {
  controller$push(command = Sys.sleep(1), data = list())
}

# 等待部分完成
Sys.sleep(60)

# 阶段 2：任务减少 → workers 逐渐关闭
controller$wait(mode = "all")

# 查看摘要
controller$summary()

controller$terminate()
```

### 4.4 与 targets 集成

```r
# _targets.R
library(targets)
library(crew.cluster)

# 配置 crew 控制器
tar_option_set(
  controller = crew_controller_slurm(
    workers = 30,
    seconds_idle = 300,
    slurm_time_minutes = 120,
    slurm_memory_gigabytes_per_cpu = 4,
    slurm_cpus_per_task = 1,
    slurm_partition = "normal",
    script_lines = c(
      "module load R/4.3.0",
      "source ~/.bashrc"
    )
  )
)

# 定义 targets
list(
  tar_target(data, read_data("input.csv")),

  # 这些 targets 会在 Slurm workers 上并行运行
  tar_target(
    model,
    fit_model(data, param),
    pattern = map(param),  # 动态分支
    deployment = "worker"   # 在 worker 上运行
  ),

  tar_target(
    results,
    summarize_models(model),
    deployment = "main"  # 在主进程运行
  )
)
```

**运行 pipeline：**

```r
# 运行
targets::tar_make()

# 或显式并行
targets::tar_make(workers = 30)
```

---

## 5. 常见问题排查

### 5.1 作业不启动

**症状：** `getStatus()` 显示作业已提交但一直是 queued 状态。

**排查步骤：**

```bash
# 检查作业状态
squeue -u $USER

# 检查作业为什么等待
squeue -u $USER -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"

# 查看详细原因
scontrol show job <JOB_ID>

# 常见原因：
# - (Priority)：队列繁忙，等待
# - (Resources)：请求的资源不可用
# - (QOSMaxJobsPerUserLimit)：超出用户作业数限制
# - (ReqNodeNotAvail)：请求的节点不可用
```

**解决方案：**

```r
# 减少资源请求
resources <- list(
  time = "01:00:00",  # 减少时间
  memory = 2000,       # 减少内存
  partition = "short"  # 换到短队列
)

# 或使用作业数组减少调度开销
# 在 batchtools 中
chunk(ids, n.chunks = 10)  # 将作业分成 10 组
```

### 5.2 R 包找不到

**症状：** 作业失败，错误信息 "there is no package called 'xxx'"

**解决方案：**

```r
# 方案 1：在 resources 中指定包路径
plan(batchtools_slurm, resources = list(
  envs = c(R_LIBS_USER = "/home/user/R/libs")
))

# 方案 2：在模板中设置
# ~/.batchtools.slurm.tmpl
# export R_LIBS_USER=/home/user/R/libs

# 方案 3：在 Registry 中指定
reg <- makeRegistry(
  file.dir = NA,
  packages = c("dplyr", "ggplot2"),  # 自动加载
  source = "functions.R"  # 源文件
)

# 方案 4：在作业中显式加载
batchMap(fun = function(x) {
  library(dplyr)  # 显式加载
  x %>% summarize(...)
}, ...)
```

### 5.3 内存不足

**症状：** 作业被杀死，日志显示 "Killed" 或 "Out of memory"

**排查：**

```bash
# 查看作业实际内存使用
sacct -j <JOB_ID> --format=JobID,MaxRSS,MaxVMSize,Elapsed

# 或使用 sstat（运行中的作业）
sstat --format=AveCPU,AveRSS,MaxRSS -j <JOB_ID>
```

**解决方案：**

```r
# 增加内存请求
resources <- list(
  mem = "64G",  # 请求更多内存
  partition = "highmem"  # 高内存分区
)

# 或在 R 中优化内存使用
# 1. 分块处理大数据
# 2. 及时删除不需要的对象
# 3. 使用 data.table 而非 data.frame
```

### 5.4 作业超时

**症状：** 作业状态为 TIMEOUT

**解决方案：**

```r
# 增加时间限制
resources <- list(
  time = "48:00:00",  # 更长时间
  partition = "long"   # 长时间队列
)

# 或使用检查点
batchMap(fun = function(x, checkpoint_file) {
  # 检查是否有检查点
  if (file.exists(checkpoint_file)) {
    state <- readRDS(checkpoint_file)
  } else {
    state <- list(progress = 0)
  }

  # 继续计算
  for (i in (state$progress + 1):100) {
    # ... 计算 ...

    # 定期保存检查点
    if (i %% 10 == 0) {
      saveRDS(list(progress = i), checkpoint_file)
    }
  }
}, ...)
```

---

## 6. 资源估算与优化

### 6.1 运行时间估算

```r
library(batchtools)

# 使用 estimateRuntimes 估算
reg <- loadRegistry("my_experiment")

# 基于已完成作业估算
runtimes <- estimateRuntimes(reg)
print(runtimes)

# 基于估算进行智能分组
# LPT (Longest Processing Time)：将长任务优先分配
ids <- findNotSubmitted()
chunks <- lpt(ids, runtimes, n.chunks = 10)

# 或使用 binpack 最小化总完成时间
chunks <- binpack(ids, runtimes, n.chunks = 10)

submitJobs(chunks)
```

### 6.2 内存估算

```r
# 使用 bench 包估算内存
library(bench)

# 在小数据上测试
small_data <- head(data, 1000)
mem_usage <- bench::bench_memory({
  result <- my_function(small_data)
})

# 估算完整数据内存
scale_factor <- nrow(data) / nrow(small_data)
estimated_memory_mb <- as.numeric(mem_usage$mem_alloc) / 1024^2 * scale_factor

# 加上安全余量
resources <- list(
  memory = ceiling(estimated_memory_mb * 1.5)  # 50% 余量
)
```

### 6.3 批量作业优化

```r
# 问题：1000 个快速作业，每个只需 1 分钟
# 糟糕：提交 1000 个作业，调度开销巨大

# 方案 1：使用作业数组（batchtools）
reg <- makeRegistry(file.dir = NA)
batchMap(fun, args)

# 分块
ids <- findJobs()
chunks <- chunk(ids, n.chunks = 50)  # 50 个作业数组

submitJobs(chunks, resources = list(
  walltime = 3600  # 每个数组 1 小时处理 ~20 个任务
))

# 方案 2：使用 future.apply 的 chunk.size
library(future.apply)
plan(batchtools_slurm, resources = list(...))

results <- future_lapply(
  1:1000,
  function(i) my_function(i),
  future.chunk.size = 20  # 每个 future 处理 20 个任务
)

# 方案 3：使用 crew（推荐）
# crew 自动管理 worker 复用
controller <- crew_controller_slurm(
  workers = 20,
  tasks_max = 100  # 每 worker 处理 100 个任务
)
```

---

## 7. 完整示例

### 7.1 使用 future.batchtools 的完整工作流

```r
#!/usr/bin/env Rscript
# run_analysis.R

library(future)
library(future.batchtools)
library(future.apply)

# 配置 Slurm 后端
plan(batchtools_slurm, resources = list(
  time = "02:00:00",
  ncpus = 4,
  memory = 4000,
  partition = "normal",
  modules = c("R/4.3.0")
))

# 定义分析函数
run_simulation <- function(param) {
  # 设置本地并行（利用请求的 4 核）
  library(parallel)

  set.seed(param$seed)

  # 模拟计算
  results <- mclapply(1:100, function(i) {
    # ... 计算 ...
    rnorm(1000, mean = param$mu, sd = param$sigma)
  }, mc.cores = 4)

  list(
    param = param,
    mean = mean(unlist(results)),
    sd = sd(unlist(results))
  )
}

# 参数网格
params <- expand.grid(
  mu = seq(-1, 1, by = 0.5),
  sigma = c(0.5, 1, 2),
  seed = 1:10
)
params <- split(params, 1:nrow(params))

# 并行运行（每个参数组合一个 Slurm 作业）
results <- future_lapply(
  params,
  run_simulation,
  future.seed = TRUE
)

# 恢复顺序执行
plan(sequential)

# 整理结果
results_df <- do.call(rbind, lapply(results, function(r) {
  data.frame(
    mu = r$param$mu,
    sigma = r$param$sigma,
    seed = r$param$seed,
    mean_estimate = r$mean,
    sd_estimate = r$sd
  )
}))

# 保存
saveRDS(results_df, "simulation_results.rds")

message("Analysis complete!")
```

### 7.2 使用 crew + targets 的完整工作流

```r
# _targets.R
library(targets)
library(crew.cluster)
library(tarchetypes)

# Slurm 控制器
tar_option_set(
  controller = crew_controller_slurm(
    workers = 50,
    seconds_idle = 300,
    slurm_time_minutes = 120,
    slurm_memory_gigabytes_per_cpu = 8,
    slurm_cpus_per_task = 1,
    slurm_partition = "normal",
    script_lines = c(
      "module load R/4.3.0",
      "module load gcc/11.2"
    )
  ),
  packages = c("dplyr", "ggplot2", "broom")
)

# Pipeline
list(
  # 数据准备（本地）
  tar_target(raw_data, read.csv("data/input.csv")),

  # 定义参数
  tar_target(
    params,
    expand.grid(
      method = c("lm", "glm", "gam"),
      cv_folds = c(5, 10),
      seed = 1:100
    )
  ),

  # 并行模型拟合（Slurm workers）
  tar_target(
    model_results,
    fit_and_evaluate(raw_data, method, cv_folds, seed),
    pattern = map(params),
    deployment = "worker"
  ),

  # 汇总结果（本地）
  tar_target(
    summary_table,
    model_results %>%
      group_by(method, cv_folds) %>%
      summarize(
        mean_rmse = mean(rmse),
        se_rmse = sd(rmse) / sqrt(n()),
        .groups = "drop"
      ),
    deployment = "main"
  ),

  # 可视化（本地）
  tar_target(
    plot,
    ggplot(summary_table, aes(x = method, y = mean_rmse, fill = factor(cv_folds))) +
      geom_col(position = "dodge") +
      geom_errorbar(aes(ymin = mean_rmse - se_rmse, ymax = mean_rmse + se_rmse),
                    position = position_dodge(0.9), width = 0.2) +
      theme_minimal(),
    deployment = "main"
  ),

  # 保存报告
  tar_render(report, "report.Rmd", deployment = "main")
)
```

**运行：**

```bash
# 在登录节点上运行
Rscript -e 'targets::tar_make()'

# 或查看进度
Rscript -e 'targets::tar_watch()'
```

---

## 附录：快速参考

### Slurm 常用命令

```bash
# 提交作业
sbatch script.sh

# 查看队列
squeue -u $USER

# 取消作业
scancel <JOB_ID>
scancel -u $USER  # 取消所有作业

# 查看作业详情
scontrol show job <JOB_ID>

# 查看作业历史
sacct -j <JOB_ID> --format=JobID,JobName,Partition,Account,AllocCPUS,State,ExitCode,Elapsed,MaxRSS

# 查看分区信息
sinfo

# 查看账户限制
sacctmgr show qos
```

### resources 参数速查表

| 参数 | Slurm 对应 | 说明 |
|------|-----------|------|
| `time` | `--time` | 墙钟时间 (HH:MM:SS) |
| `ncpus` | `--cpus-per-task` | CPU 核心数 |
| `memory` | `--mem-per-cpu` | 每核内存 (MB) |
| `mem` | `--mem` | 总内存 |
| `nodes` | `--nodes` | 节点数 |
| `ntasks` | `--ntasks` | 任务数 |
| `partition` | `--partition` | 分区 |
| `modules` | `module load` | 环境模块 |
| `asis` | 原样 | 自定义 SBATCH 指令 |

### 故障排查检查清单

- [ ] R 包路径正确？（`R_LIBS_USER`）
- [ ] 环境模块加载？（`module load R`）
- [ ] 资源请求合理？（不超限、不过少）
- [ ] 分区存在且可用？
- [ ] 作业脚本权限正确？
- [ ] 日志文件目录可写？
- [ ] 工作目录正确？
