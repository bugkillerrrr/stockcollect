"""
完整收集北交所股票数据（带日志记录）
处理所有285只北交所股票(920xxx)，详细记录整个过程
"""
import sqlite3
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import logging
from tqdm import tqdm

def setup_logging():
    """设置日志记录"""
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # 设置日志文件名（包含时间戳）
    log_filename = f"logs/bj_stocks_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("北交所股票数据收集开始")
    logger.info("="*80)

    return logger, log_filename

def get_bj_missing_stocks(logger):
    """获取缺失的北交所股票列表"""
    logger.info("步骤1: 获取缺失的北交所股票列表...")

    db_path = "data/stock_data.db"

    try:
        # 从API获取当前所有A股股票代码
        logger.info("正在从API获取股票列表...")
        stock_info_df = ak.stock_info_a_code_name()
        api_stocks = set(stock_info_df['code'].tolist())
        logger.info(f"API获取总股票数: {len(api_stocks)}")

        # 从数据库获取已有数据的股票代码
        logger.info("正在从数据库读取已有股票代码...")
        with sqlite3.connect(db_path) as conn:
            db_stocks_df = pd.read_sql("""
                SELECT DISTINCT stock_code as code
                FROM technical_data
                ORDER BY stock_code
            """, conn)
            db_stocks = set(db_stocks_df['code'].tolist())

        logger.info(f"数据库已有股票数: {len(db_stocks)}")

        # 筛选出缺失的北交所股票
        missing_stocks = api_stocks - db_stocks
        bj_stocks = [code for code in missing_stocks if code.startswith('920')]

        logger.info(f"总缺失股票数: {len(missing_stocks)}")
        logger.info(f"其中北交所股票(920xxx): {len(bj_stocks)}")

        # 记录前20只作为示例
        if bj_stocks:
            logger.info("前20只缺失的北交所股票:")
            for i, code in enumerate(bj_stocks[:20], 1):
                try:
                    stock_name = stock_info_df[stock_info_df['code'] == code]['name'].iloc[0]
                    logger.info(f"  {i:2d}. {code} - {stock_name}")
                except:
                    logger.info(f"  {i:2d}. {code}")

            if len(bj_stocks) > 20:
                logger.info(f"  ... 还有 {len(bj_stocks) - 20} 只")

        return bj_stocks

    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def collect_bj_stock_data(stock_code, logger, max_retries=3):
    """获取单只北交所股票数据，支持重试"""
    logger.info(f"正在获取北交所股票 {stock_code} 的数据...")

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"  重试第 {attempt + 1} 次...")
                time.sleep(2)  # 重试前等待2秒

            # 使用北交所股票的API调用方式
            df = ak.stock_zh_a_daily(
                symbol=f"bj{stock_code}",  # 使用bj前缀
                start_date="19910403",  # 北交所成立日期
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="hfq"  # 后复权
            )

            if df is not None and not df.empty:
                logger.info(f"  [OK] 成功获取 {len(df)} 条记录")
                logger.info(f"      时间范围: {df.index.min()} 到 {df.index.max()}")

                if 'close' in df.columns:
                    latest_price = df['close'].iloc[-1]
                    logger.info(f"      最新价格: {latest_price:.2f}")

                logger.info(f"      数据列: {list(df.columns)}")
                return df
            else:
                logger.warning(f"  [FAIL] 无数据返回")
                return None

        except Exception as e:
            logger.warning(f"  [ERROR] 第 {attempt + 1} 次尝试失败: {e}")
            if attempt == max_retries - 1:
                logger.error(f"  [FAIL] 所有重试均失败")
                return None

    return None

