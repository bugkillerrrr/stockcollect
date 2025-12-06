#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新股票列表
检查是否有新增的股票代码
"""

import akshare as ak
import sqlite3
import pandas as pd
from datetime import datetime

def update_stock_list():
    """更新股票列表"""
    print("=== 更新股票列表 ===")

    try:
        # 获取最新股票列表
        print("正在获取最新股票列表...")
        stock_info = ak.stock_info_a_code_name()
        current_stocks = set(stock_info['code'].tolist())
        print(f"当前API股票总数: {len(current_stocks)}")

        # 从数据库获取已有股票
        db_path = "data/stock_data.db"
        if not os.path.exists(db_path):
            print("数据库不存在，跳过更新")
            return

        with sqlite3.connect(db_path) as conn:
            db_stocks_df = pd.read_sql("SELECT DISTINCT stock_code FROM technical_data", conn)
            db_stocks = set(db_stocks_df['stock_code'].tolist())

        print(f"数据库现有股票: {len(db_stocks)}")

        # 找出新增股票
        new_stocks = current_stocks - db_stocks
        if new_stocks:
            print(f"发现 {len(new_stocks)} 只新增股票:")
            for code in sorted(list(new_stocks))[:10]:
                print(f"  - {code}")
            if len(new_stocks) > 10:
                print(f"  ... 还有 {len(new_stocks) - 10} 只")

            # 保存新增股票列表
            with open("new_stocks.txt", "w", encoding="utf-8") as f:
                for code in sorted(new_stocks):
                    f.write(f"{code}\n")

            print("新增股票列表已保存到: new_stocks.txt")
            return True
        else:
            print("未发现新增股票")
            return False

    except Exception as e:
        print(f"更新股票列表失败: {e}")
        return False

if __name__ == "__main__":
    import os
    update_stock_list()
