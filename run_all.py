import sys
import threading
import traceback
from datetime import datetime
import pythoncom
import os
import logging
import asyncio
import multiprocessing
from pathlib import Path

from app import create_app
from app.logs import logger
from app.services.monitor_service import MessageMonitorService
from app.services.api_client import WxAutoApiClient
from app.utils.state_manager import StateManager
from app.utils.storage_manager import StorageManager
from app.ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication

# API 配置
API_CONFIG = {
    'base_url': 'http://0.0.0.0:5000',
    'api_key': 'test-key-2'
}

# 存储配置
STORAGE_CONFIG = {
    'db_path': os.path.join(os.path.dirname(__file__), 'data', 'monitor.db')
}

# 监控配置
MONITOR_CONFIG = {
    'max_targets': 30,
    'check_new_interval': 5,  # 检查新会话间隔（秒）
    'check_messages_interval': 5,  # 检查消息间隔（秒）
    'cleanup_interval': 60,  # 清理间隔（秒）
    'inactive_timeout': 1800  # 不活跃超时（秒）
}

def run_flask_api():
    """运行 Flask API 服务"""
    try:
        app = create_app()
        logger.info("正在启动 Flask API 服务...")
        logger.info(f"API 监听地址: 0.0.0.0:5000")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Flask API 服务启动失败: {str(e)}")
        logger.error(traceback.format_exc())

class MessageMonitorService:
    """消息监控服务"""

    def __init__(self, api_client: WxAutoApiClient,
                 state_manager: StateManager,
                 storage: StorageManager):
        """
        初始化监控服务

        Args:
            api_client: API客户端
            state_manager: 状态管理器
            storage: 存储管理器
        """
        self.api_client = api_client
        self.state_manager = state_manager
        self.storage = storage
        self.scheduler = None
        self.listen_targets = set()
        self.max_targets = MONITOR_CONFIG['max_targets']

    async def initialize(self) -> bool:
        """
        初始化服务

        Returns:
            是否初始化成功
        """
        try:
            # 初始化微信连接
            success = await self.api_client.initialize_wechat()
            if not success:
                return False

            # 初始化调度器
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            self.scheduler = AsyncIOScheduler()

            # 添加定时任务
            self.scheduler.add_job(
                self.check_new_chats,
                'interval',
                seconds=MONITOR_CONFIG['check_new_interval']
            )
            self.scheduler.add_job(
                self.check_listen_messages,
                'interval',
                seconds=MONITOR_CONFIG['check_messages_interval']
            )
            self.scheduler.add_job(
                self.clean_inactive_targets,
                'interval',
                seconds=MONITOR_CONFIG['cleanup_interval']
            )

            return True

        except Exception as e:
            logger.error(f"初始化监控服务失败: {str(e)}")
            return False

    async def start(self):
        """启动服务"""
        if self.scheduler:
            self.scheduler.start()

    async def stop(self):
        """停止服务"""
        if self.scheduler:
            self.scheduler.shutdown()

    async def check_new_chats(self):
        """检查新的未读会话"""
        try:
            # 获取新的未读消息
            new_messages = await self.api_client.get_next_new_message()
            if not new_messages:
                return

            # 处理每个会话的新消息
            messages = new_messages.get('messages', {})
            for chat_name, msg_list in messages.items():
                if chat_name not in self.listen_targets and len(self.listen_targets) < self.max_targets:
                    # 添加到监听列表
                    success = await self.add_listen_target(chat_name)
                    if success:
                        logger.info(f"添加新的监听目标: {chat_name}")

        except Exception as e:
            logger.error(f"检查新会话失败: {str(e)}")

    async def check_listen_messages(self):
        """检查监听列表的消息"""
        try:
            messages = await self.api_client.get_listen_messages()
            if messages:
                # 更新状态
                self.state_manager.set_state('new_messages', messages)
                # 保存消息
                await self.storage.save_messages(messages)

        except Exception as e:
            logger.error(f"获取监听消息失败: {str(e)}")

    async def clean_inactive_targets(self):
        """清理不活跃的监听对象"""
        try:
            current_time = datetime.now()
            inactive_targets = []

            # 获取所有监听对象的最后活跃时间
            for target in self.listen_targets:
                last_active = await self.storage.get_last_active_time(target)
                if last_active and (current_time - last_active).seconds > MONITOR_CONFIG['inactive_timeout']:
                    inactive_targets.append(target)

            # 移除不活跃的目标
            for target in inactive_targets:
                await self.remove_listen_target(target)
                logger.info(f"移除不活跃的监听目标: {target}")

        except Exception as e:
            logger.error(f"清理不活跃目标失败: {str(e)}")

    async def add_listen_target(self, who: str) -> bool:
        """
        添加监听目标

        Args:
            who: 监听对象名称

        Returns:
            是否添加成功
        """
        if len(self.listen_targets) >= self.max_targets:
            return False

        try:
            success = await self.api_client.add_listen_target(who)
            if success:
                self.listen_targets.add(who)
                self.state_manager.set_state('listen_targets', list(self.listen_targets))
            return success
        except Exception as e:
            logger.error(f"添加监听目标失败: {str(e)}")
            return False

    async def remove_listen_target(self, who: str) -> bool:
        """
        移除监听目标

        Args:
            who: 监听对象名称

        Returns:
            是否移除成功
        """
        try:
            success = await self.api_client.remove_listen_target(who)
            if success:
                self.listen_targets.remove(who)
                self.state_manager.set_state('listen_targets', list(self.listen_targets))
            return success
        except Exception as e:
            logger.error(f"移除监听目标失败: {str(e)}")
            return False

