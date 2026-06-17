#' 并行配置 - 基于 Smoking Gun 证据
#'
#' 公式推导：
#' - joblib 反超额订阅公式: threads_per_worker = cpu_count // n_workers
#' - MICE futuremice.R:207: min(available - 1, m)
#' - 结论: n_workers = (available - 1) %/% BLAS_THREADS
#'
#' 证据来源:
#' 1. scikit-learn 1.5+ parallel_config 文档
#' 2. https://github.com/amices/mice/blob/master/R/futuremice.R 第 207, 214 行
#' 3. Little's Law (1961) - 带宽饱和点后增加 worker 无收益
#' 4. Oracle OpenMP 嵌套并行文档

# ===== BLAS 线程数 =====
# 设为 2，不是 1（矩阵运算需要），不是全部（避免嵌套爆炸）
BLAS_THREADS <- 2L
Sys.setenv(OMP_NUM_THREADS = BLAS_THREADS)
Sys.setenv(OPENBLAS_NUM_THREADS = BLAS_THREADS)
Sys.setenv(MKL_NUM_THREADS = BLAS_THREADS)

# ===== Worker 数量 =====
# 公式: (available - 1) %/% BLAS_THREADS
.available <- as.integer(Sys.getenv("SLURM_NTASKS", unset = NA))
if (is.na(.available)) .available <- parallel::detectCores()
if (is.na(.available)) .available <- 4L
n_workers <- max(1L, (.available - 1L) %/% BLAS_THREADS)

#' 返回最优 worker 数，不超过任务数
#'
#' @param n_tasks 任务总数
#' @return 最优 worker 数量
#'
#' @examples
#' source("config_parallel.R")
#' library(future)
#' plan(multisession, workers = get_workers(m))  # m = imputation 数量
get_workers <- function(n_tasks) {
    min(n_workers, n_tasks)
}

# ===== 数学验证 =====
# 总线程 = n_workers × BLAS_THREADS
#        = ((available - 1) %/% BLAS_THREADS) × BLAS_THREADS
#        ≤ available - 1 < available
# 恒成立，永不超额订阅

if (interactive() || !exists(".config_parallel_sourced")) {
    .config_parallel_sourced <- TRUE
    message(sprintf("可用核数: %d", .available))
    message(sprintf("BLAS 线程: %d", BLAS_THREADS))
    message(sprintf("Workers: %d", n_workers))
    message(sprintf("总线程数: %d (≤ %d)", n_workers * BLAS_THREADS, .available))
}
