"""
简化版API测试脚本
测试北交所股票和CDR股票的API调用
"""
import akshare as ak
import pandas as pd
from datetime import datetime

def test_bj_api():
    """测试北交所股票API"""
    print("=== 测试北交所股票API ===")

    # 测试920985这只股票
    try:
        print("正在测试股票 920985...")
        df = ak.stock_zh_a_daily(
            symbol="bj920985",
            start_date="20251101",
            end_date="20251130",
            adjust="hfq"
        )

        if df is not None and not df.empty:
            print(f"[SUCCESS] 成功获取 {len(df)} 条记录")
            print(f"时间范围: {df.index.min()} 到 {df.index.max()}")
            print(f"最新价格: {df['close'].iloc[-1]:.2f}")
            print(f"成交量: {df['volume'].iloc[-1]:,}")
            print(f"数据列: {list(df.columns)}")
            print("前3条数据:")
            print(df.head(3))
            return True
        else:
            print("[FAILED] 无数据返回")
            return False

    except Exception as e:
        print(f"[ERROR] API调用失败: {e}")
        return False

def test_cdr_api():
    """测试CDR股票API"""
    print("\n=== 测试CDR股票API ===")

    # 测试689009这只股票
    try:
        print("正在测试股票 689009...")
        df = ak.stock_zh_a_cdr_daily(
            symbol="sh689009",
            start_date="20251101",
            end_date="20251130"
        )

        if df is not None and not df.empty:
            print(f"[SUCCESS] 成功获取 {len(df)} 条记录")
            print(f"时间范围: {df.index.min()} 到 {df.index.max()}")
            print(f"最新价格: {df['close'].iloc[-1]:.2f}")
            print(f"成交量: {df['volume'].iloc[-1]:,}")
            print(f"数据列: {list(df.columns)}")
            print("前3条数据:")
            print(df.head(3))
            return True
        else:
            print("[FAILED] 无数据返回")
            return False

    except Exception as e:
        print(f"[ERROR] API调用失败: {e}")
        return False

def test_normal_stock():
    """测试普通A股API作为对比"""
    print("\n=== 测试普通A股API ===")

    # 测试一只普通的A股
    try:
        print("正在测试股票 000001...")
        df = ak.stock_zh_a_daily(
            symbol="000001",
            start_date="20251101",
            end_date="20251130",
            adjust="hfq"
        )

        if df is not None and not df.empty:
            print(f"[SUCCESS] 成功获取 {len(df)} 条记录")
            print(f"时间范围: {df.index.min()} 到 {df.index.max()}")
            print(f"最新价格: {df['close'].iloc[-1]:.2f}")
            print(f"成交量: {df['volume'].iloc[-1]:,}")
            print(f"数据列: {list(df.columns)}")
            return True
        else:
            print("[FAILED] 无数据返回")
            return False

    except Exception as e:
        print(f"[ERROR] API调用失败: {e}")
        return False

def test_stock_list():
    """测试获取股票列表"""
    print("\n=== 测试获取股票列表 ===")

    try:
        print("正在获取A股股票列表...")
        stock_info = ak.stock_info_a_code_name()
        print(f"[SUCCESS] 成功获取 {len(stock_info)} 只股票")

        # 统计不同前缀的股票数量
        bj_stocks = stock_info[stock_info['code'].str.startswith('920')]
        cdr_stocks = stock_info[stock_info['code'].str.startswith('689')]

        print(f"北交所股票(920xxx): {len(bj_stocks)} 只")
        print(f"CDR股票(689xxx): {len(cdr_stocks)} 只")

        # 显示前5只北交所股票
        if len(bj_stocks) > 0:
            print("前5只北交所股票:")
            print(bj_stocks.head(5)[['code', 'name']].to_string(index=False))

        # 显示前5只CDR股票
        if len(cdr_stocks) > 0:
            print("前5只CDR股票:")
            print(cdr_stocks.head(5)[['code', 'name']].to_string(index=False))

        return True

    except Exception as e:
        print(f"[ERROR] 获取股票列表失败: {e}")
        return False

def main():
    """主测试函数"""
    print("简化版API测试工具")
    print("="*50)
    print("测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*50)

    results = {
        'stock_list': False,
        'normal_stock': False,
        'bj_stock': False,
        'cdr_stock': False
    }

    # 运行测试
    try:
        print("1. 测试股票列表获取...")
        results['stock_list'] = test_stock_list()

        print("\n2. 测试普通A股API...")
        results['normal_stock'] = test_normal_stock()

        print("\n3. 测试北交所股票API...")
        results['bj_stock'] = test_bj_api()

        print("\n4. 测试CDR股票API...")
        results['cdr_stock'] = test_cdr_api()

    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")

    # 输出测试总结
    print("\n" + "="*50)
    print("测试结果总结")
    print("="*50)
    print(f"股票列表获取: {'[PASS]' if results['stock_list'] else '[FAIL]'}")
    print(f"普通A股API: {'[PASS]' if results['normal_stock'] else '[FAIL]'}")
    print(f"北交所股票API: {'[PASS]' if results['bj_stock'] else '[FAIL]'}")
    print(f"CDR股票API: {'[PASS]' if results['cdr_stock'] else '[FAIL]'}")

    success_count = sum(results.values())
    total_count = len(results)
    print(f"\n总体通过率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

    if results['bj_stock'] and results['cdr_stock']:
        print("\n[RECOMMENDATION] API测试通过，可以运行数据收集脚本")
    else:
        print("\n[RECOMMENDATION] 部分API测试失败，建议检查网络和akshare版本")

    # 保存测试报告
    report_file = f"simple_api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("简化版API测试报告\n")
        f.write("="*50 + "\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("测试结果:\n")
        f.write(f"股票列表获取: {'PASS' if results['stock_list'] else 'FAIL'}\n")
        f.write(f"普通A股API: {'PASS' if results['normal_stock'] else 'FAIL'}\n")
        f.write(f"北交所股票API: {'PASS' if results['bj_stock'] else 'FAIL'}\n")
        f.write(f"CDR股票API: {'PASS' if results['cdr_stock'] else 'FAIL'}\n")
        f.write(f"总体通过率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)\n")

    print(f"\n详细报告已保存到: {report_file}")

if __name__ == "__main__":
    main()