async def run_api_client(api_client):
    """运行API客户端"""
    try:
        await api_client.initialize_wechat()
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"API客户端运行错误: {e}", exc_info=True)

async def run_monitor_service(monitor_service):
    """运行消息监控服务"""
    try:
        await monitor_service.start()
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"监控服务运行错误: {e}", exc_info=True)

def run_ui(monitor_service, state_manager):
    """运行UI界面"""
    try:
        app = QApplication(sys.argv)
        window = MainWindow(monitor_service, state_manager)
        window.show()
        app.exec()
    except Exception as e:
        logger.error(f"UI运行错误: {e}", exc_info=True)

async def main():
    try:
        # 创建数据目录
        data_dir = os.path.dirname(STORAGE_CONFIG['db_path'])
        os.makedirs(data_dir, exist_ok=True)

        # 初始化日志
        # 确保日志目录存在
        log_dir = Path("data/api/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # 生成日志文件名
        log_filename = f"api_{datetime.now().strftime('%Y%m%d')}.log"
        log_file = log_dir / log_filename

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        # 启动 Flask API 服务（在单独的进程中）
        flask_process = multiprocessing.Process(target=run_flask_api)
        flask_process.start()
        logger.info("等待 Flask API 服务启动...")
        await asyncio.sleep(2)  # 等待 Flask API 服务启动

        # 创建共享服务和管理器
        state_manager = StateManager()
        storage = StorageManager(db_path=STORAGE_CONFIG['db_path'])

        api_client = WxAutoApiClient(
            base_url=API_CONFIG['base_url'],
            api_key=API_CONFIG['api_key']
        )

        monitor_service = MessageMonitorService(
            api_client=api_client,
            state_manager=state_manager,
            storage=storage
        )

        # 初始化监控服务
        success = await monitor_service.initialize()
        if not success:
            logger.error("无法初始化微信监控服务")
            flask_process.terminate()
            return 1

        try:
            # 启动所有服务
            await asyncio.gather(
                run_api_client(api_client),
                run_monitor_service(monitor_service),
                asyncio.to_thread(run_ui, monitor_service, state_manager)
            )
        finally:
            # 确保在主程序退出时关闭 Flask API 服务
            flask_process.terminate()
            flask_process.join()

        return 0

    except Exception as e:
        logger.error(f"主程序运行错误: {e}", exc_info=True)
        if 'flask_process' in locals():
            flask_process.terminate()
            flask_process.join()
        return 1

if __name__ == "__main__":
    try:
        logger.info("=" * 50)
        logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("正在启动所有服务...")

        if sys.platform == 'win32':
            # Windows平台特殊处理
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            multiprocessing.freeze_support()  # 支持打包后运行

        loop = asyncio.get_event_loop()
        exit_code = loop.run_until_complete(main())
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"程序启动失败: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if 'loop' in locals():
            loop.close()