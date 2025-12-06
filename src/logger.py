"""
股票数据系统日志配置模块
"""
import logging
import os
from pathlib import Path
from datetime import datetime


class StockDataLogger:
    """股票数据系统日志管理器"""

    def __init__(self, log_dir="logs", log_level="INFO"):
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper())

        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 配置日志系统
        self.setup_logger()

    def setup_logger(self):
        """设置日志配置"""
        # 创建根日志器
        self.logger = logging.getLogger("stock_data_system")
        self.logger.setLevel(self.log_level)

        # 将常用方法设置为StockDataLogger的属性
        self.info = self.logger.info
        self.warning = self.logger.warning
        self.error = self.logger.error
        self.debug = self.logger.debug
        self.critical = self.logger.critical

        # 避免重复添加处理器
        if not self.logger.handlers:
            # 创建格式化器 - 强制使用UTF-8编码
            class UTF8Formatter(logging.Formatter):
                def __init__(self):
                    super().__init__(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    )

                def format(self, record):
                    # 确保消息是UTF-8编码
                    if isinstance(record.msg, str):
                        record.msg = record.msg.encode('utf-8', errors='replace').decode('utf-8')
                    return super().format(record)

            formatter = UTF8Formatter()

            # 控制台处理器 - 设置UTF-8编码
            try:
                import sys
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                if hasattr(sys.stderr, 'reconfigure'):
                    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass

            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)

            # 尝试设置handler的编码
            try:
                console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass

            self.logger.addHandler(console_handler)

            # 文件处理器
            log_file = self.log_dir / "stock_data_system.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def get_logger(self, name=None):
        """获取日志器实例"""
        if name:
            return self.logger.getChild(name)
        return self.logger

    def log_function_call(self, func_name, **kwargs):
        """记录函数调用"""
        args_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"Calling function: {func_name}({args_str})")

    def log_data_update(self, stock_code, data_type, count, success=True):
        """记录数据更新"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Data update {status}: {stock_code} {data_type} {count} records")

    def log_error(self, error_msg, exception=None):
        """记录错误信息"""
        if exception:
            self.logger.error(f"{error_msg}: {str(exception)}", exc_info=True)
        else:
            self.logger.error(error_msg)

    def log_api_call(self, api_name, stock_code, success=True, response_time=None):
        """记录API调用"""
        status = "SUCCESS" if success else "FAILED"
        time_info = f" Duration: {response_time:.2f}s" if response_time else ""
        self.logger.debug(f"API call {status}: {api_name} {stock_code}{time_info}")


# 全局日志实例
_logger_instance = None

def get_logger(name=None):
    """获取全局日志实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StockDataLogger()
    return _logger_instance

def setup_logging(log_dir="logs", log_level="INFO"):
    """设置全局日志系统"""
    global _logger_instance
    _logger_instance = StockDataLogger(log_dir, log_level)
    return _logger_instance