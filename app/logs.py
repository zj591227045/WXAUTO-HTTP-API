import sys
import logging
import re
from logging.handlers import TimedRotatingFileHandler
from app.config import Config

# 创建一个内存日志处理器，用于捕获最近的错误日志
class MemoryLogHandler(logging.Handler):
    """内存日志处理器，用于捕获最近的错误日志"""

    def __init__(self, capacity=100):
        super().__init__()
        self.capacity = capacity
        self.buffer = []
        self.error_logs = []

    def emit(self, record):
        try:
            # 将日志记录添加到缓冲区
            msg = self.format(record)
            self.buffer.append(msg)

            # 如果是错误日志，单独保存
            if record.levelno >= logging.ERROR:
                self.error_logs.append(msg)

            # 如果缓冲区超过容量，移除最旧的记录
            if len(self.buffer) > self.capacity:
                self.buffer.pop(0)

            # 如果错误日志超过容量，移除最旧的记录
            if len(self.error_logs) > self.capacity:
                self.error_logs.pop(0)
        except Exception:
            self.handleError(record)

    def get_logs(self):
        """获取所有日志"""
        return self.buffer

    def get_error_logs(self):
        """获取错误日志"""
        return self.error_logs

    def clear(self):
        """清空日志缓冲区"""
        self.buffer = []
        self.error_logs = []

    def has_error(self, error_pattern):
        """检查是否有匹配指定模式的错误日志"""
        for log in self.error_logs:
            if error_pattern in log:
                return True

        # 如果没有找到匹配的错误日志，尝试更宽松的匹配
        for log in self.error_logs:
            if error_pattern.lower() in log.lower():
                return True

        return False

# 创建一个自定义的日志记录器，用于添加当前使用的库信息
class WeChatLibAdapter(logging.LoggerAdapter):
    """添加当前使用的库信息到日志记录"""

    def __init__(self, logger, lib_name='wxauto'):
        super().__init__(logger, {'wechat_lib': lib_name})

    def process(self, msg, kwargs):
        # 确保额外参数中包含当前使用的库信息
        if 'extra' not in kwargs:
            kwargs['extra'] = self.extra
        else:
            # 如果已经有extra参数，添加wechat_lib
            kwargs['extra'].update(self.extra)
        return msg, kwargs

    def set_lib_name(self, lib_name):
        """更新当前使用的库名称"""
        self.extra['wechat_lib'] = lib_name

    @classmethod
    def set_lib_name_static(cls, lib_name):
        """静态方法，用于更新全局logger的库名称"""
        global logger
        if isinstance(logger, cls):
            logger.set_lib_name(lib_name)

# 创建一个过滤器类，用于过滤掉重复的HTTP请求处理日志
class HttpRequestFilter(logging.Filter):
    """过滤掉重复的HTTP请求处理日志和详细的错误堆栈跟踪"""

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

        # 匹配详细错误堆栈跟踪和内部错误信息的模式
        self.error_patterns = [
            re.compile(r'Traceback \(most recent call last\):'),
            re.compile(r'File ".*?", line \d+, in .*?'),
            re.compile(r'^\s*\^\^\^+\s*$'),  # 匹配错误指示符 ^^^^^^
            re.compile(r'pywintypes\.error:'),
            re.compile(r'获取聊天对象 .* 的新消息失败:'),
            re.compile(r'获取监听消息失败:'),
            re.compile(r'检测到窗口激活失败，重新抛出异常:'),
            re.compile(r'捕获到错误日志:'),
            re.compile(r'当前错误日志列表:'),
            re.compile(r'检查错误模式:'),
            re.compile(r'找到匹配的错误日志:'),
            re.compile(r'找到宽松匹配的错误日志:')
        ]

    def filter(self, record):
        # 检查日志消息是否匹配任何HTTP请求处理模式
        msg = record.getMessage()

        # 过滤掉HTTP请求处理相关的日志
        for pattern in self.http_patterns:
            if pattern.search(msg):
                return False  # 过滤掉匹配的日志

        # 过滤掉详细的错误堆栈跟踪和内部错误信息
        for pattern in self.error_patterns:
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

        # 过滤掉特定的错误日志，但保留关键的操作日志
        if record.levelno == logging.ERROR:
            # 保留关键的错误日志，如"检测到窗口激活失败，尝试重新添加监听对象"
            if "检测到窗口激活失败，尝试重新添加监听对象" in msg:
                return True
            # 过滤掉其他错误日志，如"激活聊天窗口失败"
            if "激活聊天窗口失败" in msg or "SetWindowPos" in msg or "无效的窗口句柄" in msg:
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

    # 添加内存日志处理器，用于捕获最近的错误日志
    memory_handler = MemoryLogHandler(capacity=100)
    memory_handler.setFormatter(formatter)
    memory_handler.setLevel(logging.DEBUG)  # 捕获所有级别的日志，但只保存错误日志
    logger.addHandler(memory_handler)

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

    return logger, memory_handler

# 创建基础logger实例和内存日志处理器
base_logger, memory_handler = setup_logger()

# 使用适配器包装logger，添加当前使用的库信息
logger = WeChatLibAdapter(base_logger, Config.WECHAT_LIB)

# 导出内存日志处理器，供其他模块使用
log_memory_handler = memory_handler