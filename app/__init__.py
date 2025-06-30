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
            # 导入新的API蓝图
            from app.api.chat_routes import chat_bp
            from app.api.group_routes import group_bp
            from app.api.friend_routes import friend_bp
            from app.api.wechat_routes import wechat_bp
            from app.api.message_operations import message_ops_bp
            from app.api.moments_routes import moments_bp
            from app.api.auxiliary_routes import auxiliary_bp
        except ImportError as e:
            logging.error(f"导入蓝图模块失败: {str(e)}")
            logging.error("请确保app/api目录下的所有蓝图文件存在")
            raise

        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        app.register_blueprint(plugin_bp, url_prefix='/admin/plugins')
        # 注册新的API蓝图
        app.register_blueprint(chat_bp, url_prefix='/api/chat')
        app.register_blueprint(group_bp, url_prefix='/api/group')
        app.register_blueprint(friend_bp, url_prefix='/api/friend')
        app.register_blueprint(wechat_bp, url_prefix='/api/wechat')
        app.register_blueprint(message_ops_bp, url_prefix='/api/message')
        app.register_blueprint(moments_bp, url_prefix='/api/moments')
        app.register_blueprint(auxiliary_bp, url_prefix='/api/auxiliary')
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

    # 添加根路径重定向到API文档
    @app.route('/')
    def index():
        """根路径重定向到API文档"""
        from flask import redirect
        return redirect('/api-docs')

    # 添加API文档路由
    @app.route('/api-docs')
    def api_docs():
        """API文档路由"""
        from flask import render_template
        return render_template('api_docs.html')

    # 添加新版API文档路由
    @app.route('/api-docs-new')
    def api_docs_new():
        """新版API文档路由"""
        from flask import render_template
        return render_template('api_docs_new.html')

    # 添加模块化API文档路由
    @app.route('/api-docs-modular')
    def api_docs_modular():
        """模块化API文档路由"""
        from flask import render_template
        return render_template('api_docs_modular.html')

    # 添加日志查看路由
    @app.route('/logs')
    def view_logs():
        """日志查看页面"""
        from flask import render_template
        return render_template('logs.html')

    # 添加日志API路由
    @app.route('/api/logs/current')
    def get_current_logs():
        """获取当前日志内容"""
        from flask import jsonify
        import os
        from datetime import datetime

        try:
            # 构建当前日期的日志文件路径
            current_date = datetime.now().strftime('%Y%m%d')
            log_file_path = os.path.join('data', 'api', 'logs', f'api_{current_date}.log')

            if not os.path.exists(log_file_path):
                return jsonify({
                    'code': 404,
                    'message': '日志文件不存在',
                    'data': {'logs': [], 'file_path': log_file_path}
                })

            # 读取日志文件内容
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 只返回最后1000行日志，避免内存问题
            recent_lines = lines[-1000:] if len(lines) > 1000 else lines

            return jsonify({
                'code': 0,
                'message': '获取日志成功',
                'data': {
                    'logs': [line.rstrip() for line in recent_lines],
                    'total_lines': len(lines),
                    'returned_lines': len(recent_lines),
                    'file_path': log_file_path
                }
            })

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': f'读取日志失败: {str(e)}',
                'data': {'logs': [], 'error': str(e)}
            }), 500

    @app.route('/api/logs/tail')
    def get_log_tail():
        """获取日志文件的最新内容（类似tail命令）"""
        from flask import jsonify, request
        import os
        from datetime import datetime

        try:
            # 获取参数
            lines = request.args.get('lines', 100, type=int)
            offset = request.args.get('offset', 0, type=int)

            # 构建当前日期的日志文件路径
            current_date = datetime.now().strftime('%Y%m%d')
            log_file_path = os.path.join('data', 'api', 'logs', f'api_{current_date}.log')

            if not os.path.exists(log_file_path):
                return jsonify({
                    'code': 404,
                    'message': '日志文件不存在',
                    'data': {'logs': [], 'file_path': log_file_path}
                })

            # 读取日志文件内容
            with open(log_file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()

            # 计算要返回的行数范围
            total_lines = len(all_lines)
            start_index = max(0, total_lines - lines - offset)
            end_index = total_lines - offset

            selected_lines = all_lines[start_index:end_index]

            return jsonify({
                'code': 0,
                'message': '获取日志成功',
                'data': {
                    'logs': [line.rstrip() for line in selected_lines],
                    'total_lines': total_lines,
                    'returned_lines': len(selected_lines),
                    'start_index': start_index,
                    'end_index': end_index,
                    'file_path': log_file_path
                }
            })

        except Exception as e:
            return jsonify({
                'code': 500,
                'message': f'读取日志失败: {str(e)}',
                'data': {'logs': [], 'error': str(e)}
            }), 500

    logging.info("Flask应用创建完成")
    return app