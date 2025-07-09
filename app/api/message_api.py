"""
消息相关API
"""

import os
import sys
import time
import logging
from flask import Blueprint, request, jsonify
from app.auth import require_api_key
from app.wechat import wechat_manager
import config_manager

# 使用统一日志系统
from app.unified_logger import logger

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
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 获取参数
        savepic = request.args.get('savepic', 'false').lower() == 'true'
        savefile = request.args.get('savefile', 'false').lower() == 'true'
        savevoice = request.args.get('savevoice', 'false').lower() == 'true'
        parseurl = request.args.get('parseurl', 'false').lower() == 'true'
        filter_mute = request.args.get('filter_mute', 'false').lower() == 'true'

        # 确保临时目录存在
        config_manager.ensure_dirs()

        # 获取当前使用的库
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'

        # 根据不同的库构建不同的参数
        if lib_name == 'wxautox':
            # wxautox的GetNextNewMessage只支持filter_mute参数
            params = {
                'filter_mute': filter_mute
            }
        else:
            # wxauto的GetNextNewMessage可能不支持任何参数，使用空参数
            params = {}

        # 获取下一条新消息
        messages = wx_instance.GetNextNewMessage(**params)
        
        # 转换消息格式
        result = {}
        if messages:
            if isinstance(messages, dict):
                # wxauto实际返回字典格式: {'chat_name': '消息测试', 'chat_type': 'group', 'msg': [...]}
                if 'msg' in messages and isinstance(messages['msg'], list):
                    # 使用正确的chat_name，而不是硬编码的"新消息"
                    chat_name = messages.get('chat_name', '未知聊天')
                    result[chat_name] = []
                    for msg in messages['msg']:
                        try:
                            # 检查msg是否已经是字典格式（适配器已转换）
                            if isinstance(msg, dict):
                                # 已经是字典格式，直接使用并补充缺失字段
                                msg_obj = {
                                    'id': msg.get('id', None),
                                    'type': msg.get('type', None),
                                    'sender': msg.get('sender', None),
                                    'sender_remark': msg.get('sender_remark', None),
                                    'content': msg.get('content', str(msg)),
                                    'time': msg.get('time', None),
                                    'file_path': msg.get('file_path', None),
                                    'mtype': msg.get('mtype', None)
                                }
                            else:
                                # 原始消息对象，需要转换
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
                                    'content': getattr(msg, 'content', str(msg)),
                                    'time': getattr(msg, 'time', None),
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
                        except Exception as e:
                            logger.error(f"处理消息时出错: {str(e)}")
                            # 添加错误消息
                            result[chat_name].append({
                                'type': 'error',
                                'content': f'消息处理错误: {str(e)}',
                                'sender': '',
                                'time': '',
                                'id': '',
                                'mtype': None,
                                'sender_remark': None,
                                'file_path': None
                            })
                else:
                    # 可能是其他字典格式: {chat_name: [messages]}
                    for chat_name, msg_list in messages.items():
                        if isinstance(msg_list, list):
                            result[chat_name] = []
                            for msg in msg_list:
                                try:
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
                                        'content': getattr(msg, 'content', str(msg)),
                                        'time': getattr(msg, 'time', None),
                                        'file_path': file_path,
                                        'mtype': None
                                    }

                                    # 判断消息类型
                                    if file_path and file_path.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                        msg_obj['mtype'] = 'image'
                                    elif file_path and file_path.endswith(('.mp3', '.wav', '.amr')):
                                        msg_obj['mtype'] = 'voice'
                                    elif file_path:
                                        msg_obj['mtype'] = 'file'

                                    result[chat_name].append(msg_obj)
                                except Exception as e:
                                    logger.error(f"处理消息时出错: {str(e)}")
                                    # 添加错误消息
                                    result[chat_name].append({
                                        'type': 'error',
                                        'content': f'消息处理错误: {str(e)}',
                                        'sender': '',
                                        'time': '',
                                        'id': '',
                                        'mtype': None,
                                        'sender_remark': None,
                                        'file_path': None
                                    })
            elif isinstance(messages, list):
                # 如果wxauto确实返回列表格式（向后兼容）
                result["新消息"] = []
                for msg in messages:
                    try:
                        # 检查msg是否已经是字典格式（适配器已转换）
                        if isinstance(msg, dict):
                            # 已经是字典格式，直接使用并补充缺失字段
                            msg_obj = {
                                'id': msg.get('id', None),
                                'type': msg.get('type', None),
                                'sender': msg.get('sender', None),
                                'sender_remark': msg.get('sender_remark', None),
                                'content': msg.get('content', str(msg)),
                                'time': msg.get('time', None),
                                'file_path': msg.get('file_path', None),
                                'mtype': msg.get('mtype', None)
                            }
                        else:
                            # 原始消息对象，需要转换
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
                                'content': getattr(msg, 'content', str(msg)),
                                'time': getattr(msg, 'time', None),
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

                        result["新消息"].append(msg_obj)
                    except Exception as e:
                        logger.error(f"处理消息时出错: {str(e)}")
                        # 添加错误消息
                        result["新消息"].append({
                            'type': 'error',
                            'content': f'消息处理错误: {str(e)}',
                            'sender': '',
                            'time': '',
                            'id': '',
                            'mtype': None,
                            'sender_remark': None,
                            'file_path': None
                        })
                else:
                    # 可能是其他字典格式，假设是 {chat_name: [messages]} 格式
                    for chat_name, msg_list in messages.items():
                        if isinstance(msg_list, list):
                            result[chat_name] = []
                            for msg in msg_list:
                                try:
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
                                        'content': getattr(msg, 'content', str(msg)),
                                        'time': getattr(msg, 'time', None),
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
                                except Exception as e:
                                    logger.error(f"处理其他字典格式消息时出错: {str(e)}")
                                    # 添加错误消息
                                    result[chat_name].append({
                                        'type': 'error',
                                        'content': f'消息处理错误: {str(e)}',
                                        'sender': '',
                                        'time': '',
                                        'id': '',
                                        'mtype': None,
                                        'sender_remark': None,
                                        'file_path': None
                                    })
        
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
