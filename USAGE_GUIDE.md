# 🚀 股票数据系统使用指南

## 📊 数据库状态

**当前数据库包含：**
- 📈 **股票数量**: 5,453 只股票
- 📋 **数据记录**: 8,370,329 条技术数据
- 📅 **时间范围**: 2018-01-02 至 2025-11-28
- 💾 **数据库大小**: 约 1.5 GB

## 🎯 快速开始

### 1️⃣ 测试系统（推荐首先运行）
```bash
python scripts/test_new_data_rules.py
```
验证不同类型股票的数据获取是否正常工作

### 2️⃣ 开始收集数据

#### 测试模式 - 10只股票
```bash
python scripts/collect_full_data_new.py --mode 1
```

#### 小规模模式 - 100只股票
```bash
python scripts/collect_full_data_new.py --mode 2
```

#### 完整模式 - 所有股票
```bash
python scripts/collect_full_data_new.py --mode 4
```

### 3️⃣ 高级选项

#### 使用前复权（适合短线交易）
```bash
python scripts/collect_full_data_new.py --adjustment qfq
```

#### 自动运行（跳过确认提示）
```bash
python scripts/collect_full_data_new.py --mode 4 --auto
```

## 🔧 数据获取规则

系统自动识别股票类型并使用对应接口：

| 股票类型 | 代码前缀 | 接口 | 示例 |
|---------|---------|------|------|
| 深圳A股 | 00、30 | `stock_zh_a_daily` | sz000001 |
| 上海A股 | 60、68 | `stock_zh_a_daily` | sh600000 |
| 北交所 | 92 | `stock_zh_a_daily` | bj430002 |
| 特殊CDR | 689009 | `stock_zh_a_cdr_daily` | sh689009 |

## 📁 项目结构

```
📂 stockData2/
├── 📂 src/              # 核心代码
├── 📂 scripts/           # 执行脚本 ⭐ 主要使用
├── 📂 utils/             # 工具脚本
├── 📂 data/              # 数据库文件
├── 📂 logs/              # 日志文件
├── 📂 archive/           # 归档文件
└── 📂 tests/             # 测试文件
```

## 🔍 维护工具

### 检查数据库状态
```bash
python utils/check_database_count.py
```

### 生成数据报告
```bash
python utils/generate_data_report.py
```

### 设置定期检查
```bash
python scripts/setup_weekly_check.py
```

### 收集缺失股票
```bash
python scripts/collect_missing_stocks.py
```

## 💡 使用技巧

### 📈 数据收集建议
1. **首次使用**：建议先运行 `--mode 1` 测试
2. **完整收集**：使用 `--mode 4 --auto` 自动收集所有股票
3. **复权选择**：
   - 长期分析用 `--adjustment hfq`（后复权）
   - 短线交易用 `--adjustment qfq`（前复权）

### 🛡️ 避免被封禁
- 系统已内置请求间隔控制
- 建议：收集大量数据时分批进行
- 监控日志文件查看异常情况

### 💾 数据管理
- 定期运行 `check_database_count.py` 检查数据完整性
- 使用 `setup_weekly_check.py` 设置自动监控
- 重要报告文件会自动保存在 `archive/` 目录

### ⚠️ 注意事项
1. **网络依赖**：需要稳定的网络连接获取数据
2. **存储空间**：完整A股数据需要约2-3GB空间
3. **更新频率**：建议交易日收盘后更新数据
4. **特殊股票**：689009使用CDR专用接口，数据格式可能略有不同

## 🆚 版本说明

### 新版本（推荐）
- **主程序**：`scripts/collect_full_data_new.py`
- **核心库**：`src/data_collector_new.py` + `src/database_new.py`
- **优势**：智能股票识别、灵活配置、详细日志

### 原版本
- **主程序**：`scripts/collect_full_data.py`
- **核心库**：`src/data_collector.py` + `src/database.py`

## 🆘️ 问题排查

### 常见问题
1. **数据获取失败**：检查网络连接，查看日志文件
2. **数据库错误**：确保有足够磁盘空间
3. **特殊股票问题**：689009可能需要特殊处理

### 获取帮助
1. 查看日志：`tail -f logs/stock_data_system.log`
2. 运行测试：`python scripts/test_new_data_rules.py`
3. 检查状态：`python utils/check_database_count.py`

---

🎯 **建议**：首次使用请先运行测试脚本，确认系统工作正常后再进行大规模数据收集。