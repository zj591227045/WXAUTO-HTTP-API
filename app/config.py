import os
import logging
import sys
from datetime import datetime
from pathlib import Path

# 确保config_manager可以被导入
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入配置管理模块
try:
    # 首先尝试从app包导入
    from app import config_manager
except ImportError:
    try:
        # 如果失败，尝试直接导入
        import config_manager
    except ImportError:
        # 如果无法导入config_manager，设置为None
        config_manager = None

class Config:
    # 从配置文件或环境变量加载配置
    if config_manager:
        # 确保目录存在
        config_manager.ensure_dirs()

        # 加载应用配置
        app_config = config_manager.load_app_config()

        # Flask配置
        PORT = app_config.get('port', 5000)

        # 微信库选择配置
        configured_lib = app_config.get('wechat_lib', 'wxauto').lower()

        # 验证配置的库是否可用
        try:
            from app.wechat_lib_detector import detector
            valid, message = detector.validate_library_choice(configured_lib)
            if valid:
                WECHAT_LIB = configured_lib
            else:
                # 如果配置的库不可用，尝试获取推荐的库
                recommended = detector.get_library_switch_recommendation(configured_lib)
                if recommended:
                    WECHAT_LIB = recommended
                    print(f"警告: 配置的库 '{configured_lib}' 不可用，自动切换到 '{recommended}'")
                else:
                    WECHAT_LIB = 'wxauto'  # 默认值
                    print(f"警告: 没有可用的微信自动化库，使用默认值 'wxauto'")
        except Exception as e:
            # 如果检测失败，使用配置值
            WECHAT_LIB = configured_lib
            print(f"库检测失败，使用配置值: {e}")
    else:
        # 如果无法导入config_manager，则使用默认值
        PORT = 5000
        WECHAT_LIB = 'wxauto'

    @staticmethod
    def get_api_keys():
        """动态获取API密钥列表"""
        if config_manager:
            try:
                # 每次都重新加载配置文件以获取最新的API密钥
                app_config = config_manager.load_app_config()
                return app_config.get('api_keys', ['test-key-2'])
            except Exception:
                # 如果加载失败，使用默认值
                return ['test-key-2']
        else:
            # 如果无法导入config_manager，则使用默认值
            return ['test-key-2']

    # 为了向后兼容，我们需要在类定义后动态设置API_KEYS属性

    # 其他固定配置
    SECRET_KEY = 'your-secret-key'
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

    @staticmethod
    def get_current_log_file():
        """获取当前日期的日志文件路径"""
        log_filename = f"api_{datetime.now().strftime('%Y%m%d')}.log"
        return str(Config.LOGS_DIR / log_filename)

    # 微信监控配置
    WECHAT_CHECK_INTERVAL = 60  # 连接检查间隔（秒）
    WECHAT_AUTO_RECONNECT = True  # 自动重连
    WECHAT_RECONNECT_DELAY = 30  # 重连延迟（秒）
    WECHAT_MAX_RETRY = 3  # 最大重试次数


# 创建一个动态属性描述符，用于API_KEYS
class DynamicAPIKeys:
    def __get__(self, obj, objtype=None):
        # 忽略obj和objtype参数，直接返回最新的API密钥
        return Config.get_api_keys()

# 为了向后兼容，动态设置API_KEYS属性
# 这样每次访问Config.API_KEYS时都会调用get_api_keys()方法获取最新的配置
Config.API_KEYS = DynamicAPIKeys()