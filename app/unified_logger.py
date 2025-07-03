"""
统一的日志管理系统
实现标准格式：[时间戳] [库名称] [日志级别] 日志内容 (重复 X 次，最后: 时间戳)
"""

import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

from app.config import Config


class LogEntry:
    """日志条目"""
    def __init__(self, timestamp: datetime, lib_name: str, level: str, message: str):
        self.timestamp = timestamp
        self.lib_name = lib_name
        self.level = level
        self.message = message
        self.count = 1
        self.last_timestamp = timestamp
    
    def __eq__(self, other):
        """判断两个日志条目是否相同（用于重复检测）"""
        if not isinstance(other, LogEntry):
            return False
        return (self.lib_name == other.lib_name and 
                self.level == other.level and 
                self.message == other.message)
    
    def __hash__(self):
        """用于字典键"""
        return hash((self.lib_name, self.level, self.message))


class LogAggregator:
    """日志聚合器 - 处理重复日志"""
    def __init__(self, max_age_seconds: int = 60):
        self.max_age_seconds = max_age_seconds
        self.entries: Dict[str, LogEntry] = {}
        self._lock = threading.Lock()
    
    def add_entry(self, entry: LogEntry) -> Optional[LogEntry]:
        """添加日志条目，返回需要输出的条目（如果有）"""
        with self._lock:
            key = self._get_key(entry)
            
            # 清理过期条目
            self._cleanup_old_entries()
            
            if key in self.entries:
                # 更新现有条目
                existing = self.entries[key]
                existing.count += 1
                existing.last_timestamp = entry.timestamp
                return None  # 不输出重复条目
            else:
                # 新条目
                self.entries[key] = entry
                return entry
    
    def get_pending_entries(self) -> List[LogEntry]:
        """获取所有待输出的聚合条目"""
        with self._lock:
            result = []
            current_time = datetime.now()
            
            for key, entry in list(self.entries.items()):
                # 如果条目有重复且超过一定时间，输出聚合信息
                if (entry.count > 1 and 
                    (current_time - entry.last_timestamp).total_seconds() > 5):
                    result.append(entry)
                    del self.entries[key]
            
            return result
    
    def _get_key(self, entry: LogEntry) -> str:
        """生成条目的唯一键"""
        return f"{entry.lib_name}:{entry.level}:{entry.message}"
    
    def _cleanup_old_entries(self):
        """清理过期条目"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, entry in self.entries.items():
            if (current_time - entry.last_timestamp).total_seconds() > self.max_age_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.entries[key]


class LogFormatter:
    """日志格式化器"""
    
    @staticmethod
    def format_entry(entry: LogEntry) -> str:
        """格式化单个日志条目"""
        timestamp_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        if entry.count > 1:
            last_timestamp_str = entry.last_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            return f"[{timestamp_str}] [{entry.lib_name}] [{entry.level}] {entry.message} (重复 {entry.count} 次，最后: {last_timestamp_str})"
        else:
            return f"[{timestamp_str}] [{entry.lib_name}] [{entry.level}] {entry.message}"


class FileHandler:
    """文件日志处理器"""
    def __init__(self, log_dir: str = "data/api/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._current_file = None
        self._current_date = None
        self._lock = threading.Lock()
    
    def write(self, formatted_log: str):
        """写入日志到文件"""
        with self._lock:
            self._ensure_file()
            if self._current_file:
                try:
                    self._current_file.write(formatted_log + '\n')
                    self._current_file.flush()
                except Exception:
                    pass  # 忽略写入错误
    
    def _ensure_file(self):
        """确保日志文件存在且是当天的"""
        today = datetime.now().strftime("%Y%m%d")
        
        if self._current_date != today:
            # 关闭旧文件
            if self._current_file:
                try:
                    self._current_file.close()
                except Exception:
                    pass
            
            # 打开新文件
            log_file = self.log_dir / f"api_{today}.log"
            try:
                self._current_file = open(log_file, 'a', encoding='utf-8')
                self._current_date = today
            except Exception:
                self._current_file = None


class UnifiedLogger:
    """统一日志管理器"""
    
    def __init__(self):
        self.aggregator = LogAggregator()
        self.formatter = LogFormatter()
        self.file_handler = FileHandler()
        self.ui_handlers: List[Callable[[str], None]] = []
        self.console_enabled = True
        self._lock = threading.Lock()
        
        # 启动聚合处理线程
        self._running = True
        self._aggregation_thread = threading.Thread(target=self._process_aggregation, daemon=True)
        self._aggregation_thread.start()
    
    def add_ui_handler(self, handler: Callable[[str], None]):
        """添加UI处理器"""
        with self._lock:
            self.ui_handlers.append(handler)
    
    def remove_ui_handler(self, handler: Callable[[str], None]):
        """移除UI处理器"""
        with self._lock:
            if handler in self.ui_handlers:
                self.ui_handlers.remove(handler)
    
    def log(self, lib_name: str, level: str, message: str):
        """记录日志"""
        entry = LogEntry(datetime.now(), lib_name, level, message)
        
        # 聚合处理
        output_entry = self.aggregator.add_entry(entry)
        
        if output_entry:
            self._output_entry(output_entry)
    
    def info(self, lib_name: str, message: str):
        """记录INFO级别日志"""
        self.log(lib_name, "INFO", message)
    
    def warning(self, lib_name: str, message: str):
        """记录WARNING级别日志"""
        self.log(lib_name, "WARNING", message)
    
    def error(self, lib_name: str, message: str):
        """记录ERROR级别日志"""
        self.log(lib_name, "ERROR", message)
    
    def debug(self, lib_name: str, message: str):
        """记录DEBUG级别日志"""
        self.log(lib_name, "DEBUG", message)
    
    def _output_entry(self, entry: LogEntry):
        """输出日志条目"""
        formatted_log = self.formatter.format_entry(entry)

        # 写入文件
        self.file_handler.write(formatted_log)

        # 控制台输出 - 添加安全检查
        if self.console_enabled:
            try:
                # 检查 stdout 是否可用且未关闭
                if hasattr(sys.stdout, 'closed') and sys.stdout.closed:
                    # stdout 已关闭，禁用控制台输出
                    self.console_enabled = False
                elif hasattr(sys.stdout, 'write'):
                    # 尝试写入，如果失败则禁用控制台输出
                    print(formatted_log)
                else:
                    # stdout 不可用，禁用控制台输出
                    self.console_enabled = False
            except (ValueError, OSError, AttributeError):
                # I/O operation on closed file 或其他 I/O 错误
                # 禁用控制台输出以避免后续错误
                self.console_enabled = False
            except Exception:
                # 其他未知错误，也禁用控制台输出
                self.console_enabled = False

        # UI处理器
        with self._lock:
            for handler in self.ui_handlers:
                try:
                    handler(formatted_log)
                except Exception:
                    pass  # 忽略UI处理器错误
    
    def _process_aggregation(self):
        """处理聚合日志的后台线程"""
        while self._running:
            try:
                # 获取待输出的聚合条目
                pending_entries = self.aggregator.get_pending_entries()
                
                for entry in pending_entries:
                    self._output_entry(entry)
                
                time.sleep(1)  # 每秒检查一次
            except Exception:
                pass  # 忽略处理错误
    
    def shutdown(self):
        """关闭日志管理器"""
        self._running = False
        if self._aggregation_thread.is_alive():
            self._aggregation_thread.join(timeout=5)


# 全局统一日志管理器实例
unified_logger = UnifiedLogger()


# 便捷函数
def log_info(lib_name: str, message: str):
    """记录INFO日志"""
    unified_logger.info(lib_name, message)


def log_warning(lib_name: str, message: str):
    """记录WARNING日志"""
    unified_logger.warning(lib_name, message)


def log_error(lib_name: str, message: str):
    """记录ERROR日志"""
    unified_logger.error(lib_name, message)


def log_debug(lib_name: str, message: str):
    """记录DEBUG日志"""
    unified_logger.debug(lib_name, message)


# 统一日志适配器 - 使用真正的统一日志系统
class UnifiedLoggerAdapter:
    """统一日志适配器，使用真正的统一日志系统"""

    def __init__(self, lib_name: str = "Flask"):
        self.lib_name = lib_name

    def set_lib_name(self, lib_name: str):
        """设置库名称"""
        self.lib_name = lib_name

    def info(self, message: str):
        """INFO日志"""
        try:
            unified_logger.info(self.lib_name, message)
        except:
            # 如果统一日志系统失败，回退到简单打印
            try:
                print(f"[{self.lib_name}] INFO: {message}")
            except:
                pass

    def warning(self, message: str):
        """WARNING日志"""
        try:
            unified_logger.warning(self.lib_name, message)
        except:
            try:
                print(f"[{self.lib_name}] WARNING: {message}")
            except:
                pass

    def error(self, message: str, exc_info=None):
        """ERROR日志"""
        try:
            if exc_info:
                import traceback
                tb_str = traceback.format_exc()
                message = f"{message}\n{tb_str}"
            unified_logger.error(self.lib_name, message)
        except:
            try:
                print(f"[{self.lib_name}] ERROR: {message}")
            except:
                pass

    def debug(self, message: str):
        """DEBUG日志"""
        try:
            unified_logger.debug(self.lib_name, message)
        except:
            try:
                print(f"[{self.lib_name}] DEBUG: {message}")
            except:
                pass


# 安全的日志适配器 - 避免递归调用但提供基本功能（用于特殊情况）
class SafeLoggerAdapter:
    """安全的日志适配器，避免递归调用但提供基本日志功能"""

    def __init__(self, lib_name: str = "wxauto"):
        self.lib_name = lib_name

    def set_lib_name(self, lib_name: str):
        """设置库名称"""
        self.lib_name = lib_name

    def info(self, message: str):
        """INFO日志"""
        try:
            print(f"[{self.lib_name}] INFO: {message}")
        except:
            pass

    def warning(self, message: str):
        """WARNING日志"""
        try:
            print(f"[{self.lib_name}] WARNING: {message}")
        except:
            pass

    def error(self, message: str, exc_info=None):
        """ERROR日志"""
        try:
            if exc_info:
                import traceback
                tb_str = traceback.format_exc()
                message = f"{message}\n{tb_str}"
            print(f"[{self.lib_name}] ERROR: {message}")
        except:
            pass

    def debug(self, message: str):
        """DEBUG日志"""
        try:
            print(f"[{self.lib_name}] DEBUG: {message}")
        except:
            pass


# 创建统一日志适配器实例 - 用于API路由
logger = UnifiedLoggerAdapter("Flask")
