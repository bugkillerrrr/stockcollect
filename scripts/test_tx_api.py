"""
测试正确的akshare tx API函数
"""
import akshare as ak
import pandas as pd

def test_stock_zh_a_hist_tx():
    """测试 stock_zh_a_hist_tx 函数"""
    print("Testing: ak.stock_zh_a_hist_tx")

    try:
        # 测试当前tx API
        data = ak.stock_zh_a_hist_tx(
            symbol="000001",
            start_date="20200101",
            end_date="20231027",
            adjust="hfq"
        )

        print(f"Success!")
        print(f"Data shape: {data.shape}")
        print(f"Columns: {list(data.columns)}")
        print(f"Data types:\n{data.dtypes}")
        print(f"First few rows:")
        print(data.head())
        print(f"Last few rows:")
        print(data.tail())

        return data

    except Exception as e:
        print(f"Failed: {str(e)}")
        return None

def test_stock_zh_a_hist():
    """测试当前使用的 stock_zh_a_hist 函数"""
    print("\n" + "="*60)
    print("Testing current: ak.stock_zh_a_hist")

    try:
        # 测试当前API
        data = ak.stock_zh_a_hist(
            symbol="000001",
            period="daily",
            start_date="20200101",
            end_date="20231027",
            adjust="hfq"
        )

        print(f"Success!")
        print(f"Data shape: {data.shape}")
        print(f"Columns: {list(data.columns)}")
        print(f"Data types:\n{data.dtypes}")
        print(f"First few rows:")
        print(data.head())
        print(f"Last few rows:")
        print(data.tail())

        return data

    except Exception as e:
        print(f"Failed: {str(e)}")
        return None

if __name__ == "__main__":
    tx_data = test_stock_zh_a_hist_tx()
    current_data = test_stock_zh_a_hist()

    if tx_data is not None and current_data is not None:
        print("\n" + "="*60)
        print("COMPARISON")
        print("="*60)

        print("Column comparison:")
        print(f"TX API columns: {list(tx_data.columns)}")
        print(f"Current API columns: {list(current_data.columns)}")

        # Check if columns are compatible
        common_cols = set(tx_data.columns) & set(current_data.columns)
        tx_only = set(tx_data.columns) - set(current_data.columns)
        current_only = set(current_data.columns) - set(tx_data.columns)

        print(f"\nCommon columns: {common_cols}")
        print(f"TX API only: {tx_only}")
        print(f"Current API only: {current_only}")