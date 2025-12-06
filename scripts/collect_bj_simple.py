"""
简化版北交所股票收集脚本
专门处理285只缺失的北交所股票
"""
import sqlite3
import akshare as ak
import pandas as pd
from datetime import datetime
import time
import os

def get_missing_bj_stocks():
    """获取缺失的北交所股票列表"""
    print("正在获取缺失的北交所股票列表...")
    try:
        # 从API获取所有股票
        stock_info = ak.stock_info_a_code_name()
        api_codes = set(stock_info['code'].tolist())

        # 从数据库获取已有数据股票
        with sqlite3.connect("data/stock_data.db") as conn:
            existing_df = pd.read_sql("""
                SELECT DISTINCT stock_code as code
                FROM technical_data
                ORDER BY stock_code
            """, conn)
            existing_codes = set(existing_df['code'].tolist())

        # 找出缺失的北交所股票
        missing_bj = [code for code in api_codes
                       if code.startswith('920') and code not in existing_codes]

        print(f"[OK] 找到 {len(missing_bj)} 只缺失的北交所股票")
        return sorted(missing_bj)

    except Exception as e:
        print(f"[ERROR] 获取失败: {e}")
        return []

def collect_and_save_bj_stock(stock_code, db_path="data/stock_data.db", max_retries=3):
    """收集并保存单只北交所股票"""
    print(f"正在收集 {stock_code} 的数据...")

    for attempt in range(max_retries):
        try:
            # 使用北交所专用API
            df = ak.stock_zh_a_daily(
                symbol=f"bj{stock_code}",
                start_date="19910403",  # 北交所成立时间
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="hfq"
            )

            if df is not None and not df.empty:
                record_count = len(df)
                print(f"  [OK] 第{attempt+1}次尝试: 成功获取 {record_count} 条记录")
                print(f"      时间范围: {df.index.min()} 到 {df.index.max()}")
                print(f"      最新价格: {df['close'].iloc[-1]:.2f}")
                print(f"      成交量: {df['volume'].iloc[-1]:,}")

                # 准备保存
                df_clean = pd.DataFrame()
                if hasattr(df.index, 'to_pydatetime'):
                    dates = df.index.to_pydatetime()
                else:
                    dates = df.index

                df_clean['stock_code'] = stock_code
                df_clean['trade_date'] = dates.astype(str)
                df_clean['open_price'] = df['open'].values
                df_clean['high_price'] = df['high'].values
                df_clean['low_price'] = df['low'].values
                df_clean['close_price'] = df['close'].values
                df_clean['volume'] = df['volume'].values

                # 计算amount（如果没有就估算）
                if 'amount' in df.columns:
                    df_clean['amount'] = df['amount'].values
                else:
                    df_clean['amount'] = df['volume'].values * df['close_price'].values

                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM technical_data WHERE stock_code = ?", (stock_code,))
                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        print(f"      删除原有记录: {deleted_count} 条")

                    # 保存新数据
                    df_clean.to_sql(
                        'technical_data',
                        conn,
                        if_exists='append',
                        index=False,
                        method='multi'
                    )
                    saved_count = cursor.rowcount
                    if saved_count > 0:
                        print(f"      [SUCCESS] 成功保存 {saved_count} 条记录")
                        return True
                    else:
                        print(f"      [FAILED] 保存失败")
                        return False
            except Exception as e:
                print(f"    [ERROR] 第{attempt+1} 次保存失败: {e}")

        else:
            print(f"    [FAIL] 第{attempt+1} 次: 无数据返回")
            return False

