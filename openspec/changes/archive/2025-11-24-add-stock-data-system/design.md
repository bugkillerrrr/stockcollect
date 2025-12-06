# 股票数据系统设计文档（基于Akshare+SQLite单机版）

## 背景
学生量化交易者在单机环境下构建股票数据系统，基于Akshare数据源和SQLite数据库，支持技术数据（价格、成交量）和财会数据（财务报表）的收集、存储和联合分析。

## 目标
- 使用Akshare作为主要数据源，简化数据获取
- 基于SQLite构建轻量级本地数据库，单机完全可用
- 实现技术数据和财会数据的有效关联和统一查询
- 提供简单易用的数据更新和维护机制
- 支持量化策略的基础回测需求

## 非目标
- 不支持实时高频交易数据
- 不构建复杂的分布式系统
- 不依赖付费数据源或外部数据库

## 核心设计决策

### 1. 基于Akshare的数据获取策略

#### 为什么选择Akshare
- **完全免费：** 无需token或付费
- **数据丰富：** 支持股票、期货、财务等多种数据
- **维护活跃：** 社区驱动，更新及时
- **文档完善：** 使用简单，示例丰富
- **反爬友好：** 内置了合理的请求控制

#### Akshare使用策略
```python
import akshare as ak
import time
import random

class AkshareDataCollector:
    def __init__(self):
        self.request_interval = 0.5  # 请求间隔（秒）
        self.max_retries = 3

    def get_stock_data(self, stock_code, start_date, end_date):
        """获取股票历史数据"""
        try:
            time.sleep(self.request_interval + random.uniform(0, 0.2))
            data = ak.stock_zh_a_hist(symbol=stock_code,
                                    period="daily",
                                    start_date=start_date,
                                    end_date=end_date)
            return data
        except Exception as e:
            return self.handle_error(e)

    def get_financial_data(self, stock_code, period):
        """获取财务数据"""
        try:
            time.sleep(self.request_interval + random.uniform(0, 0.2))
            data = ak.stock_financial_analysis_indicator(symbol=stock_code, period=period)
            return data
        except Exception as e:
            return self.handle_error(e)
```

#### 简单的反爬虫应对
- **固定延迟：** 每次请求间隔0.5-0.7秒
- **随机因子：** 避免规律性请求
- **错误重试：** 网络错误自动重试3次
- **异常处理：** 优雅处理API异常

### 2. SQLite数据库设计

#### 数据库完全本地化
```python
import sqlite3
import pandas as pd

class StockDataDB:
    def __init__(self, db_path="stock_data.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            # 股票基础信息表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_master (
                    stock_code TEXT PRIMARY KEY,
                    stock_name TEXT,
                    industry TEXT,
                    market TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 技术数据表 - 基础原始数据
            conn.execute("""
                CREATE TABLE IF NOT EXISTS technical_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT,
                    trade_date TEXT,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    close_price REAL,
                    volume INTEGER,
                    amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, trade_date)
                )
            """)

            # 技术指标表 - 可扩展的指标存储
            conn.execute("""
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT,
                    trade_date TEXT,
                    indicator_name TEXT,
                    indicator_value REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, trade_date, indicator_name)
                )
            """)

            # 财务数据表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS financial_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT,
                    report_date TEXT,
                    report_type TEXT,
                    total_revenue REAL,
                    net_profit REAL,
                    total_assets REAL,
                    total_liabilities REAL,
                    eps REAL,
                    roe REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, report_date, report_type)
                )
            """)
```

#### 索引优化
```python
def create_indexes(self):
    """创建数据库索引"""
    with sqlite3.connect(self.db_path) as conn:
        # 技术数据索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_technical_stock_date ON technical_data(stock_code, trade_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_technical_date ON technical_data(trade_date)")

        # 技术指标索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_indicator_stock_date_name ON technical_indicators(stock_code, trade_date, indicator_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_indicator_stock_date ON technical_indicators(stock_code, trade_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_indicator_name ON technical_indicators(indicator_name)")

        # 财务数据索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_stock_date ON financial_data(stock_code, report_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_date ON financial_data(report_date)")
```

