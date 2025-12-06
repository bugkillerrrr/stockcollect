"""
股票数据更新模块
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    from .database import StockDataDB
    from .data_collector import AkshareDataCollector
    from .logger import get_logger
except ImportError:
    from database import StockDataDB
    from data_collector import AkshareDataCollector
    from logger import get_logger

logger = get_logger("data_updater")


class DataUpdater:
    """股票数据更新器"""

    def __init__(self, db: StockDataDB = None, collector: AkshareDataCollector = None):
        self.db = db or StockDataDB()
        self.collector = collector or AkshareDataCollector()

    def update_single_stock(self, stock_code: str, start_date: str = None, end_date: str = None) -> bool:
        """更新单只股票的技术数据"""
        try:
            # 如果没有指定开始日期，获取最后更新日期
            if start_date is None:
                last_date = self.db.get_last_update_date(stock_code)
                if last_date:
                    # 从最后更新日期的下一天开始
                    start_date = (pd.to_datetime(last_date) + timedelta(days=1)).strftime("%Y%m%d")
                else:
                    # 如果没有历史数据，从2018年开始
                    start_date = "20180101"

            # 如果没有指定结束日期，使用今天
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")

            logger.info(f"更新股票 {stock_code}: {start_date} - {end_date}")

            # 获取数据
            data = self.collector.get_stock_data(stock_code, start_date, end_date)
            if data is None:
                logger.warning(f"没有获取到股票 {stock_code} 的数据")
                return False

            # 验证数据
            if not self.collector.validate_data(data, "technical"):
                logger.error(f"股票 {stock_code} 数据验证失败")
                return False

            # 保存数据
            count = self.db.save_technical_data(stock_code, data)
            success = count > 0

            # 记录更新日志
            self.db.log_update(
                update_type="technical",
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                records_count=count,
                success=success
            )

            return success

        except Exception as e:
            logger.log_error(f"更新股票 {stock_code} 失败", e)
            self.db.log_update(
                update_type="technical",
                stock_code=stock_code,
                start_date=start_date or "",
                end_date=end_date or "",
                records_count=0,
                success=False,
                error_message=str(e)
            )
            return False

    def update_stock_list(self) -> bool:
        """更新股票列表"""
        try:
            logger.info("开始更新股票列表")
            stock_list = self.collector.get_stock_list()

            if stock_list is None or len(stock_list) == 0:
                logger.error("获取股票列表失败")
                return False

            # 保存股票基础信息
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                for _, row in stock_list.iterrows():
                    stock_code = row['stock_code']
                    stock_name = row['stock_name']

                    # 使用INSERT OR REPLACE处理重复数据
                    conn.execute("""
                        INSERT OR REPLACE INTO stock_master (stock_code, stock_name, updated_at)
                        VALUES (?, ?, ?)
                    """, (stock_code, stock_name, datetime.now()))

            logger.info(f"股票列表更新完成: {len(stock_list)} 只股票")
            return True

        except Exception as e:
            logger.log_error("更新股票列表失败", e)
            return False

    def update_financial_data(self, stock_code: str, periods: List[str] = None) -> bool:
        """更新单只股票的财务数据"""
        try:
            if periods is None:
                # 默认获取最近3年的数据
                current_year = datetime.now().year
                periods = [str(year) for year in range(current_year - 2, current_year + 1)]

            total_count = 0
            success_count = 0

            for period in periods:
                logger.info(f"获取股票 {stock_code} {period} 年财务数据")

                data = self.collector.get_financial_data(stock_code, period)
                if data is not None and len(data) > 0:
                    # 验证数据
                    if self.collector.validate_data(data, "financial"):
                        count = self.db.save_financial_data(stock_code, data, period)
                        total_count += count
                        if count > 0:
                            success_count += 1
                    else:
                        logger.warning(f"股票 {stock_code} {period} 年财务数据验证失败")

            # 记录更新日志
            self.db.log_update(
                update_type="financial",
                stock_code=stock_code,
                start_date=min(periods) if periods else "",
                end_date=max(periods) if periods else "",
                records_count=total_count,
                success=success_count > 0
            )

            logger.info(f"股票 {stock_code} 财务数据更新完成: {success_count}/{len(periods)} 成功")
            return success_count > 0

        except Exception as e:
            logger.log_error(f"更新股票 {stock_code} 财务数据失败", e)
            return False

    def batch_update_stocks(self, stock_codes: List[str] = None,
                           start_date: str = None, end_date: str = None) -> Dict[str, bool]:
        """批量更新多只股票数据"""
        try:
            if stock_codes is None:
                # 获取所有股票代码
                stock_codes = self.db.get_stock_codes()
                if not stock_codes:
                    logger.warning("没有找到需要更新的股票代码")
                    return {}

            results = {}
            total_count = len(stock_codes)
            success_count = 0

            logger.info(f"开始批量更新 {total_count} 只股票数据")

            for i, stock_code in enumerate(stock_codes, 1):
                try:
                    success = self.update_single_stock(stock_code, start_date, end_date)
                    results[stock_code] = success
                    if success:
                        success_count += 1

                    # 进度日志
                    if i % 10 == 0 or i == total_count:
                        logger.info(f"更新进度: {i}/{total_count}, 成功: {success_count}")

                except Exception as e:
                    logger.log_error(f"更新股票 {stock_code} 异常", e)
                    results[stock_code] = False

            logger.info(f"批量更新完成: {success_count}/{total_count} 成功")
            return results

        except Exception as e:
            logger.log_error("批量更新失败", e)
            return {}

    def daily_update(self, update_stock_list: bool = True) -> Dict:
        """每日更新任务"""
        logger.info("开始执行每日更新任务")
        results = {
            "stock_list_updated": False,
            "stocks_updated": {},
            "success_count": 0,
            "total_count": 0,
            "start_time": datetime.now()
        }

        try:
            # 更新股票列表
            if update_stock_list:
                results["stock_list_updated"] = self.update_stock_list()

            # 获取需要更新的股票
            stock_codes = self.db.get_stock_codes()
            results["total_count"] = len(stock_codes)

            if not stock_codes:
                logger.warning("没有找到需要更新的股票")
                return results

            # 批量更新股票数据（只更新最近的几天）
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")

            update_results = self.batch_update_stocks(stock_codes, start_date, end_date)
            results["stocks_updated"] = update_results
            results["success_count"] = sum(1 for success in update_results.values() if success)

        except Exception as e:
            logger.log_error("每日更新任务失败", e)

        finally:
            results["end_time"] = datetime.now()
            results["duration"] = results["end_time"] - results["start_time"]

        logger.info(f"每日更新完成: {results['success_count']}/{results['total_count']} 成功, "
                   f"耗时: {results['duration']}")
        return results

    def weekly_financial_update(self, stock_codes: List[str] = None) -> Dict:
        """每周财务数据更新任务"""
        logger.info("开始执行每周财务数据更新")
        results = {
            "updated_stocks": {},
            "success_count": 0,
            "total_count": 0,
            "start_time": datetime.now()
        }

        try:
            if stock_codes is None:
                stock_codes = self.db.get_stock_codes()

            results["total_count"] = len(stock_codes)
            success_count = 0

            for stock_code in stock_codes:
                try:
                    success = self.update_financial_data(stock_code)
                    results["updated_stocks"][stock_code] = success
                    if success:
                        success_count += 1

                    # 避免请求过快
                    import time
                    time.sleep(1)

                except Exception as e:
                    logger.log_error(f"更新股票 {stock_code} 财务数据异常", e)
                    results["updated_stocks"][stock_code] = False

            results["success_count"] = success_count

        except Exception as e:
            logger.log_error("每周财务更新失败", e)

        finally:
            results["end_time"] = datetime.now()
            results["duration"] = results["end_time"] - results["start_time"]

        logger.info(f"每周财务更新完成: {results['success_count']}/{results['total_count']} 成功")
        return results

    def get_update_status(self) -> Dict:
        """获取更新状态"""
        try:
            # 获取数据库信息
            db_info = self.db.get_database_info()

            # 获取最近更新记录
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                recent_updates = pd.read_sql("""
                    SELECT update_type, stock_code, records_count, success, created_at
                    FROM update_log
                    ORDER BY created_at DESC
                    LIMIT 10
                """, conn).to_dict('records')

            return {
                "database_info": db_info,
                "recent_updates": recent_updates,
                "last_check": datetime.now()
            }

        except Exception as e:
            logger.log_error("获取更新状态失败", e)
            return {}