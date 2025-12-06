#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置定期数据完整性检查机制
创建自动化的数据完整性检查和修复系统
"""

import os
import sys
from datetime import datetime, timedelta
import subprocess
import platform

def create_weekly_check_script():
    """创建每周数据检查脚本"""

    # Windows批处理文件
    if platform.system() == "Windows":
        weekly_script = """@echo off
echo ======================================
echo 股票数据完整性每周检查
echo 开始时间: %date% %time%
echo ======================================

cd /d "d:/project/PyProject/stockData/stockData2"

echo.
echo [1/4] 检查数据完整性...
python check_stock_completeness.py

echo.
echo [2/4] 如果发现缺失数据，运行修复...
if exist missing_stocks.txt (
    echo 发现缺失股票，开始自动修复...
    python fix_missing_stocks.py
) else (
    echo 未发现缺失股票
)

echo.
echo [3/4] 生成数据报告...
python generate_data_report.py

echo.
echo [4/4] 检查完成，时间: %date% %time%
echo ======================================
echo 每周检查已完成
pause
"""
        script_name = "weekly_data_check.bat"

    # Linux/Mac shell脚本
    else:
        weekly_script = """#!/bin/bash
echo "======================================"
echo "股票数据完整性每周检查"
echo "开始时间: $(date)"
echo "======================================"

cd "/d/project/PyProject/stockData/stockData2"

echo ""
echo "[1/4] 检查数据完整性..."
python check_stock_completeness.py

echo ""
echo "[2/4] 如果发现缺失数据，运行修复..."
if [ -f "missing_stocks.txt" ]; then
    echo "发现缺失股票，开始自动修复..."
    python fix_missing_stocks.py
else
    echo "未发现缺失股票"
fi

echo ""
echo "[3/4] 生成数据报告..."
python generate_data_report.py

echo ""
echo "[4/4] 检查完成，时间: $(date)"
echo "======================================"
echo "每周检查已完成"
"""
        script_name = "weekly_data_check.sh"

    # 写入脚本文件
    with open(script_name, 'w', encoding='utf-8') as f:
        f.write(weekly_script)

    # 在Linux/Mac上设置执行权限
    if platform.system() != "Windows":
        os.chmod(script_name, 0o755)

    print(f"✅ 已创建每周检查脚本: {script_name}")
    return script_name

def create_daily_check_script():
    """创建每日数据检查脚本"""

    # Windows批处理文件
    if platform.system() == "Windows":
        daily_script = """@echo off
echo ================================
echo 股票数据每日增量检查
echo 开始时间: %date% %time%
echo ================================

cd /d "d:/project/PyProject/stockData/stockData2"

echo.
echo [1/3] 更新股票列表...
python update_stock_list.py

echo.
echo [2/3] 检查新增股票...
python check_new_stocks.py

echo.
echo [3/3] 检查完成，时间: %date% %time%
echo ================================
echo 每日检查已完成
"""
        script_name = "daily_data_check.bat"

    # Linux/Mac shell脚本
    else:
        daily_script = """#!/bin/bash
echo "================================"
echo "股票数据每日增量检查"
echo "开始时间: $(date)"
echo "================================"

cd "/d/project/PyProject/stockData/stockData2"

echo ""
echo "[1/3] 更新股票列表..."
python update_stock_list.py

echo ""
echo "[2/3] 检查新增股票..."
python check_new_stocks.py

echo ""
echo "[3/3] 检查完成，时间: $(date)"
echo "================================"
echo "每日检查已完成"
"""
        script_name = "daily_data_check.sh"

    # 写入脚本文件
    with open(script_name, 'w', encoding='utf-8') as f:
        f.write(daily_script)

    # 在Linux/Mac上设置执行权限
    if platform.system() != "Windows":
        os.chmod(script_name, 0o755)

    print(f"✅ 已创建每日检查脚本: {script_name}")
    return script_name

def generate_cron_setup_instructions():
    """生成cron设置说明"""
    cron_instructions = """
# Linux/Mac cron 设置说明
# 打开终端，运行: crontab -e
# 添加以下行：

