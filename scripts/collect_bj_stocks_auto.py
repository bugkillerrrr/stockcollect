"""
自动收集北交所股票数据
专门处理285只北交所股票(920xxx)
"""
import sqlite3
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
import os

def get_bj_missing_stocks():
    """获取缺失的北交所股票列表"""
    print("获取缺失的北交所股票列表...")

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

        # 找出缺失的北交所股票
        missing_stocks = api_stocks - db_stocks
        bj_stocks = [code for code in missing_stocks if code.startswith('920')]

        print(f"API获取的总股票数: {len(api_stocks)}")
        print(f"数据库已有股票数: {len(db_stocks)}")
        print(f"总缺失股票数: {len(missing_stocks)}")
        print(f"其中北交所股票(920xxx): {len(bj_stocks)}")

        return bj_stocks

    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return []

def collect_bj_stock_data(stock_code, start_date="19910403", end_date=None):
    """获取北交所股票数据"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    print(f"[处理] 北交所股票: {stock_code}")

    try:
        # 使用北交所股票的API调用方式
        df = ak.stock_zh_a_daily(
            symbol=f"bj{stock_code}",  # 注意这里使用bj前缀
            start_date=start_date,
            end_date=end_date,
            adjust="hfq"  # 后复权
        )

        if df is not None and not df.empty:
            print(f"  [OK] 成功获取 {len(df)} 条记录")
            print(f"      时间范围: {df.index.min()} 到 {df.index.max()}")
            if 'close' in df.columns:
                print(f"      最新价格: {df['close'].iloc[-1]:.2f}")
            return df
        else:
            print(f"  [FAIL] 无数据返回")
            return None

    except Exception as e:
        print(f"  [ERROR] API调用失败: {e}")
        return None

def save_to_database(stock_code, df, db_path="data/stock_data.db"):
    """将数据保存到数据库"""
    if df is None or df.empty:
        return False

    try:
        # 转换DataFrame格式以匹配数据库表结构
        df_clean = pd.DataFrame()

        # 处理日期索引
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

        # 处理amount字段，如果存在的话
        if 'amount' in df.columns:
            df_clean['amount'] = df['amount'].values
        else:
            # 如果没有amount字段，计算一个估算值
            df_clean['amount'] = df['volume'].values * df['close'].values

        with sqlite3.connect(db_path) as conn:
            # 先删除已存在的数据，避免重复
            conn.execute("DELETE FROM technical_data WHERE stock_code = ?", (stock_code,))

            # 插入新数据
            df_clean.to_sql(
                'technical_data',
                conn,
                if_exists='append',
                index=False,
                method='multi'
            )

        return len(df_clean)

    except Exception as e:
        print(f"      [ERROR] 保存数据失败: {e}")
        return False

def collect_all_bj_stocks():
    """收集所有缺失的北交所股票数据"""
    print("="*80)
    print("自动收集北交所股票数据")
    print("="*80)

    # 获取缺失的北交所股票列表
    bj_stocks = get_bj_missing_stocks()
    if not bj_stocks:
        print("没有找到缺失的北交所股票")
        return

    db_path = "data/stock_data.db"
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    print(f"\n开始收集 {len(bj_stocks)} 只北交所股票数据...")
    print("-" * 60)

    # 统计信息
    stats = {
        'total': len(bj_stocks),
        'success': 0,
        'failed': 0,
        'total_records': 0
    }

    start_time = datetime.now()

    # 处理每只股票
    for i, stock_code in enumerate(bj_stocks, 1):
        print(f"[{i}/{len(bj_stocks)}] ", end="")

        # 获取数据
        df = collect_bj_stock_data(stock_code)

        if df is not None:
            # 保存到数据库
            records = save_to_database(stock_code, df, db_path)
            if records:
                stats['success'] += 1
                stats['total_records'] += records
                print(f"      [保存成功] {records} 条记录")
            else:
                stats['failed'] += 1
                print(f"      [保存失败]")
        else:
            stats['failed'] += 1

        # 避免请求过于频繁
        time.sleep(0.5)

        # 每处理50只股票显示一次进度
        if i % 50 == 0:
            progress = i / len(bj_stocks) * 100
            print(f"\n--- 进度: {i}/{len(bj_stocks)} ({progress:.1f}%) ---")
            print(f"当前成功: {stats['success']}, 当前失败: {stats['failed']}")
            print(f"已收集记录: {stats['total_records']:,}")
            print("-" * 40)

    # 输出统计结果
    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "="*80)
    print("北交所股票数据收集完成")
    print("="*80)
    print(f"处理时间: {duration}")
    print(f"总股票数: {stats['total']}")
    print(f"成功收集: {stats['success']}")
    print(f"收集失败: {stats['failed']}")
    print(f"成功率: {stats['success']/stats['total']*100:.1f}%")
    print(f"总记录数: {stats['total_records']:,}")

    # 验证收集结果
    print(f"\n验证收集结果...")
    with sqlite3.connect(db_path) as conn:
        # 检查新增的北交所股票数量
        bj_count = pd.read_sql("""
            SELECT COUNT(DISTINCT stock_code) as count
            FROM technical_data
            WHERE stock_code LIKE '920%'
        """, conn).iloc[0]['count']

        # 检查总股票数量
        total_count = pd.read_sql("""
            SELECT COUNT(DISTINCT stock_code) as count
            FROM technical_data
        """, conn).iloc[0]['count']

        print(f"数据库中北交所股票数: {bj_count}")
        print(f"数据库中总股票数: {total_count}")
        print(f"数据完整率: {total_count/5454*100:.2f}%")  # 5454是API获取的总数

    # 保存报告
    report_file = f"bj_stocks_collection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("北交所股票数据收集报告\n")
        f.write("="*50 + "\n")
        f.write(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"处理时长: {duration}\n\n")

        f.write("收集统计:\n")
        f.write(f"目标股票数: {stats['total']}\n")
        f.write(f"成功收集: {stats['success']}\n")
        f.write(f"收集失败: {stats['failed']}\n")
        f.write(f"成功率: {stats['success']/stats['total']*100:.1f}%\n")
        f.write(f"总记录数: {stats['total_records']:,}\n\n")

        f.write("收集结果:\n")
        f.write(f"数据库中北交所股票数: {bj_count}\n")
        f.write(f"数据库中总股票数: {total_count}\n")
        f.write(f"数据完整率: {total_count/5454*100:.2f}%\n\n")

        f.write("使用的API格式:\n")
        f.write("北交所股票: ak.stock_zh_a_daily(symbol=\"bj920xxx\", adjust=\"hfq\")\n\n")

        f.write("处理的北交所股票代码:\n")
        for i, code in enumerate(bj_stocks, 1):
            f.write(f"{i:3d}. {code}\n")

    print(f"\n详细报告已保存到: {report_file}")

    return stats

def main():
    """主函数 - 自动执行，无需确认"""
    print("北交所股票数据自动收集工具")
    print("="*50)
    print("功能:")
    print("1. 自动识别缺失的北交所股票(920xxx)")
    print("2. 使用 bj920xxx 前缀调用API")
    print("3. 自动保存到数据库")
    print("4. 显示详细进度和统计")
    print("="*50)

    try:
        # 直接开始收集，无需确认
        collect_all_bj_stocks()

    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()