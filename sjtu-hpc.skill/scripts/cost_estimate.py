#!/usr/bin/env python3
"""
cost_estimate.py - SJTU HPC 成本计算器
SJTU HPC Cost Estimator

功能 / Features:
- 根据资源配置估算作业费用
- 支持 CPU 和 GPU 队列
- 输出详细费用明细

使用方法 / Usage:
    python cost_estimate.py --cores 64 --hours 24 --queue 64c512g
    python cost_estimate.py --gpus 2 --hours 48 --queue a100
    python cost_estimate.py --interactive
    python cost_estimate.py --help

收费标准来源 / Pricing Reference:
    参考 SKILL.md 中的计费标准 (2024)
"""

import argparse
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class QueueConfig:
    """队列配置 / Queue configuration"""
    name: str
    cluster: str
    price_unit: str  # 计费单位: core-hour 或 gpu-hour
    price: float     # 单价 (元)
    cpu_per_gpu: int = 0  # GPU 队列的 CPU:GPU 比例
    mem_per_core: float = 0  # 每核内存 (GB)
    max_time_hours: int = 168  # 最大时长 (小时)
    is_gpu: bool = False
    note: str = ""


# 队列配置数据 (2024年收费标准)
QUEUES = {
    # CPU 队列
    "64c512g": QueueConfig(
        name="64c512g", cluster="Siyuan-1", price_unit="core-hour",
        price=0.03, mem_per_core=8, max_time_hours=168,
        note="思源一号 CPU 队列"
    ),
    "cpu": QueueConfig(
        name="cpu", cluster="Pi 2.0", price_unit="core-hour",
        price=0.02, mem_per_core=4, max_time_hours=168,
        note="Pi 2.0 CPU 队列 (独占)"
    ),
    "small": QueueConfig(
        name="small", cluster="Pi 2.0", price_unit="core-hour",
        price=0.02, mem_per_core=4, max_time_hours=168,
        note="Pi 2.0 小规模队列 (共享)"
    ),
    "huge": QueueConfig(
        name="huge", cluster="Pi 2.0", price_unit="core-hour",
        price=0.02, mem_per_core=35, max_time_hours=48,
        note="Pi 2.0 大内存队列"
    ),
    "192c6t": QueueConfig(
        name="192c6t", cluster="Pi 2.0", price_unit="core-hour",
        price=0.02, mem_per_core=31, max_time_hours=48,
        note="Pi 2.0 超大内存队列"
    ),
    "arm128c256g": QueueConfig(
        name="arm128c256g", cluster="ARM", price_unit="core-hour",
        price=0.01, mem_per_core=2, max_time_hours=168,
        note="ARM 平台"
    ),
    # GPU 队列
    "a100": QueueConfig(
        name="a100", cluster="Siyuan-1", price_unit="gpu-hour",
        price=2.50, cpu_per_gpu=16, mem_per_core=8, max_time_hours=168,
        is_gpu=True, note="A100 40GB"
    ),
    "dgx2": QueueConfig(
        name="dgx2", cluster="AI Platform", price_unit="gpu-hour",
        price=2.00, cpu_per_gpu=6, mem_per_core=15, max_time_hours=168,
        is_gpu=True, note="V100 32GB"
    ),
    "a800": QueueConfig(
        name="a800", cluster="Siyuan-1", price_unit="gpu-hour",
        price=2.50, cpu_per_gpu=16, mem_per_core=8, max_time_hours=168,
        is_gpu=True, note="A800"
    ),
    # 免费队列
    "debug": QueueConfig(
        name="debug", cluster="Pi 2.0", price_unit="core-hour",
        price=0.00, mem_per_core=4, max_time_hours=0.33,
        note="免费调试队列"
    ),
    "debug64c512g": QueueConfig(
        name="debug64c512g", cluster="Siyuan-1", price_unit="core-hour",
        price=0.00, mem_per_core=8, max_time_hours=1,
        note="免费调试队列"
    ),
    "debuga100": QueueConfig(
        name="debuga100", cluster="Siyuan-1", price_unit="gpu-hour",
        price=0.00, cpu_per_gpu=4, mem_per_core=8, max_time_hours=0.33,
        is_gpu=True, note="免费 GPU 调试队列 (5GB vGPU)"
    ),
}

# 存储费用 (元/TB/月)
STORAGE_PRICES = {
    "lustre": 0.28,
    "dssg": 0.28,
    "archive": 0.07,
}


