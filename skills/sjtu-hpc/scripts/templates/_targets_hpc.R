# _targets.R 模板 - 基于 Smoking Gun 公式
#
# 公式: n_workers = (available - 1) %/% BLAS_THREADS
# BLAS_THREADS = 2
#
# 证据来源:
# 1. joblib 反超额订阅公式
# 2. MICE futuremice.R:207
# 3. Little's Law

library(targets)
library(tarchetypes)
library(crew)

# ===== 统一配置 =====
BLAS_THREADS <- 2L
Sys.setenv(OMP_NUM_THREADS = BLAS_THREADS)
Sys.setenv(OPENBLAS_NUM_THREADS = BLAS_THREADS)
Sys.setenv(MKL_NUM_THREADS = BLAS_THREADS)

# ===== 检测环境 =====
on_hpc <- Sys.getenv("SLURM_JOB_ID") != ""
.available <- as.integer(Sys.getenv("SLURM_NTASKS", unset = NA))
if (is.na(.available)) .available <- parallel::detectCores()
if (is.na(.available)) .available <- 4L

# ===== 计算 worker 数（公式唯一） =====
n_workers <- max(1L, (.available - 1L) %/% BLAS_THREADS)

message(sprintf("[targets] 环境: %s, 核数: %d, workers: %d, BLAS: %d",
                if (on_hpc) "HPC" else "本地", .available, n_workers, BLAS_THREADS))

# ===== 配置 controller =====
if (on_hpc) {
    # HPC: 每个 SLURM job 作为一个 worker
    # worker 内部用 BLAS_THREADS 个线程
    controller <- crew.cluster::crew_controller_slurm(
        name = "slurm",
        workers = n_workers,
        seconds_idle = 300,
        slurm_cpus_per_task = BLAS_THREADS,  # 每个 worker 2 核
        slurm_memory_gigabytes_per_cpu = 4,
        slurm_time_minutes = 60,
        slurm_partition = "64c512g",
        script_lines = c(
            "module load R",
            paste0("export OMP_NUM_THREADS=", BLAS_THREADS),
            paste0("export OPENBLAS_NUM_THREADS=", BLAS_THREADS),
            paste0("export MKL_NUM_THREADS=", BLAS_THREADS)
        )
    )
} else {
    # 本地: 同样公式
    controller <- crew_controller_local(
        name = "local",
        workers = n_workers,
        seconds_idle = 60
    )
}

tar_option_set(
    packages = c("dplyr", "ggplot2"),  # 根据项目需要修改
    controller = controller,
    storage = "worker",      # worker 端存储，减少主进程内存压力
    retrieval = "worker",    # worker 端读取
    format = "qs",           # 比 rds 更快的序列化格式
    memory = "transient"     # 用完即释放，减少内存占用
)

tar_source()

# ===== 定义 targets =====
list(
    # 在此添加 targets
    # tar_target(data, read_data()),
    # tar_target(model, fit_model(data)),
    # tar_target(results, summarize(model))
)
