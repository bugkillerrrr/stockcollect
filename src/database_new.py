"""
新的股票数据系统数据库模块 - 用于重新开始数据获取
"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    from .logger import get_logger
except ImportError:
    from logger import get_logger

logger = get_logger("database_new")


class StockDataNewDB:
    """新股票数据数据库管理类 - 用于重新开始"""

    def __init__(self, db_path: str = "data/stock_data_new.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
        self.create_indexes()

    def init_database(self):
        """初始化数据库表结构"""
        logger.info("Initializing NEW database schema")
        with sqlite3.connect(self.db_path) as conn:
            # 股票基础信息表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_master (
                    stock_code TEXT PRIMARY KEY,
                    stock_name TEXT,
                    industry TEXT,
                    market TEXT,
                    adjustment_type TEXT DEFAULT 'hfq',  -- 默认后复权
                    api_method TEXT DEFAULT 'stock_zh_a_daily',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 技术数据表 - 基础原始数据
            conn.execute("""
                CREATE TABLE IF NOT EXISTS technical_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT,
                    trade_date TEXT,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    close_price REAL,
                    volume INTEGER,
                    amount REAL,
                    adjustment_type TEXT DEFAULT 'hfq',  -- 记录复权类型
                    api_method TEXT DEFAULT 'stock_zh_a_daily',  -- 记录API方法
                    fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 记录获取时间
                    UNIQUE(stock_code, trade_date)
                )
            """)

            # 技术指标表 - 可扩展的指标存储
            conn.execute("""
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT,
                    trade_date TEXT,
                    indicator_name TEXT,
                    indicator_value REAL,
                    adjustment_type TEXT DEFAULT 'hfq',  -- 记录复权类型
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, trade_date, indicator_name)
                )
            """)

            # 财务数据表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS financial_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT,
                    report_date TEXT,
                    report_type TEXT,
                    total_revenue REAL,
                    net_profit REAL,
                    total_assets REAL,
                    total_liabilities REAL,
                    eps REAL,
                    roe REAL,
                    adjustment_type TEXT DEFAULT 'hfq',  -- 记录复权类型
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, report_date, report_type)
                )
            """)

            # 数据更新日志表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS update_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    update_type TEXT,
                    stock_code TEXT,
                    adjustment_type TEXT,  -- 记录使用的复权类型
                    api_method TEXT,       -- 记录使用的API方法
                    start_date TEXT,
                    end_date TEXT,
                    records_count INTEGER,
                    success BOOLEAN,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 系统配置表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 插入默认配置
            self.insert_default_config(conn)

        logger.info("NEW database schema initialization completed")

    def insert_default_config(self, conn):
        """插入默认配置"""
        default_configs = [
            ('default_adjustment_type', 'hfq', '默认复权类型: hfq(后复权) 或 qfq(前复权)'),
            ('default_api_method', 'stock_zh_a_daily', '默认数据获取API方法'),
            ('data_start_year', '2018', '数据开始年份'),
            ('request_interval', '1.0', 'API请求间隔(秒)'),
            ('max_retries', '3', '最大重试次数'),
            ('batch_size', '50', '批处理股票数量'),
            ('enable_data_validation', 'true', '是否启用数据验证')
        ]

        for key, value, desc in default_configs:
            conn.execute("""
                INSERT OR IGNORE INTO system_config (key, value, description)
                VALUES (?, ?, ?)
            """, (key, value, desc))

    def create_indexes(self):
        """创建数据库索引"""
        logger.info("Creating NEW database indexes")
        with sqlite3.connect(self.db_path) as conn:
            # 技术数据索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_new_technical_stock_date ON technical_data(stock_code, trade_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_new_technical_date ON technical_data(trade_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_new_technical_adjustment ON technical_data(adjustment_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_new_technical_api_method ON technical_data(api_method)")

            # 技术指标索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_new_indicator_stock_date_name ON technical_indicators(stock_code, trade_date, indicator_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_new_indicator_stock_date ON technical_indicators(stock_code, trade_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_new_indicator_adjustment ON technical_indicators(adjustment_type)")

            # 财务数据索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_new_financial_stock_date ON financial_data(stock_code, report_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_new_financial_adjustment ON financial_data(adjustment_type)")

        logger.info("NEW database indexes creation completed")

    def set_adjustment_type(self, adjustment_type: str = 'hfq'):
        """设置默认复权类型"""
        logger.info(f"Setting default adjustment type to: {adjustment_type}")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE system_config
                SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = 'default_adjustment_type'
            """, (adjustment_type,))

        return self.get_config_value('default_adjustment_type')

    def set_api_method(self, api_method: str = 'stock_zh_a_daily'):
        """设置默认API方法"""
        logger.info(f"Setting default API method to: {api_method}")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE system_config
                SET value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = 'default_api_method'
            """, (api_method,))

        return self.get_config_value('default_api_method')

    def get_config_value(self, key: str) -> Optional[str]:
        """获取配置值"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = pd.read_sql(
                    "SELECT value FROM system_config WHERE key = ?",
                    conn, params=[key]
                )
                return result.iloc[0]['value'] if len(result) > 0 else None
        except Exception as e:
            logger.error(f"Error getting config value for {key}: {e}")
            return None

    def get_current_settings(self) -> Dict:
        """获取当前设置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                config = pd.read_sql("SELECT key, value, description FROM system_config", conn)
                return dict(zip(config['key'], config['value']))
        except Exception as e:
            logger.error(f"Error getting current settings: {e}")
            return {}

    def save_technical_data(self, stock_code: str, data: pd.DataFrame,
                           adjustment_type: str = None, api_method: str = None) -> int:
        """保存技术数据到新数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取默认设置
                if adjustment_type is None:
                    adjustment_type = self.get_config_value('default_adjustment_type') or 'hfq'
                if api_method is None:
                    api_method = self.get_config_value('default_api_method') or 'stock_zh_a_daily'

                # 准备数据
                data_to_save = data.copy()

                # 重命名列以匹配数据库结构
                column_mapping = {
                    # API列名 -> 数据库列名
                    'date': 'trade_date',
                    'open': 'open_price',
                    'high': 'high_price',
                    'low': 'low_price',
                    'close': 'close_price',
                    'volume': 'volume',
                    'amount': 'amount',
                    # 兼容中文列名
                    '日期': 'trade_date',
                    '开盘': 'open_price',
                    '最高': 'high_price',
                    '最低': 'low_price',
                    '收盘': 'close_price',
                    '成交量': 'volume',
                    '成交额': 'amount'
                }

                for api_col, db_col in column_mapping.items():
                    if api_col in data_to_save.columns:
                        data_to_save = data_to_save.rename(columns={api_col: db_col})

                # 添加元数据
                data_to_save['stock_code'] = stock_code
                data_to_save['adjustment_type'] = adjustment_type
                data_to_save['api_method'] = api_method
                data_to_save['fetch_date'] = datetime.now()

                # 验证数据完整性
                if 'trade_date' not in data_to_save.columns:
                    logger.error(f"Missing trade_date column for {stock_code}")
                    return 0

                # 选择需要的列
                available_columns = [col for col in [
                    'stock_code', 'trade_date', 'open_price', 'high_price', 'low_price',
                    'close_price', 'volume', 'amount', 'adjustment_type',
                    'api_method', 'fetch_date'
                ] if col in data_to_save.columns]

                if len(available_columns) < 5:  # 至少需要基本的价格数据
                    logger.error(f"Insufficient columns for {stock_code}: {available_columns}")
                    return 0

                data_to_save = data_to_save[available_columns]

                # 删除已存在的记录，再插入新记录
                for _, row in data_to_save.iterrows():
                    conn.execute("""
                        DELETE FROM technical_data
                        WHERE stock_code = ? AND trade_date = ?
                    """, (stock_code, row['trade_date']))

                # 插入新记录
                data_to_save.to_sql('technical_data', conn, if_exists='append', index=False, method='multi')

                count = len(data_to_save)
                logger.log_data_update(stock_code, f"新历史数据({adjustment_type})", count, success=True)

                # 记录更新日志
                self.log_update(
                    update_type="技术数据",
                    stock_code=stock_code,
                    adjustment_type=adjustment_type,
                    api_method=api_method,
                    start_date=data_to_save['trade_date'].min(),
                    end_date=data_to_save['trade_date'].max(),
                    records_count=count,
                    success=True
                )

                return count

        except Exception as e:
            logger.log_error(f"保存新技术数据失败: {stock_code}", e)
            return 0

    def get_stock_codes(self) -> List[str]:
        """获取所有股票代码"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = pd.read_sql("SELECT DISTINCT stock_code FROM technical_data ORDER BY stock_code", conn)
                return result['stock_code'].tolist()
        except Exception as e:
            logger.error("获取股票代码列表失败", e)
            return []

    def get_stock_data_count(self, stock_code: str) -> int:
        """获取指定股票的数据记录数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = pd.read_sql("""
                    SELECT COUNT(*) as count
                    FROM technical_data
                    WHERE stock_code = ?
                """, conn, params=[stock_code])
                return result.iloc[0]['count']
        except Exception as e:
            logger.error(f"获取股票数据记录数失败: {stock_code}", e)
            return 0

    def log_update(self, update_type: str, stock_code: str, adjustment_type: str,
                   api_method: str, start_date: str, end_date: str,
                   records_count: int, success: bool, error_message: str = None):
        """记录更新日志（包含复权类型和API方法）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO update_log
                    (update_type, stock_code, adjustment_type, api_method, start_date, end_date, records_count, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (update_type, stock_code, adjustment_type, api_method, start_date, end_date, records_count, success, error_message))
        except Exception as e:
            logger.error("记录更新日志失败", e)

    def get_database_info(self) -> Dict:
        """获取新数据库信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                info = {}

                # 获取各表的记录数
                tables = ['stock_master', 'technical_data', 'technical_indicators', 'financial_data']
                for table in tables:
                    result = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn)
                    info[f"new_{table}_count"] = result.iloc[0]['count']

                # 获取数据时间范围
                date_range = pd.read_sql("""
                    SELECT MIN(trade_date) as min_date, MAX(trade_date) as max_date
                    FROM technical_data
                """, conn)
                info['new_data_start_date'] = date_range.iloc[0]['min_date']
                info['new_data_end_date'] = date_range.iloc[0]['max_date']

                # 获取数据库文件大小
                info['new_database_size_mb'] = round(self.db_path.stat().st_size / (1024 * 1024), 2) if self.db_path.exists() else 0

                # 获取有数据的股票数量
                stock_count = pd.read_sql("""
                    SELECT COUNT(DISTINCT stock_code) as stock_count
                    FROM technical_data
                """, conn)
                info['new_technical_data_records'] = info['new_technical_data_count']
                info['new_stock_master_records'] = info['new_stock_master_count']

                return info

        except Exception as e:
            logger.error("获取新数据库信息失败", e)
            return {}

    def get_adjustment_summary(self) -> pd.DataFrame:
        """获取复权类型汇总"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql("""
                    SELECT
                        adjustment_type,
                        api_method,
                        COUNT(*) as record_count,
                        COUNT(DISTINCT stock_code) as stock_count,
                        MIN(trade_date) as earliest_date,
                        MAX(trade_date) as latest_date
                    FROM technical_data
                    GROUP BY adjustment_type, api_method
                    ORDER BY record_count DESC
                """, conn)
        except Exception as e:
            logger.error("获取复权类型汇总失败", e)
            return pd.DataFrame()

    def print_current_settings(self):
        """打印当前设置"""
        settings = self.get_current_settings()
        print("\n" + "="*60)
        print("NEW DATABASE SETTINGS")
        print("="*60)

        for key, value in settings.items():
            print(f"{key}: {value}")

        print("\nRECOMMENDED SETTINGS:")
        print("- Adjustment Type: hfq (后复权) for long-term analysis")
        print("- Adjustment Type: qfq (前复权) for short-term trading")
        print("- API Method: stock_zh_a_daily (complete data)")