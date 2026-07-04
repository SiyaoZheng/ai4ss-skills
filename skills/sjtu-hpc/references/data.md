# SJTU HPC Data Management Reference
# 上海交大超算数据管理参考手册

> 数据传输与同步指南。存储系统详情请参阅 [storage.md](storage.md)。
> Data transfer and synchronization guide. For storage details, see [storage.md](storage.md).

---

## Table of Contents | 目录

1. [Quick Reference | 快速参考](#quick-reference--快速参考)
2. [Data Transfer | 数据传输](#data-transfer--数据传输)
3. [Data Sharing | 数据共享](#data-sharing--数据共享)
4. [Remote Mount | 远程挂载](#remote-mount--远程挂载-sshfs)
5. [CSS Workflows | 计算社会科学工作流程](#css-workflows--计算社会科学工作流程)
6. [Common Issues | 常见问题](#common-issues--常见问题)

---

## Quick Reference | 快速参考

### Storage Overview | 存储概览

> 详细存储架构、配额、性能特性请参阅 [storage.md](storage.md)。

| 环境变量 | 用途 | 关键点 |
|----------|------|--------|
| `$HOME` | 主存储 (Lustre/GPFS) | 免费配额 3-5TB |
| `$SCRATCH` | 快速临时存储 | 3个月自动清理，无备份 |
| `$UNION` | 冷存储 (科学大数据平台) | 支持快照恢复，推荐归档 |

### Transfer Nodes | 传输节点

| 集群 | 传输节点 | 用途 |
|------|----------|------|
| Pi 2.0/AI/ARM | `data.hpc.sjtu.edu.cn` | Lustre (/lustre) 读写 |
| Siyuan-1 | `sydata.hpc.sjtu.edu.cn` | GPFS (/dssg) 读写 |

**重要**: 大批量数据传输必须使用传输节点，禁止在登录节点传输！

---

## Data Transfer | 数据传输

### Transfer Nodes | 传输节点

| Cluster | Transfer Node | Use Case |
|---------|---------------|----------|
| Siyuan-1 | sydata.hpc.sjtu.edu.cn | GPFS (/dssg) access |
| Pi 2.0/AI/ARM | data.hpc.sjtu.edu.cn | Lustre (/lustre) access |

> **IMPORTANT**: Always use transfer nodes for data transfer, not login nodes.
> **重要**：始终使用传输节点进行数据传输，不要使用登录节点。

### SCP - Simple Copy | SCP 简单复制

```bash
# Upload to Siyuan | 上传到思源
scp -r local_data/ user@sydata.hpc.sjtu.edu.cn:/dssg/home/acct-XXX/user/

# Upload to Pi 2.0 | 上传到 Pi 2.0
scp -r local_data/ user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/

# Download from Siyuan | 从思源下载
scp -r user@sydata.hpc.sjtu.edu.cn:/dssg/home/acct-XXX/user/results/ ./

# Download from Pi 2.0 | 从 Pi 2.0 下载
scp -r user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/results/ ./

# With compression for text data | 对文本数据使用压缩
scp -C -r survey_responses/ user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/
```

### Rsync - Incremental Transfer (Recommended) | Rsync 增量传输（推荐）

```bash
# Basic incremental upload | 基本增量上传
rsync -avP --partial source/ user@sydata.hpc.sjtu.edu.cn:/dssg/home/acct-XXX/user/dest/

# Explanation of flags | 参数说明:
# -a: archive mode (preserves permissions, timestamps) | 归档模式（保留权限、时间戳）
# -v: verbose | 详细输出
# -P: show progress + allow resume | 显示进度 + 允许断点续传
# --partial: keep partially transferred files | 保留部分传输的文件

# Exclude patterns (useful for CSS projects) | 排除模式（对CSS项目有用）
rsync -avP --partial \
    --exclude='*.log' \
    --exclude='.Rhistory' \
    --exclude='__pycache__/' \
    --exclude='.ipynb_checkpoints/' \
    source/ user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/project/

# Sync and delete removed files (mirror) | 同步并删除已移除文件（镜像）
rsync -avP --delete source/ user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/dest/

# Dry run first (recommended) | 先试运行（推荐）
rsync -avP --dry-run source/ user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/dest/
```

### Parallel Transfer for Large Datasets | 大数据集并发传输

```bash
# Step 1: Generate file list | 步骤1：生成文件列表
ssh user@data.hpc.sjtu.edu.cn 'ls /lustre/home/acct-XXX/user/data/' > list.txt

# Step 2: Download with 5 parallel processes | 步骤2：5进程并发下载
cat list.txt | xargs -P 5 -I {} rsync -avP \
    user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/data/{} ./download/

# For uploading many files in parallel | 并发上传多个文件
ls local_data/ | xargs -P 5 -I {} rsync -avP \
    local_data/{} user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/remote_data/

# Using GNU parallel (more control) | 使用 GNU parallel（更多控制）
parallel -j 5 rsync -avP {} user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/dest/ \
    ::: source_dir/*
```

### Inter-Cluster Transfer | 集群间传输

**前提：data 节点之间需要证书认证。** HPC 使用 CA 签发的证书（`CertificateFile`），
普通 `ssh-keygen` 生成的 pubkey 可能会被拒绝（`refuse user without password`）。

不要把长期私钥随手复制到共享或长期运行的节点。优先使用官方数据传输节点、
管理员提供的跨集群传输方式，或为传输单独签发短期凭据。确实需要在发起传输的
data 节点上放置凭据时，只放置专用短期 key/cert，限制权限，并在传输结束后删除。

```bash
# === 一次性设置：在发起传输的 data 节点上放置专用短期凭据 ===
# Setup: place a dedicated short-lived transfer key+cert on the initiating data node

# 思源 → PI 方向：专用短期凭据放 sydata
scp ~/.ssh/sjtu_transfer_ed25519 ~/.ssh/sjtu_transfer_ed25519-cert.pub hpc-data:~/.ssh/
ssh hpc-data 'chmod 600 ~/.ssh/sjtu_transfer_ed25519 ~/.ssh/sjtu_transfer_ed25519-cert.pub'

# PI → 思源 方向：专用短期凭据放 PI data node
scp ~/.ssh/sjtu_transfer_ed25519 ~/.ssh/sjtu_transfer_ed25519-cert.pub pi-data:~/.ssh/
ssh pi-data 'chmod 600 ~/.ssh/sjtu_transfer_ed25519 ~/.ssh/sjtu_transfer_ed25519-cert.pub'

# 验证 | Verify
ssh hpc-data 'ssh data.hpc.sjtu.edu.cn hostname'   # → data.pi.sjtu.edu.cn
ssh pi-data 'ssh sydata.hpc.sjtu.edu.cn hostname'   # → sydata.pi.sjtu.edu.cn
```

```bash
# === 传输数据 | Transfer data ===

# Siyuan → PI (从 sydata 推到 PI data node)
ssh hpc-data 'rsync -avP /dssg/home/acct-XXX/user/file \
    user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/'

# PI → Siyuan (从 PI data node 推到 sydata)
ssh pi-data 'rsync -avP /lustre/home/acct-XXX/user/file \
    user@sydata.hpc.sjtu.edu.cn:/dssg/home/acct-XXX/user/'

# 并行传多个文件 | Parallel transfer
ssh hpc-data 'rsync -avP file1 user@data.hpc.sjtu.edu.cn:/path/ &
rsync -avP file2 user@data.hpc.sjtu.edu.cn:/path/ &
wait'
```

**注意：** 证书有有效期，过期需重新签发。检查：`ssh-keygen -L -f ~/.ssh/sjtu_transfer_ed25519-cert.pub`。
传输完成后删除 data 节点上的专用短期凭据。

### Transfer Verification | 传输校验

```bash
# Generate checksums before transfer | 传输前生成校验和
find source_dir -type f -exec md5sum {} \; > checksums.md5

# Transfer checksums file | 传输校验和文件
rsync -avP checksums.md5 user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/dest/

# Verify after transfer (on HPC) | 传输后验证（在HPC上）
cd /lustre/home/acct-XXX/user/dest/
md5sum -c checksums.md5

# For large datasets, use md5deep | 大数据集使用 md5deep
md5deep -r source_dir > checksums.txt
```

---

> **Flash 存储与冷存储详情**：请参阅 [storage.md](storage.md#flash-storage--全闪存文件系统) 获取完整的存储系统说明。
> **Flash & Cold Storage Details**: See [storage.md](storage.md#flash-storage--全闪存文件系统) for complete storage system documentation.

---

## Data Sharing | 数据共享

### Within Research Group | 课题组内部共享

```bash
# Request shared folder from admin | 向管理员申请共享文件夹
# Location: /lustre/share/acct-XXX/ or /dssg/share/acct-XXX/

# Create symlink for convenience | 创建软链接方便访问
ln -s /lustre/share/acct-XXX/ $HOME/shared

# Set permissions for group members | 设置组成员权限
chmod 770 /lustre/share/acct-XXX/shared_data/
chgrp -R acct-XXX /lustre/share/acct-XXX/shared_data/
```

### Cross-Group Sharing with ACL | 跨课题组 ACL 共享

```bash
# Grant read access to specific user | 授予特定用户读权限
setfacl -R -m u:other_user:rx /lustre/home/acct-XXX/user/shared_project/

# Grant read access to a group | 授予组读权限
setfacl -R -m g:acct-YYY:rx /lustre/home/acct-XXX/user/shared_project/

# Make new files inherit ACL | 使新文件继承ACL
setfacl -R -d -m u:other_user:rx /lustre/home/acct-XXX/user/shared_project/

# Check current ACL | 查看当前ACL
getfacl /lustre/home/acct-XXX/user/shared_project/

# Remove ACL | 移除ACL
setfacl -R -b /lustre/home/acct-XXX/user/shared_project/
```

### External Sharing | 对外共享

For sharing data outside the HPC cluster:
对于集群外部共享数据：

- **Platform**: scidata.sjtu.edu.cn
- **平台**：scidata.sjtu.edu.cn
- Contact HPC admin for access and instructions
- 联系 HPC 管理员获取访问权限和说明

---

## Remote Mount | 远程挂载 (SSHFS)

### macOS Setup | macOS 配置

```bash
# Install macFUSE and SSHFS | 安装 macFUSE 和 SSHFS
brew install --cask macfuse
brew install sshfs

# Create mount point | 创建挂载点
mkdir -p ~/mnt/hpc_home
mkdir -p ~/mnt/hpc_scratch

# Mount home directory | 挂载家目录
sshfs user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user ~/mnt/hpc_home \
    -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3

# Mount scratch | 挂载scratch
sshfs user@data.hpc.sjtu.edu.cn:/scratch/acct-XXX/user ~/mnt/hpc_scratch \
    -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3

# Unmount | 卸载
umount ~/mnt/hpc_home
# or if busy | 或者如果忙碌
diskutil unmount force ~/mnt/hpc_home
```

### Linux Setup | Linux 配置

```bash
# Install SSHFS | 安装 SSHFS
sudo apt install sshfs  # Debian/Ubuntu
sudo yum install fuse-sshfs  # CentOS/RHEL

# Mount | 挂载
mkdir -p ~/mnt/hpc
sshfs user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user ~/mnt/hpc \
    -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3

# Unmount | 卸载
fusermount -u ~/mnt/hpc
```

### Persistent Mount (fstab) | 持久化挂载

```bash
# Add to /etc/fstab (Linux) | 添加到 /etc/fstab (Linux)
user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user /home/localuser/mnt/hpc fuse.sshfs \
    noauto,x-systemd.automount,_netdev,reconnect,identityfile=/home/localuser/.ssh/sjtu_hpc_ed25519,\
    allow_other,default_permissions,ServerAliveInterval=15,ServerAliveCountMax=3 0 0
```

### SSHFS Performance Tips | SSHFS 性能提示

```bash
# For better performance with many small files | 提高小文件性能
sshfs user@data.hpc.sjtu.edu.cn:/path ~/mnt/hpc \
    -o reconnect,ServerAliveInterval=15 \
    -o cache=yes,kernel_cache,compression=no \
    -o Ciphers=aes128-ctr

# Note: SSHFS is for convenience, not for high-performance I/O
# 注意：SSHFS 是为方便使用，不是为高性能I/O
# For intensive work, use proper data transfer methods
# 对于密集型工作，使用正确的数据传输方法
```

---

## CSS Workflows | 计算社会科学工作流程

### Workflow 1: Survey Data Analysis | 工作流程1：调查数据分析

```bash
# === LOCAL MACHINE | 本地机器 ===

# 1. Prepare data locally | 本地准备数据
cd ~/research/survey_project
ls data/
# survey_raw.csv (500MB)
# codebook.xlsx

# 2. Upload to HPC | 上传到HPC
rsync -avP data/ user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/survey_project/data/

# 3. Upload scripts | 上传脚本
rsync -avP scripts/ user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/survey_project/scripts/

# === ON HPC | 在HPC上 ===

# 4. Submit job | 提交作业
ssh user@login.hpc.sjtu.edu.cn
cd $HOME/survey_project
sbatch scripts/run_analysis.slurm

# 5. Monitor | 监控
squeue -u $USER

# === LOCAL MACHINE | 本地机器 ===

# 6. Download results | 下载结果
rsync -avP user@data.hpc.sjtu.edu.cn:/lustre/home/acct-XXX/user/survey_project/results/ ./results/
```

### Workflow 2: Social Network Analysis (Large Graph) | 工作流程2：社交网络分析（大图）

```bash
# === ON HPC | 在HPC上 ===

# This workflow uses flash storage for performance
# 此工作流程使用全闪存提高性能

#!/bin/bash
#SBATCH --job-name=network_analysis
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=40
#SBATCH --time=24:00:00

# Setup working directory in scratch | 在scratch中设置工作目录
export WORK=$SCRATCH/network_${SLURM_JOB_ID}
mkdir -p $WORK
cd $WORK

# Copy data to fast storage | 复制数据到快速存储
echo "Copying data to scratch..."
cp $HOME/network_project/data/edges.csv ./
cp $HOME/network_project/data/nodes.csv ./

# Load modules | 加载模块
module load python/3.9

# Run analysis | 运行分析
python $HOME/network_project/scripts/community_detection.py \
    --edges edges.csv \
    --nodes nodes.csv \
    --output results/

# Copy results back | 复制结果回home
cp -r results/ $HOME/network_project/

# Cleanup | 清理
rm -rf $WORK
```

### Workflow 3: Text Mining with Large Corpus | 工作流程3：大规模语料文本挖掘

```bash
# === Parallel processing of many text files | 并行处理大量文本文件 ===

#!/bin/bash
#SBATCH --job-name=text_mining
#SBATCH --partition=cpu
#SBATCH --array=1-100  # Process 100 chunks | 处理100个分块

# Each array task processes a subset | 每个数组任务处理一个子集
CHUNK_ID=$SLURM_ARRAY_TASK_ID
INPUT_DIR=$HOME/text_project/data/chunks
OUTPUT_DIR=$HOME/text_project/results

# Process this chunk | 处理此分块
python $HOME/text_project/scripts/process_chunk.py \
    --input $INPUT_DIR/chunk_${CHUNK_ID}.txt \
    --output $OUTPUT_DIR/result_${CHUNK_ID}.json

# === After all jobs complete | 所有作业完成后 ===
# Merge results locally | 本地合并结果
python scripts/merge_results.py results/*.json > final_results.json
```

### Workflow 4: Machine Learning with Checkpoints | 工作流程4：带检查点的机器学习

```bash
#!/bin/bash
#SBATCH --job-name=bert_finetune
#SBATCH --partition=dgx2
#SBATCH --gres=gpu:1
#SBATCH --time=48:00:00

# Use scratch for checkpoints (fast I/O) | 使用scratch保存检查点（快速I/O）
export CHECKPOINT_DIR=$SCRATCH/checkpoints_${SLURM_JOB_ID}
mkdir -p $CHECKPOINT_DIR

# Home for final model | Home保存最终模型
export MODEL_DIR=$HOME/ml_project/models

# Run training | 运行训练
python train_bert.py \
    --data $HOME/ml_project/data/train.csv \
    --checkpoint-dir $CHECKPOINT_DIR \
    --save-every 1000 \
    --final-model $MODEL_DIR/bert_finetuned.pt

# Copy best checkpoint to home | 复制最佳检查点到home
cp $CHECKPOINT_DIR/best_model.pt $MODEL_DIR/
rm -rf $CHECKPOINT_DIR
```

### Data Backup Strategy for CSS Projects | CSS项目数据备份策略

```bash
# Weekly backup script | 每周备份脚本
#!/bin/bash

PROJECT=$HOME/projects/my_css_project
ARCHIVE=$UNION/backups/my_css_project_$(date +%Y%m%d)

# Create backup | 创建备份
mkdir -p $ARCHIVE

# Backup code and small data | 备份代码和小数据
rsync -avP --checksum $PROJECT/scripts/ $ARCHIVE/scripts/
rsync -avP --checksum $PROJECT/data/processed/ $ARCHIVE/data/processed/

# Generate file manifest | 生成文件清单
find $PROJECT -type f -exec md5sum {} \; > $ARCHIVE/manifest.md5

# Log backup | 记录备份
echo "Backup completed: $(date)" >> $ARCHIVE/backup.log
echo "Size: $(du -sh $ARCHIVE | cut -f1)" >> $ARCHIVE/backup.log
```

---

## Common Issues | 常见问题

### Q1: "Disk quota exceeded" | 磁盘配额超限

```bash
# Check your quota | 检查配额
quota -s
# or | 或者
lfs quota -u $USER /lustre  # For Lustre
mmrepquota -u $USER /dssg   # For GPFS

# Find large files | 查找大文件
du -sh $HOME/* | sort -hr | head -20

# Find files older than 30 days | 查找30天前的文件
find $HOME -type f -mtime +30 -size +100M -ls

# Solutions | 解决方案:
# 1. Move old data to cold storage | 将旧数据移到冷存储
# 2. Clean up log files | 清理日志文件
# 3. Remove temporary files | 删除临时文件
# 4. Request quota increase (contact admin) | 申请增加配额（联系管理员）
```

### Q2: Transfer speed too slow | 传输速度太慢

```bash
# Use compression for text data | 对文本数据使用压缩
rsync -avPz source/ dest/

# Use parallel transfers | 使用并发传输
cat file_list.txt | xargs -P 10 -I {} rsync -avP {} dest/

# Check if using correct transfer node | 检查是否使用正确的传输节点
# WRONG: scp to login.hpc.sjtu.edu.cn | 错误
# RIGHT: scp to data.hpc.sjtu.edu.cn  | 正确

# For very large datasets, consider shipping hard drives
# 对于超大数据集，考虑邮寄硬盘
```

### Q3: "No space left on device" in $SCRATCH | $SCRATCH 空间不足

```bash
# Check scratch usage | 检查scratch使用情况
df -h $SCRATCH

# Clean up your scratch | 清理你的scratch
rm -rf $SCRATCH/old_job_*

# Note: Scratch is shared and auto-cleaned every 3 months
# 注意：Scratch是共享的，每3个月自动清理
```

### Q4: Permission denied when accessing shared data | 访问共享数据权限被拒绝

```bash
# Check file permissions | 检查文件权限
ls -la /path/to/shared/data

# Check ACL | 检查ACL
getfacl /path/to/shared/data

# Ask data owner to grant access | 让数据所有者授权
# Data owner runs: | 数据所有者执行：
setfacl -R -m u:your_username:rx /path/to/shared/data
```

### Q5: Data corruption after transfer | 传输后数据损坏

```bash
# Always verify with checksums | 始终用校验和验证
# Before transfer | 传输前
md5sum source_file > checksum.md5

# After transfer | 传输后
md5sum -c checksum.md5

# For directories | 对于目录
md5deep -r source_dir/ > checksums.txt
# After transfer | 传输后
cd dest_dir/
md5sum -c ../checksums.txt

# If corruption found, re-transfer | 如发现损坏，重新传输
rsync -avP --checksum source/ dest/
```

### Q6: How to resume interrupted transfer | 如何恢复中断的传输

```bash
# rsync automatically resumes with --partial | rsync使用--partial自动恢复
rsync -avP --partial source/ user@data.hpc.sjtu.edu.cn:/path/dest/

# For scp, use rsync instead | 对于scp，改用rsync
# scp cannot resume; rsync can | scp不能恢复；rsync可以
```

### Q7: SSHFS mount fails or disconnects | SSHFS挂载失败或断开

```bash
# Debug mode | 调试模式
sshfs -o debug user@host:/path ~/mnt/hpc

# Common fixes | 常见修复：
# 1. Check SSH key authentication | 检查SSH密钥认证
ssh -v user@data.hpc.sjtu.edu.cn

# 2. Use reconnect option | 使用reconnect选项
sshfs user@host:/path ~/mnt/hpc -o reconnect,ServerAliveInterval=15

# 3. Force unmount if stuck | 如果卡住强制卸载
# macOS
diskutil unmount force ~/mnt/hpc
# Linux
fusermount -uz ~/mnt/hpc
```

### Q8: How to check data integrity across time | 如何检查数据随时间的完整性

```bash
# Create baseline checksums | 创建基线校验和
md5deep -r $HOME/important_data/ > $HOME/.checksums/important_data_$(date +%Y%m%d).md5

# Later, verify nothing changed | 稍后验证没有变化
md5deep -r $HOME/important_data/ | diff - $HOME/.checksums/important_data_YYYYMMDD.md5

# For CSS raw data (should never change) | 对于CSS原始数据（不应改变）
# Store checksums with the data | 将校验和与数据一起存储
echo "Checksum generated: $(date)" > $HOME/data/raw/CHECKSUMS.md5
md5deep -r $HOME/data/raw/ >> $HOME/data/raw/CHECKSUMS.md5
```

---

## Quick Reference Card | 快速参考卡

```
STORAGE PATHS | 存储路径
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
$HOME      → Main storage (3TB free) | 主存储
$SCRATCH   → Fast temp (auto-clean) | 快速临时
$UNION     → Cold archive (paid)    | 冷归档

TRANSFER NODES | 传输节点
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pi 2.0     → data.hpc.sjtu.edu.cn
Siyuan     → sydata.hpc.sjtu.edu.cn

COMMON COMMANDS | 常用命令
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Upload:     rsync -avP local/ user@data:remote/
Download:   rsync -avP user@data:remote/ local/
Verify:     md5sum -c checksums.md5
Quota:      quota -s
Mount:      sshfs user@data:/path ~/mnt/hpc

BEST PRACTICES | 最佳实践
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Always use transfer nodes
✓ Always verify with checksums
✓ Use rsync for large transfers
✓ Backup important data to $UNION
✓ Clean $SCRATCH after jobs
✓ Use parallel transfers for many files
```

---

*Last updated | 最后更新: 2025-01*
*Reference: SJTU HPC Documentation*