def estimate_job_cost(
    queue: str,
    hours: float,
    cores: Optional[int] = None,
    gpus: Optional[int] = None,
    nodes: Optional[int] = None,
) -> dict:
    """
    估算作业费用 / Estimate job cost

    Args:
        queue: 队列名称
        hours: 运行时长 (小时)
        cores: CPU 核心数 (CPU 队列必需)
        gpus: GPU 卡数 (GPU 队列必需)
        nodes: 节点数 (可选)

    Returns:
        包含费用明细的字典
    """
    if queue not in QUEUES:
        raise ValueError(f"未知队列: {queue}. 可用队列: {list(QUEUES.keys())}")

    config = QUEUES[queue]

    result = {
        "queue": queue,
        "cluster": config.cluster,
        "hours": hours,
        "price_unit": config.price_unit,
        "unit_price": config.price,
        "note": config.note,
    }

    if config.is_gpu:
        if gpus is None:
            raise ValueError(f"GPU 队列 {queue} 需要指定 --gpus 参数")

        result["gpus"] = gpus
        result["cores"] = gpus * config.cpu_per_gpu
        result["memory_gb"] = result["cores"] * config.mem_per_core
        result["gpu_hours"] = gpus * hours
        result["total_cost"] = gpus * hours * config.price

    else:
        if cores is None:
            raise ValueError(f"CPU 队列 {queue} 需要指定 --cores 参数")

        result["cores"] = cores
        result["memory_gb"] = cores * config.mem_per_core
        result["core_hours"] = cores * hours
        result["total_cost"] = cores * hours * config.price

    # 检查时长限制
    if hours > config.max_time_hours:
        result["warning"] = f"⚠️ 超过最大时长限制 ({config.max_time_hours}小时)"

    return result


def format_cost_report(result: dict) -> str:
    """格式化费用报告 / Format cost report"""
    lines = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║           SJTU HPC 作业费用估算 / Job Cost Estimate          ║",
        "╚══════════════════════════════════════════════════════════════╝",
        "",
        f"队列 / Queue:          {result['queue']} ({result['cluster']})",
        f"说明 / Note:           {result['note']}",
        "",
        "━━━━━━━━━━━━━ 资源配置 / Resource Configuration ━━━━━━━━━━━━━━",
    ]

    if "gpus" in result:
        lines.extend([
            f"GPU 卡数:              {result['gpus']} 卡",
            f"CPU 核数:              {result['cores']} 核 (自动分配)",
        ])
    else:
        lines.append(f"CPU 核数:              {result['cores']} 核")

    lines.extend([
        f"内存:                  {result['memory_gb']:.0f} GB",
        f"运行时长:              {result['hours']:.1f} 小时",
        "",
        "━━━━━━━━━━━━━━━━ 费用计算 / Cost Calculation ━━━━━━━━━━━━━━━━",
        f"计费单位:              {result['price_unit']}",
        f"单价:                  ¥{result['unit_price']:.2f} / {result['price_unit']}",
    ])

    if "gpu_hours" in result:
        lines.append(f"GPU-小时:              {result['gpu_hours']:.1f} gpu-hours")
    else:
        lines.append(f"核-小时:               {result['core_hours']:.1f} core-hours")

    lines.extend([
        "",
        f"{'─' * 40}",
        f"💰 预估总费用:         ¥{result['total_cost']:.2f}",
        f"{'─' * 40}",
    ])

    if "warning" in result:
        lines.extend(["", result["warning"]])

    return "\n".join(lines)


def estimate_storage_cost(tb: float, storage_type: str = "lustre", months: int = 1) -> dict:
    """
    估算存储费用 / Estimate storage cost

    Args:
        tb: 存储量 (TB)
        storage_type: 存储类型 (lustre, dssg, archive)
        months: 月数

    Returns:
        包含费用明细的字典
    """
    if storage_type not in STORAGE_PRICES:
        raise ValueError(f"未知存储类型: {storage_type}")

    price = STORAGE_PRICES[storage_type]
    total = tb * price * months

    return {
        "storage_type": storage_type,
        "size_tb": tb,
        "months": months,
        "price_per_tb_month": price,
        "total_cost": total,
    }


