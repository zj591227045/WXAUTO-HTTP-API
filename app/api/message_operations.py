"""
消息操作相关API路由
实现Message类的所有交互方法
"""

from flask import Blueprint, jsonify, request
from app.auth import require_api_key
from app.unified_logger import logger
from app.wechat import wechat_manager

message_ops_bp = Blueprint('message_ops', __name__)

@message_ops_bp.route('/click', methods=['POST'])
@require_api_key
def click_message():
    """点击消息"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message_id = data.get('message_id')

    if not who or not message_id:
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

        # 获取消息
        messages = chat_wnd.GetAllMessage()
        target_message = None
        for msg in messages:
            if getattr(msg, 'id', '') == message_id:
                target_message = msg
                break

        if not target_message:
            return jsonify({
                'code': 3001,
                'message': f'未找到消息ID: {message_id}',
                'data': None
            }), 404

        # 点击消息
        target_message.click()

        return jsonify({
            'code': 0,
            'message': '点击消息成功',
            'data': {
                'who': who,
                'message_id': message_id
            }
        })
    except Exception as e:
        logger.error(f"点击消息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'点击消息失败: {str(e)}',
            'data': None
        }), 500

@message_ops_bp.route('/quote', methods=['POST'])
@require_api_key
def quote_message():
    """引用回复消息"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message_id = data.get('message_id')
    reply_text = data.get('reply_text', '')

    if not who or not message_id:
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

        # 获取消息
        messages = chat_wnd.GetAllMessage()
        target_message = None
        for msg in messages:
            if getattr(msg, 'id', '') == message_id:
                target_message = msg
                break

        if not target_message:
            return jsonify({
                'code': 3001,
                'message': f'未找到消息ID: {message_id}',
                'data': None
            }), 404

        # 引用回复
        target_message.quote(reply_text)

        return jsonify({
            'code': 0,
            'message': '引用回复成功',
            'data': {
                'who': who,
                'message_id': message_id,
                'reply_text': reply_text
            }
        })
    except Exception as e:
        logger.error(f"引用回复失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'引用回复失败: {str(e)}',
            'data': None
        }), 500

@message_ops_bp.route('/forward', methods=['POST'])
@require_api_key
def forward_message():
    """转发消息"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message_id = data.get('message_id')
    to_friends = data.get('to_friends', [])

    if not who or not message_id or not to_friends:
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

        # 获取消息
        messages = chat_wnd.GetAllMessage()
        target_message = None
        for msg in messages:
            if getattr(msg, 'id', '') == message_id:
                target_message = msg
                break

        if not target_message:
            return jsonify({
                'code': 3001,
                'message': f'未找到消息ID: {message_id}',
                'data': None
            }), 404

        # 转发消息
        target_message.forward(to_friends)

        return jsonify({
            'code': 0,
            'message': '转发消息成功',
            'data': {
                'who': who,
                'message_id': message_id,
                'to_friends': to_friends
            }
        })
    except Exception as e:
        logger.error(f"转发消息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'转发消息失败: {str(e)}',
            'data': None
        }), 500

@message_ops_bp.route('/tickle', methods=['POST'])
@require_api_key
def tickle_message():
    """拍一拍 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message_id = data.get('message_id')

    if not who or not message_id:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'
        if lib_name != 'wxautox':
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持拍一拍功能',
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

        # 获取消息
        messages = chat_wnd.GetAllMessage()
        target_message = None
        for msg in messages:
            if getattr(msg, 'id', '') == message_id:
                target_message = msg
                break

        if not target_message:
            return jsonify({
                'code': 3001,
                'message': f'未找到消息ID: {message_id}',
                'data': None
            }), 404

        # 拍一拍
        target_message.tickle()

        return jsonify({
            'code': 0,
            'message': '拍一拍成功',
            'data': {
                'who': who,
                'message_id': message_id
            }
        })
    except Exception as e:
        logger.error(f"拍一拍失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'拍一拍失败: {str(e)}',
            'data': None
        }), 500

