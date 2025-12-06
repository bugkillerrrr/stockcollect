"""
检查数据库中数据为空的股票
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

def check_empty_data_stocks(db_path: str = "data/stock_data.db"):
    """检查哪些股票数据为空"""
    print("检查数据库中数据为空的股票")
    print("="*60)

    try:
        with sqlite3.connect(db_path) as conn:
            # 获取所有有记录的股票
            stocks_with_data = pd.read_sql("""
                SELECT DISTINCT stock_code,
                       COUNT(*) as record_count,
                       MAX(trade_date) as latest_date,
                       MIN(trade_date) as earliest_date,
                       MAX(created_at) as last_updated
                FROM technical_data
                GROUP BY stock_code
            """, conn)

            print(f"\n总共有 {len(stocks_with_data)} 只股票有数据记录")

            if len(stocks_with_data) == 0:
                print("数据库中没有股票数据！")
                return

            # 检查数据为空的股票
            empty_stocks = stocks_with_data[stocks_with_data['record_count'] == 0]['stock_code'].tolist()

            print(f"\n发现 {len(empty_stocks)} 只股票数据为空：")
            print("-"*40)

            if empty_stocks:
                print("股票代码列表：")
                for i, stock_code in enumerate(empty_stocks, 1):
                    print(f"  {i:2d}. {stock_code}")

                print("-"*40)

                # 按股票代码排序
                empty_stocks_sorted = sorted(empty_stocks)

                print(f"\n数据为空的股票（按代码排序）：")
                for stock_code in empty_stocks_sorted[:20]:  # 只显示前20只
                    print(f"  {stock_code}")

                if len(empty_stocks) > 20:
                    print(f"  ... 还有 {len(empty_stocks) - 20} 只未显示")

            print("-"*40)

            # 分析可能的原因
            print(f"\n可能的原因分析：")
            print(f"1. 总记录数: {stocks_with_data['record_count'].sum()}")
            print(f"2. 有数据的股票数: {len(stocks_with_data) - len(empty_stocks)}")
            print(f"3. 数据为空的股票数: {len(empty_stocks)}")
            print(f"4. 空数据比例: {len(empty_stocks) / len(stocks_with_data) * 100:.2f}%")

            # 检查数据更新时间
            print(f"\n数据更新时间分析：")

            # 获取最近一周的更新记录
            recent_updates = pd.read_sql("""
                SELECT stock_code, record_count, update_type, created_at
                FROM update_log
                WHERE created_at >= date('now', '-7 days')
                AND success = 0
                ORDER BY created_at DESC
                LIMIT 20
            """, conn)

            if len(recent_updates) > 0:
                print("最近一周的失败更新记录：")
                for _, row in recent_updates.iterrows():
                    print(f"  {row['created_at']}: {row['stock_code']} - {row['update_type']} - {row['record_count']} 条记录")

            # 获取最早和最晚的数据日期
            date_range = pd.read_sql("""
                SELECT
                    MIN(trade_date) as overall_min_date,
                    MAX(trade_date) as overall_max_date,
                    COUNT(DISTINCT stock_code) as total_stocks_with_data
                FROM technical_data
                WHERE stock_code IN ({placeholders})
            """.format(placeholders=','.join(['?' for _ in empty_stocks]),
                          params=empty_stocks), conn)

            if not date_range.empty:
                overall_min = date_range.iloc[0]['overall_min_date']
                overall_max = date_range.iloc[0]['overall_max_date']
                total_with_data = date_range.iloc[0]['total_stocks_with_data']

                print(f"\n数据时间范围：{overall_min} 到 {overall_max}")
                print(f"这 {len(empty_stocks)} 只股票共有 {total_with_data} 条记录")

            # 生成排查建议
            print(f"\n排查建议：")
            print("1. 检查这些股票是否真实存在或代码是否正确")
            print("2. 重新获取这些股票的完整数据")
            print("3. 检查API参数和网络连接")
            print("4. 检查是否有特殊股票代码需要特殊处理")

            # 输出到文件
            output_file = f"empty_stocks_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("数据为空的股票代码列表\n")
                f.write("="*50 + "\n")
                f.write(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"总股票数: {len(stocks_with_data)}\n")
                f.write(f"数据为空的股票数: {len(empty_stocks)}\n")
                f.write(f"空数据比例: {len(empty_stocks) / len(stocks_with_data) * 100:.2f}%\n\n")

                f.write("数据为空的股票代码：\n")
                for stock_code in empty_stocks_sorted:
                    f.write(f"{stock_code}\n")

                f.write("\n可能的原因：\n")
                f.write("1. API限制或网络问题\n")
                f.write("2. 股票代码错误或不存在\n")
                f.write("3. 特殊股票需要特殊处理\n")
                f.write("4. 数据保存失败\n")

            print(f"\n检查结果已保存到: {output_file}")
            return empty_stocks_sorted[:50] if len(empty_stocks) > 50 else empty_stocks_sorted

    except Exception as e:
        print(f"检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return []

def analyze_failure_patterns(db_path: str = "data/stock_data.db"):
    """分析失败模式"""
    print("\n分析失败模式")
    print("="*60)

    try:
        with sqlite3.connect(db_path) as conn:
            # 获取失败记录
            failure_analysis = pd.read_sql("""
                SELECT
                    stock_code,
                    COUNT(*) as failure_count,
                    update_type,
                    error_message,
                    created_at
                FROM update_log
                WHERE success = 0
                AND created_at >= date('now', '-7 days')
                GROUP BY stock_code, update_type
                ORDER BY failure_count DESC
                LIMIT 20
            """, conn)

            print(f"\n最近一周的失败记录（前20条）：")
            for _, row in failure_analysis.iterrows():
                print(f"  {row['created_at']}: {row['stock_code']} - {row['update_type']} - {row['failure_count']} 次 - {row['error_message']}")

            # 按错误类型统计
            error_summary = pd.read_sql("""
                SELECT
                    error_message,
                    COUNT(*) as count
                FROM update_log
                WHERE success = 0
                AND created_at >= date('now', '-7 days')
                GROUP BY error_message
                ORDER BY count DESC
            """, conn)

            print(f"\n错误类型统计：")
            for _, row in error_summary.iterrows():
                print(f"  {row['error_message']}: {row['count']} 次")

    except Exception as e:
        print(f"分析失败模式时出错: {e}")

def main():
    """主函数"""
    db_path = "data/stock_data.db"

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    print(f"数据库路径: {db_path}")
    print(f"数据库大小: {os.path.getsize(db_path) / (1024*1024):.2f} MB")

    # 检查数据为空的股票
    empty_stocks = check_empty_data_stocks(db_path)

    if empty_stocks:
        print(f"\n找到 {len(empty_stocks)} 只数据为空的股票，可以针对性排查")
        print("建议的排查步骤：")
        print("1. 检查股票代码是否正确")
        print("2. 手动测试API调用")
        print("3. 检查网络连接")
        print("4. 检查akshare库版本")
    else:
        print(f"\n所有股票都有数据，共检查了 {len(empty_stocks)} 只股票")

if __name__ == "__main__":
    main()