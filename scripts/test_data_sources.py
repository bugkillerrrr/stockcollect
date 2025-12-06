#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源对比测试脚本
对比akshare, tushare, baostock等不同数据源的稳定性
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_akshare():
    """测试akshare数据源"""
    print("🔍 测试Akshare数据源")
    print("=" * 50)

    try:
        import akshare as ak

        # 测试几个有代表性的股票
        test_stocks = ['600000', '000001', '300015', '002415']

        total_success = 0
        total_time = 0

        for i, stock in enumerate(test_stocks, 1):
            try:
                start_time = time.time()

                # 使用股票代码格式
                if stock.startswith('60'):
                    symbol = f"sh{stock}"
                elif stock.startswith('00') or stock.startswith('30'):
                    symbol = f"sz{stock}"
                else:
                    symbol = stock

                print(f"  [{i}/{len(test_stocks)}] 测试 {stock}...")

                # 获取后复权数据
                data = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date="20250101",
                    end_date="20251129",
                    adjust="hfq"
                )

                elapsed_time = time.time() - start_time
                total_time += elapsed_time

                if data is not None and len(data) > 0:
                    total_success += 1
                    print(f"     ✅ 成功: {len(data)} 条记录, 耗时: {elapsed_time:.2f}秒")
                    print(f"     最新价格: 开盘={data.iloc[-1]['开盘']:.2f}, 收盘={data.iloc[-1]['收盘']:.2f}")
                else:
                    print(f"     ❌ 失败: 耗时: {elapsed_time:.2f}秒")

            except Exception as e:
                print(f"     ❌ 异常: {str(e)}")

            # 请求间隔，避免被封
            if i < len(test_stocks):
                wait_time = 3 + i * 0.5  # 递增延迟
                print(f"     等待 {wait_time:.1f} 秒...")
                time.sleep(wait_time)

        success_rate = total_success / len(test_stocks)
        avg_time = total_time / len(test_stocks)

        print(f"\\n📊 Akshare测试结果:")
        print(f"  成功率: {success_rate:.1%} ({total_success}/{len(test_stocks)})")
        print(f"  平均耗时: {avg_time:.2f} 秒/股")
        print(f"  总耗时: {total_time:.2f} 秒")

    except Exception as e:
        print(f"❌ Akshare测试失败: {str(e)}")

    return success_rate

def test_tushare():
    """测试tushare数据源"""
    print("\\n🔍 测试Tushare数据源")
    print("=" * 50)

    try:
        import tushare as ts

        # 设置token（如果需要）
        # ts.set_token('your_token_here')

        test_stocks = ['600000', '000001', '300015', '002415']

        total_success = 0
        total_time = 0

        for i, stock in enumerate(test_stocks, 1):
            try:
                start_time = time.time()

                # 测试获取历史数据
                data = ts.get_hist_data(
                    stock,
                    start_date='20250101',
                    end_date='20251129'
                )

                elapsed_time = time.time() - start_time
                total_time += elapsed_time

                if data is not None and len(data) > 0:
                    total_success += 1
                    print(f"  [{i}/{len(test_stocks)}] 测试 {stock}...")
                    print(f"     ✅ 成功: {len(data)} 条记录, 耗时: {elapsed_time:.2f} 秒")
                    print(f"     最新价格: 开盘={data.iloc[-1]['open']:.2f}, 收盘={data.iloc[-1]['close']:.2f}")
                else:
                    print(f"     ❌ 失败: 耗时: {elapsed_time:.2f} 秒")

            except Exception as e:
                print(f"     ❌ 异常: {str(e)}")

            # 请求间隔，tushare通常更稳定
            if i < len(test_stocks):
                wait_time = 1  # tushare间隔可以更短
                print(f"     等待 {wait_time} 秒...")
                time.sleep(wait_time)

        success_rate = total_success / len(test_stocks)
        avg_time = total_time / len(test_stocks)

        print(f"\\n📊 Tushare测试结果:")
        print(f"  成功率: {success_rate:.1%} ({total_success}/{len(test_stocks)})")
        print(f"  平均耗时: {avg_time:.2f} 秒/股")
        print(f"  总耗时: {total_time:.2f} 秒")

    except Exception as e:
        print(f"❌ Tushare测试失败: {str(e)}")

    return success_rate

def test_baostock():
    """测试baostock数据源"""
    print("\\n🔍 测试Baostock数据源")
    print("=" * 50)

    try:
        import baostock as bs

        test_stocks = ['600000', '000001', '300015', '002415']

        total_success = 0
        total_time = 0

        for i, stock in enumerate(test_stocks, 1):
            try:
                start_time = time.time()

                # 测试获取历史数据
                data = bs.query_history_daily(
                    stock,
                    start_date='20250101',
                    end_date='20251129'
                )

                elapsed_time = time.time() - start_time
                total_time += elapsed_time

                if data is not None and len(data) > 0:
                    total_success += 1
                    print(f"  [{i}/{len(test_stocks)}] 测试 {stock}...")
                    print(f"     ✅ 成功: {len(data)} 条记录, 耗时: {elapsed_time:.2f} 秒")
                    print(f"     最新价格: 开盘={data.iloc[-1]['open']:.2f}, 收盘={data.iloc[-1]['close']:.2f}")
                else:
                    print(f"     ❌ 失败: 耗时: {elapsed_time:.2f} 秒")

            except Exception as e:
                print(f"     ❌ 异常: {str(e)}")

            # 请求间隔
            if i < len(test_stocks):
                wait_time = 2
                print(f"     等待 {wait_time} 秒...")
                time.sleep(wait_time)

        success_rate = total_success / len(test_stocks)
        avg_time = total_time / len(test_stocks)

        print(f"\\n📊 Baostock测试结果:")
        print(f"  成功率: {success_rate:.1%} ({total_success}/{len(test_stocks)})")
        print(f"  平均耗时: {avg_time:.2f} 秒/股")
        print(f"  总耗时: {total_time:.2f} 秒")

    except Exception as e:
        print(f"❌ Baostock测试失败: {str(e)}")

    return success_rate

def main():
    """主函数"""
    print("🧪 数据源稳定性测试")
    print("=" * 60)
    print("测试不同数据源获取股票历史数据的稳定性")
    print("包括: Akshare, Tushare, Baostock")
    print()
    print("测试股票: 600000, 000001, 300015, 002415")
    print("测试时间: 2025年1月1日 - 2025年11月29日")
    print()

    results = {}

    # 测试Akshare
    print("\\n开始测试Akshare...")
    results['akshare'] = test_akshare()

    # 测试Tushare
    print("\\n开始测试Tushare...")
    results['tushare'] = test_tushare()

    # 测试Baostock
    print("\\n开始测试Baostock...")
    results['baostock'] = test_baostock()

    # 输出结果对比
    print("\\n" + "=" * 60)
    print("📊 测试结果对比")
    print("=" * 60)

    for source, success_rate in results.items():
        print(f"{source:10}: 成功率 {success_rate:.1%}")

    # 推荐
    print("\\n💡 建议:")
    best_source = max(results, key=results.get)
    print(f"  最稳定数据源: {best_source} (成功率 {results[best_source]:.1%})")

    if best_source == 'tushare':
        print("  建议使用Tushare作为主要数据源")
    elif best_source == 'akshare':
        print("  建议继续使用Akshare，但需要优化反爬虫策略")
    else:
        print(f"  建议使用{best_source}")

    print("\\n⚠️  注意:")
    print("   不同数据源可能有不同的数据格式和更新频率")
    print("  建议选择最稳定的数据源进行长期数据收集")

if __name__ == "__main__":
    main()