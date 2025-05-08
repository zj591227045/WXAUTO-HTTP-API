from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import Config
import logging

def create_app():
    # 配置 Werkzeug 日志
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)  # 只显示错误级别的日志

    # 创建 Flask 应用
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化限流器
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[Config.RATELIMIT_DEFAULT],
        storage_uri=Config.RATELIMIT_STORAGE_URL
    )

    # 注册蓝图
    from app.api.routes import api_bp
    from app.api.admin_routes import admin_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    @app.route('/health')
    def health_check():
        return {'status': 'ok'}

    return app