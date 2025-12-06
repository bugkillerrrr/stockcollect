"""
查找缺失股票数据的股票代码
对比API获取的股票列表和数据库中实际有数据的股票
"""
import sqlite3
import akshare as ak
from datetime import datetime
import os

def find_missing_stocks():
    """查找API有但数据库中缺失的股票"""
    print("查找缺失股票数据的股票代码")
    print("="*60)

    db_path = "data/stock_data.db"

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    try:
        # 1. 从数据库获取已有数据的股票代码
        with sqlite3.connect(db_path) as conn:
            db_stocks_df = pd.read_sql("""
                SELECT DISTINCT stock_code as code
                FROM technical_data
                ORDER BY stock_code
            """, conn)

            db_stocks = set(db_stocks_df['code'].tolist())
            print(f"数据库中有数据的股票数: {len(db_stocks)}")

        # 2. 从API获取当前所有A股股票代码
        print("正在获取A股股票列表...")
        try:
            # 获取A股基本信息
            stock_info_df = ak.stock_info_a_code_name()
            api_stocks = set(stock_info_df['code'].tolist())
            print(f"API获取的股票总数: {len(api_stocks)}")

        except Exception as e:
            print(f"获取股票列表失败: {e}")
            print("尝试使用备用方法...")
            try:
                # 备用方法：获取沪深A股
                sh_stocks = set(ak.stock_info_a_code_name().query('market=="上海"')['code'].tolist())
                sz_stocks = set(ak.stock_info_a_code_name().query('market=="深圳"')['code'].tolist())
                api_stocks = sh_stocks | sz_stocks
                print(f"备用方法获取的股票总数: {len(api_stocks)}")
            except Exception as e2:
                print(f"备用方法也失败: {e2}")
                return

        # 3. 对比找出缺失的股票
        missing_stocks = api_stocks - db_stocks
        extra_stocks = db_stocks - api_stocks  # 数据库中有但API中没有的（可能已退市）

        print(f"\n=== 股票数据对比结果 ===")
        print(f"API获取总数: {len(api_stocks)}")
        print(f"数据库有数据: {len(db_stocks)}")
        print(f"缺失股票数: {len(missing_stocks)}")
        print(f"多余股票数: {len(extra_stocks)}")
        print(f"数据完整率: {len(db_stocks) / len(api_stocks) * 100:.2f}%")

        # 4. 详细列出缺失的股票
        if missing_stocks:
            missing_list = sorted(list(missing_stocks))
            print(f"\n=== 缺失数据的股票代码 ({len(missing_list)}只) ===")

            # 显示前50只
            print("前50只缺失股票:")
            for i, code in enumerate(missing_list[:50], 1):
                print(f"  {i:3d}. {code}")

            if len(missing_list) > 50:
                print(f"  ... 还有 {len(missing_list) - 50} 只未显示")

            # 按股票代码前缀分组统计
            prefix_stats = {}
            for code in missing_list:
                prefix = code[:3] if len(code) >= 3 else code
                if prefix not in prefix_stats:
                    prefix_stats[prefix] = 0
                prefix_stats[prefix] += 1

            print(f"\n=== 缺失股票按代码前缀统计 ===")
            for prefix, count in sorted(prefix_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {prefix}xxx: {count} 只")

        if extra_stocks:
            extra_list = sorted(list(extra_stocks))
            print(f"\n=== 数据库中多余的股票 ({len(extra_list)}只，可能已退市) ===")
            for i, code in enumerate(extra_list[:20], 1):
                print(f"  {i:3d}. {code}")
            if len(extra_list) > 20:
                print(f"  ... 还有 {len(extra_list) - 20} 只未显示")

        # 5. 生成报告文件
        report_file = f"missing_stocks_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("缺失股票数据报告\n")
            f.write("="*50 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据库路径: {db_path}\n\n")

            f.write("股票数据统计:\n")
            f.write(f"1. API获取总数: {len(api_stocks)}\n")
            f.write(f"2. 数据库有数据: {len(db_stocks)}\n")
            f.write(f"3. 缺失股票数: {len(missing_stocks)}\n")
            f.write(f"4. 多余股票数: {len(extra_stocks)}\n")
            f.write(f"5. 数据完整率: {len(db_stocks) / len(api_stocks) * 100:.2f}%\n\n")

            if missing_stocks:
                f.write("缺失数据的股票代码:\n")
                for code in sorted(missing_stocks):
                    f.write(f"{code}\n")
                f.write("\n")

            if extra_stocks:
                f.write("数据库中多余的股票代码(可能已退市):\n")
                for code in sorted(extra_stocks):
                    f.write(f"{code}\n")
                f.write("\n")

            f.write("建议处理步骤:\n")
            f.write("1. 优先处理缺失的股票数据\n")
            f.write("2. 检查这些股票是否正常交易\n")
            f.write("3. 重新获取缺失股票的历史数据\n")
            f.write("4. 清理已退市的股票数据\n")
            f.write("5. 建立定期数据完整性检查机制\n")

        print(f"\n报告已保存到: {report_file}")

        return {
            'missing_stocks': sorted(list(missing_stocks)),
            'extra_stocks': sorted(list(extra_stocks)),
            'api_total': len(api_stocks),
            'db_total': len(db_stocks),
            'missing_count': len(missing_stocks),
            'extra_count': len(extra_stocks)
        }

    except Exception as e:
        print(f"检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    result = find_missing_stocks()

    if result and result['missing_count'] > 0:
        print(f"\n=== 需要重点关注的缺失股票 ===")
        missing_stocks = result['missing_stocks'][:100]  # 前100只
        print(" ".join(missing_stocks))
        print(f"\n建议:")
        print(f"1. 共有 {result['missing_count']} 只股票缺失数据")
        print("2. 检查这些股票是否正常交易")
        print("3. 重新获取这些股票的完整历史数据")
        print("4. 优先处理主板股票(000xxx、002xxx、600xxx、601xxx等)")
    elif result:
        print("\n✅ 所有股票数据完整，无缺失")
    else:
        print("\n❌ 检查失败")

if __name__ == "__main__":
    import pandas as pd  # 移到顶部避免重复导入
    main()