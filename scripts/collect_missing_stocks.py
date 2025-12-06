"""
收集缺失股票数据的脚本
专门处理北交所股票(920xxx)和科创板CDR股票(689xxx)
"""
import sqlite3
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
import os

def get_missing_stocks():
    """获取需要补充数据的股票列表"""
    print("获取需要补充数据的股票列表...")

    db_path = "data/stock_data.db"

    try:
        # 从API获取当前所有A股股票代码
        stock_info_df = ak.stock_info_a_code_name()
        api_stocks = set(stock_info_df['code'].tolist())

        # 从数据库获取已有数据的股票代码
        with sqlite3.connect(db_path) as conn:
            db_stocks_df = pd.read_sql("""
                SELECT DISTINCT stock_code as code
                FROM technical_data
                ORDER BY stock_code
            """, conn)
            db_stocks = set(db_stocks_df['code'].tolist())

        # 找出缺失的股票
        missing_stocks = api_stocks - db_stocks

        # 分类处理
        bj_stocks = [code for code in missing_stocks if code.startswith('920')]
        cdr_stocks = [code for code in missing_stocks if code.startswith('689')]

        print(f"总缺失股票数: {len(missing_stocks)}")
        print(f"北交所股票(920xxx): {len(bj_stocks)}")
        print(f"CDR股票(689xxx): {len(cdr_stocks)}")

        return {
            'bj_stocks': bj_stocks,
            'cdr_stocks': cdr_stocks,
            'all_missing': list(missing_stocks)
        }

    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return None

def collect_bj_stock_data(stock_code, start_date="19910403", end_date=None):
    """
    获取北交所股票数据
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    print(f"正在获取北交所股票 {stock_code} 的数据...")

    try:
        # 使用北交所股票的API调用方式
        df = ak.stock_zh_a_daily(
            symbol=f"bj{stock_code}",
            start_date=start_date,
            end_date=end_date,
            adjust="hfq"  # 后复权
        )

        if df is not None and not df.empty:
            print(f"  获取成功: {len(df)} 条记录")
            return df
        else:
            print(f"  获取失败: 无数据返回")
            return None

    except Exception as e:
        print(f"  获取失败: {e}")
        return None

def collect_cdr_stock_data(stock_code, start_date="19900101", end_date=None):
    """
    获取CDR股票数据
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    print(f"正在获取CDR股票 {stock_code} 的数据...")

    try:
        # 使用CDR股票的API调用方式
        df = ak.stock_zh_a_cdr_daily(
            symbol=f"sh{stock_code}",
            start_date=start_date,
            end_date=end_date
        )

        if df is not None and not df.empty:
            print(f"  获取成功: {len(df)} 条记录")
            return df
        else:
            print(f"  获取失败: 无数据返回")
            return None

    except Exception as e:
        print(f"  获取失败: {e}")
        return None

def save_to_database(stock_code, df, db_path="data/stock_data.db"):
    """将数据保存到数据库"""
    if df is None or df.empty:
        return False

    try:
        # 转换DataFrame格式以匹配数据库表结构
        df_clean = pd.DataFrame({
            'stock_code': stock_code,
            'trade_date': df.index,  # 使用日期索引
            'open_price': df['open'].values,
            'high_price': df['high'].values,
            'low_price': df['low'].values,
            'close_price': df['close'].values,
            'volume': df['volume'].values,
            'amount': df['amount'].values
        }).reset_index(drop=True)

        # 确保trade_date是字符串格式
        df_clean['trade_date'] = df_clean['trade_date'].astype(str)

        with sqlite3.connect(db_path) as conn:
            # 使用INSERT OR REPLACE避免重复
            df_clean.to_sql(
                'technical_data',
                conn,
                if_exists='append',
                index=False,
                method='multi'
            )

        return len(df_clean)

    except Exception as e:
        print(f"  保存数据失败: {e}")
        return False

