"""
插件管理API路由
提供wxauto和wxautox库的安装和管理功能
"""

import os
import sys
import tempfile
import shutil
import logging
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from app.auth import require_api_key
from app import plugin_manager
import config_manager

# 使用统一日志系统
from app.unified_logger import logger

# 创建蓝图
plugin_bp = Blueprint('plugins', __name__)

@plugin_bp.route('/status', methods=['GET'])
@require_api_key
def get_plugins_status():
    """获取插件状态"""
    try:
        status = plugin_manager.get_plugins_status()
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': status
        })
    except Exception as e:
        logger.error(f"获取插件状态失败: {str(e)}")
        return jsonify({
            'code': 5001,
            'message': f'获取插件状态失败: {str(e)}',
            'data': None
        }), 500

@plugin_bp.route('/install-wxauto', methods=['POST'])
@require_api_key
def install_wxauto():
    """安装/修复wxauto库"""
    try:
        # 检查wxauto文件夹是否存在
        wxauto_path = os.path.join(os.getcwd(), "wxauto")
        if not os.path.exists(wxauto_path) or not os.path.isdir(wxauto_path):
            return jsonify({
                'code': 4001,
                'message': 'wxauto文件夹不存在',
                'data': None
            }), 400
        
        # 检查wxauto文件夹中是否包含必要的文件
        init_file = os.path.join(wxauto_path, "wxauto", "__init__.py")
        wxauto_file = os.path.join(wxauto_path, "wxauto", "wxauto.py")
        
        if not os.path.exists(init_file) or not os.path.exists(wxauto_file):
            return jsonify({
                'code': 4002,
                'message': 'wxauto文件夹结构不完整，缺少必要文件',
                'data': None
            }), 400
        
        # 确保本地wxauto文件夹在Python路径中
        if wxauto_path not in sys.path:
            sys.path.insert(0, wxauto_path)
        
        # 尝试导入
        try:
            import wxauto
            import importlib
            importlib.reload(wxauto)  # 重新加载模块，确保使用最新版本
            
            # 更新配置文件
            config = config_manager.load_app_config()
            config['wechat_lib'] = 'wxauto'
            config_manager.save_app_config(config)
            
            return jsonify({
                'code': 0,
                'message': 'wxauto库安装/修复成功',
                'data': {'path': wxauto_path}
            })
        except ImportError as e:
            return jsonify({
                'code': 4003,
                'message': f'wxauto库导入失败: {str(e)}',
                'data': None
            }), 500
    except Exception as e:
        logger.error(f"安装/修复wxauto库失败: {str(e)}")
        return jsonify({
            'code': 5001,
            'message': f'安装/修复wxauto库失败: {str(e)}',
            'data': None
        }), 500

@plugin_bp.route('/upload-wxautox', methods=['POST'])
@require_api_key
def upload_wxautox():
    """上传并安装wxautox库"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'code': 4001,
                'message': '没有上传文件',
                'data': None
            }), 400
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({
                'code': 4002,
                'message': '文件名为空',
                'data': None
            }), 400
        
        # 检查文件扩展名
        if not file.filename.endswith('.whl'):
            return jsonify({
                'code': 4003,
                'message': '文件不是有效的wheel文件',
                'data': None
            }), 400
        
        # 检查文件名是否包含wxautox
        if 'wxautox-' not in file.filename:
            return jsonify({
                'code': 4004,
                'message': '文件不是wxautox wheel文件',
                'data': None
            }), 400
        
        # 确保临时目录存在
        config_manager.ensure_dirs()
        temp_dir = config_manager.TEMP_DIR
        
        # 保存文件到临时目录
        filename = secure_filename(file.filename)
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        logger.info(f"wxautox wheel文件已保存到: {file_path}")
        
        # 安装wxautox
        success, message = plugin_manager.install_wxautox(file_path)
        
        if success:
            return jsonify({
                'code': 0,
                'message': message,
                'data': {'file_path': file_path}
            })
        else:
            return jsonify({
                'code': 4005,
                'message': message,
                'data': None
            }), 500
    except Exception as e:
        logger.error(f"上传并安装wxautox库失败: {str(e)}")
        return jsonify({
            'code': 5001,
            'message': f'上传并安装wxautox库失败: {str(e)}',
            'data': None
        }), 500
