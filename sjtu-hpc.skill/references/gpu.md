# GPU Computing Reference | GPU 计算参考手册

Complete guide for GPU computing on SJTU HPC clusters (Siyuan-1 A100 and Pi 2.0 DGX-2).

SJTU HPC 集群 GPU 计算完整指南（思源一号 A100 和 Pi 2.0 DGX-2）。

---

## Table of Contents | 目录

1. [GPU Hardware Resources | GPU 硬件资源](#gpu-hardware-resources--gpu-硬件资源)
2. [Queue Overview | 队列概览](#queue-overview--队列概览)
3. [Job Scripts | 作业脚本](#job-scripts--作业脚本)
4. [Debug Queue | 调试队列](#debug-queue--调试队列)
5. [Interactive GPU Sessions | 交互式 GPU 会话](#interactive-gpu-sessions--交互式-gpu-会话)
6. [GPU Monitoring | GPU 监控](#gpu-monitoring--gpu-监控)
7. [CUDA Environment | CUDA 环境](#cuda-environment--cuda-环境)
8. [PyTorch Configuration | PyTorch 配置](#pytorch-configuration--pytorch-配置)
9. [TensorFlow Configuration | TensorFlow 配置](#tensorflow-configuration--tensorflow-配置)
10. [Multi-GPU Training | 多卡训练](#multi-gpu-training--多卡训练)
11. [Common Issues | 常见问题](#common-issues--常见问题)

---

## GPU Hardware Resources | GPU 硬件资源

### Siyuan-1 A100 (思源一号)

| Specification | Value |
|---------------|-------|
| GPU Nodes | 23 nodes |
| GPUs per Node | 4x NVIDIA HGX A100 40GB |
| Total GPUs | 92 A100 cards |
| GPU Memory | 40GB HBM2e per card |
| CPU:GPU Ratio | 16 CPU cores per GPU (default) |
| Interconnect | NVLink within node |
| Queues | `a100`, `debuga100` |
| Login Node | `sylogin.hpc.sjtu.edu.cn` |
| Storage Path | `/dssg/home/acct-XXX/username` |

**A100 Key Features | A100 特性:**
- Third-generation Tensor Cores (支持 TF32, FP16, BF16, INT8)
- 40GB HBM2e memory, 1.6TB/s bandwidth
- Multi-Instance GPU (MIG) support (调试队列使用此技术)
- Ideal for: Large language models, deep learning training, scientific computing

### Pi 2.0 DGX-2 (AI Platform | AI 平台)

| Specification | Value |
|---------------|-------|
| Servers | 8x NVIDIA DGX-2 |
| GPUs per Server | 16x NVIDIA Tesla V100 32GB |
| Total GPUs | 128 V100 cards |
| GPU Memory | 32GB HBM2 per card |
| CPU:GPU Ratio | 6 CPU cores per GPU (recommended) |
| GPU Interconnect | NVSwitch, 2.4TB/s bandwidth |
| Queue | `dgx2` |
| Login Node | `pilogin.hpc.sjtu.edu.cn` |
| Storage Path | `/lustre/home/acct-XXX/username` |

**DGX-2 Key Features | DGX-2 特性:**
- NVSwitch enables all-to-all GPU communication (全互联拓扑)
- 2.4TB/s total GPU-to-GPU bandwidth
- Ideal for: Multi-GPU training, model parallelism, large batch training

### Hardware Comparison | 硬件对比

| Feature | A100 40GB | V100 32GB |
|---------|-----------|-----------|
| Architecture | Ampere | Volta |
| FP32 Performance | 19.5 TFLOPS | 15.7 TFLOPS |
| FP16 Performance | 312 TFLOPS | 125 TFLOPS |
| Memory | 40GB HBM2e | 32GB HBM2 |
| Memory Bandwidth | 1.6 TB/s | 900 GB/s |
| TF32 Support | Yes | No |
| BF16 Support | Yes | No |

---

## Queue Overview | 队列概览

### GPU Queues | GPU 队列

| Queue | Cluster | Max GPUs | Max Time | CPU:GPU | Notes |
|-------|---------|----------|----------|---------|-------|
| `a100` | Siyuan-1 | 92 cards | 7 days | 16:1 | Production A100 |
| `debuga100` | Siyuan-1 | 28 virtual | 2 hours | 4:1 | Debug only, 5GB VRAM |
| `dgx2` | Pi 2.0 | 128 cards | 7 days | 6:1 | V100 DGX-2 |

### Resource Limits | 资源限制

**a100 Queue:**
- Maximum 4 GPUs per node
- 16 CPU cores allocated per GPU by default
- 7-day maximum walltime
- Exclusive node access when requesting all 4 GPUs

**dgx2 Queue:**
- Maximum 16 GPUs per node
- 6 CPU cores recommended per GPU
- 7-day maximum walltime
- NVSwitch provides high-bandwidth multi-GPU communication

---

## Job Scripts | 作业脚本

### Single Node, Single GPU (A100) | 单机单卡 (A100)

```bash
#!/bin/bash
#SBATCH --job-name=gpu_single
#SBATCH --partition=a100
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH --time=24:00:00

# Load CUDA module | 加载 CUDA 模块
module load cuda/11.8

# Load conda environment | 加载 conda 环境
module load miniconda3
source activate pytorch-env

# Run training | 运行训练
python train.py --device cuda:0
```

### Single Node, Single GPU (V100) | 单机单卡 (V100)

```bash
#!/bin/bash
#SBATCH --job-name=gpu_v100
#SBATCH --partition=dgx2
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=6
#SBATCH --gres=gpu:1
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH --time=24:00:00

module load cuda/11.8
module load miniconda3
source activate pytorch-env

python train.py --device cuda:0
```

### Single Node, Multi-GPU (A100) | 单机多卡 (A100)

```bash
#!/bin/bash
#SBATCH --job-name=gpu_multi
#SBATCH --partition=a100
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=64          # 16 cores × 4 GPUs
#SBATCH --gres=gpu:4                 # Request all 4 GPUs on node
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH --time=72:00:00

module load cuda/11.8
module load miniconda3
source activate pytorch-env

# PyTorch DataParallel | PyTorch 数据并行
python train_dp.py --num_gpus 4

# Or PyTorch DistributedDataParallel | 或 PyTorch 分布式数据并行
torchrun --standalone --nproc_per_node=4 train_ddp.py
```

### Single Node, Multi-GPU (V100 DGX-2) | 单机多卡 (V100 DGX-2)

```bash
#!/bin/bash
#SBATCH --job-name=dgx2_multi
#SBATCH --partition=dgx2
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=48          # 6 cores × 8 GPUs
#SBATCH --gres=gpu:8                 # Request 8 GPUs
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH --time=72:00:00

module load cuda/11.8
module load miniconda3
source activate pytorch-env

# Use torchrun for DDP training | 使用 torchrun 进行 DDP 训练
torchrun --standalone --nproc_per_node=8 train_ddp.py
```

### Multi-Node, Multi-GPU (A100) | 多机多卡 (A100)

```bash
#!/bin/bash
#SBATCH --job-name=multi_node
#SBATCH --partition=a100
#SBATCH -N 2                         # 2 nodes
#SBATCH --ntasks-per-node=4          # 4 tasks per node (1 per GPU)
#SBATCH --cpus-per-task=16           # 16 cores per task
#SBATCH --gres=gpu:4                 # 4 GPUs per node
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH --time=168:00:00             # 7 days

module load cuda/11.8
module load miniconda3
source activate pytorch-env

# Get master node address | 获取主节点地址
export MASTER_ADDR=$(scontrol show hostname $SLURM_NODELIST | head -n 1)
export MASTER_PORT=29500

# Total GPUs = nodes × GPUs per node | 总 GPU 数 = 节点数 × 每节点 GPU 数
NNODES=$SLURM_NNODES
GPUS_PER_NODE=4
WORLD_SIZE=$((NNODES * GPUS_PER_NODE))

# Launch with srun | 使用 srun 启动
srun torchrun \
    --nnodes=$NNODES \
    --nproc_per_node=$GPUS_PER_NODE \
    --rdzv_id=$SLURM_JOB_ID \
    --rdzv_backend=c10d \
    --rdzv_endpoint=$MASTER_ADDR:$MASTER_PORT \
    train_ddp.py \
    --world_size $WORLD_SIZE
```

### Multi-Node, Multi-GPU (DGX-2) | 多机多卡 (DGX-2)

```bash
#!/bin/bash
#SBATCH --job-name=dgx2_multi_node
#SBATCH --partition=dgx2
#SBATCH -N 2                         # 2 DGX-2 servers
#SBATCH --ntasks-per-node=16         # 16 tasks per node (1 per GPU)
#SBATCH --cpus-per-task=6            # 6 cores per task
#SBATCH --gres=gpu:16                # All 16 GPUs per node
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH --time=168:00:00

module load cuda/11.8
module load miniconda3
source activate pytorch-env

export MASTER_ADDR=$(scontrol show hostname $SLURM_NODELIST | head -n 1)
export MASTER_PORT=29500

NNODES=$SLURM_NNODES
GPUS_PER_NODE=16
WORLD_SIZE=$((NNODES * GPUS_PER_NODE))

srun torchrun \
    --nnodes=$NNODES \
    --nproc_per_node=$GPUS_PER_NODE \
    --rdzv_id=$SLURM_JOB_ID \
    --rdzv_backend=c10d \
    --rdzv_endpoint=$MASTER_ADDR:$MASTER_PORT \
    train_ddp.py \
    --world_size $WORLD_SIZE
```

---

## Debug Queue | 调试队列

### debuga100 Queue Specifications | debuga100 队列规格

The debug queue uses MIG (Multi-Instance GPU) technology to partition 4 physical A100 GPUs into 28 virtual GPUs.

调试队列使用 MIG 技术将 4 块物理 A100 分割成 28 块虚拟 GPU。

| Parameter | Value |
|-----------|-------|
| Physical GPUs | 4x A100 |
| Virtual GPUs | 28 (7 per physical GPU) |
| VRAM per virtual GPU | ~5GB |
| Max walltime | 2 hours |
| QoS requirement | `--qos=debug` |

### Debug Job Script | 调试作业脚本

```bash
#!/bin/bash
#SBATCH --job-name=debug_gpu
#SBATCH --partition=debuga100
#SBATCH --qos=debug                  # Required for debug queue | 必须指定
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4            # Fewer CPUs for debug
#SBATCH --gres=gpu:1
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH --time=02:00:00              # Max 2 hours

module load cuda/11.8
module load miniconda3
source activate pytorch-env

# Debug/test your code | 调试测试代码
python train.py --debug --epochs 1 --batch_size 8
```

### Debug Queue Usage Notes | 调试队列使用注意

1. **Memory Limitation | 显存限制**: Only ~5GB VRAM, reduce batch size and model size
2. **Time Limit | 时间限制**: Maximum 2 hours, for quick tests only
3. **QoS Required | 必须指定 QoS**: Always include `--qos=debug`
4. **Best For | 适用场景**:
   - Code debugging and testing | 代码调试测试
   - Environment verification | 环境验证
   - Small-scale experiments | 小规模实验

---

## Interactive GPU Sessions | 交互式 GPU 会话

### Interactive A100 Session | 交互式 A100 会话

```bash
# Request interactive session | 申请交互式会话
srun -p a100 -N 1 --ntasks-per-node=1 --cpus-per-task=16 \
     --gres=gpu:1 --time=04:00:00 --pty bash

# Inside the session | 在会话中
module load cuda/11.8
module load miniconda3
source activate pytorch-env
python -c "import torch; print(torch.cuda.is_available())"
```

### Interactive V100 Session | 交互式 V100 会话

```bash
srun -p dgx2 -N 1 --ntasks-per-node=1 --cpus-per-task=6 \
     --gres=gpu:1 --time=04:00:00 --pty bash
```

### Interactive Debug Session | 交互式调试会话

```bash
# Quick debug session (2 hours max) | 快速调试会话（最长 2 小时）
srun -p debuga100 --qos=debug -N 1 --ntasks-per-node=1 \
     --cpus-per-task=4 --gres=gpu:1 --time=02:00:00 --pty bash
```

### Jupyter on GPU Node | GPU 节点上的 Jupyter

```bash
#!/bin/bash
#SBATCH --job-name=jupyter_gpu
#SBATCH --partition=a100
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --output=%j.out
#SBATCH --error=%j.err
#SBATCH --time=08:00:00

module load cuda/11.8
module load miniconda3
source activate pytorch-env

# Get node hostname | 获取节点主机名
NODE=$(hostname)
PORT=8888

echo "Jupyter running on: $NODE:$PORT"
echo "SSH tunnel command: ssh -L $PORT:$NODE:$PORT username@sylogin.hpc.sjtu.edu.cn"

jupyter notebook --no-browser --ip=0.0.0.0 --port=$PORT
```

---

## GPU Monitoring | GPU 监控

### Check GPU Usage on Allocated Node | 查看已分配节点的 GPU 使用

```bash
# 1. Find your node | 查找你的节点
squeue -u $USER
# Example output: JOBID  PARTITION  NAME  USER  ST  TIME  NODES  NODELIST(REASON)
#                 12345  a100       test  user  R   0:05  1      gpu03

# 2. SSH to the node | SSH 到节点
ssh gpu03

# 3. Check GPU status | 查看 GPU 状态
nvidia-smi

# 4. Continuous monitoring (every 1 second) | 持续监控（每秒刷新）
watch -n 1 nvidia-smi

# 5. Query specific metrics | 查询特定指标
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu \
           --format=csv
```

### nvidia-smi Key Metrics | nvidia-smi 关键指标

| Metric | Description |
|--------|-------------|
| GPU-Util | GPU compute utilization (目标 > 80%) |
| Memory-Usage | VRAM usage (显存使用量) |
| Temp | GPU temperature (温度，正常 < 80°C) |
| Power | Power consumption (功耗) |
| Processes | Running processes using GPU |

### Monitor from Login Node | 从登录节点监控

```bash
# Check queue and node allocation | 查看队列和节点分配
squeue -p a100 -o "%.10i %.9P %.20j %.8u %.2t %.10M %.6D %R"

# View node GPU status (requires admin permission) | 查看节点 GPU 状态（需要权限）
sinfo -p a100 -N -l
```

### GPU Memory Monitoring in Python | Python 中的 GPU 内存监控

```python
import torch

# Check available GPUs | 检查可用 GPU
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
print(f"Current device: {torch.cuda.current_device()}")
print(f"Device name: {torch.cuda.get_device_name(0)}")

# Memory info | 内存信息
print(f"Allocated: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
print(f"Cached: {torch.cuda.memory_reserved(0) / 1024**3:.2f} GB")
print(f"Max allocated: {torch.cuda.max_memory_allocated(0) / 1024**3:.2f} GB")

# Clear cache | 清理缓存
torch.cuda.empty_cache()
```

---

## CUDA Environment | CUDA 环境

### Available CUDA Modules | 可用 CUDA 模块

```bash
# List available CUDA versions | 列出可用 CUDA 版本
module avail cuda

# Common versions on SJTU HPC | SJTU HPC 常用版本:
# cuda/10.2  cuda/11.1  cuda/11.3  cuda/11.6  cuda/11.8  cuda/12.0
```

### Load CUDA Module | 加载 CUDA 模块

```bash
# Load specific version | 加载特定版本
module load cuda/11.8

# Verify | 验证
nvcc --version
which nvcc
```

### cuDNN Setup | cuDNN 设置

```bash
# cuDNN is usually bundled with CUDA module | cuDNN 通常与 CUDA 模块捆绑
module load cuda/11.8

# Verify cuDNN | 验证 cuDNN
python -c "import torch; print(torch.backends.cudnn.version())"
```

### NCCL for Multi-GPU | 多 GPU 通信 NCCL

```bash
# NCCL is included with CUDA | NCCL 包含在 CUDA 中
module load cuda/11.8

# Verify NCCL | 验证 NCCL
python -c "import torch.distributed as dist; print('NCCL available')"
```

### Environment Variables | 环境变量

```bash
# Add to job script if needed | 如需要可添加到作业脚本
export CUDA_VISIBLE_DEVICES=0,1,2,3    # Limit visible GPUs | 限制可见 GPU
export CUDA_DEVICE_ORDER=PCI_BUS_ID    # Consistent GPU ordering | GPU 排序一致
export NCCL_DEBUG=INFO                  # Debug NCCL issues | 调试 NCCL 问题
export NCCL_IB_DISABLE=1               # Disable InfiniBand for NCCL | 禁用 IB
```

---

## PyTorch Configuration | PyTorch 配置

### Install PyTorch with CUDA | 安装支持 CUDA 的 PyTorch

```bash
module load miniconda3
conda create -n pytorch-env python=3.10
source activate pytorch-env

# PyTorch with CUDA 11.8 | 安装 PyTorch (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify installation | 验证安装
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.version.cuda}'); print(f'cuDNN: {torch.backends.cudnn.version()}')"
```

### Basic PyTorch GPU Usage | PyTorch GPU 基本使用

```python
import torch

# Set device | 设置设备
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Move model to GPU | 将模型移至 GPU
model = MyModel().to(device)

# Move data to GPU | 将数据移至 GPU
inputs = inputs.to(device)
labels = labels.to(device)

# Training loop | 训练循环
outputs = model(inputs)
loss = criterion(outputs, labels)
loss.backward()
optimizer.step()
```

### DataParallel (Simple Multi-GPU) | DataParallel（简单多卡）

```python
import torch
import torch.nn as nn

# Wrap model with DataParallel | 用 DataParallel 包装模型
model = MyModel()
if torch.cuda.device_count() > 1:
    print(f"Using {torch.cuda.device_count()} GPUs")
    model = nn.DataParallel(model)
model = model.cuda()

# Training is automatic across GPUs | 训练自动在多卡上进行
```

### DistributedDataParallel (Recommended) | DistributedDataParallel（推荐）

```python
import os
import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler

def setup(rank, world_size):
    os.environ['MASTER_ADDR'] = os.environ.get('MASTER_ADDR', 'localhost')
    os.environ['MASTER_PORT'] = os.environ.get('MASTER_PORT', '29500')
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)

def cleanup():
    dist.destroy_process_group()

def train(rank, world_size):
    setup(rank, world_size)

    # Create model and move to GPU | 创建模型并移至 GPU
    model = MyModel().cuda(rank)
    model = DDP(model, device_ids=[rank])

    # Create distributed sampler | 创建分布式采样器
    sampler = DistributedSampler(dataset, num_replicas=world_size, rank=rank)
    dataloader = DataLoader(dataset, batch_size=32, sampler=sampler)

    for epoch in range(epochs):
        sampler.set_epoch(epoch)  # Important for shuffling | 重要：用于打乱顺序
        for batch in dataloader:
            # Training step | 训练步骤
            pass

    cleanup()

if __name__ == "__main__":
    world_size = torch.cuda.device_count()
    torch.multiprocessing.spawn(train, args=(world_size,), nprocs=world_size)
```

### PyTorch Mixed Precision Training | PyTorch 混合精度训练

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    optimizer.zero_grad()

    # Mixed precision forward pass | 混合精度前向传播
    with autocast():
        outputs = model(inputs)
        loss = criterion(outputs, labels)

    # Scaled backward pass | 缩放后的反向传播
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

---

## TensorFlow Configuration | TensorFlow 配置

### Install TensorFlow with CUDA | 安装支持 CUDA 的 TensorFlow

```bash
module load miniconda3
conda create -n tf-env python=3.10
source activate tf-env

# TensorFlow with GPU support | 安装 TensorFlow GPU 版本
pip install tensorflow[and-cuda]

# Verify installation | 验证安装
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

### Basic TensorFlow GPU Usage | TensorFlow GPU 基本使用

```python
import tensorflow as tf

# Check GPUs | 检查 GPU
gpus = tf.config.list_physical_devices('GPU')
print(f"Available GPUs: {len(gpus)}")

# Memory growth (recommended) | 内存增长（推荐）
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)

# Limit GPU memory | 限制 GPU 内存
# tf.config.set_logical_device_configuration(
#     gpus[0],
#     [tf.config.LogicalDeviceConfiguration(memory_limit=8192)]  # 8GB
# )
```

### TensorFlow Multi-GPU Strategy | TensorFlow 多 GPU 策略

```python
import tensorflow as tf

# MirroredStrategy for single-node multi-GPU | 单机多卡策略
strategy = tf.distribute.MirroredStrategy()

print(f'Number of devices: {strategy.num_replicas_in_sync}')

with strategy.scope():
    model = create_model()
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')

model.fit(train_dataset, epochs=10)
```

### TensorFlow Mixed Precision | TensorFlow 混合精度

```python
from tensorflow.keras import mixed_precision

# Enable mixed precision | 启用混合精度
mixed_precision.set_global_policy('mixed_float16')

# Build model normally | 正常构建模型
model = create_model()

# For the last layer, use float32 | 最后一层使用 float32
outputs = layers.Activation('softmax', dtype='float32')(x)
```

---

## Multi-GPU Training | 多卡训练

### Strategy Comparison | 策略对比

| Strategy | Use Case | Scaling |
|----------|----------|---------|
| DataParallel (DP) | Quick prototyping | Single node |
| DistributedDataParallel (DDP) | Production training | Multi-node |
| Model Parallel | Very large models | Single/Multi-node |
| Pipeline Parallel | Sequential models | Multi-node |

### torchrun Launch Script | torchrun 启动脚本

```bash
#!/bin/bash
#SBATCH --job-name=ddp_train
#SBATCH --partition=a100
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=64
#SBATCH --gres=gpu:4
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load cuda/11.8
module load miniconda3
source activate pytorch-env

# Single node, 4 GPUs | 单节点 4 卡
torchrun --standalone --nproc_per_node=4 train_ddp.py

# With specific parameters | 带特定参数
torchrun --standalone \
    --nproc_per_node=4 \
    train_ddp.py \
    --batch_size 64 \
    --learning_rate 0.001 \
    --epochs 100
```

### DeepSpeed Integration | DeepSpeed 集成

```bash
# Install DeepSpeed | 安装 DeepSpeed
pip install deepspeed

# Launch with DeepSpeed | 使用 DeepSpeed 启动
deepspeed --num_gpus=4 train_ds.py --deepspeed_config ds_config.json
```

**ds_config.json example | 配置示例:**

```json
{
    "train_batch_size": 256,
    "gradient_accumulation_steps": 4,
    "fp16": {
        "enabled": true,
        "loss_scale": 0
    },
    "zero_optimization": {
        "stage": 2,
        "offload_optimizer": {
            "device": "cpu"
        }
    }
}
```

### Hugging Face Accelerate | Hugging Face Accelerate

```bash
# Install | 安装
pip install accelerate

# Configure | 配置
accelerate config

# Launch | 启动
accelerate launch train.py
```

---

## Common Issues | 常见问题

### 1. CUDA Out of Memory | CUDA 内存不足

**Symptoms | 症状:**
```
RuntimeError: CUDA out of memory. Tried to allocate X MiB
```

**Solutions | 解决方案:**

```python
# 1. Reduce batch size | 减小批量大小
batch_size = batch_size // 2

# 2. Use gradient accumulation | 使用梯度累积
accumulation_steps = 4
for i, batch in enumerate(dataloader):
    loss = model(batch) / accumulation_steps
    loss.backward()
    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()

# 3. Use mixed precision | 使用混合精度
from torch.cuda.amp import autocast, GradScaler

# 4. Clear cache periodically | 定期清理缓存
torch.cuda.empty_cache()

# 5. Use gradient checkpointing | 使用梯度检查点
from torch.utils.checkpoint import checkpoint
```

### 2. NCCL Timeout | NCCL 超时

**Symptoms | 症状:**
```
RuntimeError: NCCL timeout or connection refused
```

**Solutions | 解决方案:**

```bash
# Increase timeout | 增加超时时间
export NCCL_TIMEOUT=1800

# Disable IB if problematic | 如有问题可禁用 IB
export NCCL_IB_DISABLE=1

# Use socket instead | 使用 socket
export NCCL_SOCKET_IFNAME=eth0
```

### 3. GPU Not Visible | GPU 不可见

**Symptoms | 症状:**
```
torch.cuda.is_available() returns False
```

**Solutions | 解决方案:**

```bash
# Check CUDA_VISIBLE_DEVICES | 检查环境变量
echo $CUDA_VISIBLE_DEVICES

# Check GPU allocation | 检查 GPU 分配
nvidia-smi

# Verify CUDA module loaded | 验证 CUDA 模块已加载
module list

# Check driver | 检查驱动
cat /proc/driver/nvidia/version
```

### 4. cuDNN Version Mismatch | cuDNN 版本不匹配

**Symptoms | 症状:**
```
RuntimeError: cuDNN error: CUDNN_STATUS_NOT_SUPPORTED
```

**Solutions | 解决方案:**

```bash
# Reinstall PyTorch with correct CUDA version | 重新安装正确 CUDA 版本的 PyTorch
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Or disable cuDNN for specific operations | 或禁用特定操作的 cuDNN
torch.backends.cudnn.enabled = False
```

### 5. Slow Data Loading | 数据加载慢

**Symptoms | 症状:**
GPU utilization low, training bottlenecked by data loading

**Solutions | 解决方案:**

```python
# Increase num_workers | 增加 worker 数量
dataloader = DataLoader(
    dataset,
    batch_size=64,
    num_workers=8,          # Increase based on CPUs | 根据 CPU 数量增加
    pin_memory=True,        # Pin memory for faster transfer | 固定内存加速传输
    prefetch_factor=2,      # Prefetch batches | 预取批次
    persistent_workers=True # Keep workers alive | 保持 worker 存活
)
```

### 6. Debug Queue Memory Error | 调试队列内存错误

**Symptoms | 症状:**
Out of memory on debuga100 queue

**Solutions | 解决方案:**

```python
# Debug queue only has ~5GB VRAM | 调试队列仅有 ~5GB 显存
# Use smaller batch size | 使用更小的批量大小
batch_size = 4

# Use smaller model | 使用更小的模型
model = SmallModel()

# Or use fp16 | 或使用 fp16
model = model.half()
```

### 7. Job Pending Too Long | 作业排队过久

**Check queue status | 检查队列状态:**

```bash
# Check pending jobs | 查看排队作业
squeue -p a100 | grep PD

# Check node availability | 查看节点可用性
sinfo -p a100

# Consider using debug queue for testing | 考虑使用调试队列测试
# Or reduce resource request | 或减少资源请求
```

---

## Best Practices | 最佳实践

### 1. Resource Efficiency | 资源效率

```bash
# Request only what you need | 只申请需要的资源
#SBATCH --gres=gpu:1              # Don't request 4 if you need 1
#SBATCH --cpus-per-task=16        # Match CPU:GPU ratio
#SBATCH --time=04:00:00           # Estimate accurately
```

### 2. Checkpointing | 检查点

```python
# Save checkpoints regularly | 定期保存检查点
if epoch % save_interval == 0:
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
    }, f'checkpoint_epoch_{epoch}.pt')
```

### 3. Monitoring | 监控

```python
# Add logging | 添加日志
import wandb  # or tensorboard
wandb.init(project='my-project')
wandb.log({'loss': loss, 'gpu_mem': torch.cuda.memory_allocated()})
```

### 4. Testing Before Production | 生产前测试

```bash
# Always test on debug queue first | 总是先在调试队列测试
sbatch --partition=debuga100 --qos=debug --time=00:30:00 test_job.slurm
```

---

## 相关文档 | Related Documentation

- **Python/R 环境配置**: [python-r.md](python-r.md) - CUDA 环境、conda 配置
- **队列详情**: [queues.md](queues.md) - GPU 队列规格与限制
- **存储系统**: [storage.md](storage.md) - 检查点存储建议
- **故障排查**: [troubleshooting.md](troubleshooting.md) - GPU 相关问题解决

---

## External Resources | 外部资源

- SJTU HPC Documentation: https://docs.hpc.sjtu.edu.cn
- NVIDIA A100 Datasheet: https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/nvidia-a100-datasheet.pdf
- PyTorch DDP Tutorial: https://pytorch.org/tutorials/intermediate/ddp_tutorial.html
- DeepSpeed Documentation: https://www.deepspeed.ai/docs/
- NCCL Documentation: https://docs.nvidia.com/deeplearning/nccl/
