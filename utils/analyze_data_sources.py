"""
分析数据库中不同API来源的数据
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import StockDataDB

def analyze_data_sources():
    """分析数据库中不同来源的数据"""
    print("Analyzing Data Sources in Database")
    print("="*50)

    db = StockDataDB()

    try:
        # 1. 查看数据日期分布
        print("1. Data Date Distribution Analysis:")
        with sqlite3.connect(db.db_path) as conn:
            # 获取数据的日期范围
            date_analysis = pd.read_sql("""
                SELECT
                    stock_code,
                    MIN(trade_date) as earliest_date,
                    MAX(trade_date) as latest_date,
                    COUNT(*) as record_count,
                    COUNT(DISTINCT trade_date) as trading_days
                FROM technical_data
                GROUP BY stock_code
                ORDER BY record_count DESC
            """, conn)

            print(f"Total stocks: {len(date_analysis)}")
            print(f"Total records: {date_analysis['record_count'].sum()}")

            # 分析数据的更新时间特征
            print(f"\nStock sample analysis:")
            print(date_analysis.head(10))

            # 2. 检查数据密度（缺失交易日的股票）
            print(f"\n2. Data Completeness Analysis:")

            # 计算每个股票的理论交易日数量
            for _, row in date_analysis.head(5).iterrows():
                stock_code = row['stock_code']
                earliest = pd.to_datetime(row['earliest_date'])
                latest = pd.to_datetime(row['latest_date'])
                trading_days = row['trading_days']

                # 估算理论交易日（简单计算，节假日未过滤）
                theoretical_days = (latest - earliest).days
                trading_density = trading_days / theoretical_days if theoretical_days > 0 else 0

                print(f"{stock_code}: {trading_days} trading days over {theoretical_days} calendar days ({trading_density:.2%} density)")

            # 3. 检查是否有数据来源标识
            print(f"\n3. Checking for Data Source Identification:")

            # 查看是否有额外的字段可以识别数据来源
            column_info = pd.read_sql("PRAGMA table_info(technical_data)", conn)
            print(f"Technical data table columns:")
            for col in column_info['name']:
                print(f"  - {col}")

            # 4. 分析数据获取的时间戳模式
            print(f"\n4. Data Creation Timestamp Analysis:")
            timestamp_analysis = pd.read_sql("""
                SELECT
                    DATE(created_at) as creation_date,
                    stock_code,
                    COUNT(*) as records_created,
                    MIN(trade_date) as min_trade_date,
                    MAX(trade_date) as max_trade_date
                FROM technical_data
                WHERE created_at IS NOT NULL
                GROUP BY DATE(created_at), stock_code
                ORDER BY creation_date DESC, records_created DESC
                LIMIT 20
            """, conn)

            print("Recent data creation patterns:")
            print(timestamp_analysis)

        # 5. 检查是否能通过数据特征区分API来源
        print(f"\n5. API Source Detection by Data Features:")
        with sqlite3.connect(db.db_path) as conn:
            # 检查volume字段的数据分布（不同API可能返回不同的数据格式）
            volume_analysis = pd.read_sql("""
                SELECT
                    stock_code,
                    COUNT(*) as total_records,
                    SUM(CASE WHEN volume = 0 THEN 1 ELSE 0 END) as zero_volume_records,
                    MIN(volume) as min_volume,
                    MAX(volume) as max_volume,
                    AVG(volume) as avg_volume
                FROM technical_data
                GROUP BY stock_code
                ORDER BY total_records DESC
                LIMIT 10
            """, conn)

            print("Volume data analysis (can help identify API source):")
            print(volume_analysis)

            # 检查amount字段
            amount_analysis = pd.read_sql("""
                SELECT
                    stock_code,
                    COUNT(*) as total_records,
                    SUM(CASE WHEN amount = 0 THEN 1 ELSE 0 END) as zero_amount_records,
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount,
                    AVG(amount) as avg_amount
                FROM technical_data
                GROUP BY stock_code
                ORDER BY total_records DESC
                LIMIT 10
            """, conn)

            print("\nAmount data analysis:")
            print(amount_analysis)

        # 6. 数据质量检查
        print(f"\n6. Data Quality Check:")
        with sqlite3.connect(db.db_path) as conn:
            quality_check = pd.read_sql("""
                SELECT
                    stock_code,
                    COUNT(*) as total_records,
                    SUM(CASE WHEN open_price > 0 THEN 1 ELSE 0 END) as valid_open_records,
                    SUM(CASE WHEN high_price > 0 THEN 1 ELSE 0 END) as valid_high_records,
                    SUM(CASE WHEN low_price > 0 THEN 1 ELSE 0 END) as valid_low_records,
                    SUM(CASE WHEN close_price > 0 THEN 1 ELSE 0 END) as valid_close_records,
                    SUM(CASE WHEN high_price >= low_price AND high_price >= open_price AND high_price >= close_price THEN 1 ELSE 0 END) as valid_price_relationship_records
                FROM technical_data
                GROUP BY stock_code
                ORDER BY total_records DESC
                LIMIT 10
            """, conn)

            print("Data quality analysis:")
            print(quality_check)

    except Exception as e:
        print(f"Error analyzing data sources: {e}")
        import traceback
        traceback.print_exc()

def suggest_data_management():
    """提供数据管理建议"""
    print(f"\n" + "="*50)
    print("DATA MANAGEMENT SUGGESTIONS")
    print("="*50)

    db = StockDataDB()

    try:
        # 获取数据库信息
        db_info = db.get_database_info()

        if db_info:
            print(f"Current database status:")
            for key, value in db_info.items():
                print(f"  {key}: {value}")

        print(f"\nRecommendations for managing mixed API sources:")

        print(f"""
