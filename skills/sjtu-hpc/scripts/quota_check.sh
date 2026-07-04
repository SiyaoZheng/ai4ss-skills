#!/bin/bash
# quota_check.sh - SJTU HPC 配额监控脚本
# SJTU HPC Quota Monitoring Script
#
# 功能 / Features:
# - 检查各存储系统配额使用情况
# - 超过阈值时发出警告
# - 列出大文件/目录帮助清理
#
# 使用方法 / Usage:
#   ./quota_check.sh                    # 检查所有存储
#   ./quota_check.sh --warning 80       # 使用量超过 80% 时警告
#   ./quota_check.sh --top 20           # 显示 Top 20 大文件/目录
#   ./quota_check.sh --help             # 显示帮助
#
# 依赖 / Dependencies:
#   - 在 SJTU HPC 集群上运行 (思源一号或 Pi 2.0)
#   - 需要 lfs (Lustre) 或 mmlsquota (GPFS) 命令

set -euo pipefail

# 默认参数 / Default parameters
WARNING_THRESHOLD=80  # 警告阈值 (%)
TOP_N=10              # 显示 Top N 大文件

# 颜色定义 / Color definitions
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 帮助信息 / Help message
show_help() {
    cat << EOF
SJTU HPC 配额监控脚本 / Quota Monitoring Script

使用方法 / Usage:
    $0 [选项]

选项 / Options:
    --warning N     设置警告阈值为 N% (默认 80%)
                    Set warning threshold to N% (default 80%)

    --top N         显示 Top N 大文件/目录 (默认 10)
                    Show top N largest files/directories (default 10)

    --help          显示此帮助信息
                    Show this help message

示例 / Examples:
    $0                      # 默认检查
    $0 --warning 90         # 90% 阈值警告
    $0 --top 20             # 显示 Top 20

EOF
}

# 解析参数 / Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --warning)
            WARNING_THRESHOLD="$2"
            shift 2
            ;;
        --top)
            TOP_N="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "未知参数 / Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# 打印分隔线 / Print separator
print_separator() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 检查使用率并设置颜色 / Check usage and set color
get_color() {
    local usage=$1
    if (( usage >= 90 )); then
        echo -e "${RED}"
    elif (( usage >= WARNING_THRESHOLD )); then
        echo -e "${YELLOW}"
    else
        echo -e "${GREEN}"
    fi
}

# 检测集群类型 / Detect cluster type
detect_cluster() {
    if [[ -d /dssg ]]; then
        echo "siyuan"
    elif [[ -d /lustre ]]; then
        echo "pi2"
    else
        echo "unknown"
    fi
}

# 格式化字节大小 / Format byte size
format_size() {
    local size=$1
    if (( size >= 1099511627776 )); then
        echo "$(echo "scale=2; $size / 1099511627776" | bc)T"
    elif (( size >= 1073741824 )); then
        echo "$(echo "scale=2; $size / 1073741824" | bc)G"
    elif (( size >= 1048576 )); then
        echo "$(echo "scale=2; $size / 1048576" | bc)M"
    else
        echo "${size}B"
    fi
}

# 检查 Lustre 配额 / Check Lustre quota
check_lustre_quota() {
    echo -e "\n${BLUE}📁 Lustre 存储配额 (/lustre)${NC}"
    print_separator

    if ! command -v lfs &> /dev/null; then
        echo "⚠️  lfs 命令不可用 (可能不在 Pi 2.0 集群)"
        return
    fi

    local quota_output
    quota_output=$(lfs quota -u "$USER" /lustre 2>/dev/null || true)

    if [[ -z "$quota_output" ]]; then
        echo "⚠️  无法获取 Lustre 配额信息"
        return
    fi

    echo "$quota_output"

    # 解析配额信息 (简化输出)
    local used limit
    used=$(echo "$quota_output" | grep -oP '\d+(?=\s+\d+\s+\d+\s+-)' | head -1 || echo "0")
    limit=$(echo "$quota_output" | grep -oP '\d+(?=\s+\d+\s+-)' | head -1 || echo "1")

    if [[ -n "$used" && -n "$limit" && "$limit" -gt 0 ]]; then
        local usage=$((used * 100 / limit))
        local color
        color=$(get_color "$usage")
        echo -e "\n使用率 / Usage: ${color}${usage}%${NC}"

        if (( usage >= WARNING_THRESHOLD )); then
            echo -e "${YELLOW}⚠️  警告: 存储使用率超过 ${WARNING_THRESHOLD}%，建议清理${NC}"
        fi
    fi
}

