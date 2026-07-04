# Slurm Commands Complete Reference | Slurm 命令完全参考手册

> 本文档涵盖 Slurm 工作负载管理器的所有常用命令和参数，适用于 SJTU HPC 集群。
> This document covers all commonly used Slurm commands and parameters for the SJTU HPC cluster.

---

## 目录 | Table of Contents

1. [常用命令速查 | Quick Reference](#常用命令速查--quick-reference)
2. [sbatch 提交作业 | Job Submission](#sbatch-提交作业--job-submission)
3. [squeue 查看作业 | Job Queue](#squeue-查看作业--job-queue)
4. [scancel 取消作业 | Cancel Jobs](#scancel-取消作业--cancel-jobs)
5. [sinfo 集群状态 | Cluster Status](#sinfo-集群状态--cluster-status)
6. [sacct 历史记录 | Job History](#sacct-历史记录--job-history)
7. [scontrol 作业控制 | Job Control](#scontrol-作业控制--job-control)
8. [srun 交互运行 | Interactive Execution](#srun-交互运行--interactive-execution)
9. [salloc 资源申请 | Resource Allocation](#salloc-资源申请--resource-allocation)
10. [环境变量 | Environment Variables](#环境变量--environment-variables)
11. [作业脚本模板 | Job Script Templates](#作业脚本模板--job-script-templates)
12. [高级用法 | Advanced Usage](#高级用法--advanced-usage)

---

## 常用命令速查 | Quick Reference

| 命令 Command | 功能 Function | 常用示例 Example |
|-------------|---------------|------------------|
| `sbatch` | 提交批处理作业 Submit batch job | `sbatch job.slurm` |
| `squeue` | 查看排队/运行作业 View job queue | `squeue -u $USER` |
| `scancel` | 取消作业 Cancel job | `scancel 12345` |
| `sinfo` | 查看集群状态 View cluster status | `sinfo -p cpu` |
| `sacct` | 查看已完成作业 View completed jobs | `sacct -j 12345` |
| `scontrol` | 查看/修改作业参数 View/modify job | `scontrol show job 12345` |
| `srun` | 交互式运行命令 Interactive execution | `srun -n 4 ./a.out` |
| `salloc` | 申请资源分配 Allocate resources | `salloc -N 1 -n 40` |
| `sprio` | 查看作业优先级 View job priority | `sprio -u $USER` |
| `sstat` | 查看运行中作业统计 Running job stats | `sstat -j 12345` |
| `sreport` | 生成使用报告 Generate reports | `sreport cluster utilization` |

---

## sbatch 提交作业 | Job Submission

### 基本用法 | Basic Usage

```bash
sbatch script.slurm           # 提交作业脚本
sbatch --parsable script.slurm  # 仅输出作业ID（适合脚本使用）
```

### 完整参数表 | Complete Parameter Reference

#### 资源配置 | Resource Configuration

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `-n, --ntasks` | 总进程/任务数 Total tasks | `-n 40` |
| `-N, --nodes` | 节点数 Number of nodes | `-N 2` |
| `--ntasks-per-node` | 每节点进程数 Tasks per node | `--ntasks-per-node=40` |
| `-c, --cpus-per-task` | 每进程CPU核数 CPUs per task | `-c 4` (常用于OpenMP) |
| `--mem` | 每节点内存 Memory per node | `--mem=100G` |
| `--mem-per-cpu` | 每CPU内存 Memory per CPU | `--mem-per-cpu=4G` |
| `--mem-per-gpu` | 每GPU内存 Memory per GPU | `--mem-per-gpu=32G` |
| `--gres` | 通用资源(GPU等) Generic resources | `--gres=gpu:2` |
| `--gpus` | GPU数量（新语法） GPU count | `--gpus=4` |
| `--gpus-per-node` | 每节点GPU数 GPUs per node | `--gpus-per-node=2` |
| `--gpus-per-task` | 每任务GPU数 GPUs per task | `--gpus-per-task=1` |
| `--exclusive` | 独占节点 Exclusive node | `--exclusive` |
| `--overcommit` | 允许超额分配 Allow overcommit | `--overcommit` |

#### 队列与时间 | Partition and Time

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `-p, --partition` | 队列/分区名 Partition name | `-p small` |
| `--qos` | 服务质量等级 Quality of Service | `--qos=debug` |
| `-t, --time` | 最大运行时间 Time limit | `--time=7-00:00:00` |
| `--time-min` | 最小运行时间 Minimum time | `--time-min=1:00:00` |
| `--deadline` | 截止时间 Deadline | `--deadline=2024-12-31T23:59:59` |

**时间格式 Time Formats:**
- `minutes` - 分钟
- `minutes:seconds` - 分:秒
- `hours:minutes:seconds` - 时:分:秒
- `days-hours` - 天-时
- `days-hours:minutes` - 天-时:分
- `days-hours:minutes:seconds` - 天-时:分:秒

#### 作业标识 | Job Identification

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `-J, --job-name` | 作业名称 Job name | `-J my_simulation` |
| `-o, --output` | 标准输出文件 Output file | `-o %j.out` |
| `-e, --error` | 标准错误文件 Error file | `-e %j.err` |
| `-D, --chdir` | 工作目录 Working directory | `-D /path/to/dir` |
| `--comment` | 作业注释 Job comment | `--comment="test run"` |

**输出文件名变量 Output Filename Variables:**
- `%j` - 作业ID Job ID
- `%J` - 作业ID.步骤ID Job ID.step ID
- `%N` - 节点名 Node name
- `%n` - 节点序号 Node index
- `%A` - 序列作业主ID Array job ID
- `%a` - 序列作业任务ID Array task ID
- `%u` - 用户名 Username
- `%x` - 作业名 Job name

#### 节点选择 | Node Selection

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `-w, --nodelist` | 指定节点 Specific nodes | `-w cas001,cas002` |
| `-x, --exclude` | 排除节点 Exclude nodes | `-x cas003` |
| `--contiguous` | 要求连续节点 Contiguous nodes | `--contiguous` |
| `-C, --constraint` | 节点特性约束 Node constraints | `-C "intel&avx2"` |
| `--switches` | 交换机数量限制 Switch count | `--switches=1@00:30:00` |
| `--prefer` | 优先特性（软约束） Preferred features | `--prefer=gpu` |

#### 通知与依赖 | Notifications and Dependencies

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `--mail-type` | 邮件通知类型 Mail notification | `--mail-type=END,FAIL` |
| `--mail-user` | 邮箱地址 Email address | `--mail-user=user@sjtu.edu.cn` |
| `-d, --dependency` | 作业依赖 Job dependency | `-d afterok:12345` |
| `--kill-on-invalid-dep` | 依赖无效时取消 Kill if dep invalid | `--kill-on-invalid-dep=yes` |

**邮件通知类型 Mail Types:**
- `BEGIN` - 作业开始
- `END` - 作业结束
- `FAIL` - 作业失败
- `REQUEUE` - 作业重新排队
- `ALL` - 所有事件
- `TIME_LIMIT_90` - 时间达到90%时
- `ARRAY_TASKS` - 每个序列任务都通知

**依赖类型 Dependency Types:**
- `after:jobid` - 指定作业开始后
- `afterany:jobid` - 指定作业结束后（任意状态）
- `afterok:jobid` - 指定作业成功完成后
- `afternotok:jobid` - 指定作业失败后
- `aftercorr:jobid` - 对应序列任务完成后
- `singleton` - 同名作业同时只运行一个

```bash
# 依赖示例 Dependency examples
sbatch -d afterok:12345 job2.slurm           # job2 在 12345 成功后运行
sbatch -d afterok:12345:12346 job3.slurm     # job3 在两个作业都成功后运行
sbatch -d singleton job.slurm                 # 同名作业串行执行
```

#### 序列作业 | Array Jobs

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `-a, --array` | 序列作业索引 Array indices | `--array=1-100` |

**序列作业格式 Array Formats:**
```bash
--array=0-15           # 索引 0 到 15
--array=1,3,5,7        # 特定索引
--array=1-100:2        # 步长为2 (1,3,5,...,99)
--array=1-1000%50      # 最多同时运行50个
--array=1-100%10       # 100个任务，同时运行不超过10个
```

#### 账户与优先级 | Account and Priority

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `-A, --account` | 账户/项目 Account | `-A my_project` |
| `--reservation` | 预留资源 Reservation | `--reservation=workshop` |
| `--priority` | 优先级调整 Priority | `--priority=high` |
| `--nice` | 优先级偏移 Nice value | `--nice=100` |
| `--hold` | 提交后暂停 Submit on hold | `--hold` |

#### 高级选项 | Advanced Options

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `--requeue` | 允许重新排队 Allow requeue | `--requeue` |
| `--no-requeue` | 禁止重新排队 No requeue | `--no-requeue` |
| `--signal` | 超时前发信号 Signal before timeout | `--signal=USR1@60` |
| `--wait` | 等待作业完成 Wait for completion | `--wait` |
| `--wrap` | 包装命令 Wrap command | `--wrap="echo hello"` |
| `--test-only` | 测试不提交 Test only | `--test-only` |
| `--export` | 环境变量导出 Export variables | `--export=ALL` |
| `--get-user-env` | 获取用户环境 Get user env | `--get-user-env` |
| `--propagate` | 传递资源限制 Propagate limits | `--propagate=ALL` |

---

## squeue 查看作业 | Job Queue

### 基本用法 | Basic Usage

```bash
squeue                      # 查看所有作业
squeue -u $USER             # 查看自己的作业
squeue -u user1,user2       # 查看多个用户的作业
squeue -j 12345             # 查看特定作业
squeue -j 12345,12346       # 查看多个作业
squeue -p small             # 查看特定队列
squeue -A my_account        # 查看特定账户
```

### 完整参数表 | Complete Parameters

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `-u, --user` | 按用户筛选 Filter by user | `-u $USER` |
| `-j, --jobs` | 按作业ID筛选 Filter by job ID | `-j 12345` |
| `-p, --partition` | 按队列筛选 Filter by partition | `-p cpu,gpu` |
| `-A, --account` | 按账户筛选 Filter by account | `-A project1` |
| `-t, --states` | 按状态筛选 Filter by state | `-t PENDING,RUNNING` |
| `-n, --name` | 按作业名筛选 Filter by name | `-n my_job` |
| `-w, --nodelist` | 按节点筛选 Filter by node | `-w cas001` |
| `-l, --long` | 详细输出 Long format | `-l` |
| `-r, --array` | 显示序列作业详情 Show array details | `-r` |
| `--start` | 显示预计开始时间 Show start time | `--start` |
| `-i, --iterate` | 定时刷新 Auto refresh | `-i 5` (每5秒) |
| `--noheader` | 不显示表头 No header | `--noheader` |
| `-o, --format` | 自定义输出格式 Custom format | `-o "%.18i %.9P %.8j"` |
| `-O, --Format` | 长格式字段 Long format fields | `-O jobid,name,state` |
| `-S, --sort` | 排序字段 Sort field | `-S +i` (按ID升序) |

### 作业状态 | Job States

| 状态 State | 代码 Code | 说明 Description |
|-----------|-----------|------------------|
| `PENDING` | `PD` | 排队等待中 Waiting in queue |
| `RUNNING` | `R` | 运行中 Running |
| `COMPLETING` | `CG` | 正在完成 Completing |
| `COMPLETED` | `CD` | 已完成 Completed |
| `FAILED` | `F` | 失败 Failed |
| `CANCELLED` | `CA` | 已取消 Cancelled |
| `TIMEOUT` | `TO` | 超时 Timeout |
| `NODE_FAIL` | `NF` | 节点故障 Node failure |
| `PREEMPTED` | `PR` | 被抢占 Preempted |
| `SUSPENDED` | `S` | 已暂停 Suspended |
| `OUT_OF_MEMORY` | `OOM` | 内存不足 Out of memory |

### 排队原因 | Pending Reasons

| 原因 Reason | 说明 Description |
|-------------|------------------|
| `Priority` | 等待更高优先级 Waiting for priority |
| `Resources` | 等待资源 Waiting for resources |
| `Dependency` | 等待依赖作业 Waiting for dependency |
| `PartitionTimeLimit` | 队列时间限制 Partition time limit |
| `QOSMaxJobsPerUserLimit` | QOS用户作业数限制 |
| `AssocGrpCpuLimit` | 账户CPU限制 Account CPU limit |
| `ReqNodeNotAvail` | 请求节点不可用 Requested node unavailable |

### 自定义输出格式 | Custom Output Format

```bash
# 常用格式示例 Common format examples
squeue -o "%.10i %.9P %.30j %.8u %.8T %.10M %.9l %.6D %R"

# 格式字段 Format fields
# %i - 作业ID Job ID
# %j - 作业名 Job name
# %u - 用户名 Username
# %P - 队列 Partition
# %T - 状态(完整) State (full)
# %t - 状态(缩写) State (compact)
# %M - 运行时间 Time used
# %l - 时间限制 Time limit
# %D - 节点数 Node count
# %C - CPU数 CPU count
# %R - 原因/节点 Reason/NodeList
# %S - 开始时间 Start time
# %e - 结束时间 End time
# %V - 提交时间 Submit time
# %a - 账户 Account
# %b - GRES Generic resources
# %m - 内存 Memory

# 实用格式 Practical formats
# 查看作业的开始时间估计
squeue -u $USER --start -o "%.10i %.30j %.10T %.19S"

# 查看GPU作业的资源使用
squeue -u $USER -o "%.10i %.30j %.8u %.10T %.10M %.6D %.6C %b"
```

---

## scancel 取消作业 | Cancel Jobs

### 基本用法 | Basic Usage

```bash
scancel 12345                # 取消单个作业
scancel 12345 12346 12347    # 取消多个作业
scancel -u $USER             # 取消自己所有作业
scancel -n job_name          # 按作业名取消
scancel -p partition_name    # 取消指定队列的作业
scancel -t PENDING           # 取消所有排队中的作业
```

### 完整参数表 | Complete Parameters

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `job_id` | 作业ID Job ID | `scancel 12345` |
| `-u, --user` | 按用户 By user | `-u $USER` |
| `-n, --name` | 按作业名 By job name | `-n my_job` |
| `-p, --partition` | 按队列 By partition | `-p small` |
| `-t, --state` | 按状态 By state | `-t PENDING` |
| `-A, --account` | 按账户 By account | `-A project1` |
| `-R, --reservation` | 按预留 By reservation | `-R workshop` |
| `--signal` | 发送信号 Send signal | `--signal=TERM` |
| `-f, --full` | 完全取消(含步骤) Full cancel | `-f` |
| `-i, --interactive` | 交互确认 Interactive | `-i` |
| `-b, --batch` | 仅取消批处理脚本 Batch script only | `-b` |
| `-Q, --quiet` | 静默模式 Quiet mode | `-Q` |

### 序列作业取消 | Cancel Array Jobs

```bash
scancel 12345                # 取消整个序列作业
scancel 12345_10             # 取消序列中的第10个任务
scancel 12345_[1-10]         # 取消序列中的1-10任务
scancel 12345_[1-100:2]      # 取消奇数索引任务
```

### 发送信号 | Send Signals

```bash
scancel --signal=USR1 12345  # 发送USR1信号（用于checkpoint）
scancel --signal=TERM 12345  # 发送TERM信号（优雅终止）
scancel --signal=KILL 12345  # 发送KILL信号（强制终止）
```

---

## sinfo 集群状态 | Cluster Status

### 基本用法 | Basic Usage

```bash
sinfo                        # 查看集群总览
sinfo -N                     # 节点级别信息
sinfo -p cpu                 # 查看特定队列
sinfo -N -l                  # 节点详细信息
sinfo -N --states=idle       # 查看空闲节点
sinfo -N --states=alloc      # 查看被占用节点
```

### 完整参数表 | Complete Parameters

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `-N, --Node` | 节点级别显示 Node level | `-N` |
| `-p, --partition` | 指定队列 Specific partition | `-p cpu,gpu` |
| `-n, --nodes` | 指定节点 Specific nodes | `-n cas[001-010]` |
| `-t, --states` | 按状态筛选 Filter by state | `-t idle,mix` |
| `-l, --long` | 详细格式 Long format | `-l` |
| `-s, --summarize` | 摘要格式 Summary | `-s` |
| `-r, --responding` | 仅响应节点 Responding only | `-r` |
| `-d, --dead` | 仅无响应节点 Dead only | `-d` |
| `-R, --list-reasons` | 显示节点原因 Show reasons | `-R` |
| `-T, --reservation` | 显示预留信息 Show reservations | `-T` |
| `-o, --format` | 自定义格式 Custom format | `-o "%n %P %t %c %m"` |
| `-i, --iterate` | 定时刷新 Auto refresh | `-i 5` |

### 节点状态 | Node States

| 状态 State | 说明 Description |
|-----------|------------------|
| `idle` | 完全空闲 Completely idle |
| `alloc` | 完全占用 Fully allocated |
| `mix` | 部分占用 Partially allocated |
| `drain` | 排空中（不接受新作业） Draining |
| `drained` | 已排空 Drained |
| `down` | 下线 Down |
| `fail` | 故障 Failed |
| `failing` | 正在失效 Failing |
| `future` | 未来可用 Future |
| `unknown` | 状态未知 Unknown |

带 `*` 后缀表示无响应，如 `idle*`。

### 自定义输出格式 | Custom Output Format

```bash
# 常用格式 Common formats
sinfo -o "%20P %5a %.10l %.6D %.6t %N"
# %P - 队列名
# %a - 可用性(up/down)
# %l - 时间限制
# %D - 节点数
# %t - 状态
# %N - 节点列表

# 查看详细资源 Detailed resources
sinfo -N -o "%N %.6D %.9P %.11T %.4c %.8m %.8G %f"
# %c - CPU数
# %m - 内存(MB)
# %G - GRES
# %f - 特性

# 查看GPU资源 GPU resources
sinfo -p a100 -o "%N %G %t"
```

---

## sacct 历史记录 | Job History

### 基本用法 | Basic Usage

```bash
sacct                        # 查看过去24小时的作业
sacct -j 12345               # 查看特定作业
sacct -u $USER               # 查看自己的作业
sacct -S 2024-01-01          # 从指定日期开始
sacct -E 2024-01-31          # 到指定日期结束
```

### 完整参数表 | Complete Parameters

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `-j, --jobs` | 指定作业ID Specific jobs | `-j 12345,12346` |
| `-u, --user` | 指定用户 Specific user | `-u $USER` |
| `-A, --accounts` | 指定账户 Specific account | `-A project1` |
| `-S, --starttime` | 开始时间 Start time | `-S 2024-01-01` |
| `-E, --endtime` | 结束时间 End time | `-E now` |
| `-s, --state` | 按状态筛选 Filter by state | `-s COMPLETED,FAILED` |
| `-r, --partition` | 按队列筛选 Filter by partition | `-r cpu` |
| `-n, --name` | 按作业名筛选 Filter by name | `-n my_job` |
| `-a, --allusers` | 所有用户 All users | `-a` |
| `-X, --allocations` | 仅显示分配 Allocations only | `-X` |
| `-l, --long` | 详细格式 Long format | `-l` |
| `-b, --brief` | 简要格式 Brief format | `-b` |
| `-o, --format` | 自定义格式 Custom format | `-o JobID,JobName,State` |
| `--parsable` | 可解析格式 Parsable format | `--parsable` |
| `--parsable2` | 可解析格式(无尾部分隔) | `--parsable2` |
| `--noheader` | 不显示表头 No header | `--noheader` |
| `--units` | 内存单位 Memory units | `--units=G` |

### 常用格式字段 | Common Format Fields

```bash
# 推荐格式 Recommended format
sacct -j 12345 --format="JobID,JobName,Partition,State,ExitCode,Elapsed,MaxRSS,MaxVMSize,NCPUS,NNodes"

# 可用字段 Available fields
# JobID         - 作业ID
# JobName       - 作业名
# User          - 用户
# Group         - 用户组
# Account       - 账户
# Partition     - 队列
# State         - 状态
# ExitCode      - 退出码
# Elapsed       - 运行时间
# TotalCPU      - 总CPU时间
# CPUTime       - CPU时间(核数*时间)
# Submit        - 提交时间
# Start         - 开始时间
# End           - 结束时间
# Timelimit     - 时间限制
# MaxRSS        - 最大常驻内存
# MaxVMSize     - 最大虚拟内存
# MaxDiskRead   - 最大磁盘读取
# MaxDiskWrite  - 最大磁盘写入
# NCPUS         - CPU数
# NNodes        - 节点数
# NodeList      - 节点列表
# ReqMem        - 请求内存
# AllocCPUS     - 分配CPU数
# AllocGRES     - 分配的GRES
```

### 实用查询示例 | Practical Query Examples

```bash
# 查看失败作业 View failed jobs
sacct -u $USER -s FAILED -S 2024-01-01 --format="JobID,JobName,State,ExitCode,End"

# 查看资源使用效率 Check resource efficiency
sacct -j 12345 --format="JobID,Elapsed,TotalCPU,NCPUS,MaxRSS" --units=G

# 查看超时作业 View timed out jobs
sacct -u $USER -s TIMEOUT -S $(date -d "7 days ago" +%Y-%m-%d)

# 统计账户使用量 Account usage statistics
sacct -A my_account -S 2024-01-01 --format="JobID,User,Elapsed,NCPUS" -X | tail -n +3

# 导出为CSV Export as CSV
sacct -j 12345 --format="JobID,JobName,State,Elapsed,MaxRSS" --parsable2 > job_report.csv
```

---

## scontrol 作业控制 | Job Control

### 查看信息 | View Information

```bash
scontrol show job 12345           # 查看作业详情
scontrol show job 12345 -d        # 查看作业详情(含步骤)
scontrol show node cas001         # 查看节点详情
scontrol show partition cpu       # 查看队列详情
scontrol show reservation         # 查看预留资源
scontrol show config              # 查看Slurm配置
```

### 修改作业 | Modify Jobs

```bash
# 修改时间限制 Change time limit
scontrol update JobId=12345 TimeLimit=2-00:00:00

# 修改作业名 Change job name
scontrol update JobId=12345 JobName=new_name

# 修改队列 Change partition
scontrol update JobId=12345 Partition=small

# 修改节点数 Change node count
scontrol update JobId=12345 NumNodes=4

# 修改依赖 Change dependency
scontrol update JobId=12345 Dependency=afterok:11111

# 清除依赖 Clear dependency
scontrol update JobId=12345 Dependency=
```

### 作业状态控制 | Job State Control

```bash
# 暂停作业（保持在队列中但不调度）
scontrol hold 12345
scontrol hold JobId=12345

# 恢复作业调度
scontrol release 12345

# 重新排队（仅限可重新排队的作业）
scontrol requeue 12345

# 暂停运行中的作业
scontrol suspend 12345

# 恢复暂停的作业
scontrol resume 12345

# 设置作业优先级为0（永不运行）
scontrol update JobId=12345 Priority=0

# 恢复优先级
scontrol update JobId=12345 Priority=4294967294
```

### 节点控制（管理员） | Node Control (Admin)

```bash
# 设置节点为drain状态
scontrol update NodeName=cas001 State=drain Reason="maintenance"

# 恢复节点
scontrol update NodeName=cas001 State=resume

# 设置节点下线
scontrol update NodeName=cas001 State=down Reason="hardware issue"
```

### 常用参数 | Common Parameters

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `show job` | 显示作业信息 Show job info | `show job 12345` |
| `show node` | 显示节点信息 Show node info | `show node cas001` |
| `show partition` | 显示队列信息 Show partition info | `show partition cpu` |
| `update JobId=` | 更新作业 Update job | `update JobId=12345 ...` |
| `hold` | 暂停调度 Hold job | `hold 12345` |
| `release` | 恢复调度 Release job | `release 12345` |
| `requeue` | 重新排队 Requeue | `requeue 12345` |
| `suspend` | 暂停运行 Suspend | `suspend 12345` |
| `resume` | 恢复运行 Resume | `resume 12345` |
| `-d, --details` | 详细信息 Details | `-d` |
| `-o, --oneliner` | 单行输出 One line | `-o` |

---

## srun 交互运行 | Interactive Execution

### 基本用法 | Basic Usage

```bash
# 申请资源并运行命令
srun -n 4 ./my_program

# 申请交互式shell
srun -p small -n 4 --pty /bin/bash

# 在已分配的资源上运行（在sbatch脚本内或salloc后）
srun ./my_program
```

### 完整参数表 | Complete Parameters

继承 sbatch 的大部分参数，额外参数：

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `--pty` | 分配伪终端 Pseudo terminal | `--pty /bin/bash` |
| `--unbuffered` | 无缓冲输出 Unbuffered output | `--unbuffered` |
| `--label` | 输出带任务标签 Label output | `--label` |
| `--mpi` | MPI类型 MPI type | `--mpi=pmi2` |
| `--multi-prog` | 多程序配置 Multi-program | `--multi-prog prog.conf` |
| `--task-epilog` | 任务后脚本 Task epilog | `--task-epilog=script.sh` |
| `--task-prolog` | 任务前脚本 Task prolog | `--task-prolog=script.sh` |

### 交互式作业示例 | Interactive Job Examples

```bash
# 申请4个CPU核的交互式终端
srun -p small -n 4 --pty /bin/bash

# 申请1个GPU的交互式终端
srun -p a100 -N 1 --gres=gpu:1 --cpus-per-task=16 --pty /bin/bash

# 申请1个节点独占
srun -p cpu -N 1 --exclusive --pty /bin/bash

# 申请2小时的交互式会话
srun -p small -n 1 -t 2:00:00 --pty /bin/bash

# 运行GUI程序（需要X11转发）
srun -p small -n 1 --x11 --pty matlab
```

### 在作业脚本中使用 | Usage in Job Scripts

```bash
#!/bin/bash
#SBATCH -N 2
#SBATCH -n 80
#SBATCH -p cpu

# 运行MPI程序
srun ./my_mpi_program

# 运行多个并行任务（不同节点）
srun -N 1 -n 40 ./task1 &
srun -N 1 -n 40 ./task2 &
wait
```

---

## salloc 资源申请 | Resource Allocation

### 基本用法 | Basic Usage

```bash
# 申请资源（进入子shell）
salloc -N 1 -n 40 -p small

# 申请资源并指定命令
salloc -N 1 -n 4 /bin/bash

# 申请GPU资源
salloc -p a100 -N 1 --gres=gpu:2
```

### 完整参数表 | Complete Parameters

继承 sbatch 的大部分资源相关参数，额外参数：

| 参数 Parameter | 说明 Description | 示例 Example |
|---------------|------------------|--------------|
| `--no-shell` | 不启动shell No shell | `--no-shell` |
| `--bell` | 分配时响铃 Bell on allocation | `--bell` |
| `--immediate` | 立即分配或失败 Immediate or fail | `--immediate` |
| `-I, --immediate=` | 超时秒数 Timeout seconds | `-I 60` |

### 使用流程 | Usage Workflow

```bash
# 1. 申请资源
salloc -N 2 -n 80 -p cpu

# 2. 查看分配的节点
echo $SLURM_JOB_NODELIST

# 3. 在分配的资源上运行作业
srun ./my_program

# 或者SSH到分配的节点
ssh $(echo $SLURM_JOB_NODELIST | cut -d',' -f1)

# 4. 退出释放资源
exit
```

### salloc vs srun --pty

```bash
# srun --pty: 直接在计算节点上启动shell
srun -p small -n 4 --pty /bin/bash
# - 简单直接
# - 断开连接会终止作业

# salloc: 在登录节点分配资源，然后手动srun或ssh
salloc -p small -n 4
srun ./program   # 或 ssh $SLURM_JOB_NODELIST
# - 更灵活
# - 可以多次srun
# - 断开后资源仍保留（直到超时或手动释放）
```

---

## 环境变量 | Environment Variables

### 作业基本信息 | Basic Job Information

| 变量 Variable | 说明 Description |
|--------------|------------------|
| `SLURM_JOB_ID` | 作业ID |
| `SLURM_JOB_NAME` | 作业名称 |
| `SLURM_JOB_USER` | 提交用户 |
| `SLURM_JOB_ACCOUNT` | 账户名 |
| `SLURM_JOB_PARTITION` | 队列名 |
| `SLURM_JOB_QOS` | QOS名称 |
| `SLURM_SUBMIT_DIR` | 提交目录 |
| `SLURM_SUBMIT_HOST` | 提交主机 |

### 资源分配信息 | Resource Allocation

| 变量 Variable | 说明 Description |
|--------------|------------------|
| `SLURM_NTASKS` | 总任务/进程数 |
| `SLURM_NPROCS` | 等同于SLURM_NTASKS |
| `SLURM_NNODES` | 节点数 |
| `SLURM_JOB_NODELIST` | 节点列表 |
| `SLURM_JOB_NUM_NODES` | 节点数 |
| `SLURM_CPUS_PER_TASK` | 每任务CPU数 |
| `SLURM_CPUS_ON_NODE` | 当前节点CPU数 |
| `SLURM_MEM_PER_CPU` | 每CPU内存(MB) |
| `SLURM_MEM_PER_NODE` | 每节点内存(MB) |
| `SLURM_TASKS_PER_NODE` | 每节点任务数 |

### 节点和任务信息 | Node and Task Information

| 变量 Variable | 说明 Description |
|--------------|------------------|
| `SLURM_NODEID` | 当前节点在作业中的ID (0-based) |
| `SLURM_PROCID` | MPI rank (0-based) |
| `SLURM_LOCALID` | 节点内任务ID (0-based) |
| `SLURM_TASK_PID` | 任务进程ID |
| `SLURMD_NODENAME` | 当前节点名 |

### 序列作业 | Array Jobs

| 变量 Variable | 说明 Description |
|--------------|------------------|
| `SLURM_ARRAY_JOB_ID` | 序列作业主ID |
| `SLURM_ARRAY_TASK_ID` | 当前任务的数组索引 |
| `SLURM_ARRAY_TASK_COUNT` | 序列任务总数 |
| `SLURM_ARRAY_TASK_MAX` | 最大索引 |
| `SLURM_ARRAY_TASK_MIN` | 最小索引 |
| `SLURM_ARRAY_TASK_STEP` | 索引步长 |

### GPU相关 | GPU Related

| 变量 Variable | 说明 Description |
|--------------|------------------|
| `SLURM_JOB_GPUS` | 分配的GPU ID列表 |
| `SLURM_GPUS_ON_NODE` | 当前节点GPU数 |
| `SLURM_STEP_GPUS` | 步骤GPU ID |
| `CUDA_VISIBLE_DEVICES` | CUDA可见设备（Slurm自动设置） |
| `GPU_DEVICE_ORDINAL` | GPU设备序号（ROCm） |

### 使用示例 | Usage Examples

```bash
#!/bin/bash
#SBATCH -J my_job
#SBATCH -n 4
#SBATCH --array=1-10

echo "Job ID: $SLURM_JOB_ID"
echo "Job Name: $SLURM_JOB_NAME"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Running on node: $SLURMD_NODENAME"
echo "Working directory: $SLURM_SUBMIT_DIR"
echo "Number of tasks: $SLURM_NTASKS"

# 使用数组任务ID处理不同数据
INPUT_FILE="data/input_${SLURM_ARRAY_TASK_ID}.csv"
OUTPUT_FILE="results/output_${SLURM_ARRAY_TASK_ID}.csv"

python process.py $INPUT_FILE $OUTPUT_FILE
```

---

## 作业脚本模板 | Job Script Templates

### 基础模板 | Basic Template

```bash
#!/bin/bash
#SBATCH -J job_name              # 作业名称
#SBATCH -p small                 # 队列名称
#SBATCH -N 1                     # 节点数
#SBATCH -n 4                     # 任务数
#SBATCH -t 1:00:00               # 时间限制
#SBATCH -o %j.out                # 标准输出
#SBATCH -e %j.err                # 标准错误

# 加载环境模块
module load gcc/11.2.0

# 进入工作目录
cd $SLURM_SUBMIT_DIR

# 运行程序
./my_program
```

### MPI并行作业 | MPI Parallel Job

```bash
#!/bin/bash
#SBATCH -J mpi_job
#SBATCH -p cpu
#SBATCH -N 2                     # 2个节点
#SBATCH --ntasks-per-node=40     # 每节点40进程
#SBATCH -t 24:00:00
#SBATCH -o %j.out
#SBATCH -e %j.err

module load intel/2021.4.0
module load mpi/2021.4.0

cd $SLURM_SUBMIT_DIR

# 使用srun运行MPI程序
srun ./mpi_program

# 或者使用mpirun (取决于集群配置)
# mpirun -np $SLURM_NTASKS ./mpi_program
```

### OpenMP多线程作业 | OpenMP Multithreaded Job

```bash
#!/bin/bash
#SBATCH -J openmp_job
#SBATCH -p small
#SBATCH -N 1
#SBATCH -n 1                     # 1个任务
#SBATCH --cpus-per-task=40       # 40个CPU核用于线程
#SBATCH -t 4:00:00
#SBATCH -o %j.out
#SBATCH -e %j.err

module load gcc/11.2.0

# 设置OpenMP线程数
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

cd $SLURM_SUBMIT_DIR
./openmp_program
```

### 混合MPI+OpenMP作业 | Hybrid MPI+OpenMP Job

```bash
#!/bin/bash
#SBATCH -J hybrid_job
#SBATCH -p cpu
#SBATCH -N 4                     # 4个节点
#SBATCH --ntasks-per-node=2      # 每节点2个MPI进程
#SBATCH --cpus-per-task=20       # 每进程20个线程
#SBATCH -t 48:00:00
#SBATCH -o %j.out
#SBATCH -e %j.err

module load intel/2021.4.0
module load mpi/2021.4.0

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

cd $SLURM_SUBMIT_DIR
srun ./hybrid_program
```

### GPU作业 | GPU Job

```bash
#!/bin/bash
#SBATCH -J gpu_job
#SBATCH -p a100                  # GPU队列
#SBATCH -N 1
#SBATCH --gres=gpu:2             # 2块GPU
#SBATCH --cpus-per-task=16       # CPU核
#SBATCH --mem=64G                # 内存
#SBATCH -t 24:00:00
#SBATCH -o %j.out
#SBATCH -e %j.err

module load cuda/11.8
module load cudnn/8.6.0

cd $SLURM_SUBMIT_DIR

# 查看分配的GPU
echo "CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
nvidia-smi

python train.py --gpus 2
```

### 多GPU分布式训练 | Multi-GPU Distributed Training

```bash
#!/bin/bash
#SBATCH -J distributed_train
#SBATCH -p a100
#SBATCH -N 2                     # 2个节点
#SBATCH --ntasks-per-node=4      # 每节点4个进程
#SBATCH --gres=gpu:4             # 每节点4块GPU
#SBATCH --cpus-per-task=8
#SBATCH --mem=256G
#SBATCH -t 72:00:00
#SBATCH -o %j.out
#SBATCH -e %j.err

module load cuda/11.8
module load nccl/2.15.5

# PyTorch分布式环境变量
export MASTER_PORT=29500
export MASTER_ADDR=$(scontrol show hostname $SLURM_NODELIST | head -n 1)
export WORLD_SIZE=$SLURM_NTASKS

cd $SLURM_SUBMIT_DIR

srun python -m torch.distributed.launch \
    --nproc_per_node=4 \
    --nnodes=$SLURM_NNODES \
    --node_rank=$SLURM_NODEID \
    --master_addr=$MASTER_ADDR \
    --master_port=$MASTER_PORT \
    train_distributed.py
```

### 序列作业 | Array Job

```bash
#!/bin/bash
#SBATCH -J array_job
#SBATCH -p small
#SBATCH -n 4
#SBATCH -t 1:00:00
#SBATCH --array=1-100%20         # 100个任务，最多同时20个
#SBATCH -o logs/%A_%a.out        # %A=主ID, %a=任务ID
#SBATCH -e logs/%A_%a.err

# 确保日志目录存在
mkdir -p logs

cd $SLURM_SUBMIT_DIR

# 使用任务ID选择输入
INPUT="data/input_${SLURM_ARRAY_TASK_ID}.dat"
OUTPUT="results/output_${SLURM_ARRAY_TASK_ID}.dat"

# 从文件读取参数
PARAM=$(sed -n "${SLURM_ARRAY_TASK_ID}p" params.txt)

./my_program -i $INPUT -o $OUTPUT -p $PARAM
```

### 依赖作业链 | Job Chain with Dependencies

```bash
# 脚本1: 数据预处理
# preprocess.slurm
#!/bin/bash
#SBATCH -J preprocess
#SBATCH -p small
#SBATCH -n 4
#SBATCH -t 2:00:00
#SBATCH -o preprocess_%j.out

python preprocess.py

# 脚本2: 主计算（依赖预处理）
# compute.slurm
#!/bin/bash
#SBATCH -J compute
#SBATCH -p cpu
#SBATCH -N 4
#SBATCH --ntasks-per-node=40
#SBATCH -t 48:00:00
#SBATCH -o compute_%j.out

srun ./compute

# 脚本3: 后处理（依赖主计算）
# postprocess.slurm
#!/bin/bash
#SBATCH -J postprocess
#SBATCH -p small
#SBATCH -n 1
#SBATCH -t 1:00:00
#SBATCH -o postprocess_%j.out

python postprocess.py

# 提交依赖作业链
JOB1=$(sbatch --parsable preprocess.slurm)
JOB2=$(sbatch --parsable --dependency=afterok:$JOB1 compute.slurm)
JOB3=$(sbatch --parsable --dependency=afterok:$JOB2 postprocess.slurm)
echo "Submitted job chain: $JOB1 -> $JOB2 -> $JOB3"
```

### 带Checkpoint的长时间作业 | Long Job with Checkpoint

```bash
#!/bin/bash
#SBATCH -J checkpoint_job
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 40
#SBATCH -t 7-00:00:00            # 7天
#SBATCH --signal=USR1@300        # 超时前5分钟发信号
#SBATCH --requeue                # 允许重新排队
#SBATCH -o %j.out

# 信号处理函数
checkpoint_and_requeue() {
    echo "Received signal, saving checkpoint..."
    # 保存checkpoint
    cp state.dat checkpoint/state_${SLURM_JOB_ID}.dat

    # 重新提交作业
    scontrol requeue $SLURM_JOB_ID
    exit 0
}

trap checkpoint_and_requeue USR1

# 检查是否有checkpoint可恢复
if [ -f checkpoint/state_${SLURM_JOB_ID}.dat ]; then
    echo "Resuming from checkpoint..."
    cp checkpoint/state_${SLURM_JOB_ID}.dat state.dat
fi

# 运行程序（后台运行以便接收信号）
./my_long_program &
wait
```

### R语言作业 | R Language Job

```bash
#!/bin/bash
#SBATCH -J r_analysis
#SBATCH -p small
#SBATCH -n 8
#SBATCH --mem=32G
#SBATCH -t 4:00:00
#SBATCH -o %j.out
#SBATCH -e %j.err

module load R/4.2.0

cd $SLURM_SUBMIT_DIR

# 设置R并行
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

Rscript --vanilla analysis.R
```

### Python作业（Conda环境） | Python Job (Conda)

```bash
#!/bin/bash
#SBATCH -J python_job
#SBATCH -p small
#SBATCH -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH -t 4:00:00
#SBATCH -o %j.out
#SBATCH -e %j.err

# 加载Anaconda
module load anaconda3/2022.05

# 激活环境
source activate myenv

cd $SLURM_SUBMIT_DIR
python my_script.py --threads $SLURM_CPUS_PER_TASK
```

---

## 高级用法 | Advanced Usage

### 资源使用效率分析 | Resource Efficiency Analysis

```bash
# 查看作业效率
seff 12345

# 手动计算CPU效率
sacct -j 12345 --format="JobID,Elapsed,TotalCPU,NCPUS" | awk '
NR>2 && $1!~"\\." {
    elapsed_sec = $2
    # 转换时间格式为秒
    # 计算效率 = TotalCPU / (Elapsed * NCPUS) * 100
}
'

# 查看内存使用效率
sacct -j 12345 --format="JobID,ReqMem,MaxRSS" --units=G
```

### 批量作业管理 | Batch Job Management

```bash
# 批量取消特定前缀的作业
squeue -u $USER -o "%.10i %.30j" | awk '$2~/^test_/ {print $1}' | xargs scancel

# 批量修改作业时间限制
for jobid in $(squeue -u $USER -h -o "%i"); do
    scontrol update JobId=$jobid TimeLimit=2-00:00:00
done

# 统计用户作业状态
squeue -u $USER -o "%t" | sort | uniq -c

# 等待所有作业完成
while squeue -u $USER -h | grep -q .; do
    echo "Waiting for jobs to complete..."
    sleep 60
done
echo "All jobs completed!"
```

### 作业监控脚本 | Job Monitoring Script

```bash
#!/bin/bash
# monitor_jobs.sh - 监控作业状态

watch -n 30 '
echo "=== Running Jobs ==="
squeue -u $USER -t R -o "%.10i %.20j %.8T %.10M %.9l %.6D %R"
echo ""
echo "=== Pending Jobs ==="
squeue -u $USER -t PD -o "%.10i %.20j %.8T %.10M %.6D %R" --start
echo ""
echo "=== Recently Completed ==="
sacct -u $USER -S $(date -d "1 hour ago" +%Y-%m-%dT%H:%M) -o "JobID,JobName,State,Elapsed,ExitCode" | head -20
'
```

### 资源预估 | Resource Estimation

```bash
# 测试作业资源需求（短时间运行）
sbatch --test-only job.slurm

# 使用debug队列快速测试
sbatch -p debug -t 00:15:00 --wrap="./my_program --test"

# 基于历史作业估计资源
sacct -n -X -j 12340,12341,12342 --format="Elapsed,MaxRSS,NCPUS" | awk '
{
    split($1,t,":")
    sec = t[1]*3600 + t[2]*60 + t[3]
    if(sec>max_time) max_time=sec
    mem = $2; gsub(/[KMG]/,"",mem)
    if(mem>max_mem) max_mem=mem
}
END {
    printf "Recommended: --time=%d:00:00 --mem=%dG\n", max_time/3600+1, max_mem/1024+1
}
'
```

### 常见问题排查 | Troubleshooting

```bash
# 作业一直PD（排队）的原因
squeue -j 12345 -o "%r"

# 查看节点为什么不可用
sinfo -N -n cas001 -o "%N %T %E"

# 查看作业为什么失败
sacct -j 12345 --format="JobID,State,ExitCode,DerivedExitCode,Comment"

# 检查作业输出文件
ls -la slurm-12345.out

# 查看详细的作业步骤
sacct -j 12345 --format="JobID,JobName,State,ExitCode,MaxRSS,Elapsed"

# 节点资源使用情况
scontrol show node cas001 | grep -E "(NodeName|CPUAlloc|CPUTot|RealMemory|AllocMem|State)"
```

### 与其他工具集成 | Integration with Other Tools

```bash
# 使用jq解析squeue JSON输出
squeue -u $USER -o "%all" --json | jq '.jobs[] | {id:.job_id, name:.name, state:.job_state}'

# 发送作业完成通知到微信/钉钉
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=your_webhook_endpoint

# 使用GNU Parallel + Slurm
parallel -j 10 'sbatch --wrap="python process.py {}"' ::: data/*.csv

# 与Snakemake集成
snakemake --cluster "sbatch -p {cluster.partition} -n {cluster.n} -t {cluster.time}" \
          --cluster-config cluster.yaml --jobs 100
```

---

## 快速故障排查 | Quick Troubleshooting

| 问题 Problem | 可能原因 Possible Cause | 解决方案 Solution |
|-------------|------------------------|-------------------|
| 作业一直PD | 资源不足/优先级低 | `squeue -j ID -o "%r"` 查看原因 |
| 作业立即失败 | 脚本错误 | 检查 `.err` 文件 |
| OOM错误 | 内存不足 | 增加 `--mem` |
| 超时 | 时间估计不足 | 增加 `--time` |
| GPU不可见 | CUDA设置问题 | 检查 `$CUDA_VISIBLE_DEVICES` |
| MPI错误 | MPI版本不匹配 | 检查 module 加载 |
| 输出文件为空 | 工作目录错误 | 检查 `-D` 或 `cd` |
| 节点故障 | 硬件问题 | `--exclude` 排除问题节点 |

---

## 参考链接 | References

- [Slurm Official Documentation](https://slurm.schedmd.com/documentation.html)
- [Slurm Quick Start Guide](https://slurm.schedmd.com/quickstart.html)
- [Slurm sbatch Manual](https://slurm.schedmd.com/sbatch.html)
- [SJTU HPC Documentation](https://docs.hpc.sjtu.edu.cn/)

---

*Last updated: 2026-01-29*
