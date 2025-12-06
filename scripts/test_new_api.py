"""
测试新的ak.stock_zh_a_hist_tx_df API
"""
import akshare as ak
import pandas as pd
from datetime import datetime

def test_new_api():
    """测试新的数据获取API"""
    print("Testing new API: ak.stock_zh_a_hist_tx_df")

    try:
        # 测试新API
        stock_zh_a_hist_tx_df = ak.stock_zh_a_hist_tx_df(
            symbol="sz000001",
            start_date="20200101",
            end_date="20231027",
            adjust="hfq"
        )

        print(f"New API Success!")
        print(f"Data shape: {stock_zh_a_hist_tx_df.shape}")
        print(f"Columns: {list(stock_zh_a_hist_tx_df.columns)}")
        print(f"Data types:\n{stock_zh_a_hist_tx_df.dtypes}")
        print(f"First few rows:")
        print(stock_zh_a_hist_tx_df.head())
        print(f"Last few rows:")
        print(stock_zh_a_hist_tx_df.tail())

        return stock_zh_a_hist_tx_df

    except Exception as e:
        print(f"New API failed: {str(e)}")
        return None

def test_old_api():
    """测试当前使用的数据获取API"""
    print("\n" + "="*50)
    print("Testing current API: ak.stock_zh_a_hist")

    try:
        # 测试当前API
        stock_zh_a_hist = ak.stock_zh_a_hist(
            symbol="000001",
            period="daily",
            start_date="20200101",
            end_date="20231027",
            adjust="hfq"
        )

        print(f"Current API Success!")
        print(f"Data shape: {stock_zh_a_hist.shape}")
        print(f"Columns: {list(stock_zh_a_hist.columns)}")
        print(f"Data types:\n{stock_zh_a_hist.dtypes}")
        print(f"First few rows:")
        print(stock_zh_a_hist.head())
        print(f"Last few rows:")
        print(stock_zh_a_hist.tail())

        return stock_zh_a_hist

    except Exception as e:
        print(f"Current API failed: {str(e)}")
        return None

def compare_apis():
    """比较新旧API的数据结构"""
    new_data = test_new_api()
    old_data = test_old_api()

    if new_data is not None and old_data is not None:
        print("\n" + "="*50)
        print("COMPARISON ANALYSIS")
        print("="*50)

        print("Column names comparison:")
        print(f"New API columns: {list(new_data.columns)}")
        print(f"Old API columns: {list(old_data.columns)}")

        # 检查数据格式的差异
        print("\nData format differences:")
        for col in old_data.columns:
            if col not in new_data.columns:
                print(f"Missing in new API: {col}")

        for col in new_data.columns:
            if col not in old_data.columns:
                print(f"New in new API: {col}")

        # 检查数据样本
        print("\nSample data comparison (first row):")
        print("New API sample:")
        print(new_data.iloc[0].to_dict())
        print("\nOld API sample:")
        print(old_data.iloc[0].to_dict())

if __name__ == "__main__":
    compare_apis()