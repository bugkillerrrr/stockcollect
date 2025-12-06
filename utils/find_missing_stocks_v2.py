"""
对比检查缺失的股票代码
从API获取股票列表，与数据库现有数据对比，找出缺失的股票
"""
import sqlite3
import akshare as ak
import pandas as pd
from datetime import datetime
import os

def get_all_api_stocks():
    """从API获取所有A股股票"""
    print("正在从API获取所有A股股票代码...")
    try:
        # 获取A股基本信息
        stock_info = ak.stock_info_a_code_name()
        print(f"[OK] 成功获取 {len(stock_info)} 只股票")
        return stock_info
    except Exception as e:
        print(f"[ERROR] API获取失败: {e}")
        return None

def get_existing_database_stocks(db_path="data/stock_data.db"):
    """从数据库获取已有数据的股票"""
    print("正在从数据库读取已有股票代码...")
    try:
        with sqlite3.connect(db_path) as conn:
            # 获取已有数据的股票代码
            existing_stocks = pd.read_sql("""
                SELECT DISTINCT stock_code as code
                FROM technical_data
                ORDER BY stock_code
            """, conn)
            print(f"[OK] 数据库中有 {len(existing_stocks)} 只股票")
            return existing_stocks
    except Exception as e:
        print(f"[ERROR] 数据库读取失败: {e}")
        return None

def find_missing_stocks():
    """找出缺失的股票"""
    print("="*80)
    print("第一步：对比检查缺失的股票代码")
    print("="*80)

    # 获取API股票列表
    api_stocks_df = get_all_api_stocks()
    if api_stocks_df is None:
        print("无法获取API股票列表，退出")
        return

    # 获取数据库已有股票
    existing_stocks_df = get_existing_database_stocks()
    if existing_stocks_df is None:
        print("无法读取数据库，退出")
        return

    # 对比找出缺失的股票
    api_codes = set(api_stocks_df['code'].tolist())
    existing_codes = set(existing_stocks_df['code'].tolist())
    missing_codes = api_codes - existing_codes

    print(f"\n=== 对比结果 ===")
    print(f"API获取总股票数: {len(api_codes)}")
    print(f"数据库已有股票数: {len(existing_codes)}")
    print(f"缺失股票数: {len(missing_codes)}")

    # 按交易所分类
    def classify_stock(code):
        if code.startswith('920'):
            return '北交所(920xxx)'
        elif code.startswith('689'):
            return 'CDR(689xxx)'
        elif code.startswith('688'):
            return '科创板(688xxx)'
        elif code.startswith('300') or code.startswith('301'):
            return '创业板(30xxxx)'
        elif code.startswith('600') or code.startswith('601') or code.startswith('603') or code.startswith('605'):
            return '沪市主板(60xxxx)'
        elif code.startswith('000') or code.startswith('001') or code.startswith('002') or code.startswith('003'):
            return '深市主板(00xxxx)'
        else:
            return '其他'

    # 分类统计缺失股票
    missing_classified = {}
    for code in missing_codes:
        category = classify_stock(code)
        if category not in missing_classified:
            missing_classified[category] = []
        missing_classified[category].append(code)

    print(f"\n=== 缺失股票分类统计 ===")
    for category, codes in missing_classified.items():
        print(f"{category}: {len(codes)} 只")
        print(f"  示例: {', '.join(codes[:5])}")

    # 生成详细缺失股票清单
    print(f"\n=== 缺失股票详细清单 ===")
    all_missing_sorted = sorted(list(missing_codes))

    for i, code in enumerate(all_missing_sorted, 1):
        # 获取股票名称
        try:
            stock_name = api_stocks_df[api_stocks_df['code'] == code]['name'].iloc[0]
        except:
            stock_name = "未知"

        category = classify_stock(code)
        print(f"{i:4d}. {code} - {stock_name} [{category}]")

        # 每50只股票显示一次分类统计
        if i % 50 == 0:
            print(f"\n--- 已列出 {i} 只，进度: {i/len(all_missing_sorted)*100:.1f}% ---")

    # 保存缺失股票清单到文件
    report_file = f"missing_stocks_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("缺失股票代码检查报告\n")
        f.write("="*50 + "\n")
        f.write(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"API获取总股票数: {len(api_codes)}\n")
        f.write(f"数据库已有股票数: {len(existing_codes)}\n")
        f.write(f"缺失股票总数: {len(missing_codes)}\n")
        f.write(f"数据完整率: {len(existing_codes)/len(api_codes)*100:.2f}%\n\n")

        f.write("缺失股票分类统计:\n")
        for category, codes in missing_classified.items():
            f.write(f"{category}: {len(codes)} 只\n")
            if codes:
                f.write(f"  股票: {', '.join(codes[:10])}\n")
                if len(codes) > 10:
                    f.write(f"  ... 还有 {len(codes) - 10} 只\n")

        f.write("\n详细缺失股票清单:\n")
        for i, code in enumerate(all_missing_sorted, 1):
            try:
                stock_name = api_stocks_df[api_stocks_df['code'] == code]['name'].iloc[0]
            except:
                stock_name = "未知"
            category = classify_stock(code)
            f.write(f"{i:4d}. {code} - {stock_name} [{category}]\n")

        f.write("\n建议补充顺序:\n")
        f.write("1. 优先处理北交所(920xxx)股票\n")
        f.write("2. 然后处理CDR(689xxx)股票\n")
        f.write("3. 最后处理其他A股\n")
        f.write("4. 按交易所分批处理，避免API限制\n")
        f.write("5. 重点关注数据异常股票\n")

    print(f"\n缺失股票清单已保存到: {report_file}")

    return {
        'api_codes': list(api_codes),
        'existing_codes': list(existing_codes),
        'missing_codes': all_missing_sorted,
        'missing_classified': missing_classified
    }

def main():
    """主函数"""
    print("缺失股票代码检查工具")
    print("="*50)
    print("功能:")
    print("1. 从API获取所有A股股票代码")
    print("2. 与数据库现有数据对比")
    print("3. 按交易所分类统计缺失股票")
    print("4. 生成缺失股票详细清单")
    print("5. 保存到报告文件")
    print("="*50)

    try:
        missing_info = find_missing_stocks()

        if missing_info['missing_codes']:
            print(f"\n发现 {len(missing_info['missing_codes'])} 只缺失股票")
            print("已生成详细报告文件")
            print("下一步: 运行数据补充脚本")
        else:
            print("\n✅ 没有发现缺失股票！数据库数据完整")

    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()