### 3. 技术数据与财会数据关联设计

#### 统一的股票代码管理
- **代码标准化：** 所有股票使用6位数字代码
- **市场标识：** 沪市(SH)、深市(SZ)后缀标识
- **代码映射：** 处理更名、重组等情况

#### 时间对齐策略
```python
class DataAligner:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_combined_data(self, stock_code, start_date, end_date):
        """获取合并的技术和财务数据"""
        # 获取技术数据（日频）
        technical_query = """
            SELECT * FROM technical_data
            WHERE stock_code = ? AND trade_date BETWEEN ? AND ?
            ORDER BY trade_date
        """

        # 获取财务数据（季频，补充到每日数据中）
        financial_query = """
            SELECT * FROM financial_data
            WHERE stock_code = ? AND report_date <= ?
            ORDER BY report_date DESC
        """

        # 合并数据逻辑
        technical_df = pd.read_sql(technical_query, self.db, params=[stock_code, start_date, end_date])
        financial_df = pd.read_sql(financial_query, self.db, params=[stock_code, end_date])

        return self.merge_data(technical_df, financial_df)

    def merge_data(self, technical_df, financial_df):
        """将财务数据按时间对齐到技术数据"""
        # 对每个交易日，填充最新的财务数据
        merged_data = technical_df.copy()

        for idx, row in technical_df.iterrows():
            trade_date = row['trade_date']
            # 找到该交易日之前的最新财务数据
            latest_financial = financial_df[financial_df['report_date'] <= trade_date].iloc[0] if len(financial_df) > 0 else None

            if latest_financial is not None:
                # 将财务数据添加到行中
                for col in ['total_revenue', 'net_profit', 'eps', 'roe']:
                    merged_data.at[idx, f'fin_{col}'] = latest_financial[col]

        return merged_data
```

### 3.5. 可扩展技术指标系统