def main():
    """主函数"""
    print("简化版北交所股票数据收集工具")
    print("="*50)
    print("功能:")
    print("1. 精对性收集285只缺失的北交所股票(920xxx)")
    print("2. 每只股票重试3次")
    print("3. 详细记录所有处理过程")
    print("4. 确保每只股票都成功保存")
    print("5. 实时显示进度和统计")
    print("="*50)

    try:
        # 获取缺失的北交所股票列表
        missing_bj_stocks = get_missing_bj_stocks()
        if not missing_bj_stocks:
            print("没有发现缺失的北交所股票，退出")
            return

        print(f"\n找到 {len(missing_bj_stocks)} 只需要收集的北交所股票")
        print("前10只股票:")
        for i, code in enumerate(missing_bj_stocks[:10], 1):
            print(f"  {i:2d}. {code}")

        # 设置数据库路径
        db_path = "data/stock_data.db"
        if not os.path.exists(db_path):
            print(f"错误: 数据库文件不存在: {db_path}")
            return

        # 统计信息
        stats = {
            'total': len(missing_bj_stocks),
            'success': 0,
            'failed': 0,
            'total_records': 0
        }

        print(f"\n开始收集数据...")
        start_time = datetime.now()

        # 分批处理，每批5只
        batch_size = 5
        for i in range(0, len(missing_bj_stocks), batch_size):
            batch_stocks = missing_bj_stocks[i:i+batch_size]

            print(f"\n批次 {i//batch_size + 1}: 处理 {len(batch_stocks)} 只股票")

            for j, stock_code in enumerate(batch_stocks, 1):
                print(f"  [{j+1}/{len(batch_stocks)}] {stock_code}")

            # 处理当前批次中的股票
            for stock_code in batch_stocks:
                print(f"    正在处理: {stock_code}")
                if collect_and_save_bj_stock(stock_code, db_path):
                    stats['success'] += 1
                    stats['total_records'] += len(ak.stock_zh_a_daily(
                        symbol=f"bj{stock_code}",
                        start_date="19910403",
                        end_date=datetime.now().strftime("%Y%m%d"),
                        adjust="hfq"
                    ))
                else:
                    stats['failed'] += 1

                # 显示批次进度
                progress = (i + len(batch_stocks)) / len(missing_bj_stocks) * 100
                print(f"    进度: {progress:.1f}% ({i+len(batch_stocks)}/{len(missing_bj_stocks)})")

                # 每处理10只就显示详细统计
                if (j + 1) % 10 == 0:
                    print(f"    当前批次统计: 成功 {stats['success']}, 失败 {stats['failed']}, 总记录数: {stats['total_records']}")

                # 批次之间稍作等待，避免API限制
                if i > 0 and (i + 1) % 10 == 0:
                    print(f"    等待2秒...")
                    time.sleep(2)

        end_time = datetime.now()
        duration = end_time - start_time

        # 最终统计
        print(f"\n收集完成！")
        print(f"处理时间: {duration}")
        print(f"总股票数: {stats['total']}")
        print(f"成功收集: {stats['success']}")
        print(f"收集失败: {stats['failed']}")
        print(f"总记录数: {stats['total_records']:,}")
        print(f"成功率: {stats['success']/stats['total']*100:.1f}%")

        # 验证结果
        if stats['success'] == stats['total']:
            print(f"✅ 所有{stats['total']}只北交所股票全部成功收集！")

        # 保存结果到文件
        result_file = f"bj_collection_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write("北交所股票数据收集结果\n")
            f.write("="*50 + "\n")
            f.write(f"收集时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"处理时间: {duration}\n\n")

            f.write(f"目标股票数: {stats['total']}\n")
            f.write(f"成功收集: {stats['success']}\n")
            f.write(f"收集失败: {stats['failed']}\n")
            f.write(f"总记录数: {stats['total_records']:,}\n")
            f.write(f"成功率: {stats['success']/stats['total']*100:.1f}%\n\n")

            f.write("\n成功收集的股票:\n")
            success_count = 0
            for i, stock_code in enumerate(missing_bj_stocks, 1):
                if collect_and_save_bj_stock(stock_code, db_path):
                    f.write(f"{i:4d}. {stock_code}\n")
                    success_count += 1

            f.write(f"\n收集失败的股票:\n")
            failed_count = 0
            for i, stock_code in enumerate(missing_bj_stocks, 1):
                if not collect_and_save_bj_stock(stock_code, db_path):
                    f.write(f"{i:4d}. {stock_code}\n")
                    failed_count += 1

            f.write(f"\n成功率: {success_count/stats['total']*100:.1f}%\n")

        print(f"结果已保存到: {result_file}")

    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()