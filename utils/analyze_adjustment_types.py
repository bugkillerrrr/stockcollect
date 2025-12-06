"""
分析数据库中的复权数据类型（前复权qfq vs 后复权hfq）
"""
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import StockDataDB

def detect_adjustment_type_by_data_pattern():
    """通过数据模式检测复权类型"""
    print("Detecting Adjustment Types by Data Patterns")
    print("="*60)

    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            # 分析股票的价格走势模式来推断复权类型
            print("1. Price Pattern Analysis (Detecting hfq vs qfq):")

            # 获取几只代表性股票的数据
            sample_stocks = ["000001", "000002", "600000"]

            for stock_code in sample_stocks:
                print(f"\nAnalyzing {stock_code}:")

                # 获取该股票的最早和最新数据
                stock_data = pd.read_sql("""
                    SELECT
                        trade_date,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume,
                        amount
                    FROM technical_data
                    WHERE stock_code = ?
                    ORDER BY trade_date ASC
                """, conn, params=[stock_code])

                if len(stock_data) == 0:
                    print(f"  No data for {stock_code}")
                    continue

                print(f"  Data range: {stock_data['trade_date'].min()} to {stock_data['trade_date'].max()}")
                print(f"  Total records: {len(stock_data)}")

                # 价格走势分析
                first_price = stock_data.iloc[0]['close_price']
                last_price = stock_data.iloc[-1]['close_price']
                price_change_pct = (last_price - first_price) / first_price * 100

                print(f"  Price change: {first_price:.2f} → {last_price:.2f} ({price_change_pct:+.2f}%)")

                # 检测除权除息日（价格跳跃）
                stock_data['price_change'] = stock_data['close_price'].pct_change()
                large_gaps = stock_data[abs(stock_data['price_change']) > 0.15]  # >15%的单日变化

                print(f"  Large price gaps (>15%): {len(large_gaps)} days")
                if len(large_gaps) > 0:
                    print(f"  Sample gaps:")
                    for _, row in large_gaps.head(3).iterrows():
                        print(f"    {row['trade_date']}: {row['price_change']:+.2%}")

                # 检测前复权特征
                # 前复权(qfq): 早期价格会被调整，历史价格可能看起来"不真实"
                # 后复权(hfq): 保持历史价格的真实性，只调整后续价格

                if len(stock_data) > 100:  # 有足够数据时才分析
                    # 计算平均成交量
                    avg_volume = stock_data['volume'].mean()
                    avg_amount = stock_data['amount'].mean()

                    print(f"  Average volume: {avg_volume:,.0f}")
                    print(f"  Average amount: {avg_amount:,.0f}")

                    # 检测数据一致性
                    # 如果早期价格很"奇怪"（比如在2018年的股票价格很低），可能是前复权
                    early_2018_data = stock_data[stock_data['trade_date'] < '2019-01-01']
                    if len(early_2018_data) > 0:
                        early_avg_close = early_2018_data['close_price'].mean()
                        print(f"  2018 average close: {early_avg_close:.2f}")

                        # 如果是深交所主板股票，2018年平均价格过低可能表示前复权
                        if stock_code.startswith('00') and early_avg_close < 5:
                            print(f"  ⚠ Possible qfq (前复权): Very low 2018 average price")
                        elif stock_code.startswith('00') and early_avg_close > 15:
                            print(f"  ✓ Possible hfq (后复权): Reasonable 2018 average price")
                        else:
                            print(f"  ? Unclear adjustment type from price level")

    except Exception as e:
        print(f"Error in pattern analysis: {e}")
        import traceback
        traceback.print_exc()

def analyze_data_creation_timeline():
    """分析数据创建时间线来识别可能的复权类型变更"""
    print("\n" + "="*60)
    print("Data Creation Timeline Analysis")
    print("="*60)

    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            # 获取数据创建的时间分布
            creation_analysis = pd.read_sql("""
                SELECT
                    DATE(created_at) as creation_date,
                    COUNT(*) as records_added,
                    COUNT(DISTINCT stock_code) as unique_stocks,
                    MIN(trade_date) as earliest_trade_date,
                    MAX(trade_date) as latest_trade_date
                FROM technical_data
                WHERE created_at IS NOT NULL
                GROUP BY DATE(created_at)
                ORDER BY creation_date DESC
            """, conn)

            print("Data creation by date:")
            for _, row in creation_analysis.iterrows():
                print(f"  {row['creation_date']}: +{row['records_added']} records, {row['unique_stocks']} stocks")
                if row['earliest_trade_date']:
                    print(f"    Trade range: {row['earliest_trade_date']} to {row['latest_trade_date']}")

            # 检查最近的数据更新（可能使用了新的API和复权类型）
            print(f"\nRecent detailed analysis:")
            recent_data = pd.read_sql("""
                SELECT
                    stock_code,
                    created_at,
                    trade_date,
                    open_price,
                    close_price,
                    volume,
                    amount
                FROM technical_data
                WHERE DATE(created_at) = (
                    SELECT MAX(DATE(created_at)) FROM technical_data WHERE created_at IS NOT NULL
                )
                ORDER BY stock_code, trade_date
            """, conn)

            if len(recent_data) > 0:
                print(f"Most recent data batch ({recent_data['created_at'].iloc[0]}):")
                recent_stocks = recent_data['stock_code'].unique()
                print(f"  Stocks updated: {len(recent_stocks)}")
                print(f"  Stock codes: {list(recent_stocks[:10])}")

                # 分析最近数据的特征
                sample_stock = recent_stocks[0] if len(recent_stocks) > 0 else None
                if sample_stock:
                    stock_sample = recent_data[recent_data['stock_code'] == sample_stock]
                    if len(stock_sample) > 0:
                        print(f"  Sample {sample_stock} recent data:")
                        print(f"    First record: {stock_sample['trade_date'].min()}, Close: {stock_sample['close_price'].iloc[0]:.2f}")
                        print(f"    Last record: {stock_sample['trade_date'].max()}, Close: {stock_sample['close_price'].iloc[-1]:.2f}")

    except Exception as e:
        print(f"Error in timeline analysis: {e}")
        import traceback
        traceback.print_exc()

