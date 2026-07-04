#!/bin/bash
# hpc-sync.sh - 本地 <-> HPC 项目同步脚本
# Seamless project synchronization between local and SJTU HPC
#
# 使用方法 / Usage:
#   hpc-sync push              # 推送本地项目到 HPC
#   hpc-sync pull              # 拉取 HPC 结果到本地
#   hpc-sync status            # 查看同步状态
#   hpc-sync init              # 初始化项目配置
#
# 配置文件: .hpc-sync.conf (项目根目录)

set -euo pipefail

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置文件名
CONFIG_FILE=".hpc-sync.conf"

# 默认排除列表 (适用于 R/Python 计算社会科学项目)
# 设计原则：隔离方案 - 本地和 HPC 各自维护独立的构建状态
DEFAULT_EXCLUDES=(
    # 版本控制
    ".git"
    # R 临时文件
    ".Rhistory"
    ".RData"
    ".Rproj.user"
    # Python 临时文件
    "__pycache__"
    "*.pyc"
    ".pytest_cache"
    ".mypy_cache"
    # 编辑器临时文件
    ".DS_Store"
    "*.swp"
    "*.swo"
    # 日志 (每边各自的)
    "*.log"
    # R targets - 整个目录排除！本地和 HPC 各自独立维护
    # 这样最安全：不会有元数据冲突，不会传输巨大的 objects
    "_targets"
    # GNU Make 构建产物 (如果用 Make)
    # 注意：不排除 build/，因为可能包含需要的中间数据
)

# 显示帮助
show_help() {
    cat << 'EOF'
hpc-sync - 本地 <-> HPC 项目同步

命令:
    push        推送本地项目到 HPC (代码 + 数据)
    pull        拉取 HPC 结果到本地 (output/ 目录)
    pull-all    拉取 HPC 全部内容到本地
    status      查看本地与 HPC 的差异
    init        初始化项目配置文件
    run <cmd>   在 HPC 上执行命令 (如: hpc-sync run "make analysis")

配置:
    项目根目录需要 .hpc-sync.conf 文件，格式:

    HPC_HOST=sydata.hpc.sjtu.edu.cn
    HPC_USER=your_username
    HPC_PATH=/dssg/home/acct-XXX/username/project_name
    EXCLUDE_EXTRA=("large_cache" "temp_data")

示例:
    cd ~/projects/my_research
    hpc-sync init                    # 首次配置
    hpc-sync push                    # 推送到 HPC
    ssh user@sylogin... "sbatch job.slurm"  # 提交作业
    hpc-sync pull                    # 回收结果

EOF
}

# 查找项目根目录 (向上查找 .hpc-sync.conf)
find_project_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/$CONFIG_FILE" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

# 加载配置
load_config() {
    local project_root
    if ! project_root=$(find_project_root); then
        echo -e "${RED}错误: 未找到 $CONFIG_FILE${NC}"
        echo "请先运行 'hpc-sync init' 初始化项目"
        exit 1
    fi

    cd "$project_root"
    source "$CONFIG_FILE"

    # 验证必需配置
    if [[ -z "${HPC_HOST:-}" || -z "${HPC_USER:-}" || -z "${HPC_PATH:-}" ]]; then
        echo -e "${RED}错误: 配置不完整${NC}"
        echo "请检查 $CONFIG_FILE 包含 HPC_HOST, HPC_USER, HPC_PATH"
        exit 1
    fi
}

# 初始化配置
init_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        echo -e "${YELLOW}警告: $CONFIG_FILE 已存在${NC}"
        read -p "是否覆盖? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi

    echo -e "${BLUE}初始化 HPC 同步配置${NC}"
    echo ""

    # 获取用户输入
    read -p "HPC 传输节点 [sydata.hpc.sjtu.edu.cn]: " host
    host=${host:-sydata.hpc.sjtu.edu.cn}

    read -p "HPC 用户名: " user
    if [[ -z "$user" ]]; then
        echo -e "${RED}错误: 用户名不能为空${NC}"
        exit 1
    fi

    local default_path="/dssg/home/acct-XXX/$user/$(basename "$PWD")"
    read -p "HPC 项目路径 [$default_path]: " path
    path=${path:-$default_path}

    # 写入配置
    cat > "$CONFIG_FILE" << EOF
# HPC 同步配置 - 由 hpc-sync init 生成
# 请根据实际情况修改

# HPC 连接信息
HPC_HOST=$host
HPC_USER=$user
HPC_PATH=$path

# 额外排除的文件/目录 (可选)
# EXCLUDE_EXTRA=("large_cache" "temp_data")