# 每周一凌晨2点执行完整检查
0 2 * * 1 /path/to/d:/project/PyProject/stockData/stockData2/weekly_data_check.sh >> /path/to/logs/weekly_check.log 2>&1

# 每天凌晨1点执行增量检查
0 1 * * * /path/to/d:/project/PyProject/stockData/stockData2/daily_data_check.sh >> /path/to/logs/daily_check.log 2>&1

# 注意事项：
# 1. 将 /path/to/ 替换为实际路径
# 2. 确保脚本有执行权限 (chmod +x *.sh)
# 3. 确保日志目录存在并有写入权限
# 4. 首次运行前手动测试脚本
"""

    with open("cron_setup_instructions.txt", 'w', encoding='utf-8') as f:
        f.write(cron_instructions)

    print("✅ 已创建cron设置说明: cron_setup_instructions.txt")

def generate_windows_task_instructions():
    """生成Windows任务计划程序设置说明"""
    task_instructions = """
# Windows 任务计划程序设置说明

# 1. 打开"任务计划程序" (Task Scheduler)
#    - Win+R，输入 taskschd.msc，回车

# 2. 创建每周完整检查任务：
#    - 右侧点击"创建基本任务"
#    - 名称: 股票数据周检
#    - 描述: 每周执行股票数据完整性检查
#    - 触发器: 每周 星期一 凌晨2:00
#    - 操作: 启动程序
#    - 程序/脚本: d:/project/PyProject/stockData/stockData2/weekly_data_check.bat
#    - 勾选"不管用户是否登录都要运行"

# 3. 创建每日增量检查任务：
#    - 右侧点击"创建基本任务"
#    - 名称: 股票数据日检
#    - 描述: 每日检查新增股票数据
#    - 触发器: 每天 凌晨1:00
#    - 操作: 启动程序
#    - 程序/脚本: d:/project/PyProject/stockData/stockData2/daily_data_check.bat
#    - 勾选"不管用户是否登录都要运行"

# 4. 测试任务：
#    - 创建完成后，右键点击任务选择"运行"
#    - 检查输出日志是否正常

