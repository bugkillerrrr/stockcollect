"""
测试北交所股票数据获取
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_collector import AkshareDataCollector
from database import StockDataDB

def test_bj_stocks():
    """测试北交所股票"""
    print("测试北交所股票数据获取")
    print("="*60)

    # 初始化
    collector = AkshareDataCollector(request_interval=1.0, max_retries=3)
    db = StockDataDB()

    # 测试北交所股票列表
    bj_test_stocks = [
        "920985",  # 你提供的例子
        "920002",  # 测试另一个北交所股票
        "920111",  # 第三个测试
    ]

    print(f"测试北交所股票: {bj_test_stocks}")

    for stock_code in bj_test_stocks:
        print(f"\n{'='*60}")
        print(f"正在测试 {stock_code}...")

        try:
            # 测试不同的日期范围
            data = collector.get_stock_data(stock_code, "20240101", "20240131")

            if data is not None and len(data) > 0:
                print(f"✓ 成功获取 {stock_code} 数据!")
                print(f"  数据形状: {data.shape}")
                print(f"   列名: {list(data.columns)}")

                # 检查关键字段
                key_fields = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
                missing_fields = [field for field in key_fields if field not in data.columns]
                if missing_fields:
                    print(f"  ⚠ 缺失字段: {missing_fields}")
                else:
                    print(f"  ✓ 所有关键字段完整")

                # 检查数据质量
                if len(data) > 0:
                    print(f"   日期范围: {data.iloc[0, 0]} 到 {data.iloc[-1, 0]}")
                    print(f"  成交量范围: {data['volume'].min():.0f} 到 {data['volume'].max():.0f}")
                    print(f"  成交额范围: {data['amount'].min():.0f} 到 {data['amount'].max():.0f}")

                    # 检查市场前缀是否正确
                    if stock_code.startswith('92'):
                        first_date = data.iloc[0, 0]
                        last_date = data.iloc[-1, 0]
                        print(f"  ✓ 北交所股票格式正确，数据完整性良好")

                        # 保存到数据库
                        saved_count = db.save_technical_data(stock_code, data)
                        print(f"  ✓ 保存到数据库: {saved_count} 条记录")

                        # 验证数据库保存
                        db_count = db.get_stock_data_count(stock_code)
                        print(f"  ✓ 数据库验证: {db_count} 条记录")
                    else:
                        print(f"  ⚠ 市场前缀可能不正确: {stock_code}")

            else:
                print(f"  ✗ 获取失败: {stock_code}")

        except Exception as e:
            print(f"  ✗ 测试异常: {str(e)}")

def check_existing_bj_data():
    """检查现有北交所数据"""
    print("\n" + "="*60)
    print("检查现有北交所数据")
    print("="*60)

    db = StockDataDB()

    try:
        with sqlite3.connect('data/stock_data.db') as conn:
            # 查询所有北交所股票
            bj_stocks = pd.read_sql("""
                SELECT DISTINCT stock_code
                FROM technical_data
                WHERE stock_code LIKE '92%'
                ORDER BY stock_code
            """, conn)

            if len(bj_stocks) > 0:
                print(f"找到 {len(bj_stocks)} 只北交所股票:")
                print(bj_stocks['stock_code'].tolist())

                # 查询每只股票的数据详情
                for stock_code in bj_stocks['stock_code'].head(10):
                    detail = pd.read_sql("""
                        SELECT
                            stock_code,
                            COUNT(*) as record_count,
                            MIN(trade_date) as earliest_date,
                            MAX(trade_date) as latest_date,
                            AVG(close_price) as avg_close,
                            MIN(close_price) as min_close,
                            MAX(close_price) as max_close
                        FROM technical_data
                        WHERE stock_code = ?
                    """, conn, params=[stock_code])

                    if len(detail) > 0:
                        print(f"\n{stock_code}:")
                        print(f"  记录数: {detail.iloc[0]['record_count']}")
                        print(f"  时间范围: {detail.iloc[0]['earliest_date']} 到 {detail.iloc[0]['latest_date']}")
                        print(f"  平均收盘价: {detail.iloc[0]['avg_close']:.2f}")
                        print(f"  价格区间: {detail.iloc[0]['min_close']:.2f} - {detail.iloc[0]['max_close']:.2f}")
                    else:
                        print(f"\n{stock_code}: 无数据")
            else:
                print("数据库中没有北交所股票数据!")

    except Exception as e:
        print(f"检查数据时出错: {str(e)}")

def test_bj_api_calls():
    """测试不同的北交所API调用方式"""
    print("\n" + "="*60)
    print("测试不同的北交所API调用方式")
    print("="*60)

    collector = AkshareDataCollector(request_interval=2.0, max_retries=2)
    test_stock = "920985"

    # 测试方法1: 直接使用股票代码
    print(f"\n1. 测试直接使用股票代码: {test_stock}")
    try:
        data1 = collector.get_stock_data(test_stock, "20240101", "20240131")
        if data1 is not None:
            print(f"   ✓ 成功! 数据形状: {data1.shape}")
        else:
            print(f"   ✗ 失败")
    except Exception as e:
        print(f"   ✗ 异常: {str(e)}")

    # 测试方法2: 使用bj前缀
    print(f"\n2. 测试使用bj前缀: bj{test_stock}")
    try:
        data2 = collector.get_stock_data(f"bj{test_stock}", "20240101", "20240131")
        if data2 is not None:
            print(f"   ✓ 成功! 数据形状: {data2.shape}")
        else:
            print(f"   ✗ 失败")
    except Exception as e:
        print(f"   ✗ 异常: {str(e)}")

    # 测试方法3: 检查API函数是否存在
    print(f"\n3. 检查API函数:")
    try:
        if hasattr(akshare, 'stock_zh_a_daily'):
            print("   ✓ ak.stock_zh_a_daily 存在")
        else:
            print("   ✗ ak.stock_zh_a_daily 不存在")

        # 检查其他可能的北交所API
        if hasattr(akshare, 'stock_zh_bj_daily'):
            print("   ✓ ak.stock_zh_bj_daily 存在")
        else:
            print("   ✗ ak.stock_zh_bj_daily 不存在")

    except Exception as e:
        print(f"   ✗ 检查异常: {str(e)}")

if __name__ == "__main__":
    print("北交所股票数据测试程序")
    print("="*60)
    print("1. 测试北交所股票数据获取")
    print("2. 检查现有北交所数据")
    print("3. 测试不同的API调用方式")
    print("="*60)

    # 运行测试
    test_bj_stocks()
    check_existing_bj_data()
    test_bj_api_calls()

    print("\n" + "="*60)
    print("测试完成!")
    print("根据测试结果，数据收集程序应该:")
    print("1. 使用 bj920985 格式调用 stock_zh_a_daily")
    print("2. 确保网络连接正常")
    print("3. 如果仍有问题，可能需要专门的北交所API")