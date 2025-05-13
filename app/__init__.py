import os
import sys
import logging

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 确保父目录在Python路径中
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from flask import Flask
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError as e:
    logging.error(f"导入Flask相关模块失败: {str(e)}")
    logging.error("请确保已安装Flask和flask-limiter")
    raise

try:
    from app.config import Config
except ImportError:
    try:
        # 尝试直接导入
        from config import Config
    except ImportError:
        logging.error("无法导入Config模块，请确保app/config.py文件存在")
        raise

def create_app():
    """创建并配置Flask应用"""
    logging.info("开始创建Flask应用...")

    # 配置 Werkzeug 日志
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)  # 只显示错误级别的日志

    # 确保所有日志处理器立即刷新
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.DEBUG)
        handler.flush()

    # 初始化微信相关配置
    try:
        logging.info("正在初始化微信相关配置...")
        from app.wechat_init import initialize as init_wechat
        init_wechat()
        logging.info("微信相关配置初始化完成")
    except ImportError as e:
        logging.error(f"导入微信初始化模块失败: {str(e)}")
        logging.warning("将继续创建Flask应用，但微信功能可能不可用")
    except Exception as e:
        logging.error(f"初始化微信配置时出错: {str(e)}")
        logging.warning("将继续创建Flask应用，但微信功能可能不可用")

    # 导入插件管理模块，确保它被初始化
    try:
        logging.info("正在导入插件管理模块...")
        from app import plugin_manager
        logging.info("插件管理模块导入成功")
    except ImportError as e:
        logging.error(f"导入插件管理模块失败: {str(e)}")
        logging.warning("将继续创建Flask应用，但插件功能可能不可用")

    # 创建 Flask 应用
    logging.info("正在创建Flask实例...")
    app = Flask(__name__)
    app.config.from_object(Config)
    logging.info("Flask实例创建成功")

    # 配置Flask日志处理
    if not app.debug:
        # 在非调试模式下，禁用自动重载器
        app.config['USE_RELOADER'] = False
        logging.info("已禁用Flask自动重载器")

    # 初始化限流器
    try:
        logging.info("正在初始化限流器...")
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[Config.RATELIMIT_DEFAULT],
            storage_uri=Config.RATELIMIT_STORAGE_URL
        )
        logging.info("限流器初始化成功")
    except Exception as e:
        logging.error(f"初始化限流器时出错: {str(e)}")
        logging.warning("将继续创建Flask应用，但API限流功能可能不可用")

    # 注册蓝图
    try:
        logging.info("正在注册蓝图...")
        try:
            from app.api.routes import api_bp
            from app.api.admin_routes import admin_bp
            from app.api.plugin_routes import plugin_bp
        except ImportError as e:
            logging.error(f"导入蓝图模块失败: {str(e)}")
            logging.error("请确保app/api目录下的routes.py、admin_routes.py和plugin_routes.py文件存在")
            raise

        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        app.register_blueprint(plugin_bp, url_prefix='/admin/plugins')
        logging.info("蓝图注册成功")
    except Exception as e:
        logging.error(f"注册蓝图时出错: {str(e)}")
        logging.error("无法继续创建Flask应用")
        raise

    # 添加健康检查路由
    @app.route('/health')
    def health_check():
        """健康检查路由"""
        return {'status': 'ok'}

    logging.info("Flask应用创建完成")
    return app