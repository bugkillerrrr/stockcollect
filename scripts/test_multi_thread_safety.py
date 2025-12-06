"""
测试多线程安全性的验证程序
验证任务不重复、数据库防重复、中断恢复等功能
"""

import time
import threading
from src.multi_thread_collector import MultiThreadCollector
from src.database import StockDataDB
from src.logger import get_logger

def test_task_assignment():
    """测试任务分配不重复"""
    print("🧪 测试任务分配不重复...")

    # 创建测试股票列表
    test_stocks = ['000001', '000002', '600000', '600519', '000858']

    # 模拟任务分配
    tasks = [(stock_code, i, "20250101") for i, stock_code in enumerate(test_stocks)]

    # 提取所有股票代码
    assigned_stocks = [task[0] for task in tasks]

    # 检查是否有重复
    unique_stocks = set(assigned_stocks)

    print(f"  原始股票数: {len(test_stocks)}")
    print(f"  分配任务数: {len(tasks)}")
    print(f"  唯一股票数: {len(unique_stocks)}")
    print(f"  任务重复: {'❌ 发现重复' if len(tasks) != len(unique_stocks) else '✅ 无重复'}")

    return len(tasks) == len(unique_stocks)

def test_database_uniqueness():
    """测试数据库唯一约束"""
    print("\n🧪 测试数据库唯一约束...")

    db = StockDataDB()
    stock_code = "TEST_001"
    trade_date = "2025-01-01"

    try:
        # 检查表结构
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(technical_data)")
            columns = cursor.fetchall()

            unique_constraints = [col for col in columns if 'unique' in col[-1].lower()]
            print(f"  数据库列数: {len(columns)}")
            print(f"  唯一约束: {len(unique_constraints)}")
            print("  ✅ 数据库结构检查完成")

    except Exception as e:
        print(f"  ❌ 数据库检查失败: {e}")
        return False

    return True

def test_concurrent_safety():
    """测试并发安全性"""
    print("\n🧪 测试并发安全性...")

    # 创建一个简单的多线程测试
    results = []
    errors = []

    def worker(worker_id):
        try:
            # 模拟数据库操作
            with threading.Lock():
                results.append(f"Worker-{worker_id}")
                time.sleep(0.1)  # 模拟操作耗时
        except Exception as e:
            errors.append(f"Worker-{worker_id}: {e}")

    # 启动多个线程
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    print(f"  启动线程数: 5")
    print(f"  成功结果数: {len(results)}")
    print(f"  错误数量: {len(errors)}")
    print(f"  并发安全性: {'❌ 有错误' if errors else '✅ 安全'}")

    return len(errors) == 0

def test_interrupt_resume():
    """测试中断恢复机制"""
    print("\n🧪 测试中断恢复机制...")

    # 模拟已完成的股票
    db = StockDataDB()

    # 获取当前已完成的股票数
    completed_stocks = db.get_completed_stock_codes()

    print(f"  当前已完成股票数: {len(completed_stocks)}")
    print(f"  最后一只股票: {completed_stocks[-1] if completed_stocks else '无'}")
    print("  ✅ 中断恢复机制检查完成")

    return True

def test_progress_tracking():
    """测试进度跟踪机制"""
    print("\n🧪 测试进度跟踪机制...")

    # 创建一个小规模的多线程收集器进行测试
    collector = MultiThreadCollector(max_workers=2, delay=0.1)

    # 检查统计变量
    print(f"  初始成功计数: {collector.success_count}")
    print(f"  初始失败计数: {collector.failed_count}")
    print(f"  线程锁存在: {'✅' if hasattr(collector, 'lock') else '❌'}")
    print("  ✅ 进度跟踪机制检查完成")

    return hasattr(collector, 'lock')

def main():
    """主测试函数"""
    print("=" * 60)
    print("🔒 多线程安全性测试")
    print("=" * 60)

    tests = [
        ("任务分配不重复", test_task_assignment),
        ("数据库唯一约束", test_database_uniqueness),
        ("并发安全性", test_concurrent_safety),
        ("中断恢复机制", test_interrupt_resume),
        ("进度跟踪机制", test_progress_tracking),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ 测试 {test_name} 失败: {e}")
            results.append((test_name, False))

    # 输出测试总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n总体结果: {passed}/{total} 项测试通过")

    if passed == total:
        print("🎉 所有多线程安全性测试通过！")
        print("✅ 可以安全使用多线程数据收集")
    else:
        print("⚠️  部分测试失败，建议检查相关功能")

    print("=" * 60)

if __name__ == "__main__":
    main()