def save_to_database(stock_code, df, logger, db_path="data/stock_data.db"):
    """将数据保存到数据库"""
    if df is None or df.empty:
        logger.warning(f"  跳过保存 {stock_code}: 数据为空")
        return False

    try:
        logger.info(f"  正在保存 {stock_code} 的数据到数据库...")

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

        # 处理amount字段
        if 'amount' in df.columns:
            df_clean['amount'] = df['amount'].values
            logger.debug(f"    使用原始amount字段")
        else:
            # 如果没有amount字段，计算估算值
            df_clean['amount'] = df['volume'].values * df['close'].values
            logger.debug(f"    计算amount字段 (volume * close)")

        with sqlite3.connect(db_path) as conn:
            # 先删除已存在的数据，避免重复
            cursor = conn.cursor()
            cursor.execute("DELETE FROM technical_data WHERE stock_code = ?", (stock_code,))
            deleted_rows = cursor.rowcount
            if deleted_rows > 0:
                logger.info(f"    删除原有记录: {deleted_rows} 条")

            # 插入新数据
            df_clean.to_sql(
                'technical_data',
                conn,
                if_exists='append',
                index=False,
                method='multi'
            )

        logger.info(f"  [OK] 成功保存 {len(df_clean)} 条记录")
        return len(df_clean)

    except Exception as e:
        logger.error(f"  [ERROR] 保存数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def collect_all_bj_stocks(logger):
    """收集所有缺失的北交所股票数据"""
    logger.info("步骤2: 开始收集所有缺失的北交所股票数据...")

    # 获取缺失的北交所股票列表
    bj_stocks = get_bj_missing_stocks(logger)
    if not bj_stocks:
        logger.info("没有找到缺失的北交所股票")
        return

    db_path = "data/stock_data.db"
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return

    logger.info(f"开始收集 {len(bj_stocks)} 只北交所股票数据...")
    logger.info("-" * 60)

    # 统计信息
    stats = {
        'total': len(bj_stocks),
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'total_records': 0,
        'total_deleted': 0
    }

    start_time = datetime.now()

    # 使用tqdm显示进度条
    with tqdm(bj_stocks, desc="收集北交所股票", unit="只") as pbar:
        for i, stock_code in enumerate(pbar, 1):
            logger.info(f"[{i}/{len(bj_stocks)}] 处理股票: {stock_code}")
            pbar.set_description(f"处理 {stock_code}")

            try:
                # 获取数据
                df = collect_bj_stock_data(stock_code, logger)

                if df is not None:
                    # 保存到数据库
                    records = save_to_database(stock_code, df, logger, db_path)
                    if records:
                        stats['success'] += 1
                        stats['total_records'] += records
                        logger.info(f"  [SUCCESS] {stock_code}: 收集并保存 {records} 条记录")
                    else:
                        stats['failed'] += 1
                        logger.error(f"  [FAILED] {stock_code}: 保存失败")
                else:
                    stats['failed'] += 1
                    logger.warning(f"  [FAILED] {stock_code}: 数据获取失败")

            except KeyboardInterrupt:
                logger.warning(f"  用户中断，跳过 {stock_code}")
                stats['skipped'] += 1
                break
            except Exception as e:
                logger.error(f"  [ERROR] 处理 {stock_code} 时发生异常: {e}")
                stats['failed'] += 1

            # 避免请求过于频繁
            time.sleep(0.5)

            # 每处理50只股票显示一次进度
            if i % 50 == 0:
                progress = i / len(bj_stocks) * 100
                logger.info(f"--- 进度: {i}/{len(bj_stocks)} ({progress:.1f}%) ---")
                logger.info(f"当前成功: {stats['success']}, 失败: {stats['failed']}, 跳过: {stats['skipped']}")
                logger.info(f"已收集记录: {stats['total_records']:,}")

    # 输出最终统计结果
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("\n" + "="*80)
    logger.info("北交所股票数据收集完成")
    logger.info("="*80)
    logger.info(f"处理时间: {duration}")
    logger.info(f"总股票数: {stats['total']}")
    logger.info(f"成功收集: {stats['success']}")
    logger.info(f"收集失败: {stats['failed']}")
    logger.info(f"用户跳过: {stats['skipped']}")

    if stats['total'] > 0:
        logger.info(f"成功率: {stats['success']/stats['total']*100:.1f}%")

    logger.info(f"总记录数: {stats['total_records']:,}")

    # 验证收集结果
    logger.info(f"\n验证收集结果...")
    try:
        with sqlite3.connect(db_path) as conn:
            # 检查新增的北交所股票数量
            bj_count_result = pd.read_sql("""
                SELECT COUNT(DISTINCT stock_code) as count
                FROM technical_data
                WHERE stock_code LIKE '920%'
            """, conn)
            bj_count = bj_count_result.iloc[0]['count']

            # 检查总股票数量
            total_count_result = pd.read_sql("""
                SELECT COUNT(DISTINCT stock_code) as count
                FROM technical_data
            """, conn)
            total_count = total_count_result.iloc[0]['count']

            logger.info(f"数据库中北交所股票数: {bj_count}")
            logger.info(f"数据库中总股票数: {total_count}")

            # 5454是API获取的总数
            completeness = total_count / 5454 * 100
            logger.info(f"数据完整率: {completeness:.2f}%")

    except Exception as e:
        logger.error(f"验证结果时出错: {e}")

    return stats

def generate_final_report(stats, logger, log_filename, bj_stocks):
    """生成最终报告"""
    report_filename = f"北交所股票收集报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("北交所股票数据收集完整报告\n")
            f.write("="*80 + "\n")
            f.write(f"收集开始时间: {logger.handlers[0].formatter.formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}\n")
            f.write(f"收集结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"详细日志文件: {log_filename}\n\n")

            f.write("收集统计:\n")
            f.write(f"目标股票数: {stats['total']}\n")
            f.write(f"成功收集: {stats['success']}\n")
            f.write(f"收集失败: {stats['failed']}\n")
            f.write(f"用户跳过: {stats['skipped']}\n")
            f.write(f"成功率: {stats['success']/stats['total']*100:.1f}%\n" if stats['total'] > 0 else "成功率: N/A\n")
            f.write(f"总记录数: {stats['total_records']:,}\n\n")

            f.write("技术说明:\n")
            f.write("1. 使用API: ak.stock_zh_a_daily()\n")
            f.write("2. 股票前缀: bj920xxx (北交所)\n")
            f.write("3. 数据类型: 后复权(hfq)\n")
            f.write("4. 时间范围: 1991-04-03 至今\n")
            f.write("5. 数据表: technical_data\n\n")

            f.write("处理的北交所股票代码:\n")
            for i, code in enumerate(bj_stocks, 1):
                f.write(f"{i:3d}. {code}\n")
                if i % 20 == 0:
                    f.write("\n")

        logger.info(f"最终报告已保存到: {report_filename}")
        return report_filename

    except Exception as e:
        logger.error(f"生成报告失败: {e}")
        return None

def main():
    """主函数"""
    print("北交所股票数据完整收集工具")
    print("="*80)
    print("功能:")
    print("1. 自动识别缺失的北交所股票(920xxx)")
    print("2. 使用 bj920xxx 前缀调用API")
    print("3. 自动保存到数据库")
    print("4. 详细日志记录所有过程")
    print("5. 生成完整收集报告")
    print("="*80)

    try:
        # 设置日志
        logger, log_filename = setup_logging()

        # 获取北交所股票列表
        bj_stocks = get_bj_missing_stocks(logger)
        if not bj_stocks:
            logger.info("没有找到缺失的北交所股票，退出")
            return

        logger.info(f"确认开始收集 {len(bj_stocks)} 只北交所股票数据...")
        logger.info("按 Ctrl+C 可以随时中断收集")
        time.sleep(3)  # 给用户3秒时间考虑

        # 开始收集
        stats = collect_all_bj_stocks(logger)

        # 生成最终报告
        generate_final_report(stats, logger, log_filename, bj_stocks)

        logger.info("北交所股票数据收集任务完成！")

    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()