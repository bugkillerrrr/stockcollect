"""
检查akshare中可用的股票历史数据获取函数
"""
import akshare as ak
import pandas as pd

def check_functions():
    """检查akshare中相关的函数"""
    # 获取所有akshare函数
    ak_functions = [func for func in dir(ak) if not func.startswith('_')]

    # 筛选可能相关的函数
    relevant_functions = []
    keywords = ['stock', 'hist', 'tx', 'df', 'zh', 'a']

    for func in ak_functions:
        func_lower = func.lower()
        if any(keyword in func_lower for keyword in keywords):
            relevant_functions.append(func)

    print("Available akshare functions containing stock/hist/tx/df/zh/a:")
    for func in sorted(relevant_functions):
        print(f"  {func}")

    # 专门搜索可能的新函数
    tx_functions = [func for func in ak_functions if 'tx' in func.lower()]
    print(f"\nFunctions containing 'tx': {tx_functions}")

    hist_functions = [func for func in ak_functions if 'hist' in func.lower()]
    print(f"\nFunctions containing 'hist': {hist_functions}")

if __name__ == "__main__":
    check_functions()