1. **如果数据质量一致，可以保留所有数据**：
   - stock_zh_a_daily API提供的数据更完整（包含volume等所有字段）
   - 如果现有数据质量良好，无需删除
   - 未来的更新将使用stock_zh_a_daily，逐步统一数据源

2. **如果希望完全统一，可以考虑清理**：
   - 识别使用旧API（缺失volume）的股票数据
   - 重新获取这些股票的完整历史数据
   - 删除不完整的历史数据

3. **最佳实践建议**：
   - 保留现有数据，确保数据连续性
   - 对数据质量进行标记（在表中添加API来源字段）
   - 新数据获取使用stock_zh_a_daily
   - 对于关键数据缺失的股票，重新获取完整历史

4. **如何识别当前数据来源**：
   - volume = 0 的记录可能来自旧API
   - 数据密度低的股票可能来自不同的API
   - 根据created_at时间戳可以区分不同时期的获取操作
        """)

    except Exception as e:
        print(f"Error generating suggestions: {e}")

def identify_incomplete_stocks():
    """识别可能数据不完整的股票"""
    print(f"\n" + "="*50)
    print("IDENTIFYING STOCKS WITH INCOMPLETE DATA")
    print("="*50)

    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            # 查找volume为0的股票（可能来自旧API）
            incomplete_stocks = pd.read_sql("""
                SELECT
                    stock_code,
                    COUNT(*) as total_records,
                    SUM(CASE WHEN volume = 0 THEN 1 ELSE 0 END) as zero_volume_count,
                    MAX(trade_date) as latest_date,
                    MIN(trade_date) as earliest_date,
                    AVG(volume) as avg_volume
                FROM technical_data
                GROUP BY stock_code
                HAVING SUM(CASE WHEN volume = 0 THEN 1 ELSE 0 END) > 0
                   OR COUNT(*) < 200  -- 交易日数量少于预期的股票
                ORDER BY zero_volume_count DESC, total_records ASC
            """, conn)

            print(f"Found {len(incomplete_stocks)} stocks with potentially incomplete data:")

            if len(incomplete_stocks) > 0:
                print(incomplete_stocks.head(20))

                print(f"\nRecommendation for these {len(incomplete_stocks)} stocks:")
                print("- Consider re-fetching complete historical data using stock_zh_a_daily")
                print("- These stocks may have been fetched with older API lacking volume data")
            else:
                print("All stocks appear to have complete data!")

    except Exception as e:
        print(f"Error identifying incomplete stocks: {e}")

if __name__ == "__main__":
    analyze_data_sources()
    suggest_data_management()
    identify_incomplete_stocks()