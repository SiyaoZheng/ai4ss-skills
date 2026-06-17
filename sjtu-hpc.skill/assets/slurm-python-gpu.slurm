#!/bin/bash
#===============================================================================
# SJTU HPC Slurm Template: Python GPU Job (A100)
# 适用场景: 深度学习训练/推理、BERT/LLM微调、大规模embedding计算
#===============================================================================

#-------------------------------------------------------------------------------
# 作业基本信息
#-------------------------------------------------------------------------------
#SBATCH --job-name=gpu_job              # 作业名称
#SBATCH --partition=a100                # GPU队列:
                                        #   a100: A100 80GB (推荐，大模型)
                                        #   dgx2: V100 32GB (旧型号)

#-------------------------------------------------------------------------------
# GPU 资源配置
#-------------------------------------------------------------------------------
#SBATCH --gres=gpu:1                    # GPU数量 (1-8卡)
#SBATCH -n 6                            # CPU核数 (建议: 每GPU 6核)
#SBATCH --ntasks-per-node=6
#SBATCH --mem=64G                       # 内存 (建议: 每GPU 64G)
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
module load miniconda3
module load cuda/11.8                   # 根据PyTorch版本选择CUDA

source activate your_env_name

# 设置 CUDA 环境变量
export CUDA_VISIBLE_DEVICES=$SLURM_LOCALID

# 显示环境信息
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "GPUs allocated: $CUDA_VISIBLE_DEVICES"
echo "Python: $(which python)"
echo "PyTorch version: $(python -c 'import torch; print(torch.__version__)')"
echo "CUDA available: $(python -c 'import torch; print(torch.cuda.is_available())')"
echo "GPU count: $(python -c 'import torch; print(torch.cuda.device_count())')"
echo "Start time: $(date)"
echo "=========================================="

#===============================================================================
# 运行程序
#===============================================================================

# 单GPU训练
python train.py

# 或者使用 torchrun 进行分布式训练（多GPU）
# torchrun --nproc_per_node=$SLURM_GPUS_ON_NODE train.py

# 常见深度学习任务示例:
# BERT微调
# python finetune_bert.py --model bert-base-chinese --epochs 3 --batch_size 32

# Sentence Transformers embedding
# python encode_texts.py --input corpus.txt --output embeddings.npy

#===============================================================================
# 结束信息
#===============================================================================
echo "=========================================="
echo "End time: $(date)"
echo "Job finished"
echo "=========================================="

#===============================================================================
# 使用说明
#===============================================================================
# 提交作业: sbatch slurm-python-gpu.slurm
# 查看GPU使用: squeue -u $USER -o "%.10i %.9P %.20j %.8u %.2t %.10M %.6D %R %b"
#
# GPU内存估算（计算社会科学常见模型）:
#   - BERT-base 微调: batch_size=32 约 8GB
#   - BERT-large 微调: batch_size=16 约 16GB
#   - Chinese-BERT-wwm: batch_size=32 约 10GB
#   - Sentence-BERT encoding: 取决于文本长度，通常 4-8GB
#   - LLaMA-7B 推理: 约 14GB (fp16)
#   - LLaMA-7B LoRA微调: 约 20GB
#
# A100 80GB 适合:
#   - 大batch训练
#   - 长文本处理 (max_length > 512)
#   - 大模型微调 (7B-13B参数)
#
# 多GPU注意事项:
#   - 使用 DataParallel 或 DistributedDataParallel
#   - batch_size 可按GPU数量线性增加
#   - 学习率通常也需要相应调整
#===============================================================================
