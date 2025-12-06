"""
测试修改后的系统
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_collector import AkshareDataCollector
from database import StockDataDB
import pandas as pd
from datetime import datetime, timedelta

def test_updated_system():
    """测试修改后的系统"""
    print("Testing Updated Stock Data System")
    print("="*50)

    # 初始化组件
    collector = AkshareDataCollector(request_interval=0.5, max_retries=3)
    db = StockDataDB()

    # 测试数据获取
    print("1. Testing data collection with new API...")
    test_stocks = ["000001", "000002", "600000"]
    start_date = "20200101"
    end_date = "20200131"

    for stock_code in test_stocks:
        print(f"\nTesting {stock_code}...")
        try:
            data = collector.get_stock_data(stock_code, start_date, end_date)

            if data is not None and len(data) > 0:
                print(f"✓ Data collection successful for {stock_code}")
                print(f"  Shape: {data.shape}")
                print(f"  Columns: {list(data.columns)}")
                print(f"  Date range: {data['date'].min()} to {data['date'].max()}")

                # 测试数据保存到数据库
                print(f"\n2. Testing database save for {stock_code}...")
                saved_count = db.save_technical_data(stock_code, data)
                print(f"✓ Saved {saved_count} records to database")

                # 验证数据库中的数据
                print(f"\n3. Verifying data in database for {stock_code}...")
                db_count = db.get_stock_data_count(stock_code)
                print(f"✓ Database shows {db_count} records for {stock_code}")

                last_date = db.get_last_update_date(stock_code)
                print(f"✓ Last update date: {last_date}")

            else:
                print(f"✗ No data collected for {stock_code}")

        except Exception as e:
            print(f"✗ Error testing {stock_code}: {str(e)}")
            import traceback
            traceback.print_exc()

    # 显示数据库信息
    print(f"\n4. Database Information:")
    db_info = db.get_database_info()
    if db_info:
        for key, value in db_info.items():
            print(f"  {key}: {value}")

    # 显示所有已完成的股票
    print(f"\n5. Completed stocks in database:")
    completed_stocks = db.get_completed_stock_codes()
    print(f"  Total: {len(completed_stocks)} stocks")
    if completed_stocks:
        print(f"  Sample: {completed_stocks[:5]}")

if __name__ == "__main__":
    test_updated_system()