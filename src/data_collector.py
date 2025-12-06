"""
股票数据收集模块 - 基于Akshare
"""
import akshare as ak
import time
import random
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta

try:
    from .logger import get_logger
except ImportError:
    from logger import get_logger

logger = get_logger("data_collector")


class AkshareDataCollector:
    """基于Akshare的数据收集器"""

    def __init__(self, request_interval: float = 0.5, max_retries: int = 3):
        self.request_interval = request_interval
        self.max_retries = max_retries
        self.last_request_time = 0

    def _wait_between_requests(self):
        """请求之间的等待"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            # 基础延迟 + 2-5秒随机延迟，避免被封IP
            wait_time = self.request_interval - elapsed + random.uniform(2.0, 5.0)
            time.sleep(wait_time)
        else:
            # 即使已经过了基础间隔，也添加1-3秒的随机延迟
            time.sleep(random.uniform(1.0, 3.0))
        self.last_request_time = time.time()

    def _retry_on_error(self, func, *args, **kwargs):
        """错误重试机制"""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                self._wait_between_requests()
                result = func(*args, **kwargs)
                if result is not None and len(result) > 0:
                    logger.log_api_call(func.__name__, str(args[0]) if args else "", success=True)
                    return result
                else:
                    logger.warning(f"API返回空数据: {func.__name__}, 尝试 {attempt + 1}/{self.max_retries}")
            except Exception as e:
                last_exception = e
                logger.log_api_call(func.__name__, str(args[0]) if args else "", success=False)
                logger.warning(f"API调用失败: {func.__name__}, 尝试 {attempt + 1}/{self.max_retries}: {str(e)}")

                if attempt < self.max_retries - 1:
                    # 递增等待时间，模拟人类操作
                    wait_time = (attempt + 1) * 3 + random.uniform(1, 3)  # 4-9秒
                    logger.info(f"等待 {wait_time:.1f} 秒后重试...")
                    time.sleep(wait_time)

        logger.error(f"API调用最终失败: {func.__name__}, 错误: {str(last_exception)}")
        return None

    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        def _fetch_stock_list():
            return ak.stock_info_a_code_name()

        result = self._retry_on_error(_fetch_stock_list)
        if result is not None:
            # 清理数据，保留需要的列
            print(f"Raw data columns: {list(result.columns)}")
            print(f"Data shape: {result.shape}")

            # 尝试不同的列名映射
            for code_col, name_col in [('code', 'name'), ('代码', '名称'), ('stock_code', 'stock_name'), ('symbol', 'name')]:
                if code_col in result.columns and name_col in result.columns:
                    stock_list = result[[code_col, name_col]].copy()
                    stock_list.columns = ['stock_code', 'stock_name']
                    logger.info(f"获取股票列表成功: {len(stock_list)}只股票")
                    return stock_list

            # 如果都没找到，打印可用的列名
            print("Available columns:", list(result.columns))
            print("Sample data:")
            print(result.head())
            logger.warning("无法找到合适的代码和名称列")
            return result

        logger.error("获取股票列表失败")
        return pd.DataFrame()

    def get_stock_data(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取单只股票的历史数据"""
        def _fetch_stock_data():
            # 使用不同的API，需要带市场前缀
            symbol = stock_code

            # CDR股票 (689009) - 使用stock_zh_a_cdr_daily，带sh前缀
            if stock_code == '689009':
                logger.info(f"检测到CDR股票: {stock_code}")
                symbol = f"sh{stock_code}"
                return ak.stock_zh_a_cdr_daily(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                    # CDR API 不支持 adjust 参数
                )

            # 其他CDR股票 (688开头) - 使用stock_zh_a_cdr_daily
            elif stock_code.startswith('688'):
                logger.info(f"检测到CDR股票: {stock_code}")
                symbol = f"sh{stock_code}"
                return ak.stock_zh_a_cdr_daily(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                    # CDR API 不支持 adjust 参数
                )

            # 北交所股票 (92开头) - 使用bj前缀
            elif stock_code.startswith('92'):
                logger.info(f"检测到北交所股票: {stock_code}")
                symbol = f"bj{stock_code}"
                return ak.stock_zh_a_daily(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust="hfq"  # 后复权
                )

            # 深圳股票 (00, 30开头) - 使用sz前缀
            elif stock_code.startswith('00') or stock_code.startswith('30'):
                logger.info(f"检测到深圳股票: {stock_code}")
                symbol = f"sz{stock_code}"
                return ak.stock_zh_a_daily(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust="hfq"  # 后复权
                )

            # 上海股票 (60, 68开头, 不包含688的CDR) - 使用sh前缀
            elif stock_code.startswith('60') or (stock_code.startswith('68') and not stock_code.startswith('688')):
                logger.info(f"检测到上海股票: {stock_code}")
                symbol = f"sh{stock_code}"
                return ak.stock_zh_a_daily(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust="hfq"  # 后复权
                )

            # 其他情况，尝试直接使用股票代码
            else:
                logger.warning(f"未识别的市场前缀: {stock_code}，尝试直接使用")
                return ak.stock_zh_a_daily(
                    symbol=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    adjust="hfq"  # 后复权
                )

        result = self._retry_on_error(_fetch_stock_data)
        if result is not None and len(result) > 0:
            logger.log_data_update(stock_code, "历史数据", len(result), success=True)
            return result
        else:
            logger.log_data_update(stock_code, "历史数据", 0, success=False)
            return None

    def get_financial_data(self, stock_code: str, period: str = "2023") -> Optional[pd.DataFrame]:
        """获取财务数据"""
        def _fetch_financial_data():
            try:
                # 获取财务指标数据
                return ak.stock_financial_analysis_indicator(symbol=stock_code, period=period)
            except Exception as e:
                logger.warning(f"获取财务指标失败，尝试财务报表: {str(e)}")
                # 如果财务指标失败，尝试获取基础财务报表
                try:
                    return ak.stock_financial_analysis_ths(symbol=stock_code, year=period)
                except Exception as e2:
                    logger.warning(f"获取财务报表也失败: {str(e2)}")
                    return None

        result = self._retry_on_error(_fetch_financial_data)
        if result is not None and len(result) > 0:
            logger.log_data_update(stock_code, f"财务数据({period})", len(result), success=True)
            return result
        else:
            logger.log_data_update(stock_code, f"财务数据({period})", 0, success=False)
            return None

    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict]:
        """获取股票基础信息"""
        def _fetch_basic_info():
            try:
                # 获取个股信息
                info = ak.stock_individual_info_em(symbol=stock_code)
                if info is not None and len(info) > 0:
                    # 转换为字典格式
                    info_dict = dict(zip(info['item'], info['value']))
                    return info_dict
            except Exception as e:
                logger.warning(f"获取个股信息失败: {str(e)}")
                return None

        result = self._retry_on_error(_fetch_basic_info)
        if result is not None:
            logger.info(f"获取股票基础信息成功: {stock_code}")
        return result

    def batch_get_stock_data(self, stock_codes: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """批量获取多只股票数据"""
        results = {}
        total_count = len(stock_codes)
        success_count = 0

        logger.info(f"开始批量获取 {total_count} 只股票数据，时间范围: {start_date} - {end_date}")

        for i, stock_code in enumerate(stock_codes, 1):
            try:
                data = self.get_stock_data(stock_code, start_date, end_date)
                if data is not None:
                    results[stock_code] = data
                    success_count += 1

                # 进度日志
                if i % 10 == 0 or i == total_count:
                    logger.info(f"进度: {i}/{total_count}, 成功: {success_count}")

                # 避免请求过快
                time.sleep(self.request_interval)

            except Exception as e:
                logger.log_error(f"获取股票数据异常: {stock_code}", e)

        logger.info(f"批量获取完成: {success_count}/{total_count} 成功")
        return results

    def batch_get_financial_data(self, stock_codes: List[str], periods: List[str] = None) -> Dict[str, pd.DataFrame]:
        """批量获取财务数据"""
        if periods is None:
            # 默认获取最近3年的数据
            current_year = datetime.now().year
            periods = [str(year) for year in range(current_year - 2, current_year + 1)]

        results = {}
        total_count = len(stock_codes) * len(periods)
        current_count = 0

        logger.info(f"开始批量获取 {len(stock_codes)} 只股票的财务数据，时间范围: {periods}")

        for stock_code in stock_codes:
            for period in periods:
                current_count += 1
                try:
                    data = self.get_financial_data(stock_code, period)
                    if data is not None and len(data) > 0:
                        key = f"{stock_code}_{period}"
                        results[key] = data

                    # 进度日志
                    if current_count % 10 == 0 or current_count == total_count:
                        logger.info(f"财务数据进度: {current_count}/{total_count}")

                except Exception as e:
                    logger.log_error(f"获取财务数据异常: {stock_code}_{period}", e)

        logger.info(f"批量获取财务数据完成: {len(results)}/{total_count} 成功")
        return results

    def validate_data(self, data: pd.DataFrame, data_type: str = "technical") -> bool:
        """数据验证"""
        if data is None or len(data) == 0:
            logger.warning("数据为空，验证失败")
            return False

        try:
            if data_type == "technical":
                # 验证技术数据
                required_columns = ['日期', '开盘', '最高', '最低', '收盘']
                missing_columns = [col for col in required_columns if col not in data.columns]

                if missing_columns:
                    logger.warning(f"技术数据缺少必要列: {missing_columns}")
                    return False

                # 检查价格数据合理性
                price_columns = ['开盘', '最高', '最低', '收盘']
                for col in price_columns:
                    if col in data.columns:
                        # 检查是否有负价格
                        if (data[col] <= 0).any():
                            logger.warning(f"发现非正价格数据: {col}")
                            return False

                        # 检查价格异常波动
                        if len(data) > 1:
                            price_change = data[col].pct_change().abs()
                            if (price_change > 0.2).any():  # 单日涨跌幅超过20%
                                logger.warning(f"发现异常价格波动: {col}")
                                # 这里不返回False，只是记录警告

            elif data_type == "financial":
                # 验证财务数据
                if len(data.columns) == 0:
                    logger.warning("财务数据没有列")
                    return False

            logger.debug(f"{data_type}数据验证通过")
            return True

        except Exception as e:
            logger.log_error(f"数据验证异常", e)
            return False