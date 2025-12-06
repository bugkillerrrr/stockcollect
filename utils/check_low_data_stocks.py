"""
查找数据异常的股票代码
"""
import sqlite3
import pandas as pd
from datetime import datetime
import os

def find_problematic_stocks(db_path: str = "data/stock_data.db"):
    """查找数据异常的股票"""
    print("查找数据库中数据异常的股票")
    print("="*60)

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            # 获取所有股票的数据统计
            stock_stats = pd.read_sql("""
                SELECT
                    stock_code,
                    COUNT(*) as record_count,
                    MIN(trade_date) as earliest_date,
                    MAX(trade_date) as latest_date,
                    COUNT(DISTINCT trade_date) as trading_days
                FROM technical_data
                GROUP BY stock_code
                ORDER BY record_count ASC
            """, conn)

            print(f"数据库中共有 {len(stock_stats)} 只股票")
            print(f"总记录数: {stock_stats['record_count'].sum():,}")
            print(f"数据时间范围: {stock_stats['earliest_date'].min()} 到 {stock_stats['latest_date'].max()}")

            # 分类问题股票
            severe_lack = stock_stats[stock_stats['record_count'] < 10]
            low_data = stock_stats[(stock_stats['record_count'] >= 10) & (stock_stats['record_count'] < 50)]
            less_data = stock_stats[(stock_stats['record_count'] >= 50) & (stock_stats['record_count'] < 200)]

            print(f"\n=== 问题股票分类 ===")
            print(f"严重数据不足(<10条): {len(severe_lack)} 只")
            print(f"数据较少(10-49条): {len(low_data)} 只")
            print(f"数据偏少(50-199条): {len(less_data)} 只")

            # 详细列出严重问题的股票
            if len(severe_lack) > 0:
                print(f"\n=== 严重数据不足的股票 ({len(severe_lack)}只) ===")
                for _, row in severe_lack.iterrows():
                    print(f"  {row['stock_code']}: {row['record_count']} 条记录")
                    print(f"    时间范围: {row['earliest_date']} 到 {row['latest_date']}")
                    print(f"    交易日数: {row['trading_days']} 天")
                    print()

            # 列出数据较少的股票
            if len(low_data) > 0:
                print(f"\n=== 数据较少的股票 ({len(low_data)}只，前20只) ===")
                for _, row in low_data.head(20).iterrows():
                    print(f"  {row['stock_code']}: {row['record_count']} 条记录 ({row['earliest_date']} 到 {row['latest_date']})")

                if len(low_data) > 20:
                    print(f"  ... 还有 {len(low_data) - 20} 只未显示")

            # 统计正常数据的股票
            normal_stocks = stock_stats[stock_stats['record_count'] >= 200]
            print(f"\n=== 正常数据股票 ===")
            print(f"数据充足(≥200条): {len(normal_stocks)} 只")
            if len(normal_stocks) > 0:
                avg_records = normal_stocks['record_count'].mean()
                print(f"平均记录数: {avg_records:.0f} 条")
                print(f"最少记录: {normal_stocks['record_count'].min()} 条")
                print(f"最多记录: {normal_stocks['record_count'].max()} 条")

            # 生成报告文件
            report_file = f"problematic_stocks_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("数据异常股票报告\n")
                f.write("="*50 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"数据库路径: {db_path}\n")
                f.write(f"总股票数: {len(stock_stats)}\n")
                f.write(f"总记录数: {stock_stats['record_count'].sum():,}\n\n")

                f.write("问题股票统计:\n")
                f.write(f"1. 严重数据不足(<10条): {len(severe_lack)} 只\n")
                f.write(f"2. 数据较少(10-49条): {len(low_data)} 只\n")
                f.write(f"3. 数据偏少(50-199条): {len(less_data)} 只\n")
                f.write(f"4. 数据正常(≥200条): {len(normal_stocks)} 只\n\n")

                if len(severe_lack) > 0:
                    f.write("严重数据不足的股票代码:\n")
                    for _, row in severe_lack.iterrows():
                        f.write(f"{row['stock_code']}\t{row['record_count']}\t{row['earliest_date']}\t{row['latest_date']}\n")
                    f.write("\n")

                if len(low_data) > 0:
                    f.write("数据较少的股票代码:\n")
                    for _, row in low_data.iterrows():
                        f.write(f"{row['stock_code']}\t{row['record_count']}\t{row['earliest_date']}\t{row['latest_date']}\n")

                f.write("\n建议排查步骤:\n")
                f.write("1. 优先处理严重数据不足的股票\n")
                f.write("2. 检查股票代码是否正确\n")
                f.write("3. 检查这些股票是否最近上市\n")
                f.write("4. 重新获取历史数据\n")
                f.write("5. 检查API调用是否有限制\n")

            print(f"\n报告已保存到: {report_file}")

            # 返回需要重点关注的股票代码
            critical_stocks = severe_lack['stock_code'].tolist() + low_data['stock_code'].tolist()
            return critical_stocks[:50] if len(critical_stocks) > 50 else critical_stocks

    except Exception as e:
        print(f"检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """主函数"""
    problematic_stocks = find_problematic_stocks()

    if problematic_stocks:
        print(f"\n需要重点关注的股票代码 (共{len(problematic_stocks)}只):")
        print(" ".join(problematic_stocks))
        print(f"\n建议:")
        print("1. 检查这些股票代码是否正确")
        print("2. 确认这些股票是否正常交易")
        print("3. 重新获取这些股票的完整历史数据")
        print("4. 检查API调用限制和网络连接")
    else:
        print("\n未发现明显的数据异常股票")

if __name__ == "__main__":
    main()