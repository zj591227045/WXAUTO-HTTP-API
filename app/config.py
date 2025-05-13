import os
import logging
import sys
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# 确保config_manager可以被导入
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入配置管理模块
try:
    import config_manager
except ImportError:
    # 如果无法导入，则使用环境变量
    load_dotenv()
    config_manager = None

class Config:
    # 从配置文件或环境变量加载配置
    if config_manager:
        # 确保目录存在
        config_manager.ensure_dirs()

        # 加载应用配置
        app_config = config_manager.load_app_config()

        # API配置
        API_KEYS = app_config.get('api_keys', ['test-key-2'])

        # Flask配置
        PORT = app_config.get('port', 5000)

        # 微信库选择配置
        WECHAT_LIB = app_config.get('wechat_lib', 'wxauto').lower()
    else:
        # 如果无法导入config_manager，则使用环境变量
        API_KEYS = os.getenv('API_KEYS', 'test-key-2').split(',')
        PORT = int(os.getenv('PORT', 5000))
        WECHAT_LIB = os.getenv('WECHAT_LIB', 'wxauto').lower()

    # 其他固定配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    DEBUG = True
    HOST = '0.0.0.0'  # 允许所有IP访问

    # 限流配置
    RATELIMIT_DEFAULT = "100 per minute"
    RATELIMIT_STORAGE_URL = "memory://"

    # 日志配置
    LOG_LEVEL = logging.INFO  # 设置为INFO级别，减少DEBUG日志
    LOG_FORMAT = '%(asctime)s - [%(wechat_lib)s] - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  # 统一的时间戳格式
    LOG_MAX_BYTES = 20 * 1024 * 1024  # 20MB
    LOG_BACKUP_COUNT = 5  # 保留5个备份文件

    # 日志文件路径
    DATA_DIR = Path("data")
    API_DIR = DATA_DIR / "api"
    LOGS_DIR = API_DIR / "logs"
    LOG_FILENAME = f"api_{datetime.now().strftime('%Y%m%d')}.log"
    LOG_FILE = str(LOGS_DIR / LOG_FILENAME)

    # 微信监控配置
    WECHAT_CHECK_INTERVAL = int(os.getenv('WECHAT_CHECK_INTERVAL', 60))  # 连接检查间隔（秒）
    WECHAT_AUTO_RECONNECT = os.getenv('WECHAT_AUTO_RECONNECT', 'true').lower() == 'true'
    WECHAT_RECONNECT_DELAY = int(os.getenv('WECHAT_RECONNECT_DELAY', 30))  # 重连延迟（秒）
    WECHAT_MAX_RETRY = int(os.getenv('WECHAT_MAX_RETRY', 3))  # 最大重试次数