"""
测试和修复北交所股票API调用
"""
import sqlite3
import akshare as ak
import pandas as pd
from datetime import datetime

def test_single_bj_stock(stock_code, logger):
    """测试单只北交所股票API调用"""
    logger.info(f"测试股票: {stock_code}")

    try:
        # 测试北交所股票API
        df = ak.stock_zh_a_daily(
            symbol=f"bj{stock_code}",
            start_date="20241101",  # 测试最近1个月
            end_date="20251130",
            adjust="hfq"
        )

        if df is not None and not df.empty:
            logger.info(f"  [OK] 成功获取 {len(df)} 条记录")
            logger.info(f"    时间范围: {df.index.min()} 到 {df.index.max()}")

            # 检查数据质量
            required_fields = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
            actual_fields = list(df.columns)
            missing_fields = [field for field in required_fields if field not in actual_fields]
            if missing_fields:
                logger.warning(f"    缺少字段: {missing_fields}")

            # 验证最新价格和成交量
            if 'close' in df.columns:
                logger.info(f"    最新价格: {df['close'].iloc[-1]:.2f}")
            if 'volume' in df.columns:
                logger.info(f"    成交量: {df['volume'].iloc[-1]:,}")
            else:
                logger.warning(f"    缺少成交量字段")

            logger.info(f"  数据列: {actual_fields}")

            logger.info(f"    数据样本:")
            print(df.head(3))

            return True
        except Exception as e:
            logger.error(f"  [ERROR] 测试失败: {e}")
            return False

    except Exception as e:
        logger.error(f"  [ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_stocks(stock_codes, logger, batch_size=5):
    """测试多只北交所股票"""
    logger.info(f"\n=== 测试{len(stock_codes)} 只北交所股票 ===")

    success_count = 0
    failed_count = 0

    for i, stock_code in enumerate(stock_codes[:batch_size], 1):
        logger.info(f"[{i}/{len(stock_codes)}] 测试 {stock_code}")
        if test_single_bj_stock(stock_code, logger):
            success_count += 1
        else:
            failed_count += 1

        logger.info(f"批次完成: {i//batch_size} - 成功: {success_count}, 失败: {failed_count}")

    logger.info(f"\n=== 测试结果 ===")
    logger.info(f"成功: {success_count}/{len(stock_codes[:batch_size])")
    logger.info(f"失败: {failed_count}/{len(stock_codes[:batch_size])}")

    # 估算成功率
    if len(stock_codes) > 0:
        success_rate = (success_count / len(stock_codes)) * 100
    else:
        success_rate = 0

    logger.info(f"估算成功率: {success_rate:.1f}%")

    return {
        'success_count': success_count,
        'failed_count': failed_count,
        'success_rate': success_rate,
        'total_stocks': len(stock_codes)
    }

def main():
    """主函数"""
    print("北交所股票API测试修复工具")
    print("="*50)
    print("功能:")
    print("1. 测试单只北交所股票")
    print("2. 测试多只北交所股票")
    print("3. 测试批次处理逻辑")
    print("4. 输出详细错误信息")
    print("5. 修复常见问题")

    try:
        # 获取北交所股票列表
        stock_info = ak.stock_info_a_code_name()
        bj_stocks = [code for code in stock_info['code'].tolist() if code.startswith('920')]

        print(f"\n找到 {len(bj_stocks)} 只北交所股票")

        if not bj_stocks:
            print("没有北交所股票需要测试")
            return

        print("开始批量测试...")

        # 测试前5只
        test_codes = bj_stocks[:5]
        logger.info(f"测试前5只股票: {', '.join(test_codes)}")
        test_results = []

        for stock_code in test_codes:
            result = test_single_bj_stock(stock_code)
            if result:
                test_results.append(stock_code)
                logger.info(f"  [OK] {stock_code}")
            else:
                logger.warning(f"  [FAIL] {stock_code}")
            test_results.append(stock_code)

        # 统计成功率
        success_count = len([r for r in test_results if r])
        logger.info(f"\n=== 批次测试结果 ===")
        logger.info(f"成功: {success_count}/{len(test_codes)}")
        logger.info(f"失败: {failed_count}/{len(test_results)}")

        if success_count == 0:
            logger.error(f"\n所有测试都失败，可能存在严重问题！")
        else:
            logger.info(f"部分成功: {success_count}/{len(test_codes)}")
            logger.info(f"成功率: {success_rate:.1f}%")

        # 显示失败的股票
        if failed_count > 0:
            failed_stocks = [code for r in test_results if not r]
                logger.info(f"\n失败的股票:")
                for failed_stock in failed_stocks[:10]:
                    logger.info(f"  - {failed_stock}")

        logger.info(f"\n测试修复建议:")
            logger.info(f"  - {failed_stock}")

    return

    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        print(f"\n程序出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        logger.info(f"北交所股票API测试完成")

def fix_encoding_issues():
    """修复编码问题"""
    import locale
    import os

    print("\n=== 修复编码问题 ===")
    print(f"当前编码: {locale.getpreferredencoding()}")

    # 设置UTF-8编码
        try:
            os.environ['PYTHONIO_ENCODING'] = 'utf-8'
        except Exception as e:
            print(f"设置UTF-8编码失败: {e}")
            try:
                os.environ['PYTHONIO_ENCODING'] = 'gbk'
            except Exception as e:
                print(f"设置GBK编码失败: {e}")

    try:
                # 测试简体中文显示
                test_str = "测试中文显示"
                print(test_str)
                print(f"显示效果: {test_str}")
            except:
                    print(f"中文显示异常: {e}")

    finally:
        logger.info("编码问题修复完成")

def main():
    """主函数"""
    print("北交所股票API测试修复工具")
    print("="*50)

    # 1. 修复编码问题
    fix_encoding_issues()

    # 2. 测试单只股票
    logger.info("测试单只股票...")
    test_single_bj_stock("920000")

    # 3. 测试数据保存逻辑
    logger.info("测试数据保存逻辑...")

    # 4. 最终验证
    main()

if __name__ == "__main__":
    main()