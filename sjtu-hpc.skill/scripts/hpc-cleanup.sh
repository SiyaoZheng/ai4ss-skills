#!/bin/bash
# hpc-cleanup.sh - HPC 资源清理脚本
# 擦干净屁股：确保不留残留作业和临时文件
#
# 使用方法:
#   hpc-cleanup             # 检查并清理当前用户的残留资源
#   hpc-cleanup --check     # 仅检查，不清理
#   hpc-cleanup --force     # 强制清理所有作业（危险！）
#
# 建议：每次会话结束前运行一次

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECK_ONLY=false
FORCE=false

show_help() {
    cat << 'EOF'
hpc-cleanup - HPC 资源清理脚本

用法:
    hpc-cleanup              检查并交互式清理
    hpc-cleanup --check      仅检查，不清理
    hpc-cleanup --force      强制取消所有作业（危险！）
    hpc-cleanup --help       显示帮助

检查内容:
    1. 运行中/排队中的作业
    2. $SCRATCH 临时目录
    3. 孤立的 screen/tmux 会话
    4. 残留的 Python/R 进程

EOF
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --check) CHECK_ONLY=true; shift ;;
        --force) FORCE=true; shift ;;
        --help|-h) show_help; exit 0 ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              HPC 资源清理检查                                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "用户: $USER"
echo "时间: $(date)"
echo ""

# ========== 1. 检查作业 ==========
echo -e "${BLUE}[1/4] 检查运行中/排队中的作业${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

JOBS=$(squeue -u "$USER" -h 2>/dev/null || true)
JOB_COUNT=$(echo "$JOBS" | grep -c . || echo 0)

if [[ $JOB_COUNT -gt 0 ]]; then
    echo -e "${YELLOW}发现 $JOB_COUNT 个作业:${NC}"
    squeue -u "$USER" -o "%.10i %.9P %.20j %.8T %.10M %.6D %R" 2>/dev/null || true
    echo ""

    if [[ "$CHECK_ONLY" == true ]]; then
        echo "(仅检查模式，跳过清理)"
    elif [[ "$FORCE" == true ]]; then
        echo -e "${RED}强制取消所有作业...${NC}"
        scancel -u "$USER"
        echo -e "${GREEN}已取消${NC}"
    else
        echo "是否取消这些作业？"
        echo "  1) 取消全部"
        echo "  2) 选择性取消"
        echo "  3) 跳过"
        read -p "选择 [3]: " choice
        choice=${choice:-3}

        case $choice in
            1)
                scancel -u "$USER"
                echo -e "${GREEN}已取消所有作业${NC}"
                ;;
            2)
                read -p "输入要取消的作业ID (空格分隔): " job_ids
                if [[ -n "$job_ids" ]]; then
                    scancel $job_ids
                    echo -e "${GREEN}已取消指定作业${NC}"
                fi
                ;;
            *)
                echo "跳过"
                ;;
        esac
    fi
else
    echo -e "${GREEN}✓ 无运行中的作业${NC}"
fi
echo ""

# ========== 2. 检查 SCRATCH ==========
echo -e "${BLUE}[2/4] 检查 \$SCRATCH 临时目录${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ -n "${SCRATCH:-}" && -d "$SCRATCH" ]]; then
    SCRATCH_SIZE=$(du -sh "$SCRATCH" 2>/dev/null | cut -f1 || echo "0")
    SCRATCH_FILES=$(find "$SCRATCH" -type f 2>/dev/null | wc -l || echo 0)

    if [[ $SCRATCH_FILES -gt 0 ]]; then
        echo -e "${YELLOW}SCRATCH 使用: $SCRATCH_SIZE ($SCRATCH_FILES 个文件)${NC}"
        echo ""
        echo "内容预览:"
        ls -la "$SCRATCH" 2>/dev/null | head -10
        echo ""

        if [[ "$CHECK_ONLY" != true ]]; then
            read -p "是否清理 SCRATCH? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -rf "${SCRATCH:?}"/*
                echo -e "${GREEN}已清理 SCRATCH${NC}"
            fi
        fi
    else
        echo -e "${GREEN}✓ SCRATCH 为空${NC}"
    fi
else
    echo "SCRATCH 环境变量未设置或目录不存在"
fi
echo ""

# ========== 3. 检查 screen/tmux ==========
echo -e "${BLUE}[3/4] 检查 screen/tmux 会话${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Screen
SCREENS=$(screen -ls 2>/dev/null | grep -c "Detached\|Attached" || echo 0)
if [[ $SCREENS -gt 0 ]]; then
    echo -e "${YELLOW}发现 $SCREENS 个 screen 会话:${NC}"
    screen -ls 2>/dev/null || true
else
    echo -e "${GREEN}✓ 无 screen 会话${NC}"
fi

# Tmux
TMUX_SESSIONS=$(tmux list-sessions 2>/dev/null | wc -l || echo 0)
if [[ $TMUX_SESSIONS -gt 0 ]]; then
    echo -e "${YELLOW}发现 $TMUX_SESSIONS 个 tmux 会话:${NC}"
    tmux list-sessions 2>/dev/null || true
else
    echo -e "${GREEN}✓ 无 tmux 会话${NC}"
fi
echo ""

# ========== 4. 检查残留进程 ==========
echo -e "${BLUE}[4/4] 检查残留进程 (登录节点)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查是否有长时间运行的 Python/R 进程
PROCS=$(ps -u "$USER" -o pid,etime,cmd 2>/dev/null | grep -E "(python|Rscript|R --)" | grep -v grep || true)
if [[ -n "$PROCS" ]]; then
    echo -e "${YELLOW}发现可能的残留进程:${NC}"
    echo "$PROCS"
    echo ""
    echo -e "${RED}警告: 登录节点禁止运行计算任务！${NC}"

    if [[ "$CHECK_ONLY" != true ]]; then
        read -p "是否终止这些进程? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "$PROCS" | awk '{print $1}' | xargs -r kill -9 2>/dev/null || true
            echo -e "${GREEN}已终止${NC}"
        fi
    fi
else
    echo -e "${GREEN}✓ 无残留计算进程${NC}"
fi
echo ""

# ========== 总结 ==========
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [[ "$CHECK_ONLY" == true ]]; then
    echo -e "${BLUE}检查完成 (仅检查模式)${NC}"
else
    echo -e "${GREEN}✅ 清理检查完成${NC}"
fi
echo ""
echo "提示: 建议每次会话结束前运行此脚本"
