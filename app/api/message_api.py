"""
消息相关API
"""

import os
import sys
import time
import logging
from flask import Blueprint, request, jsonify
from app.auth import require_api_key
from app.wechat_adapter import WeChatAdapter
import config_manager

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
message_bp = Blueprint('message', __name__)

# 应用wxauto补丁
wxauto_patch_path = os.path.join(os.getcwd(), "wxauto_patch.py")
if os.path.exists(wxauto_patch_path):
    sys.path.insert(0, os.getcwd())
    try:
        import wxauto_patch
        logger.info("已应用wxauto补丁，增强了图片保存功能")
    except Exception as e:
        logger.error(f"应用wxauto补丁失败: {str(e)}")

@message_bp.route('/get-next-new', methods=['GET'])
@require_api_key
def get_next_new_message():
    """获取下一条新消息"""
    try:
        # 获取参数
        savepic = request.args.get('savepic', 'false').lower() == 'true'
        savefile = request.args.get('savefile', 'false').lower() == 'true'
        savevoice = request.args.get('savevoice', 'false').lower() == 'true'
        parseurl = request.args.get('parseurl', 'false').lower() == 'true'
        
        # 确保临时目录存在
        config_manager.ensure_dirs()
        
        # 获取微信适配器
        adapter = WeChatAdapter()
        
        # 获取下一条新消息
        messages = adapter.GetNextNewMessage(
            savepic=savepic,
            savefile=savefile,
            savevoice=savevoice,
            parseurl=parseurl
        )
        
        # 转换消息格式
        result = {}
        if messages:
            for chat_name, msg_list in messages.items():
                result[chat_name] = []
                for msg in msg_list:
                    # 检查文件路径是否存在
                    file_path = None
                    if hasattr(msg, 'content') and msg.content and isinstance(msg.content, str):
                        if os.path.exists(msg.content):
                            file_path = msg.content
                    
                    # 构建消息对象
                    msg_obj = {
                        'id': getattr(msg, 'id', None),
                        'type': getattr(msg, 'type', None),
                        'sender': getattr(msg, 'sender', None),
                        'sender_remark': getattr(msg, 'sender_remark', None) if hasattr(msg, 'sender_remark') else None,
                        'content': getattr(msg, 'content', None),
                        'file_path': file_path,
                        'mtype': None  # 消息类型，如图片、文件等
                    }
                    
                    # 判断消息类型
                    if file_path and file_path.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        msg_obj['mtype'] = 'image'
                    elif file_path and file_path.endswith(('.mp3', '.wav', '.amr')):
                        msg_obj['mtype'] = 'voice'
                    elif file_path:
                        msg_obj['mtype'] = 'file'
                    
                    result[chat_name].append(msg_obj)
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'messages': result
            }
        })
    except Exception as e:
        logger.error(f"获取下一条新消息失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}',
            'data': None
        })
