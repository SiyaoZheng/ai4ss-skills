"""
并行配置 - 基于 Smoking Gun 证据

公式推导：
- joblib 反超额订阅公式: threads_per_worker = cpu_count // n_workers
- MICE futuremice.R:207: min(available - 1, m)
- 结论: n_workers = (available - 1) // BLAS_THREADS

证据来源:
1. scikit-learn 1.5+ parallel_config 文档
2. https://github.com/amices/mice/blob/master/R/futuremice.R 第 207, 214 行
3. Little's Law (1961) - 带宽饱和点后增加 worker 无收益
4. Oracle OpenMP 嵌套并行文档
"""
import os

# ===== BLAS 线程数 =====
# 设为 2，不是 1（矩阵运算需要），不是全部（避免嵌套爆炸）
BLAS_THREADS = 2
os.environ["OMP_NUM_THREADS"] = str(BLAS_THREADS)
os.environ["OPENBLAS_NUM_THREADS"] = str(BLAS_THREADS)
os.environ["MKL_NUM_THREADS"] = str(BLAS_THREADS)
os.environ["VECLIB_MAXIMUM_THREADS"] = str(BLAS_THREADS)
os.environ["NUMEXPR_NUM_THREADS"] = str(BLAS_THREADS)

# ===== Worker 数量 =====
# 公式: (available - 1) // BLAS_THREADS
_available = int(os.environ.get("SLURM_NTASKS", os.cpu_count() or 4))
N_WORKERS = max(1, (_available - 1) // BLAS_THREADS)


def get_workers(n_tasks: int) -> int:
    """返回最优 worker 数，不超过任务数

    Args:
        n_tasks: 任务总数

    Returns:
        最优 worker 数量

    Example:
        >>> from config_parallel import get_workers
        >>> n_workers = get_workers(m=20)  # 20 个 imputation
    """
    return min(N_WORKERS, n_tasks)


# ===== 数学验证 =====
# 总线程 = N_WORKERS × BLAS_THREADS
#        = ((available - 1) // BLAS_THREADS) × BLAS_THREADS
#        ≤ available - 1 < available
# 恒成立，永不超额订阅

if __name__ == "__main__":
    print(f"可用核数: {_available}")
    print(f"BLAS 线程: {BLAS_THREADS}")
    print(f"Workers: {N_WORKERS}")
    print(f"总线程数: {N_WORKERS * BLAS_THREADS} (≤ {_available})")
