#!/bin/bash
# backup_to_union.sh - SJTU HPC 归档脚本
# Archive data to Scientific Big Data Platform (科学大数据平台)
#
# 功能 / Features:
# - 使用 rsync 归档数据到 $UNION
# - 自动生成 MD5 校验和验证完整性
# - 可选删除源文件释放配额
#
# 使用方法 / Usage:
#   ./backup_to_union.sh <source_dir> [dest_subdir]
#   ./backup_to_union.sh --help
#
# 示例 / Examples:
#   ./backup_to_union.sh ~/projects/completed_2024
#   ./backup_to_union.sh ~/projects/completed_2024 archive/2024
#   ./backup_to_union.sh ~/projects/old_data --delete-source
#
# 重要说明 / Important:
#   必须在传输节点 (data.hpc.sjtu.edu.cn 或 sydata.hpc.sjtu.edu.cn) 上运行
#   Must run on transfer nodes (data.hpc.sjtu.edu.cn or sydata.hpc.sjtu.edu.cn)

set -euo pipefail

# 颜色定义 / Color definitions
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 默认参数
DELETE_SOURCE=false
DRY_RUN=false

# 帮助信息 / Help message
show_help() {
    cat << EOF
SJTU HPC 归档脚本 / Archive Script to Scientific Big Data Platform

使用方法 / Usage:
    $0 <source_dir> [dest_subdir] [选项]

参数 / Arguments:
    source_dir      要归档的源目录 (必需)
                    Source directory to archive (required)

    dest_subdir     目标子目录，相对于 \$UNION (可选)
                    Destination subdirectory under \$UNION (optional)
                    默认使用源目录名

选项 / Options:
    --delete-source 校验成功后删除源文件 (危险操作!)
                    Delete source files after verification (dangerous!)

    --dry-run       仅显示将执行的操作，不实际执行
                    Show what would be done without doing it

    --help          显示此帮助信息
                    Show this help message

示例 / Examples:
    # 归档到默认位置
    $0 ~/projects/completed_2024

    # 归档到指定子目录
    $0 ~/projects/completed_2024 archive/projects/2024

    # 预览操作 (不实际执行)
    $0 ~/projects/old_data --dry-run

    # 归档并删除源文件 (谨慎使用!)
    $0 ~/projects/old_data --delete-source

重要说明 / Important Notes:
    1. 必须在传输节点上运行 (data.hpc.sjtu.edu.cn 或 sydata.hpc.sjtu.edu.cn)
       Must run on transfer nodes

    2. 计算节点上只能读取 \$UNION，不能写入
       Compute nodes have read-only access to \$UNION

    3. 科学大数据平台支持快照恢复，是最安全的长期存储选择
       Scientific Big Data Platform supports snapshot recovery

EOF
}