def interactive_mode():
    """交互模式 / Interactive mode"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           SJTU HPC 成本计算器 (交互模式)                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # 显示可用队列
    print("可用队列 / Available queues:")
    print("-" * 60)
    print(f"{'队列':<15} {'集群':<12} {'类型':<8} {'单价':<10} {'说明'}")
    print("-" * 60)
    for name, q in QUEUES.items():
        qtype = "GPU" if q.is_gpu else "CPU"
        print(f"{name:<15} {q.cluster:<12} {qtype:<8} ¥{q.price:<9.2f} {q.note}")
    print("-" * 60)
    print()

    # 获取用户输入
    queue = input("请输入队列名称 / Enter queue name: ").strip()

    if queue not in QUEUES:
        print(f"错误: 未知队列 '{queue}'")
        return

    config = QUEUES[queue]

    if config.is_gpu:
        gpus = int(input("请输入 GPU 卡数 / Enter number of GPUs: "))
        cores = None
    else:
        cores = int(input("请输入 CPU 核数 / Enter number of cores: "))
        gpus = None

    hours = float(input("请输入运行时长 (小时) / Enter runtime in hours: "))

    # 计算并显示结果
    try:
        result = estimate_job_cost(queue, hours, cores=cores, gpus=gpus)
        print()
        print(format_cost_report(result))
    except ValueError as e:
        print(f"错误: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="SJTU HPC 成本计算器 / Cost Estimator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 / Examples:
    # CPU 作业费用估算
    %(prog)s --queue 64c512g --cores 64 --hours 24

    # GPU 作业费用估算
    %(prog)s --queue a100 --gpus 2 --hours 48

    # 存储费用估算
    %(prog)s --storage 5 --storage-type lustre --months 12

    # 交互模式
    %(prog)s --interactive

收费标准 (2024):
    CPU: 0.01-0.03 元/核时
    GPU: 2.00-2.50 元/卡时
    存储: 0.07-0.28 元/TB/月
        """
    )

    parser.add_argument("--queue", "-q", help="队列名称 / Queue name")
    parser.add_argument("--cores", "-c", type=int, help="CPU 核数 / Number of cores")
    parser.add_argument("--gpus", "-g", type=int, help="GPU 卡数 / Number of GPUs")
    parser.add_argument("--hours", "-t", type=float, help="运行时长 (小时) / Runtime in hours")
    parser.add_argument("--nodes", "-n", type=int, help="节点数 / Number of nodes")

    parser.add_argument("--storage", type=float, help="存储量 (TB) / Storage size in TB")
    parser.add_argument("--storage-type", default="lustre",
                       choices=["lustre", "dssg", "archive"],
                       help="存储类型 / Storage type")
    parser.add_argument("--months", type=int, default=1, help="月数 / Number of months")

    parser.add_argument("--interactive", "-i", action="store_true",
                       help="交互模式 / Interactive mode")
    parser.add_argument("--list-queues", action="store_true",
                       help="列出所有队列 / List all queues")

    args = parser.parse_args()

    if args.list_queues:
        print("可用队列 / Available queues:")
        print("-" * 70)
        print(f"{'队列':<15} {'集群':<12} {'类型':<8} {'单价':<12} {'说明'}")
        print("-" * 70)
        for name, q in QUEUES.items():
            qtype = "GPU" if q.is_gpu else "CPU"
            unit = "卡时" if q.is_gpu else "核时"
            print(f"{name:<15} {q.cluster:<12} {qtype:<8} ¥{q.price:.2f}/{unit:<4} {q.note}")
        return

    if args.interactive:
        interactive_mode()
        return

    if args.storage:
        result = estimate_storage_cost(args.storage, args.storage_type, args.months)
        print(f"存储费用估算:")
        print(f"  存储类型: {result['storage_type']}")
        print(f"  存储量: {result['size_tb']:.1f} TB")
        print(f"  月数: {result['months']}")
        print(f"  单价: ¥{result['price_per_tb_month']:.2f}/TB/月")
        print(f"  总费用: ¥{result['total_cost']:.2f}")
        return

    if not args.queue or not args.hours:
        parser.print_help()
        print("\n错误: 请指定 --queue 和 --hours 参数，或使用 --interactive 模式")
        sys.exit(1)

    try:
        result = estimate_job_cost(
            args.queue, args.hours,
            cores=args.cores, gpus=args.gpus, nodes=args.nodes
        )
        print(format_cost_report(result))
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
