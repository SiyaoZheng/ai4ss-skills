#!/bin/bash
#===============================================================================
# SJTU HPC Slurm Template: R Parallel Job (future/furrr)
# 适用场景: Bootstrap、交叉验证、蒙特卡洛模拟、多模型批量估计
#===============================================================================

#-------------------------------------------------------------------------------
# 作业基本信息
#-------------------------------------------------------------------------------
#SBATCH --job-name=r_parallel           # 作业名称
#SBATCH --partition=cpu                 # 队列 (并行任务建议用cpu队列)
                                        #   small: 1-20核
                                        #   cpu: 40-24000核（推荐）
                                        #   64c512g: 思源一号

#-------------------------------------------------------------------------------
# 资源配置（并行计算需要更多资源）
#-------------------------------------------------------------------------------
#SBATCH -n 40                           # 总核数（根据并行任务数设置）
#SBATCH --ntasks-per-node=40            # 每节点核数（思源一号最大64核）
#SBATCH --mem=160G                      # 内存（每核4G × 40核）
#SBATCH --time=72:00:00                 # 最大运行时间

#-------------------------------------------------------------------------------
# 输出与通知
#-------------------------------------------------------------------------------
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=YOUR_EMAIL@sjtu.edu.cn

#===============================================================================
# 环境配置
#===============================================================================

module purge
module load r/4.2.0
# 或使用 conda 环境
# module load miniconda3
# source activate r_env

# 传递核数到环境变量
export SLURM_CORES=$SLURM_NTASKS
export OMP_NUM_THREADS=1                # 避免嵌套并行冲突
export MKL_NUM_THREADS=1

echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Cores for parallel: $SLURM_CORES"
echo "Start time: $(date)"
echo "=========================================="

#===============================================================================
# 运行程序
#===============================================================================

Rscript your_parallel_analysis.R

#===============================================================================
# 结束信息
#===============================================================================
echo "=========================================="
echo "End time: $(date)"
echo "Job finished"
echo "=========================================="

#===============================================================================
# R 脚本示例 (your_parallel_analysis.R)
#===============================================================================
#
# library(future)
# library(furrr)
# library(tictoc)
#
# # 获取 Slurm 分配的核数
# n_cores <- as.integer(Sys.getenv("SLURM_CORES", "4"))
# cat("Using", n_cores, "cores\n")
#
# # 设置并行后端
# plan(multisession, workers = n_cores)
#
# # ============== 示例1: Bootstrap 置信区间 ==============
# bootstrap_iteration <- function(i, data) {
#   sample_data <- data[sample(nrow(data), replace = TRUE), ]
#   coef(lm(y ~ x1 + x2, data = sample_data))
# }
#
# tic("Bootstrap")
# boot_results <- future_map(
#   1:1000,
#   ~bootstrap_iteration(.x, my_data),
#   .options = furrr_options(seed = TRUE),
#   .progress = TRUE
# )
# toc()
#
# # ============== 示例2: 多重插补并行 ==============
# library(mice)
#
# # mice 内置并行 (推荐)
# imp <- mice(data, m = 50, maxit = 20,
#             parallelseed = 123,
#             n.core = n_cores)
#
# # ============== 示例3: 交叉验证 ==============
# cv_fold <- function(fold_id, data, folds) {
#   train <- data[folds != fold_id, ]
#   test <- data[folds == fold_id, ]
#   model <- lm(y ~ ., data = train)
#   pred <- predict(model, test)
#   mean((test$y - pred)^2)  # MSE
# }
#
# tic("Cross-validation")
# cv_results <- future_map_dbl(
#   1:10,
#   ~cv_fold(.x, my_data, fold_ids),
#   .options = furrr_options(seed = TRUE)
# )
# toc()
#
# # ============== 示例4: 蒙特卡洛模拟 ==============
# simulate_once <- function(i, n = 1000) {
#   x <- rnorm(n)
#   y <- 2 + 3*x + rnorm(n)
#   coef(lm(y ~ x))[2]  # 返回斜率估计
# }
#
# tic("Monte Carlo")
# sim_results <- future_map_dbl(
#   1:10000,
#   simulate_once,
#   .options = furrr_options(seed = TRUE),
#   .progress = TRUE
# )
# toc()
#
# # 关闭并行
# plan(sequential)
#
#===============================================================================
# 最佳实践
#===============================================================================
# 1. 设置 OMP_NUM_THREADS=1 避免嵌套并行
# 2. 使用 furrr_options(seed = TRUE) 确保可重复性
# 3. 内存估算: 单任务内存 × 核数 × 1.2
# 4. 任务粒度: 每个任务至少运行几秒，避免调度开销
# 5. 进度监控: 使用 .progress = TRUE 或 progressr 包
#
# 内存优化技巧:
#   - 使用 future_map 而非 future_lapply (更高效)
#   - 大对象用 globals 参数显式传递
#   - 考虑分批处理: split(1:10000, cut(1:10000, 100))
#===============================================================================