def collect_all_missing_stocks():
    """收集所有缺失的股票数据"""
    print("="*80)
    print("开始收集缺失股票数据")
    print("="*80)

    # 获取缺失股票列表
    missing_info = get_missing_stocks()
    if not missing_info:
        print("无法获取缺失股票列表")
        return

    db_path = "data/stock_data.db"

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    # 统计信息
    stats = {
        'bj_total': len(missing_info['bj_stocks']),
        'cdr_total': len(missing_info['cdr_stocks']),
        'bj_success': 0,
        'cdr_success': 0,
        'bj_failed': 0,
        'cdr_failed': 0,
        'total_records': 0
    }

    start_time = datetime.now()

    # 处理北交所股票
    if missing_info['bj_stocks']:
        print(f"\n开始处理北交所股票 ({len(missing_info['bj_stocks'])}只)...")
        print("-" * 60)

        for i, stock_code in enumerate(missing_info['bj_stocks'], 1):
            print(f"[{i}/{len(missing_info['bj_stocks'])}] 处理 {stock_code}")

            # 获取数据
            df = collect_bj_stock_data(stock_code)

            if df is not None:
                # 保存到数据库
                records = save_to_database(stock_code, df, db_path)
                if records:
                    stats['bj_success'] += 1
                    stats['total_records'] += records
                    print(f"  ✓ 成功保存 {records} 条记录")
                else:
                    stats['bj_failed'] += 1
                    print(f"  ✗ 保存失败")
            else:
                stats['bj_failed'] += 1

            # 避免请求过于频繁
            time.sleep(0.5)

    # 处理CDR股票
    if missing_info['cdr_stocks']:
        print(f"\n开始处理CDR股票 ({len(missing_info['cdr_stocks'])}只)...")
        print("-" * 60)

        for i, stock_code in enumerate(missing_info['cdr_stocks'], 1):
            print(f"[{i}/{len(missing_info['cdr_stocks'])}] 处理 {stock_code}")

            # 获取数据
            df = collect_cdr_stock_data(stock_code)

            if df is not None:
                # 保存到数据库
                records = save_to_database(stock_code, df, db_path)
                if records:
                    stats['cdr_success'] += 1
                    stats['total_records'] += records
                    print(f"  ✓ 成功保存 {records} 条记录")
                else:
                    stats['cdr_failed'] += 1
                    print(f"  ✗ 保存失败")
            else:
                stats['cdr_failed'] += 1

            # 避免请求过于频繁
            time.sleep(0.5)

    # 输出统计结果
    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "="*80)
    print("数据收集完成统计")
    print("="*80)
    print(f"处理时间: {duration}")
    print(f"北交所股票: 成功 {stats['bj_success']}/{stats['bj_total']}, 失败 {stats['bj_failed']}")
    print(f"CDR股票: 成功 {stats['cdr_success']}/{stats['cdr_total']}, 失败 {stats['cdr_failed']}")
    print(f"总成功: {stats['bj_success'] + stats['cdr_success']}")
    print(f"总失败: {stats['bj_failed'] + stats['cdr_failed']}")
    print(f"总记录数: {stats['total_records']:,}")

    # 保存报告
    report_file = f"missing_stocks_collection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("缺失股票数据收集报告\n")
        f.write("="*50 + "\n")
        f.write(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"处理时长: {duration}\n\n")

        f.write("处理统计:\n")
        f.write(f"北交所股票: 成功 {stats['bj_success']}/{stats['bj_total']}, 失败 {stats['bj_failed']}\n")
        f.write(f"CDR股票: 成功 {stats['cdr_success']}/{stats['cdr_total']}, 失败 {stats['cdr_failed']}\n")
        f.write(f"总成功: {stats['bj_success'] + stats['cdr_success']}\n")
        f.write(f"总失败: {stats['bj_failed'] + stats['cdr_failed']}\n")
        f.write(f"总记录数: {stats['total_records']:,}\n")

        if missing_info['bj_stocks']:
            f.write("\n处理的北交所股票:\n")
            f.write(" ".join(missing_info['bj_stocks']) + "\n")

        if missing_info['cdr_stocks']:
            f.write("\n处理的CDR股票:\n")
            f.write(" ".join(missing_info['cdr_stocks']) + "\n")

    print(f"\n详细报告已保存到: {report_file}")

def main():
    """主函数"""
    print("缺失股票数据收集工具")
    print("="*50)
    print("功能:")
    print("1. 收集北交所股票(920xxx)数据")
    print("2. 收集CDR股票(689xxx)数据")
    print("3. 自动保存到数据库")
    print("="*50)

    try:
        confirm = input("确认开始收集缺失股票数据? (y/n): ")
        if confirm.lower() == 'y':
            collect_all_missing_stocks()
        else:
            print("操作已取消")
    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()