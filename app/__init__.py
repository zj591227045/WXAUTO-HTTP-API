from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import Config

def create_app():
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