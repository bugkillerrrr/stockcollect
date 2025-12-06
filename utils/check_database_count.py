#!/usr/bin/env python3
"""
检查数据库中股票数据数量
"""
import sqlite3
import pandas as pd
from pathlib import Path

def check_database_count():
    """检查数据库中的股票数据数量"""

    # 检查主数据库
    db_path = "data/stock_data.db"
    if Path(db_path).exists():
        print(f"正在检查数据库: {db_path}")
        print("=" * 60)

        try:
            with sqlite3.connect(db_path) as conn:
                # 获取总体信息
                info = pd.read_sql("""
                    SELECT
                        COUNT(DISTINCT stock_code) as stock_count,
                        COUNT(*) as total_records,
                        MIN(trade_date) as earliest_date,
                        MAX(trade_date) as latest_date
                    FROM technical_data
                """, conn)

                if len(info) > 0 and info.iloc[0]['stock_count'] > 0:
                    stock_count = info.iloc[0]['stock_count']
                    total_records = info.iloc[0]['total_records']
                    earliest_date = info.iloc[0]['earliest_date']
                    latest_date = info.iloc[0]['latest_date']

                    print(f"股票数量: {stock_count}")
                    print(f"总记录数: {total_records}")
                    print(f"数据时间范围: {earliest_date} 至 {latest_date}")

                    # 获取每个股票的记录数
                    stock_records = pd.read_sql("""
                        SELECT stock_code, COUNT(*) as record_count
                        FROM technical_data
                        GROUP BY stock_code
                        ORDER BY record_count DESC
                    """, conn)

                    print(f"\n每个股票的记录数（前20名）:")
                    print("-" * 40)
                    for _, row in stock_records.head(20).iterrows():
                        print(f"{row['stock_code']}: {row['record_count']} 条记录")

                    # 按记录数统计
                    record_stats = stock_records['record_count'].describe()
                    print(f"\n记录数统计:")
                    print("-" * 30)
                    print(f"平均记录数: {record_stats['mean']:.1f}")
                    print(f"最少记录数: {record_stats['min']}")
                    print(f"最多记录数: {record_stats['max']}")
                    print(f"中位数: {record_stats['50%']}")

                    # 记录数分布
                    less_100 = len(stock_records[stock_records['record_count'] < 100])
                    between_100_500 = len(stock_records[(stock_records['record_count'] >= 100) & (stock_records['record_count'] < 500)])
                    between_500_1000 = len(stock_records[(stock_records['record_count'] >= 500) & (stock_records['record_count'] < 1000)])
                    greater_1000 = len(stock_records[stock_records['record_count'] >= 1000])

                    print(f"\n记录数分布:")
                    print("-" * 30)
                    print(f"< 100条: {less_100} 只股票")
                    print(f"100-500条: {between_100_500} 只股票")
                    print(f"500-1000条: {between_500_1000} 只股票")
                    print(f">= 1000条: {greater_1000} 只股票")

                else:
                    print("数据库中没有找到技术数据")

        except Exception as e:
            print(f"查询数据库失败: {e}")
    else:
        print(f"数据库文件不存在: {db_path}")

    # 检查是否有新数据库
    new_db_path = "data/stock_data_new.db"
    if Path(new_db_path).exists():
        print(f"\n正在检查新数据库: {new_db_path}")
        print("=" * 60)

        try:
            with sqlite3.connect(new_db_path) as conn:
                info = pd.read_sql("""
                    SELECT
                        COUNT(DISTINCT stock_code) as stock_count,
                        COUNT(*) as total_records,
                        MIN(trade_date) as earliest_date,
                        MAX(trade_date) as latest_date
                    FROM technical_data
                """, conn)

                if len(info) > 0 and info.iloc[0]['stock_count'] > 0:
                    stock_count = info.iloc[0]['stock_count']
                    total_records = info.iloc[0]['total_records']
                    earliest_date = info.iloc[0]['earliest_date']
                    latest_date = info.iloc[0]['latest_date']

                    print(f"新数据库股票数量: {stock_count}")
                    print(f"新数据库总记录数: {total_records}")
                    print(f"新数据库时间范围: {earliest_date} 至 {latest_date}")
                else:
                    print("新数据库中没有找到技术数据")

        except Exception as e:
            print(f"查询新数据库失败: {e}")

if __name__ == "__main__":
    check_database_count()