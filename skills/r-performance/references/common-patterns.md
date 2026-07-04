# R 性能优化常见模式与陷阱

本文档总结 R 语言中常见的性能优化模式，包括反模式（慢）和推荐模式（快）的对比代码示例。

## 目录

1. [向量化模式](#1-向量化模式)
   - [向量增长 vs 预分配](#11-向量增长-vs-预分配)
   - [循环中的 rbind vs rbindlist](#12-循环中的-rbind-vs-rbindlist)
   - [行操作 vs 列操作](#13-行操作-vs-列操作)
   - [ifelse vs case_when](#14-ifelse-vs-case_when)
2. [数据结构选择](#2-数据结构选择)
   - [data.frame vs data.table vs tibble](#21-dataframe-vs-datatable-vs-tibble)
   - [matrix vs data.frame](#22-matrix-vs-dataframe)
   - [list vs environment](#23-list-vs-environment)
   - [hash tables](#24-hash-tables-哈希表)
3. [函数调用优化](#3-函数调用优化)
   - [避免循环中重复函数查找](#31-避免循环中重复函数查找)
   - [显式命名空间](#32-显式命名空间)
   - [Memoization 缓存](#33-memoization-缓存)
4. [I/O 优化](#4-io-优化)
   - [fread/fwrite vs read.csv/write.csv](#41-freadfwrite-vs-readcsvwritecsv)
   - [readRDS/saveRDS vs save/load](#42-readrdssaverds-vs-saveload)
   - [Arrow/Parquet](#43-arrowparquet)
   - [数据库连接池](#44-数据库连接池)
5. [并行化陷阱](#5-并行化陷阱)
   - [开销 vs 收益](#51-开销-vs-收益)
   - [负载均衡与分块](#52-负载均衡与分块)
   - [避免嵌套并行](#53-避免嵌套并行)
   - [随机种子处理](#54-随机种子处理)
   - [全局变量识别问题](#55-全局变量识别问题)
   - [不可导出对象](#56-不可导出对象)
   - [包依赖问题](#57-包依赖问题)
6. [data.table 特有优化](#6-datatable-特有优化)
   - [:= 原地修改](#61--原地修改)
   - [.SD 和 .SDcols](#62-sd-和-sdcols)
   - [setkey 快速连接](#63-setkey-快速连接)
   - [by= 分组效率](#64-by-分组效率)
7. [常见陷阱清单](#7-常见陷阱清单)
   - [stringsAsFactors](#71-stringsasfactors)
   - [1:length(x) vs seq_along(x)](#72-1lengthx-vs-seq_alongx)
   - [sapply 类型不稳定](#73-sapply-类型不稳定)
   - [浮点数比较](#74-浮点数比较)
   - [避免 attach() 和 <<-](#75-避免-attach-和--)
   - [字符串操作优化](#76-字符串操作优化)
   - [矩阵运算优化](#77-矩阵运算优化)
8. [内存追踪工具](#8-内存追踪工具)
   - [tracemem 追踪对象复制](#81-tracemem-追踪对象复制)
   - [Copy-on-modify 机制](#82-copy-on-modify-机制)

---

## 1. 向量化模式

### 1.1 向量增长 vs 预分配

**问题**：在循环中逐步增长向量会导致 R 反复重新分配内存，时间复杂度为 O(n²)。

```r
# 慢：向量逐步增长
result <- c()
for (i in 1:100000) {
  result <- c(result, i^2)  # 每次都复制整个向量
}

# 快：预分配内存
result <- numeric(100000)  # 一次性分配
for (i in 1:100000) {
  result[i] <- i^2
}

# 最快：完全向量化
result <- (1:100000)^2
```

**性能差异**：10 万次迭代，增长方式约需 10 秒，预分配约 0.1 秒，向量化约 0.001 秒。

### 1.2 循环中的 rbind vs rbindlist

**问题**：`rbind()` 在循环中合并 data.frame 同样存在内存重复分配问题。

```r
# 慢：循环中使用 rbind
result <- data.frame()
for (i in 1:1000) {
  row <- data.frame(x = i, y = i^2)
  result <- rbind(result, row)  # O(n²) 复杂度
}

# 快：收集到 list，最后合并
library(data.table)
result_list <- vector("list", 1000)
for (i in 1:1000) {
  result_list[[i]] <- data.frame(x = i, y = i^2)
}
result <- rbindlist(result_list)  # data.table 方式，最快

# 或使用 base R
result <- do.call(rbind, result_list)
```

**推荐**：优先使用 `data.table::rbindlist()`，其次是 `dplyr::bind_rows()`，最后才是 `do.call(rbind, ...)`。

### 1.3 行操作 vs 列操作

**问题**：R 的 data.frame 是列存储的，按列操作比按行操作快得多。

```r
df <- data.frame(a = rnorm(100000), b = rnorm(100000))

# 慢：按行操作
result <- numeric(nrow(df))
for (i in 1:nrow(df)) {
  result[i] <- df$a[i] + df$b[i]
}

# 慢：apply 按行
result <- apply(df, 1, function(row) row["a"] + row["b"])

# 快：向量化列操作
result <- df$a + df$b
```

**注意**：`apply(df, 1, ...)` 会将 data.frame 转换为 matrix，丢失类型信息且性能不佳。

### 1.4 ifelse vs case_when

**问题**：嵌套 `ifelse` 难读且效率低；`case_when` 更清晰但有开销。

```r
x <- sample(1:100, 100000, replace = TRUE)

# 慢且难读：嵌套 ifelse
result <- ifelse(x < 25, "low",
           ifelse(x < 50, "medium-low",
             ifelse(x < 75, "medium-high", "high")))

# 更清晰：dplyr::case_when
library(dplyr)
result <- case_when(
  x < 25 ~ "low",
  x < 50 ~ "medium-low",
  x < 75 ~ "medium-high",
  TRUE   ~ "high"
)

# 最快：使用 cut 或 findInterval
result <- cut(x, breaks = c(0, 25, 50, 75, 100),
              labels = c("low", "medium-low", "medium-high", "high"))

# 或使用查找表（适合离散值）
levels <- c("low", "medium-low", "medium-high", "high")
result <- levels[findInterval(x, c(25, 50, 75)) + 1]
```

**建议**：连续区间用 `cut()` 或 `findInterval()`；离散值用查找表或 `match()`。

---

## 2. 数据结构选择

### 2.1 data.frame vs data.table vs tibble

| 特性 | data.frame | data.table | tibble |
|------|-----------|------------|--------|
| 速度 | 基准 | 最快 (10-100x) | 略慢于 data.frame |
| 内存效率 | 一般 | 最优（原地修改） | 一般 |
| 语法 | 基础 | 简洁但学习曲线陡 | 与 dplyr 配合 |
| 打印 | 全部输出 | 智能截断 | 智能截断 |
| 适用场景 | 小数据、兼容性 | 大数据、性能敏感 | tidyverse 生态 |

```r
# data.frame: 基础 R
df <- data.frame(x = 1:1e6, y = rnorm(1e6))
result <- aggregate(y ~ x %% 100, data = df, FUN = mean)

# data.table: 高性能
library(data.table)
dt <- data.table(x = 1:1e6, y = rnorm(1e6))
result <- dt[, .(mean_y = mean(y)), by = x %% 100]

# tibble + dplyr: 可读性
library(dplyr)
tb <- tibble(x = 1:1e6, y = rnorm(1e6))
result <- tb %>% group_by(x %% 100) %>% summarise(mean_y = mean(y))
```

**选择建议**：
- 数据 > 100万行：优先 data.table
- tidyverse 工作流：tibble
- 简单分析或教学：data.frame

### 2.2 matrix vs data.frame

**问题**：data.frame 是 list 的特殊形式，每列可以不同类型；matrix 是单一类型的高效数组。

```r
# 数值计算用 matrix 更快
n <- 1000
m <- 1000

# 慢：data.frame 数值运算
df <- data.frame(matrix(rnorm(n * m), n, m))
result <- rowSums(df)  # 需要类型转换

# 快：matrix 数值运算
mat <- matrix(rnorm(n * m), n, m)
result <- rowSums(mat)  # 原生支持
```

**使用场景**：
- 纯数值计算（线性代数、统计）：matrix
- 混合类型数据：data.frame/data.table
- 需要行名列名且类型一致：matrix

### 2.3 list vs environment

**问题**：list 用索引或名称访问，复杂度 O(n)；environment 用哈希表，复杂度 O(1)。

```r
n <- 10000
keys <- paste0("key_", 1:n)

# list: 按名访问是 O(n)
my_list <- setNames(as.list(1:n), keys)
system.time(for (i in 1:1000) my_list[["key_5000"]])

# environment: 按名访问是 O(1)
my_env <- list2env(setNames(as.list(1:n), keys))
system.time(for (i in 1:1000) my_env[["key_5000"]])
```

**注意**：environment 有引用语义（reference semantics），修改会影响原对象。

### 2.4 hash tables (哈希表)

R 没有原生哈希表，但可以用 environment 模拟。

```r
# 创建哈希表
hash_new <- function() new.env(hash = TRUE, parent = emptyenv())

hash_set <- function(h, key, value) {
  h[[as.character(key)]] <- value
  invisible(h)
}

hash_get <- function(h, key) {
  h[[as.character(key)]]
}

hash_exists <- function(h, key) {
  exists(as.character(key), envir = h, inherits = FALSE)
}

# 使用示例
cache <- hash_new()
hash_set(cache, "user_123", list(name = "Alice", score = 95))
hash_get(cache, "user_123")

# 或使用 collections 包
# install.packages("collections")
library(collections)
d <- dict()
d$set("key", "value")
```

---

## 3. 函数调用优化

### 3.1 避免循环中重复函数查找

**问题**：R 每次调用函数都要在 search path 中查找，循环中会重复查找。

```r
n <- 1000000

# 慢：每次循环都查找 sqrt
result <- numeric(n)
for (i in 1:n) {
  result[i] <- sqrt(i)
}

# 快：提前缓存函数引用
sqrt_local <- sqrt
result <- numeric(n)
for (i in 1:n) {
  result[i] <- sqrt_local(i)
}

# 最快：向量化（不需要循环）
result <- sqrt(1:n)
```

### 3.2 显式命名空间

**问题**：`dplyr::filter` 比 `filter` 快，因为跳过了 search path 查找。

```r
# 慢：需要在 search path 中查找 filter
library(dplyr)
result <- filter(df, x > 0)

# 快：显式命名空间，直接定位
result <- dplyr::filter(df, x > 0)

# 额外好处：避免命名冲突
# stats::filter 和 dplyr::filter 是不同函数
```

**最佳实践**：在包开发中始终使用显式命名空间；在脚本中至少对常用函数显式指定。

### 3.3 Memoization 缓存

**问题**：相同输入重复计算浪费时间，memoization 可以缓存结果。

```r
# 安装：install.packages("memoise")
library(memoise)

# 原始函数（假设计算开销大）
slow_fib <- function(n) {
  if (n <= 1) return(n)
  slow_fib(n - 1) + slow_fib(n - 2)
}

# memoized 版本
fast_fib <- memoise(slow_fib)

# 第一次调用：计算并缓存
system.time(fast_fib(30))  # 约 1 秒

# 第二次调用：直接返回缓存
system.time(fast_fib(30))  # 约 0 秒

# 带过期时间的缓存
cached_api_call <- memoise(
  api_call,
  cache = cache_filesystem("~/.rcache"),
  ~timeout(3600)  # 1 小时过期
)
```

**适用场景**：
- 纯函数（相同输入必然相同输出）
- 计算开销大
- 会被重复调用

---

## 4. I/O 优化

### 4.1 fread/fwrite vs read.csv/write.csv

```r
library(data.table)

# 写入 100 万行测试数据
df <- data.frame(
  id = 1:1000000,
  value = rnorm(1000000),
  category = sample(letters, 1000000, replace = TRUE)
)

# 慢：base R
system.time(write.csv(df, "test_base.csv", row.names = FALSE))
# 约 15 秒

# 快：data.table
system.time(fwrite(df, "test_dt.csv"))
# 约 0.3 秒（快 50 倍）

# 读取对比
system.time(read.csv("test_base.csv"))  # 约 10 秒
system.time(fread("test_dt.csv"))        # 约 0.2 秒
```

**fread 额外优势**：
- 自动检测分隔符、列类型、编码
- 支持选择特定列：`fread("file.csv", select = c("id", "value"))`
- 支持 shell 命令：`fread("gunzip -c file.csv.gz")`

### 4.2 readRDS/saveRDS vs save/load

```r
# save/load：保存对象及其名称
save(df, file = "data.RData")  # 必须用原名加载
load("data.RData")  # df 自动出现在环境中

# saveRDS/readRDS：保存对象，可以自定义名称（推荐）
saveRDS(df, "data.rds")
my_df <- readRDS("data.rds")  # 可以用任意名称

# saveRDS 更灵活，适合管道式工作流
result <- readRDS("input.rds") %>%
  transform(new_col = old_col * 2) %>%
  saveRDS("output.rds")
```

**压缩选项**：
```r
# 不压缩（最快写入，文件最大）
saveRDS(df, "data.rds", compress = FALSE)

# gzip 压缩（默认，平衡速度和大小）
saveRDS(df, "data.rds", compress = "gzip")

# xz 压缩（最小文件，最慢）
saveRDS(df, "data.rds", compress = "xz")

# 使用 qs 包更快
# install.packages("qs")
library(qs)
qsave(df, "data.qs")
df <- qread("data.qs")  # 比 saveRDS 快 3-5 倍
```

### 4.3 Arrow/Parquet

Parquet 是列式存储格式，适合大数据分析。

```r
# install.packages("arrow")
library(arrow)

# 写入 Parquet
write_parquet(df, "data.parquet")

# 读取 Parquet
df <- read_parquet("data.parquet")

# 部分列读取（列式存储优势）
df <- read_parquet("data.parquet", col_select = c("id", "value"))

# 分区数据集
write_dataset(df, "data_partitioned", partitioning = "category")

# 延迟计算（只读取需要的数据）
ds <- open_dataset("data_partitioned")
result <- ds %>%
  filter(category == "a") %>%
  select(id, value) %>%
  collect()  # 此时才真正读取
```

**何时使用 Parquet**：
- 数据 > 1GB
- 只需要部分列
- 需要跨语言共享（Python、Spark 都支持）

### 4.4 数据库连接池

**问题**：每次查询都创建新连接开销大。

```r
# 慢：每次查询新建连接
fetch_data <- function(query) {
  con <- DBI::dbConnect(RSQLite::SQLite(), "database.db")
  result <- DBI::dbGetQuery(con, query)
  DBI::dbDisconnect(con)
  result
}

# 快：使用连接池
library(pool)
pool <- dbPool(
  drv = RSQLite::SQLite(),
  dbname = "database.db",
  minSize = 1,
  maxSize = 10
)

fetch_data <- function(query) {
  DBI::dbGetQuery(pool, query)  # 自动管理连接
}

# 程序结束时关闭池
# poolClose(pool)
```

---

## 5. 并行化陷阱

### 5.1 开销 vs 收益

**问题**：并行化有启动开销，小任务反而更慢。

```r
library(future.apply)
plan(multisession, workers = 4)

# 不适合并行：单次操作太快
x <- 1:1000
system.time(future_sapply(x, sqrt))  # 可能比 sapply 更慢
system.time(sapply(x, sqrt))

# 适合并行：单次操作耗时
slow_func <- function(i) {
  Sys.sleep(0.01)  # 模拟耗时操作
  i^2
}
system.time(future_sapply(1:100, slow_func))  # 约 0.25 秒
system.time(sapply(1:100, slow_func))          # 约 1 秒
```

**并行化值得的条件**：
- 单次操作 > 10ms
- 任务数量足够多（至少 CPU 核心数的几倍）
- 任务之间无依赖

### 5.2 负载均衡与分块

**问题**：任务大小不均匀时，部分 worker 可能空闲。

```r
# 不均匀任务
tasks <- c(rep(0.001, 90), rep(1, 10))  # 90 个快任务，10 个慢任务

# 默认调度可能不均匀
plan(multisession, workers = 4)
future_sapply(tasks, function(t) { Sys.sleep(t); t })

# 动态调度：future.scheduling = Inf
future_sapply(tasks, function(t) { Sys.sleep(t); t },
              future.scheduling = Inf)  # 完成一个立即分配下一个

# 或手动分块
chunk_size <- ceiling(length(tasks) / 4)
chunks <- split(tasks, ceiling(seq_along(tasks) / chunk_size))
# 然后每个 chunk 并行处理
```

### 5.3 避免嵌套并行

**问题**：外层并行调用内层并行，可能创建过多进程耗尽资源。

```r
# 危险：嵌套并行
library(future.apply)
plan(multisession, workers = 4)

outer_func <- function(x) {
  # 内层也用并行！
  future_sapply(1:100, function(i) i * x)  # 4 * 4 = 16 个进程！
}
future_sapply(1:4, outer_func)  # 可能耗尽内存

# 安全：内层使用顺序执行
outer_func <- function(x) {
  sapply(1:100, function(i) i * x)  # 顺序执行
}
future_sapply(1:4, outer_func)

# 或使用 %plan% 局部覆盖
outer_func <- function(x) {
  old_plan <- plan(sequential)  # 内层强制顺序
  on.exit(plan(old_plan))
  future_sapply(1:100, function(i) i * x)
}
```

### 5.4 随机种子处理

**问题**：并行时各 worker 可能使用相同随机种子，导致结果不可重复或相同。

```r
library(future.apply)
plan(multisession, workers = 4)

# 错误：不设置种子，结果不可重复
future_sapply(1:4, function(i) rnorm(1))

# 正确：使用 future.seed
set.seed(42)
future_sapply(1:4, function(i) rnorm(1), future.seed = TRUE)

# 每次运行结果相同
set.seed(42)
future_sapply(1:4, function(i) rnorm(1), future.seed = TRUE)

# 使用 L'Ecuyer-CMRG 种子（推荐用于并行）
RNGkind("L'Ecuyer-CMRG")
set.seed(42)
future_sapply(1:4, function(i) rnorm(1), future.seed = TRUE)
```

### 5.5 全局变量识别问题

**问题**：future 框架通过静态代码分析识别全局变量，但某些情况下会失败。

```r
library(future)
plan(multisession)

# 问题 1：条件赋值导致全局变量无法识别
reset <- FALSE
x <- 1
y %<-% { if (reset) x <- 0; x + 1 }  # 错误：object 'x' not found

# 解决：在表达式开头引用变量
y %<-% { x; if (reset) x <- 0; x + 1 }  # 正确

# 问题 2：do.call() 中用字符串指定函数
library(tools)
do.call("file_ext", list("foo.txt"))  # 可能在 worker 中找不到

# 解决：用函数对象而非字符串
do.call(file_ext, list("foo.txt"))  # 正确

# 问题 3：get() 无法被静态分析
a <- 1:3
my_sum <- function(var) sum(get(var))
f <- future(my_sum("a"))  # 错误：object 'a' not found

# 解决方案 1：显式声明额外全局变量
f <- future(my_sum("a"), globals = structure(TRUE, add = "a"))

# 解决方案 2：在表达式中引用
f <- future({ a; my_sum("a") })

# 问题 4：glue() 字符串中的变量
library(glue)
a <- 42
s %<-% glue("The value is {a}.")  # 错误

# 解决
s %<-% glue("The value is {a}.") %globals% structure(TRUE, add = "a")
# 或
s %<-% { a; glue("The value is {a}.") }
```

**规则**：避免使用 `get()`、`mget()`、`assign()` 等动态变量访问。如必须使用，需显式声明全局变量。

### 5.6 不可导出对象

**问题**：某些对象（external pointer）绑定到特定 R 会话，无法传递给 worker。

```r
library(future)
plan(multisession)

# 常见不可导出对象
# - xml2 的 XML 对象
# - DBI 数据库连接
# - 某些 C++ 对象（Rcpp）
# - 文件句柄

library(xml2)
xml <- read_xml("<body></body>")
f <- future(xml_children(xml))
value(f)  # 错误：external pointer is not valid

# 启用检测
options(future.globals.onReference = "error")
f <- future(xml_children(xml))
# 错误：Detected a non-exportable reference...

# 解决：在 worker 内部创建对象
f <- future({
  xml <- read_xml("<body></body>")
  xml_children(xml)
})

# 数据库连接也类似
f <- future({
  con <- DBI::dbConnect(...)
  on.exit(DBI::dbDisconnect(con))
  DBI::dbGetQuery(con, query)
})
```

### 5.7 包依赖问题

**问题**：S3 方法可能在 worker 中不可用，导致回退到错误的方法。

```r
library(future)
plan(multisession)

library(data.table)
DT <- data.table(a = LETTERS[1:3], b = 1:3)
y %<-% DT[, sum(b)]
y  # 错误：object 'b' not found

# 原因：worker 没有加载 data.table，使用了 data.frame 的 [ 方法
# 解决：显式声明包依赖
y %<-% DT[, sum(b)] %packages% "data.table"
y  # [1] 6

# 或使用 future() 函数
f <- future(DT[, sum(b)], packages = "data.table")
value(f)

# 注意：不要用 library() 在 future 内加载包
# 错误做法
y %<-% { library(data.table); DT[, sum(b)] }  # 不推荐
```

**"..." 传递问题**：

```r
# 问题：在 future 中使用 ... 作为全局变量
my_fcn <- function(X, ...) {
  y <- future_lapply(X, FUN = function(x) {
    round(x, ...)  # 错误：'...' used in an incorrect context
  })
  y
}

# 解决：正确传递 ...
my_fcn <- function(X, ...) {
  y <- future_lapply(X, FUN = function(x, ...) {
    round(x, ...)
  }, ...)  # 通过 ... 显式传递
  y
}
```

---

## 6. data.table 特有优化

### 6.1 := 原地修改

**问题**：base R 的修改会复制整个对象；data.table 的 `:=` 是原地修改。

```r
library(data.table)
dt <- data.table(x = 1:1e6, y = rnorm(1e6))

# 慢：复制后修改（base R 语义）
dt_copy <- copy(dt)
dt_copy$z <- dt_copy$x + dt_copy$y  # 创建新对象

# 快：原地修改
dt[, z := x + y]  # 不复制，直接修改

# 原地删除列
dt[, z := NULL]

# 原地修改多列
dt[, c("a", "b") := .(x * 2, y * 2)]

# 条件修改（避免 ifelse）
dt[x > 500000, category := "high"]
dt[x <= 500000, category := "low"]
```

**注意**：`:=` 修改的是原对象，如需保留原数据请先 `copy()`。

### 6.2 .SD 和 .SDcols

`.SD` (Subset of Data) 是当前分组的子集 data.table。

```r
dt <- data.table(
  group = rep(c("A", "B", "C"), each = 1000),
  x = rnorm(3000),
  y = rnorm(3000),
  z = rnorm(3000)
)

# 对所有数值列求均值
dt[, lapply(.SD, mean), by = group]

# 只对指定列操作（更快）
dt[, lapply(.SD, mean), by = group, .SDcols = c("x", "y")]

# 使用模式选择列
dt[, lapply(.SD, mean), by = group, .SDcols = patterns("^x|^y")]

# 对数值列标准化
num_cols <- c("x", "y", "z")
dt[, (num_cols) := lapply(.SD, scale), .SDcols = num_cols]
```

### 6.3 setkey 快速连接

```r
# 创建测试数据
dt1 <- data.table(id = sample(1:1e5, 1e6, replace = TRUE), value1 = rnorm(1e6))
dt2 <- data.table(id = 1:1e5, value2 = rnorm(1e5))

# 慢：无键连接
system.time(merge(dt1, dt2, by = "id"))

# 快：设置键后连接
setkey(dt1, id)
setkey(dt2, id)
system.time(dt1[dt2])  # 快 10 倍以上

# 二级键
setkey(dt1, id)  # 物理排序
setindex(dt1, value1)  # 逻辑索引，不改变物理顺序

# 范围查询也更快
setkey(dt1, id)
dt1[.(1:100)]  # 快速获取 id 在 1-100 的行
```

### 6.4 by= 分组效率

```r
dt <- data.table(
  group = sample(letters, 1e6, replace = TRUE),
  subgroup = sample(1:100, 1e6, replace = TRUE),
  value = rnorm(1e6)
)

# 基本分组
dt[, .(mean_val = mean(value)), by = group]

# 多列分组
dt[, .(mean_val = mean(value)), by = .(group, subgroup)]

# keyby：分组并按键排序结果
dt[, .(mean_val = mean(value)), keyby = group]

# .N：每组行数
dt[, .N, by = group]

# .GRP：分组序号
dt[, .(grp_id = .GRP, count = .N), by = group]

# 分组后取每组前 N 行
dt[, head(.SD, 3), by = group]

# 分组后取每组最大值所在行
dt[, .SD[which.max(value)], by = group]
```

---

## 7. 常见陷阱清单

### 7.1 stringsAsFactors

**问题**：R < 4.0 中 `data.frame()` 默认将字符串转为 factor，可能导致意外行为。

```r
# R < 4.0 的坑
df <- data.frame(name = c("Alice", "Bob"))
df$name[1] <- "Charlie"  # 错误：factor 没有 "Charlie" 这个 level

# 解决方案 1：显式指定
df <- data.frame(name = c("Alice", "Bob"), stringsAsFactors = FALSE)

# 解决方案 2：全局设置（不推荐，影响其他代码）
options(stringsAsFactors = FALSE)

# R >= 4.0：默认 stringsAsFactors = FALSE，无此问题
```

### 7.2 1:length(x) vs seq_along(x)

**问题**：当 `x` 为空时，`1:length(x)` 返回 `c(1, 0)`，导致循环执行两次。

```r
x <- c()  # 空向量

# 危险
for (i in 1:length(x)) {
  print(i)  # 输出 1, 然后 0！
}

# 安全
for (i in seq_along(x)) {
  print(i)  # 不输出任何内容
}

# seq_len 也是安全的
for (i in seq_len(length(x))) {
  print(i)
}
```

**规则**：永远使用 `seq_along()` 或 `seq_len()`，永远不要用 `1:n`。

### 7.3 sapply 类型不稳定

**问题**：`sapply()` 根据结果自动简化类型，可能返回 vector、matrix 或 list。

```r
# 结果长度一致：返回 vector
sapply(1:3, function(i) i^2)
# [1] 1 4 9

# 结果长度不一致：返回 list
sapply(1:3, function(i) rep(i, i))
# [[1]] [1] 1
# [[2]] [1] 2 2
# [[3]] [1] 3 3 3

# 结果为空：返回 list()
sapply(c(), function(i) i^2)
# list()

# 安全替代：vapply 显式指定返回类型
vapply(1:3, function(i) i^2, FUN.VALUE = numeric(1))

# 或始终返回 list
lapply(1:3, function(i) i^2)
```

**规则**：
- 生产代码用 `vapply()` 或 `lapply()`
- 只在交互式探索时用 `sapply()`

### 7.4 浮点数比较

**问题**：浮点数运算有精度误差，直接比较可能失败。

```r
# 危险：直接比较
0.1 + 0.2 == 0.3  # FALSE!

# 原因
print(0.1 + 0.2, digits = 20)  # 0.30000000000000004

# 安全：使用容差比较
all.equal(0.1 + 0.2, 0.3)  # TRUE

# 在条件判断中
x <- 0.1 + 0.2
if (isTRUE(all.equal(x, 0.3))) {
  print("Equal")
}

# 或使用 dplyr::near
library(dplyr)
near(0.1 + 0.2, 0.3)  # TRUE

# 自定义容差
near(0.1 + 0.2, 0.3, tol = 1e-10)  # TRUE

# 向量比较
x <- c(0.1 + 0.2, 0.3, 0.30001)
near(x, 0.3)  # TRUE TRUE FALSE
```

**规则**：
- 永远不要用 `==` 比较浮点数
- 使用 `all.equal()` 或 `dplyr::near()`
- 如需整数，显式转换：`as.integer(round(x))`

### 7.5 避免 attach() 和 <<-

**问题**：`attach()` 和 `<<-` 会产生全局副作用，导致难以追踪的 bug。

```r
# 危险：attach() 污染搜索路径
df <- data.frame(x = 1:10, y = 11:20)
attach(df)
x + y  # 可以直接访问，但...
x <- 100  # 创建了新的全局变量，不是修改 df$x！
detach(df)

# 危险：<<- 修改父环境
counter <- 0
increment <- function() {
  counter <<- counter + 1  # 修改全局变量
}
# 问题：难以追踪、测试、并行化

# 正确做法：使用显式传参和返回值
counter <- 0
increment <- function(counter) {
  counter + 1  # 返回新值
}
counter <- increment(counter)

# 或使用 R6/环境封装状态
Counter <- R6::R6Class("Counter",
  public = list(
    value = 0,
    increment = function() {
      self$value <- self$value + 1
      invisible(self)
    }
  )
)
```

**规则**：
- 永远不要用 `attach()`，使用 `with()` 或 `$`
- 避免 `<<-`，除非在闭包中有意使用

### 7.6 字符串操作优化

```r
# paste0 vs paste：paste0 稍快（不需要 sep 参数处理）
system.time(replicate(1e5, paste("a", "b", sep = "")))
system.time(replicate(1e5, paste0("a", "b")))

# sprintf 比多次 paste 更高效
# 慢：多次字符串拼接
msg <- paste("Name:", name, ", Age:", age, ", Score:", score)

# 快：sprintf 一次完成
msg <- sprintf("Name: %s, Age: %d, Score: %.2f", name, age, score)

# 大量字符串拼接：使用 stringi 或 collapse
library(stringi)

# 慢：循环拼接
result <- ""
for (s in strings) {
  result <- paste0(result, s)  # O(n²)
}

# 快：paste 的 collapse 参数
result <- paste(strings, collapse = "")

# 更快：stringi
result <- stri_c(strings, collapse = "")

# 字符串搜索：fixed = TRUE 更快
grepl("pattern", x, fixed = TRUE)  # 精确匹配，快
grepl("pattern", x)                 # 正则匹配，慢
```

### 7.7 矩阵运算优化

```r
# 使用优化的 BLAS 库（如 OpenBLAS、MKL）
# 检查当前 BLAS
sessionInfo()  # 查看 BLAS/LAPACK

# 逐元素 vs 矩阵运算
n <- 1000
A <- matrix(rnorm(n^2), n, n)
B <- matrix(rnorm(n^2), n, n)

# 慢：逐元素循环
C <- matrix(0, n, n)
for (i in 1:n) {
  for (j in 1:n) {
    C[i, j] <- A[i, j] + B[i, j]
  }
}

# 快：向量化矩阵运算
C <- A + B

# 矩阵乘法：使用 %*% 而非手动循环
# 慢
C <- matrix(0, n, n)
for (i in 1:n) {
  for (j in 1:n) {
    for (k in 1:n) {
      C[i, j] <- C[i, j] + A[i, k] * B[k, j]
    }
  }
}

# 快：利用 BLAS
C <- A %*% B

# tcrossprod 和 crossprod 比 %*% 更快
# t(A) %*% B 等价于 crossprod(A, B)
# A %*% t(B) 等价于 tcrossprod(A, B)

# 对称矩阵：只计算一半
# 普通
cov_matrix <- t(X) %*% X

# 更快（利用对称性）
cov_matrix <- crossprod(X)
```

---

## 8. 内存追踪工具

### 8.1 tracemem 追踪对象复制

`tracemem()` 可以追踪特定对象何时被复制（需要 R 编译时启用 `--enable-memory-profiling`）。

```r
# 标记对象进行追踪
x <- 1:1000000
tracemem(x)
# [1] "<0x7f8b12345678>"

# 修改时会显示复制
y <- x  # 不复制（只是引用）
y[1] <- 0L  # 复制发生！
# tracemem[0x7f8b12345678 -> 0x7f8b87654321]: ...

# data.frame 的隐藏复制
df <- data.frame(a = 1:1000, b = 1:1000)
tracemem(df)

df$c <- df$a + df$b  # 可能触发整个 df 的复制！

# 停止追踪
untracemem(x)
```

**示例：发现意外复制**

```r
# boot 包的例子（来自 R 官方文档）
st <- data.frame(Time = 1:100, fit = rnorm(100))
tracemem(st)

# 这行代码会触发多次复制
st$Time <- st$fit + rnorm(100)
# memtrace[... -> ...]: $<-.data.frame $<- ...
```

### 8.2 Copy-on-modify 机制

R 使用 copy-on-modify 语义：对象在被修改时才复制，不是在赋值时。

```r
# 赋值不复制
x <- 1:1e6
y <- x  # y 和 x 共享同一内存
pryr::address(x) == pryr::address(y)  # TRUE

# 修改时复制
y[1] <- 0L  # 此时 y 才获得自己的副本
pryr::address(x) == pryr::address(y)  # FALSE

# 函数参数传递
modify_first <- function(vec) {
  vec[1] <- 0  # 在函数内修改会触发复制
  vec
}

x <- 1:1e6
tracemem(x)
y <- modify_first(x)  # 复制发生在函数内部
# x 不变，因为 R 是 call-by-value（通过 copy-on-modify 实现）

# data.frame 列赋值的陷阱
df <- data.frame(x = 1:1e6, y = rnorm(1e6))
tracemem(df)

# 这会复制整个 data.frame！
df$z <- df$x + df$y

# data.table 避免这个问题
library(data.table)
dt <- data.table(x = 1:1e6, y = rnorm(1e6))
tracemem(dt)

# := 是原地修改，不复制
dt[, z := x + y]  # 不触发 tracemem
```

**Rprofmem() 追踪内存分配**：

```r
# 启动内存分配追踪
Rprofmem("memory.out", threshold = 1000)  # 只记录 > 1KB 的分配

# 运行代码
result <- some_function()

# 停止追踪
Rprofmem(NULL)

# 查看结果
readLines("memory.out", n = 20)
```

---

## 快速参考表

| 场景 | 避免 | 推荐 |
|------|------|------|
| 增长向量 | `c(vec, new)` | 预分配 / 向量化 |
| 合并 data.frame | 循环 `rbind()` | `rbindlist()` / `bind_rows()` |
| 行操作 | `apply(df, 1, ...)` | 列向量化 |
| 读写 CSV | `read.csv` / `write.csv` | `fread()` / `fwrite()` |
| 循环索引 | `1:length(x)` | `seq_along(x)` |
| 浮点比较 | `x == y` | `near(x, y)` / `all.equal()` |
| 类型稳定 | `sapply()` | `vapply()` / `lapply()` |
| 原地修改 | `df$col <- ...` | `dt[, col := ...]` |
| 函数查找 | `filter(...)` | `dplyr::filter(...)` |
| 条件分支 | 嵌套 `ifelse()` | `cut()` / `findInterval()` |
| 全局副作用 | `attach()` / `<<-` | `with()` / 显式传参 |
| 字符串拼接 | 循环 `paste0()` | `paste(collapse=)` / `sprintf()` |
| 矩阵乘法 | 手动循环 | `%*%` / `crossprod()` |
| 动态变量 | `get()` / `assign()` | 列表 / 环境 |
| future 中的包 | `library()` 在 future 内 | `%packages%` 参数 |
| 追踪复制 | 猜测 | `tracemem()` |
