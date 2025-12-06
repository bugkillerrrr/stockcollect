"""
为现有数据添加API来源标识和获取完整数据
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_collector import AkshareDataCollector
from database import StockDataDB
from datetime import datetime, timedelta

def add_api_source_column():
    """添加API来源列到数据库"""
    print("Adding API source tracking to database")
    print("="*50)

    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            # 检查是否已有source列
            cursor = conn.execute("PRAGMA table_info(technical_data)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'api_source' not in columns:
                print("Adding api_source column...")
                conn.execute("ALTER TABLE technical_data ADD COLUMN api_source TEXT")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_api_source ON technical_data(api_source)")
                print("✓ API source column added")
            else:
                print("✓ API source column already exists")

            # 标记现有数据
            print("\nMarking existing data sources...")

            # 基于数据特征推断API来源
            cursor = conn.execute("""
                UPDATE technical_data
                SET api_source = 'stock_zh_a_daily'
                WHERE api_source IS NULL
                AND volume > 0
                AND amount > 0
                AND (high_price >= open_price AND high_price >= close_price AND high_price >= low_price)
            """)

            conn.commit()
            marked_count = cursor.rowcount
            print(f"✓ Marked {marked_count} records as stock_zh_a_daily source")

            # 标记可能来自旧API的数据
            cursor = conn.execute("""
                UPDATE technical_data
                SET api_source = 'unknown_old_api'
                WHERE api_source IS NULL
            """)

            conn.commit()
            unknown_count = cursor.rowcount
            print(f"✓ Marked {unknown_count} records as unknown source")

            # 显示数据源分布
            print(f"\nAPI Source Distribution:")
            source_analysis = pd.read_sql("""
                SELECT api_source, COUNT(*) as record_count, COUNT(DISTINCT stock_code) as stock_count
                FROM technical_data
                GROUP BY api_source
                ORDER BY record_count DESC
            """, conn)

            print(source_analysis)

    except Exception as e:
        print(f"Error adding API source column: {e}")
        import traceback
        traceback.print_exc()

def fetch_complete_data_for_stocks():
    """为关键股票获取完整的stock_zh_a_daily数据"""
    print(f"\n" + "="*50)
    print("FETCHING COMPLETE DATA FOR KEY STOCKS")
    print("="*50)

    collector = AkshareDataCollector(request_interval=1.0, max_retries=3)
    db = StockDataDB()

    # 获取需要重新获取数据的股票（记录数较少的）
    try:
        with sqlite3.connect(db.db_path) as conn:
            incomplete_stocks = pd.read_sql("""
                SELECT stock_code, COUNT(*) as record_count,
                       MAX(trade_date) as latest_date
                FROM technical_data
                GROUP BY stock_code
                HAVING record_count < 1800  -- 少于完整数据的股票
                ORDER BY record_count ASC
            """, conn)

            print(f"Found {len(incomplete_stocks)} stocks with incomplete data:")
            if len(incomplete_stocks) > 0:
                print(incomplete_stocks)

                for _, stock_row in incomplete_stocks.iterrows():
                    stock_code = stock_row['stock_code']
                    print(f"\nFetching complete data for {stock_code}...")

                    # 删除现有的不完整数据
                    conn.execute("DELETE FROM technical_data WHERE stock_code = ?", (stock_code,))
                    conn.commit()

                    # 重新获取完整历史数据（2018年至今）
                    start_date = "20180101"
                    end_date = datetime.now().strftime("%Y%m%d")

                    try:
                        data = collector.get_stock_data(stock_code, start_date, end_date)

                        if data is not None and len(data) > 0:
                            # 保存到数据库
                            saved_count = db.save_technical_data(stock_code, data)
                            print(f"✓ Fetched and saved {saved_count} records for {stock_code}")

                            # 验证数据完整性
                            db_count = db.get_stock_data_count(stock_code)
                            print(f"✓ Database now contains {db_count} records for {stock_code}")

                        else:
                            print(f"✗ Failed to fetch data for {stock_code}")

                    except Exception as e:
                        print(f"✗ Error fetching {stock_code}: {str(e)}")
            else:
                print("✓ All stocks have complete data!")

    except Exception as e:
        print(f"Error in fetching complete data: {e}")
        import traceback
        traceback.print_exc()

def verify_data_consistency():
    """验证数据一致性"""
    print(f"\n" + "="*50)
    print("VERIFING DATA CONSISTENCY")
    print("="*50)

    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            # 检查数据质量
            quality_report = pd.read_sql("""
                SELECT
                    stock_code,
                    api_source,
                    COUNT(*) as total_records,
                    SUM(CASE WHEN volume > 0 THEN 1 ELSE 0 END) as records_with_volume,
                    SUM(CASE WHEN amount > 0 THEN 1 ELSE 0 END) as records_with_amount,
                    SUM(CASE WHEN high_price >= open_price AND high_price >= close_price AND high_price >= low_price THEN 1 ELSE 0 END) as valid_price_records,
                    MIN(trade_date) as earliest_date,
                    MAX(trade_date) as latest_date
                FROM technical_data
                GROUP BY stock_code, api_source
                ORDER BY total_records DESC
            """, conn)

            print("Data consistency by stock and API source:")
            print(quality_report)

            # 计算数据完整性指标
            print(f"\nCompleteness Summary:")
            total_records = quality_report['total_records'].sum()
            volume_complete = quality_report['records_with_volume'].sum()
            amount_complete = quality_report['records_with_amount'].sum()
            price_valid = quality_report['valid_price_records'].sum()

            print(f"Total records: {total_records}")
            print(f"Volume complete: {volume_complete}/{total_records} ({volume_complete/total_records:.1%})")
            print(f"Amount complete: {amount_complete}/{total_records} ({amount_complete/total_records:.1%})")
            print(f"Price relationships valid: {price_valid}/{total_records} ({price_valid/total_records:.1%})")

            if volume_complete / total_records > 0.99:
                print("✓ Data appears to be from stock_zh_a_daily API (complete volume data)")
            elif volume_complete / total_records < 0.5:
                print("⚠ Data appears to be from older API (missing volume data)")
            else:
                print("⚠ Mixed data sources detected")

    except Exception as e:
        print(f"Error verifying consistency: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sqlite3
    import pandas as pd

    add_api_source_column()
    fetch_complete_data_for_stocks()
    verify_data_consistency()