# 5. 日志位置：
#    - 任务执行后会在脚本所在目录生成日志文件
#    - 可以在任务计划程序中查看任务历史记录
"""

    with open("windows_task_setup_instructions.txt", 'w', encoding='utf-8') as f:
        f.write(task_instructions)

    print("✅ 已创建Windows任务计划说明: windows_task_setup_instructions.txt")

def create_data_report_generator():
    """创建数据报告生成器"""
    report_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成数据完整性报告
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

def generate_data_report():
    """生成数据报告"""
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print("=== 生成数据报告 ===")

    # 连接数据库
    db_path = "data/stock_data.db"
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            # 获取数据库信息
            info = {}

            # 各表记录数
            tables = ['stock_master', 'technical_data', 'technical_indicators', 'financial_data']
            for table in tables:
                try:
                    result = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn)
                    info[f"{table}_count"] = result.iloc[0]['count']
                except:
                    info[f"{table}_count"] = 0

            # 股票数量
            stock_count = pd.read_sql("""
                SELECT COUNT(DISTINCT stock_code) as stock_count
                FROM technical_data
            """, conn)
            info['stock_count'] = stock_count.iloc[0]['stock_count']

            # 数据时间范围
            date_range = pd.read_sql("""
                SELECT MIN(trade_date) as min_date, MAX(trade_date) as max_date
                FROM technical_data
            """, conn)
            info['data_start_date'] = date_range.iloc[0]['min_date']
            info['data_end_date'] = date_range.iloc[0]['max_date']

            # 数据库文件大小
            info['database_size_mb'] = round(os.path.getsize(db_path) / (1024 * 1024), 2)

            # 按市场统计
            market_stats = pd.read_sql("""
                SELECT
                    CASE
                        WHEN stock_code LIKE '000%' THEN '深交所主板'
                        WHEN stock_code LIKE '002%' THEN '深交所中小板'
                        WHEN stock_code LIKE '300%' THEN '创业板'
                        WHEN stock_code LIKE '600%' OR stock_code LIKE '601%' OR stock_code LIKE '603%' THEN '上交所主板'
                        WHEN stock_code LIKE '688%' THEN '科创板'
                        WHEN stock_code LIKE '920%' THEN '北交所'
                        ELSE '其他市场'
                    END as market,
                    COUNT(DISTINCT stock_code) as stock_count,
                    COUNT(*) as record_count
                FROM technical_data
                GROUP BY market
                ORDER BY stock_count DESC
            """, conn)

            # 生成报告文件
            report_file = f"data_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("股票数据库报告\\n")
                f.write("="*50 + "\\n")
                f.write(f"生成时间: {report_time}\\n\\n")

                f.write("数据库概览:\\n")
                f.write(f"- 数据库大小: {info['database_size_mb']} MB\\n")
                f.write(f"- 股票总数: {info['stock_count']} 只\\n")
                f.write(f"- 技术数据记录: {info['technical_data_count']:,} 条\\n")
                f.write(f"- 股票主数据: {info['stock_master_count']:,} 条\\n")
                f.write(f"- 技术指标: {info['technical_indicators_count']:,} 条\\n")
                f.write(f"- 财务数据: {info['financial_data_count']:,} 条\\n\\n")

                if info['data_start_date'] and info['data_end_date']:
                    f.write("数据时间范围:\\n")
                    f.write(f"- 开始日期: {info['data_start_date']}\\n")
                    f.write(f"- 结束日期: {info['data_end_date']}\\n\\n")

                f.write("按市场分布:\\n")
                f.write("-" * 40 + "\\n")
                for _, row in market_stats.iterrows():
                    f.write(f"{row['market']:<12}: {row['stock_count']:4d} 只股票, {row['record_count']:8d} 条记录\\n")

            print(f"✅ 报告已生成: {report_file}")
            return report_file

    except Exception as e:
        print(f"❌ 生成报告失败: {e}")
        return None

if __name__ == "__main__":
    generate_data_report()
'''

    with open("generate_data_report.py", 'w', encoding='utf-8') as f:
        f.write(report_script)

    print("✅ 已创建数据报告生成器: generate_data_report.py")

def create_update_scripts():
    """创建股票列表更新脚本"""
    update_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新股票列表
检查是否有新增的股票代码
"""

import akshare as ak
import sqlite3
import pandas as pd
from datetime import datetime

def update_stock_list():
    """更新股票列表"""
    print("=== 更新股票列表 ===")

    try:
        # 获取最新股票列表
        print("正在获取最新股票列表...")
        stock_info = ak.stock_info_a_code_name()
        current_stocks = set(stock_info['code'].tolist())
        print(f"当前API股票总数: {len(current_stocks)}")

        # 从数据库获取已有股票
        db_path = "data/stock_data.db"
        if not os.path.exists(db_path):
            print("数据库不存在，跳过更新")
            return

        with sqlite3.connect(db_path) as conn:
            db_stocks_df = pd.read_sql("SELECT DISTINCT stock_code FROM technical_data", conn)
            db_stocks = set(db_stocks_df['stock_code'].tolist())

        print(f"数据库现有股票: {len(db_stocks)}")

        # 找出新增股票
        new_stocks = current_stocks - db_stocks
        if new_stocks:
            print(f"发现 {len(new_stocks)} 只新增股票:")
            for code in sorted(list(new_stocks))[:10]:
                print(f"  - {code}")
            if len(new_stocks) > 10:
                print(f"  ... 还有 {len(new_stocks) - 10} 只")

            # 保存新增股票列表
            with open("new_stocks.txt", 'w', encoding='utf-8') as f:
                for code in sorted(new_stocks):
                    f.write(f"{code}\\n")

            print("新增股票列表已保存到: new_stocks.txt")
            return True
        else:
            print("未发现新增股票")
            return False

    except Exception as e:
        print(f"更新股票列表失败: {e}")
        return False

