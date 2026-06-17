# SJTU HPC Storage Systems Reference
# 上海交大超算存储系统参考手册

> Comprehensive guide to storage architecture, performance characteristics, and best practices on SJTU HPC clusters.
> 上海交大超算集群存储架构、性能特性和最佳实践完整指南。

---

## Table of Contents | 目录

1. [Storage Architecture Overview | 存储系统架构概览](#storage-architecture-overview--存储系统架构概览)
2. [Lustre File System | Lustre 文件系统](#lustre-file-system--lustre-文件系统)
3. [GPFS File System | GPFS 文件系统](#gpfs-file-system--gpfs-文件系统)
4. [Flash Storage | 全闪存文件系统](#flash-storage--全闪存文件系统)
5. [Cold Storage | 冷存储系统](#cold-storage--冷存储系统)
6. [Directory Structure | 目录结构](#directory-structure--目录结构)
7. [Storage Quotas | 存储配额](#storage-quotas--存储配额)
8. [Performance Optimization | 性能优化](#performance-optimization--性能优化)
9. [Queue-Storage Mapping | 队列与存储对应关系](#queue-storage-mapping--队列与存储对应关系)
10. [Data Safety | 数据安全](#data-safety--数据安全)
11. [Common Issues | 常见问题](#common-issues--常见问题)
12. [Quick Reference Card | 快速参考卡](#quick-reference-card--快速参考卡)

---

## Storage Architecture Overview | 存储系统架构概览

### Master Comparison Table | 系统对比总表 (2025-12 更新)

| 文件系统 | 挂载点 | 容量 | 介质 | 访问节点 | 免费配额 | 快照 |
|----------|--------|------|------|----------|----------|------|
| Lustre | /lustre | 25PB | HDD | Pi 2.0 登录/计算/data 传输节点 | 3TB | 无 |
| GPFS | /dssg | **23.8PB** | HDD | 思源一号 登录/计算/data/sydata 传输节点 | **5TB** | 无 |
| Flash (全闪存) | /scratch | 108TB | NVMe SSD | Pi 2.0 登录/计算/data 传输节点 | 免费 | 无 |
| 科学大数据平台 | /union | **40.7PB** | HDD | 传输节点读写，**计算节点只读** | **10TB** | **有** |

**平台总存储容量已突破 105PB**

### 2025-12 存储升级要点

1. **思源一号 GPFS**: 10PB → **23.8PB**，配额 3TB → **5TB/课题组**，聚合吞吐 **120GB/s+**，可容纳 **75亿文件**
2. **科学大数据平台**: 23.5PB → **40.7PB**，配额 3TB → **10TB/课题组**
3. **价格不变**: 扩容"加量不加价"

### 省钱策略 | Cost-Saving Tips

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 💰 省钱妙招                                                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ 1. 新增原始数据 → 直接上传到科学大数据平台 (/union)                        │
│    而不是思源一号或 π 超算的家目录                                         │
│    Upload new raw data directly to /union, NOT to /dssg or /lustre      │
│                                                                         │
│ 2. 计算分析结束 → 及时归档到科学大数据平台                                  │
│    结果不再修改后，rsync 到 /union 并删除家目录副本                         │
│    After analysis, archive to /union and delete from home               │
│                                                                         │
│ 3. 计算时从 /union 读取数据（只读）                                        │
│    使用 $UNION 环境变量简化脚本                                           │
│    Read from /union during computation (read-only, use $UNION var)      │
│                                                                         │
│ 存储价格对比:                                                            │
│   - 思源一号 /dssg: 0.28 元/TB/月                                        │
│   - 科学大数据 /union: 更低成本，适合长期存储                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Architecture Diagram | 架构示意图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SJTU HPC Storage Architecture                        │
│                          上海交大超算存储架构                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐        │
│  │      Pi 2.0 Cluster         │    │     Siyuan-1 Cluster        │        │
│  │      Pi 2.0 集群            │    │     思源一号集群             │        │
│  ├─────────────────────────────┤    ├─────────────────────────────┤        │
│  │ Login/Compute Nodes         │    │ Login/Compute Nodes         │        │
│  │ 登录/计算节点               │    │ 登录/计算节点               │        │
│  │         ↓                   │    │         ↓                   │        │
│  │ ┌─────────────────────────┐ │    │ ┌─────────────────────────┐ │        │
│  │ │  Lustre (/lustre)       │ │    │ │  GPFS (/dssg)           │ │        │
│  │ │  25PB, HDD              │ │    │ │  10PB, HDD              │ │        │
│  │ │  Primary Storage        │ │    │ │  Primary Storage        │ │        │
│  │ └─────────────────────────┘ │    │ └─────────────────────────┘ │        │
│  │         ↓                   │    │                             │        │
│  │ ┌─────────────────────────┐ │    │                             │        │
│  │ │  Flash (/scratch)       │ │    │                             │        │
│  │ │  108TB, NVMe SSD        │ │    │                             │        │
│  │ │  High-Performance I/O   │ │    │                             │        │
│  │ └─────────────────────────┘ │    │                             │        │
│  └─────────────────────────────┘    └─────────────────────────────┘        │
│                    ↘                      ↙                                 │
│              ┌────────────────────────────────────────────────┐            │
│              │          Transfer Nodes (data/sydata)          │            │
│              │              传输节点                           │            │
│              │                     ↓                           │            │
│              │    ┌────────────────────────────────────────┐  │            │
│              │    │   Cold Storage (/archive, /vault)      │  │            │
│              │    │   40PB+, HDD, With Snapshots           │  │            │
│              │    │   冷存储，支持快照恢复                   │  │            │
│              │    │                                        │  │            │
│              │    │   /union = Merged View (合并视图)       │  │            │
│              │    └────────────────────────────────────────┘  │            │
│              └────────────────────────────────────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Storage Selection Guide | 存储选择指南

```
Decision Tree for Research Data | 研究数据决策树:

1. Is this actively used data for ongoing computation?
   是否是正在进行计算的活跃数据？
   → YES: $HOME (Lustre/GPFS)
   → NO: Continue...

2. Does this require high-speed random I/O (small files, databases)?
   是否需要高速随机 I/O（小文件、数据库）？
   → YES: $SCRATCH (Flash storage) + Copy results back!
   → NO: Continue...

3. Is this historical data you rarely access?
   是否是很少访问的历史数据？
   → YES: $UNION (Cold storage with snapshots)
   → NO: Keep in $HOME
```

---

## Lustre File System | Lustre 文件系统

### Overview | 概述

Lustre is a distributed parallel file system designed for HPC workloads, providing PB-scale storage with high aggregate I/O throughput.
Lustre 是专为 HPC 工作负载设计的分布式并行文件系统，提供 PB 级存储和高聚合 I/O 吞吐。

| Parameter | Value | 参数 | 值 |
|-----------|-------|------|-----|
| Mount Point | /lustre | 挂载点 | /lustre |
| Capacity | 25PB (expanded from 14PB) | 容量 | 25PB（从14PB扩容） |
| Media Type | HDD | 介质类型 | 机械硬盘 |
| Free Quota | 3TB per account | 免费配额 | 每账户 3TB |
| Snapshot | Not available | 快照功能 | 无 |

### Access Nodes | 访问节点

| Node Type | Access | 节点类型 | 可访问性 |
|-----------|--------|----------|----------|
| Pi 2.0 Login Nodes | Full R/W | Pi 2.0 登录节点 | 完全读写 |
| Pi 2.0 Compute Nodes | Full R/W | Pi 2.0 计算节点 | 完全读写 |
| data.hpc.sjtu.edu.cn | Full R/W | data 传输节点 | 完全读写 |
| AI Platform Nodes | Full R/W | AI 平台节点 | 完全读写 |
| ARM Platform Nodes | Full R/W | ARM 平台节点 | 完全读写 |

### Lustre Architecture Basics | Lustre 架构基础

```
Lustre File System Components | Lustre 文件系统组件:

┌─────────────────────────────────────────────────────────────────┐
│                         Clients (Compute Nodes)                  │
│                         客户端（计算节点）                        │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
          ┌───────────────────────┴───────────────────────┐
          ↓                                               ↓
┌───────────────────┐                       ┌───────────────────────┐
│ MDS (Metadata     │                       │ OSS (Object Storage   │
│  Server)          │                       │  Servers)             │
│ 元数据服务器       │                       │ 对象存储服务器         │
│                   │                       │                       │
│ Stores:           │                       │ Stores:               │
│ - File names      │                       │ - Actual file data    │
│ - Permissions     │                       │ - Distributed across  │
│ - Directory tree  │                       │   multiple OSTs       │
│ 存储：文件名、权限  │                       │ 存储：实际文件数据     │
│ 目录结构           │                       │ 分布在多个 OST 上      │
└───────────────────┘                       └───────────────────────┘
```

### Striping for Performance | 分条提高性能

Striping distributes file data across multiple OSTs (Object Storage Targets) for parallel I/O.
分条将文件数据分布到多个 OST（对象存储目标）上，实现并行 I/O。

```bash
# Check current stripe settings of a file | 查看文件当前分条设置
lfs getstripe filename
lfs getstripe -d directory/  # Check directory default

# Example output:
# filename
# lmm_stripe_count:  1
# lmm_stripe_size:   1048576    # 1MB stripe size
# lmm_pattern:       raid0
# lmm_layout_gen:    0
#   obdidx         objid        objid           group
#        5          12345       0x3039              0

# Set stripe for a directory (new files inherit) | 设置目录分条（新文件继承）
# Recommended for large files (>100MB) | 大文件（>100MB）推荐设置
lfs setstripe -c 4 -S 4M directory/

# Parameters | 参数说明:
# -c COUNT: Number of OSTs to stripe across (分条的 OST 数量)
#           -c 4: stripe across 4 OSTs
#           -c -1: stripe across all available OSTs
# -S SIZE:  Stripe size (每条大小)
#           -S 1M: 1 MB stripe unit
#           -S 4M: 4 MB stripe unit (recommended for large files)

# Create a new file with specific stripe | 创建指定分条的新文件
lfs setstripe -c 8 -S 2M large_output.dat

# Best practice for large dataset directories | 大数据集目录最佳实践
mkdir $HOME/large_data
lfs setstripe -c 4 -S 4M $HOME/large_data/

# Stripe settings recommendation table | 分条设置推荐表
# File Size        | Stripe Count | Stripe Size
# 文件大小          | 分条数        | 条带大小
# ───────────────────────────────────────────
# < 100 MB         | 1 (default)  | 1M
# 100 MB - 1 GB    | 4            | 4M
# 1 GB - 10 GB     | 8            | 4M
# > 10 GB          | 16 or -1     | 4M
```

### Lustre Performance Characteristics | Lustre 性能特性

| Scenario | Performance | Recommendation |
|----------|-------------|----------------|
| Large sequential files (>1GB) | Excellent | Use striping |
| Many small files (<1MB) | Poor | Avoid or use Flash |
| Random access patterns | Moderate | Consider Flash for intensive workloads |
| Parallel I/O (MPI-IO) | Excellent | Stripe across many OSTs |

| 场景 | 性能 | 建议 |
|------|------|------|
| 大文件顺序读写（>1GB） | 优秀 | 使用分条 |
| 大量小文件（<1MB） | 较差 | 避免或使用全闪存 |
| 随机访问模式 | 中等 | 密集型负载考虑全闪存 |
| 并行 I/O（MPI-IO） | 优秀 | 跨多 OST 分条 |

---

## GPFS File System | GPFS 文件系统

### Overview | 概述

GPFS (General Parallel File System) is IBM's enterprise parallel file system used on Siyuan-1 cluster.
GPFS（通用并行文件系统）是 IBM 的企业级并行文件系统，用于思源一号集群。

| Parameter | Value | 参数 | 值 |
|-----------|-------|------|-----|
| Mount Point | /dssg | 挂载点 | /dssg |
| Capacity | **23.8PB** (2025-12 扩容) | 容量 | **23.8PB** |
| Aggregate Throughput | **120GB/s+** | 聚合吞吐 | **120GB/s+** |
| Max Files | **7.5 billion** | 最大文件数 | **75亿** |
| Media Type | HDD | 介质类型 | 机械硬盘 |
| Infrastructure | 4× DSS-GServer nodes | 基础设施 | 4 台 DSS-GServer 节点 |
| Metadata Redundancy | 3 replicas | 元数据冗余 | 3 副本 |
| Data Redundancy | 8+2p (RAID-like) | 数据冗余 | 8+2p 纠删码 |
| Free Quota | **5TB per group** (2025-12 升级) | 免费配额 | **每课题组 5TB** |
| Snapshot | Not available | 快照功能 | 无 |

**⚠️ 重要**: 思源一号存储误删数据**无法恢复**，请谨慎操作。如需数据保护，请归档到科学大数据平台。

### Access Nodes | 访问节点

| Node Type | Access | 节点类型 | 可访问性 |
|-----------|--------|----------|----------|
| Siyuan-1 Login Nodes | Full R/W | 思源一号登录节点 | 完全读写 |
| Siyuan-1 Compute Nodes | Full R/W | 思源一号计算节点 | 完全读写 |
| data.hpc.sjtu.edu.cn | Full R/W | data 传输节点 | 完全读写 |
| sydata.hpc.sjtu.edu.cn | Full R/W | sydata 传输节点 | 完全读写 |

### GPFS vs Lustre Comparison | GPFS 与 Lustre 对比

| Feature | GPFS (/dssg) | Lustre (/lustre) |
|---------|--------------|------------------|
| Cluster | Siyuan-1 | Pi 2.0/AI/ARM |
| Capacity | 10PB | 25PB |
| Redundancy | 8+2p erasure coding | Configurable |
| Metadata | 3-way replication | Separate MDS |
| Performance | ~1.5 GB/s R, ~800 MB/s W | ~2 GB/s R, ~1 GB/s W |
| Best for | General purpose, high reliability | Large-scale parallel I/O |

| 特性 | GPFS (/dssg) | Lustre (/lustre) |
|------|--------------|------------------|
| 集群 | 思源一号 | Pi 2.0/AI/ARM |
| 容量 | 10PB | 25PB |
| 冗余 | 8+2p 纠删码 | 可配置 |
| 元数据 | 3 副本复制 | 独立 MDS |
| 性能 | 读 ~1.5 GB/s, 写 ~800 MB/s | 读 ~2 GB/s, 写 ~1 GB/s |
| 最佳用途 | 通用计算、高可靠性 | 大规模并行 I/O |

### GPFS Commands | GPFS 常用命令

```bash
# Check quota on GPFS | 查看 GPFS 配额
mmlsquota -u $USER --block-size auto

# Check filesystem usage | 查看文件系统使用情况
df -h /dssg

# Check file placement (filesets) | 查看文件放置
mmlsattr -L filename

# List file ACLs | 查看文件 ACL
mmgetacl filename
```

---

## Flash Storage | 全闪存文件系统

### Overview | 概述

The Flash storage system provides ultra-high performance NVMe SSD storage for I/O-intensive workloads.
全闪存系统提供超高性能的 NVMe SSD 存储，适用于 I/O 密集型工作负载。

| Parameter | Value | 参数 | 值 |
|-----------|-------|------|-----|
| Mount Point | /scratch | 挂载点 | /scratch |
| Capacity | 108TB (shared) | 容量 | 108TB（共享） |
| Media Type | NVMe SSD | 介质类型 | NVMe 固态硬盘 |
| Single Client Read | ~5.7 GB/s | 单客户端读 | ~5.7 GB/s |
| Single Client Write | ~10 GB/s | 单客户端写 | ~10 GB/s |
| 4K Random Read IOPS | ~170,000 | 4K 随机读 IOPS | ~170,000 |
| 4K Random Write IOPS | ~126,000 | 4K 随机写 IOPS | ~126,000 |
| Retention Period | **3 months (auto-cleaned)** | 保留期限 | **3 个月（自动清理）** |
| Backup | **None** | 备份 | **无** |
| High Availability | **None** | 高可用 | **无** |
| Cost | Free | 费用 | 免费 |

### Critical Warnings | 重要警告

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ⚠️  IMPORTANT: Flash Storage Limitations | 重要：全闪存存储限制           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ 1. AUTO-CLEANUP EVERY 3 MONTHS | 每 3 个月自动清理                       │
│    Files older than 3 months are automatically deleted!                 │
│    超过 3 个月的文件会被自动删除！                                        │
│                                                                         │
│ 2. NO BACKUP | 无备份                                                   │
│    Data loss is unrecoverable - always backup important files!          │
│    数据丢失不可恢复 - 务必备份重要文件！                                   │
│                                                                         │
│ 3. NO HIGH AVAILABILITY | 无高可用                                      │
│    Hardware failure = data loss. Use for temporary data only!           │
│    硬件故障 = 数据丢失。仅用于临时数据！                                   │
│                                                                         │
│ 4. SHARED CAPACITY | 共享容量                                           │
│    108TB shared among all users - don't store more than needed          │
│    108TB 所有用户共享 - 不要存储超过需要的数据                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### When to Use Flash Storage | 何时使用全闪存

| Scenario | Use Flash? | Reason |
|----------|------------|--------|
| Network graph computation with random access | YES | High IOPS benefits random I/O |
| Machine learning training checkpoints | YES | Fast write, frequent saves |
| Database-like operations (SQLite, key-value) | YES | Random read/write heavy |
| Processing many small text files | YES | Avoids Lustre small-file overhead |
| Monte Carlo simulations with intermediate I/O | YES | High throughput for temp files |
| Long-term storage | NO | Auto-cleanup, no backup |
| Final results | NO | Use $HOME for permanent storage |
| Data that needs backup | NO | No redundancy |

| 场景 | 使用全闪存？ | 原因 |
|------|------------|------|
| 网络图计算（随机访问） | 是 | 高 IOPS 有利于随机 I/O |
| 机器学习训练检查点 | 是 | 写入快，频繁保存 |
| 类数据库操作（SQLite、键值存储） | 是 | 随机读写密集 |
| 处理大量小文本文件 | 是 | 避免 Lustre 小文件开销 |
| 带中间 I/O 的蒙特卡洛模拟 | 是 | 临时文件高吞吐 |
| 长期存储 | 否 | 自动清理，无备份 |
| 最终结果 | 否 | 使用 $HOME 永久存储 |
| 需要备份的数据 | 否 | 无冗余 |

### Usage Pattern | 使用模式

```bash
#!/bin/bash
#SBATCH --job-name=io_intensive
#SBATCH --partition=cpu

# === SETUP: Create job-specific scratch directory | 设置：创建作业专用 scratch 目录 ===
export WORK=$SCRATCH/job_${SLURM_JOB_ID}
mkdir -p $WORK
cd $WORK

echo "Working in scratch: $WORK"
echo "Job started at: $(date)"

# === STAGE-IN: Copy input data from home to scratch | 数据导入：从 home 复制到 scratch ===
echo "Staging data to scratch..."
cp $HOME/project/data/input.csv ./
cp $HOME/project/data/graph.edgelist ./

# === COMPUTATION: Run I/O-intensive workload | 计算：运行 I/O 密集型任务 ===
# Flash storage provides 10x+ faster I/O for random access patterns
# 全闪存对随机访问模式提供 10 倍以上的 I/O 加速
python $HOME/project/scripts/analyze.py \
    --input input.csv \
    --graph graph.edgelist \
    --output results/

# === STAGE-OUT: Copy results back to home | 数据导出：复制结果回 home ===
echo "Copying results to home..."
mkdir -p $HOME/project/output/job_${SLURM_JOB_ID}
cp -r results/* $HOME/project/output/job_${SLURM_JOB_ID}/

# === CLEANUP: Remove scratch directory | 清理：删除 scratch 目录 ===
echo "Cleaning up scratch..."
rm -rf $WORK

echo "Job completed at: $(date)"
```

### Automated Cleanup Function | 自动清理函数

Add this to your job scripts for reliable cleanup:
将此函数添加到作业脚本以确保可靠清理：

```bash
# scratch_helper.sh - Include in your job scripts
# scratch_helper.sh - 在作业脚本中包含此文件

setup_scratch() {
    export WORK=$SCRATCH/job_${SLURM_JOB_ID:-$$}
    mkdir -p $WORK
    cd $WORK
    echo "[SCRATCH] Created: $WORK"
}

cleanup_scratch() {
    local exit_code=$?
    if [ -d "$WORK" ]; then
        # Save important results first | 先保存重要结果
        if [ -d "$WORK/results" ]; then
            local dest=$HOME/jobs/${SLURM_JOB_ID:-$$}/
            mkdir -p $dest
            cp -r $WORK/results/* $dest/
            echo "[SCRATCH] Results saved to: $dest"
        fi
        rm -rf $WORK
        echo "[SCRATCH] Cleaned up: $WORK"
    fi
    return $exit_code
}

# Set trap to cleanup on exit (success or failure)
# 设置退出时（成功或失败）自动清理
trap cleanup_scratch EXIT

# Usage in job script | 作业脚本中使用:
# source $HOME/scripts/scratch_helper.sh
# setup_scratch
# ... your computation ...
# Results in $WORK/results/ will be auto-saved on exit
```

---

## 科学大数据平台 (Cold Storage) | Scientific Big Data Platform

### Overview | 概述

科学大数据平台采用高密度存储系统，具有**性价比高、访问方法多样、可靠性高**的特点，特别适合用于长久存储"一次写入多次读取"的科学计算数据。

**2025-12 扩容后**：总容量 **40.7PB**，默认配额 **10TB/课题组**

| Storage | Mount Point | Capacity | Purpose |
|---------|-------------|----------|---------|
| Archive | /archive | 23.5PB | Primary archive |
| Vault | /vault | 17.28PB | Secondary/vault storage |
| **Union** | **/union** | **40.7PB (合并视图)** | **推荐使用的统一入口** |

| 存储 | 挂载点 | 容量 | 用途 |
|------|--------|------|------|
| Archive | /archive | 23.5PB | 主要归档 |
| Vault | /vault | 17.28PB | 次级/保险库存储 |
| **Union** | **/union** | **40.7PB** | **推荐：合并视图统一入口** |

### 五种访问方法 | 5 Access Methods

#### 方法1: SFTP 客户端

```bash
# 连接数据传输节点
sftp user@data.hpc.sjtu.edu.cn

# 进入 /union 目录管理数据
cd /union/home/acct-XXX/user/
put local_file.dat
get remote_file.dat
```

#### 方法2: HPC Studio 可视化平台

1. 登录 https://studio.hpc.sjtu.edu.cn
2. 点击 Files 文件管理功能
3. 进入 **Union Home Directory** 目录
4. 在浏览器中管理数据

**注意**: 单个文件大小建议不超过 1GB

#### 方法3: 数据传输节点命令行

```bash
# 登录传输节点
ssh user@data.hpc.sjtu.edu.cn

# 使用 rsync 归档（支持断点续传）
rsync -avP $HOME/completed_project/ $UNION/projects/completed_project/

# 批量校验数据完整性
cd $HOME/completed_project/
find . -type f -exec md5sum {} \; > /tmp/source.md5
cd $UNION/projects/completed_project/
find . -type f -exec md5sum {} \; > /tmp/dest.md5
diff /tmp/source.md5 /tmp/dest.md5
```

参考文档: https://docs.hpc.sjtu.edu.cn/transport/archiveusage.html

#### 方法4: 计算节点读取（只读）

```bash
#!/bin/bash
#SBATCH --job-name=read_union
#SBATCH --partition=cpu
#SBATCH -n 80
#SBATCH --ntasks-per-node=40
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load lammps

# 使用 $UNION 环境变量读取科学大数据平台的数据
# $UNION 自动指向 /union/home/acct-XXX/user/
srun --mpi=pmi2 lmp -i $UNION/YOUR_INPUT_FILE

# ⚠️ 注意：计算节点上只能读取，不能写入！
```

#### 方法5: SSHFS 挂载到本地

```bash
# Linux/Mac 本地挂载
mkdir ~/hpc_union
sshfs user@data.hpc.sjtu.edu.cn:/union/home/acct-XXX/user ~/hpc_union

# 使用完毕后卸载
fusermount -u ~/hpc_union  # Linux
umount ~/hpc_union         # Mac
```

参考文档: https://docs.hpc.sjtu.edu.cn/transport/remoteaccessdata.html#sshfs

### Key Features | 主要特性

| Feature | Cold Storage | Primary Storage (Lustre/GPFS) |
|---------|--------------|-------------------------------|
| Capacity | 40PB+ | 25PB / 10PB |
| Snapshot/Recovery | **YES** | NO |
| Write Access | Transfer nodes only | All nodes |
| Read Access | All nodes (slower) | All nodes |
| Cost | Paid | 3TB free |
| Best For | Archival, backup | Active work |

| 特性 | 冷存储 | 主存储（Lustre/GPFS） |
|------|--------|----------------------|
| 容量 | 40PB+ | 25PB / 10PB |
| 快照/恢复 | **支持** | 不支持 |
| 写入权限 | 仅传输节点 | 所有节点 |
| 读取权限 | 所有节点（较慢） | 所有节点 |
| 费用 | 收费 | 3TB 免费 |
| 最佳用途 | 归档、备份 | 活跃工作 |

### Access Restrictions | 访问限制

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Cold Storage Access Matrix | 冷存储访问矩阵                  │
├───────────────────────────────┬────────────────┬────────────────────────┤
│ Node Type                     │ Read Access    │ Write Access           │
│ 节点类型                       │ 读取权限        │ 写入权限               │
├───────────────────────────────┼────────────────┼────────────────────────┤
│ Login Nodes (登录节点)         │ ✓ (slower)    │ ✗                      │
│ Compute Nodes (计算节点)       │ ✓ (slower)    │ ✗                      │
│ data.hpc.sjtu.edu.cn          │ ✓ (full speed)│ ✓                      │
│ sydata.hpc.sjtu.edu.cn        │ ✓ (full speed)│ ✓                      │
└───────────────────────────────┴────────────────┴────────────────────────┘

To write to cold storage, you MUST ssh to a transfer node first!
要写入冷存储，必须先 SSH 到传输节点！
```

### Migration to Cold Storage | 迁移到冷存储

```bash
# Step 1: Login to transfer node | 步骤1：登录传输节点
ssh user@data.hpc.sjtu.edu.cn   # For Lustre users
ssh user@sydata.hpc.sjtu.edu.cn # For GPFS users

# Step 2: Create archive structure | 步骤2：创建归档结构
mkdir -p $UNION/projects/project_2024

# Step 3: Use rsync with checksum verification | 步骤3：使用 rsync 校验传输
rsync -avP --checksum \
    /lustre/home/acct-XXX/user/completed_project/ \
    $UNION/projects/project_2024/

# Step 4: Verify transfer with checksums | 步骤4：使用校验和验证传输
cd /lustre/home/acct-XXX/user/completed_project/
find . -type f -exec md5sum {} \; | sort > /tmp/source.md5

cd $UNION/projects/project_2024/
find . -type f -exec md5sum {} \; | sort > /tmp/dest.md5

diff /tmp/source.md5 /tmp/dest.md5
# If no output, transfer is verified | 如无输出，传输验证成功

# Step 5: After verification, remove from home | 步骤5：验证后从 home 删除
rm -rf /lustre/home/acct-XXX/user/completed_project/
```

### Snapshot Recovery | 快照恢复

Cold storage has snapshots that can recover accidentally deleted files.
冷存储有快照功能，可以恢复误删文件。

```bash
# To recover deleted files from cold storage | 从冷存储恢复删除的文件:
# 1. Do NOT write anything to the same location | 不要向同一位置写入任何内容
# 2. Contact HPC admin immediately | 立即联系 HPC 管理员
#    Email: hpc@sjtu.edu.cn
#    Subject: Snapshot Recovery Request | 主题：快照恢复请求
#    Include:
#    - Full path of deleted files | 删除文件的完整路径
#    - Approximate deletion time | 大约删除时间
#    - Your username | 您的用户名

# Recovery is NOT guaranteed - depends on snapshot retention
# 恢复不保证成功 - 取决于快照保留策略
```

### Recommended Archive Structure | 推荐归档结构

```bash
$UNION/
├── projects/                      # Completed research projects | 已完成研究项目
│   └── project_name_YYYY/
│       ├── README.md              # Project description | 项目描述
│       ├── MANIFEST.md5           # Checksums for all files | 所有文件校验和
│       ├── data/
│       │   ├── raw/               # Original data (NEVER modify) | 原始数据（永不修改）
│       │   └── processed/         # Analysis-ready data | 分析用数据
│       ├── code/                  # Analysis scripts (also in git) | 分析脚本
│       ├── results/               # Final outputs | 最终输出
│       └── docs/                  # Documentation | 文档
│
├── raw_data/                      # Raw data archive | 原始数据归档
│   ├── surveys/
│   └── social_media/
│
└── backups/                       # Periodic backups | 定期备份
    └── project_name_YYYYMMDD/

# Generate manifest for a project | 为项目生成清单
cd $UNION/projects/project_2024/
echo "# File Manifest - Generated $(date)" > MANIFEST.md5
find . -type f -name '*.csv' -o -name '*.rds' -o -name '*.pkl' | \
    xargs md5sum >> MANIFEST.md5
```

---

## Directory Structure | 目录结构

### Environment Variables | 环境变量

These are pre-configured when you login:
登录时已自动配置：

| Variable | Path Pattern | Description |
|----------|--------------|-------------|
| $HOME | /lustre/home/acct-XXX/user or /dssg/home/acct-XXX/user | Main home directory |
| $SCRATCH | /scratch/acct-XXX/user | Flash storage temporary directory |
| $UNION | /union/acct-XXX/user | Cold storage merged view |
| $ARCHIVE | /archive/acct-XXX/user | Archive cold storage |
| $VAULT | /vault/acct-XXX/user | Vault cold storage |

| 变量 | 路径模式 | 说明 |
|------|----------|------|
| $HOME | /lustre/home/acct-XXX/user 或 /dssg/home/acct-XXX/user | 主目录 |
| $SCRATCH | /scratch/acct-XXX/user | 全闪存临时目录 |
| $UNION | /union/acct-XXX/user | 冷存储合并视图 |
| $ARCHIVE | /archive/acct-XXX/user | archive 冷存储 |
| $VAULT | /vault/acct-XXX/user | vault 冷存储 |

```bash
# Check your environment variables | 检查环境变量
echo "HOME:    $HOME"
echo "SCRATCH: $SCRATCH"
echo "UNION:   $UNION"
echo "ARCHIVE: $ARCHIVE"
echo "VAULT:   $VAULT"

# Example output (Pi 2.0 user):
# HOME:    /lustre/home/acct-XXX/user
# SCRATCH: /scratch/acct-XXX/user
# UNION:   /union/acct-XXX/user
# ARCHIVE: /archive/acct-XXX/user
# VAULT:   /vault/acct-XXX/user
```

### Recommended Directory Organization | 推荐目录组织

```bash
$HOME/                              # Quota: 3TB free (Lustre/GPFS)
├── projects/                       # Active research projects | 活跃研究项目
│   ├── project_alpha/
│   │   ├── data/                   # Working data | 工作数据
│   │   ├── scripts/                # Analysis code | 分析代码
│   │   ├── results/                # Output files | 输出文件
│   │   └── logs/                   # Job logs | 作业日志
│   └── project_beta/
│
├── envs/                           # Virtual environments | 虚拟环境
│   ├── python_ml/                  # Python ML environment
│   └── r_analysis/                 # R packages
│
├── software/                       # Custom compiled software | 自定义软件
│   └── local/
│
├── jobs/                           # Job scripts and results | 作业脚本和结果
│   └── {JOB_ID}/                   # Per-job output directory
│
└── shared -> /lustre/share/acct-XXX/   # Symlink to group share | 组共享链接

$SCRATCH/                           # Capacity: 108TB shared, FREE, 3-month cleanup
└── job_${SLURM_JOB_ID}/            # Per-job temporary directory | 作业临时目录
    ├── input/                      # Staged input data | 导入的输入数据
    ├── work/                       # Intermediate files | 中间文件
    └── output/                     # Results before copy-back | 待复制的结果

$UNION/                             # Capacity: 40PB+, PAID, with snapshots
├── raw_data/                       # Original data archive | 原始数据归档
│   ├── surveys/                    # Survey datasets
│   └── scraped/                    # Web-scraped data
│
├── completed_projects/             # Archived finished projects | 已归档完成项目
│   └── project_2023/
│
└── backups/                        # Periodic backups | 定期备份
    └── weekly_YYYYMMDD/
```

---

## Storage Quotas | 存储配额

### Checking Quotas | 查看配额

```bash
# Universal command (works on most systems) | 通用命令
quota -s

# Lustre-specific quota check | Lustre 专用配额查看
lfs quota -u $USER /lustre
lfs quota -g $(id -gn) /lustre    # Group quota | 组配额

# GPFS-specific quota check | GPFS 专用配额查看
mmlsquota -u $USER --block-size auto
mmlsquota -g $(id -gn) --block-size auto   # Group quota

# Check disk usage breakdown | 查看磁盘使用细分
du -sh $HOME/*
du -sh $HOME/projects/*

# Find largest files | 查找最大文件
find $HOME -type f -size +100M -exec ls -lh {} \; | sort -k5 -hr | head -20

# Find largest directories | 查找最大目录
du -h --max-depth=2 $HOME | sort -hr | head -20

# Count files (check inode usage) | 统计文件数（检查 inode 使用）
find $HOME -type f | wc -l
```

### Quota Interpretation | 配额解读

```bash
# Example Lustre quota output:
# Disk quotas for user user (uid 12345):
#      Filesystem  blocks   quota   limit   grace   files   quota   limit   grace
#          lustre  1536.2G  3072G   3072G       -  156789  500000  500000       -

# Explanation | 解释:
# blocks:  Current disk usage | 当前磁盘使用量
# quota:   Soft limit (warning) | 软限制（警告）
# limit:   Hard limit (cannot exceed) | 硬限制（不可超过）
# grace:   Time remaining to reduce if over soft limit | 超软限制后剩余时间
# files:   Number of files (inode count) | 文件数量（inode 计数）

# You are over quota if:
# 你超出配额如果：
# - blocks > limit (hard limit exceeded) | blocks > limit（超出硬限制）
# - blocks > quota AND grace period expired | blocks > quota 且宽限期已过
```

### Quota Policies | 配额政策 (2025-12 更新)

| Storage | Default Free Quota | Additional Quota | Contact |
|---------|-------------------|------------------|---------|
| Lustre (Pi 2.0) | 3TB/课题组 | Paid expansion | hpc@sjtu.edu.cn |
| GPFS (思源一号) | **5TB/课题组** | Paid expansion | hpc@sjtu.edu.cn |
| Scratch | Unlimited (shared 108TB) | N/A | N/A |
| 科学大数据平台 | **10TB/课题组** | Paid | hpc@sjtu.edu.cn |

| 存储 | 默认免费配额 | 扩容配额 | 联系 |
|------|-------------|----------|------|
| Lustre (Pi 2.0) | 3TB/课题组 | 付费扩容 | hpc@sjtu.edu.cn |
| GPFS (思源一号) | **5TB/课题组** | 付费扩容 | hpc@sjtu.edu.cn |
| Scratch | 无限（共享 108TB） | 不适用 | 不适用 |
| 科学大数据平台 | **10TB/课题组** | 付费 | hpc@sjtu.edu.cn |

### Requesting Quota Increase | 申请增加配额

```
Email to: hpc@sjtu.edu.cn
Subject: 存储配额申请 / Storage Quota Request

Content should include | 内容应包括:
- Username | 用户名
- Account group (acct-XXX) | 账户组
- Current quota and usage | 当前配额和使用量
- Requested new quota | 申请的新配额
- Justification (project name, data description) | 理由（项目名、数据说明）
- Duration needed | 需要的期限
```

---

## Performance Optimization | 性能优化

### I/O Pattern Best Practices | I/O 模式最佳实践

| Pattern | Best Storage | Why |
|---------|--------------|-----|
| Large sequential files (>100MB) | Lustre/GPFS with striping | Parallel I/O across OSTs |
| Many small files (<1MB) | Scratch (Flash) | High IOPS, low latency |
| Random access (databases) | Scratch (Flash) | NVMe IOPS advantage |
| Temporary/intermediate files | Scratch (Flash) | High throughput, no backup needed |
| Long-term storage | Lustre/GPFS | Persistent, quota-managed |
| Archival | Cold Storage | Cheapest, with snapshots |

| 模式 | 最佳存储 | 原因 |
|------|----------|------|
| 大文件顺序读写（>100MB） | 带分条的 Lustre/GPFS | 跨 OST 并行 I/O |
| 大量小文件（<1MB） | Scratch（全闪存） | 高 IOPS，低延迟 |
| 随机访问（数据库） | Scratch（全闪存） | NVMe IOPS 优势 |
| 临时/中间文件 | Scratch（全闪存） | 高吞吐，无需备份 |
| 长期存储 | Lustre/GPFS | 持久化，配额管理 |
| 归档 | 冷存储 | 最便宜，有快照 |

### Lustre/GPFS Optimization Tips | Lustre/GPFS 优化技巧

```bash
# 1. Use appropriate stripe settings for large files | 大文件使用合适的分条设置
mkdir $HOME/large_output
lfs setstripe -c 8 -S 4M $HOME/large_output/

# 2. Aggregate small files before transfer | 传输前聚合小文件
tar -czf archive.tar.gz many_small_files/
# Transfer the archive, then extract | 传输归档后解压

# 3. Avoid metadata-intensive operations | 避免元数据密集操作
# BAD: Creating millions of small files | 不好：创建数百万小文件
# GOOD: Use HDF5, Parquet, or other container formats | 好：使用 HDF5、Parquet 等容器格式

# 4. Use local SSD for intermediate I/O in jobs | 作业中使用本地 SSD 做中间 I/O
# Stage data to scratch, compute, stage back | 数据导入 scratch，计算，导出
```

### Flash Storage Optimization Tips | 全闪存优化技巧

```bash
# 1. Always use job-specific directories | 始终使用作业专用目录
export WORK=$SCRATCH/job_${SLURM_JOB_ID}
mkdir -p $WORK

# 2. Clean up after job completion | 作业完成后清理
trap 'rm -rf $WORK' EXIT

# 3. Stage data in/out properly | 正确导入/导出数据
# Stage in at job start | 作业开始时导入
cp $HOME/input/* $WORK/

# Stage out at job end | 作业结束时导出
cp $WORK/results/* $HOME/output/

# 4. Don't use scratch for long-term storage | 不要用于长期存储
# Data is auto-cleaned every 3 months | 数据每 3 个月自动清理
```

### Avoiding Common Performance Pitfalls | 避免常见性能陷阱

```bash
# PITFALL 1: Creating millions of small files on Lustre | 陷阱1：在 Lustre 创建数百万小文件
# BAD | 不好:
for i in {1..1000000}; do echo "data" > file_$i.txt; done

# GOOD | 好: Use a container format | 使用容器格式
python << 'EOF'
import pandas as pd
df = pd.DataFrame({'data': range(1000000)})
df.to_parquet('data.parquet')
EOF

# PITFALL 2: Not using appropriate stripe settings | 陷阱2：不使用合适的分条设置
# BAD | 不好: Default stripe for 50GB file
cp huge_file.dat $HOME/

# GOOD | 好: Set stripe first
lfs setstripe -c 8 -S 4M $HOME/huge_file.dat
cp huge_file.dat $HOME/huge_file.dat

# PITFALL 3: Running I/O-intensive operations on Lustre | 陷阱3：在 Lustre 运行 I/O 密集操作
# BAD | 不好: SQLite on Lustre
python script.py --db $HOME/database.sqlite

# GOOD | 好: Stage to scratch first
cp $HOME/database.sqlite $SCRATCH/
python script.py --db $SCRATCH/database.sqlite
cp $SCRATCH/database.sqlite $HOME/

# PITFALL 4: Forgetting to backup scratch data | 陷阱4：忘记备份 scratch 数据
# IMPORTANT: Copy results before job ends! | 重要：作业结束前复制结果！
```

---

## Queue-Storage Mapping | 队列与存储对应关系

### Critical: Pi 2.0 and Siyuan-1 Use Different Storage | 重要：Pi 2.0 和思源一号使用不同存储

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ⚠️  WARNING: Data is NOT shared between clusters!                        │
│ ⚠️  警告：数据在集群之间不互通！                                           │
│                                                                         │
│ - Pi 2.0 jobs can only access /lustre                                   │
│ - Siyuan-1 jobs can only access /dssg                                   │
│                                                                         │
│ - Pi 2.0 作业只能访问 /lustre                                             │
│ - 思源一号作业只能访问 /dssg                                               │
│                                                                         │
│ To use data on both clusters, you must transfer between them!           │
│ 要在两个集群使用数据，必须在它们之间传输！                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Queue to Storage Mapping | 队列存储映射

| Queue | Cluster | File System | Home Path |
|-------|---------|-------------|-----------|
| small | Pi 2.0 | Lustre | /lustre/home/acct-XXX/user |
| cpu | Pi 2.0 | Lustre | /lustre/home/acct-XXX/user |
| huge | Pi 2.0 | Lustre | /lustre/home/acct-XXX/user |
| 192c6t | Pi 2.0 | Lustre | /lustre/home/acct-XXX/user |
| dgx2 | AI Platform | Lustre | /lustre/home/acct-XXX/user |
| arm128c256g | ARM Platform | Lustre | /lustre/home/acct-XXX/user |
| 64c512g | Siyuan-1 | GPFS | /dssg/home/acct-XXX/user |
| a100 | Siyuan-1 | GPFS | /dssg/home/acct-XXX/user |

| 队列 | 集群 | 文件系统 | 家目录路径 |
|------|------|----------|-----------|
| small | Pi 2.0 | Lustre | /lustre/home/acct-XXX/user |
| cpu | Pi 2.0 | Lustre | /lustre/home/acct-XXX/user |
| huge | Pi 2.0 | Lustre | /lustre/home/acct-XXX/user |
| 192c6t | Pi 2.0 | Lustre | /lustre/home/acct-XXX/user |
| dgx2 | AI 平台 | Lustre | /lustre/home/acct-XXX/user |
| arm128c256g | ARM 平台 | Lustre | /lustre/home/acct-XXX/user |
| 64c512g | 思源一号 | GPFS | /dssg/home/acct-XXX/user |
| a100 | 思源一号 | GPFS | /dssg/home/acct-XXX/user |

### Inter-Cluster Data Transfer | 集群间数据传输

```bash
# Transfer from Pi 2.0 (Lustre) to Siyuan-1 (GPFS) | 从 Pi 2.0 传输到思源一号

# Step 1: Login to transfer node | 步骤1：登录传输节点
ssh user@data.hpc.sjtu.edu.cn

# Step 2: Transfer using rsync | 步骤2：使用 rsync 传输
rsync -avP /lustre/home/acct-XXX/user/project/ \
    user@sydata.hpc.sjtu.edu.cn:/dssg/home/acct-XXX/user/project/

# Or use scp for simple transfers | 或使用 scp 进行简单传输
scp -r /lustre/home/acct-XXX/user/data/ \
    user@sydata.hpc.sjtu.edu.cn:/dssg/home/acct-XXX/user/data/

# Verify transfer | 验证传输
ssh user@sydata.hpc.sjtu.edu.cn "ls -la /dssg/home/acct-XXX/user/project/"
```

---

## Data Safety | 数据安全

### Backup Strategy Overview | 备份策略概览

| Storage | Has Backup? | Has Snapshot? | Recommendation |
|---------|-------------|---------------|----------------|
| Lustre (/lustre) | NO | NO | User must backup to cold storage |
| GPFS (/dssg) | NO | NO | User must backup to cold storage |
| Scratch (/scratch) | NO | NO | Never store important data here |
| Cold Storage (/union) | NO | YES | Most reliable; can recover deleted files |

| 存储 | 有备份？ | 有快照？ | 建议 |
|------|----------|----------|------|
| Lustre (/lustre) | 无 | 无 | 用户必须备份到冷存储 |
| GPFS (/dssg) | 无 | 无 | 用户必须备份到冷存储 |
| Scratch (/scratch) | 无 | 无 | 永远不要存储重要数据 |
| 冷存储 (/union) | 无 | 有 | 最可靠；可恢复删除的文件 |

### Best Practices for Data Safety | 数据安全最佳实践

```bash
# 1. Use git for code version control | 代码使用 git 版本控制
cd $HOME/projects/my_project
git init
git add scripts/
git commit -m "Initial commit"
# Also push to remote (GitHub, GitLab) | 同时推送到远程仓库

# 2. Keep raw data immutable | 保持原始数据不变
mkdir $HOME/data/raw
chmod 444 $HOME/data/raw/*   # Read-only | 只读
# Or use cold storage for raw data | 或使用冷存储存放原始数据

# 3. Regular backup to cold storage | 定期备份到冷存储
# Create a backup script | 创建备份脚本
cat > $HOME/scripts/backup_project.sh << 'EOF'
#!/bin/bash
PROJECT=$1
DATE=$(date +%Y%m%d)

# Must run from transfer node | 必须从传输节点运行
ssh data.hpc.sjtu.edu.cn << REMOTE
  mkdir -p $UNION/backups/${PROJECT}_${DATE}
  rsync -avP --checksum \
    $HOME/projects/$PROJECT/ \
    $UNION/backups/${PROJECT}_${DATE}/
  find $UNION/backups/${PROJECT}_${DATE} -type f -exec md5sum {} \; > \
    $UNION/backups/${PROJECT}_${DATE}/CHECKSUMS.md5
REMOTE

echo "Backup complete: $UNION/backups/${PROJECT}_${DATE}"
EOF

# 4. Verify data integrity with checksums | 使用校验和验证数据完整性
# Create checksums for important data | 为重要数据创建校验和
find $HOME/data/raw -type f -exec md5sum {} \; > $HOME/data/raw.md5

# Verify later | 稍后验证
md5sum -c $HOME/data/raw.md5

# 5. Never rely solely on HPC storage | 不要仅依赖 HPC 存储
# - Keep copies on local machines | 在本地机器保留副本
# - Use institutional backup services | 使用机构备份服务
# - Consider cloud storage for critical data | 关键数据考虑云存储
```

### Data Recovery Scenarios | 数据恢复场景

| Scenario | Storage | Can Recover? | How |
|----------|---------|--------------|-----|
| Deleted file from /lustre | Lustre | **NO** | Gone forever unless you have backup |
| Deleted file from /dssg | GPFS | **NO** | Gone forever unless you have backup |
| Deleted file from /scratch | Flash | **NO** | Gone forever (and auto-cleaned anyway) |
| Deleted file from /union | 科学大数据 | **YES** ✓ | 管理员可从回收站和快照恢复 |

| 场景 | 存储 | 可恢复？ | 方法 |
|------|------|----------|------|
| 从 /lustre 删除文件 | Lustre | **否** | 永久丢失，除非有备份 |
| 从 /dssg 删除文件 | GPFS (思源一号) | **否** | 永久丢失，除非有备份 |
| 从 /scratch 删除文件 | Flash | **否** | 永久丢失（反正会自动清理） |
| 从 /union 删除文件 | 科学大数据平台 | **可以** ✓ | 发送路径至 hpc@sjtu.edu.cn，管理员可尝试从回收站和快照恢复 |

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 💡 数据安全建议                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ 1. 重要数据优先存放科学大数据平台 (/union)                                 │
│    - 有快照保护，误删可恢复                                               │
│    - 配额大 (10TB)，价格低                                               │
│                                                                         │
│ 2. 思源一号 (/dssg) 存储误删数据无法找回                                   │
│    - 仅用于活跃计算数据                                                   │
│    - 计算完成后及时归档到 /union                                          │
│                                                                         │
│ 3. 删除原始数据前，务必：                                                 │
│    - rsync 归档后使用 md5sum 验证完整性                                   │
│    - 确认副本无误后再删除                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Common Issues | 常见问题

### Issue 1: "Disk quota exceeded" | 问题1：磁盘配额超限

**Symptoms | 症状:**
- Cannot create new files | 无法创建新文件
- Write operations fail with "Disk quota exceeded" | 写操作失败并提示 "Disk quota exceeded"
- Jobs fail immediately | 作业立即失败

**Diagnosis | 诊断:**
```bash
# Check quota | 检查配额
quota -s
lfs quota -u $USER /lustre   # Lustre
mmlsquota -u $USER --block-size auto  # GPFS

# Find where space is used | 查找空间使用位置
du -sh $HOME/* | sort -hr | head -20
du -sh $HOME/projects/* | sort -hr

# Find large files | 查找大文件
find $HOME -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr

# Find files older than 30 days larger than 100MB | 查找30天前超过100MB的文件
find $HOME -type f -mtime +30 -size +100M -ls 2>/dev/null
```

**Solutions | 解决方案:**
```bash
# 1. Clean up log files | 清理日志文件
find $HOME -name "*.log" -mtime +7 -delete
find $HOME -name "slurm-*.out" -mtime +30 -delete

# 2. Remove temporary files | 删除临时文件
rm -rf $HOME/.cache/*
rm -rf $HOME/tmp/*

# 3. Move old data to cold storage | 将旧数据移到冷存储
# (See cold storage migration section)

# 4. Compress infrequently used data | 压缩不常用数据
tar -czvf old_project.tar.gz old_project/
rm -rf old_project/

# 5. Request quota increase | 申请增加配额
# Email hpc@sjtu.edu.cn with justification
```

### Issue 2: "Read-only file system" | 问题2：文件系统只读

**Symptoms | 症状:**
- All write operations fail with "Read-only file system" | 所有写操作失败并提示 "Read-only file system"
- Even `touch` command fails | 即使 `touch` 命令也失败

**Possible Causes | 可能原因:**
1. File system temporarily mounted read-only due to errors | 文件系统因错误临时以只读挂载
2. Trying to write to cold storage from login/compute nodes | 从登录/计算节点写入冷存储
3. File system maintenance | 文件系统维护中

**Solutions | 解决方案:**
```bash
# Check if it's a cold storage access issue | 检查是否是冷存储访问问题
echo $PWD   # If in /archive, /vault, /union - that's the issue

# For cold storage: must use transfer node | 冷存储：必须使用传输节点
ssh data.hpc.sjtu.edu.cn   # Then write to cold storage

# For other file systems: contact admin | 其他文件系统：联系管理员
# Email hpc@sjtu.edu.cn with:
# - Error message | 错误信息
# - File system affected | 受影响的文件系统
# - Time of occurrence | 发生时间
```

### Issue 3: Permission denied | 问题3：权限被拒绝

**Symptoms | 症状:**
- Cannot access files/directories | 无法访问文件/目录
- "Permission denied" errors | "Permission denied" 错误

**Diagnosis | 诊断:**
```bash
# Check file permissions | 检查文件权限
ls -la /path/to/file

# Check ACLs (if set) | 检查 ACL（如果设置了）
getfacl /path/to/file

# Check your groups | 检查你所属的组
id
groups
```

**Solutions | 解决方案:**
```bash
# For your own files: fix permissions | 自己的文件：修复权限
chmod 644 file       # Read for all, write for owner | 所有人可读，所有者可写
chmod 755 directory  # Access for all, modify for owner | 所有人可访问，所有者可修改

# For shared files: ask owner to grant access | 共享文件：请所有者授权
# Owner runs: | 所有者执行：
setfacl -m u:username:rx /path/to/shared/   # Grant read+execute
setfacl -R -m u:username:rx /path/to/dir/   # Recursive

# Check current ACLs | 查看当前 ACL
getfacl /path/to/shared/
```

### Issue 4: Slow I/O performance | 问题4：I/O 性能慢

**Symptoms | 症状:**
- Jobs run much slower than expected | 作业运行比预期慢得多
- High wait times for I/O operations | I/O 操作等待时间长

**Diagnosis | 诊断:**
```bash
# Check file system load | 检查文件系统负载
lfs df -h /lustre    # Lustre usage

# Check your I/O pattern | 检查你的 I/O 模式
strace -c -e trace=read,write,open your_program 2>&1 | tail -20
```

**Solutions | 解决方案:**
```bash
# 1. If many small files: use flash storage | 如果是大量小文件：使用全闪存
cp -r small_files/ $SCRATCH/
# Run computation on scratch
cp $SCRATCH/results/* $HOME/output/

# 2. If large files: use striping | 如果是大文件：使用分条
lfs setstripe -c 8 -S 4M output_directory/

# 3. Aggregate small files | 聚合小文件
# Use HDF5, Parquet, or tar archives instead of many small files

# 4. Stage data to scratch for I/O-intensive work | I/O 密集型任务数据导入 scratch
# See Flash Storage section for staging patterns
```

### Issue 5: Scratch data disappeared | 问题5：Scratch 数据丢失

**Symptoms | 症状:**
- Files in $SCRATCH are gone | $SCRATCH 中的文件消失了
- Job failed because input data not found | 作业失败因为找不到输入数据

**Causes | 原因:**
1. Automatic 3-month cleanup | 3 个月自动清理
2. Job cleanup trap removed data | 作业清理 trap 删除了数据
3. Forgot to stage data before job | 作业前忘记导入数据

**Prevention | 预防:**
```bash
# 1. Always stage data at job start | 作业开始时始终导入数据
cp $HOME/data/* $SCRATCH/job_${SLURM_JOB_ID}/

# 2. Always save results before job ends | 作业结束前始终保存结果
cp $SCRATCH/job_${SLURM_JOB_ID}/results/* $HOME/output/

# 3. NEVER store important data on scratch long-term | 永远不要在 scratch 长期存储重要数据

# 4. Check scratch usage regularly | 定期检查 scratch 使用
ls -la $SCRATCH/
find $SCRATCH -type f -mtime +60  # Files older than 60 days
```

### Issue 6: File checksum mismatch after transfer | 问题6：传输后文件校验和不匹配

**Symptoms | 症状:**
- Data corruption after transfer | 传输后数据损坏
- Analysis gives different results on HPC | 在 HPC 上分析结果不同

**Diagnosis | 诊断:**
```bash
# Generate and compare checksums | 生成并比较校验和
# Local:
md5sum local_file.dat > checksums.local

# On HPC:
md5sum remote_file.dat > checksums.remote

# Compare
diff checksums.local checksums.remote
```

**Solutions | 解决方案:**
```bash
# 1. Always use rsync with --checksum for important data | 重要数据始终使用 rsync --checksum
rsync -avP --checksum source/ dest/

# 2. Re-transfer corrupted files | 重新传输损坏的文件
rsync -avP --checksum --ignore-existing source/ dest/  # Skip existing
rsync -avP --checksum source/ dest/  # Or just re-transfer all

# 3. Verify after transfer | 传输后验证
cd source/
find . -type f -exec md5sum {} \; | sort > /tmp/source.md5
cd dest/
find . -type f -exec md5sum {} \; | sort > /tmp/dest.md5
diff /tmp/source.md5 /tmp/dest.md5
```

---

## Quick Reference Card | 快速参考卡

### Storage Summary | 存储总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SJTU HPC Storage Quick Reference                        │
│                      上海交大超算存储快速参考                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STORAGE TYPES | 存储类型                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Lustre (/lustre)  │ 25PB │ HDD    │ Pi 2.0/AI/ARM  │ 3TB free │ No backup │
│  GPFS (/dssg)      │ 10PB │ HDD    │ Siyuan-1       │ 3TB free │ No backup │
│  Flash (/scratch)  │108TB │ NVMe   │ Pi 2.0         │ Free     │ 3-mo clean│
│  Cold (/union)     │ 40PB │ HDD    │ Transfer nodes │ Paid     │ Snapshots │
│                                                                             │
│  ENVIRONMENT VARIABLES | 环境变量                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  $HOME     → Main storage (Lustre or GPFS) | 主存储                         │
│  $SCRATCH  → Flash temp storage | 全闪存临时                                │
│  $UNION    → Cold storage (merged view) | 冷存储（合并视图）                  │
│                                                                             │
│  CLUSTER → STORAGE MAPPING | 集群存储映射                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Pi 2.0 queues (small, cpu, huge, 192c6t, dgx2, arm) → /lustre              │
│  Siyuan-1 queues (64c512g, a100)                     → /dssg                │
│  ⚠️  Data NOT shared between clusters! | 集群间数据不互通！                    │
│                                                                             │
│  COMMON COMMANDS | 常用命令                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Check quota:       quota -s                                                │
│  Lustre quota:      lfs quota -u $USER /lustre                              │
│  GPFS quota:        mmlsquota -u $USER --block-size auto                    │
│  Disk usage:        du -sh $HOME/*                                          │
│  Large files:       find $HOME -size +100M -ls                              │
│  Stripe settings:   lfs getstripe filename                                  │
│  Set stripe:        lfs setstripe -c 4 -S 4M directory/                     │
│                                                                             │
│  BEST PRACTICES | 最佳实践                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  ✓ Use $SCRATCH for I/O-intensive temporary data                           │
│  ✓ Use striping for large files on Lustre                                  │
│  ✓ Backup important data to cold storage ($UNION)                          │
│  ✓ Use checksums to verify data integrity                                  │
│  ✓ Clean up $SCRATCH after jobs complete                                   │
│  ✓ Stage data in/out when using $SCRATCH                                   │
│  ✗ Don't create millions of small files on Lustre/GPFS                     │
│  ✗ Don't store important data only on $SCRATCH                             │
│  ✗ Don't rely on HPC storage as your only backup                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Decision Tree | 决策树

```
Which storage should I use? | 我应该使用哪个存储？

┌─────────────────────────────────────────────────────────────────┐
│                        Is it temporary?                         │
│                        是临时数据吗？                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
             YES                          NO
              │                           │
              ↓                           ↓
┌─────────────────────────┐   ┌─────────────────────────┐
│ Is it I/O intensive?    │   │ Is it historical/rare?  │
│ 是否 I/O 密集？          │   │ 是历史数据/很少访问？     │
└───────────┬─────────────┘   └───────────┬─────────────┘
            │                             │
    ┌───────┴───────┐             ┌───────┴───────┐
   YES             NO            YES             NO
    │               │              │               │
    ↓               ↓              ↓               ↓
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│ $SCRATCH  │ │ $HOME tmp │ │ $UNION    │ │ $HOME     │
│ 全闪存     │ │ 临时目录   │ │ 冷存储     │ │ 主目录     │
│           │ │           │ │           │ │           │
│ Fast NVMe │ │ Lustre/   │ │ Cold      │ │ Lustre/   │
│ Auto-clean│ │ GPFS      │ │ Snapshots │ │ GPFS      │
└───────────┘ └───────────┘ └───────────┘ └───────────┘
```

---

## 相关文档 | Related Documentation

- **数据传输方法**: [data.md](data.md) - rsync, scp, SFTP, 集群间同步
- **故障排查**: [troubleshooting.md](troubleshooting.md) - 配额问题、传输问题、数据恢复
- **队列信息**: [queues.md](queues.md) - 各队列对应的存储系统
- **实用脚本**: 参见 `scripts/` 目录
  - `quota_check.sh` - 配额监控脚本
  - `backup_to_union.sh` - 归档到科学大数据平台
  - `cost_estimate.py` - 成本计算器

---

*Last updated | 最后更新: 2026-01*
*Reference: SJTU HPC Documentation*
