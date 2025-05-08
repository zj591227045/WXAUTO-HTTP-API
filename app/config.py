import os
import logging
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

load_dotenv()

class Config:
    # API配置
    API_KEYS = os.getenv('API_KEYS', '').split(',')
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')

    # Flask配置
    DEBUG = True
    HOST = '0.0.0.0'  # 允许所有IP访问
    PORT = int(os.getenv('PORT', 5000))

    # 限流配置
    RATELIMIT_DEFAULT = "100 per minute"
    RATELIMIT_STORAGE_URL = "memory://"

    # 日志配置
    LOG_LEVEL = logging.INFO  # 设置为INFO级别，减少DEBUG日志
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  # 统一的时间戳格式

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

    # 微信库选择配置
    # 可选值: 'wxauto', 'wxautox'
    WECHAT_LIB = os.getenv('WECHAT_LIB', 'wxauto').lower()  # 默认使用wxauto