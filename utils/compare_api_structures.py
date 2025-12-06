"""
详细比较新旧API返回的数据结构
"""
import akshare as ak
import pandas as pd

def get_new_api_data():
    """获取新API数据"""
    try:
        data = ak.stock_zh_a_hist_tx(
            symbol="sz000001",
            start_date="20200101",
            end_date="20231027",
            adjust="hfq"
        )
        return data
    except Exception as e:
        print(f"New API failed: {e}")
        return None

def get_current_api_data():
    """获取当前API数据"""
    try:
        data = ak.stock_zh_a_hist(
            symbol="000001",
            period="daily",
            start_date="20200101",
            end_date="20231027",
            adjust="hfq"
        )
        return data
    except Exception as e:
        print(f"Current API failed: {e}")
        return None

def analyze_data_structure(data, api_name):
    """分析数据结构"""
    print(f"\n{api_name} API Data Structure:")
    print(f"Shape: {data.shape}")
    print(f"Columns: {list(data.columns)}")
    print(f"Data types:")
    for col in data.columns:
        print(f"  {col}: {data[col].dtype}")

    print(f"\nSample data (first 2 rows):")
    print(data.head(2))

    print(f"\nMissing values:")
    print(data.isnull().sum())

    # 检查日期格式
    if 'date' in data.columns or '日期' in data.columns:
        date_col = 'date' if 'date' in data.columns else '日期'
        print(f"\nDate range: {data[date_col].min()} to {data[date_col].max()}")

def compare_with_database_schema():
    """比较API数据与数据库schema的兼容性"""
    print("\n" + "="*60)
    print("DATABASE SCHEMA COMPATIBILITY ANALYSIS")
    print("="*60)

    # 从database.py中看到的列名映射
    database_columns = [
        'trade_date',  # 交易日期
        'open_price',  # 开盘价
        'high_price',  # 最高价
        'low_price',   # 最低价
        'close_price', # 收盘价
        'volume',      # 成交量
        'amount'       # 成交额
    ]

    new_api_data = get_new_api_data()

    if new_api_data is not None:
        print(f"\nNew API columns: {list(new_api_data.columns)}")
        print(f"Required database columns: {database_columns}")

        # 检查哪些列需要映射
        column_mapping_needed = {}
        for db_col in database_columns:
            if db_col not in new_api_data.columns:
                # 尝试找到对应的API列
                if 'trade_date' == db_col and 'date' in new_api_data.columns:
                    column_mapping_needed[db_col] = 'date'
                elif 'open_price' == db_col and 'open' in new_api_data.columns:
                    column_mapping_needed[db_col] = 'open'
                elif 'high_price' == db_col and 'high' in new_api_data.columns:
                    column_mapping_needed[db_col] = 'high'
                elif 'low_price' == db_col and 'low' in new_api_data.columns:
                    column_mapping_needed[db_col] = 'low'
                elif 'close_price' == db_col and 'close' in new_api_data.columns:
                    column_mapping_needed[db_col] = 'close'
                elif 'amount' == db_col and 'amount' in new_api_data.columns:
                    column_mapping_needed[db_col] = 'amount'
                elif 'volume' == db_col:  # 新API可能没有volume
                    print(f"WARNING: 'volume' column not found in new API!")

        print(f"\nRequired column mapping: {column_mapping_needed}")

        # 检查是否有缺失的列
        missing_columns = []
        for db_col in database_columns:
            if db_col not in new_api_data.columns and db_col not in column_mapping_needed:
                missing_columns.append(db_col)

        if missing_columns:
            print(f"WARNING: Missing columns in new API: {missing_columns}")
        else:
            print("✓ All required database columns can be mapped from new API")

        # 检查数据类型兼容性
        print(f"\nData type analysis:")
        for col in new_api_data.columns:
            print(f"  {col}: {new_api_data[col].dtype}")

        return column_mapping_needed, missing_columns
    else:
        return {}, []

def main():
    """主函数"""
    print("Comparing Akshare API Data Structures")
    print("="*60)

    # 分析新API
    new_data = get_new_api_data()
    if new_data is not None:
        analyze_data_structure(new_data, "NEW (stock_zh_a_hist_tx)")

    # 分析当前API（如果可用）
    current_data = get_current_api_data()
    if current_data is not None:
        analyze_data_structure(current_data, "CURRENT (stock_zh_a_hist)")

    # 比较与数据库schema的兼容性
    mapping, missing = compare_with_database_schema()

    if mapping:
        print(f"\n" + "="*60)
        print("SUMMARY OF CHANGES NEEDED")
        print("="*60)
        print(f"1. New API requires column mapping: {mapping}")
        print(f"2. Missing columns: {missing if missing else 'None'}")
        print(f"3. Stock code format: Must include market prefix (sz/sh)")
        print(f"4. Function name: stock_zh_a_hist_tx instead of stock_zh_a_hist")

if __name__ == "__main__":
    main()