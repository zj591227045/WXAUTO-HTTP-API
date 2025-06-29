import sys
import logging
import re
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from app.config import Config

# 创建一个动态日志文件处理器，支持跨天自动切换日志文件
class DailyRotatingFileHandler(logging.Handler):
    """动态日志文件处理器，支持跨天自动切换日志文件，线程安全"""

    def __init__(self, log_dir, filename_prefix="api", max_bytes=20*1024*1024, backup_count=5):
        super().__init__()
        self.log_dir = log_dir
        self.filename_prefix = filename_prefix
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.current_date = None
        self.current_handler = None
        # 添加线程锁，确保线程安全
        import threading
        self._lock = threading.RLock()

    def _get_current_log_file(self):
        """获取当前日期的日志文件路径"""
        current_date = datetime.now().strftime('%Y%m%d')
        filename = f"{self.filename_prefix}_{current_date}.log"
        return os.path.join(self.log_dir, filename)

    def _ensure_handler(self):
        """确保当前有有效的文件处理器，线程安全"""
        current_date = datetime.now().strftime('%Y%m%d')

        # 使用锁确保线程安全
        with self._lock:
            # 如果日期发生变化或者还没有处理器，创建新的处理器
            if self.current_date != current_date or self.current_handler is None:
                # 安全关闭旧的处理器
                if self.current_handler:
                    try:
                        self.current_handler.close()
                    except Exception:
                        pass  # 忽略关闭时的异常

                # 创建新的处理器
                try:
                    log_file = self._get_current_log_file()
                    self.current_handler = RotatingFileHandler(
                        log_file,
                        maxBytes=self.max_bytes,
                        backupCount=self.backup_count,
                        encoding='utf-8'
                    )

                    # 设置格式化器和过滤器
                    if hasattr(self, 'formatter') and self.formatter:
                        self.current_handler.setFormatter(self.formatter)
                    if hasattr(self, 'filters'):
                        for filter_obj in self.filters:
                            self.current_handler.addFilter(filter_obj)

                    self.current_date = current_date
                except Exception:
                    # 如果创建处理器失败，设置为None
                    self.current_handler = None

    def emit(self, record):
        """发送日志记录，线程安全"""
        try:
            self._ensure_handler()
            # 使用锁确保emit操作的线程安全
            with self._lock:
                if self.current_handler:
                    self.current_handler.emit(record)
        except (ValueError, OSError, AttributeError, RuntimeError, IOError, BrokenPipeError):
            # 忽略I/O错误、属性错误、运行时错误、IO错误和管道错误
            try:
                # 尝试重新创建处理器
                self.current_handler = None
                self._ensure_handler()
            except Exception:
                # 如果重新创建也失败，使用默认错误处理
                self.handleError(record)
        except Exception:
            # 对于其他异常，使用默认错误处理
            self.handleError(record)

    def flush(self):
        """刷新日志，线程安全"""
        try:
            with self._lock:
                if self.current_handler:
                    self.current_handler.flush()
        except (ValueError, OSError, AttributeError, RuntimeError, IOError, BrokenPipeError):
            # 忽略文件已关闭或其他I/O错误
            try:
                # 尝试重新创建处理器
                self.current_handler = None
                self._ensure_handler()
            except Exception:
                # 如果重新创建也失败，就完全忽略
                pass
        except Exception:
            # 忽略其他所有异常
            try:
                # 尝试重新创建处理器
                self.current_handler = None
                self._ensure_handler()
            except Exception:
                # 如果重新创建也失败，就完全忽略
                pass

    def setFormatter(self, formatter):
        """设置格式化器，线程安全"""
        super().setFormatter(formatter)
        with self._lock:
            if self.current_handler:
                self.current_handler.setFormatter(formatter)

    def addFilter(self, filter_obj):
        """添加过滤器，线程安全"""
        super().addFilter(filter_obj)
        with self._lock:
            if self.current_handler:
                self.current_handler.addFilter(filter_obj)

    def close(self):
        """关闭处理器，线程安全"""
        with self._lock:
            if self.current_handler:
                try:
                    self.current_handler.close()
                except Exception:
                    pass  # 忽略关闭时的异常
                finally:
                    self.current_handler = None
        super().close()

# 创建一个内存日志处理器，用于捕获最近的错误日志
class MemoryLogHandler(logging.Handler):
    """内存日志处理器，用于捕获最近的错误日志，线程安全"""

    def __init__(self, capacity=100):
        super().__init__()
        self.capacity = capacity
        self.buffer = []
        self.error_logs = []
        # 添加线程锁，确保线程安全
        import threading
        self._lock = threading.RLock()

    def emit(self, record):
        try:
            # 将日志记录添加到缓冲区
            msg = self.format(record)

            # 使用锁确保线程安全
            with self._lock:
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

    def flush(self):
        """刷新处理器（内存处理器无需实际刷新）"""
        pass

    def get_logs(self):
        """获取所有日志，线程安全"""
        with self._lock:
            return self.buffer.copy()

    def get_error_logs(self):
        """获取错误日志，线程安全"""
        with self._lock:
            return self.error_logs.copy()

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