if __name__ == "__main__":
    import os
    update_stock_list()
'''

    with open("update_stock_list.py", 'w', encoding='utf-8') as f:
        f.write(update_script)

    print("✅ 已创建股票列表更新脚本: update_stock_list.py")

def create_new_stocks_check_script():
    """创建新增股票检查脚本"""
    check_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并收集新增股票数据
"""

import os
from fix_missing_stocks import MissingStocksFixer

def check_new_stocks():
    """检查新增股票"""
    print("=== 检查新增股票 ===")

    if not os.path.exists("new_stocks.txt"):
        print("未发现新增股票列表")
        return

    print("发现新增股票，开始收集数据...")

    # 读取新增股票
    with open("new_stocks.txt", 'r', encoding='utf-8') as f:
        new_stocks = [line.strip() for line in f if line.strip()]

    print(f"需要收集 {len(new_stocks)} 只新增股票数据")

    # 使用现有的数据收集器
    fixer = MissingStocksFixer()

    # 收集新增股票数据
    success_count = 0
    for stock_code in new_stocks:
        try:
            print(f"收集 {stock_code}...")
            success, records = fixer.collect_single_stock(stock_code)
            if success:
                success_count += 1
                print(f"  ✅ {records} 条记录")
            else:
                print(f"  ❌ 收集失败")
        except Exception as e:
            print(f"  ❌ 异常: {e}")

    print(f"\\n=== 新增股票收集结果 ===")
    print(f"成功: {success_count}/{len(new_stocks)}")

    # 清理文件
    if success_count > 0:
        os.rename("new_stocks.txt", f"new_stocks_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        print("✅ 新增股票已处理，列表文件已重命名")

if __name__ == "__main__":
    from datetime import datetime
    check_new_stocks()
'''

    with open("check_new_stocks.py", 'w', encoding='utf-8') as f:
        f.write(check_script)

    print("✅ 已创建新增股票检查脚本: check_new_stocks.py")

def main():
    """主函数"""
    print("设置定期数据完整性检查机制")
    print("="*50)

    print("\\n1. 创建每周检查脚本...")
    weekly_script = create_weekly_check_script()

    print("\\n2. 创建每日检查脚本...")
    daily_script = create_daily_check_script()

    print("\\n3. 创建数据报告生成器...")
    create_data_report_generator()

    print("\\n4. 创建股票列表更新脚本...")
    create_update_scripts()

    print("\\n5. 创建新增股票检查脚本...")
    create_new_stocks_check_script()

    print("\\n6. 生成自动化设置说明...")
    generate_cron_setup_instructions()
    generate_windows_task_instructions()

    print("\\n=== 设置完成 ===")
    print(f"✅ 已创建 {weekly_script} (每周完整检查)")
    print(f"✅ 已创建 {daily_script} (每日增量检查)")
    print("✅ 已创建 generate_data_report.py (数据报告生成)")
    print("✅ 已创建 update_stock_list.py (股票列表更新)")
    print("✅ 已创建 check_new_stocks.py (新增股票检查)")
    print("✅ 已创建 cron_setup_instructions.txt (Linux/Mac定时任务说明)")
    print("✅ 已创建 windows_task_setup_instructions.txt (Windows任务计划说明)")

    print("\\n=== 使用建议 ===")
    print("1. 手动测试脚本:")
    if platform.system() == "Windows":
        print("   - 双击运行 weekly_data_check.bat")
        print("   - 双击运行 daily_data_check.bat")
    else:
        print("   - ./weekly_data_check.sh")
        print("   - ./daily_data_check.sh")

    print("\\n2. 设置自动化任务:")
    if platform.system() == "Windows":
        print("   - 参考 windows_task_setup_instructions.txt")
    else:
        print("   - 参考 cron_setup_instructions.txt")

    print("\\n3. 监控和维护:")
    print("   - 定期检查日志文件")
    print("   - 根据需要调整检查频率")
    print("   - 监控数据库大小和性能")

    print("\\n⚠️  首次运行前请先手动测试脚本功能")

if __name__ == "__main__":
    main()