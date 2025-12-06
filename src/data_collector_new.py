"""
新股票数据收集模块 - 支持配置复权类型
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

logger = get_logger("data_collector_new")


class AkshareDataCollectorNew:
    """新的数据收集器 - 支持复权类型配置"""

    def __init__(self, db, request_interval: float = 1.0, max_retries: int = 3,
                 adjustment_type: str = 'hfq', api_method: str = 'stock_zh_a_daily'):
        self.db = db
        self.request_interval = request_interval
        self.max_retries = max_retries
        self.adjustment_type = adjustment_type  # 'hfq' 或 'qfq'
        self.api_method = api_method
        self.last_request_time = 0

        # 设置数据库默认配置
        self.db.set_adjustment_type(adjustment_type)
        self.db.set_api_method(api_method)

        logger.info(f"Data collector initialized - Adjustment: {adjustment_type}, API: {api_method}")

    def _wait_between_requests(self):
        """请求之间的等待"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            # 基础延迟 + 1-3秒随机延迟
            wait_time = self.request_interval - elapsed + random.uniform(1.0, 3.0)
            time.sleep(wait_time)
        else:
            # 即使已经过了基础间隔，也添加随机延迟
            time.sleep(random.uniform(0.5, 1.5))
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
                    # 递增等待时间
                    wait_time = (attempt + 1) * 2 + random.uniform(1, 3)  # 3-9秒
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

    def get_stock_data(self, stock_code: str, start_date: str, end_date: str,
                       adjustment_type: str = None, api_method: str = None) -> Optional[pd.DataFrame]:
        """获取单只股票的历史数据 - 根据股票类型自动选择合适的接口"""

        # 使用传入的参数或默认配置
        current_adjustment = adjustment_type or self.adjustment_type
        current_api_method = api_method or self.api_method

        def _fetch_stock_data():
            # 其他所有股票都使用标准接口，先初始化symbol
            symbol = stock_code

            # 特殊处理689009股票（规则3）
            if stock_code == '689009':
                logger.info(f"检测到特殊股票: {stock_code}，使用CDR接口")
                symbol = f"sh{stock_code}"
                logger.info(f"使用接口: stock_zh_a_cdr_daily, symbol={symbol}")
                return ak.stock_zh_a_cdr_daily(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                    # CDR接口不支持adjust参数
                )

            # 北交所股票（92开头）- 规则2
            elif stock_code.startswith('92'):
                logger.info(f"检测到北交所股票: {stock_code}")
                symbol = f"bj{stock_code}"
                market = "北交所"

            # 深圳股票（00、30开头）- 规则1
            elif stock_code.startswith('00') or stock_code.startswith('30'):
                symbol = f"sz{stock_code}"
                market = "深圳"

            # 上海股票（60、68开头，包括688的CDR）- 规则1
            elif stock_code.startswith('60') or stock_code.startswith('68'):
                symbol = f"sh{stock_code}"
                market = "上海"

            else:
                # 其他情况，尝试直接使用股票代码
                logger.warning(f"未识别的市场前缀: {stock_code}，尝试直接使用")
                symbol = stock_code
                market = "未知"

            logger.info(f"检测到{market}股票: {stock_code}，使用接口: {current_api_method}, symbol={symbol}, adjustment={current_adjustment}")

            # 根据API方法选择标准接口
            if current_api_method == 'stock_zh_a_daily':
                return ak.stock_zh_a_daily(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=current_adjustment
                )
            elif current_api_method == 'stock_zh_a_hist':
                return ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=current_adjustment
                )
            else:
                raise ValueError(f"不支持的API方法: {current_api_method}")

        result = self._retry_on_error(_fetch_stock_data)
        if result is not None and len(result) > 0:
            # 根据股票类型记录不同的日志信息
            if stock_code == '689009':
                data_type = "历史数据(CDR特殊接口)"
            elif stock_code.startswith('92'):
                data_type = f"历史数据({current_adjustment},北交所)"
            else:
                data_type = f"历史数据({current_adjustment})"

            logger.log_data_update(stock_code, data_type, len(result), success=True)
            return result
        else:
            logger.log_data_update(stock_code, "历史数据", 0, success=False)
            return None

    def save_stock_data(self, stock_code: str, data: pd.DataFrame,
                       adjustment_type: str = None, api_method: str = None) -> int:
        """保存股票数据到数据库"""
        current_adjustment = adjustment_type or self.adjustment_type
        current_api_method = api_method or self.api_method

        return self.db.save_technical_data(
            stock_code=stock_code,
            data=data,
            adjustment_type=current_adjustment,
            api_method=current_api_method
        )

    def batch_get_stock_data(self, stock_codes: List[str], start_date: str, end_date: str,
                            adjustment_type: str = None, api_method: str = None) -> Dict[str, pd.DataFrame]:
        """批量获取多只股票数据"""
        results = {}
        total_count = len(stock_codes)
        success_count = 0

        current_adjustment = adjustment_type or self.adjustment_type
        current_api_method = api_method or self.api_method

        logger.info(f"开始批量获取 {total_count} 只股票数据，复权类型: {current_adjustment}, API: {current_api_method}")
        logger.info(f"时间范围: {start_date} - {end_date}")

        for i, stock_code in enumerate(stock_codes, 1):
            try:
                data = self.get_stock_data(stock_code, start_date, end_date, current_adjustment, current_api_method)
                if data is not None:
                    results[stock_code] = data
                    saved_count = self.save_stock_data(stock_code, data, current_adjustment, current_api_method)
                    if saved_count > 0:
                        success_count += 1
                    logger.info(f"{stock_code} 获取并保存了 {saved_count} 条记录")

                # 进度日志
                if i % 10 == 0 or i == total_count:
                    logger.info(f"进度: {i}/{total_count}, 成功: {success_count}")

                # 避免请求过快
                time.sleep(self.request_interval)

            except Exception as e:
                logger.log_error(f"获取股票数据异常: {stock_code}", e)

        logger.info(f"批量获取完成: {success_count}/{total_count} 成功")
        return results

    def get_and_save_single_stock(self, stock_code: str, start_date: str, end_date: str,
                                  adjustment_type: str = None, api_method: str = None) -> bool:
        """获取并保存单只股票数据"""
        try:
            current_adjustment = adjustment_type or self.adjustment_type
            current_api_method = api_method or self.api_method

            logger.info(f"开始获取 {stock_code} 数据 (复权: {current_adjustment}, API: {current_api_method})")

            # 获取数据
            data = self.get_stock_data(stock_code, start_date, end_date, current_adjustment, current_api_method)

            if data is not None and len(data) > 0:
                # 保存到数据库
                saved_count = self.save_stock_data(stock_code, data, current_adjustment, current_api_method)

                if saved_count > 0:
                    logger.info(f"{stock_code} 数据获取成功: {saved_count} 条记录")

                    # 打印数据概览
                    print(f"\n{stock_code} 数据概览:")
                    print(f"  时间范围: {data.iloc[0, 0] if len(data) > 0 else 'N/A'} 到 {data.iloc[-1, 0] if len(data) > 0 else 'N/A'}")
                    print(f"  记录数量: {len(data)}")
                    print(f"  保存记录: {saved_count}")

                    # 检查关键字段
                    required_fields = ['date', 'open', 'high', 'low', 'close']
                    if 'volume' in data.columns:
                        print(f"  成交量: 完整 (平均: {data['volume'].mean():.0f})")
                    else:
                        print(f"  成交量: 缺失")

                    if 'amount' in data.columns:
                        print(f"  成交额: 完整 (平均: {data['amount'].mean():.0f})")
                    else:
                        print(f"  成交额: 缺失")

                    return True
                else:
                    logger.warning(f"{stock_code} 数据保存失败")
                    return False
            else:
                logger.error(f"{stock_code} 数据获取失败或为空")
                return False

        except Exception as e:
            logger.log_error(f"获取保存股票数据异常: {stock_code}", e)
            return False

    def test_api_methods(self, stock_code: str = "000001", start_date: str = "20240101", end_date: str = "20240131") -> Dict:
        """测试不同的API方法和复权类型"""
        print(f"\n{'='*60}")
        print(f"测试API方法和复权类型 (股票: {stock_code})")
        print(f"{'='*60}")

        test_results = {}

        # 测试API方法
        api_methods = ['stock_zh_a_daily', 'stock_zh_a_hist']
        adjustment_types = ['hfq', 'qfq']

        for api_method in api_methods:
            for adjustment in adjustment_types:
                test_key = f"{api_method}_{adjustment}"
                print(f"\n测试 {test_key}:")

                try:
                    data = self.get_stock_data(stock_code, start_date, end_date, adjustment, api_method)

                    if data is not None and len(data) > 0:
                        print(f"  ✓ 成功! 数据形状: {data.shape}")
                        print(f"  ✓ 列名: {list(data.columns)}")

                        # 检查关键字段
                        key_fields = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
                        missing_fields = [field for field in key_fields if field not in data.columns]
                        if missing_fields:
                            print(f"  ⚠ 缺失字段: {missing_fields}")
                        else:
                            print(f"  ✓ 所有关键字段完整")

                        # 打印样本数据
                        if len(data) > 0:
                            print(f"  样本数据 (前2行):")
                            print(data.head(2).to_string())

                        test_results[test_key] = {
                            'success': True,
                            'shape': data.shape,
                            'columns': list(data.columns),
                            'missing_fields': missing_fields
                        }

                        # 保存测试数据到数据库
                        if len(data) > 0:
                            saved_count = self.save_stock_data(stock_code, data, adjustment, api_method)
                            print(f"  ✓ 已保存 {saved_count} 条测试数据到数据库")

                    else:
                        print(f"  ✗ 失败: 无数据返回")
                        test_results[test_key] = {'success': False, 'error': 'No data returned'}

                except Exception as e:
                    print(f"  ✗ 失败: {str(e)}")
                    test_results[test_key] = {'success': False, 'error': str(e)}

        return test_results

    def print_current_settings(self):
        """打印当前设置"""
        settings = self.db.get_current_settings()
        print(f"\n{'='*60}")
        print("当前数据收集设置")
        print(f"{'='*60}")

        for key, value in settings.items():
            print(f"{key}: {value}")

        print(f"\n使用说明:")
        print(f"  adjustment_type: 'hfq' (后复权，适合长期分析) 或 'qfq' (前复权，适合短线交易)")
        print(f"  api_method: 'stock_zh_a_daily' (推荐，数据完整) 或 'stock_zh_a_hist' (备选)")

    def update_settings(self, adjustment_type: str = None, api_method: str = None):
        """更新设置"""
        if adjustment_type:
            self.adjustment_type = adjustment_type
            self.db.set_adjustment_type(adjustment_type)
            logger.info(f"复权类型已更新为: {adjustment_type}")

        if api_method:
            self.api_method = api_method
            self.db.set_api_method(api_method)
            logger.info(f"API方法已更新为: {api_method}")