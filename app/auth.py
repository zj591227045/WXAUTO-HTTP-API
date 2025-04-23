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
        
        if api_key not in Config.API_KEYS:
            return jsonify({
                'code': 1001,
                'message': 'API密钥无效',
                'data': None
            }), 401
            
        return f(*args, **kwargs)
    return decorated_function