from functools import wraps
from flask import request, jsonify
from app.config import Config

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                'code': 1001,
                'message': '缺少API密钥',
                'data': None
            }), 401

        # 动态获取最新的API密钥列表
        current_api_keys = Config.get_api_keys()
        if api_key not in current_api_keys:
            return jsonify({
                'code': 1001,
                'message': 'API密钥无效',
                'data': None
            }), 401

        return f(*args, **kwargs)
    return decorated_function