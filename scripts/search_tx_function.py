"""
搜索akshare中包含tx的股票历史数据函数
"""
import akshare as ak

def search_tx_functions():
    """搜索tx相关的函数"""
    # 获取所有函数
    all_functions = dir(ak)

    # 搜索包含tx的函数
    tx_functions = [func for func in all_functions if 'tx' in func.lower()]

    print("Functions containing 'tx':")
    for func in tx_functions:
        print(f"  {func}")

    # 尝试检查文档字符串（如果有的话）
    stock_tx_functions = [func for func in tx_functions if 'stock' in func.lower() and 'hist' in func.lower()]
    print(f"\nStock history functions containing 'tx': {stock_tx_functions}")

    # 尝试可能的函数名变体
    possible_names = [
        'stock_zh_a_hist_tx',
        'stock_zh_a_hist_tx_df',
        'stock_zh_hist_tx',
        'stock_hist_tx',
        'stock_zh_a_tx_hist'
    ]

    print(f"\nTesting possible function names:")
    for name in possible_names:
        if hasattr(ak, name):
            print(f"  ✓ {name} - exists")
            try:
                func = getattr(ak, name)
                print(f"    Function: {func}")
                if hasattr(func, '__doc__') and func.__doc__:
                    print(f"    Doc: {func.__doc__[:200]}...")
            except Exception as e:
                print(f"    Error getting doc: {e}")
        else:
            print(f"  ✗ {name} - not found")

if __name__ == "__main__":
    search_tx_functions()