import threading
import time
import pythoncom
from app.unified_logger import logger
from app.config import Config
from app.wechat_adapter import wechat_adapter

class WeChatManager:
    def __init__(self):
        self._instance = None
        self._lock = threading.Lock()
        self._last_check = 0
        self._check_interval = Config.WECHAT_CHECK_INTERVAL
        self._reconnect_delay = Config.WECHAT_RECONNECT_DELAY
        self._max_retry = Config.WECHAT_MAX_RETRY
        self._monitor_thread = None
        self._running = False
        self._retry_count = 0
        self._adapter = wechat_adapter

    def initialize(self):
        """初始化微信实例"""
        with self._lock:
            success = self._adapter.initialize()
            if success:
                self._instance = self._adapter.get_instance()
                if Config.WECHAT_AUTO_RECONNECT:
                    self._start_monitor()
                self._retry_count = 0
                # 暂时禁用日志管理器更新，避免递归调用
                lib_name = self._adapter.get_lib_name()
                # logger.set_lib_name(lib_name)
                logger.info(f"微信初始化成功，使用库: {lib_name}")
            return success

    def get_instance(self):
        """获取微信实例"""
        # 返回适配器而不是直接返回实例，这样可以使用适配器的参数处理功能
        return self._adapter

    def check_connection(self):
        """检查微信连接状态"""
        if not self._instance:
            return False

        try:
            result = self._adapter.check_connection()
            if result:
                self._retry_count = 0  # 重置重试计数
            return result
        except Exception as e:
            error_str = str(e)
            # 对于GetNextSiblingControl等控件访问错误，使用debug级别
            if any(keyword in error_str for keyword in ["GetNextSiblingControl", "NoneType", "Control", "uiautomation"]):
                logger.debug(f"微信连接检查失败（控件访问异常）: {error_str}")
            else:
                logger.error(f"微信连接检查失败: {error_str}")
            return False

    def _monitor_connection(self):
        """监控微信连接状态"""
        # 为监控线程初始化COM环境
        pythoncom.CoInitialize()

        while self._running:
            try:
                if not self.check_connection():
                    if self._retry_count < self._max_retry:
                        logger.warning(f"微信连接已断开，正在尝试重新连接 (尝试 {self._retry_count + 1}/{self._max_retry})...")
                        self._instance = None
                        self.initialize()
                        self._retry_count += 1
                        time.sleep(self._reconnect_delay)  # 重连等待时间
                    else:
                        logger.error("重连次数超过最大限制，停止自动重连")
                        self._running = False
                else:
                    time.sleep(self._check_interval)
            except Exception as e:
                logger.error(f"连接监控异常: {str(e)}")
                time.sleep(self._check_interval)

        # 监控线程结束时清理COM环境
        pythoncom.CoUninitialize()

    def _start_monitor(self):
        """启动监控线程"""
        if not self._monitor_thread or not self._monitor_thread.is_alive():
            self._running = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_connection,
                daemon=True,
                name="WeChatMonitor"
            )
            self._monitor_thread.start()
            logger.info("微信连接监控已启动")

    def stop(self):
        """停止监控"""
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
            logger.info("微信连接监控已停止")

# 创建全局WeChat管理器实例
wechat_manager = WeChatManager()