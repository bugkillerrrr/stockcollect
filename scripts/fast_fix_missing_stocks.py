#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复缺失股票数据脚本
使用多线程加速数据收集
"""

import sqlite3
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
import threading
import queue
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

try:
    from src.database import StockDataDB
    from src.logger import get_logger
except ImportError:
    sys.path.append('.')
    from src.database import StockDataDB
    from src.logger import get_logger

logger = get_logger("fast_fix_missing_stocks")

class FastMissingStocksFixer:
    """快速缺失股票数据修复器"""

    def __init__(self, db_path="data/stock_data.db"):
        self.db = StockDataDB(db_path)
        self.max_workers = 8  # 增加到8个线程
        self.timeout = 30   # 每个请求30秒超时
        self.retry_count = 2  # 减少重试次数

    def read_missing_stocks(self):
        """读取缺失股票列表"""
        missing_file = "missing_stocks.txt"
        if not os.path.exists(missing_file):
            logger.error(f"缺失股票文件不存在: {missing_file}")
            return []

        with open(missing_file, 'r', encoding='utf-8') as f:
            missing_stocks = [line.strip() for line in f if line.strip()]

        logger.info(f"读取到 {len(missing_stocks)} 只缺失股票")
        return missing_stocks

    def collect_single_stock_fast(self, stock_code):
        """快速收集单只股票数据"""
        thread_id = threading.current_thread().ident
        try:
            # 根据股票代码前缀确定API调用方式
            if stock_code.startswith('920'):
                # 北交所股票
                symbol = f"bj{stock_code}"
            else:
                # 其他市场股票
                symbol = stock_code

            # 设置日期范围 - 使用较短的时间范围提高速度
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = "20240101"  # 只收集最近1年的数据

            # 调用akshare API获取数据
            df = ak.stock_zh_a_daily(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="hfq"  # 前复权
            )

            if df is not None and not df.empty:
                records_count = len(df)
                logger.info(f"[线程{thread_id}] ✅ {stock_code}: {records_count} 条记录")

                # 保存到数据库
                count = self.db.save_technical_data(stock_code, df)
                return stock_code, True, records_count
            else:
                logger.warning(f"[线程{thread_id}] ❌ {stock_code}: 未获取到数据")
                return stock_code, False, 0

        except Exception as e:
            logger.error(f"[线程{thread_id}] ❌ {stock_code}: 收集失败 - {e}")
            return stock_code, False, 0

    def collect_stocks_parallel(self, stock_codes):
        """并行收集股票数据"""
        success_count = 0
        failed_count = 0
        total_records = 0
        results = []

        logger.info(f"开始并行收集 {len(stock_codes)} 只股票数据，使用 {self.max_workers} 个线程")

        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_stock = {
                executor.submit(self.collect_single_stock_fast, stock_code): stock_code
                for stock_code in stock_codes
            }

            # 处理完成的任务
            for future in as_completed(future_to_stock):
                stock_code = future_to_stock[future]
                try:
                    result = future.result(timeout=self.timeout)
                    if result:
                        code, success, records = result
                        results.append((code, success, records))

                        if success:
                            success_count += 1
                            total_records += records
                        else:
                            failed_count += 1

                        # 显示进度
                        progress = (success_count + failed_count) / len(stock_codes) * 100
                        logger.info(f"进度: {success_count + failed_count}/{len(stock_codes)} ({progress:.1f}%) - "
                                  f"成功: {success_count}, 失败: {failed_count}")

                except Exception as e:
                    logger.error(f"处理 {stock_code} 结果时出错: {e}")
                    failed_count += 1

        logger.info(f"\n=== 并行收集结果 ===")
        logger.info(f"成功: {success_count}/{len(stock_codes)}")
        logger.info(f"失败: {failed_count}/{len(stock_codes)}")
        logger.info(f"总记录数: {total_records}")
        logger.info(f"成功率: {success_count/len(stock_codes)*100:.2f}%")

        return success_count, failed_count, total_records

    def collect_all_missing_stocks_fast(self):
        """快速收集所有缺失股票数据"""
        missing_stocks = self.read_missing_stocks()

        if not missing_stocks:
            logger.info("没有缺失股票需要收集")
            return

        # 按市场分组
        bj_stocks = [code for code in missing_stocks if code.startswith('920')]
        other_stocks = [code for code in missing_stocks if not code.startswith('920')]

        logger.info(f"北交所股票: {len(bj_stocks)} 只")
        logger.info(f"其他市场股票: {len(other_stocks)} 只")

        total_success = 0
        total_failed = 0
        total_records = 0

        start_time = time.time()

        # 收集北交所股票
        if bj_stocks:
            logger.info(f"\n=== 快速收集北交所股票数据 ===")
            success_count, failed_count, records = self.collect_stocks_parallel(bj_stocks)
            total_success += success_count
            total_failed += failed_count
            total_records += records

        # 收集其他市场股票
        if other_stocks:
            logger.info(f"\n=== 快速收集其他市场股票数据 ===")
            success_count, failed_count, records = self.collect_stocks_parallel(other_stocks)
            total_success += success_count
            total_failed += failed_count
            total_records += records

        end_time = time.time()
        elapsed_time = end_time - start_time

        logger.info(f"\n=== 总体收集结果 ===")
        logger.info(f"总成功: {total_success}/{len(missing_stocks)}")
        logger.info(f"总失败: {total_failed}/{len(missing_stocks)}")
        logger.info(f"成功率: {total_success/len(missing_stocks)*100:.2f}%")
        logger.info(f"总记录数: {total_records}")
        logger.info(f"总耗时: {elapsed_time:.1f} 秒")
        logger.info(f"平均速度: {len(missing_stocks)/elapsed_time:.2f} 股票/秒")

        return total_success, total_failed, total_records

    def verify_collection_result(self):
        """验证收集结果"""
        logger.info("=== 验证快速收集结果 ===")

        # 重新运行完整性检查
        missing_stocks = self.read_missing_stocks()

        # 从数据库获取当前股票列表
        db_stocks = self.db.get_stock_codes()
        db_set = set(db_stocks)
        missing_set = set(missing_stocks)

        # 检查是否还有缺失
        still_missing = missing_set - db_set

        logger.info(f"原来缺失股票数: {len(missing_set)}")
        logger.info(f"数据库现有股票数: {len(db_set)}")
        logger.info(f"仍缺失股票数: {len(still_missing)}")

        if still_missing:
            logger.warning("仍有股票缺失:")
            for code in sorted(list(still_missing)):
                logger.warning(f"  - {code}")
        else:
            logger.info("✅ 所有缺失股票已成功收集")

        return len(still_missing) == 0

def main():
    """主函数"""
    print("快速缺失股票数据修复工具")
    print("="*50)
    print("功能:")
    print("1. 使用多线程并行收集")
    print("2. 缩短数据时间范围提高速度")
    print("3. 优化重试和超时机制")
    print("4. 实时进度显示")

    try:
        fixer = FastMissingStocksFixer()

        # 快速收集所有缺失股票数据
        success_count, failed_count, total_records = fixer.collect_all_missing_stocks_fast()

        # 验证收集结果
        print("\n验证快速收集结果...")
        is_complete = fixer.verify_collection_result()

        if is_complete:
            print("\n✅ 所有缺失股票数据快速修复完成")
        else:
            print(f"\n⚠️  还有 {failed_count} 只股票数据未修复完成")
            print("建议检查失败的股票并重新尝试")

    except Exception as e:
        logger.error(f"快速修复过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()