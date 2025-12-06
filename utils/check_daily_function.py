"""
检查stock_zh_a_daily函数的正确用法
"""
import akshare as ak

def check_function_info():
    """检查函数信息"""
    try:
        # 尝试检查函数文档
        func = ak.stock_zh_a_daily
        if hasattr(func, '__doc__') and func.__doc__:
            print("Function documentation:")
            print(func.__doc__)
        else:
            print("No documentation available")

        # 检查函数签名
        import inspect
        sig = inspect.signature(func)
        print(f"\nFunction signature: {sig}")

        # 查看函数位置
        print(f"\nFunction module: {func.__module__}")

    except Exception as e:
        print(f"Error checking function info: {e}")

def test_simple_call():
    """测试简单调用"""
    print("\nTesting simple call:")

    # 尝试不同的调用方式
    test_calls = [
        # 无参数
        lambda: ak.stock_zh_a_daily(),
        # 只带symbol
        lambda: ak.stock_zh_a_daily(symbol="000001"),
        # 带symbol和日期
        lambda: ak.stock_zh_a_daily(symbol="000001", start_date="20200101", end_date="20200131"),
        # 带所有参数
        lambda: ak.stock_zh_a_daily(symbol="000001", start_date="20200101", end_date="20200131", adjust="hfq"),
    ]

    for i, call_func in enumerate(test_calls):
        print(f"\nTest call {i+1}:")
        try:
            data = call_func()
            if data is not None and len(data) > 0:
                print(f"Success! Shape: {data.shape}")
                print(f"Columns: {list(data.columns)}")
                print(f"First row:")
                print(data.iloc[0])
                break
            else:
                print("No data returned")
        except Exception as e:
            print(f"Failed: {str(e)}")

if __name__ == "__main__":
    check_function_info()
    test_simple_call()