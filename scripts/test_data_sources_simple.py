#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的数据源测试
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_akshare_simple():
    """测试Akshare"""
    import akshare as ak

    print("测试Akshare (当前使用):")
    print("-" * 40)

    test_stocks = ['600000', '000001']

    total_success = 0
    total_time = 0

    for i, stock in enumerate(test_stocks, 1):
        try:
            start_time = time.time()
            data = ak.stock_zh_a_hist(
                symbol=stock,
                period="daily",
                start_date="20251101",
                end_date="20251110",
                adjust="hfq"
            )

            elapsed_time = time.time() - start_time
            total_time += elapsed_time

            if data is not None and len(data) > 0:
                total_success += 1
                print(f"  [{i}/{len(test_stocks)}] {stock}: 成功 {len(data)} 条记录, 耗时 {elapsed_time:.2f} 秒")
            else:
                print(f"  [{i}/{len(test_stocks)}] {stock}: 失败, 耗时 {elapsed_time:.2f} 秒")

        except Exception as e:
            print(f"  [{i}/{len(test_stocks)}] {stock}: 异常 {str(e)}")

    success_rate = total_success / len(test_stocks)
    avg_time = total_time / len(test_stocks)

    print("-" * 40)
    print(f"总成功率: {success_rate:.1%}")
    print(f"平均耗时: {avg_time:.2f} 秒/股")
    print(f"总耗时: {total_time:.2f} 秒")

def test_tushare_simple():
    """测试Tushare"""
    try:
        import tushare as ts

        print("测试Tushare:")
        print("-" * 40)

        test_stocks = ['600000', '000001']

        total_success = 0
        total_time = 0

        for i, stock in enumerate(test_stocks, 1):
            try:
                start_time = time.time()
                data = ts.get_hist_data(
                    code=stock,
                    start_date='20251101',
                    end_date='20251110'
                )

                elapsed_time = time.time() - start_time
                total_time += elapsed_time

                if data is not None and len(data) > 0:
                    total_success += 1
                    print(f"  [{i}/{len(test_stocks)}] {stock}: 成功 {len(data)} 条记录, 耗时 {elapsed_time:.2f} 秒")
                else:
                    print(f"  [{i}/{len(test_stocks)}] {stock}: 失败, 耗时 {elapsed_time:.2f} 秒")

            except Exception as e:
                print(f"  [{i}/{len(test_stocks)}] {stock}: 异常 {str(e)}")

        success_rate = total_success / len(test_stocks)
        avg_time = total_time / len(test_stocks)

        print("-" * 40)
        print(f"总成功率: {success_rate:.1%}")
        print(f"平均耗时: {avg_time:.2f} 秒/股")
        print(f"总耗时: {total_time:.2f} 秒")

        return success_rate, avg_time

    return success_rate, avg_time

def main():
    print("数据源对比测试")
    print("=" * 50)

    # 测试Akshare
    print("1. 测试当前Akshare (后复权):")
    test_akshare_simple()

    print("\\n2. 测试Tushare (需要token):")
    try:
        ts_success_rate, ts_avg_time = test_tushare_simple()
        print(f"Tushare成功率: {ts_success_rate:.1%}, 平均耗时: {ts_avg_time:.2f} 秒/股")
    except Exception as e:
        print(f"Tushare测试失败: {str(e)}")

    print("\\n3. 建议:")
    print("如果Akshare不稳定，可以考虑:")
    print("- 使用Tushare (需要申请token)")
    print("- 使用Baostock等更稳定的数据源")
    print("- 等待Akshare服务恢复后再继续")

if __name__ == "__main__":
    main()