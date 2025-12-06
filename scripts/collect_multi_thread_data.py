#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据系统 - 多线程数据收集程序
使用多线程并发收集提高数据收集效率
"""

import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 导入模块
try:
    from src.multi_thread_collector import MultiThreadCollector, get_optimal_thread_count
    from src.database import StockDataDB
    from src.logger import get_logger
    from src.data_collector import AkshareDataCollector
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在BettaFish环境中运行，并且所有依赖包已安装")
    sys.exit(1)

# 信号处理
import signal

class GracefulKiller:
    """优雅停止处理器"""
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        print(f"\n检测到中断信号 {signum}，正在优雅退出...")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='多线程股票数据收集程序')

    parser.add_argument('--mode', type=int, choices=[1, 2, 3, 4], default=4,
                       help='收集模式: 1=测试(10只), 2=小量(100只), 3=中量(1000只), 4=完整(全部)')

    parser.add_argument('--workers', type=int, default=None,
                       help=f'线程数 (默认自动推荐: {get_optimal_thread_count()})')

    parser.add_argument('--delay', type=float, default=0.3,
                       help='请求延迟(秒), 默认0.3秒')

    parser.add_argument('--auto', action='store_true',
                       help='自动模式，不需要确认')

    return parser.parse_args()


def get_pending_stocks(db, all_stock_codes):
    """获取待收集的股票列表，自动跳过已完成的股票"""
    logger = get_logger()
    logger.info("正在检查已完成的股票...")

    try:
        # 获取已完成数据收集的股票代码
        completed_codes = set(db.get_completed_stock_codes())

        # 过滤出待收集的股票代码
        pending_codes = []
        for code in all_stock_codes:
            if code not in completed_codes:
                pending_codes.append(code)
            else:
                # 检查数据质量，确保数据完整
                count = db.get_stock_data_count(code)
                if count < 100:  # 假设正常股票应该有超过100条记录
                    logger.warning(f"股票 {code} 数据不完整 ({count} 条记录)，重新收集")
                    pending_codes.append(code)

        logger.info(f"已完成: {len(completed_codes)} 只股票")
        logger.info(f"待收集: {len(pending_codes)} 只股票")

        if completed_codes:
            logger.info(f"已完成的股票: {sorted(list(completed_codes))[:10]}...")

        return pending_codes, len(completed_codes)

    except Exception as e:
        logger.error(f"获取待处理股票失败: {e}")
        return all_stock_codes, 0


def show_database_info(db):
    """显示数据库信息"""
    try:
        info = db.get_database_info()
        print(f"  技术数据记录: {info.get('technical_data_records', 0):,}")
        print(f"  股票主表记录: {info.get('stock_master_records', 0):,}")
        print(f"  数据库大小: {info.get('database_size_mb', 0):.2f} MB")
    except Exception as e:
        print(f"  无法获取数据库信息: {e}")


def main():
    args = parse_arguments()
    killer = GracefulKiller()
    logger = get_logger()

    # 模式限制
    mode_limits = {1: 10, 2: 100, 3: 1000, 4: None}
    limit = mode_limits[args.mode]
    mode_names = {1: "测试模式", 2: "小量模式", 3: "中量模式", 4: "完整模式"}

    # 线程数设置
    if args.workers is None:
        max_workers = get_optimal_thread_count()
    else:
        max_workers = args.workers

    print("=" * 80)
    print("股票数据系统 - 多线程数据收集程序")
    print("=" * 80)
    print("收集范围: 2018年1月1日 至今的所有A股历史数据")
    print("多线程特性:")
    print(f"  ✓ 并发收集: {max_workers} 线程同时工作")
    print(f"  ✓ 智能延迟: {args.delay} 秒基础延迟避免API限制")
    print("  ✓ 进度跟踪: 实时显示收集进度和预估时间")
    print("  ✓ 错误隔离: 单个失败不影响整体进度")
    print("  ✓ 自动续传: 跳过已完成股票，支持中断后继续")
    print("=" * 80)
    print("提示: 任何时候按 Ctrl+C 可以安全停止程序")

    # 如果不是自动模式，询问用户是否继续
    if not args.auto:
        try:
            confirm = input(f"\n确认开始{mode_names[args.mode]}数据收集? (y/n): ").lower().strip()
            if confirm not in ['y', 'yes', '是', '开始']:
                print("程序已取消")
                return
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            return

    print(f"\n开始多线程数据收集...")
    print(f"模式: {mode_names[args.mode]}")
    if limit:
        print(f"限制: 只收集前 {limit} 只股票")
    else:
        print("模式: 收集所有股票数据")
    print(f"并发: {max_workers} 线程")

    start_time = datetime.now()
    print(f"开始时间: {start_time}")

    try:
        # 获取数据库信息
        db = StockDataDB()
        print("\n当前数据库状态:")
        show_database_info(db)

        # 获取股票代码
        collector = AkshareDataCollector()
        all_stock_codes = collector.get_stock_list()

        if all_stock_codes is None or all_stock_codes.empty:
            print("错误：无法获取股票代码列表")
            return

        # 提取股票代码
        if 'stock_code' in all_stock_codes.columns:
            all_stock_codes = all_stock_codes['stock_code'].tolist()
        elif 'code' in all_stock_codes.columns:
            all_stock_codes = all_stock_codes['code'].tolist()
        elif '股票代码' in all_stock_codes.columns:
            all_stock_codes = all_stock_codes['股票代码'].tolist()
        else:
            print(f"无法找到股票代码列，可用列: {list(all_stock_codes.columns)}")
            return

        # 排序确保一致性
        all_stock_codes.sort()

        # 应用限制
        if limit and limit > 0:
            all_stock_codes = all_stock_codes[:limit]

        print(f"\n总股票数: {len(all_stock_codes)}")

        # 获取待收集股票
        pending_stocks, completed_count = get_pending_stocks(db, all_stock_codes)

        if not pending_stocks:
            print("\n✅ 所有股票数据收集已完成！")
            return

        # 设置时间范围
        start_date = "20180101"
        end_date = datetime.now().strftime("%Y%m%d")

        # 创建多线程收集器
        multi_collector = MultiThreadCollector(
            max_workers=max_workers,
            delay=args.delay
        )

        print(f"\n开始多线程收集 {len(pending_stocks)} 只股票...")
        print(f"并发线程数: {max_workers}")
        print(f"时间范围: {start_date} - {end_date}")

        # 开始多线程收集
        result = multi_collector.collect_all_data(
            pending_stocks,
            start_date,
            end_date
        )

        # 显示最终结果
        end_time = datetime.now()
        duration = end_time - start_time

        print(f"\n结束时间: {end_time}")
        print(f"总耗时: {duration}")

        print(f"\n最终数据库状态:")
        show_database_info(db)

        if result['failed'] > 0:
            print(f"\n⚠️  有 {result['failed']} 只股票收集失败:")
            print(f"   {result['failed_stocks'][:10]}{'...' if len(result['failed_stocks']) > 10 else ''}")
            print("   您可以重新运行程序，系统会自动重试失败的股票")

        print(f"\n📊 收集统计:")
        print(f"   处理股票: {result['total']} 只")
        print(f"   成功收集: {result['success']} 只")
        print(f"   收集失败: {result['failed']} 只")
        print(f"   成功率: {result['success']/result['total']*100:.1f}%")

    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()