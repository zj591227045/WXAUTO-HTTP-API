import threading
import time
import pythoncom
from wxautox import WeChat
from app.logs import logger
from app.config import Config

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

    def initialize(self):
        """初始化微信实例"""
        with self._lock:
            if not self._instance:
                try:
                    # 初始化COM环境
                    pythoncom.CoInitialize()
                    self._instance = WeChat()
                    if Config.WECHAT_AUTO_RECONNECT:
                        self._start_monitor()
                    self._retry_count = 0
                    return True
                except Exception as e:
                    logger.error(f"微信初始化失败: {str(e)}")
                    # 出错时确保COM环境被清理
                    pythoncom.CoUninitialize()
                    return False
            return True

    def get_instance(self):
        """获取微信实例"""
        return self._instance

    def check_connection(self):
        """检查微信连接状态"""
        if not self._instance:
            return False
        
        try:
            self._instance.GetSessionList()
            self._retry_count = 0  # 重置重试计数
            return True
        except Exception as e:
            logger.error(f"微信连接检查失败: {str(e)}")
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