# 检查 GPFS 配额 / Check GPFS quota
check_gpfs_quota() {
    echo -e "\n${BLUE}📁 GPFS 存储配额 (/dssg)${NC}"
    print_separator

    if ! command -v mmlsquota &> /dev/null; then
        echo "⚠️  mmlsquota 命令不可用 (可能不在思源一号集群)"
        return
    fi

    local quota_output
    quota_output=$(mmlsquota -u "$USER" --block-size auto 2>/dev/null || true)

    if [[ -z "$quota_output" ]]; then
        echo "⚠️  无法获取 GPFS 配额信息"
        return
    fi

    echo "$quota_output"
}

# 检查 Scratch 使用 / Check Scratch usage
check_scratch_usage() {
    echo -e "\n${BLUE}⚡ Scratch 存储使用 (/scratch)${NC}"
    print_separator

    if [[ ! -d "$SCRATCH" ]]; then
        echo "⚠️  \$SCRATCH 目录不存在或未设置"
        return
    fi

    local scratch_size
    scratch_size=$(du -sh "$SCRATCH" 2>/dev/null | cut -f1 || echo "0")

    echo "当前使用 / Current usage: $scratch_size"

    # 列出 Scratch 中的目录
    echo -e "\n目录内容 / Directory contents:"
    ls -lah "$SCRATCH" 2>/dev/null | head -20 || echo "(空目录)"

    # 警告: Scratch 3个月自动清理
    echo -e "\n${YELLOW}⚠️  提醒: Scratch 数据每 3 个月自动清理，请及时备份重要数据${NC}"
}

# 检查 Home 目录使用 / Check Home directory usage
check_home_usage() {
    echo -e "\n${BLUE}🏠 Home 目录使用 (\$HOME)${NC}"
    print_separator

    echo "Home 目录: $HOME"

    # 计算总使用量
    local home_size
    home_size=$(du -sh "$HOME" 2>/dev/null | cut -f1 || echo "unknown")
    echo "总使用量 / Total usage: $home_size"

    # 显示子目录占用
    echo -e "\n子目录占用 / Subdirectory usage:"
    du -sh "$HOME"/* 2>/dev/null | sort -hr | head -"$TOP_N"
}

# 查找大文件 / Find large files
find_large_files() {
    echo -e "\n${BLUE}🔍 大文件列表 (>100MB)${NC}"
    print_separator

    echo "Top $TOP_N 大文件 / Largest files:"
    find "$HOME" -type f -size +100M -exec ls -lh {} \; 2>/dev/null | \
        sort -k5 -hr | head -"$TOP_N" | \
        awk '{print $5 "\t" $9}'

    # 查找旧的日志文件
    echo -e "\n${YELLOW}可清理的旧文件 (>30天) / Old files (>30 days):${NC}"
    find "$HOME" -type f \( -name "*.log" -o -name "slurm-*.out" -o -name "*.err" \) \
        -mtime +30 2>/dev/null | head -"$TOP_N" || echo "(无)"
}

# 显示清理建议 / Show cleanup suggestions
show_cleanup_suggestions() {
    echo -e "\n${BLUE}💡 清理建议 / Cleanup Suggestions${NC}"
    print_separator

    cat << 'EOF'
1. 清理 Conda 缓存 / Clean Conda cache:
   conda clean --all

2. 清理 pip 缓存 / Clean pip cache:
   pip cache purge

3. 删除旧日志 / Remove old logs:
   find $HOME -name "*.log" -mtime +30 -delete
   find $HOME -name "slurm-*.out" -mtime +30 -delete

4. 归档到冷存储 / Archive to cold storage:
   # 登录传输节点 / Login to transfer node
   ssh data.hpc.sjtu.edu.cn
   # 使用 rsync 归档 / Archive with rsync
   rsync -avP $HOME/old_project/ $UNION/archive/old_project/

5. 压缩不常用数据 / Compress inactive data:
   tar -czvf project.tar.gz project/
   rm -rf project/

EOF
}

# 主程序 / Main program
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║        SJTU HPC 配额监控 / Quota Monitor                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo "用户 / User: $USER"
    echo "时间 / Time: $(date)"
    echo "警告阈值 / Warning threshold: ${WARNING_THRESHOLD}%"

    local cluster
    cluster=$(detect_cluster)
    echo "集群 / Cluster: $cluster"

    # 根据集群类型检查配额
    case $cluster in
        siyuan)
            check_gpfs_quota
            ;;
        pi2)
            check_lustre_quota
            ;;
        *)
            echo "⚠️  未知集群类型，尝试通用检查"
            quota -s 2>/dev/null || echo "quota 命令不可用"
            ;;
    esac

    check_scratch_usage
    check_home_usage
    find_large_files
    show_cleanup_suggestions

    echo -e "\n${GREEN}✅ 配额检查完成${NC}"
}

# 运行主程序
main
