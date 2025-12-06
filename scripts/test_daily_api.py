"""
测试stock_zh_a_daily API
"""
import akshare as ak
import pandas as pd

def test_stock_zh_a_daily():
    """测试stock_zh_a_daily方法"""
    print("Testing: ak.stock_zh_a_daily")

    # 测试不同的股票代码格式
    test_codes = [
        "000001",      # 不带前缀
        "sz000001",    # 深圳前缀
        "sh600000",    # 上海前缀
        "600000",      # 上海不带前缀
        "bj430047"     # 北交所（测试是否支持）
    ]

    for symbol in test_codes:
        print(f"\nTesting with symbol: {symbol}")
        try:
            data = ak.stock_zh_a_daily(
                symbol=symbol,
                start_date="20200101",
                end_date="20200131",
                adjust="hfq"  # 后复权
            )

            print(f"✓ Success! Shape: {data.shape}")
            print(f"Columns: {list(data.columns)}")

            if len(data) > 0:
                print(f"Date range: {data.iloc[0, 0]} to {data.iloc[-1, 0]}")
                print(f"Sample data:")
                print(data.head(1))

                # 检查数据完整性
                print(f"Data quality check:")
                for col in data.columns:
                    null_count = data[col].isnull().sum()
                    print(f"  {col}: {null_count} null values")

        except Exception as e:
            print(f"✗ Failed: {str(e)}")

def test_vs_current():
    """对比stock_zh_a_daily与stock_zh_a_hist"""
    print("\n" + "="*60)
    print("Comparing stock_zh_a_daily vs stock_zh_a_hist")
    print("="*60)

    try:
        # 测试daily API
        print("Testing stock_zh_a_daily...")
        daily_data = ak.stock_zh_a_daily(
            symbol="000001",
            start_date="20200101",
            end_date="20200131",
            adjust="hfq"
        )
        print(f"Daily API - Shape: {daily_data.shape}, Columns: {list(daily_data.columns)}")

        # 测试hist API（如果可用）
        try:
            print("Testing stock_zh_a_hist...")
            hist_data = ak.stock_zh_a_hist(
                symbol="000001",
                period="daily",
                start_date="20200101",
                end_date="20200131",
                adjust="hfq"
            )
            print(f"Hist API - Shape: {hist_data.shape}, Columns: {list(hist_data.columns)}")

        except Exception as e:
            print(f"Hist API failed: {e}")
            hist_data = None

        # 比较数据
        if 'daily_data' in locals() and daily_data is not None:
            print(f"\nDaily API data analysis:")
            print(f"  Date range: {daily_data.iloc[0, 0]} to {daily_data.iloc[-1, 0]}")
            print(f"  Data types: {daily_data.dtypes.to_dict()}")

    except Exception as e:
        print(f"Comparison failed: {e}")

if __name__ == "__main__":
    test_stock_zh_a_daily()
    test_vs_current()