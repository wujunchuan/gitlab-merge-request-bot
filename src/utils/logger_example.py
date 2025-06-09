"""
日志工具使用示例

展示如何在不同场景下使用日志工具模块
"""

import logging

from utils.logger import LoggerConfig, get_logger, setup_logger


def example_basic_usage():
    """基本使用示例"""
    # 方式1：使用快速方法获取日志记录器
    logger = get_logger(__name__)

    logger.info("这是一个信息日志")
    logger.warning("这是一个警告日志")
    logger.error("这是一个错误日志")


def example_custom_config():
    """自定义配置示例"""
    # 方式2：使用自定义配置
    config = LoggerConfig(
        name="custom_module",
        level=logging.DEBUG,
        log_file="custom_module.log",
        console_output=True,
        file_output=True,
        log_dir="custom_logs",
    )

    logger = setup_logger(config)

    logger.debug("这是一个调试日志")
    logger.info("这是一个信息日志")
    logger.warning("这是一个警告日志")


def example_different_levels():
    """不同日志级别示例"""
    # 创建只输出ERROR级别及以上的日志记录器
    error_logger = get_logger(
        name="error_only", level=logging.ERROR, log_file="errors_only.log"
    )

    # 创建详细调试日志记录器
    debug_logger = get_logger(
        name="debug_verbose", level=logging.DEBUG, log_file="debug_verbose.log"
    )

    # 这些日志不会被error_logger记录
    error_logger.info("这条信息不会被记录")
    error_logger.warning("这条警告不会被记录")

    # 这条会被记录
    error_logger.error("这条错误会被记录")

    # 所有级别都会被debug_logger记录
    debug_logger.debug("调试信息")
    debug_logger.info("普通信息")
    debug_logger.warning("警告信息")
    debug_logger.error("错误信息")


if __name__ == "__main__":
    print("运行日志工具示例...")

    example_basic_usage()
    example_custom_config()
    example_different_levels()

    print("示例执行完成，请查看生成的日志文件")
