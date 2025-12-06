#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复缺失股票数据脚本
主要用于收集北交所股票数据
"""

import sqlite3
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import sys

try:
    from src.database import StockDataDB
    from src.logger import get_logger
except ImportError:
    sys.path.append('.')
    from src.database import StockDataDB
    from src.logger import get_logger

logger = get_logger("fix_missing_stocks")

class MissingStocksFixer:
    """缺失股票数据修复器"""

    def __init__(self, db_path="data/stock_data.db"):
        self.db = StockDataDB(db_path)
        self.batch_size = 10  # 批次大小
        self.retry_count = 3   # 重试次数
        self.retry_delay = 5   # 重试延迟(秒)

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

    def collect_single_stock(self, stock_code, start_date="20220101"):
        """收集单只股票数据"""
        try:
            # 根据股票代码前缀确定API调用方式
            if stock_code.startswith('920'):
                # 北交所股票
                symbol = f"bj{stock_code}"
                logger.info(f"收集北交所股票: {stock_code} (symbol: {symbol})")
            else:
                # 其他市场股票
                symbol = stock_code
                logger.info(f"收集股票: {stock_code} (symbol: {symbol})")

            # 设置日期范围
            end_date = datetime.now().strftime('%Y%m%d')

            # 调用akshare API获取数据
            df = ak.stock_zh_a_daily(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="hfq"  # 前复权
            )

            if df is not None and not df.empty:
                logger.info(f"  成功获取 {len(df)} 条记录")
                logger.info(f"  时间范围: {df.index.min()} 到 {df.index.max()}")

                # 保存到数据库
                count = self.db.save_technical_data(stock_code, df)
                logger.info(f"  保存到数据库: {count} 条记录")
                return True, count
            else:
                logger.warning(f"  未获取到数据")
                return False, 0

        except Exception as e:
            logger.error(f"  收集失败: {e}")
            return False, 0

    def collect_stocks_batch(self, stock_codes):
        """批量收集股票数据"""
        success_count = 0
        failed_count = 0
        total_records = 0

        logger.info(f"开始批量收集 {len(stock_codes)} 只股票数据")

        for i, stock_code in enumerate(stock_codes, 1):
            logger.info(f"[{i}/{len(stock_codes)}] 处理 {stock_code}")

            success = False
            records = 0

            # 重试机制
            for retry in range(self.retry_count):
                try:
                    success, records = self.collect_single_stock(stock_code)
                    if success:
                        break
                    elif retry < self.retry_count - 1:
                        logger.warning(f"  第 {retry + 1} 次尝试失败，等待 {self.retry_delay} 秒后重试...")
                        time.sleep(self.retry_delay)
                except Exception as e:
                    logger.error(f"  第 {retry + 1} 次尝试异常: {e}")
                    if retry < self.retry_count - 1:
                        time.sleep(self.retry_delay)

            if success:
                success_count += 1
                total_records += records
                logger.info(f"  ✅ {stock_code} - {records} 条记录")
            else:
                failed_count += 1
                logger.error(f"  ❌ {stock_code} - 收集失败")

            # 避免请求过于频繁
            time.sleep(1)

        logger.info(f"\n=== 批次收集结果 ===")
        logger.info(f"成功: {success_count}/{len(stock_codes)}")
        logger.info(f"失败: {failed_count}/{len(stock_codes)}")
        logger.info(f"总记录数: {total_records}")

        return success_count, failed_count, total_records

    def collect_all_missing_stocks(self):
        """收集所有缺失股票数据"""
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

        # 优先处理北交所股票
        if bj_stocks:
            logger.info("\n=== 开始收集北交所股票数据 ===")
            success_count, failed_count, records = self.collect_stocks_batch(bj_stocks)
            total_success += success_count
            total_failed += failed_count
            total_records += records

        # 处理其他市场股票
        if other_stocks:
            logger.info("\n=== 开始收集其他市场股票数据 ===")
            success_count, failed_count, records = self.collect_stocks_batch(other_stocks)
            total_success += success_count
            total_failed += failed_count
            total_records += records

        # 总结
        logger.info(f"\n=== 总体收集结果 ===")
        logger.info(f"总成功: {total_success}/{len(missing_stocks)}")
        logger.info(f"总失败: {total_failed}/{len(missing_stocks)}")
        logger.info(f"成功率: {total_success/len(missing_stocks)*100:.2f}%")
        logger.info(f"总记录数: {total_records}")

        # 生成报告
        self.generate_collection_report(total_success, total_failed, len(missing_stocks), total_records)

        return total_success, total_failed

    def generate_collection_report(self, success_count, failed_count, total_stocks, total_records):
        """生成收集报告"""
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_file = f"missing_stocks_collection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("缺失股票数据收集报告\n")
            f.write("="*50 + "\n")
            f.write(f"生成时间: {report_time}\n")
            f.write(f"处理股票总数: {total_stocks}\n")
            f.write(f"成功收集: {success_count}\n")
            f.write(f"收集失败: {failed_count}\n")
            f.write(f"成功率: {success_count/total_stocks*100:.2f}%\n")
            f.write(f"总记录数: {total_records}\n\n")

            f.write("建议后续操作:\n")
            f.write("1. 对于收集失败的股票，检查其交易状态\n")
            f.write("2. 可能需要调整API调用参数或重试\n")
            f.write("3. 建立定期数据收集机制\n")
            f.write("4. 监控数据质量\n")

        logger.info(f"收集报告已保存到: {report_file}")

    def verify_collection_result(self):
        """验证收集结果"""
        logger.info("=== 验证数据收集结果 ===")

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
    print("缺失股票数据修复工具")
    print("="*50)

    fixer = MissingStocksFixer()

    try:
        # 收集所有缺失股票数据
        success_count, failed_count = fixer.collect_all_missing_stocks()

        # 验证收集结果
        print("\n验证数据收集结果...")
        is_complete = fixer.verify_collection_result()

        if is_complete:
            print("\n✅ 所有缺失股票数据修复完成")
        else:
            print(f"\n⚠️  还有 {failed_count} 只股票数据未修复完成")
            print("建议检查失败的股票并重新尝试")

    except Exception as e:
        logger.error(f"修复过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()