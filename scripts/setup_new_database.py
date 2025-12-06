"""
设置新数据库并配置复权类型
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database_new import StockDataNewDB
from data_collector_new import AkshareDataCollectorNew

def setup_new_database():
    """设置新的数据库"""
    print("设置新股票数据库")
    print("="*60)

    # 初始化新数据库
    print("1. 初始化新数据库...")
    db = StockDataNewDB()
    print("✓ 新数据库初始化完成")

    # 显示当前设置
    print("\n2. 当前数据库设置:")
    current_settings = db.get_current_settings()
    for key, value in current_settings.items():
        print(f"  {key}: {value}")

    # 显示数据库信息
    print("\n3. 数据库信息:")
    db_info = db.get_database_info()
    for key, value in db_info.items():
        print(f"  {key}: {value}")

    print("\n✓ 新数据库设置完成!")

def configure_data_collection(adjustment_type: str = 'hfq', api_method: str = 'stock_zh_a_daily'):
    """配置数据收集设置"""
    print(f"\n配置数据收集设置")
    print("="*60)

    # 初始化数据库和收集器
    db = StockDataNewDB()
    collector = AkshareDataCollectorNew(db)

    # 设置复权类型
    collector.update_settings(adjustment_type=adjustment_type, api_method=api_method)

    # 显示更新后的设置
    print("\n更新后的设置:")
    collector.print_current_settings()

    print(f"\n✓ 配置完成!")
    print(f"  复权类型: {adjustment_type}")
    print(f"  API方法: {api_method}")

    return collector, db

def test_configuration(collector: AkshareDataCollectorNew):
    """测试配置"""
    print(f"\n测试配置")
    print("="*60)

    # 测试股票
    test_stock = "000001"
    start_date = "20240101"
    end_date = "20240131"

    print(f"测试获取 {test_stock} 数据...")
    success = collector.get_and_save_single_stock(test_stock, start_date, end_date)

    if success:
        print(f"✓ 测试成功!")
        # 显示数据库信息
        db_info = collector.db.get_database_info()
        print(f"  新数据库记录数: {db_info.get('new_technical_data_count', 0)}")

        # 显示复权类型汇总
        summary = collector.db.get_adjustment_summary()
        print(f"\n复权类型汇总:")
        print(summary)
    else:
        print(f"✗ 测试失败!")

def main():
    """主函数"""
    print("新股票数据系统设置")
    print("="*60)

    # 设置数据库
    setup_new_database()

    # 获取用户配置选择
    print(f"\n请选择配置:")
    print("1. 后复权(hfq) + stock_zh_a_daily (推荐，数据完整)")
    print("2. 前复权(qfq) + stock_zh_a_daily (适合短线交易)")
    print("3. 后复权(hfq) + stock_zh_a_hist (备选API)")
    print("4. 前复权(qfq) + stock_zh_a_hist (备选API)")

    try:
        choice = input(f"\n请输入选择 (1-4): ").strip()

        config_map = {
            '1': ('hfq', 'stock_zh_a_daily'),
            '2': ('qfq', 'stock_zh_a_daily'),
            '3': ('hfq', 'stock_zh_a_hist'),
            '4': ('qfq', 'stock_zh_a_hist')
        }

        if choice in config_map:
            adjustment_type, api_method = config_map[choice]

            print(f"\n你选择了: 复权类型={adjustment_type}, API方法={api_method}")

            # 配置数据收集
            collector, db = configure_data_collection(adjustment_type, api_method)

            # 测试配置
            test_configuration(collector)

            print(f"\n" + "="*60)
            print("✓ 新数据库配置完成!")
            print(f"  数据库路径: data/stock_data_new.db")
            print(f"  复权类型: {adjustment_type}")
            print(f"  API方法: {api_method}")
            print(f"  你现在可以开始数据获取了!")

            # 提供使用说明
            print(f"\n使用说明:")
            print(f"1. 数据获取示例:")
            print(f"   python -c \"import sys; import os;")
            print(f"   sys.path.append('src');")
            print(f"   from database_new import StockDataNewDB;")
            print(f"   from data_collector_new import AkshareDataCollectorNew;")
            print(f"   db = StockDataNewDB();")
            print(f"   collector = AkshareDataCollectorNew(db, adjustment_type='{adjustment_type}');")
            print(f"   collector.get_and_save_single_stock('000001', '20240101', '20240131');\"")

        else:
            print("无效的选择，请重新运行脚本")

    except KeyboardInterrupt:
        print(f"\n操作已取消")
    except Exception as e:
        print(f"配置出错: {e}")

if __name__ == "__main__":
    main()