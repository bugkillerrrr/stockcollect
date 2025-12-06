"""
测试缺失股票的API调用
验证北交所股票和CDR股票的数据获取功能
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def test_bj_stock():
    """测试北交所股票API"""
    print("测试北交所股票API (920xxx)")
    print("-" * 50)

    # 从缺失的北交所股票中选择几只进行测试
    test_stocks = ["920985", "920000", "920001", "920002", "920003"]

    for stock_code in test_stocks:
        print(f"\n测试股票: {stock_code}")
        try:
            # 测试北交所股票数据获取
            df = ak.stock_zh_a_daily(
                symbol=f"bj{stock_code}",
                start_date="20241101",  # 测试最近1个月的数据
                end_date="20251130",
                adjust="hfq"
            )

            if df is not None and not df.empty:
                print(f"  [OK] 成功获取 {len(df)} 条记录")
                print(f"    时间范围: {df.index.min()} 到 {df.index.max()}")
                print(f"    最新价格: {df['close'].iloc[-1]:.2f}")
                print(f"    成交量: {df['volume'].iloc[-1]:,}")

                # 显示前3条和后3条数据
                print(f"    样本数据:")
                print(f"    前3条: {df.head(3)['close'].values}")
                print(f"    后3条: {df.tail(3)['close'].values}")
            else:
                print(f"  ✗ 无数据返回")

        except Exception as e:
            print(f"  ✗ API调用失败: {e}")

def test_cdr_stock():
    """测试CDR股票API"""
    print("\n\n测试CDR股票API (689xxx)")
    print("-" * 50)

    # 测试689009股票
    stock_code = "689009"
    print(f"\n测试股票: {stock_code}")

    try:
        # 测试CDR股票数据获取
        df = ak.stock_zh_a_cdr_daily(
            symbol=f"sh{stock_code}",
            start_date="20241101",
            end_date="20251130"
        )

        if df is not None and not df.empty:
            print(f"  ✓ 成功获取 {len(df)} 条记录")
            print(f"    时间范围: {df.index.min()} 到 {df.index.max()}")
            print(f"    最新价格: {df['close'].iloc[-1]:.2f}")
            print(f"    成交量: {df['volume'].iloc[-1]:,}")

            # 显示前3条和后3条数据
            print(f"    样本数据:")
            print(f"    前3条: {df.head(3)['close'].values}")
            print(f"    后3条: {df.tail(3)['close'].values}")
        else:
            print(f"  ✗ 无数据返回")

    except Exception as e:
        print(f"  ✗ API调用失败: {e}")

def test_api_availability():
    """测试API基本可用性"""
    print("\n\n测试API基本可用性")
    print("-" * 50)

    try:
        # 测试akshare是否正常工作
        print("测试akshare库连接...")
        stock_info = ak.stock_info_a_code_name()
        print(f"  ✓ 成功获取股票列表，共 {len(stock_info)} 只股票")

        # 测试几只普通股票作为对比
        test_normal_stocks = ["000001", "000002", "600000"]
        print(f"\n测试普通A股数据获取...")

        for stock_code in test_normal_stocks[:2]:  # 只测试2只
            try:
                df = ak.stock_zh_a_daily(symbol=stock_code, start_date="20251101", end_date="20251130")
                if df is not None and not df.empty:
                    print(f"  ✓ {stock_code}: 成功获取 {len(df)} 条记录")
                else:
                    print(f"  ✗ {stock_code}: 无数据")
            except Exception as e:
                print(f"  ✗ {stock_code}: 获取失败 - {e}")

    except Exception as e:
        print(f"  ✗ akshare连接失败: {e}")

def generate_test_report():
    """生成测试报告"""
    print("\n\n" + "="*80)
    print("测试报告总结")
    print("="*80)

    report = f"""
测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

API测试结果:
1. akshare库连接: 需要运行测试确认
2. 北交所股票API: 需要运行测试确认
3. CDR股票API: 需要运行测试确认

建议:
- 如果北交所API工作正常，使用 stock_zh_a_daily(symbol="bj920xxx") 格式
- 如果CDR API工作正常，使用 stock_zh_a_cdr_daily(symbol="sh689xxx") 格式
- 注意API调用频率限制，适当添加延时
- 检查返回的数据格式和字段名称

下一步操作:
- 运行 collect_missing_stocks.py 开始数据收集
- 监控收集进度和错误日志
- 验证数据完整性
"""

    print(report)

    # 保存测试报告
    with open(f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w', encoding='utf-8') as f:
        f.write(report)

def main():
    """主函数"""
    print("缺失股票API测试工具")
    print("="*80)
    print("测试内容:")
    print("1. 北交所股票API (920xxx)")
    print("2. CDR股票API (689xxx)")
    print("3. akshare库基本功能")
    print("="*80)

    try:
        # 运行各项测试
        test_api_availability()
        test_bj_stock()
        test_cdr_stock()
        generate_test_report()

    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()