# 并行配置公式 | Parallel Configuration

**唯一正确的公式**（数学推导，非建议）：

```
BLAS_THREADS = 2
n_workers = (available_cores - 1) // BLAS_THREADS
实际使用: min(n_workers, n_tasks)
```

## Smoking Gun 证据

| 证据 | 来源 | 关键点 |
|------|------|--------|
| joblib 反超额订阅 | scikit-learn 1.5+ 生产代码 | `threads_per_worker = cpu_count // n_workers` |
| MICE 保留核心 | futuremice.R:207 | `min(available - 1, m)` |
| MICE 不超任务 | futuremice.R:214 | `min(available - 1, m, n.core)` |
| Little's Law | 1961 年数学定理 | 超过带宽饱和点后增加 worker 无收益 |

## 数学证明

```
总线程 = n_workers × BLAS_THREADS
       = ((available - 1) // BLAS_THREADS) × BLAS_THREADS
       ≤ available - 1 < available
恒成立，永不超额订阅！
```

## 数值表（直接查表，无需计算）

| 机器核数 | BLAS线程 | Workers | 总线程 | 验证 |
|----------|----------|---------|--------|------|
| 4 核 | 2 | 1 | 2 | ≤4 ✓ |
| 8 核 | 2 | 3 | 6 | ≤8 ✓ |
| 16 核 | 2 | 7 | 14 | ≤16 ✓ |
| 64 核 (HPC) | 2 | 31 | 62 | ≤64 ✓ |

## 使用模板

位于 `scripts/templates/`:

| 文件 | 用途 |
|------|------|
| `config_parallel.py` | Python 并行配置（导入即用） |
| `config_parallel.R` | R 并行配置（source 即用） |
| `_targets_hpc.R` | targets 项目 HPC 模板 |

### Python 使用示例

```python
# 在 import numpy 之前！
from config_parallel import get_workers, N_WORKERS

from concurrent.futures import ProcessPoolExecutor
n_workers = get_workers(n_tasks=20)
with ProcessPoolExecutor(max_workers=n_workers) as executor:
    results = list(executor.map(process_item, items))
```

### R 使用示例

```r
source("config_parallel.R")
library(future)
plan(multisession, workers = get_workers(m))  # m = imputation 数量
```
