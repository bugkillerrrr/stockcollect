#!/usr/bin/env python3
"""
测试新的数据获取规则
验证不同类型股票的数据获取是否正常工作
"""

import sys
import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from data_collector_new import AkshareDataCollectorNew
    from database_new import StockDataNewDB
    from logger import get_logger
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的环境中运行，并且所有依赖包已安装")
    sys.exit(1)

def test_stock_types():
    """测试不同类型股票的数据获取"""
    logger = get_logger()

    # 创建新的数据库和收集器
    db = StockDataNewDB()
    collector = AkshareDataCollectorNew(
        db=db,
        request_interval=1.0,
        max_retries=2,
        adjustment_type='hfq',
        api_method='stock_zh_a_daily'
    )

    # 测试用例：不同类型的股票
    test_cases = [
        # 规则1：沪深A股
        {'code': '000001', 'type': '深圳A股(平安银行)', 'expected_symbol': 'sz000001'},
        {'code': '000002', 'type': '深圳A股(万科A)', 'expected_symbol': 'sz000002'},
        {'code': '600000', 'type': '上海A股(浦发银行)', 'expected_symbol': 'sh600000'},
        {'code': '600036', 'type': '上海A股(招商银行)', 'expected_symbol': 'sh600036'},
        {'code': '300001', 'type': '创业板(特锐德)', 'expected_symbol': 'sz300001'},

        # 规则2：北交所股票
        {'code': '430002', 'type': '北交所(中科软)', 'expected_symbol': 'bj430002'},
        {'code': '430005', 'type': '北交所(原子高科)', 'expected_symbol': 'bj430005'},

        # 规则3：特殊CDR股票
        {'code': '689009', 'type': 'CDR特殊股票(九号公司)', 'expected_symbol': 'sh689009', 'special_api': True},
    ]

    print("=" * 80)
    print("测试新的股票数据获取规则")
    print("=" * 80)

    # 设置测试时间范围（最近5个交易日）
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")

    print(f"测试时间范围: {start_date} - {end_date}")
    print(f"复权类型: {collector.adjustment_type}")
    print(f"API方法: {collector.api_method}")
    print("=" * 80)

    success_count = 0
    total_count = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        stock_code = test_case['code']
        stock_type = test_case['type']
        expected_symbol = test_case['expected_symbol']
        is_special = test_case.get('special_api', False)

        print(f"\n[{i}/{total_count}] 测试 {stock_type}")
        print(f"股票代码: {stock_code}")
        print(f"期望symbol: {expected_symbol}")
        print(f"特殊接口: {'是' if is_special else '否'}")
        print("-" * 60)

        try:
            # 测试数据获取
            if is_special:
                # 对于689009，应该使用CDR接口
                success = collector.get_and_save_single_stock(
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    adjustment_type=None,  # CDR接口不支持adjust参数
                    api_method='stock_zh_a_cdr_daily'  # 强制使用CDR接口
                )
            else:
                # 其他股票使用标准接口
                success = collector.get_and_save_single_stock(
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date
                )

            if success:
                success_count += 1
                print(f"✓ {stock_code} 测试成功")

                # 验证数据是否正确保存
                record_count = db.get_stock_data_count(stock_code)
                print(f"✓ 数据库记录数: {record_count}")

            else:
                print(f"✗ {stock_code} 测试失败")

        except Exception as e:
            print(f"✗ {stock_code} 测试异常: {e}")
            logger.error(f"测试股票异常: {stock_code}", e)

    # 统计结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    print(f"总测试数量: {total_count}")
    print(f"成功数量: {success_count}")
    print(f"失败数量: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")

    # 数据库统计
    print("\n数据库统计:")
    try:
        stats = db.get_database_info()
        print(f"技术数据记录: {stats.get('new_technical_data_records', 0)}")
        print(f"有数据的股票: {len(db.get_stock_codes())}")

        # 显示按复权类型和API方法的汇总
        adjustment_summary = db.get_adjustment_summary()
        if not adjustment_summary.empty:
            print("\n数据收集方式汇总:")
            for _, row in adjustment_summary.iterrows():
                print(f"  {row['adjustment_type']} ({row['api_method']}): "
                      f"{row['record_count']} 条记录, {row['stock_count']} 只股票")
    except Exception as e:
        print(f"获取数据库统计失败: {e}")

    print("\n" + "=" * 80)

    if success_count == total_count:
        print("🎉 所有测试通过！新的数据获取规则工作正常。")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关股票的接口配置。")
        return False

def test_api_methods():
    """测试不同的API方法"""
    print("\n" + "=" * 80)
    print("测试不同API方法的兼容性")
    print("=" * 80)

    db = StockDataNewDB()
    collector = AkshareDataCollectorNew(db=db)

    # 测试不同API方法
    test_results = collector.test_api_methods(
        stock_code="000001",
        start_date="20241201",
        end_date="20241205"
    )

    print("\nAPI方法测试结果:")
    for key, result in test_results.items():
        if result.get('success', False):
            print(f"✓ {key}: 成功")
            if 'shape' in result:
                print(f"   数据形状: {result['shape']}")
        else:
            print(f"✗ {key}: 失败")
            if 'error' in result:
                print(f"   错误: {result['error']}")

def main():
    """主函数"""
    print("开始测试新的股票数据获取规则...")

    try:
        # 测试不同类型股票
        success = test_stock_types()

        # 测试API方法
        test_api_methods()

        print("\n测试完成！")

        if success:
            print("✅ 新规则实现正确，可以开始完整数据收集。")
            print("\n使用方法:")
            print("  python collect_full_data_new.py --mode 1  # 测试模式")
            print("  python collect_full_data_new.py --mode 4  # 完整模式")
            print("  python collect_full_data_new.py --adjustment qfq  # 前复权")
            print("  python collect_full_data_new.py --api stock_zh_a_hist  # 备选API")
        else:
            print("❌ 需要修复问题后再进行完整数据收集。")

    except Exception as e:
        print(f"测试过程中出现错误: {e}")

if __name__ == "__main__":
    main()