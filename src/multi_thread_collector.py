"""
多线程股票数据收集器
提高数据收集效率，减少总耗时
"""

import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd

# 设置编码
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    from .data_collector import AkshareDataCollector
    from .database import StockDataDB
    from .logger import get_logger
except ImportError:
    from data_collector import AkshareDataCollector
    from database import StockDataDB
    from logger import get_logger

logger = get_logger("multi_thread_collector")


class MultiThreadCollector:
    """多线程股票数据收集器"""

    def __init__(self, max_workers: int = 3, delay: float = 1.5):
        """
        初始化多线程收集器

        Args:
            max_workers: 最大并发线程数（建议2-3，平衡效率和安全）
            delay: 每个请求之间的基础延迟（秒，建议1.5-2秒，避免被封）
        """
        self.max_workers = max_workers
        self.delay = delay
        self.collector = AkshareDataCollector()
        self.db = StockDataDB()

        # 线程安全的状态跟踪
        self.lock = threading.Lock()
        self.success_count = 0
        self.failed_count = 0
        self.processed_count = 0
        self.failed_stocks = []

        # 进度跟踪
        self.start_time = 0
        self.total_stocks = 0

    def process_single_stock(self, stock_info: Tuple[str, int, str]) -> Dict:
        """
        处理单只股票的数据收集

        Args:
            stock_info: (股票代码, 索引, 开始日期)

        Returns:
            处理结果字典
        """
        stock_code, index, start_date = stock_info

        # 为每个线程创建延迟，避免所有线程同时请求
        import random
        # 基础延迟 + 随机抖动，避免被识别为机器人
        thread_delay = self.delay * (1 + random.uniform(0.2, 0.8))

        try:
            # 获取股票数据
            data = self.collector.get_stock_data(stock_code, start_date, self.end_date)

            if data is not None and len(data) > 0:
                # 保存到数据库
                saved_count = self.db.save_technical_data(stock_code, data)

                # 请求延迟
                time.sleep(thread_delay)

                return {
                    'stock_code': stock_code,
                    'success': True,
                    'records': saved_count,
                    'index': index,
                    'error': None
                }
            else:
                return {
                    'stock_code': stock_code,
                    'success': False,
                    'records': 0,
                    'index': index,
                    'error': '获取数据为空'
                }

        except Exception as e:
            time.sleep(thread_delay * 2)  # 出错时延迟更长时间
            return {
                'stock_code': stock_code,
                'success': False,
                'records': 0,
                'index': index,
                'error': str(e)
            }

    def update_progress(self, result: Dict):
        """
        更新进度统计（线程安全）
        """
        with self.lock:
            self.processed_count += 1

            if result['success']:
                self.success_count += 1
            else:
                self.failed_count += 1
                self.failed_stocks.append(result['stock_code'])

            # 计算进度和预估时间
            progress = self.processed_count / self.total_stocks
            elapsed = time.time() - self.start_time

            if self.processed_count > 0:
                avg_time = elapsed / self.processed_count
                remaining_time = avg_time * (self.total_stocks - self.processed_count)
                remaining_hours = remaining_time / 3600
                progress_pct = progress * 100

                logger.info(
                    f"进度: {self.processed_count}/{self.total_stocks} ({progress_pct:.1f}%) "
                    f"成功: {self.success_count} 失败: {self.failed_count} "
                    f"平均: {avg_time:.1f}秒/股 "
                    f"预计剩余: {remaining_hours:.1f} 小时"
                )

    def collect_all_data(self, stock_codes: List[str], start_date: str, end_date: str,
                        batch_size: int = 50):
        """
        多线程收集所有股票数据

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            batch_size: 批次大小（用于进度显示）
        """
        self.end_date = end_date
        self.total_stocks = len(stock_codes)
        self.start_time = time.time()

        logger.info(f"开始多线程收集 {self.total_stocks} 只股票数据")
        logger.info(f"并发线程数: {self.max_workers}")
        logger.info(f"基础延迟: {self.delay} 秒")
        logger.info(f"时间范围: {start_date} - {end_date}")
        logger.info("=" * 60)

        # 准备任务列表
        tasks = [(stock_code, i, start_date) for i, stock_code in enumerate(stock_codes)]

        # 使用线程池执行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_stock = {
                executor.submit(self.process_single_stock, task): task[0]
                for task in tasks
            }

            # 处理完成的任务
            for future in as_completed(future_to_stock):
                try:
                    result = future.result()
                    self.update_progress(result)
                except Exception as e:
                    stock_code = future_to_stock[future]
                    logger.error(f"处理任务异常: {stock_code} - {e}")

        # 输出最终统计
        elapsed_time = time.time() - self.start_time
        total_hours = elapsed_time / 3600

        logger.info("=" * 60)
        logger.info("多线程数据收集完成!")
        logger.info(f"总股票数: {self.total_stocks}")
        logger.info(f"成功收集: {self.success_count}")
        logger.info(f"收集失败: {self.failed_count}")
        logger.info(f"总耗时: {total_hours:.2f} 小时")
        if self.total_stocks > 0:
            logger.info(f"平均每只股票: {elapsed_time/self.total_stocks:.2f} 秒")

        if self.failed_stocks:
            logger.info(f"失败的股票代码: {self.failed_stocks[:20]}...")

        return {
            'total': self.total_stocks,
            'success': self.success_count,
            'failed': self.failed_count,
            'failed_stocks': self.failed_stocks,
            'time_elapsed': elapsed_time
        }


def get_optimal_thread_count() -> int:
    """
    根据系统情况建议最优线程数
    考虑到Akshare反爬虫限制，建议保守设置

    Returns:
        建议的线程数
    """
    import multiprocessing

    # 基于CPU核心数，但为了防止被封，限制在较低水平
    cpu_count = multiprocessing.cpu_count()
    recommended = min(max(cpu_count - 1, 2), 3)  # 2-3个线程，避免被封

    return recommended


if __name__ == "__main__":
    # 测试多线程收集器
    collector = MultiThreadCollector(max_workers=3, delay=0.3)

    # 测试几只股票
    test_stocks = ['000001', '000002', '600000', '600519', '000858']

    import datetime
    end_date = datetime.datetime.now().strftime("%Y%m%d")
    start_date = "20250101"

    result = collector.collect_all_data(test_stocks, start_date, end_date)
    print(f"测试结果: {result}")