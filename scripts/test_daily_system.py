"""
测试使用stock_zh_a_daily API的修改后系统
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_collector import AkshareDataCollector
from database import StockDataDB
import pandas as pd
from datetime import datetime, timedelta

def test_daily_api_system():
    """测试使用stock_zh_a_daily的系统"""
    print("Testing Stock Data System with stock_zh_a_daily API")
    print("="*60)

    # 初始化组件
    collector = AkshareDataCollector(request_interval=1.0, max_retries=3)
    db = StockDataDB()

    # 测试数据获取
    print("1. Testing data collection with stock_zh_a_daily...")
    test_stocks = ["000001", "000002", "600000"]
    start_date = "20200101"
    end_date = "20200131"

    for stock_code in test_stocks:
        print(f"\nTesting {stock_code} with stock_zh_a_daily...")
        try:
            data = collector.get_stock_data(stock_code, start_date, end_date)

            if data is not None and len(data) > 0:
                print(f"✓ Data collection successful for {stock_code}")
                print(f"  Shape: {data.shape}")
                print(f"  Columns: {list(data.columns)}")
                print(f"  Date range: {data['date'].min()} to {data['date'].max()}")

                # 检查关键字段
                key_fields = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
                missing_fields = [field for field in key_fields if field not in data.columns]
                if missing_fields:
                    print(f"  ⚠ Missing fields: {missing_fields}")
                else:
                    print(f"  ✓ All required fields present")

                # 检查数据质量
                print(f"  Data quality:")
                print(f"    Volume > 0: {(data['volume'] > 0).sum()}/{len(data)} rows")
                print(f"    Amount > 0: {(data['amount'] > 0).sum()}/{len(data)} rows")
                print(f"    Price ranges valid: {all((data['high'] >= data['low']) & (data['high'] >= data['open']) & (data['high'] >= data['close']))}")

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
            if key != 'database_size_mb':  # 跳过文件大小信息，保持输出简洁
                print(f"  {key}: {value}")

    # 测试北交所支持
    print(f"\n5. Testing Beijing Stock Exchange support...")
    try:
        bj_data = collector.get_stock_data("430047", "20200101", "20200131")
        if bj_data is not None and len(bj_data) > 0:
            print("✓ Beijing Stock Exchange data collection successful")
            print(f"  Shape: {bj_data.shape}")
        else:
            print("⚠ Beijing Stock Exchange data collection failed (expected limitation)")
    except Exception as e:
        print(f"⚠ Beijing Stock Exchange error: {str(e)} (expected limitation)")

    # 比较数据完整性
    print(f"\n6. Data completeness comparison:")
    try:
        # 获取完整数据范围的数据
        full_data = collector.get_stock_data("000001", "20200101", "20201231")
        if full_data is not None:
            print(f"  000001 full year 2020 data:")
            print(f"    Trading days: {len(full_data)}")
            print(f"    Date range: {full_data['date'].min()} to {full_data['date'].max()}")

            # 检查成交量数据的完整性
            volume_zero = (full_data['volume'] == 0).sum()
            if volume_zero == 0:
                print(f"    ✓ Volume data complete: {len(full_data)} non-zero records")
            else:
                print(f"    ⚠ Volume data incomplete: {volume_zero}/{len(full_data)} zero records")
    except Exception as e:
        print(f"  Error checking data completeness: {e}")

if __name__ == "__main__":
    test_daily_api_system()