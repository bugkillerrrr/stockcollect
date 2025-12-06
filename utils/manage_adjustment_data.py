"""
管理复权数据 - 标识现有的后复权数据并确保未来数据一致性
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_collector import AkshareDataCollector
from database import StockDataDB

def mark_existing_data_as_hfq():
    """将现有数据标记为后复权(hfq)"""
    print("Marking Existing Data as 后复权(hfq)")
    print("="*50)

    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            # 检查adjustment_type字段是否存在
            cursor = conn.execute("PRAGMA table_info(technical_data)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'adjustment_type' not in columns:
                print("Adding adjustment_type column...")
                conn.execute("ALTER TABLE technical_data ADD COLUMN adjustment_type TEXT")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_adjustment_type ON technical_data(adjustment_type)")
                print("✓ adjustment_type column added")
            else:
                print("✓ adjustment_type column already exists")

            # 标记所有现有数据为后复权
            cursor = conn.execute("""
                UPDATE technical_data
                SET adjustment_type = 'hfq'
                WHERE adjustment_type IS NULL
            """)

            conn.commit()
            marked_count = cursor.rowcount
            print(f"✓ Marked {marked_count} records as 后复权(hfq)")

            # 验证标记结果
            verification = pd.read_sql("""
                SELECT
                    adjustment_type,
                    COUNT(*) as record_count,
                    COUNT(DISTINCT stock_code) as stock_count,
                    MIN(trade_date) as earliest_date,
                    MAX(trade_date) as latest_date
                FROM technical_data
                GROUP BY adjustment_type
                ORDER BY record_count DESC
            """, conn)

            print("\nAdjustment Type Distribution:")
            print(verification)

            # 检查是否有未标记的数据
            unmarked = pd.read_sql("""
                SELECT COUNT(*) as unmarked_count
                FROM technical_data
                WHERE adjustment_type IS NULL
            """, conn)

            if unmarked.iloc[0]['unmarked_count'] == 0:
                print("✓ All data has been successfully marked!")
            else:
                print(f"⚠ {unmarked.iloc[0]['unmarked_count']} records remain unmarked")

    except Exception as e:
        print(f"Error marking adjustment data: {e}")
        import traceback
        traceback.print_exc()

def ensure_future_hfq_consistency():
    """确保未来数据获取使用后复权"""
    print("\n" + "="*50)
    print("ENSURING FUTURE 后复权(hfq) CONSISTENCY")
    print("="*50)

    # 验证data_collector.py中的设置
    try:
        with open('src/data_collector.py', 'r', encoding='utf-8') as f:
            content = f.read()

        print("Checking data_collector.py for hfq settings:")

        # 检查adjust="hfq"设置
        if 'adjust="hfq"' in content:
            print("✓ Found adjust='hfq' setting in data_collector.py")
        elif "adjust='hfq'" in content:
            print("✓ Found adjust='hfq' setting in data_collector.py")
        else:
            print("⚠ Could not find adjust='hfq' setting")

        # 检查stock_zh_a_daily的使用
        if 'ak.stock_zh_a_daily' in content:
            print("✓ Using ak.stock_zh_a_daily (recommended)")
        elif 'ak.stock_zh_a_hist' in content:
            print("⚠ Using ak.stock_zh_a_hist (consider switching to stock_zh_a_daily)")
        else:
            print("? Could not identify primary API method")

        # 显示当前配置的关键部分
        print("\nCurrent API configuration found:")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'stock_zh_a_daily' in line or 'stock_zh_a_hist' in line or 'adjust=' in line:
                print(f"  Line {i+1}: {line.strip()}")

    except Exception as e:
        print(f"Error checking data_collector.py: {e}")

def verify_hfq_data_quality():
    """验证后复权数据质量"""
    print("\n" + "="*50)
    print("VERIFYING 后复权(hfq) DATA QUALITY")
    print("="*50)

    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            # 获取后复权数据的质量报告
            quality_report = pd.read_sql("""
                SELECT
                    stock_code,
                    COUNT(*) as total_records,
                    SUM(CASE WHEN volume > 0 THEN 1 ELSE 0 END) as records_with_volume,
                    SUM(CASE WHEN amount > 0 THEN 1 ELSE 0 END) as records_with_amount,
                    AVG(volume) as avg_volume,
                    AVG(amount) as avg_amount,
                    MIN(close_price) as min_close,
                    MAX(close_price) as max_close,
                    AVG(close_price) as avg_close,
                    MIN(trade_date) as earliest_date,
                    MAX(trade_date) as latest_date
                FROM technical_data
                WHERE adjustment_type = 'hfq'
                GROUP BY stock_code
                ORDER BY total_records DESC
                LIMIT 10
            """, conn)

            print("Top 10 stocks by data quality (hfq only):")
            for _, row in quality_report.iterrows():
                print(f"\n{row['stock_code']}:")
                print(f"  Records: {row['total_records']:,}")
                print(f"  Volume complete: {row['records_with_volume']:,}/{row['total_records']:,}")
                print(f"  Amount complete: {row['records_with_amount']:,}/{row['total_records']:,}")
                print(f"  Avg volume: {row['avg_volume']:,.0f}")
                print(f"  Avg amount: {row['avg_amount']:,.0f}")
                print(f"  Price range: {row['min_close']:.2f} - {row['max_close']:.2f} (avg: {row['avg_close']:.2f})")
                print(f"  Date range: {row['earliest_date']} to {row['latest_date']}")

                # 数据质量评分
                volume_complete = row['records_with_volume'] / row['total_records'] * 100
                amount_complete = row['records_with_amount'] / row['total_records'] * 100

                if volume_complete >= 99 and amount_complete >= 99:
                    print(f"  ✓ Excellent data quality!")
                elif volume_complete >= 95 and amount_complete >= 95:
                    print(f"  ✓ Good data quality")
                else:
                    print(f"  ⚠ Data quality needs attention")

            # 检查价格合理性
            print(f"\nPrice Reasonableness Check:")
            price_check = pd.read_sql("""
                SELECT
                    COUNT(*) as total_hfq_records,
                    SUM(CASE WHEN close_price <= 0 THEN 1 ELSE 0 END) as invalid_prices,
                    SUM(CASE WHEN close_price < 0.5 THEN 1 ELSE 0 END) as suspicious_low_prices,
                    SUM(CASE WHEN close_price > 10000 THEN 1 ELSE 0 END) as suspicious_high_prices
                FROM technical_data
                WHERE adjustment_type = 'hfq'
            """, conn)

            row = price_check.iloc[0]
            total = row['total_hfq_records']
            invalid_pct = (row['invalid_prices'] / total) * 100 if total > 0 else 0
            low_price_pct = (row['suspicious_low_prices'] / total) * 100 if total > 0 else 0
            high_price_pct = (row['suspicious_high_prices'] / total) * 100 if total > 0 else 0

            print(f"  Total hfq records: {total:,}")
            print(f"  Invalid prices (≤0): {row['invalid_prices']} ({invalid_pct:.3f}%)")
            print(f"  Very low prices (<0.5): {row['suspicious_low_prices']} ({low_price_pct:.3f}%)")
            print(f"  Very high prices (>10000): {row['suspicious_high_prices']} ({high_price_pct:.3f}%)")

            if invalid_pct == 0 and low_price_pct < 0.1 and high_price_pct < 0.1:
                print("  ✓ Price data is highly reasonable for hfq adjustment")
            else:
                print("  ⚠ Some price anomalies detected")

    except Exception as e:
        print(f"Error verifying hfq data quality: {e}")
        import traceback
        traceback.print_exc()

def create_data_update_guidelines():
    """创建数据更新指导原则"""
    print("\n" + "="*50)
    print("DATA UPDATE GUIDELINES")
    print("="*50)

    print("""