# 检查是否在传输节点 / Check if on transfer node
check_transfer_node() {
    local hostname
    hostname=$(hostname)

    if [[ "$hostname" != *"data"* && "$hostname" != *"sydata"* ]]; then
        echo -e "${YELLOW}⚠️  警告: 当前主机 ($hostname) 可能不是传输节点${NC}"
        echo "建议在传输节点上运行此脚本:"
        echo "  ssh data.hpc.sjtu.edu.cn     # Pi 2.0"
        echo "  ssh sydata.hpc.sjtu.edu.cn   # 思源一号"
        echo ""
        read -p "是否继续? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查环境变量 / Check environment variables
check_environment() {
    if [[ -z "${UNION:-}" ]]; then
        echo -e "${RED}❌ 错误: \$UNION 环境变量未设置${NC}"
        echo "请确保在 HPC 集群上运行此脚本"
        exit 1
    fi

    if [[ ! -d "$UNION" ]]; then
        echo -e "${RED}❌ 错误: \$UNION 目录不存在: $UNION${NC}"
        exit 1
    fi
}

# 计算目录 MD5 校验和 / Calculate directory MD5 checksums
calculate_checksums() {
    local dir=$1
    local output_file=$2

    echo "计算校验和 / Calculating checksums: $dir"
    find "$dir" -type f -exec md5sum {} \; | sort > "$output_file"
}

# 比较校验和 / Compare checksums
compare_checksums() {
    local source_md5=$1
    local dest_md5=$2

    if diff -q "$source_md5" "$dest_md5" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 主归档函数 / Main archive function
archive_directory() {
    local source_dir=$1
    local dest_subdir=${2:-$(basename "$source_dir")}
    local dest_dir="$UNION/$dest_subdir"

    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║        SJTU HPC 数据归档 / Data Archive                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo "源目录 / Source:      $source_dir"
    echo "目标目录 / Destination: $dest_dir"
    echo "删除源文件 / Delete source: $DELETE_SOURCE"
    echo "预览模式 / Dry run: $DRY_RUN"
    echo ""

    # 检查源目录存在
    if [[ ! -d "$source_dir" ]]; then
        echo -e "${RED}❌ 错误: 源目录不存在: $source_dir${NC}"
        exit 1
    fi

    # 计算源目录大小
    local source_size
    source_size=$(du -sh "$source_dir" | cut -f1)
    echo "源目录大小 / Source size: $source_size"

    # 统计文件数量
    local file_count
    file_count=$(find "$source_dir" -type f | wc -l)
    echo "文件数量 / File count: $file_count"
    echo ""

    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${YELLOW}[预览模式] 将执行以下操作:${NC}"
        echo "1. rsync -avP --checksum $source_dir/ $dest_dir/"
        echo "2. 生成并比较 MD5 校验和"
        if [[ "$DELETE_SOURCE" == true ]]; then
            echo "3. 删除源目录 (校验成功后)"
        fi
        echo ""
        echo "rsync 预览:"
        rsync -avP --checksum --dry-run "$source_dir/" "$dest_dir/"
        return 0
    fi

    # 确认操作
    echo -e "${YELLOW}即将开始归档，这可能需要较长时间...${NC}"
    read -p "确认继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "操作已取消"
        exit 0
    fi

    # Step 1: 创建目标目录
    echo -e "\n${BLUE}[Step 1/4] 创建目标目录...${NC}"
    mkdir -p "$dest_dir"

    # Step 2: 使用 rsync 传输
    echo -e "\n${BLUE}[Step 2/4] 使用 rsync 传输数据...${NC}"
    rsync -avP --checksum "$source_dir/" "$dest_dir/"

    # Step 3: 验证数据完整性
    echo -e "\n${BLUE}[Step 3/4] 验证数据完整性...${NC}"

    local tmp_dir
    tmp_dir=$(mktemp -d)
    local source_md5="$tmp_dir/source.md5"
    local dest_md5="$tmp_dir/dest.md5"

    echo "计算源目录校验和..."
    calculate_checksums "$source_dir" "$source_md5"

    echo "计算目标目录校验和..."
    # 需要调整路径前缀以便比较
    (cd "$source_dir" && find . -type f -exec md5sum {} \; | sort) > "$source_md5"
    (cd "$dest_dir" && find . -type f -exec md5sum {} \; | sort) > "$dest_md5"

    if compare_checksums "$source_md5" "$dest_md5"; then
        echo -e "${GREEN}✅ 校验成功: 所有文件完整无误${NC}"
    else
        echo -e "${RED}❌ 校验失败: 存在不一致的文件${NC}"
        echo "差异如下:"
        diff "$source_md5" "$dest_md5" || true
        rm -rf "$tmp_dir"
        exit 1
    fi

    # 保存校验和到目标目录
    cp "$source_md5" "$dest_dir/CHECKSUMS.md5"
    echo "校验和已保存到: $dest_dir/CHECKSUMS.md5"

    # Step 4: 可选删除源文件
    if [[ "$DELETE_SOURCE" == true ]]; then
        echo -e "\n${BLUE}[Step 4/4] 删除源文件...${NC}"
        echo -e "${RED}⚠️  警告: 即将删除源目录: $source_dir${NC}"
        read -p "确认删除? 此操作不可逆! (yes/NO) " confirm
        if [[ "$confirm" == "yes" ]]; then
            rm -rf "$source_dir"
            echo -e "${GREEN}✅ 源目录已删除${NC}"
        else
            echo "跳过删除操作"
        fi
    else
        echo -e "\n${BLUE}[Step 4/4] 跳过 (未指定 --delete-source)${NC}"
    fi

    # 清理临时文件
    rm -rf "$tmp_dir"

    # 完成
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ 归档完成!                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "归档位置: $dest_dir"
    echo "校验文件: $dest_dir/CHECKSUMS.md5"
    echo ""
    echo "后续操作建议:"
    echo "  - 确认目标数据可访问: ls -la $dest_dir"
    echo "  - 验证校验和: cd $dest_dir && md5sum -c CHECKSUMS.md5"
    if [[ "$DELETE_SOURCE" != true ]]; then
        echo "  - 清理源目录 (确认无误后): rm -rf $source_dir"
    fi
}

# 解析参数 / Parse arguments
SOURCE_DIR=""
DEST_SUBDIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --delete-source)
            DELETE_SOURCE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        -*)
            echo "未知选项 / Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            if [[ -z "$SOURCE_DIR" ]]; then
                SOURCE_DIR="$1"
            elif [[ -z "$DEST_SUBDIR" ]]; then
                DEST_SUBDIR="$1"
            else
                echo "错误: 参数过多"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# 检查必需参数
if [[ -z "$SOURCE_DIR" ]]; then
    echo -e "${RED}错误: 未指定源目录${NC}"
    show_help
    exit 1
fi

# 主程序
check_transfer_node
check_environment
archive_directory "$SOURCE_DIR" "$DEST_SUBDIR"
