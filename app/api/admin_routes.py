"""
管理员API路由
提供配置重载、服务状态查询等功能
"""

from flask import Blueprint, jsonify, request, g
from app.auth import require_api_key
from app.unified_logger import logger
import importlib
import os
import time
from app.config import Config

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/reload-config', methods=['POST'])
@require_api_key
def reload_config():
    """重新加载配置"""
    try:
        # 重新加载配置模块
        importlib.reload(importlib.import_module('app.config'))
        
        # 记录日志
        logger.info("配置已重新加载")
        
        return jsonify({
            'code': 0,
            'message': '配置已重新加载',
            'data': None
        })
    except Exception as e:
        logger.error(f"重新加载配置失败: {str(e)}")
        return jsonify({
            'code': 5001,
            'message': f'重新加载配置失败: {str(e)}',
            'data': None
        }), 500

@admin_bp.route('/stats', methods=['GET'])
@require_api_key
def get_stats():
    """获取服务统计信息"""
    try:
        # 获取进程信息
        import psutil
        process = psutil.Process(os.getpid())
        
        # CPU使用率
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # 内存使用
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        
        # 运行时间
        start_time = process.create_time()
        uptime_seconds = int(time.time() - start_time)
        
        # 返回统计信息
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'uptime_seconds': uptime_seconds,
                'pid': os.getpid(),
                'threads': len(process.threads()),
                'connections': len(process.connections())
            }
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return jsonify({
            'code': 5002,
            'message': f'获取统计信息失败: {str(e)}',
            'data': None
        }), 500
