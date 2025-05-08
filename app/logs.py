import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from app.config import Config

def setup_logger():
    # 确保日志目录存在
    Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # 创建logger实例
    logger = logging.getLogger('wxauto-api')
    logger.setLevel(Config.LOG_LEVEL)  # 使用配置文件中的日志级别

    # 如果logger已经有处理器，先清除
    if logger.handlers:
        logger.handlers.clear()

    # 创建格式化器，使用统一的时间戳格式
    formatter = logging.Formatter(Config.LOG_FORMAT, Config.LOG_DATE_FORMAT)

    # 添加文件处理器 - 使用按日期滚动的日志文件
    file_handler = TimedRotatingFileHandler(
        Config.LOG_FILE,
        when='midnight',  # 每天午夜滚动
        interval=1,       # 每1天滚动一次
        backupCount=30,   # 保留30天的日志
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 设置传播标志为False，避免日志重复
    logger.propagate = False

    return logger

# 创建全局logger实例
logger = setup_logger()