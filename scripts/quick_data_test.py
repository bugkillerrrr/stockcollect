"""
Quick Data Test - Test the core data collection functionality
"""
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_quick_collection():
    """Quick test of data collection"""
    print("=" * 60)
    print("Stock Data System - Quick Data Test")
    print("=" * 60)

    try:
        # Import modules
        from database import StockDataDB
        from data_collector import AkshareDataCollector
        from logger import get_logger

        print("SUCCESS: All modules imported successfully")

        # Setup
        logger = get_logger()
        collector = AkshareDataCollector()
        db = StockDataDB()

        print("SUCCESS: System components initialized")

        # Test stocks
        test_stocks = ["000001", "000002"]

        print(f"\nTesting with stocks: {test_stocks}")

        for stock_code in test_stocks:
            print(f"\n[{stock_code}] Collecting data...")

            try:
                # Get data
                data = collector.get_stock_data(stock_code, "20251120", "20251124")

                if data is not None and not data.empty:
                    print(f"SUCCESS: Retrieved {len(data)} records")
                    print(f"  Columns: {list(data.columns)}")

                    # Try to save
                    count = db.save_technical_data(stock_code, data)
                    if count > 0:
                        print(f"SUCCESS: Saved {count} records to database")
                    else:
                        print("WARNING: Failed to save data")
                else:
                    print("WARNING: No data retrieved")

            except Exception as e:
                print(f"ERROR: {e}")

        # Check database status
        try:
            stats = db.get_database_info()
            print(f"\nDatabase status:")
            print(f"  Technical data records: {stats.get('technical_data_records', 0)}")
            print(f"  Database size: {stats.get('database_size_mb', 0):.2f} MB")
        except Exception as e:
            print(f"ERROR getting database info: {e}")

        print("\n" + "=" * 60)
        print("QUICK TEST COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: Test failed - {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quick_collection()