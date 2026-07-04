# R 内部机制与性能优化

> 理解 R 的底层机制是性能优化的基础。本文档涵盖 Copy-on-Modify、向量化、内存管理、SEXP 对象结构及 ALTREP 机制。

---

## 目录

1. [Copy-on-Modify 机制](#1-copy-on-modify-机制)
   - [引用计数与 lobstr 工具](#11-引用计数与-lobstr-工具)
   - [性能陷阱：循环中的修改](#12-性能陷阱循环中的修改)
   - [tracemem() 检测复制](#13-tracemem-检测复制)
   - [避免复制的技巧](#14-避免复制的技巧)
2. [向量化原理](#2-向量化原理)
   - [为什么向量化快](#21-为什么向量化快)
   - [常用向量化函数表](#22-常用向量化函数表)
   - [apply 家族比较](#23-apply-家族比较)
   - [无法向量化的情况](#24-无法向量化的情况)
3. [内存管理与 GC](#3-内存管理与-gc)
   - [R 内存结构](#31-r-内存结构)
   - [gc() 输出解读](#32-gc-输出解读)
   - [GC 触发条件](#33-gc-触发条件)
   - [减少 GC 压力](#34-减少-gc-压力)
4. [SEXP 与 R 对象结构](#4-sexp-与-r-对象结构)
   - [SEXP 类型概览](#41-sexp-类型概览)
   - [类型转换开销](#42-类型转换开销)
   - [属性存储机制](#43-属性存储机制)
5. [ALTREP - 替代表示](#5-altrep---替代表示)
   - [什么是 ALTREP](#51-什么是-altrep)
   - [ALTREP 展开时机](#52-altrep-展开时机)
   - [如何利用 ALTREP](#53-如何利用-altrep)

---

## 1. Copy-on-Modify 机制

R 使用 **Copy-on-Modify** (CoW) 语义：对象在被修改时才会复制，而不是在赋值时。这是 R 的核心内存管理策略。

### 1.1 引用计数与 lobstr 工具

R 4.0+ 使用引用计数来追踪对象被引用的次数：

```r
library(lobstr)

# 创建向量
x <- 1:1e6
obj_addr(x)
#> [1] "0x7f8b1c000000"

# 赋值给 y - 不复制，共享内存
y <- x
obj_addr(y)
#> [1] "0x7f8b1c000000"  # 相同地址！

# 检查引用计数
ref(x)
#> [1:0x7f8b1c000000] <int>  # 引用计数 = 2
```

**引用计数规则**：

```
┌─────────────────────────────────────────────────────────────┐
│                    引用计数状态图                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ref = 1 (唯一引用)      ref = 2+ (共享引用)              │
│   ┌─────────┐             ┌─────────┐                      │
│   │    x    │             │  x   y  │                      │
│   │    │    │             │  │   │  │                      │
│   │    ▼    │             │  ▼   ▼  │                      │
│   │ [data]  │             │ [data]  │                      │
│   └─────────┘             └─────────┘                      │
│        │                       │                            │
│        ▼                       ▼                            │
│   修改时原地更新          修改时触发复制                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

```r
# 引用计数 = 1，原地修改
x <- 1:3
.Internal(inspect(x))  # 查看引用计数

x[1] <- 10L  # 不触发复制

# 引用计数 = 2，触发复制
x <- 1:3
y <- x
x[1] <- 10L  # 触发复制！

obj_addr(x)  # 新地址
obj_addr(y)  # 保持原地址
```

### 1.2 性能陷阱：循环中的修改

**最常见的性能杀手**：在循环中逐步增长对象。

```r
# ❌ 错误示范：每次迭代都复制整个向量
result <- c()
for (i in 1:1e5) {
  result <- c(result, i^2)  # O(n^2) 复杂度！
}

# 内存复制过程示意：
# 迭代1: 分配 1 个元素
# 迭代2: 复制 1 个 + 分配新 → 2 个元素
# 迭代3: 复制 2 个 + 分配新 → 3 个元素
# ...
# 迭代n: 复制 n-1 个 + 分配新 → n 个元素
# 总复制次数: 1 + 2 + 3 + ... + (n-1) = n(n-1)/2 ≈ O(n^2)
```

```r
# ✅ 正确做法：预分配
result <- numeric(1e5)
for (i in 1:1e5) {
  result[i] <- i^2  # O(n) 复杂度
}

# 或者向量化（最佳）
result <- (1:1e5)^2  # O(n)，且只有一次 C 调用
```

**性能对比**：

```r
library(bench)

# 动态增长 vs 预分配 vs 向量化
n <- 1e4
bench::mark(
  grow = {
    x <- c()
    for (i in 1:n) x <- c(x, i^2)
  },
  prealloc = {
    x <- numeric(n)
    for (i in 1:n) x[i] <- i^2
  },
  vectorized = (1:n)^2,
  check = FALSE
)
#>   expression      min   median `itr/sec` mem_alloc
#>   <bch:expr> <bch:tm> <bch:tm>     <dbl> <bch:byt>
#> 1 grow         195ms    198ms      5.06     382MB  ← 大量内存分配
#> 2 prealloc    1.23ms   1.35ms    740        78KB
#> 3 vectorized  42.6µs   45.2µs  21893        78KB  ← 最快
```

### 1.3 tracemem() 检测复制

`tracemem()` 可以追踪对象何时被复制：

```r
x <- 1:10
tracemem(x)
#> [1] "<0x7f8b1c000000>"

y <- x           # 不输出 - 没有复制
y[1] <- 100L     # 输出复制信息
#> tracemem[0x7f8b1c000000 -> 0x7f8b1c100000]:

untracemem(x)    # 停止追踪
```

**在函数中追踪**：

```r
tracemem_demo <- function(x) {
  tracemem(x)
  x[1] <- 0       # 函数参数默认 ref > 1
  x
}

v <- 1:5
tracemem_demo(v)
#> tracemem[... -> ...]: tracemem_demo
# 函数内的修改触发复制
```

**批量检测复制**：

```r
# 自定义函数检测操作是否触发复制
detect_copy <- function(expr) {
  x <- 1:1e6
  tracemem(x)

  old_addr <- lobstr::obj_addr(x)
  eval(substitute(expr))
  new_addr <- lobstr::obj_addr(x)

  untracemem(x)

  list(
    copied = old_addr != new_addr,
    old = old_addr,
    new = new_addr
  )
}

detect_copy(x[1] <- 1L)
#> $copied
#> [1] FALSE  # 唯一引用，原地修改
```

### 1.4 避免复制的技巧

#### 1.4.1 使用 data.table 的 `:=` 原地修改

```r
library(data.table)

# data.frame 修改触发复制
df <- data.frame(x = 1:1e6, y = rnorm(1e6))
tracemem(df)
df$z <- df$x + df$y  # 复制整个 data.frame！

# data.table 原地修改
dt <- data.table(x = 1:1e6, y = rnorm(1e6))
tracemem(dt)
dt[, z := x + y]     # 没有复制！使用 := 原地添加列
```

**data.table 原地操作对比**：

```r
# 常见操作的复制行为
┌────────────────────────┬─────────────┬─────────────┐
│ 操作                   │ data.frame  │ data.table  │
├────────────────────────┼─────────────┼─────────────┤
│ 添加列                 │ 复制        │ 原地 (:=)   │
│ 修改列                 │ 复制        │ 原地 (:=)   │
│ 删除列                 │ 复制        │ 原地 (:=)   │
│ 按引用排序             │ 复制        │ 原地 setorder() │
│ 设置键/索引            │ 复制        │ 原地 setkey()   │
│ 重命名列               │ 复制        │ 原地 setnames() │
└────────────────────────┴─────────────┴─────────────┘
```

#### 1.4.2 使用 environment 作为可变容器

```r
# environment 是引用语义，天然避免复制
make_accumulator <- function() {
  env <- new.env(parent = emptyenv())
  env$data <- numeric(0)

  add <- function(x) {
    env$data <- c(env$data, x)  # 仍有增长开销
  }

  get <- function() env$data

  list(add = add, get = get)
}

# 更高效：预分配 + 指针
make_buffer <- function(capacity = 1000) {
  env <- new.env(parent = emptyenv())
  env$data <- numeric(capacity)
  env$pos <- 0L

  add <- function(x) {
    if (env$pos >= length(env$data)) {
      # 容量翻倍
      env$data <- c(env$data, numeric(length(env$data)))
    }
    env$pos <- env$pos + 1L
    env$data[env$pos] <- x
  }

  get <- function() env$data[seq_len(env$pos)]

  list(add = add, get = get)
}
```

#### 1.4.3 使用 list 替代 data.frame 进行迭代构建

```r
# ❌ 逐行添加 data.frame
df <- data.frame()
for (i in 1:1000) {
  df <- rbind(df, data.frame(x = i, y = i^2))  # 每次复制
}

# ✅ 先用 list 收集，最后合并
results <- vector("list", 1000)
for (i in 1:1000) {
  results[[i]] <- data.frame(x = i, y = i^2)
}
df <- do.call(rbind, results)

# ✅✅ 更好：用 data.table::rbindlist
df <- data.table::rbindlist(results)
```

#### 1.4.4 Rcpp 完全控制内存

```cpp
// [[Rcpp::export]]
NumericVector cumsum_inplace(NumericVector x) {
  // 原地累加，不创建新对象
  for (int i = 1; i < x.size(); i++) {
    x[i] += x[i-1];
  }
  return x;  // 返回修改后的同一对象
}
```

---

## 2. 向量化原理

### 2.1 为什么向量化快

向量化的核心优势在于 **减少 R 解释器开销**。

```
┌─────────────────────────────────────────────────────────────┐
│               循环 vs 向量化执行流程                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  for 循环 (n=1000):                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │ R解释器 → C代码 → 返回R → R解释器 → C代码 → ...    │    │
│  │    ↑________________________________________↓       │    │
│  │              重复 1000 次                          │    │
│  └────────────────────────────────────────────────────┘    │
│  开销 = 1000 × (函数调用 + 类型检查 + 内存分配)            │
│                                                             │
│  向量化 (n=1000):                                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │ R解释器 → C循环处理全部1000个元素 → 返回R          │    │
│  └────────────────────────────────────────────────────┘    │
│  开销 = 1 × (函数调用 + 类型检查 + 内存分配)               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**R 解释器的开销**：

1. **函数查找**：每次调用都要在环境链中查找函数
2. **参数匹配**：解析参数名、默认值
3. **类型检查**：验证输入类型
4. **内存分配**：为临时结果分配内存
5. **垃圾回收**：触发 GC 检查

```r
# 对比示例
x <- rnorm(1e6)

# 循环：100万次 R 解释器调用
system.time({
  result <- numeric(length(x))
  for (i in seq_along(x)) {
    result[i] <- x[i]^2
  }
})
#>    user  system elapsed
#>   0.45    0.01    0.46

# 向量化：1 次 R 解释器调用
system.time({
  result <- x^2
})
#>    user  system elapsed
#>   0.01    0.00    0.01

# 速度差异: ~45倍
```

### 2.2 常用向量化函数表

| 循环操作 | 向量化替代 | 说明 |
|---------|-----------|------|
| `for (i in 1:n) sum <- sum + x[i]` | `sum(x)` | 求和 |
| `for (i in 1:n) if (x[i] > 0) count <- count + 1` | `sum(x > 0)` | 条件计数 |
| `for (i in 1:n) result[i] <- if (x[i] > 0) "pos" else "neg"` | `ifelse(x > 0, "pos", "neg")` | 条件选择 |
| `for (i in 1:n) result[i] <- x[i] + y[i]` | `x + y` | 元素相加 |
| `for (i in 2:n) result[i] <- x[i] - x[i-1]` | `diff(x)` | 差分 |
| `for (i in 1:n) result[i] <- sum(x[1:i])` | `cumsum(x)` | 累加 |
| `for (i in 1:n) result[i] <- max(x[1:i])` | `cummax(x)` | 累计最大值 |
| `for (i in 1:n) result[i] <- paste0("item_", i)` | `paste0("item_", 1:n)` | 字符串拼接 |
| 逐行/列操作 | `rowSums()`, `colMeans()` 等 | 矩阵操作 |
| 分组计算 | `tapply()`, `aggregate()`, `dplyr::group_by()` | 分组统计 |
| 滑动窗口 | `zoo::rollmean()`, `data.table::frollmean()` | 移动平均 |

**矩阵专用向量化函数**：

```r
# 行/列操作
rowSums(m)     # 行求和
colMeans(m)   # 列均值
rowMaxs(m)    # matrixStats 包

# 矩阵运算
m %*% n       # 矩阵乘法（调用 BLAS）
crossprod(m)  # t(m) %*% m，更高效
tcrossprod(m) # m %*% t(m)

# 外积
outer(x, y, FUN = "*")  # 生成 length(x) × length(y) 矩阵
```

### 2.3 apply 家族比较

```
┌─────────────────────────────────────────────────────────────┐
│                   apply 家族速度排名                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  最快 ────────────────────────────────────────────── 最慢  │
│                                                             │
│  vapply > lapply > sapply > mapply > apply > tapply        │
│                                                             │
│  ┌──────────┬─────────────────────────────────────────┐    │
│  │ vapply   │ 预先指定返回类型，无需推断             │    │
│  ├──────────┼─────────────────────────────────────────┤    │
│  │ lapply   │ 总返回 list，无类型转换开销            │    │
│  ├──────────┼─────────────────────────────────────────┤    │
│  │ sapply   │ 需要推断返回类型并简化                 │    │
│  ├──────────┼─────────────────────────────────────────┤    │
│  │ mapply   │ 多参数匹配开销                         │    │
│  ├──────────┼─────────────────────────────────────────┤    │
│  │ apply    │ 需要转换为矩阵 + 类型推断              │    │
│  ├──────────┼─────────────────────────────────────────┤    │
│  │ tapply   │ 分组开销 + 类型推断                    │    │
│  └──────────┴─────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**代码示例**：

```r
x <- as.list(1:1e5)

# sapply - 需要推断返回类型
system.time(sapply(x, function(i) i^2))
#>    user  system elapsed
#>   0.12    0.00    0.12

# vapply - 预先指定类型，更快
system.time(vapply(x, function(i) i^2, numeric(1)))
#>    user  system elapsed
#>   0.09    0.00    0.09

# lapply - 返回 list，最快
system.time(lapply(x, function(i) i^2))
#>    user  system elapsed
#>   0.08    0.00    0.08
```

**apply 家族选择指南**：

```r
# lapply: 输入 list/vector，返回 list
lapply(1:3, function(x) x^2)
#> [[1]] 1
#> [[2]] 4
#> [[3]] 9

# sapply: 同 lapply，但尝试简化为 vector/matrix
sapply(1:3, function(x) x^2)
#> [1] 1 4 9

# vapply: 同 sapply，但必须指定返回类型（推荐！）
vapply(1:3, function(x) x^2, numeric(1))
#> [1] 1 4 9

# Map: 并行迭代多个参数（返回 list）
Map(function(x, y) x + y, 1:3, 4:6)
#> [[1]] 5
#> [[2]] 7
#> [[3]] 9

# mapply: 同 Map，但尝试简化
mapply(function(x, y) x + y, 1:3, 4:6)
#> [1] 5 7 9

# apply: 对矩阵的行(1)或列(2)应用函数
apply(matrix(1:6, 2, 3), 1, sum)  # 行求和
#> [1]  9 12
```

**重要提示**：`apply` 家族 **不是真正的向量化**！它们只是隐藏了循环，底层仍是 R 解释器循环。

```r
# apply 并不比显式循环快多少
m <- matrix(rnorm(1e6), 1000, 1000)

# apply
system.time(apply(m, 1, sum))
#>    user  system elapsed
#>   0.08    0.00    0.08

# 显式循环
system.time({
  result <- numeric(1000)
  for (i in 1:1000) result[i] <- sum(m[i, ])
})
#>    user  system elapsed
#>   0.07    0.00    0.07

# 真正的向量化
system.time(rowSums(m))
#>    user  system elapsed
#>   0.01    0.00    0.01  # 快 8 倍
```

### 2.4 无法向量化的情况

某些操作由于 **状态依赖** 无法向量化：

```r
# 情况1: 当前值依赖于前一个计算结果
# 斐波那契数列
fib <- function(n) {
  result <- numeric(n)
  result[1:2] <- 1
  for (i in 3:n) {
    result[i] <- result[i-1] + result[i-2]  # 依赖前两个结果
  }
  result
}

# 情况2: 条件分支依赖运行时状态
# 累积求和直到超过阈值
cumsum_until <- function(x, threshold) {
  total <- 0
  for (i in seq_along(x)) {
    total <- total + x[i]
    if (total > threshold) return(i)
  }
  length(x)
}

# 情况3: 递归关系
# AR(1) 过程: y[t] = phi * y[t-1] + e[t]
ar1_sim <- function(n, phi, sigma) {
  y <- numeric(n)
  e <- rnorm(n, sd = sigma)
  y[1] <- e[1]
  for (t in 2:n) {
    y[t] <- phi * y[t-1] + e[t]
  }
  y
}
```

**解决方案**：

1. **Rcpp**：用 C++ 写循环
2. **filter()**：某些递归可用 `stats::filter()` 处理
3. **Reduce()**：某些累积操作可用

```r
# 使用 filter() 实现 AR(1)
ar1_filter <- function(n, phi, sigma) {
  e <- rnorm(n, sd = sigma)
  as.numeric(filter(e, phi, method = "recursive"))
}

# 使用 Reduce 实现累积操作
# 累积乘积（等同于 cumprod）
Reduce(`*`, 1:5, accumulate = TRUE)
#> [1]   1   2   6  24 120
```

---

## 3. 内存管理与 GC

### 3.1 R 内存结构

R 使用两种内存池：

```
┌─────────────────────────────────────────────────────────────┐
│                    R 内存结构                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Heap Memory                        │  │
│  │  ┌────────────────────┐  ┌────────────────────────┐  │  │
│  │  │     Ncells         │  │       Vcells           │  │  │
│  │  │  (Node cells)      │  │   (Vector cells)       │  │  │
│  │  ├────────────────────┤  ├────────────────────────┤  │  │
│  │  │ • SEXP 头部信息    │  │ • 实际数据存储         │  │  │
│  │  │ • 固定大小(56字节) │  │ • 可变大小             │  │  │
│  │  │ • 类型/引用计数    │  │ • 数值向量             │  │  │
│  │  │ • 属性指针         │  │ • 字符串内容           │  │  │
│  │  │ • 数据指针         │  │ • 列表元素             │  │  │
│  │  └────────────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  内存计算公式:                                               │
│  Ncells: 每个对象 56 bytes                                  │
│  Vcells: 每 8 bytes = 1 Vcell                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**对象内存占用估算**：

```r
library(lobstr)

# 基本类型
obj_size(1L)           # integer: 56 bytes (头) + 8 bytes (数据) = 64 bytes
obj_size(1.0)          # double: 同上
obj_size("a")          # character: 56 + 8 + 字符串池

# 向量
obj_size(integer(0))   # 空向量: 56 bytes（仅头部）
obj_size(1:100)        # ALTREP: 680 bytes（紧凑表示）
obj_size(as.integer(1:100))  # 普通: 456 bytes

# 近似公式（非 ALTREP）
# numeric vector: 40 + 8*n bytes
# integer vector: 40 + 4*n bytes
# character vector: 40 + 8*n + 每个字符串的大小
```

**向量分配类（gccls 字段）**：

| 类 | 数据大小 | 分配方式 |
|----|---------|---------|
| 0 | 非向量节点 | 节点池 |
| 1 | <= 8 字节 | 小向量池（~2000 字节页面） |
| 2 | <= 16 字节 | 小向量池 |
| 3 | <= 32 字节 | 小向量池 |
| 4 | <= 64 字节 | 小向量池 |
| 5 | <= 128 字节 | 小向量池 |
| 6 | 自定义分配器 | 不计入 GC 统计 |
| 7 | > 128 字节 | malloc 单独分配 |

**性能含义**：小向量（<= 128 字节，约 16 个 double 或 32 个 int）从预分配页面分配，速度快；大向量需要调用系统 malloc，有额外开销。

### 3.2 gc() 输出解读

```r
gc()
#>           used  (Mb) gc trigger  (Mb) max used  (Mb)
#> Ncells  500000  26.8    1000000  53.4   750000  40.1
#> Vcells 1000000   7.7    2000000  15.3  1500000  11.5
```

**字段含义**：

| 字段 | 含义 |
|------|------|
| `used` | 当前正在使用的 cells 数量 |
| `(Mb)` | 对应的内存大小（MB） |
| `gc trigger` | 触发下次 GC 的阈值 |
| `max used` | 会话期间的峰值使用量 |

```r
# 重置最大值统计
gc(reset = TRUE)

# 强制完整 GC（两代）
gc(full = TRUE)

# 详细输出
gc(verbose = TRUE)
#> Garbage collection 12 = 8+2+2 (level 2) ...
#> 23.5 Mbytes of cons cells used (47%)
#> 15.2 Mbytes of vectors used (38%)
```

### 3.3 GC 触发条件

```
┌─────────────────────────────────────────────────────────────┐
│                    GC 触发时机                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 自动触发:                                               │
│     • Vcells 使用量超过 gc trigger                          │
│     • Ncells 使用量超过 gc trigger                          │
│     • 内存分配失败时                                        │
│                                                             │
│  2. 显式调用:                                               │
│     • gc()                                                  │
│     • R 启动时的 --min-vsize, --min-nsize 参数             │
│                                                             │
│  3. 三代垃圾回收:                                           │
│     • Level 0: 只收集最年轻的代（每 20 次后升级到 Level 1） │
│     • Level 1: 收集两个年轻代（每 5 次后升级到 Level 2）    │
│     • Level 2: 完整 GC，收集所有代（gc() 调用或内存不足）   │
│     • 若 level-n 回收后空闲空间 < 20%，下次升级到 level-n+1 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**监控 GC 活动**：

```r
# 开启 GC 信息输出
gcinfo(TRUE)

x <- rnorm(1e7)  # 可能触发 GC 消息
#> Garbage collection 15 = 10+3+2 (level 1) ...

gcinfo(FALSE)  # 关闭

# 测量包含 GC 的总时间
system.time(gc())  # GC 本身的开销
```

### 3.4 减少 GC 压力

#### 3.4.1 预分配

```r
# ❌ 动态增长触发频繁 GC
grow_vector <- function(n) {
  x <- c()
  for (i in 1:n) {
    x <- c(x, rnorm(1))  # 每次分配新内存
  }
  x
}

# ✅ 预分配避免 GC
prealloc_vector <- function(n) {
  x <- numeric(n)
  for (i in 1:n) {
    x[i] <- rnorm(1)
  }
  x
}

# 比较 GC 次数
gc.before <- gc(reset = TRUE)
result1 <- grow_vector(1e4)
gc.after1 <- gc()

gc.before <- gc(reset = TRUE)
result2 <- prealloc_vector(1e4)
gc.after2 <- gc()

# grow_vector 可能触发数百次 GC
# prealloc_vector 可能只触发几次
```

#### 3.4.2 及时删除大对象

```r
process_large_data <- function(file) {
  # 读取大文件
  raw_data <- read.csv(file)  # 假设 1GB

  # 处理
  processed <- transform(raw_data)

  # 立即删除不需要的大对象
  rm(raw_data)
  gc()  # 释放内存

  # 继续后续处理
  final_result <- analyze(processed)

  final_result
}
```

#### 3.4.3 分块处理

```r
# 处理超大文件时分块读取
process_large_csv <- function(file, chunk_size = 1e5) {
  # 使用 data.table::fread 的 skip + nrows
  total_rows <- as.numeric(system(paste("wc -l <", file), intern = TRUE))

  results <- vector("list", ceiling(total_rows / chunk_size))

  for (i in seq_along(results)) {
    skip <- (i - 1) * chunk_size
    chunk <- data.table::fread(
      file,
      skip = skip,
      nrows = chunk_size,
      header = (i == 1)
    )

    results[[i]] <- process_chunk(chunk)

    rm(chunk)
    if (i %% 10 == 0) gc()  # 每10个块 GC 一次
  }

  data.table::rbindlist(results)
}
```

#### 3.4.4 避免创建不必要的中间对象

```r
# ❌ 创建多个中间对象
result <- df
result <- subset(result, x > 0)
result <- transform(result, y = y^2)
result <- result[order(result$y), ]

# ✅ 使用管道或链式操作
library(data.table)
result <- df[x > 0][, y := y^2][order(y)]

# 或使用 magrittr 管道（但仍有中间对象）
library(dplyr)
result <- df %>%
  filter(x > 0) %>%
  mutate(y = y^2) %>%
  arrange(y)
```

---

## 4. SEXP 与 R 对象结构

### 4.1 SEXP 类型概览

SEXP (S-expression pointer) 是 R 内部所有对象的基础类型。

```
┌─────────────────────────────────────────────────────────────┐
│                    SEXP 结构 (Rinternals.h)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  struct SEXPREC {                                           │
│    SEXPTYPE type;      // 对象类型 (5 bits)                 │
│    unsigned int obj;   // 是否有 class 属性                 │
│    unsigned int named; // 引用计数 (2 bits, 已弃用)         │
│    unsigned int gp;    // general purpose bits              │
│    unsigned int mark;  // GC 标记                           │
│    unsigned int debug; // 调试标记                          │
│    unsigned int trace; // trace 标记                        │
│    unsigned int spare; // 保留                              │
│    struct sxpinfo_struct *sxpinfo;                          │
│    struct SEXPREC *attrib;  // 属性列表                     │
│    struct SEXPREC *gengc_next_node; // GC 链表              │
│    struct SEXPREC *gengc_prev_node;                         │
│  };                                                         │
│                                                             │
│  union {                                                    │
│    ... // 类型特定的数据                                    │
│  };                                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**常见 SEXP 类型**：

```r
# 使用 typeof() 查看类型
typeof(1L)         # "integer" -> INTSXP
typeof(1.0)        # "double"  -> REALSXP
typeof("a")        # "character" -> STRSXP
typeof(TRUE)       # "logical" -> LGLSXP
typeof(list())     # "list"    -> VECSXP
typeof(NULL)       # "NULL"    -> NILSXP
typeof(function(){}) # "closure" -> CLOSXP
typeof(environment()) # "environment" -> ENVSXP
typeof(1:10)       # "integer" -> INTSXP (可能是 ALTREP)
```

| SEXPTYPE | 编号 | R typeof() | 描述 |
|----------|------|------------|------|
| NILSXP | 0 | NULL | 空对象，只有一个实例 R_NilValue |
| SYMSXP | 1 | symbol | 符号（变量名、函数名） |
| LISTSXP | 2 | pairlist | 成对列表，用于参数列表等 |
| CLOSXP | 3 | closure | 用户定义的函数 |
| ENVSXP | 4 | environment | 环境 |
| PROMSXP | 5 | promise | 承诺（惰性求值的参数） |
| LANGSXP | 6 | language | 语言对象（函数调用、公式） |
| SPECIALSXP | 7 | special | 特殊函数（if, for, function 等） |
| BUILTINSXP | 8 | builtin | 内置函数（+, sum, sqrt 等） |
| CHARSXP | 9 | - | 内部字符串（不直接暴露给用户） |
| LGLSXP | 10 | logical | 逻辑向量 |
| *(11-12 已废弃)* | | | *曾用于内部 factor，已移除* |
| INTSXP | 13 | integer | 整数向量 |
| REALSXP | 14 | double | 实数（双精度）向量 |
| CPLXSXP | 15 | complex | 复数向量 |
| STRSXP | 16 | character | 字符向量（元素指向 CHARSXP） |
| DOTSXP | 17 | ... | 点点点参数对象 |
| ANYSXP | 18 | any | 占位符类型（无实际对象） |
| VECSXP | 19 | list | 列表（通用向量） |
| EXPRSXP | 20 | expression | 表达式向量 |
| BCODESXP | 21 | bytecode | 字节码（编译后的函数） |
| EXTPTRSXP | 22 | externalptr | 外部指针（C 级别指针） |
| WEAKREFSXP | 23 | weakref | 弱引用 |
| RAWSXP | 24 | raw | 原始字节向量 |
| OBJSXP | 25 | S4 | S4 对象（非简单类型的对象） |

### 4.2 类型转换开销

类型转换会创建新对象，有内存和性能开销：

```r
library(bench)

x <- 1:1e6  # integer

# 类型转换开销测试
bench::mark(
  as_double = as.double(x),
  as_char = as.character(x),
  check = FALSE
)
#>   expression      min   median mem_alloc
#>   <bch:expr> <bch:tm> <bch:tm> <bch:byt>
#> 1 as_double    3.5ms    4.2ms    7.63MB  # double 占 8 bytes/元素
#> 2 as_char     89.2ms   92.5ms   64.5MB   # 字符串更大
```

**类型转换成本排名**（从低到高）：

```
┌─────────────────────────────────────────────────────────────┐
│                 类型转换成本                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  低成本                                                     │
│  ├── integer → double (位扩展)                              │
│  ├── logical → integer (0/1)                                │
│  ├── logical → double (0.0/1.0)                             │
│                                                             │
│  中等成本                                                   │
│  ├── double → integer (截断)                                │
│  ├── integer → logical (0 → FALSE, 其他 → TRUE)            │
│  ├── numeric → complex                                      │
│                                                             │
│  高成本                                                     │
│  ├── numeric → character (sprintf 格式化)                   │
│  ├── character → numeric (解析)                             │
│  ├── character → factor (构建层级)                          │
│  └── factor → character (查表)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**避免隐式类型转换**：

```r
# ❌ 混合类型导致隐式转换
x <- c(1L, 2.5, "3")  # 全部转为 character
typeof(x)  # "character"

# ❌ 逻辑操作中的类型提升
sum(c(TRUE, FALSE, TRUE))  # logical → integer: 2

# ✅ 显式控制类型
x <- c(1L, 2L, 3L)  # 保持 integer
y <- as.integer(c(TRUE, FALSE, TRUE))  # 明确转换
```

### 4.3 属性存储机制

R 对象的属性存储在 `attrib` 链表中：

```
┌─────────────────────────────────────────────────────────────┐
│                    属性存储结构                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SEXP object                                                │
│  ├── sxpinfo (类型、引用计数等)                             │
│  ├── data (实际数据)                                        │
│  └── attrib ──→ LISTSXP (pairlist)                         │
│                  ├── TAG: "names"  VALUE: ["a","b","c"]    │
│                  ├── TAG: "class"  VALUE: ["data.frame"]   │
│                  ├── TAG: "row.names" VALUE: [1,2,3]       │
│                  └── TAG: "dim"    VALUE: [2,3]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**属性操作**：

```r
x <- 1:6
dim(x) <- c(2, 3)  # 添加 dim 属性，变成矩阵
attributes(x)
#> $dim
#> [1] 2 3

# 查看所有属性
attributes(iris)
#> $names
#> [1] "Sepal.Length" "Sepal.Width" ...
#> $class
#> [1] "data.frame"
#> $row.names
#>  [1]  1  2  3 ...

# 属性访问开销
library(bench)
x <- setNames(1:1e6, paste0("v", 1:1e6))
bench::mark(
  bracket = x["v500000"],
  match = x[match("v500000", names(x))],
  which = x[which(names(x) == "v500000")]
)
# 命名访问有查找开销
```

**属性对性能的影响**：

```r
# 属性会被复制
x <- 1:1e6
attr(x, "custom") <- "some metadata"

tracemem(x)
y <- x        # 不复制
y[1] <- 0L    # 复制时也复制属性

# 矩阵 vs 向量的开销
m <- matrix(1:1e6, 1000, 1000)
v <- 1:1e6

bench::mark(
  matrix_sum = sum(m),
  vector_sum = sum(v)
)
# 几乎相同 - sum() 忽略 dim 属性
```

---

## 5. ALTREP - 替代表示

### 5.1 什么是 ALTREP

**ALTREP** (Alternative Representation) 是 R 3.5+ 引入的机制，允许用紧凑方式表示某些对象。

```
┌─────────────────────────────────────────────────────────────┐
│                    ALTREP 机制                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  传统表示 (1:1000000):                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [1, 2, 3, 4, 5, ..., 999998, 999999, 1000000]       │   │
│  │ 存储: 4 MB (100万个 4-byte 整数)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ALTREP 表示 (1:1000000):                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ type: compact_intseq                                │   │
│  │ start: 1                                            │   │
│  │ length: 1000000                                     │   │
│  │ step: 1                                             │   │
│  │ 存储: ~56 bytes (仅元数据)                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**R 内置的 ALTREP 类型**：

| 类型 | 描述 | 示例 |
|------|------|------|
| compact_intseq | 紧凑整数序列 | `1:1000000` |
| compact_realseq | 紧凑实数序列 | `seq(0, 1, by=0.001)` |
| deferred_string | 延迟字符串转换 | `as.character(1:1000)` |
| wrapper | 向量包装器，附加元数据 | 记录 is_sorted、no_na 等信息 |
| mmap | 内存映射文件 | 某些包实现（如 simplemmap） |

**Wrapper 对象的作用**：
- 可以记录向量的元数据（如是否已排序、是否有 NA）
- 允许修改属性而不复制底层数据
- `shallow_duplicate` 会标记 payload 为不可变，请求可写指针时才复制

```r
# 检查是否是 ALTREP
.Internal(inspect(1:10))
#> @0x... 13 INTSXP g0c0 [MARK,REF(65535)] 1 : 10 (compact)
#                                                    ^^^^^^^ ALTREP 标记

.Internal(inspect(c(1L, 2L, 3L)))
#> @0x... 13 INTSXP g0c2 [REF(1)] (len=3, tl=0) 1,2,3
#                                               没有 compact 标记
```

### 5.2 ALTREP 展开时机

ALTREP 在需要访问实际数据时会 **展开** (materialize) 为普通向量：

```r
# ALTREP 保持紧凑的操作
x <- 1:1e8
length(x)      # O(1)，不展开
x[1]           # O(1)，元素访问不展开
x[1e8]         # O(1)
sum(x)         # O(1)，有专门的求和方法！
min(x); max(x) # O(1)

# 验证 sum 的 O(1) 特性
bench::mark(
  sum_small = sum(1:100),
  sum_large = sum(1:1e8),
  check = FALSE
)
#>   expression      min   median
#> 1 sum_small    180ns    220ns
#> 2 sum_large    180ns    220ns   # 几乎相同！
```

**触发展开的操作**：

```r
x <- 1:1e6

# 修改 - 立即展开
tracemem(x)
x[1] <- 0L  # 展开 + 修改
#> tracemem[... -> ...]:

# 子集（非连续）
y <- x[c(1, 3, 5)]  # 创建新向量

# 某些函数不支持 ALTREP
sort(x)  # 需要完整数据（但排序后的序列可能仍是 ALTREP）

# 传递给 C 代码
.C("some_function", as.integer(x))  # 必须展开
```

**内存差异演示**：

```r
library(lobstr)

# ALTREP 序列
obj_size(1:1e8)
#> 680 B

# 强制展开
obj_size(c(1:1e8))  # c() 会展开
#> 400,000,048 B (400 MB)

# 或
x <- 1:1e8
x[1] <- 1L  # 修改触发展开
obj_size(x)
#> 400,000,048 B
```

### 5.3 如何利用 ALTREP

#### 5.3.1 使用 `:` 创建序列

```r
# ✅ 使用 : 或 seq()
x <- 1:1e8         # ALTREP，680 bytes
y <- seq_len(1e8)  # ALTREP，680 bytes
z <- seq.int(1, 1e8)  # ALTREP

# ❌ 避免 c() 包装
x <- c(1:1e8)      # 展开为 400 MB！

# ❌ 避免不必要的操作
x <- as.integer(1:1e8)  # 可能展开
```

#### 5.3.2 延迟字符串转换

```r
# R 4.0+ 的延迟字符串
x <- 1:1e6
y <- as.character(x)  # 延迟转换（deferred_string）

# 只有访问时才转换
y[1]  # 此时才计算 "1"

# 检查
.Internal(inspect(as.character(1:100)))
#> ... (deferred string conversion) ...
```

#### 5.3.3 利用 ALTREP 感知的函数

```r
# 这些函数对 ALTREP 有优化
sum(1:1e9)     # 使用公式 n*(n+1)/2，O(1)
min(1:1e9)     # 直接返回 1
max(1:1e9)     # 直接返回 1e9
mean(1:1e9)    # 使用公式 (n+1)/2
length(1:1e9)  # O(1)

# 比较非 ALTREP
x <- sample(1e6)
sum(x)         # 需要遍历，O(n)
```

#### 5.3.4 自定义 ALTREP（高级）

通过 Rcpp 可以创建自定义 ALTREP 类：

```cpp
// 示例：创建一个常数向量的 ALTREP
#include <Rcpp.h>
#include <R_ext/Altrep.h>

// ALTREP 方法...
// 这需要较深的 R 内部知识
```

**实际应用场景**：

- `bigstatsr`：使用 ALTREP 处理超大矩阵
- `vroom`：延迟读取 CSV 文件
- `arrow`：Apache Arrow 数据的 ALTREP 表示

```r
# vroom 的 ALTREP 示例
library(vroom)
# vroom 使用 ALTREP 实现延迟解析
df <- vroom("huge_file.csv")  # 快速"读取"
# 数据在访问时才真正解析
df$column1[1]  # 此时才解析第一行
```

---

## 总结：性能优化检查清单

```
┌─────────────────────────────────────────────────────────────┐
│                    性能优化检查清单                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  □ Copy-on-Modify                                           │
│    ├── 是否在循环中增长对象？→ 预分配                       │
│    ├── 是否有不必要的变量复制？→ 检查引用计数               │
│    └── 是否可以用 data.table := 原地修改？                  │
│                                                             │
│  □ 向量化                                                   │
│    ├── 是否有可向量化的循环？→ 使用向量函数                 │
│    ├── 是否用了 apply 以为更快？→ 检查是否有专门函数        │
│    └── 状态依赖无法向量化？→ 考虑 Rcpp                      │
│                                                             │
│  □ 内存管理                                                 │
│    ├── 大对象是否及时删除？→ rm() + gc()                    │
│    ├── 是否创建过多中间对象？→ 管道或原地操作               │
│    └── 数据是否需要分块处理？→ 迭代器模式                   │
│                                                             │
│  □ 类型                                                     │
│    ├── 是否有不必要的类型转换？→ 保持类型一致               │
│    ├── 数值计算是否用了 character？→ 使用 numeric           │
│    └── 是否了解对象的真实结构？→ typeof(), class()          │
│                                                             │
│  □ ALTREP                                                   │
│    ├── 序列是否用 : 创建？→ 避免 c() 包装                   │
│    ├── 是否触发了不必要的展开？→ 检查 inspect()             │
│    └── 是否利用了 ALTREP 感知函数？→ sum/min/max/length     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 参考资料

- [R Internals](https://cran.r-project.org/doc/manuals/r-release/R-ints.html) - 官方内部文档
- [Advanced R (2nd ed.) - Hadley Wickham](https://adv-r.hadley.nz/) - 第 2、23、24、25 章
- [R's ALTREP](https://svn.r-project.org/R/branches/ALTREP/ALTREP.html) - ALTREP 设计文档
- [lobstr package](https://lobstr.r-lib.org/) - 内存和对象检查工具
- [Writing R Extensions](https://cran.r-project.org/doc/manuals/r-release/R-exts.html) - 第 5 章 System and foreign language interfaces