#### 技术指标管理类
```python
class TechnicalIndicatorManager:
    def __init__(self, db_connection):
        self.db = db_connection
        self.available_indicators = {
            'ma5': '5日移动平均线',
            'ma10': '10日移动平均线',
            'ma20': '20日移动平均线',
            'ma60': '60日移动平均线',
            'rsi': 'RSI相对强弱指标',
            'macd': 'MACD指标',
            'bollinger_upper': '布林带上轨',
            'bollinger_lower': '布林带下轨',
            'volume_ratio': '量比'
        }

    def calculate_ma(self, stock_code, periods=[5, 10, 20, 60]):
        """计算移动平均线"""
        for period in periods:
            query = """
                SELECT stock_code, trade_date, close_price,
                       AVG(close_price) OVER (
                           PARTITION BY stock_code
                           ORDER BY trade_date
                           ROWS BETWEEN {period}-1 PRECEDING AND CURRENT ROW
                       ) as ma{period}
                FROM technical_data
                WHERE stock_code = ?
                ORDER BY trade_date
            """.format(period=period)

            df = pd.read_sql(query, self.db, params=[stock_code])
            self.save_indicators(df, ['ma{period}'.format(period=period)])

    def calculate_rsi(self, stock_code, period=14):
        """计算RSI指标"""
        # 获取价格数据
        price_query = "SELECT trade_date, close_price FROM technical_data WHERE stock_code = ? ORDER BY trade_date"
        df = pd.read_sql(price_query, self.db, params=[stock_code])

        if len(df) < period + 1:
            return

        # 计算价格变化
        df['price_change'] = df['close_price'].diff()
        df['gain'] = df['price_change'].where(df['price_change'] > 0, 0)
        df['loss'] = -df['price_change'].where(df['price_change'] < 0, 0)

        # 计算RSI
        df['avg_gain'] = df['gain'].rolling(window=period).mean()
        df['avg_loss'] = df['loss'].rolling(window=period).mean()
        df['rs'] = df['avg_gain'] / df['avg_loss']
        df['rsi'] = 100 - (100 / (1 + df['rs']))

        # 保存RSI指标
        indicator_data = df[['trade_date', 'rsi']].copy()
        indicator_data['stock_code'] = stock_code
        indicator_data = indicator_data.dropna()
        self.save_indicators(indicator_data, ['rsi'])

    def save_indicators(self, df, indicator_names):
        """保存技术指标到数据库"""
        for indicator_name in indicator_names:
            if indicator_name in df.columns:
                indicator_df = df[['stock_code', 'trade_date', indicator_name]].copy()
                indicator_df = indicator_df.dropna()
                indicator_df['indicator_name'] = indicator_name
                indicator_df['indicator_value'] = indicator_df[indicator_name]

                # 保存到technical_indicators表
                indicator_df[['stock_code', 'trade_date', 'indicator_name', 'indicator_value']].to_sql(
                    'technical_indicators',
                    self.db,
                    if_exists='append',
                    index=False
                )

    def get_stock_with_indicators(self, stock_code, start_date, end_date, indicators=None):
        """获取带技术指标的股票数据"""
        if indicators is None:
            indicators = ['ma5', 'ma10', 'ma20', 'rsi']

        # 获取基础技术数据
        base_query = """
            SELECT * FROM technical_data
            WHERE stock_code = ? AND trade_date BETWEEN ? AND ?
            ORDER BY trade_date
        """
        base_data = pd.read_sql(base_query, self.db, params=[stock_code, start_date, end_date])

        # 获取技术指标数据
        indicator_placeholders = ','.join(['?' for _ in indicators])
        indicator_query = f"""
            SELECT stock_code, trade_date, indicator_name, indicator_value
            FROM technical_indicators
            WHERE stock_code = ? AND trade_date BETWEEN ? AND ?
            AND indicator_name IN ({indicator_placeholders})
            ORDER BY trade_date, indicator_name
        """

        indicator_params = [stock_code, start_date, end_date] + indicators
        indicator_data = pd.read_sql(indicator_query, self.db, params=indicator_params)

        # 将指标数据透视到列
        if len(indicator_data) > 0:
            indicator_pivot = indicator_data.pivot_table(
                index=['stock_code', 'trade_date'],
                columns='indicator_name',
                values='indicator_value',
                aggfunc='first'
            ).reset_index()

            # 合并基础数据和指标数据
            merged_data = pd.merge(base_data, indicator_pivot, on=['stock_code', 'trade_date'], how='left')
        else:
            merged_data = base_data

        return merged_data

    def add_custom_indicator(self, name, description, calculation_func):
        """添加自定义技术指标"""
        self.available_indicators[name] = description
        # 可以将自定义函数保存到配置中，支持动态加载
```

#### 指标自动计算和更新
```python
def calculate_all_indicators(self, stock_code):
    """为指定股票计算所有技术指标"""
    try:
        # 计算移动平均线
        self.calculate_ma(stock_code, [5, 10, 20, 60])

        # 计算RSI
        self.calculate_rsi(stock_code, 14)

        # 可以添加更多指标...

        print(f"股票 {stock_code} 的技术指标计算完成")
    except Exception as e:
        print(f"计算股票 {stock_code} 技术指标时出错: {e}")

def batch_update_indicators(self, stock_codes=None):
    """批量更新技术指标"""
    if stock_codes is None:
        # 获取所有股票代码
        stock_query = "SELECT DISTINCT stock_code FROM technical_data"
        stock_codes = pd.read_sql(stock_query, self.db)['stock_code'].tolist()

    for code in stock_codes:
        self.calculate_all_indicators(code)
        time.sleep(0.1)  # 避免计算过于密集
```

### 4. 简化的数据更新机制

