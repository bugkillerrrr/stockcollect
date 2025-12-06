#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成数据报告
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

def generate_data_report():
    """生成数据报告"""
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print("=== 生成数据报告 ===")

    # 连接数据库
    db_path = "data/stock_data.db"
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            # 获取数据库信息
            info = {}

            # 各表记录数
            tables = ['stock_master', 'technical_data', 'technical_indicators', 'financial_data']
            for table in tables:
                try:
                    result = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn)
                    info[f"{table}_count"] = result.iloc[0]['count']
                except:
                    info[f"{table}_count"] = 0

            # 股票数量
            stock_count = pd.read_sql("""
                SELECT COUNT(DISTINCT stock_code) as stock_count
                FROM technical_data
            """, conn)
            info['stock_count'] = stock_count.iloc[0]['stock_count']

            # 数据时间范围
            date_range = pd.read_sql("""
                SELECT MIN(trade_date) as min_date, MAX(trade_date) as max_date
                FROM technical_data
            """, conn)
            info['data_start_date'] = date_range.iloc[0]['min_date']
            info['data_end_date'] = date_range.iloc[0]['max_date']

            # 数据库文件大小
            info['database_size_mb'] = round(os.path.getsize(db_path) / (1024 * 1024), 2)

            # 按市场统计
            market_stats = pd.read_sql("""
                SELECT
                    CASE
                        WHEN stock_code LIKE '000%' THEN '深交所主板'
                        WHEN stock_code LIKE '002%' THEN '深交所中小板'
                        WHEN stock_code LIKE '300%' THEN '创业板'
                        WHEN stock_code LIKE '600%' OR stock_code LIKE '601%' OR stock_code LIKE '603%' THEN '上交所主板'
                        WHEN stock_code LIKE '688%' THEN '科创板'
                        WHEN stock_code LIKE '920%' THEN '北交所'
                        ELSE '其他市场'
                    END as market,
                    COUNT(DISTINCT stock_code) as stock_count,
                    COUNT(*) as record_count
                FROM technical_data
                GROUP BY market
                ORDER BY stock_count DESC
            """, conn)

            # 生成报告文件
            report_file = f"data_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("股票数据库报告\n")
                f.write("="*50 + "\n")
                f.write(f"生成时间: {report_time}\n\n")

                f.write("数据库概览:\n")
                f.write(f"- 数据库大小: {info['database_size_mb']} MB\n")
                f.write(f"- 股票总数: {info['stock_count']} 只\n")
                f.write(f"- 技术数据记录: {info['technical_data_count']:,} 条\n")
                f.write(f"- 股票主数据: {info['stock_master_count']:,} 条\n")
                f.write(f"- 技术指标: {info['technical_indicators_count']:,} 条\n")
                f.write(f"- 财务数据: {info['financial_data_count']:,} 条\n\n")

                if info['data_start_date'] and info['data_end_date']:
                    f.write("数据时间范围:\n")
                    f.write(f"- 开始日期: {info['data_start_date']}\n")
                    f.write(f"- 结束日期: {info['data_end_date']}\n\n")

                f.write("按市场分布:\n")
                f.write("-"*40 + "\n")
                for _, row in market_stats.iterrows():
                    f.write(f"{row['market']:<12}: {row['stock_count']:4d} 只股票, {row['record_count']:8d} 条记录\n")

            print(f"报告已生成: {report_file}")
            return report_file

    except Exception as e:
        print(f"生成报告失败: {e}")
        return None

if __name__ == "__main__":
    generate_data_report()
