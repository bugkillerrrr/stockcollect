# 股票数据系统

基于Akshare和SQLite的量化交易数据收集和管理系统，专为个人投资者和学生设计。

## 功能特点

- ✅ **免费数据源**: 基于Akshare获取A股数据，无需付费
- ✅ **单机环境**: 使用SQLite本地数据库，无需外部服务器
- ✅ **技术数据**: 收集股价、成交量等技术指标数据
- ✅ **财务数据**: 整合财务报表数据，支持基本面分析
- ✅ **智能更新**: 增量更新机制，避免重复下载
- ✅ **扩展性**: 支持动态添加技术指标
- ✅ **反爬虫**: 内置请求控制，避免被封禁

## 系统要求

- Python 3.8+
- conda环境 (推荐BettaFish环境)
- 网络连接 (用于获取股票数据)

## 安装依赖

在您的conda环境中安装必要的依赖：

```bash
conda activate Bettafish
pip install akshare pandas numpy schedule matplotlib seaborn
```

## 快速开始

### 1. 基础测试

```bash
python test_basic.py
```

### 2. 运行示例

```bash
python example_usage.py
```

### 3. 编程使用

```python
from stock_data_system import StockDataSystem

# 初始化系统
system = StockDataSystem()

# 获取股票列表
stock_list = system.get_stock_list()

# 更新单只股票数据 (2018年至今)
system.update_single_stock("000001", start_date="20180101")

# 批量更新所有股票最新数据
system.update_latest_data()

# 获取数据库信息
db_info = system.get_database_info()
print(f"数据库包含 {db_info['technical_data_count']} 条技术数据")
```

## 项目结构

```
stockData2/
├── src/                    # 核心源代码
│   ├── database.py         # 数据库管理
│   ├── data_collector.py   # 数据收集 (Akshare)
│   ├── data_updater.py     # 数据更新逻辑
│   └── logger.py          # 日志系统
├── stock_data_system/      # 主入口模块
├── config/                 # 配置文件
│   └── config.yaml
├── data/                   # 数据存储目录
├── logs/                   # 日志文件
├── tests/                  # 测试文件
├── example_usage.py        # 使用示例
├── test_basic.py          # 基础测试
└── README.md              # 说明文档
```

## 核心功能

### 数据收集

- **技术数据**: 开盘价、最高价、最低价、收盘价、成交量、成交额
- **财务数据**: 营业收入、净利润、总资产、净资产、EPS、ROE等
- **数据范围**: 支持从2018年至今的历史数据

### 数据更新

- **增量更新**: 只下载新的数据，节省时间和流量
- **自动重试**: 网络异常时自动重试机制
- **请求控制**: 0.5-0.7秒请求间隔，避免反爬虫

### 数据存储

- **SQLite数据库**: 轻量级，适合单机环境
- **数据索引**: 优化查询性能
- **扩展设计**: 支持动态添加新的技术指标

## 使用场景

### 1. 技术分析

```python
# 获取股票技术数据
system.update_single_stock("000001")
# 数据已保存到数据库，可用于技术指标计算
```

### 2. 基本面分析

```python
# 获取财务数据
updater = DataUpdater()
updater.update_financial_data("000001")
# 可以结合股价数据进行PE、PB等指标计算
```

### 3. 策略回测

```python
# 获取历史数据进行回测
# 系统提供基础数据，可在此基础上开发回测策略
```

## 注意事项

1. **网络依赖**: 需要稳定的网络连接获取数据
2. **数据源限制**: Akshare为免费数据源，可能存在访问限制
3. **存储空间**: 完整A股数据可能占用几个GB空间
4. **更新频率**: 建议交易日收盘后更新数据

## 扩展开发

### 添加新的技术指标

```python
# 系统采用EAV模式存储技术指标
# 可以轻松添加自定义指标而无需修改数据库结构

from src.technical_indicators import TechnicalIndicatorManager

indicator_manager = TechnicalIndicatorManager(db_connection)
indicator_manager.add_custom_indicator("my_indicator", "我的指标", calculation_function)
```

### 自定义数据源

```python
# 可以扩展支持其他数据源
class CustomDataCollector(AkshareDataCollector):
    def get_custom_data(self, stock_code):
        # 实现自定义数据获取逻辑
        pass
```

## 常见问题

### Q: 数据获取失败怎么办？
A: 检查网络连接，确认akshare版本，查看日志文件获取详细错误信息。

### Q: 如何更换数据存储位置？
A: 初始化系统时指定db_path参数：
```python
system = StockDataSystem(db_path="/path/to/your/database.db")
```

### Q: 系统支持哪些股票？
A: 支持所有A股，包括沪深两市的主板、中小板、创业板。

### Q: 数据更新频率建议？
A: 建议每个交易日收盘后更新一次，财务数据每季度更新一次。

## 贡献

欢迎提交Issue和Pull Request来改进这个系统。

## 许可证

本项目仅供学习和研究使用，请遵守相关数据源的使用条款。