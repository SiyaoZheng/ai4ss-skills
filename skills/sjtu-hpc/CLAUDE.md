# CLAUDE.md - SJTU HPC Skill 项目记忆

## 并行配置公式 (2025-01-29)

**唯一正确的公式**（数学推导，非建议）：

```
BLAS_THREADS = 2
n_workers = (available_cores - 1) // BLAS_THREADS
实际使用: min(n_workers, n_tasks)
```

### Smoking Gun 证据

1. **joblib 反超额订阅** (scikit-learn 1.5+): `threads_per_worker = cpu_count // n_workers`
2. **MICE futuremice.R:207**: `min(available - 1, m)` — 保留 1 核给系统
3. **MICE futuremice.R:214**: `min(available - 1, m, n.core)` — worker 不超过任务数
4. **Little's Law (1961)**: 超过带宽饱和点后增加 worker 无收益

### 数学证明

```
总线程 = n_workers × BLAS_THREADS
       = ((available - 1) // BLAS_THREADS) × BLAS_THREADS
       ≤ available - 1 < available
恒成立，永不超额订阅！
```

### ⚠️ 验证状态

**公式未经真实数据验证。** 模拟数据测试结果已删除（违反"不用假数据测试"原则）。

公式基于理论推导（joblib/MICE 源码），但本地实测表明：
1. 对于小任务（<100ms/任务），并行开销 > 计算收益，单线程更快
2. 需要在 HPC 上用真实长时间任务验证

### 模板位置

`scripts/templates/` 目录包含：
- `config_parallel.py` / `config_parallel.R` — 导入即用的配置
- `_targets_hpc.R` — targets 项目 HPC 模板
- `benchmark_parallel.py` / `benchmark_parallel.R` — 基准测试脚本

## 关键设计决策

1. **BLAS_THREADS = 2**：不是 1（矩阵运算需要），不是全部（避免嵌套爆炸）
2. **保留 1 核**：`available - 1`，给系统和 I/O 留空间
3. **整除取整**：`//` 保证总线程数不超过可用核数
4. **min(workers, tasks)**：worker 不应超过任务数，避免空闲进程

## ⚠️ 血泪教训 (2025-01-29)

**ProcessPoolExecutor + 大数据 = 内存爆炸**

```python
# 错误 ❌ - 每个 worker 重新加载整个数据集
df = pd.read_parquet("big_data.parquet")  # 2GB
def task(i):
    return df.sample(50000)  # 7 workers × 2GB = 14GB 内存爆炸！

# 正确 ✓ - 父进程预处理，传递小数据
df = pd.read_parquet("big_data.parquet")
chunks = [df.sample(50000) for _ in range(n_tasks)]  # 预先抽样
with ProcessPoolExecutor() as ex:
    results = ex.map(process_chunk, chunks)  # 只传 50KB/chunk
```

**原因**：macOS 的 spawn 模式下，子进程重新执行模块顶层代码，每个 worker 都会重新加载数据。
