"""
日志工具模块

提供统一的日志配置和记录器实例，支持文件日志和控制台输出。
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class LoggerConfig:
    """日志配置类"""

    def __init__(
        self,
        name: str = __name__,
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
        console_output: bool = True,
        file_output: bool = True,
        log_dir: str = "logs",
    ):
        """
        初始化日志配置

        Args:
            name: 日志记录器名称
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: 日志文件名，如果为None则使用模块名
            log_format: 日志格式字符串
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            log_dir: 日志文件目录
        """
        self.name = name
        self.level = level
        self.log_file = log_file
        self.log_format = (
            log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.console_output = console_output
        self.file_output = file_output
        self.log_dir = log_dir


def setup_logger(config: LoggerConfig) -> logging.Logger:
    """
    根据配置创建和设置日志记录器

    Args:
        config: 日志配置对象

    Returns:
        配置好的日志记录器实例
    """
    logger = logging.getLogger(config.name)
    logger.setLevel(config.level)

    # 清除已有的处理器，避免重复添加
    if logger.hasHandlers():
        logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter(config.log_format)

    handlers = []

    # 添加控制台处理器
    if config.console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(config.level)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    # 添加文件处理器
    if config.file_output:
        # 确定日志文件路径
        if config.log_file:
            log_filename = config.log_file
        else:
            # 根据模块名生成日志文件名
            module_name = (
                config.name.split(".")[-1] if "." in config.name else config.name
            )
            log_filename = f"{module_name}.log"

        # 创建日志目录
        log_dir_path = Path(config.log_dir)
        log_dir_path.mkdir(exist_ok=True)

        log_file_path = log_dir_path / log_filename

        file_handler = RotatingFileHandler(
            log_file_path, encoding="utf-8", backupCount=5, maxBytes=1024 * 1024 * 5
        )
        file_handler.setLevel(config.level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # 添加所有处理器到日志记录器
    for handler in handlers:
        logger.addHandler(handler)

    return logger


def get_logger(
    name: str = None,
    level: int = logging.INFO,
    log_file: str = None,
    console_output: bool = True,
    file_output: bool = True,
) -> logging.Logger:
    """
    快速获取配置好的日志记录器

    Args:
        name: 日志记录器名称，如果为None则使用调用模块名
        level: 日志级别
        log_file: 日志文件名
        console_output: 是否输出到控制台
        file_output: 是否输出到文件

    Returns:
        配置好的日志记录器实例
    """
    if name is None:
        # 获取调用者的模块名
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "unknown")

    config = LoggerConfig(
        name=name,
        level=level,
        log_file=log_file,
        console_output=console_output,
        file_output=file_output,
    )

    return setup_logger(config)


# 预配置的日志记录器实例
default_logger = get_logger("gitlab_merge_request_bot", log_file="app.log")