@message_ops_bp.route('/delete', methods=['POST'])
@require_api_key
def delete_message():
    """删除消息 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message_id = data.get('message_id')

    if not who or not message_id:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'
        if lib_name != 'wxautox':
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持删除消息功能',
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

        # 获取消息
        messages = chat_wnd.GetAllMessage()
        target_message = None
        for msg in messages:
            if getattr(msg, 'id', '') == message_id:
                target_message = msg
                break

        if not target_message:
            return jsonify({
                'code': 3001,
                'message': f'未找到消息ID: {message_id}',
                'data': None
            }), 404

        # 删除消息
        target_message.delete()

        return jsonify({
            'code': 0,
            'message': '删除消息成功',
            'data': {
                'who': who,
                'message_id': message_id
            }
        })
    except Exception as e:
        logger.error(f"删除消息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'删除消息失败: {str(e)}',
            'data': None
        }), 500

@message_ops_bp.route('/download', methods=['POST'])
@require_api_key
def download_message():
    """下载图片/文件"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message_id = data.get('message_id')
    save_path = data.get('save_path')

    if not who or not message_id:
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

        # 获取消息
        messages = chat_wnd.GetAllMessage()
        target_message = None
        for msg in messages:
            if getattr(msg, 'id', '') == message_id:
                target_message = msg
                break

        if not target_message:
            return jsonify({
                'code': 3001,
                'message': f'未找到消息ID: {message_id}',
                'data': None
            }), 404

        # 下载文件
        if save_path:
            result = target_message.download(save_path)
        else:
            result = target_message.download()

        return jsonify({
            'code': 0,
            'message': '下载成功',
            'data': {
                'who': who,
                'message_id': message_id,
                'save_path': save_path,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"下载失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'下载失败: {str(e)}',
            'data': None
        }), 500

@message_ops_bp.route('/to-text', methods=['POST'])
@require_api_key
def voice_to_text():
    """语音转文字"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message_id = data.get('message_id')

    if not who or not message_id:
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

        # 获取消息
        messages = chat_wnd.GetAllMessage()
        target_message = None
        for msg in messages:
            if getattr(msg, 'id', '') == message_id:
                target_message = msg
                break

        if not target_message:
            return jsonify({
                'code': 3001,
                'message': f'未找到消息ID: {message_id}',
                'data': None
            }), 404

        # 检查消息类型
        msg_type = getattr(target_message, 'type', '')
        if msg_type != 'voice':
            return jsonify({
                'code': 3001,
                'message': '该消息不是语音消息',
                'data': None
            }), 400

        # 语音转文字
        text_result = target_message.to_text()

        return jsonify({
            'code': 0,
            'message': '语音转文字成功',
            'data': {
                'who': who,
                'message_id': message_id,
                'text': text_result
            }
        })
    except Exception as e:
        logger.error(f"语音转文字失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'语音转文字失败: {str(e)}',
            'data': None
        }), 500

@message_ops_bp.route('/select-option', methods=['POST'])
@require_api_key
def select_message_option():
    """右键菜单操作"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message_id = data.get('message_id')
    option = data.get('option')

    if not who or not message_id or not option:
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

        # 获取消息
        messages = chat_wnd.GetAllMessage()
        target_message = None
        for msg in messages:
            if getattr(msg, 'id', '') == message_id:
                target_message = msg
                break

        if not target_message:
            return jsonify({
                'code': 3001,
                'message': f'未找到消息ID: {message_id}',
                'data': None
            }), 404

        # 执行右键菜单操作
        result = target_message.select_option(option)

        return jsonify({
            'code': 0,
            'message': '右键菜单操作成功',
            'data': {
                'who': who,
                'message_id': message_id,
                'option': option,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"右键菜单操作失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'右键菜单操作失败: {str(e)}',
            'data': None
        }), 500