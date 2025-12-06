#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据完整性检查工具
对比API获取的股票列表和数据库中实际有数据的股票
"""

def check_stock_completeness():
    """检查股票数据完整性"""
    print("=== 股票数据完整性检查工具 ===")

    try:
        # 读取股票列表
        with open('db_stocks.txt', 'r', encoding='utf-8') as f:
            db_stocks = [line.strip() for line in f if line.strip()]

        with open('api_stocks.txt', 'r', encoding='utf-8') as f:
            api_stocks = [line.strip() for line in f if line.strip()]

        # 转换为集合进行对比
        db_set = set(db_stocks)
        api_set = set(api_stocks)

        # 找出差异
        missing_stocks = api_set - db_set  # API有但数据库没有的
        extra_stocks = db_set - api_set    # 数据库有但API没有的（可能已退市）

        print(f'\n=== 股票数据完整性对比结果 ===')
        print(f'API获取总数: {len(api_set)}')
        print(f'数据库有数据: {len(db_set)}')
        print(f'缺失股票数: {len(missing_stocks)}')
        print(f'多余股票数: {len(extra_stocks)}')

        if len(api_set) > 0:
            print(f'数据完整率: {len(db_set) / len(api_set) * 100:.2f}%')

        # 详细分析缺失股票
        if missing_stocks:
            missing_list = sorted(list(missing_stocks))
            print(f'\n=== 缺失数据的股票代码 ({len(missing_list)}只) ===')

            # 按市场分组统计缺失股票
            market_stats = {}
            for code in missing_list:
                if len(code) >= 6:
                    prefix = code[0]
                    market_stats[prefix] = market_stats.get(prefix, 0) + 1

            print('按市场分组统计:')
            for market, count in sorted(market_stats.items()):
                print(f'  {market}xxx: {count} 只')

            # 显示前50只缺失股票
            print(f'\n前50只缺失股票:')
            for i, code in enumerate(missing_list[:50], 1):
                print(f'  {i:3d}. {code}')

            if len(missing_list) > 50:
                print(f'  ... 还有 {len(missing_list) - 50} 只未显示')

            # 保存缺失股票列表
            with open('missing_stocks.txt', 'w', encoding='utf-8') as f:
                for code in missing_list:
                    f.write(f'{code}\n')

            print(f'\n缺失股票列表已保存到: missing_stocks.txt')

        # 分析多余股票
        if extra_stocks:
            extra_list = sorted(list(extra_stocks))
            print(f'\n=== 数据库中多余的股票 ({len(extra_list)}只，可能已退市) ===')

            # 按市场分组统计多余股票
            market_stats = {}
            for code in extra_list:
                if len(code) >= 6:
                    prefix = code[0]
                    market_stats[prefix] = market_stats.get(prefix, 0) + 1

            print('按市场分组统计:')
            for market, count in sorted(market_stats.items()):
                print(f'  {market}xxx: {count} 只')

            # 显示前20只多余股票
            print(f'\n前20只多余股票:')
            for i, code in enumerate(extra_list[:20], 1):
                print(f'  {i:3d}. {code}')

            if len(extra_list) > 20:
                print(f'  ... 还有 {len(extra_list) - 20} 只未显示')

            # 保存多余股票列表
            with open('extra_stocks.txt', 'w', encoding='utf-8') as f:
                for code in extra_list:
                    f.write(f'{code}\n')

            print(f'\n多余股票列表已保存到: extra_stocks.txt')

        print(f'\n=== 重点关注建议 ===')
        if missing_stocks:
            print('1. 优先处理主板股票缺失问题:')
            print('   - 000xxx: 深交所主板')
            print('   - 002xxx: 深交所中小板')
            print('   - 600xxx, 601xxx, 603xxx: 上交所主板')
            print('   - 688xxx: 科创板')
            print('   - 920xxx: 北交所')

            # 统计各板块股票缺失情况
            main_board_missing = [code for code in missing_stocks if code.startswith(('000', '002', '600', '601', '603'))]
            if main_board_missing:
                print(f'   主板股票缺失: {len(main_board_missing)} 只')

            科创板_missing = [code for code in missing_stocks if code.startswith('688')]
            if 科创板_missing:
                print(f'   科创板股票缺失: {len(科创板_missing)} 只')

            北交所_missing = [code for code in missing_stocks if code.startswith('920')]
            if 北交所_missing:
                print(f'   北交所股票缺失: {len(北交所_missing)} 只')

        print(f'\n2. 建议处理步骤:')
        print(f'   a) 重新获取缺失股票的历史数据')
        print(f'   b) 清理已退市的股票数据')
        print(f'   c) 建立定期数据完整性检查机制')

        return {
            'api_total': len(api_set),
            'db_total': len(db_set),
            'missing_count': len(missing_stocks),
            'extra_count': len(extra_stocks),
            'missing_stocks': sorted(list(missing_stocks)),
            'extra_stocks': sorted(list(extra_stocks))
        }

    except FileNotFoundError as e:
        print(f"文件未找到: {e}")
        print("请先运行数据收集脚本生成 db_stocks.txt 和 api_stocks.txt")
        return None
    except Exception as e:
        print(f"检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    result = check_stock_completeness()

    if result:
        if result['missing_count'] > 0:
            print(f"\n=== 需要重点关注的缺失股票 ===")
            missing_stocks = result['missing_stocks'][:50]  # 前50只
            print(" ".join(missing_stocks))
            print(f"\n建议:")
            print(f"1. 共有 {result['missing_count']} 只股票缺失数据")
            print("2. 检查这些股票是否正常交易")
            print("3. 重新获取这些股票的完整历史数据")
            print("4. 优先处理主板股票(000xxx、002xxx、600xxx、601xxx等)")
        elif result['missing_count'] == 0:
            print("\n✅ 所有股票数据完整，无缺失")

        if result['extra_count'] > 0:
            print(f"\n=== 数据库中的多余股票 ===")
            print(f"共有 {result['extra_count']} 只股票可能在API中已不存在（可能已退市）")
            print("建议检查这些股票是否已退市，并考虑清理相关数据")
    else:
        print("\n❌ 检查失败")

if __name__ == "__main__":
    main()