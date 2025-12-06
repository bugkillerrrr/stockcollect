#!/usr/bin/env python3
"""
股票数据系统 - 启动数据收集程序（自动开始）
"""
import os
import sys
import time
from datetime import datetime

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from data_collector import AkshareDataCollector
    from logger import get_logger
    from database import StockDataDB
    from collect_full_data import FullDataCollector
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确环境中运行，并且所有依赖包已安装")
    sys.exit(1)

def main():
    """主函数"""
    print("股票数据系统 - 自动启动数据收集")
    print("=" * 60)
    print("开始收集2018年至今的所有A股历史数据")
    print("=" * 60)

    try:
        # 创建完整数据收集器
        collector = FullDataCollector()

        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"收集范围: {collector.start_date} 到 {collector.end_date}")
        print("\n正在获取股票列表...")

        # 获取所有股票代码
        all_stock_codes = collector.get_all_stock_codes()

        if not all_stock_codes:
            print("无法获取股票列表，程序退出")
            return

        print(f"获取到 {len(all_stock_codes)} 只股票")

        # 开始数据收集（自动开始，无需确认）
        collector.collect_all_data(all_stock_codes)

    except KeyboardInterrupt:
        print("\n用户中断了程序")
    except Exception as e:
        print(f"程序异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()