def check_historical_price_reasonableness():
    """检查历史价格的合理性来推断复权类型"""
    print("\n" + "="*60)
    print("Historical Price Reasonableness Check")
    print("="*60)

    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            # 获取各年份的平均价格数据
            yearly_analysis = pd.read_sql("""
                SELECT
                    stock_code,
                    STRFTIME('%Y', trade_date) as year,
                    AVG(close_price) as avg_close_price,
                    MIN(close_price) as min_close_price,
                    MAX(close_price) as max_close_price,
                    COUNT(*) as trading_days
                FROM technical_data
                GROUP BY stock_code, STRFTIME('%Y', trade_date)
                HAVING trading_days > 100  -- 只分析有足够交易日的年份
                ORDER BY stock_code, year
            """, conn)

            if len(yearly_analysis) == 0:
                print("No yearly data available for analysis")
                return

            print("Yearly average close prices by stock:")
            for stock_code in yearly_analysis['stock_code'].unique()[:5]:  # 分析前5只股票
                stock_yearly = yearly_analysis[yearly_analysis['stock_code'] == stock_code]

                print(f"\n{stock_code}:")
                for _, row in stock_yearly.iterrows():
                    print(f"  {row['year']}: avg={row['avg_close_price']:.2f}, range={row['min_close_price']:.2f}-{row['max_close_price']:.2f}")

                # 价格趋势分析
                if len(stock_yearly) >= 3:
                    early_avg = stock_yearly.iloc[0]['avg_close_price']  # 最早的年份
                    latest_avg = stock_yearly.iloc[-1]['avg_close_price']  # 最新的年份
                    trend_pct = (latest_avg - early_avg) / early_avg * 100

                    print(f"  Price trend: {trend_pct:+.2f}% from {stock_yearly.iloc[0]['year']} to {stock_yearly.iloc[-1]['year']}")

                    # 推断复权类型
                    if abs(trend_pct) > 50:  # 价格变化超过50%
                        if trend_pct > 0:
                            print(f"  ⚠ Possible qfq (前复权): Large upward trend")
                        else:
                            print(f"  ⚠ Possible qfq (前复权): Large downward trend")
                    else:
                        print(f"  ✓ Possible hfq (后复权): Reasonable price trend")

            # 检查异常低价
            print(f"\nUnusual low prices (possible qfq adjustment):")
            low_prices = pd.read_sql("""
                SELECT
                    stock_code,
                    trade_date,
                    close_price,
                    amount
                FROM technical_data
                WHERE close_price < 1.0  -- 价格低于1元
                ORDER BY close_price ASC
                LIMIT 20
            """, conn)

            if len(low_prices) > 0:
                print("Found extremely low prices:")
                for _, row in low_prices.iterrows():
                    print(f"  {row['stock_code']} {row['trade_date']}: {row['close_price']:.4f}")
                print("  ⚠ These very low prices suggest qfq (前复权) adjustment")
            else:
                print("✓ No extremely low prices found (suggests hfq)")

    except Exception as e:
        print(f"Error in price reasonableness check: {e}")
        import traceback
        traceback.print_exc()

def suggest_adjustment_management():
    """提供复权数据管理建议"""
    print("\n" + "="*60)
    print("ADJUSTMENT TYPE MANAGEMENT SUGGESTIONS")
    print("="*60)

    print("""
建议的复权数据处理策略：

1. **识别现有数据的复权类型**：
   - 前复权(qfq): 历史价格可能很"奇怪"，早期价格过低或过高
   - 后复权(hfq): 保持历史价格真实性，推荐用于长期分析

2. **数据一致性要求**：
   - 同一只股票不能混合使用qfq和hfq数据
   - 不同股票之间可以使用不同的复权类型，但需要在分析时统一
   - 技术指标计算必须基于相同的复权类型

3. **清理建议**：
   - 确定主要使用哪种复权类型（推荐hfq用于长期分析）
   - 删除或重新获取不一致的数据
   - 在数据库中添加复权类型标识字段

4. **未来数据获取**：
   - 统一使用一种复权类型（hfq或qfq）
   - 在数据库中记录每次获取的复权类型
   - 定期检查数据一致性
    """)

    # 检查是否需要添加复权类型字段
    db = StockDataDB()

    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(technical_data)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'adjustment_type' not in columns:
                print(f"\n建议添加复权类型标识字段到数据库：")
                print("ALTER TABLE technical_data ADD COLUMN adjustment_type TEXT")
                print("CREATE INDEX idx_adjustment_type ON technical_data(adjustment_type)")
            else:
                print(f"\n✓ 数据库已包含adjustment_type字段")

    except Exception as e:
        print(f"Error checking for adjustment_type field: {e}")

if __name__ == "__main__":
    detect_adjustment_type_by_data_pattern()
    analyze_data_creation_timeline()
    check_historical_price_reasonableness()
    suggest_adjustment_management()