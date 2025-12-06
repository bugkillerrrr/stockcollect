"""
BettaFish Environment Test - Real Data Collection
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Fix encoding issues
try:
    from config.encoding_fix import setup_console_encoding, print_utf8
    setup_console_encoding()
except ImportError:
    pass  # Continue if encoding fix module not available

def test_real_data_collection():
    """Test real data collection in BettaFish environment"""
    print("=" * 60)
    print("Stock Data System - Real Data Test (BettaFish Environment)")
    print("=" * 60)

    try:
        # Import modules
        from database import StockDataDB
        from data_collector import AkshareDataCollector
        from data_updater_simple import DataUpdater
        from logger import setup_logging

        print("SUCCESS: All modules imported successfully")

        # Setup logging
        setup_logging("logs", "INFO")
        print("SUCCESS: Logging system initialized")

        # Initialize components
        db = StockDataDB("data/test_bettafish.db")
        collector = AkshareDataCollector(request_interval=1.0, max_retries=3)
        updater = DataUpdater(db, collector)
        print("SUCCESS: System components initialized")

        # Select test stocks
        test_stocks = [
            "000001",  # Ping An Bank
            "000002",  # Vanke A
            "600036",  # China Merchants Bank
            "600519"   # Kweichow Moutai
        ]

        # Calculate date range (last 4 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=4)

        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        print(f"\nDate range: {start_date_str} - {end_date_str}")
        print(f"Test stocks: {test_stocks}")

        # Get stock list
        print("\n1. Getting stock list...")
        stock_list = collector.get_stock_list()
        if stock_list is not None and len(stock_list) > 0:
            print(f"SUCCESS: Stock list retrieved - {len(stock_list)} stocks")

            # Show test stock names
            print("Test stocks:")
            for stock_code in test_stocks:
                stock_info = stock_list[stock_list['stock_code'] == stock_code]
                if len(stock_info) > 0:
                    name = stock_info.iloc[0]['stock_name']
                    print(f"  {stock_code} - {name}")
        else:
            print("FAILED: Could not retrieve stock list")
            return False

        # Collect stock data
        print(f"\n2. Collecting stock data...")
        success_count = 0

        for i, stock_code in enumerate(test_stocks, 1):
            print(f"\n[{i}/{len(test_stocks)}] Collecting data for {stock_code}...")

            try:
                # Get stock data
                data = collector.get_stock_data(stock_code, start_date_str, end_date_str)

                if data is not None and len(data) > 0:
                    print(f"SUCCESS: Retrieved {len(data)} records")

                    # Show data preview
                    print(f"  Columns: {list(data.columns)}")
                    print("  First 3 records:")
                    for j, (_, row) in enumerate(data.head(3).iterrows()):
                        if '日期' in data.columns and '收盘' in data.columns:
                            date = row['日期']
                            close = row['收盘']
                            volume = row.get('成交量', 'N/A')
                            print(f"    {j+1}. Date: {date}, Close: {close}, Volume: {volume}")

                    # Save to database
                    saved_count = db.save_technical_data(stock_code, data)
                    if saved_count > 0:
                        print(f"SUCCESS: Saved {saved_count} records to database")
                        success_count += 1
                    else:
                        print("FAILED: Could not save data")
                else:
                    print("FAILED: No data retrieved")

            except Exception as e:
                print(f"ERROR: Failed to collect data for {stock_code}: {str(e)}")

        # Show database information
        print(f"\n3. Database information...")
        db_info = db.get_database_info()
        print(f"  Technical data records: {db_info.get('technical_data_count', 0)}")
        print(f"  Stock master records: {db_info.get('stock_master_count', 0)}")
        print(f"  Database size: {db_info.get('database_size_mb', 0)} MB")

        # Test data query
        print(f"\n4. Testing data query...")
        try:
            stock_codes = db.get_stock_codes()
            print(f"  Stock codes in database: {stock_codes}")

            for stock_code in stock_codes:
                last_date = db.get_last_update_date(stock_code)
                print(f"  {stock_code} last update date: {last_date}")

        except Exception as e:
            print(f"  Query test error: {str(e)}")

        # Summary
        print(f"\n" + "=" * 60)
        print("TEST RESULTS:")
        print(f"  Stocks tested: {len(test_stocks)}")
        print(f"  Successfully collected: {success_count}")
        print(f"  Database records: {db_info.get('technical_data_count', 0)}")
        print(f"  System status: {'NORMAL' if success_count > 0 else 'ABNORMAL'}")

        if success_count > 0:
            print("\n*** REAL DATA TEST SUCCESSFUL! ***")
            print("The system is working correctly in BettaFish environment.")
        else:
            print("\n*** DATA COLLECTION FAILED ***")
            print("Please check network connection or Akshare status.")

        return success_count > 0

    except Exception as e:
        print(f"\nERROR: Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Starting real data test in BettaFish environment...")
    print("Please ensure:")
    print("1. BettaFish environment is activated")
    print("2. Network connection is working")
    print("3. akshare package is installed")

    success = test_real_data_collection()

    if success:
        print("\n*** ALL TESTS PASSED! ***")
        print("The stock data system is ready for use.")
    else:
        print("\n*** TESTS FAILED ***")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()