# 禁用Python logging模块的I/O错误输出，避免显示"--- Logging error ---"信息
def disable_logging_io_error_output():
    """只禁用I/O相关的日志错误输出，保留其他错误处理"""
    import logging
    import sys

    # 保存原始的handleError方法
    original_handle_error = logging.Handler.handleError

    def selective_handle_error(self, record):
        """选择性处理日志错误，只抑制I/O相关错误"""
        try:
            # 调用原始的handleError方法
            original_handle_error(self, record)
        except Exception as e:
            # 检查是否是I/O相关的错误
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in [
                'i/o operation on closed file',
                'bad file descriptor',
                'broken pipe',
                'connection reset',
                'errno 9',  # Bad file descriptor
                'errno 32'  # Broken pipe
            ]):
                # 对于I/O错误，静默处理
                pass
            else:
                # 对于其他错误，仍然输出到stderr（但不是stdout）
                try:
                    sys.stderr.write(f"Logging error in handler {self.__class__.__name__}: {str(e)}\n")
                    sys.stderr.flush()
                except:
                    # 如果连stderr都有问题，就完全忽略
                    pass

    # 替换原始的handleError方法
    logging.Handler.handleError = selective_handle_error

# 在模块加载时就禁用I/O日志错误输出
disable_logging_io_error_output()

# 创建一个安全的流处理器，避免I/O错误
class SafeStreamHandler(logging.StreamHandler):
    """安全的流处理器，避免I/O操作错误"""

    def __init__(self, stream=None):
        super().__init__(stream)
        import threading
        self._lock = threading.RLock()

    def emit(self, record):
        """安全地发送日志记录"""
        try:
            with self._lock:
                # 检查流是否仍然有效
                if not self.stream or (hasattr(self.stream, 'closed') and self.stream.closed):
                    # 如果流已关闭或不存在，尝试重新设置为 sys.stdout
                    import sys
                    self.stream = sys.stdout

                # 再次检查流是否可写
                if self.stream and hasattr(self.stream, 'write'):
                    try:
                        # 检查流是否真的可以写入
                        if hasattr(self.stream, 'closed') and self.stream.closed:
                            import sys
                            self.stream = sys.stdout

                        # 尝试写入日志
                        super().emit(record)
                    except (ValueError, OSError, AttributeError, RuntimeError, IOError, BrokenPipeError):
                        # 如果写入失败，静默忽略，避免产生更多错误日志
                        pass
        except (ValueError, OSError, AttributeError, RuntimeError, IOError, BrokenPipeError):
            # 忽略I/O错误、属性错误、运行时错误、IO错误和管道错误
            # 不再尝试重新设置流，避免递归错误
            pass
        except Exception:
            # 忽略其他所有异常，避免产生更多错误日志
            pass

    def flush(self):
        """安全地刷新流"""
        try:
            with self._lock:
                # 检查流是否仍然有效
                if not self.stream or (hasattr(self.stream, 'closed') and self.stream.closed):
                    # 如果流已关闭或不存在，尝试重新设置为 sys.stdout
                    import sys
                    self.stream = sys.stdout

                # 再次检查流是否可以刷新
                if self.stream and hasattr(self.stream, 'flush'):
                    try:
                        # 检查流是否真的可以刷新
                        if hasattr(self.stream, 'closed') and self.stream.closed:
                            import sys
                            self.stream = sys.stdout

                        # 尝试刷新流
                        self.stream.flush()
                    except (ValueError, OSError, AttributeError, RuntimeError, IOError, BrokenPipeError):
                        # 如果刷新失败，静默忽略，避免产生更多错误日志
                        pass
        except (ValueError, OSError, AttributeError, RuntimeError, IOError, BrokenPipeError):
            # 忽略I/O错误、属性错误、运行时错误、IO错误和管道错误
            # 不再尝试重新设置流，避免递归错误
            pass
        except Exception:
            # 忽略其他所有异常，避免产生更多错误日志
            pass

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

    # 添加动态日志文件处理器 - 支持跨天自动切换
    file_handler = DailyRotatingFileHandler(
        log_dir=str(Config.LOGS_DIR),
        filename_prefix="api",
        max_bytes=Config.LOG_MAX_BYTES,
        backup_count=Config.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(http_filter)  # 添加过滤器
    # 设置为INFO级别，减少日志量
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # 添加控制台处理器
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(http_filter)  # 添加过滤器
    # 设置为INFO级别，减少日志量
    console_handler.setLevel(logging.INFO)
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