#### 增量更新策略
```python
class DataUpdater:
    def __init__(self, db, collector):
        self.db = db
        self.collector = collector

    def update_technical_data(self, stock_code):
        """更新单只股票的技术数据"""
        # 获取最后更新日期
        last_date_query = "SELECT MAX(trade_date) FROM technical_data WHERE stock_code = ?"
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.execute(last_date_query, [stock_code])
            last_date = cursor.fetchone()[0]

        # 确定更新日期范围
        start_date = last_date or "20180101"
        end_date = pd.Timestamp.now().strftime("%Y%m%d")

        # 获取新数据并保存
        new_data = self.collector.get_stock_data(stock_code, start_date, end_date)
        if new_data is not None and len(new_data) > 0:
            self.save_technical_data(stock_code, new_data)

    def batch_update_all_stocks(self):
        """批量更新所有股票"""
        stock_codes = self.get_all_stock_codes()
        for code in stock_codes:
            try:
                self.update_technical_data(code)
                print(f"更新 {code} 完成")
            except Exception as e:
                print(f"更新 {code} 失败: {e}")
```

#### 自动化更新调度
```python
import schedule
import time

def setup_auto_update():
    """设置自动更新任务"""
    # 每个工作日收盘后更新
    schedule.every().monday.at "16:00".do(daily_update)
    schedule.every().tuesday.at "16:00".do(daily_update)
    schedule.every().wednesday.at "16:00".do(daily_update)
    schedule.every().thursday.at "16:00".do(daily_update)
    schedule.every().friday.at "16:00".do(daily_update)

    # 每季度更新财务数据
    schedule.every().month.at "01:00".do(monthly_financial_update)

    while True:
        schedule.run_pending()
        time.sleep(60)
```

### 5. 数据查询接口

#### 统一查询类
```python
class StockDataQuery:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_stock_basic_info(self, stock_code=None):
        """获取股票基础信息"""
        if stock_code:
            query = "SELECT * FROM stock_master WHERE stock_code = ?"
            return pd.read_sql(query, sqlite3.connect(self.db_path), params=[stock_code])
        else:
            return pd.read_sql("SELECT * FROM stock_master", sqlite3.connect(self.db_path))

    def get_technical_data(self, stock_code, start_date=None, end_date=None):
        """获取技术数据"""
        query = "SELECT * FROM technical_data WHERE stock_code = ?"
        params = [stock_code]

        if start_date:
            query += " AND trade_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND trade_date <= ?"
            params.append(end_date)

        query += " ORDER BY trade_date"
        return pd.read_sql(query, sqlite3.connect(self.db_path), params=params)

    def get_financial_data(self, stock_code, start_quarter=None, end_quarter=None):
        """获取财务数据"""
        query = "SELECT * FROM financial_data WHERE stock_code = ?"
        params = [stock_code]

        if start_quarter:
            query += " AND report_date >= ?"
            params.append(start_quarter)
        if end_quarter:
            query += " AND report_date <= ?"
            params.append(end_quarter)

        query += " ORDER BY report_date"
        return pd.read_sql(query, sqlite3.connect(self.db_path), params=params)

    def get_multi_stock_data(self, stock_codes, start_date, end_date):
        """获取多只股票数据"""
        codes_str = "','".join(stock_codes)
        query = f"""
            SELECT * FROM technical_data
            WHERE stock_code IN ('{codes_str}')
            AND trade_date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY stock_code, trade_date
        """
        return pd.read_sql(query, sqlite3.connect(self.db_path))
```

### 6. 财会数据和技术数据结合使用示例

