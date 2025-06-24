"""
Chat类相关API路由
实现Chat类的所有方法
"""

from flask import Blueprint, jsonify, request
from app.auth import require_api_key
from app.logs import logger
from app.wechat import wechat_manager
import time

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/show', methods=['POST'])
@require_api_key
def show_chat_window():
    """显示聊天窗口"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')

    if not who:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 获取聊天窗口
        listen = wx_instance.listen
        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 显示窗口
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name == 'wxautox':
            chat_wnd.Show()
        else:
            # wxauto库的处理方式
            if hasattr(wx_instance, '_handle_chat_window_method'):
                wx_instance._handle_chat_window_method(chat_wnd, 'Show')
            else:
                chat_wnd.Show()

        return jsonify({
            'code': 0,
            'message': '显示窗口成功',
            'data': {'who': who}
        })
    except Exception as e:
        logger.error(f"显示聊天窗口失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'显示窗口失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/load-more-messages', methods=['POST'])
@require_api_key
def load_more_messages():
    """加载更多聊天记录"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')

    if not who:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 获取聊天窗口
        listen = wx_instance.listen
        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 加载更多消息
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name == 'wxautox':
            chat_wnd.LoadMoreMessage()
        else:
            # wxauto库的处理方式
            if hasattr(wx_instance, '_handle_chat_window_method'):
                wx_instance._handle_chat_window_method(chat_wnd, 'LoadMoreMessage')
            else:
                chat_wnd.LoadMoreMessage()

        return jsonify({
            'code': 0,
            'message': '加载更多消息成功',
            'data': {'who': who}
        })
    except Exception as e:
        logger.error(f"加载更多消息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'加载更多消息失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/get-all-messages', methods=['GET'])
@require_api_key
def get_all_messages():
    """获取当前聊天窗口的所有消息"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    who = request.args.get('who')

    if not who:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 获取聊天窗口
        listen = wx_instance.listen
        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 获取所有消息
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name == 'wxautox':
            messages = chat_wnd.GetAllMessage()
        else:
            # wxauto库的处理方式
            if hasattr(wx_instance, '_handle_chat_window_method'):
                messages = wx_instance._handle_chat_window_method(chat_wnd, 'GetAllMessage')
            else:
                messages = chat_wnd.GetAllMessage()

        # 格式化消息
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                'type': getattr(msg, 'type', 'unknown'),
                'content': getattr(msg, 'content', ''),
                'sender': getattr(msg, 'sender', ''),
                'id': getattr(msg, 'id', ''),
                'mtype': getattr(msg, 'mtype', None),
                'sender_remark': getattr(msg, 'sender_remark', None),
                'file_path': getattr(msg, 'file_path', None)
            }
            formatted_messages.append(formatted_msg)

        return jsonify({
            'code': 0,
            'message': '获取消息成功',
            'data': {
                'who': who,
                'messages': formatted_messages
            }
        })
    except Exception as e:
        logger.error(f"获取所有消息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取消息失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/close', methods=['POST'])
@require_api_key
def close_chat_window():
    """关闭聊天窗口"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')

    if not who:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 获取聊天窗口
        listen = wx_instance.listen
        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 关闭窗口
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name == 'wxautox':
            chat_wnd.Close()
        else:
            # wxauto库的处理方式
            if hasattr(wx_instance, '_handle_chat_window_method'):
                wx_instance._handle_chat_window_method(chat_wnd, 'Close')
            else:
                chat_wnd.Close()

        return jsonify({
            'code': 0,
            'message': '关闭窗口成功',
            'data': {'who': who}
        })
    except Exception as e:
        logger.error(f"关闭聊天窗口失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'关闭窗口失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/send-emotion', methods=['POST'])
@require_api_key
def send_emotion():
    """发送自定义表情 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    emotion_index = data.get('emotion_index')

    if not who or emotion_index is None:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 获取聊天窗口
        listen = wx_instance.listen
        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 发送表情
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name == 'wxautox':
            chat_wnd.SendEmotion(emotion_index)
        else:
            # wxauto库可能不支持此功能
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持发送自定义表情功能',
                'data': None
            }), 400

        return jsonify({
            'code': 0,
            'message': '发送表情成功',
            'data': {'who': who, 'emotion_index': emotion_index}
        })
    except Exception as e:
        logger.error(f"发送表情失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'发送表情失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/merge-forward', methods=['POST'])
@require_api_key
def merge_forward():
    """合并转发消息 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message_ids = data.get('message_ids', [])
    to_friends = data.get('to_friends', [])

    if not who or not message_ids or not to_friends:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name != 'wxautox':
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持合并转发功能',
                'data': None
            }), 400

        # 获取聊天窗口
        listen = wx_instance.listen
        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 合并转发消息
        result = chat_wnd.MergeForward(message_ids, to_friends)

        return jsonify({
            'code': 0,
            'message': '合并转发成功',
            'data': {
                'who': who,
                'message_ids': message_ids,
                'to_friends': to_friends,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"合并转发失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'合并转发失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/get-dialog', methods=['GET'])
@require_api_key
def get_dialog():
    """获取对话框 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    who = request.args.get('who')

    if not who:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name != 'wxautox':
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持获取对话框功能',
                'data': None
            }), 400

        # 获取聊天窗口
        listen = wx_instance.listen
        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 获取对话框
        dialog = chat_wnd.GetDialog()

        return jsonify({
            'code': 0,
            'message': '获取对话框成功',
            'data': {
                'who': who,
                'dialog': str(dialog) if dialog else None
            }
        })
    except Exception as e:
        logger.error(f"获取对话框失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取对话框失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/get-top-message', methods=['GET'])
@require_api_key
def get_top_message():
    """获取置顶消息 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    who = request.args.get('who')

    if not who:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name != 'wxautox':
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持获取置顶消息功能',
                'data': None
            }), 400

        # 获取聊天窗口
        listen = wx_instance.listen
        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 获取置顶消息
        top_message = chat_wnd.GetTopMessage()

        # 格式化置顶消息
        formatted_message = None
        if top_message:
            formatted_message = {
                'type': getattr(top_message, 'type', 'unknown'),
                'content': getattr(top_message, 'content', ''),
                'sender': getattr(top_message, 'sender', ''),
                'id': getattr(top_message, 'id', ''),
                'mtype': getattr(top_message, 'mtype', None),
                'sender_remark': getattr(top_message, 'sender_remark', None),
                'file_path': getattr(top_message, 'file_path', None)
            }

        return jsonify({
            'code': 0,
            'message': '获取置顶消息成功',
            'data': {
                'who': who,
                'top_message': formatted_message
            }
        })
    except Exception as e:
        logger.error(f"获取置顶消息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取置顶消息失败: {str(e)}',
            'data': None
        }), 500