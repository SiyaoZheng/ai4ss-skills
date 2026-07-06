---

name: sjtu-hpc
description: "Trigger on SJTU HPC, 交我算, Slurm, srun, sbatch, IDEKube, hpc/sy SSH; use for cluster jobs and transfer."

---

# SJTU HPC Platform Guide (交我算)

## Full-Auto Harness Contract

在自动 harness 中，本 skill 不得暂停等待人工选择，也不得返回无进展的终止状态。必须自动选择最安全可行的连接别名、队列、
Slurm 模板、资源配置和验证命令。若实时 SSH/提交不可用，不要反复撞登录节点；改为生成可提交
`job.slurm`、数据传输命令、环境初始化脚本和本地/远端验证清单，让研究流水线继续推进到
发表级 `paper/full_draft.pdf` 所需的计算产物。

## .aiss State Machine

当从 AI4SS research-factory workspace 调用时，先定位
`.ai4ss/research_model.aiss` 并运行
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss`，再决定或返回
`next_skill_route`。启动、完成、失败和 watchdog heartbeat 观察应记录为
`.aiss` `event` declaration，或返回可合并的
`aiss.py transition --event ...` deterministic fragment。event 不能替代语义更新：
作业脚本、提交状态、输出路径和失败修复仍要落到相应 `artifact`、`check`、
`decision` 或日志声明。

## SSH 连接安全 (fail2ban)

**关键规则：**
- **用别名登录**: `ssh hpc` 或 `ssh sy`，不要直接用 `ssh sylogin.hpc.sjtu.edu.cn`（可能用错用户名）
- **fail2ban 保护**: 3 次认证失败 → IP 封禁 1 小时
- **失败 2 次就切换策略**: 检查 SSH 配置，改用 `hpc-data` 验证或生成离线可提交脚本，**不要继续尝试**触发封禁
- **被封后**: 换网络（手机热点）立即恢复，或等 1 小时自动解封
- **验证账号**: `ssh hpc-data` 数据节点通常不受 fail2ban 影响，可用于验证账号/证书是否正常

**推荐 SSH 配置** (`~/.ssh/config`):
```
Host hpc sy
    HostName sylogin.hpc.sjtu.edu.cn
    User YOUR_HPC_USERNAME
    IdentityFile ~/.ssh/sjtu_hpc_ed25519

Host hpc-data
    HostName sydata.hpc.sjtu.edu.cn
    User YOUR_HPC_USERNAME
    IdentityFile ~/.ssh/sjtu_hpc_ed25519
