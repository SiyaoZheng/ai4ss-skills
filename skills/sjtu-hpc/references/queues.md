# SJTU HPC 队列参考手册 / Queue Reference Guide

本文档详细介绍上海交通大学高性能计算平台的所有队列配置。
This document provides comprehensive information about all queue configurations on SJTU HPC platforms.

---

## 目录 / Table of Contents

1. [思源一号集群 / Siyuan-1 Cluster](#思源一号集群--siyuan-1-cluster)
2. [Pi 2.0 集群 / Pi 2.0 Cluster](#pi-20-集群--pi-20-cluster)
3. [AI 平台 / AI Platform](#ai-平台--ai-platform)
4. [ARM 平台 / ARM Platform](#arm-平台--arm-platform)
5. [操作系统升级说明 / Operating System Upgrades](#操作系统升级说明--operating-system-upgrades)
6. [资源计算公式 / Resource Allocation Formulas](#资源计算公式--resource-allocation-formulas)
7. [队列选择指南 / Queue Selection Guide](#队列选择指南--queue-selection-guide)
8. [作业延期政策 / Job Extension Policy](#作业延期政策--job-extension-policy)

---

## 思源一号集群 / Siyuan-1 Cluster

思源一号是交大最新的高性能计算集群，配备高内存节点和 NVIDIA A100 GPU。
Siyuan-1 is SJTU's latest HPC cluster featuring high-memory nodes and NVIDIA A100 GPUs.

### 队列总览 / Queue Overview

| 队列 Queue | 类型 Type | 核心范围 Cores | 最大时长 Max Time | 节点模式 Node Mode |
|:-----------|:----------|:---------------|:------------------|:-------------------|
| `64c512g` | CPU | 1 - 60,000 | 7 days | Exclusive |
| `a100` | GPU | 1 - 92 cards | 7 days | Exclusive |
| `debug64c512g` | CPU Debug | 1 - 128 (2 nodes) | 60 min | Exclusive |
| `debuga100` | GPU Debug | 1 - 64 (1 node) | 20 min | Exclusive |

### 详细配置 / Detailed Specifications

#### 64c512g 队列 (CPU Queue)

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 单节点配置 Node Config | 64 cores, 512 GB RAM |
| 每核内存 Memory/Core | 8 GB |
| 可申请核数 Core Range | 1 - 60,000 |
| 最大运行时长 Max Walltime | 7 days (168 hours) |
| 节点模式 Node Mode | 独占 Exclusive |

**适用场景 / Use Cases:**
- 大规模并行计算 (Large-scale parallel computing)
- 内存密集型应用 (Memory-intensive applications)
- MPI 作业 (MPI jobs)
- 科学计算与数值模拟 (Scientific computing & numerical simulations)

**Slurm 提交示例 / Submission Example:**
```bash
#!/bin/bash
#SBATCH --job-name=cpu_job
#SBATCH --partition=64c512g
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=64
#SBATCH --time=24:00:00

# 总核数: 2 × 64 = 128 cores
# 总内存: 2 × 512 GB = 1024 GB
```

#### a100 队列 (GPU Queue)

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 单节点配置 Node Config | 64 cores, 512 GB RAM, 4× A100 40GB |
| GPU 型号 GPU Model | NVIDIA A100 40GB |
| 每卡配比 CPU Cores/GPU | 16 cores |
| 每核内存 Memory/Core | 8 GB |
| 可申请卡数 GPU Range | 1 - 92 cards |
| 最大运行时长 Max Walltime | 7 days (168 hours) |

**资源配比规则 / Resource Allocation Rules:**
- 申请 1 GPU → 自动分配 16 CPU cores + 128 GB RAM
- 申请 4 GPU (1 node) → 自动分配 64 CPU cores + 512 GB RAM

**适用场景 / Use Cases:**
- 深度学习训练 (Deep learning training)
- 大模型微调 (LLM fine-tuning)
- GPU 加速计算 (GPU-accelerated computing)
- 多卡并行训练 (Multi-GPU parallel training)

**Slurm 提交示例 / Submission Example:**
```bash
#!/bin/bash
#SBATCH --job-name=gpu_job
#SBATCH --partition=a100
#SBATCH --nodes=1
#SBATCH --gres=gpu:2
#SBATCH --time=48:00:00

# 申请 2 块 A100 GPU
# 自动分配: 32 CPU cores, 256 GB RAM
```

#### debug64c512g 队列 (CPU Debug Queue)

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 最大节点数 Max Nodes | 2 nodes |
| 最大核数 Max Cores | 128 cores |
| 最大时长 Max Time | 60 minutes |
| 优先级 Priority | High (快速调度) |

**使用限制 / Limitations:**
- 仅用于代码调试和测试 (Debugging and testing only)
- 禁止用于生产计算 (No production jobs)
- 超时自动终止 (Auto-terminated when time limit reached)

#### debuga100 队列 (GPU Debug Queue)

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 最大节点数 Max Nodes | 1 node |
| 最大 GPU 数 Max GPUs | 28 virtual cards (虚拟卡) |
| GPU 显存 VRAM | **5GB per virtual GPU** (非真实 A100) |
| 最大时长 Max Time | 20 minutes |
| 优先级 Priority | High (快速调度) |

**⚠️ 重要警告 / Critical Warning:**
- **这不是真正的 A100 GPU！** 是 5GB 显存的虚拟 GPU
- This is NOT real A100! Virtual GPUs with only 5GB VRAM
- 不适合实际 GPU 计算，仅用于脚本测试 (Script testing only, not for real computation)

**使用限制 / Limitations:**
- 仅用于 GPU 代码调试 (GPU debugging only)
- 测试 CUDA 程序兼容性 (Test CUDA compatibility)
- 验证脚本语法和环境配置 (Verify script syntax and environment)

---

## Pi 2.0 集群 / Pi 2.0 Cluster

Pi 2.0 是交大主力计算集群，提供多种队列满足不同计算需求。
Pi 2.0 is SJTU's main computing cluster, offering various queues for different computational needs.

### 队列总览 / Queue Overview

| 队列 Queue | 核心范围 Cores | 每核内存 Mem/Core | 最大时长 Max Time | 节点模式 |
|:-----------|:---------------|:------------------|:------------------|:---------|
| `cpu` | 40 - 24,000 | 4 GB | 7 days | Exclusive |
| `small` | 1 - 20 | 4 GB | 7 days | Shared |
| `debug` | 1 - 80 | 4 GB | 20 min | Shared |
| `huge` | 1 - 80 | 35 GB | 2 days | Exclusive |
| `192c6t` | 1 - 192 | 31 GB | 2 days | Exclusive |

### 详细配置 / Detailed Specifications

#### cpu 队列 (Standard CPU Queue)

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 单节点配置 Node Config | 40 cores, 192 GB RAM |
| 每核内存 Memory/Core | 4 GB (约 4.8 GB 可用) |
| 可申请核数 Core Range | 40 - 24,000 |
| 最大运行时长 Max Walltime | 7 days (168 hours) |
| 节点模式 Node Mode | 独占 Exclusive |

**重要说明 / Important Notes:**
- 最小申请 40 核 (1 完整节点) — Minimum 40 cores (1 full node)
- 节点独占模式，不与其他作业共享 — Exclusive mode, no sharing

**Slurm 提交示例 / Submission Example:**
```bash
#!/bin/bash
#SBATCH --job-name=pi_cpu
#SBATCH --partition=cpu
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=40
#SBATCH --time=72:00:00

# 总核数: 4 × 40 = 160 cores
# 总内存: 4 × 192 GB = 768 GB
```

#### small 队列 (Shared CPU Queue)

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 可申请核数 Core Range | 1 - 20 |
| 每核内存 Memory/Core | 4 GB |
| 最大运行时长 Max Walltime | 7 days (168 hours) |
| 节点模式 Node Mode | 共享 Shared |

**适用场景 / Use Cases:**
- 小规模串行任务 (Small serial jobs)
- 数据预处理 (Data preprocessing)
- 交互式调试 (Interactive debugging)
- 不需要完整节点的作业 (Jobs not requiring full nodes)

**Slurm 提交示例 / Submission Example:**
```bash
#!/bin/bash
#SBATCH --job-name=small_job
#SBATCH --partition=small
#SBATCH --ntasks=8
#SBATCH --time=24:00:00

# 8 cores, 32 GB RAM (shared node)
```

#### debug 队列 (Debug Queue)

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 可申请核数 Core Range | 1 - 80 |
| 每核内存 Memory/Core | 4 GB |
| 最大时长 Max Time | 20 minutes |
| 优先级 Priority | High |

**适用场景 / Use Cases:**
- 快速测试脚本语法 (Quick syntax testing)
- 验证作业配置 (Verify job configuration)
- 检查环境依赖 (Check environment dependencies)

#### huge 队列 (High-Memory Queue)

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 单节点配置 Node Config | 80 cores, 3 TB RAM |
| 每核内存 Memory/Core | 35 GB |
| 可申请核数 Core Range | 1 - 80 |
| 最大运行时长 Max Walltime | 2 days (48 hours) |
| 节点模式 Node Mode | 独占 Exclusive |

**适用场景 / Use Cases:**
- 超大内存需求 (Extremely memory-intensive jobs)
- 基因组组装 (Genome assembly)
- 大规模图计算 (Large-scale graph computing)
- 内存数据库操作 (In-memory database operations)

**注意事项 / Notes:**
- 资源稀缺，请合理使用 (Limited resources, use wisely)
- 优先考虑是否可以用 `cpu` 队列替代 (Consider `cpu` queue first)

#### 192c6t 队列 (Ultra High-Memory Queue)

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 单节点配置 Node Config | 192 cores, 6 TB RAM |
| 每核内存 Memory/Core | 31 GB |
| 可申请核数 Core Range | 1 - 192 |
| 最大运行时长 Max Walltime | 2 days (48 hours) |
| 节点模式 Node Mode | 独占 Exclusive |

**适用场景 / Use Cases:**
- 极端内存密集型任务 (Extreme memory requirements)
- 需要 TB 级内存的单一任务 (Single jobs needing TB-scale RAM)

---

## AI 平台 / AI Platform

AI 平台配备 NVIDIA DGX-2 系统，适合大规模深度学习训练。
The AI Platform features NVIDIA DGX-2 systems for large-scale deep learning.

### dgx2 队列

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 单节点配置 Node Config | 96 cores, 1.45 TB RAM, 16× V100 32GB |
| GPU 型号 GPU Model | NVIDIA V100 32GB (NVLink 互联) |
| 每卡配比 CPU Cores/GPU | 6 cores |
| 每核内存 Memory/Core | 15 GB |
| 可申请卡数 GPU Range | 1 - 128 cards |
| 最大运行时长 Max Walltime | 7 days (168 hours) |

**资源配比规则 / Resource Allocation Rules:**
- 申请 1 GPU → 自动分配 6 CPU cores + 90 GB RAM
- 申请 16 GPU (1 node) → 自动分配 96 CPU cores + 1.45 TB RAM

**DGX-2 特点 / DGX-2 Features:**
- 16 块 V100 通过 NVSwitch 全互联 (16× V100 fully connected via NVSwitch)
- 节点内 GPU 带宽 300 GB/s (Intra-node GPU bandwidth: 300 GB/s)
- 适合多卡并行训练 (Ideal for multi-GPU training)

**Slurm 提交示例 / Submission Example:**
```bash
#!/bin/bash
#SBATCH --job-name=dgx2_train
#SBATCH --partition=dgx2
#SBATCH --nodes=1
#SBATCH --gres=gpu:8
#SBATCH --time=168:00:00

# 申请 8 块 V100 GPU
# 自动分配: 48 CPU cores, 720 GB RAM
```

---

## ARM 平台 / ARM Platform

ARM 平台采用国产飞腾处理器，适合 ARM 架构软件测试与开发。
The ARM Platform uses domestic Phytium processors for ARM software development and testing.

### arm128c256g 队列

| 参数 Parameter | 值 Value |
|:---------------|:---------|
| 单节点配置 Node Config | 128 cores, 256 GB RAM |
| 处理器 Processor | 飞腾 (Phytium) ARM |
| 每核内存 Memory/Core | 2 GB |
| 可申请核数 Core Range | 1 - 12,800 |
| 最大运行时长 Max Walltime | 7 days (168 hours) |

**适用场景 / Use Cases:**
- ARM 架构软件移植 (ARM software porting)
- 国产化适配测试 (Domestic adaptation testing)
- ARM 性能评估 (ARM performance benchmarking)

**注意事项 / Notes:**
- 需要 ARM 架构编译的程序 (Requires ARM-compiled binaries)
- x86 程序无法直接运行 (x86 programs won't run directly)

---

## 操作系统升级说明 / Operating System Upgrades

部分集群队列已完成操作系统升级，以应对原有系统停止维护的问题。
Some cluster queues have been upgraded to new operating systems due to end-of-life of the original systems.

### KOS 系统 (Pi 2.0 cpu 队列) / KOS System (Pi 2.0 cpu Queue)

Pi 2.0 集群的 `cpu` 队列已从 CentOS 7 升级至 KOS（基于 Linux Kernel 和 OpenAnolis）。
The `cpu` queue on Pi 2.0 has been upgraded from CentOS 7 to KOS (based on Linux Kernel and OpenAnolis).

| 参数 Parameter | 说明 Description |
|:---------------|:-----------------|
| 升级原因 Upgrade Reason | CentOS 7 于 2024 年 6 月停止维护 (CentOS 7 reached end-of-life in June 2024) |
| 登录节点 Login Node | `pilogin.hpc.sjtu.edu.cn` |
| 模块路径 Module Path | `/lustre/share/spack/modules/cascadelake/linux-rhel8-skylake_avx512` |

**可用软件 / Available Software:**
- 编译器 Compilers: gcc/8.5.0, Intel oneAPI 2021.4.0
- MPI 库 MPI Libraries: OpenMPI 4.1.5
- 科学库 Scientific Libraries: FFTW, HDF5, NetCDF
- 分子动力学 Molecular Dynamics: GROMACS, LAMMPS
- 量子化学 Quantum Chemistry: CP2K, Quantum ESPRESSO
- 流体力学 CFD: OpenFOAM
- 天气模拟 Weather Simulation: WRF
- 生物信息学工具 Bioinformatics Tools

**重要说明 / Important Notes:**
- 性能与原 CentOS 7 系统保持一致 (Performance is consistent with the previous CentOS 7 system)
- 使用流程与原系统相同 (Usage procedures remain the same)

**Slurm 提交示例 / Submission Examples:**

交互式作业 / Interactive Job:
```bash
# 申请交互式会话
# Request an interactive session
srun -p cpu -N 1 -n 40 --pty /bin/bash
```

批处理作业 / Batch Job:
```bash
#!/bin/bash
#SBATCH --job-name=kos_job
#SBATCH --partition=cpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=40
#SBATCH --time=24:00:00

# 加载模块 / Load modules
module use /lustre/share/spack/modules/cascadelake/linux-rhel8-skylake_avx512
module load gcc/8.5.0
module load openmpi/4.1.5

# 运行程序 / Run program
mpirun ./your_program
```

### Rocky Linux 系统 (Siyuan-1 64c512g 队列) / Rocky Linux System (Siyuan-1 64c512g Queue)

思源一号集群的 `64c512g` 队列已从 CentOS 8 升级至 Rocky Linux。
The `64c512g` queue on Siyuan-1 has been upgraded from CentOS 8 to Rocky Linux.

| 参数 Parameter | 说明 Description |
|:---------------|:-----------------|
| 升级原因 Upgrade Reason | CentOS 8 于 2021 年 12 月停止维护 (CentOS 8 reached end-of-maintenance in December 2021) |
| 登录节点 Login Node | `sylogin.hpc.sjtu.edu.cn` |
| 节点配置 Node Specs | 64 核, 512GB 内存 (64 cores, 512GB RAM) |

**重要说明 / Important Notes:**
- 节点配置保持不变 (Node specs remain unchanged: 64 cores, 512GB RAM)
- 大部分主流应用已完成适配 (Most mainstream applications have been adapted)
- 如有兼容性问题，请联系 hpc@sjtu.edu.cn (Contact hpc@sjtu.edu.cn for any compatibility issues)

**Slurm 提交示例 / Submission Examples:**

交互式作业 / Interactive Job:
```bash
# 申请交互式会话
# Request an interactive session
srun -p 64c512g -N 1 -n 64 --pty /bin/bash
```

批处理作业 / Batch Job:
```bash
#!/bin/bash
#SBATCH --job-name=rocky_job
#SBATCH --partition=64c512g
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=64
#SBATCH --time=48:00:00

# 加载模块 / Load modules
module load gcc
module load openmpi

# 运行程序 / Run program
mpirun ./your_program
```

---

## 资源计算公式 / Resource Allocation Formulas

### CPU 队列内存计算 / CPU Queue Memory Calculation

| 集群 Cluster | 队列 Queue | 公式 Formula |
|:-------------|:-----------|:-------------|
| Siyuan-1 | 64c512g | `Memory = Cores × 8 GB` |
| Pi 2.0 | cpu, small, debug | `Memory = Cores × 4 GB` |
| Pi 2.0 | huge | `Memory = Cores × 35 GB` |
| Pi 2.0 | 192c6t | `Memory = Cores × 31 GB` |
| ARM | arm128c256g | `Memory = Cores × 2 GB` |

### GPU 队列资源配比 / GPU Queue Resource Allocation

| 集群 Cluster | 队列 Queue | GPU | CPU/GPU | Memory/CPU |
|:-------------|:-----------|:----|:--------|:-----------|
| Siyuan-1 | a100 | A100 40GB | 16 cores | 8 GB |
| AI Platform | dgx2 | V100 32GB | 6 cores | 15 GB |

**GPU 队列计算公式 / GPU Queue Formulas:**

```
# Siyuan-1 a100 队列
Cores = GPUs × 16
Memory = Cores × 8 GB = GPUs × 128 GB

# AI Platform dgx2 队列
Cores = GPUs × 6
Memory = Cores × 15 GB = GPUs × 90 GB
```

**示例 / Examples:**

| 队列 | 申请 GPU | 分配 CPU | 分配内存 |
|:-----|:---------|:---------|:---------|
| a100 | 1 | 16 | 128 GB |
| a100 | 2 | 32 | 256 GB |
| a100 | 4 | 64 | 512 GB |
| dgx2 | 1 | 6 | 90 GB |
| dgx2 | 8 | 48 | 720 GB |
| dgx2 | 16 | 96 | 1.45 TB |

---

## 队列选择指南 / Queue Selection Guide

### 决策流程图 / Decision Flowchart

```
开始 → 是否需要 GPU?
         ↓
    ┌────┴────┐
   是         否
    ↓          ↓
需要 A100?   内存需求?
    ↓          ↓
┌───┴───┐  ┌──┴──┐
是      否  ≤4GB  >4GB
↓       ↓   ↓      ↓
a100   dgx2 cpu   huge/192c6t
```

### 推荐场景对照表 / Recommended Queue by Scenario

| 场景 Scenario | 推荐队列 Queue | 说明 Notes |
|:--------------|:---------------|:-----------|
| 深度学习训练 | a100 / dgx2 | A100 更新，V100 数量多 |
| MPI 并行计算 | 64c512g / cpu | 选择合适的集群 |
| 小规模测试 | small | 快速调度，共享节点 |
| 代码调试 | debug* | 高优先级，快速启动 |
| 基因组分析 | huge | 需要大内存 |
| 内存数据库 | 192c6t | 超大内存需求 |
| ARM 开发 | arm128c256g | ARM 架构专用 |

### Debug 队列使用建议 / Debug Queue Best Practices

| 队列 | 用途 | 限制 |
|:-----|:-----|:-----|
| debug | 快速测试脚本 | 20 min, 80 cores max |
| debug64c512g | 测试高内存代码 | 60 min, 2 nodes max |
| debuga100 | 测试 GPU 代码 | 20 min, 1 node max |

**最佳实践 / Best Practices:**
1. 先用 debug 队列验证作业脚本 (Test scripts in debug queue first)
2. 确认无误后再提交正式队列 (Submit to production queue after verification)
3. 不要在 debug 队列运行实际计算 (Don't run actual computations in debug)

---

## 作业延期政策 / Job Extension Policy

### 标准作业时限 / Standard Time Limits

| 队列类型 | 默认最大时长 | 可延期上限 |
|:---------|:-------------|:-----------|
| 生产队列 | 7 days | 14 days |
| 大内存队列 | 2 days | 4 days |
| 调试队列 | 20-60 min | 不可延期 |

### 延期申请流程 / Extension Request Process

1. **提前申请 / Advance Request**
   - 在作业到期前 **2 天** 发送邮件 (Email **2 days** before expiration)
   - 发送至 HPC 管理员邮箱 (Send to HPC admin email)

2. **邮件内容 / Email Content**
   ```
   主题: 作业延期申请 - [作业ID]
   Subject: Job Extension Request - [Job ID]

   - 作业 ID (Job ID)
   - 用户名 (Username)
   - 当前队列 (Current Queue)
   - 申请延期时长 (Requested Extension)
   - 延期原因 (Reason for Extension)
   ```

3. **延期限制 / Extension Limits**
   - 单次延期最长 7 天 (Max 7 days per extension)
   - 总运行时间不超过 14 天 (Total runtime ≤ 14 days)
   - 调试队列不支持延期 (Debug queues cannot be extended)

### 避免延期的建议 / Tips to Avoid Extensions

1. **检查点机制 / Checkpointing**
   - 定期保存中间结果 (Save intermediate results regularly)
   - 支持断点续算 (Enable restart from checkpoints)

2. **合理估算时间 / Estimate Time Properly**
   - 小规模测试后估算总时间 (Estimate from small-scale tests)
   - 预留 20% 余量 (Add 20% buffer)

3. **数组作业 / Job Arrays**
   - 将长任务拆分为多个短任务 (Split long jobs into shorter ones)
   - 使用 `--array` 参数 (Use `--array` parameter)

---

## 快速参考卡 / Quick Reference Card

### Siyuan-1 集群

```
┌─────────────────────────────────────────────────────────────┐
│ 64c512g    │ CPU    │ 1-60000核  │ 8GB/核  │ 7天  │ 独占  │
│ a100       │ GPU    │ 1-92卡     │ 16核/卡 │ 7天  │ 独占  │
│ debug64c512g│ Debug │ ≤2节点    │ 8GB/核  │ 60分 │ 独占  │
│ debuga100  │ Debug  │ ≤1节点    │ 16核/卡 │ 20分 │ 独占  │
└─────────────────────────────────────────────────────────────┘
```

### Pi 2.0 集群

```
┌─────────────────────────────────────────────────────────────┐
│ cpu        │ CPU    │ 40-24000核 │ 4GB/核  │ 7天  │ 独占  │
│ small      │ CPU    │ 1-20核     │ 4GB/核  │ 7天  │ 共享  │
│ debug      │ Debug  │ 1-80核     │ 4GB/核  │ 20分 │ 共享  │
│ huge       │ HiMem  │ 1-80核     │ 35GB/核 │ 2天  │ 独占  │
│ 192c6t     │ HiMem  │ 1-192核    │ 31GB/核 │ 2天  │ 独占  │
└─────────────────────────────────────────────────────────────┘
```

### AI & ARM 平台

```
┌─────────────────────────────────────────────────────────────┐
│ dgx2       │ GPU    │ 1-128卡V100│ 6核/卡  │ 7天  │ 独占  │
│ arm128c256g│ ARM    │ 1-12800核  │ 2GB/核  │ 7天  │ 独占  │
└─────────────────────────────────────────────────────────────┘
```

---

## 相关文档 | Related Documentation

- **存储系统**: [storage.md](storage.md) - 各集群对应的存储系统 (Pi 2.0→Lustre, Siyuan-1→GPFS)
- **GPU 计算**: [gpu.md](gpu.md) - GPU 队列详细使用指南
- **故障排查**: [troubleshooting.md](troubleshooting.md) - 作业排队、超时等问题

---

*最后更新 / Last Updated: 2026-01*
*适用于 SJTU HPC 平台 / Applicable to SJTU HPC Platform*
