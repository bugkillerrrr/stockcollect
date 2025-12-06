"""
测试不同参数格式的tx函数
"""
import akshare as ak

def test_variations():
    """测试不同的参数格式"""
    symbol_variations = [
        "000001",
        "sz000001",
        "sh000001",
        "sz:000001"
    ]

    for symbol in symbol_variations:
        print(f"\nTesting with symbol: {symbol}")
        try:
            data = ak.stock_zh_a_hist_tx(
                symbol=symbol,
                start_date="20200101",
                end_date="20231027",
                adjust="hfq"
            )
            print(f"Success! Shape: {data.shape}")
            print(f"Columns: {list(data.columns)}")
            if len(data) > 0:
                print(f"Sample data:")
                print(data.head(2))
            return data
        except Exception as e:
            print(f"Failed: {str(e)}")

    # 尝试不同的参数名
    print(f"\nTrying different parameter names:")
    try:
        # 检查函数签名
        import inspect
        sig = inspect.signature(ak.stock_zh_a_hist_tx)
        print(f"Function signature: {sig}")
    except Exception as e:
        print(f"Cannot inspect function: {e}")

if __name__ == "__main__":
    test_variations()