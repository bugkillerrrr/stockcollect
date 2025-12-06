#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试北交所股票API调用
"""

import akshare as ak
import pandas as pd
from datetime import datetime

def test_bj_stock_api():
    """测试北交所股票API调用"""
    print("=== 测试北交所股票API调用 ===")

    # 测试几只北交所股票
    test_stocks = ['920000', '920001', '920002']

    for stock_code in test_stocks:
        print(f"\n测试股票: {stock_code}")

        try:
            # 北交所股票使用bj前缀
            symbol = f"bj{stock_code}"
            print(f"调用符号: {symbol}")

            # 获取最近几个月的数据进行测试
            df = ak.stock_zh_a_daily(
                symbol=symbol,
                start_date="20241101",  # 测试最近2个月
                end_date="20251130",
                adjust="hfq"
            )

            if df is not None and not df.empty:
                print(f"  [成功] 获取 {len(df)} 条记录")
                print(f"  时间范围: {df.index.min()} 到 {df.index.max()}")
                print(f"  数据列: {list(df.columns)}")

                # 显示最新几条数据的基本信息
                if 'close' in df.columns:
                    latest_price = df['close'].iloc[-1]
                    print(f"  最新价格: {latest_price:.2f}")

                if 'volume' in df.columns:
                    latest_volume = df['volume'].iloc[-1]
                    print(f"  最新成交量: {latest_volume:,}")

                # 显示前3条数据
                print("  前3条数据样本:")
                print(df.head(3))

            else:
                print("  [失败] 未获取到数据")

        except Exception as e:
            print(f"  [错误] 调用失败: {e}")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_bj_stock_api()