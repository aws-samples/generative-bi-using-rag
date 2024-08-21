import os
import logging

# 设置日志级别
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

logger = None


def getLogger():
    global logger
    if logger is not None:
        return logger

    # 创建日志记录器
    logger = logging.getLogger('application')
    logger.propagate = False
    logger.setLevel(LOG_LEVEL)
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)

    # 设置日志格式
    log_format = '%(asctime)s [%(module)s L%(lineno)d] [%(levelname)s] %(message)s'
    formatter = logging.Formatter(log_format)

    # 设置日志处理器格式
    console_handler.setFormatter(formatter)

    # 添加日志处理器
    logger.addHandler(console_handler)

    return logger
