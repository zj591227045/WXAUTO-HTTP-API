import os
import logging
from dotenv import load_dotenv

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
    LOG_LEVEL = logging.DEBUG  # 设置为DEBUG级别
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'app.log'

    # 微信监控配置
    WECHAT_CHECK_INTERVAL = int(os.getenv('WECHAT_CHECK_INTERVAL', 60))  # 连接检查间隔（秒）
    WECHAT_AUTO_RECONNECT = os.getenv('WECHAT_AUTO_RECONNECT', 'true').lower() == 'true'
    WECHAT_RECONNECT_DELAY = int(os.getenv('WECHAT_RECONNECT_DELAY', 30))  # 重连延迟（秒）
    WECHAT_MAX_RETRY = int(os.getenv('WECHAT_MAX_RETRY', 3))  # 最大重试次数