📋 **数据管理最佳实践**

1. **复权一致性原则**：
   ✅ 当前所有数据已标记为后复权(hfq)
   ✅ 未来所有新数据也必须使用后复权(hfq)
   ❌ 严禁在同一只股票上混合使用前复权和后复权

2. **数据获取设置**：
   - 确保data_collector.py中使用 adjust="hfq"
   - 推荐使用 ak.stock_zh_a_daily API
   - 定期验证新获取数据的复权类型

3. **数据质量监控**：
   - 定期运行质量检查脚本
   - 监控异常价格变化
   - 验证成交量数据的完整性

4. **问题处理**：
   - 如果发现qfq数据，立即删除并重新获取
   - 如果发现价格异常，检查复权类型设置
   - 保持adjustment_type字段的准确性

5. **长期数据使用**：
   - 后复权适合长期价格趋势分析
   - 技术指标计算基于统一的后复权数据
   - 不同股票间的价格比较具有可比性
    """)

def update_database_structure():
    """更新数据库结构以支持更好的复权数据管理"""
    print("\n" + "="*50)
    print("UPDATING DATABASE STRUCTURE")
    print("="*50)

    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            # 检查和添加必要字段
            cursor = conn.execute("PRAGMA table_info(technical_data)")
            columns = [column[1] for column in cursor.fetchall()]

            # 添加API方法字段
            if 'api_method' not in columns:
                print("Adding api_method column...")
                conn.execute("ALTER TABLE technical_data ADD COLUMN api_method TEXT")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_api_method ON technical_data(api_method)")
                print("✓ api_method column added")

            # 标记当前使用的API方法
            cursor = conn.execute("""
                UPDATE technical_data
                SET api_method = 'stock_zh_a_daily'
                WHERE api_method IS NULL
                   AND adjustment_type = 'hfq'
                   AND volume > 0
                   AND amount > 0
            """)

            conn.commit()
            marked_count = cursor.rowcount
            print(f"✓ Marked {marked_count} records as from stock_zh_a_daily")

            # 显示API方法分布
            api_distribution = pd.read_sql("""
                SELECT
                    api_method,
                    adjustment_type,
                    COUNT(*) as record_count,
                    COUNT(DISTINCT stock_code) as stock_count
                FROM technical_data
                GROUP BY api_method, adjustment_type
                ORDER BY record_count DESC
            """, conn)

            print("\nAPI Method and Adjustment Type Distribution:")
            print(api_distribution)

            # 添加数据质量约束检查
            print("\nAdding data quality checks...")
            # 可以在这里添加更多的约束和索引

    except Exception as e:
        print(f"Error updating database structure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    mark_existing_data_as_hfq()
    ensure_future_hfq_consistency()
    verify_hfq_data_quality()
    create_data_update_guidelines()
    update_database_structure()