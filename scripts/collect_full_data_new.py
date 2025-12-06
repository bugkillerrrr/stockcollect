#!/usr/bin/env python3
"""
股票数据系统 - 完整数据收集程序（使用新的数据收集器）
根据新规则收集2018年至今的所有股票历史数据

规则说明：
1. 沪深A股：使用标准接口 stock_zh_a_daily
   - 深圳（00、30开头）：sz + 股票代码
   - 上海（60、68开头）：sh + 股票代码
2. 北交所（92开头）：使用标准接口 stock_zh_a_daily，bj + 股票代码
3. 689009特殊股票：使用 CDR 接口 stock_zh_a_cdr_daily，sh + 股票代码
"""

import os
import sys
import time
import argparse
import json
import signal
from datetime import datetime, timedelta
from pathlib import Path

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from data_collector_new import AkshareDataCollectorNew
    from database_new import StockDataNewDB
    from logger import get_logger
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的环境中运行，并且所有依赖包已安装")
    sys.exit(1)

class GracefulKiller:
    """优雅停止处理器"""
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        print(f"\n检测到中断信号 {signum}，将在当前股票完成后停止...")


class NewFullDataCollector:
    """完整数据收集器（使用新的数据收集器和数据库）"""

    def __init__(self, adjustment_type='hfq', api_method='stock_zh_a_daily'):
        self.logger = get_logger()
        self.db = StockDataNewDB()
        self.collector = AkshareDataCollectorNew(
            db=self.db,
            request_interval=2.0,
            max_retries=3,
            adjustment_type=adjustment_type,
            api_method=api_method
        )
        self.killer = GracefulKiller()

        # 设置时间范围：从2018年到现在
        self.start_date = "20180101"
        self.end_date = datetime.now().strftime("%Y%m%d")

        # 进度文件
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.progress_file = self.log_dir / "new_collection_progress.json"

    def get_all_stock_codes(self, limit=None):
        """获取所有A股股票代码"""
        self.logger.info("正在获取所有A股股票列表...")

        try:
            stock_list_df = self.collector.get_stock_list()

            if stock_list_df is None or stock_list_df.empty:
                self.logger.error("获取股票列表失败")
                return []

            # 适配不同的列名
            if 'stock_code' in stock_list_df.columns:
                stock_codes = stock_list_df['stock_code'].tolist()
            elif 'code' in stock_list_df.columns:
                stock_codes = stock_list_df['code'].tolist()
            else:
                print(f"可用的列名: {list(stock_list_df.columns)}")
                print(f"数据示例: {stock_list_df.head()}")
                self.logger.error(f"无法找到股票代码列，可用列: {list(stock_list_df.columns)}")
                return []

            # 如果设置了限制，只取前N只股票进行测试
            if limit and limit > 0:
                stock_codes = stock_codes[:limit]
                self.logger.info(f"测试模式：只收集前 {limit} 只股票")

            # 按规则分类显示
            self._classify_and_display_stocks(stock_codes)

            self.logger.info(f"获取到 {len(stock_codes)} 只股票")
            return stock_codes

        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return []

    def _classify_and_display_stocks(self, stock_codes):
        """按规则分类显示股票"""
        special_689009 = []
        beijing_stocks = []
        shenzhen_stocks = []
        shanghai_stocks = []
        other_stocks = []

        for code in stock_codes:
            if code == '689009':
                special_689009.append(code)
            elif code.startswith('92'):
                beijing_stocks.append(code)
            elif code.startswith('00') or code.startswith('30'):
                shenzhen_stocks.append(code)
            elif code.startswith('60') or code.startswith('68'):
                shanghai_stocks.append(code)
            else:
                other_stocks.append(code)

        print(f"\n股票分类统计:")
        print(f"  特殊股票(689009): {len(special_689009)} 只")
        print(f"  北交所股票(92开头): {len(beijing_stocks)} 只")
        print(f"  深圳股票(00/30开头): {len(shenzhen_stocks)} 只")
        print(f"  上海股票(60/68开头): {len(shanghai_stocks)} 只")
        print(f"  其他股票: {len(other_stocks)} 只")
        print(f"  总计: {len(stock_codes)} 只")

        # 显示特殊股票
        if special_689009:
            print(f"\n特殊股票(CDR接口): {special_689009}")

    def get_pending_stocks(self, all_stock_codes):
        """获取待收集的股票列表，自动跳过已完成的股票"""
        self.logger.info("正在检查已完成的股票...")

        try:
            # 获取已完成数据收集的股票代码
            completed_codes = set(self.db.get_stock_codes())

            # 过滤出待收集的股票代码
            pending_codes = []
            for code in all_stock_codes:
                if code not in completed_codes:
                    pending_codes.append(code)
                else:
                    # 检查数据质量，确保数据完整
                    count = self.db.get_stock_data_count(code)
                    if count < 100:  # 假设正常股票应该有超过100条记录
                        self.logger.warning(f"股票 {code} 数据不完整 ({count} 条记录)，重新收集")
                        pending_codes.append(code)

            self.logger.info(f"已完成: {len(completed_codes)} 只股票")
            self.logger.info(f"待收集: {len(pending_codes)} 只股票")

            if completed_codes:
                self.logger.info(f"已完成的股票: {sorted(list(completed_codes))[:10]}...")

            return pending_codes, len(completed_codes)

        except Exception as e:
            self.logger.error(f"获取待处理股票失败: {e}")
            return all_stock_codes, 0

    def save_progress(self, current_index, total_count, current_stock, success_count, failed_stocks):
        """保存当前进度"""
        try:
            progress_data = {
                "current_index": current_index,
                "total_count": total_count,
                "current_stock": current_stock,
                "success_count": success_count,
                "failed_count": len(failed_stocks),
                "failed_stocks": failed_stocks[:20],  # 只保存前20个失败的股票
                "timestamp": datetime.now().isoformat(),
                "percentage": (current_index / total_count * 100) if total_count > 0 else 0
            }

            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.warning(f"保存进度文件失败: {e}")

    def collect_stock_data(self, stock_code, start_date=None, end_date=None):
        """收集单只股票的数据"""
        if start_date is None:
            start_date = self.start_date
        if end_date is None:
            end_date = self.end_date

        try:
            # 使用新的数据收集器，自动应用规则
            success = self.collector.get_and_save_single_stock(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date
            )
            return success

        except Exception as e:
            self.logger.error(f"收集 {stock_code} 数据失败: {e}")
            return False

    def collect_all_data(self, stock_codes=None, max_retries=3, delay=2.0, limit=None):
        """收集所有股票数据，支持自动续传和优雅停止"""
        if stock_codes is None:
            # 获取所有股票代码并排序确保一致性
            all_stock_codes = self.get_all_stock_codes(limit=limit)
            all_stock_codes.sort()  # 排序确保每次运行的顺序一致

            # 获取待收集的股票（自动跳过已完成的）
            stock_codes, completed_count = self.get_pending_stocks(all_stock_codes)

            if not stock_codes:
                self.logger.info("所有股票数据收集已完成！")
                return

        if not stock_codes:
            self.logger.error("没有股票代码，无法开始收集")
            return

        total_stocks = len(stock_codes)
        success_count = 0
        failed_stocks = []

        self.logger.info(f"开始收集 {total_stocks} 只股票的数据")
        self.logger.info(f"时间范围: {self.start_date} - {self.end_date}")
        self.logger.info(f"复权类型: {self.collector.adjustment_type}")
        self.logger.info(f"API方法: {self.collector.api_method}")
        self.logger.info("=" * 80)

        start_time = time.time()

        for i, stock_code in enumerate(stock_codes, 1):
            # 检查是否收到停止信号
            if self.killer.kill_now:
                self.logger.info("收到停止信号，正在优雅退出...")
                self.logger.info(f"当前进度: {i-1}/{total_stocks} ({(i-1)/total_stocks*100:.1f}%)")
                self.save_progress(i-1, total_stocks, stock_code, success_count, failed_stocks)
                break

            self.logger.info(f"[{i}/{total_stocks}] 正在收集 {stock_code}...")

            retry_count = 0
            success = False

            while retry_count < max_retries and not success:
                # 每次重试前检查停止信号
                if self.killer.kill_now:
                    break

                try:
                    success = self.collect_stock_data(stock_code)

                    if not success:
                        retry_count += 1
                        if retry_count < max_retries and not self.killer.kill_now:
                            self.logger.warning(f"{stock_code} 收集失败，正在重试 ({retry_count}/{max_retries})")
                            time.sleep(delay * retry_count)  # 递增延迟

                except Exception as e:
                    self.logger.error(f"{stock_code} 收集异常: {e}")
                    retry_count += 1
                    if retry_count < max_retries and not self.killer.kill_now:
                        time.sleep(delay * retry_count)

            # 如果收到停止信号，跳出主循环
            if self.killer.kill_now:
                break

            if success:
                success_count += 1
            else:
                failed_stocks.append(stock_code)
                if not self.killer.kill_now:
                    self.logger.error(f"{stock_code} 收集失败，已达到最大重试次数")

            # 保存进度
            self.save_progress(i, total_stocks, stock_code, success_count, failed_stocks)

            # 请求间隔，避免过于频繁
            if not self.killer.kill_now:
                time.sleep(delay)

            # 每50只股票显示一次进度
            if i % 50 == 0:
                elapsed_time = time.time() - start_time
                avg_time = elapsed_time / i
                remaining_time = avg_time * (total_stocks - i)
                remaining_hours = remaining_time / 3600

                self.logger.info(f"进度: {i}/{total_stocks} ({i/total_stocks*100:.1f}%) "
                               f"成功: {success_count} 失败: {len(failed_stocks)} "
                               f"平均: {avg_time:.1f}秒/股 "
                               f"预计剩余: {remaining_hours:.1f} 小时")

        # 统计结果
        end_time = time.time()
        total_time = end_time - start_time
        total_hours = total_time / 3600

        self.logger.info("=" * 80)
        if self.killer.kill_now:
            self.logger.info("数据收集已暂停!")
        else:
            self.logger.info("数据收集完成!")

        self.logger.info(f"本次处理: {total_stocks} 只股票")
        self.logger.info(f"成功收集: {success_count}")
        self.logger.info(f"收集失败: {len(failed_stocks)}")
        self.logger.info(f"总耗时: {total_hours:.2f} 小时")
        if total_stocks > 0:
            self.logger.info(f"平均每只股票: {total_time/total_stocks:.2f} 秒")

        if failed_stocks:
            self.logger.info(f"失败的股票代码: {failed_stocks[:10]}...")  # 只显示前10个

        # 清理进度文件（如果正常完成）
        if not self.killer.kill_now and not failed_stocks:
            try:
                if self.progress_file.exists():
                    self.progress_file.unlink()
                    self.logger.info("已清理进度文件")
            except Exception as e:
                self.logger.warning(f"清理进度文件失败: {e}")

    def get_database_stats(self):
        """获取数据库统计信息"""
        try:
            stats = self.db.get_database_info()
            print("\n新数据库统计信息:")
            print(f"  技术数据记录: {stats.get('new_technical_data_records', 0):,}")
            print(f"  股票主表记录: {stats.get('new_stock_master_records', 0):,}")
            print(f"  数据库大小: {stats.get('new_database_size_mb', 0):.2f} MB")
            print(f"  数据时间范围: {stats.get('new_data_start_date', 'N/A')} 到 {stats.get('new_data_end_date', 'N/A')}")

            # 显示按复权类型和API方法的汇总
            adjustment_summary = self.db.get_adjustment_summary()
            if not adjustment_summary.empty:
                print("\n数据收集方式汇总:")
                for _, row in adjustment_summary.iterrows():
                    print(f"  {row['adjustment_type']} ({row['api_method']}): "
                          f"{row['record_count']:,} 条记录, {row['stock_count']} 只股票, "
                          f"时间范围: {row['earliest_date']} 到 {row['latest_date']}")

        except Exception as e:
            self.logger.error(f"获取数据库统计信息失败: {e}")

    def print_current_settings(self):
        """打印当前设置"""
        self.collector.print_current_settings()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='股票数据系统 - 完整数据收集程序（新规则）')
    parser.add_argument('--mode', type=int, choices=[1, 2, 3, 4], default=1,
                       help='收集模式: 1=测试模式(10只), 2=小规模(100只), 3=中等规模(1000只), 4=完整模式(所有)')
    parser.add_argument('--adjustment', type=str, choices=['hfq', 'qfq'], default='hfq',
                       help='复权类型: hfq=后复权(长期分析), qfq=前复权(短线交易)')
    parser.add_argument('--api', type=str, choices=['stock_zh_a_daily', 'stock_zh_a_hist'],
                       default='stock_zh_a_daily', help='API方法')
    parser.add_argument('--auto', action='store_true', help='自动运行，跳过确认提示')

    args = parser.parse_args()

    mode_limits = {1: 10, 2: 100, 3: 1000, 4: None}
    limit = mode_limits[args.mode]

    print("=" * 100)
    print("股票数据系统 - 完整数据收集程序（新规则版）")
    print("=" * 100)
    print("数据获取规则:")
    print("  1. 沪深A股：使用标准接口 stock_zh_a_daily")
    print("     - 深圳（00、30开头）：sz + 股票代码")
    print("     - 上海（60、68开头）：sh + 股票代码")
    print("  2. 北交所（92开头）：使用标准接口 stock_zh_a_daily，bj + 股票代码")
    print("  3. 689009特殊股票：使用 CDR 接口 stock_zh_a_cdr_daily，sh + 股票代码")
    print("\n新增功能:")
    print("  ✓ 自动续传 - 跳过已完成股票，支持中断后继续")
    print("  ✓ 优雅停止 - Ctrl+C 安全暂停，保存当前进度")
    print("  ✓ 股票排序 - 确保每次运行顺序一致")
    print("  ✓ 进度追踪 - 实时显示收集进度和剩余时间")
    print("  ✓ 规则分类 - 自动识别并分类不同市场股票")
    print("  ✓ 灵活配置 - 支持不同复权类型和API方法")
    print("=" * 100)
    print("提示: 任何时候按 Ctrl+C 可以安全停止程序")

    # 创建收集器
    collector = NewFullDataCollector(
        adjustment_type=args.adjustment,
        api_method=args.api
    )

    # 显示当前设置
    print("\n当前数据收集设置:")
    collector.print_current_settings()

    # 显示当前数据库状态
    print("\n当前数据库状态:")
    collector.get_database_stats()

    # 显示选择的模式
    mode_names = {1: "测试模式", 2: "小规模模式", 3: "中等规模模式", 4: "完整模式"}
    print(f"\n收集模式: {mode_names[args.mode]}")

    # 如果不是自动模式，询问用户是否继续
    if not args.auto:
        try:
            response = input("\n是否开始收集数据? (y/N): ").strip().lower()
            if response not in ['y', 'yes', '是']:
                print("已取消")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n检测到中断，使用自动模式运行")

    # 开始收集
    start_time = datetime.now()
    print(f"\n开始时间: {start_time}")

    if limit:
        print(f"测试模式：只收集前 {limit} 只股票")
    else:
        print("完整模式：收集所有股票数据")

    try:
        print(f"\n开始收集数据...")
        print("注意：程序会自动跳过已完成的股票，支持中断后继续")

        # 开始收集（传None表示自动获取待收集股票）
        collector.collect_all_data(stock_codes=None, limit=limit)

        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n结束时间: {end_time}")
        print(f"总耗时: {duration}")

        # 显示最终数据库状态
        print("\n最终数据库状态:")
        collector.get_database_stats()

    except KeyboardInterrupt:
        print("\n\n用户中断了数据收集过程")
    except Exception as e:
        print(f"\n\n数据收集过程中出现错误: {e}")
        collector.logger.error(f"数据收集异常: {e}", exc_info=True)


if __name__ == "__main__":
    main()