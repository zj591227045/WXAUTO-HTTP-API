import sys
import logging
import re
from logging.handlers import TimedRotatingFileHandler
from app.config import Config

# 创建一个过滤器类，用于过滤掉重复的HTTP请求处理日志
class HttpRequestFilter(logging.Filter):
    """过滤掉重复的HTTP请求处理日志"""

    def __init__(self):
        super().__init__()
        # 匹配HTTP请求处理相关的日志模式
        self.http_patterns = [
            re.compile(r'BaseHTTPRequestHandler\.handle'),
            re.compile(r'handle_one_request'),
            re.compile(r'run_wsgi'),
            re.compile(r'execute\(self\.server\.app\)'),
            re.compile(r'File ".*?\\werkzeug\\serving\.py"'),
            re.compile(r'File ".*?\\http\\server\.py"'),
            re.compile(r'self\.handle_one_request\(\)'),
            re.compile(r'miniconda3\\envs\\wxauto-api')
        ]

    def filter(self, record):
        # 检查日志消息是否匹配任何HTTP请求处理模式
        msg = record.getMessage()

        # 过滤掉HTTP请求处理相关的日志
        for pattern in self.http_patterns:
            if pattern.search(msg):
                return False  # 过滤掉匹配的日志

        # 过滤掉重复的HTTP请求处理堆栈日志
        if record.levelno == logging.ERROR and any(x in msg for x in [
            "BaseHTTPRequestHandler.handle",
            "handle_one_request",
            "run_wsgi",
            "execute(self.server.app)"
        ]):
            return False

        return True  # 保留其他日志

def setup_logger():
    # 确保日志目录存在
    Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # 设置第三方库的日志级别
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # 减少werkzeug的日志
    logging.getLogger('http.server').setLevel(logging.WARNING)  # 减少HTTP服务器的日志

    # 创建logger实例
    logger = logging.getLogger('wxauto-api')
    logger.setLevel(Config.LOG_LEVEL)  # 使用配置文件中的日志级别

    # 如果logger已经有处理器，先清除
    if logger.handlers:
        logger.handlers.clear()

    # 创建格式化器，使用统一的时间戳格式
    formatter = logging.Formatter(Config.LOG_FORMAT, Config.LOG_DATE_FORMAT)

    # 创建HTTP请求过滤器
    http_filter = HttpRequestFilter()

    # 添加文件处理器 - 使用按日期滚动的日志文件
    file_handler = TimedRotatingFileHandler(
        Config.LOG_FILE,
        when='midnight',  # 每天午夜滚动
        interval=1,       # 每1天滚动一次
        backupCount=30,   # 保留30天的日志
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(http_filter)  # 添加过滤器
    logger.addHandler(file_handler)

    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(http_filter)  # 添加过滤器
    logger.addHandler(console_handler)

    # 设置传播标志为False，避免日志重复
    logger.propagate = False

    return logger

# 创建全局logger实例
logger = setup_logger()