#### 策略分析示例
```python
class StrategyAnalyzer:
    def __init__(self, query):
        self.query = query

    def analyze_pe_strategy(self, stock_codes, start_date, end_date):
        """分析PE策略"""
        results = []
        for code in stock_codes:
            # 获取合并数据
            technical_data = self.query.get_technical_data(code, start_date, end_date)
            financial_data = self.query.get_financial_data(code)

            if len(technical_data) > 0 and len(financial_data) > 0:
                # 计算PE比率（需要结合股价和每股收益）
                merged_data = self.merge_financial_to_price(technical_data, financial_data)

                # 简单的PE策略
                low_pe_stocks = merged_data[merged_data['pe_ratio'] < 15]
                if len(low_pe_stocks) > 0:
                    results.append({
                        'stock_code': code,
                        'low_pe_days': len(low_pe_stocks),
                        'avg_return': self.calculate_average_return(low_pe_stocks)
                    })

        return results

    def merge_financial_to_price(self, price_data, financial_data):
        """将财务数据合并到价格数据中"""
        # 为每个交易日找到最新的财务数据
        result = price_data.copy()

        for idx, row in price_data.iterrows():
            trade_date = row['trade_date']
            # 找到该日期前发布的最新财报
            latest_financial = financial_data[financial_data['report_date'] <= trade_date].iloc[0] if len(financial_data) > 0 else None

            if latest_financial is not None and latest_financial['eps'] > 0:
                # 计算PE比率
                result.at[idx, 'pe_ratio'] = row['close_price'] / latest_financial['eps']
                result.at[idx, 'pb_ratio'] = row['close_price'] / latest_financial['book_value_per_share'] if latest_financial['book_value_per_share'] > 0 else None

        return result
```

## 风险和权衡

### 主要风险
1. **Akshare稳定性：** 依赖单一数据源，可能面临API变更
2. **数据质量：** 免费数据可能存在错误或缺失
3. **单点故障：** 单机环境，硬件故障影响数据安全
4. **性能限制：** SQLite在大量数据时性能下降

### 缓解措施
1. **数据备份：** 定期备份数据库文件
2. **数据验证：** 实施数据质量检查
3. **监控机制：** 监控API调用成功率
4. **性能优化：** 合理使用索引和数据分区

## 安装和部署

### 环境要求
```bash
# Python 3.8+
pip install akshare pandas sqlite3 schedule

# 可选依赖（用于更好性能）
pip install numpy matplotlib seaborn
```

### 数据库初始化
```python
from stock_data_system import StockDataDB

# 创建数据库
db = StockDataDB("stock_data.db")

# 初始化股票列表
db.init_stock_list()
```

## 使用示例

### 基础使用
```python
from stock_data_system import StockDataSystem

# 初始化系统
system = StockDataSystem()

# 获取股票列表
stocks = system.get_stock_list()

# 更新所有股票数据（2018年至今）
system.update_all_stocks(start_date="20180101")

# 查询特定股票数据
data = system.query.get_technical_data("000001", "20230101", "20231201")

# 获取合并的技术和财务数据
combined_data = system.query.get_combined_data("000001", "20230101", "20231201")
```

### 自动更新设置
```python
# 启动自动更新服务
system.start_auto_update()

# 手动更新最新数据
system.update_latest_data()
```

## 迁移计划

### 第一阶段：基础框架（1周）
1. 安装配置开发环境
2. 创建SQLite数据库结构
3. 实现基础的Akshare数据获取
4. 测试单只股票数据获取

### 第二阶段：数据收集（1-2周）
1. 实现批量数据收集
2. 添加错误处理和重试机制
3. 完成2018年至今历史数据获取
4. 实现增量更新功能

### 第三阶段：数据整合（1周）
1. 实现财会数据获取
2. 开发数据对齐和关联功能
3. 创建统一查询接口
4. 测试数据完整性

### 第四阶段：优化完善（1周）
1. 性能优化和索引创建
2. 添加数据质量检查
3. 完善错误处理和日志
4. 创建使用文档和示例

## 预期效果
- **数据完整性：** 覆盖2018年至今的A股主要股票数据
- **查询效率：** 支持秒级查询单只股票的历史数据
- **更新便捷：** 一键更新，支持自动化定时更新
- **扩展性好：** 便于后续添加更多分析功能