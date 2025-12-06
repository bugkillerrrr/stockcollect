"""
股票数据系统数据库模块
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

logger = get_logger("database")


class StockDataDB:
    """股票数据数据库管理类"""

    def __init__(self, db_path: str = "data/stock_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
        self.create_indexes()

    def init_database(self):
        """初始化数据库表结构"""
        logger.info("Initializing database schema")
        with sqlite3.connect(self.db_path) as conn:
            # 股票基础信息表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_master (
                    stock_code TEXT PRIMARY KEY,
                    stock_name TEXT,
                    industry TEXT,
                    market TEXT,
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

        logger.info("Database schema initialization completed")

    def create_indexes(self):
        """创建数据库索引"""
        logger.info("Creating database indexes")
        with sqlite3.connect(self.db_path) as conn:
            # 技术数据索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_technical_stock_date ON technical_data(stock_code, trade_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_technical_date ON technical_data(trade_date)")

            # 技术指标索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_indicator_stock_date_name ON technical_indicators(stock_code, trade_date, indicator_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_indicator_stock_date ON technical_indicators(stock_code, trade_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_indicator_name ON technical_indicators(indicator_name)")

            # 财务数据索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_stock_date ON financial_data(stock_code, report_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_date ON financial_data(report_date)")

        logger.info("Database indexes creation completed")

    def save_technical_data(self, stock_code: str, data: pd.DataFrame) -> int:
        """保存技术数据到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 准备数据
                data_to_save = data.copy()

                # 重命名列以匹配数据库结构
                # stock_zh_a_daily API返回完整的英文列名
                column_mapping = {
                    # API列名 -> 数据库列名
                    'date': 'trade_date',
                    'open': 'open_price',
                    'high': 'high_price',
                    'low': 'low_price',
                    'close': 'close_price',
                    'volume': 'volume',  # API直接提供volume数据
                    'amount': 'amount',
                    # 兼容其他可能的API列名
                    '日期': 'trade_date',
                    '股票代码': 'stock_code',
                    '开盘': 'open_price',
                    '最高': 'high_price',
                    '最低': 'low_price',
                    '收盘': 'close_price',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    'outstanding_share': 'outstanding_share',
                    'turnover': 'turnover'
                }

                for akshare_col, db_col in column_mapping.items():
                    if akshare_col in data_to_save.columns:
                        data_to_save = data_to_save.rename(columns={akshare_col: db_col})

                # 确保股票代码正确（在列映射之后）
                if 'stock_code' not in data_to_save.columns:
                    data_to_save['stock_code'] = stock_code
                else:
                    # 确保stock_code是字符串而不是Series
                    data_to_save['stock_code'] = stock_code

                data_to_save['created_at'] = datetime.now()

                # 选择需要的列
                # stock_zh_a_daily API提供完整字段，包括volume
                required_columns = ['stock_code', 'trade_date', 'open_price', 'high_price',
                                  'low_price', 'close_price', 'volume', 'amount', 'created_at']

                # 检查必需的列是否存在
                missing_columns = [col for col in required_columns if col not in data_to_save.columns and col != 'created_at']
                if missing_columns:
                    logger.warning(f"股票{stock_code}数据缺少列: {missing_columns}")

                available_columns = [col for col in required_columns if col in data_to_save.columns]
                data_to_save = data_to_save[available_columns]

                # 保存数据（使用REPLACE INTO处理重复数据）
                # 先删除已存在的记录，再插入新记录
                if not data_to_save.empty:
                    for _, row in data_to_save.iterrows():
                        stock_code = row['stock_code']
                        trade_date = row['trade_date']
                        # 删除已存在的记录
                        conn.execute(
                            'DELETE FROM technical_data WHERE stock_code = ? AND trade_date = ?',
                            (stock_code, trade_date)
                        )

                    # 插入新记录
                    data_to_save.to_sql('technical_data', conn, if_exists='append', index=False, method='multi')

                count = len(data_to_save)
                logger.log_data_update(stock_code, "技术数据", count, success=True)
                return count

        except Exception as e:
            logger.log_error(f"保存技术数据失败: {stock_code}", e)
            return 0

    def save_financial_data(self, stock_code: str, data: pd.DataFrame, report_type: str = "quarterly") -> int:
        """保存财务数据到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 准备数据
                data_to_save = data.copy()
                data_to_save['stock_code'] = stock_code
                data_to_save['report_type'] = report_type
                data_to_save['created_at'] = datetime.now()

                # 保存数据
                data_to_save.to_sql('financial_data', conn, if_exists='append', index=False)

                count = len(data_to_save)
                logger.log_data_update(stock_code, f"财务数据({report_type})", count, success=True)
                return count

        except Exception as e:
            logger.log_error(f"保存财务数据失败: {stock_code}", e)
            return 0

    def save_technical_indicators(self, indicators_data: pd.DataFrame) -> int:
        """保存技术指标数据到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                indicators_data['created_at'] = datetime.now()
                indicators_data.to_sql('technical_indicators', conn, if_exists='append', index=False)

                count = len(indicators_data)
                logger.info(f"Saved technical indicators data: {count} records")
                return count

        except Exception as e:
            logger.log_error("保存技术指标数据失败", e)
            return 0

    def get_stock_codes(self) -> List[str]:
        """获取所有股票代码"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = pd.read_sql("SELECT DISTINCT stock_code FROM technical_data ORDER BY stock_code", conn)
                return result['stock_code'].tolist()
        except Exception as e:
            logger.log_error("获取股票代码列表失败", e)
            return []

    def get_last_update_date(self, stock_code: str) -> Optional[str]:
        """获取股票的最后更新日期"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = pd.read_sql(
                    "SELECT MAX(trade_date) as last_date FROM technical_data WHERE stock_code = ?",
                    conn, params=[stock_code]
                )
                return result.iloc[0]['last_date'] if not pd.isna(result.iloc[0]['last_date']) else None
        except Exception as e:
            logger.log_error(f"获取最后更新日期失败: {stock_code}", e)
            return None

    def log_update(self, update_type: str, stock_code: str, start_date: str, end_date: str,
                   records_count: int, success: bool, error_message: str = None):
        """记录更新日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO update_log
                    (update_type, stock_code, start_date, end_date, records_count, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (update_type, stock_code, start_date, end_date, records_count, success, error_message))
        except Exception as e:
            logger.log_error("记录更新日志失败", e)

    def get_database_info(self) -> Dict:
        """获取数据库信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                info = {}

                # 获取各表的记录数
                tables = ['stock_master', 'technical_data', 'technical_indicators', 'financial_data']
                for table in tables:
                    result = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn)
                    info[f"{table}_count"] = result.iloc[0]['count']

                # 获取数据时间范围
                date_range = pd.read_sql("""
                    SELECT MIN(trade_date) as min_date, MAX(trade_date) as max_date
                    FROM technical_data
                """, conn)
                info['data_start_date'] = date_range.iloc[0]['min_date']
                info['data_end_date'] = date_range.iloc[0]['max_date']

                # 获取数据库文件大小
                info['database_size_mb'] = round(self.db_path.stat().st_size / (1024 * 1024), 2)

                # 获取有数据的股票数量
                stock_count = pd.read_sql("""
                    SELECT COUNT(DISTINCT stock_code) as stock_count
                    FROM technical_data
                """, conn)
                info['technical_data_records'] = info['technical_data_count']
                info['stock_master_records'] = info['stock_master_count']

                return info

        except Exception as e:
            logger.log_error("获取数据库信息失败", e)
            return {}

    def get_completed_stock_codes(self) -> List[str]:
        """获取已完成数据收集的股票代码列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = pd.read_sql("""
                    SELECT DISTINCT stock_code
                    FROM technical_data
                    ORDER BY stock_code
                """, conn)
                return result['stock_code'].tolist()
        except Exception as e:
            logger.log_error("获取已完成股票代码失败", e)
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
            logger.log_error(f"获取股票数据记录数失败: {stock_code}", e)
            return 0