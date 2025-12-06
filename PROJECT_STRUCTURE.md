# 📁 股票数据收集系统 - 项目结构说明

## 🗂️ 整理后的目录结构

```
stockData2/
├── 📂 src/                          # 核心源代码
│   ├── database.py               # 原始数据库模块
│   ├── database_new.py           # 🆕 新数据库模块（支持复权配置）
│   ├── data_collector.py         # 原始数据收集器
│   ├── data_collector_new.py     # 🆕 新数据收集器（支持规则自动识别）
│   ├── logger.py                # 日志系统
│   └── multi_thread_collector.py # 多线程数据收集器
│
├── 📂 scripts/                      # 所有执行脚本
│   ├── collect_full_data.py     # 原始完整数据收集脚本
│   ├── collect_full_data_new.py # 🆕 新规则完整数据收集脚本 ⭐ 推荐
│   ├── collect_bj_*.py         # 北交所股票收集脚本
│   ├── collect_missing_stocks.py # 缺失股票收集脚本
│   ├── setup_*.py              # 数据库和监控设置脚本
│   ├── test_new_data_rules.py   # 🆕 新规则测试脚本
│   └── [其他测试和收集脚本...]   # 其他相关脚本
│
├── 📂 utils/                        # 工具脚本
│   ├── analyze_*.py            # 数据分析工具
│   ├── check_*.py              # 数据检查工具
│   ├── find_*.py               # 数据查找工具
│   ├── manage_*.py             # 数据管理工具
│   └── [其他工具脚本...]         # 其他辅助工具
│
├── 📂 archive/                      # 归档文件
│   ├── *.txt                   # 各种报告和清单文件
│   ├── *.bat                   # 批处理脚本
│   └── [缓存目录...]              # 缓存和临时文件
│
├── 📂 logs/                         # 日志文件目录
│   └── stock_data_system.log   # 系统运行日志
│
├── 📂 data/                         # 数据文件
│   ├── stock_data.db           # 原始数据库
│   ├── stock_data_new.db       # 🆕 新数据库
│   └── [其他数据文件...]         # 测试和临时数据库
│
└── 📂 docs/                         # 文档目录（建议创建）
    └── README.md               # 项目说明文档
```

## 🎯 数据获取规则（新版本）

### 规则1：沪深A股
- **深圳股票**（00、30开头）：使用 `sz` 前缀
- **上海股票**（60、68开头）：使用 `sh` 前缀
- **接口**：`ak.stock_zh_a_daily()`

### 规则2：北交所股票（92开头）
- **前缀**：`bj` + 股票代码
- **接口**：`ak.stock_zh_a_daily()`

### 规则3：特殊股票 689009
- **格式**：`sh689009`
- **接口**：`ak.stock_zh_a_cdr_daily()`（CDR专用接口）

## 🚀 推荐使用方法

### 1. 测试新规则
```bash
python scripts/test_new_data_rules.py
```

### 2. 收集数据（推荐使用新版本）
```bash
# 测试模式（10只股票）
python scripts/collect_full_data_new.py --mode 1

# 小规模模式（100只股票）
python scripts/collect_full_data_new.py --mode 2

# 完整模式（所有股票）
python scripts/collect_full_data_new.py --mode 4
```

### 3. 数据收集选项
```bash
# 使用前复权（适合短线交易）
python scripts/collect_full_data_new.py --adjustment qfq

# 使用备选API方法
python scripts/collect_full_data_new.py --api stock_zh_a_hist

# 自动运行（跳过确认）
python scripts/collect_full_data_new.py --mode 4 --auto
```

## 🆕 新功能特性

### ✅ 智能股票类型识别
- 根据股票代码前缀自动识别交易所
- 自动选择合适的API接口
- 智能处理特殊股票（如689009）

### ✅ 灵活配置选项
- 支持后复权（hfq）和前复权（qfq）
- 支持多种API方法选择
- 可配置请求间隔和重试次数

### ✅ 数据完整性保障
- 自动续传功能
- 优雅停止（Ctrl+C安全退出）
- 数据验证和质量检查
- 详细的进度跟踪

### ✅ 增强的日志系统
- 按股票类型分类记录
- 详细的错误报告
- 性能统计和分析

## 📊 数据库信息

当前数据库包含：
- **股票数量**：5,453 只
- **数据记录**：8,370,329 条
- **时间范围**：2018-01-02 至 2025-11-28
- **数据库大小**：约 1.5 GB

## 📋 维护建议

### 日常操作
1. 定期运行 `scripts/setup_weekly_check.py` 检查数据完整性
2. 使用 `utils/generate_data_report.py` 生成数据报告
3. 检查 `logs/stock_data_system.log` 监控系统状态

### 问题排查
1. 使用 `utils/check_*.py` 脚本检查数据质量
2. 运行 `scripts/test_new_data_rules.py` 验证API接口
3. 查看 `archive/` 目录中的历史报告

## 🔄 版本说明

- **原版本**：`collect_full_data.py` + `data_collector.py`
- **新版本**：`collect_full_data_new.py` + `data_collector_new.py` ⭐

新版本优势：
- 更准确的股票分类
- 灵活的配置选项
- 更好的错误处理
- 详细的日志记录

建议使用新版本进行数据收集。

## 📝 清理完成情况

### ✅ 已完成的整理
1. **脚本分类**：所有Python脚本按功能分类到不同目录
2. **文件归档**：报告、批处理文件移至archive目录
3. **缓存清理**：__pycache__等缓存文件归档
4. **目录创建**：创建utils、scripts、archive等有序目录
5. **文档更新**：创建项目结构说明文档

### 🗂️ 保留的核心文件
- **src/**：所有核心源代码
- **scripts/**：可执行的收集和测试脚本
- **utils/**：辅助工具脚本
- **data/**：数据库文件
- **logs/**：日志文件

### 📦 归档的文件
- **archive/**：历史报告、批处理文件、缓存
- 无用或重复的测试文件
- 临时生成的清单文件

现在项目结构清晰，便于维护和使用。