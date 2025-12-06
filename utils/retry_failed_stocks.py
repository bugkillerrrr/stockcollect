"""
重新获取之前失败的股票数据
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import StockDataDB
from data_collector import AkshareDataCollector

def get_failed_stocks():
    """获取之前获取失败的股票"""
    print("检查之前获取失败的股票")
    print("="*50)

    db = StockDataDB()
    collector = AkshareDataCollector()

    # 查询获取日志中的失败记录
    try:
        with sqlite3.connect(db.db_path) as conn:
            failed_stocks = pd.read_sql("""
                SELECT DISTINCT stock_code, COUNT(*) as failure_count
                FROM update_log
                WHERE success = 0
                AND update_type = '技术数据'
                AND created_at >= date('now', '-30 days')
                GROUP BY stock_code
                ORDER BY failure_count DESC
            """, conn)

            print(f"最近30天内获取失败的股票:")
            if len(failed_stocks) > 0:
                for _, row in failed_stocks.iterrows():
                    print(f"  {row['stock_code']}: {row['failure_count']} 次失败")

                return failed_stocks['stock_code'].tolist()
            else:
                print("  没有发现获取失败的记录")
                return []

    except Exception as e:
        print(f"查询失败记录时出错: {e}")
        return []

def retry_failed_stocks(failed_stocks):
    """重新获取失败股票的数据"""
    if not failed_stocks:
        print("没有需要重新获取的股票")
        return

    print(f"\n开始重新获取 {len(failed_stocks)} 只失败股票")
    print("="*50)

    db = StockDataDB()
    collector = AkshareDataCollector()

    # 设置时间范围（获取最近一年的数据）
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

    success_count = 0
    total_count = len(failed_stocks)

    for i, stock_code in enumerate(failed_stocks, 1):
        print(f"\n[{i}/{total_count}] 正在重新获取 {stock_code}...")

        try:
            # 删除已有的错误数据
            with sqlite3.connect(db.db_path) as conn:
                conn.execute("DELETE FROM technical_data WHERE stock_code = ?", (stock_code,))
                conn.commit()

            # 重新获取数据
            data = collector.get_stock_data(stock_code, start_date, end_date)

            if data is not None and len(data) > 0:
                # 保存数据
                saved_count = db.save_technical_data(stock_code, data)

                print(f"  ✓ 成功获取 {len(data)} 条记录")
                print(f"  ✓ 成功保存 {saved_count} 条记录")
                print(f"  ✓ 日期范围: {data.iloc[0, 0]} 到 {data.iloc[-1, 0]}")

                success_count += 1

                # 记录成功日志
                db.log_update(
                    update_type="技术数据重试",
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    records_count=len(data),
                    success=True
                )

            else:
                print(f"  ✗ 获取失败或无数据")

                # 记录失败日志
                db.log_update(
                    update_type="技术数据重试",
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    records_count=0,
                    success=False,
                    error_message="获取失败或无数据"
                )

        except Exception as e:
            print(f"  ✗ 处理 {stock_code} 时出错: {str(e)}")

            # 每处理完5只股票休息一下
            if i % 5 == 0:
                print(f"\n已处理 {i}/{total_count} 只股票，休息3秒...")
                import time
                time.sleep(3)

    print(f"\n" + "="*50)
    print(f"重新获取完成: {success_count}/{total_count} 成功")

def get_missing_data_stocks():
    """获取数据可能不完整的股票"""
    print("\n检查数据可能不完整的股票")
    print("="*50)

    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            # 检查最近更新但数据量很少的股票
            suspicious_stocks = pd.read_sql("""
                SELECT
                    td.stock_code,
                    COUNT(td.trade_date) as record_count,
                    MIN(td.trade_date) as earliest_date,
                    MAX(td.trade_date) as latest_date
                FROM technical_data td
                WHERE td.created_at >= date('now', '-7 days')
                GROUP BY td.stock_code
                HAVING COUNT(td.trade_date) < 200  -- 少于200条记录
                ORDER BY record_count ASC
                LIMIT 20
            """, conn)

            print("可能数据不完整的股票:")
            if len(suspicious_stocks) > 0:
                for _, row in suspicious_stocks.iterrows():
                    print(f"  {row['stock_code']}: {row['record_count']} 条记录")
                    print(f"    日期范围: {row['earliest_date']} 到 {row['latest_date']}")

                return suspicious_stocks['stock_code'].tolist()
            else:
                print("  没有发现数据量异常的股票")
                return []

    except Exception as e:
        print(f"查询数据完整性时出错: {e}")
        return []

def show_database_summary():
    """显示数据库概要"""
    print("\n数据库概要")
    print("="*50)

    db = StockDataDB()

    try:
        db_info = db.get_database_info()

        print(f"数据库名称: {db.db_path}")
        print(f"数据记录数: {db_info.get('technical_data_count', 0):,}")
        print(f"有数据的股票数: {len(db.get_completed_stock_codes())}")
        print(f"数据时间范围: {db_info.get('data_start_date', 'N/A')} 到 {db_info.get('data_end_date', 'N/A')}")
        print(f"数据库大小: {db_info.get('database_size_mb', 0):.2f} MB")

    except Exception as e:
        print(f"获取数据库信息时出错: {e}")

def main():
    print("股票数据重试和完整性检查")
    print("="*60)

    # 显示数据库概要
    show_database_summary()

    # 获取失败的股票
    failed_stocks = get_failed_stocks()

    # 获取可能数据不完整的股票
    incomplete_stocks = get_missing_data_stocks()

    # 合并需要重试的股票
    retry_stocks = list(set(failed_stocks + incomplete_stocks))

    print(f"\n需要重新获取的股票总数: {len(retry_stocks)}")
    print(f"  - 失败重试: {len(failed_stocks)}")
    print(f"  - 完整性检查: {len(incomplete_stocks)}")

    if retry_stocks:
        print("\n详细的重试股票列表:")
        for i, stock in enumerate(retry_stocks, 1):
            mark = "❌" if stock in failed_stocks else "⚠️"
            print(f"  {i:2d}. {stock} {mark}")

        # 询问是否开始重新获取
        choice = input(f"\n是否开始重新获取这 {len(retry_stocks)} 只股票? (y/N): ").strip().lower()

        if choice == 'y' or choice == 'yes':
            retry_failed_stocks(retry_stocks)
        else:
            print("已取消重新获取")
    else:
        print("没有需要重新获取的股票")

if __name__ == "__main__":
    main()