# Utility Scripts | 实用脚本

位于 `scripts/` 目录:

| 脚本 | 用途 |
|------|------|
| `hpc-sync.sh` | **项目同步** - 本地 ↔ HPC 无感同步，支持 Make/targets 项目 |
| `hpc-cleanup.sh` | **资源清理** - 检查并清理残留作业、临时文件、孤立进程 |
| `quota_check.sh` | 配额监控 - 检查存储使用，定位大文件，提供清理建议 |
| `backup_to_union.sh` | 归档脚本 - rsync 到科学大数据平台，自动 MD5 校验 |
| `cost_estimate.py` | 成本计算器 - 根据资源配置估算费用 |
| `templates/` | 并行配置模板 - config_parallel.py/R, _targets_hpc.R |

## hpc-sync 使用示例 (核心工具)

```bash
cd ~/projects/my_research
hpc-sync init                    # 首次: 初始化配置
hpc-sync push                    # 推送代码+数据到 HPC
hpc-sync pull                    # 回收结果 (output/, results/, figures/)
hpc-sync status                  # 查看同步状态
```

## 资源清理 (每次会话结束前必须运行!)

```bash
hpc-cleanup                                     # 检查并清理残留
hpc-cleanup --check                             # 仅检查
```

## 其他工具

```bash
./scripts/quota_check.sh --warning 80           # 配额警告
./scripts/backup_to_union.sh ~/project archive/ # 归档项目
python scripts/cost_estimate.py --queue a100 --gpus 2 --hours 24
```