# 仅拉取这些目录的结果 (默认 output/)
# PULL_DIRS=("output" "results" "figures")
EOF

    echo -e "${GREEN}✅ 配置已保存到 $CONFIG_FILE${NC}"
    echo ""
    echo "下一步:"
    echo "  1. 编辑 $CONFIG_FILE 确认路径正确"
    echo "  2. 运行 'hpc-sync push' 推送项目"
}

# 构建 rsync 排除参数
build_excludes() {
    local excludes=()

    # 添加默认排除
    for item in "${DEFAULT_EXCLUDES[@]}"; do
        excludes+=("--exclude=$item")
    done

    # 添加用户自定义排除
    if [[ -n "${EXCLUDE_EXTRA:-}" ]]; then
        for item in "${EXCLUDE_EXTRA[@]}"; do
            excludes+=("--exclude=$item")
        done
    fi

    echo "${excludes[@]}"
}

# 推送到 HPC
do_push() {
    load_config

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}推送项目到 HPC${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "本地: $(pwd)"
    echo "远程: ${HPC_USER}@${HPC_HOST}:${HPC_PATH}"
    echo ""

    local excludes
    excludes=$(build_excludes)

    # 创建远程目录
    ssh "${HPC_USER}@${HPC_HOST}" "mkdir -p ${HPC_PATH}"

    # rsync 推送
    # shellcheck disable=SC2086
    rsync -avP --delete \
        $excludes \
        ./ "${HPC_USER}@${HPC_HOST}:${HPC_PATH}/"

    echo ""
    echo -e "${GREEN}✅ 推送完成${NC}"
}

# 从 HPC 拉取结果
do_pull() {
    load_config

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}拉取 HPC 结果${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # 默认拉取目录
    local pull_dirs=("output" "results" "figures" "build")
    if [[ -n "${PULL_DIRS:-}" ]]; then
        pull_dirs=("${PULL_DIRS[@]}")
    fi

    for dir in "${pull_dirs[@]}"; do
        # 检查远程目录是否存在
        if ssh "${HPC_USER}@${HPC_HOST}" "test -d ${HPC_PATH}/${dir}"; then
            echo "拉取: ${dir}/"
            mkdir -p "${dir}"
            rsync -avP "${HPC_USER}@${HPC_HOST}:${HPC_PATH}/${dir}/" "${dir}/"
        fi
    done

    # 注意：不同步 _targets/，本地和 HPC 各自独立维护
    # 如果需要 HPC 的 targets 对象，请手动：
    # rsync -avP user@hpc:path/_targets/objects/specific_target ./

    echo ""
    echo -e "${GREEN}✅ 拉取完成${NC}"
}

# 拉取全部
do_pull_all() {
    load_config

    echo -e "${BLUE}拉取 HPC 全部内容${NC}"

    local excludes
    excludes=$(build_excludes)

    # shellcheck disable=SC2086
    rsync -avP \
        $excludes \
        "${HPC_USER}@${HPC_HOST}:${HPC_PATH}/" ./

    echo -e "${GREEN}✅ 全量拉取完成${NC}"
}

# 查看状态
do_status() {
    load_config

    echo -e "${BLUE}同步状态${NC}"
    echo ""
    echo "本地: $(pwd)"
    echo "远程: ${HPC_USER}@${HPC_HOST}:${HPC_PATH}"
    echo ""

    local excludes
    excludes=$(build_excludes)

    echo "差异文件 (本地 vs HPC):"
    # shellcheck disable=SC2086
    rsync -avPn --delete \
        $excludes \
        ./ "${HPC_USER}@${HPC_HOST}:${HPC_PATH}/" 2>/dev/null | grep -v "^$" | head -30 || echo "(无差异)"
}

# 在 HPC 上执行命令
do_run() {
    load_config
    local cmd="$*"

    if [[ -z "$cmd" ]]; then
        echo -e "${RED}错误: 请指定要执行的命令${NC}"
        echo "用法: hpc-sync run \"make analysis\""
        exit 1
    fi

    echo -e "${BLUE}在 HPC 上执行: $cmd${NC}"
    # 使用登录节点执行 (注意: 不要在登录节点跑计算!)
    local login_host="${HPC_HOST/data/login}"
    login_host="${login_host/sydata/sylogin}"

    ssh "${HPC_USER}@${login_host}" "cd ${HPC_PATH} && $cmd"
}

# 主程序
main() {
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi

    local cmd="$1"
    shift

    case "$cmd" in
        push)
            do_push
            ;;
        pull)
            do_pull
            ;;
        pull-all)
            do_pull_all
            ;;
        status)
            do_status
            ;;
        init)
            init_config
            ;;
        run)
            do_run "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}未知命令: $cmd${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