```

---

## Quick Reference

### Login & Data Nodes

| Cluster | Login Node | Data Node |
|---------|-----------|-----------|
| Siyuan-1 (思源一号) | `sylogin.hpc.sjtu.edu.cn` | `sydata.hpc.sjtu.edu.cn` |
| Pi 2.0 / AI | `pilogin.hpc.sjtu.edu.cn` | `data.hpc.sjtu.edu.cn` |
| ARM | `armlogin.hpc.sjtu.edu.cn` | `data.hpc.sjtu.edu.cn` |

### Queue Summary

| Queue | Cluster | Max Cores | Max GPU | Max Time | Use Case |
|-------|---------|-----------|---------|----------|----------|
| `64c512g` | Siyuan-1 | 60,000 | - | 7 days | Large CPU jobs |
| `a100` | Siyuan-1 | - | 92 cards | 7 days | GPU computing (A100 40GB) |
| `debug64c512g` | Siyuan-1 | 128 | - | 60 min | CPU debugging |
| `debuga100` | Siyuan-1 | 64 | 28 virtual | 20 min | GPU debug (5GB vGPU, NOT real A100) |
| `cpu` | Pi 2.0 | 24,000 | - | 7 days | CPU jobs (exclusive) |
| `small` | Pi 2.0 | 1-20 | - | 7 days | Small jobs (shared) |
| `dgx2` | AI | - | 128 cards | 7 days | GPU computing (V100) |
| `huge` | Pi 2.0 | 80 | - | 2 days | Large memory (3TB) |

**Important**: Login nodes prohibit running jobs and parallel compilation. For interactive work: `srun -p 64c512g -n 4 --pty /bin/bash`

---

## 核心原则：擦干净屁股

每次操作结束后（无论正常还是异常），必须确保不留残留：

```bash
squeue -u $USER   # 检查残留作业
ls $SCRATCH        # 检查残留临时文件
```

**违反后果**：残留作业持续计费（浪费钱），资源滥用可能封号。

---

## 禁止操作

1. **登录节点运行计算** → 用 `sbatch` 或 `srun -p 64c512g ...`
2. **登录节点并行编译** → 申请计算节点后再 `make -j`
3. **登录节点大批量传输** → 使用数据传输节点
4. **Debug 队列跑正式计算** → Debug 仅用于测试脚本
5. **超配额写入** → 定期清理，归档到科学大数据平台
6. **共享账号** → 每人使用自己的账号

### 交互式作业

```bash
srun -p 64c512g -n 4 --pty /bin/bash      # CPU 交互
srun -p a100 --gres=gpu:1 --pty /bin/bash  # GPU 交互
```

---

## Common Commands

| Command | Description |
|---------|-------------|
| `sbatch job.slurm` | Submit job |
| `squeue -u $USER` | View your jobs |
| `scancel JOBID` | Cancel job |
| `sinfo -p QUEUE` | View queue status |
| `sacct -j JOBID` | View completed job info |
| `module avail` | List available modules |
| `module load NAME` | Load module |

## Proxy Settings (Compute Node Internet Access)

| Cluster | Proxy |
|---------|-------|
| Siyuan-1 | `http://proxy2.pi.sjtu.edu.cn:3128` |
| Pi 2.0 | `http://proxy.pi.sjtu.edu.cn:3004` |

```bash
export http_proxy=http://proxy2.pi.sjtu.edu.cn:3128   # Siyuan-1
export https_proxy=http://proxy2.pi.sjtu.edu.cn:3128
```

---

## Detailed Documentation

| Topic | Reference |
|-------|-----------|
| **SSH access & environment variables** | [references/access.md](references/access.md) |
| Slurm job templates (CPU/GPU/Array) | [references/job-templates.md](references/job-templates.md) |
| Python & R environment setup | [references/python-r.md](references/python-r.md) |
| GPU computing (A100/V100) | [references/gpu.md](references/gpu.md) |
| Data transfer methods | [references/data.md](references/data.md) |
| Storage architecture & quotas | [references/storage.md](references/storage.md) |
| Queue specifications | [references/queues.md](references/queues.md) |
| Complete Slurm commands | [references/slurm-commands.md](references/slurm-commands.md) |
| HPC Studio web GUI | [references/hpc-studio.md](references/hpc-studio.md) |
| Troubleshooting | [references/troubleshooting.md](references/troubleshooting.md) |
| Billing & cost estimation | [references/billing.md](references/billing.md) |
| Cluster monitoring dashboard | [references/monitoring.md](references/monitoring.md) |
| Compute outsourcing workflow | [references/compute-outsourcing.md](references/compute-outsourcing.md) |
| Parallel configuration formula | [references/parallel-config.md](references/parallel-config.md) |
| Utility scripts | [references/utility-scripts.md](references/utility-scripts.md) |

## External Resources

- Documentation: https://docs.hpc.sjtu.edu.cn
- HPC Studio (Web GUI): https://studio.hpc.sjtu.edu.cn
- Account Management: https://my.hpc.sjtu.edu.cn
- Usage Monitor: https://account.hpc.sjtu.edu.cn/top/
- Cluster Status: https://mon.hpc.sjtu.edu.cn/d/Q6W7OfInk/
- Support Email: hpc@sjtu.edu.cn

## Related Skills

- **r-performance** — 并行配置公式、BLAS 线程、future 生态
- **targets-expert** — 在 HPC 上跑 targets pipeline（crew.cluster）
