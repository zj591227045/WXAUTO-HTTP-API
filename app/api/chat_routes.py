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
        # 直接使用ChatWith方法打开聊天窗口（不依赖监听列表）
        wx_instance.ChatWith(who)
        time.sleep(0.5)  # 等待窗口加载

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
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'
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

@chat_bp.route('/send-message', methods=['POST'])
@require_api_key
def send_message():
    """发送消息"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        data = request.get_json()
        who = data.get('who')
        message = data.get('message')
        at_list = data.get('at_list', [])
        clear = data.get('clear', True)

        if not who or not message:
            return jsonify({
                'code': 4001,
                'message': '缺少必要参数: who, message',
                'data': None
            }), 400

        # 显示聊天窗口
        wx_instance.ChatWith(who)
        time.sleep(0.5)  # 等待窗口加载

        # 发送消息
        if at_list:
            wx_instance.SendMsg(message, clear=clear, at=at_list)
        else:
            wx_instance.SendMsg(message, clear=clear)

        return jsonify({
            'code': 0,
            'message': '发送成功',
            'data': {
                'who': who,
                'message': message,
                'at_list': at_list
            }
        })

    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'发送消息失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/send-file', methods=['POST'])
@require_api_key
def send_file():
    """发送文件"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        data = request.get_json()
        who = data.get('who')
        file_paths = data.get('file_paths', [])

        if not who or not file_paths:
            return jsonify({
                'code': 4001,
                'message': '缺少必要参数: who, file_paths',
                'data': None
            }), 400

        # 显示聊天窗口
        wx_instance.ChatWith(who)
        time.sleep(0.5)  # 等待窗口加载

        # 发送文件
        success_count = 0
        failed_files = []

        for file_path in file_paths:
            try:
                import os
                if not os.path.exists(file_path):
                    failed_files.append({
                        'path': file_path,
                        'reason': '文件不存在'
                    })
                    continue

                wx_instance.SendFiles(file_path)
                success_count += 1
            except Exception as e:
                failed_files.append({
                    'path': file_path,
                    'reason': str(e)
                })

        return jsonify({
            'code': 0,
            'message': f'发送完成，成功: {success_count}，失败: {len(failed_files)}',
            'data': {
                'who': who,
                'success_count': success_count,
                'failed_files': failed_files
            }
        })

    except Exception as e:
        logger.error(f"发送文件失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'发送文件失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/get-next-new', methods=['GET'])
@require_api_key
def get_next_new():
    """获取下一条新消息"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 使用与成功API完全相同的实现方式
        # 获取参数（使用默认值）
        savepic = False
        savevideo = False
        savefile = False
        savevoice = False
        parseurl = False

        # 获取当前使用的库
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'

        # 根据不同的库构建不同的参数
        if lib_name == 'wxautox':
            # wxautox支持所有参数
            params = {
                'savepic': savepic,
                'savevideo': savevideo,
                'savefile': savefile,
                'savevoice': savevoice,
                'parseurl': parseurl
            }
        else:
            # wxauto不支持savevideo和parseurl参数
            params = {
                'savepic': savepic,
                'savefile': savefile,
                'savevoice': savevoice
            }

        # 调用GetNextNewMessage方法
        try:
            messages = wx_instance.GetNextNewMessage(**params)
        except Exception as e:
            logger.error(f"获取新消息失败: {str(e)}")
            # 如果出现异常，返回空字典表示没有新消息
            messages = {}

        # 处理返回的消息（与成功API完全相同的处理方式）
        if not messages:
            return jsonify({
                'code': 0,
                'message': '没有新消息',
                'data': {'messages': {}}
            })

        # 辅助函数：清理群名中的人数信息
        def clean_group_name(name):
            # 匹配群名后面的 (数字) 模式
            import re
            return re.sub(r'\s*\(\d+\)$', '', name)

        # 格式化消息 - 处理不同库的返回格式
        formatted_messages = {}

        if lib_name == "wxautox":
            # wxautox返回格式: {'chat_name': 'name', 'chat_type': 'type', 'msg': [messages]}
            if isinstance(messages, dict) and 'chat_name' in messages and 'msg' in messages:
                chat_name = messages.get('chat_name', 'Unknown')
                msg_list = messages.get('msg', [])

                # 清理群名中的人数信息
                clean_name = clean_group_name(chat_name)
                formatted_messages[clean_name] = []

                for msg in msg_list:
                    try:
                        # 检查msg是否是对象
                        if hasattr(msg, 'type'):
                            # 检查消息类型
                            if hasattr(msg, 'type') and getattr(msg, 'type', '') in ['image', 'file', 'video', 'voice']:
                                # 检查文件是否存在且大小大于0
                                if hasattr(msg, 'file_path') and getattr(msg, 'file_path', ''):
                                    try:
                                        import os
                                        file_path = getattr(msg, 'file_path', '')
                                        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                                            logger.warning(f"文件不存在或大小为0: {file_path}")
                                    except Exception as e:
                                        logger.error(f"检查文件失败: {str(e)}")

                            formatted_messages[clean_name].append({
                                'type': getattr(msg, 'type', 'unknown'),
                                'content': getattr(msg, 'content', str(msg)),
                                'sender': getattr(msg, 'sender', ''),
                                'id': getattr(msg, 'id', ''),
                                'mtype': getattr(msg, 'mtype', None),
                                'sender_remark': getattr(msg, 'sender_remark', None),
                                'file_path': getattr(msg, 'file_path', None)
                            })
                        else:
                            # 如果msg是字符串或其他类型，转换为文本消息
                            formatted_messages[clean_name].append({
                                'type': 'text',
                                'content': str(msg),
                                'sender': '',
                                'id': '',
                                'mtype': None,
                                'sender_remark': None,
                                'file_path': None
                            })
                    except Exception as e:
                        logger.error(f"处理消息时出错: {str(e)}")
                        # 添加错误消息
                        formatted_messages[clean_name].append({
                            'type': 'error',
                            'content': f'消息处理错误: {str(e)}',
                            'sender': '',
                            'id': '',
                            'mtype': None,
                            'sender_remark': None,
                            'file_path': None
                        })
        else:
            # wxauto库的处理方式（如果有的话）
            if isinstance(messages, dict):
                formatted_messages = messages

        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'messages': formatted_messages
            }
        })

    except Exception as e:
        logger.error(f"获取新消息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取新消息失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/listen/add', methods=['POST'])
@require_api_key
def listen_add():
    """添加消息监听"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        data = request.get_json()
        who = data.get('who')

        if not who:
            return jsonify({
                'code': 4001,
                'message': '缺少必要参数: who',
                'data': None
            }), 400

        # 使用与成功API相同的实现方式
        try:
            # 获取当前使用的库
            lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
            logger.debug(f"当前使用的库: {lib_name}")

            # 根据不同的库构建不同的参数
            if lib_name == 'wxautox':
                # wxautox支持所有参数
                params = {
                    'who': who,
                    'savepic': False,
                    'savevideo': False,
                    'savefile': False,
                    'savevoice': False,
                    'parseurl': False
                }
            else:
                # wxauto不支持savevideo和parseurl参数
                params = {
                    'who': who,
                    'savepic': False,
                    'savefile': False,
                    'savevoice': False
                }

            # 调用AddListenChat方法（与成功的API相同）
            wx_instance.AddListenChat(**params)

            return jsonify({
                'code': 0,
                'message': '添加监听成功',
                'data': {
                    'who': who,
                    'status': 'listening'
                }
            })

        except Exception as method_error:
            logger.error(f"添加监听失败: {str(method_error)}")
            return jsonify({
                'code': 3001,
                'message': f'添加监听失败: {str(method_error)}',
                'data': None
            }), 500

    except Exception as e:
        logger.error(f"添加监听失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'添加监听失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/listen/get', methods=['GET'])
@require_api_key
def listen_get():
    """获取监听消息 - 使用GetNextNewMessage方法 - 已更新版本"""
    # 添加调试日志来确认这个函数被调用了
    logger.info("=== 调用了更新后的 listen_get 函数 ===")

    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        who = request.args.get('who')  # 可选参数
        limit = int(request.args.get('limit', 10))

        # 获取参数
        savepic = request.args.get('savepic', 'false').lower() == 'true'
        savevideo = request.args.get('savevideo', 'false').lower() == 'true'
        savefile = request.args.get('savefile', 'false').lower() == 'true'
        savevoice = request.args.get('savevoice', 'false').lower() == 'true'
        parseurl = request.args.get('parseurl', 'false').lower() == 'true'
        filter_mute = request.args.get('filter_mute', 'false').lower() == 'true'

        # 获取当前使用的库
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'
        logger.debug(f"获取监听消息，当前使用的库: {lib_name}")

        # 根据不同的库构建不同的参数
        if lib_name == 'wxautox':
            # wxautox支持所有参数，包括filter_mute
            params = {
                'savepic': savepic,
                'savevideo': savevideo,
                'savefile': savefile,
                'savevoice': savevoice,
                'parseurl': parseurl,
                'filter_mute': filter_mute
            }
        else:
            # wxauto不支持savevideo、parseurl和filter_mute参数
            params = {
                'savepic': savepic,
                'savefile': savefile,
                'savevoice': savevoice
            }

        # 调用GetNextNewMessage方法
        try:
            messages = wx_instance.GetNextNewMessage(**params)
        except Exception as e:
            logger.error(f"获取新消息失败: {str(e)}")
            # 如果出现异常，返回空字典表示没有新消息
            messages = {}

        # 处理返回的消息
        if not messages:
            return jsonify({
                'code': 0,
                'message': '没有新消息',
                'data': {'messages': {}} if not who else {'who': who, 'messages': [], 'count': 0}
            })

        # 辅助函数：清理群名中的人数信息
        def clean_group_name(name):
            import re
            return re.sub(r'\s*\(\d+\)$', '', name)

        # 格式化消息 - 处理不同库的返回格式
        formatted_messages = {}

        if lib_name == "wxautox":
            # wxautox返回格式: {'chat_name': 'name', 'chat_type': 'type', 'msg': [messages]}
            if isinstance(messages, dict) and 'chat_name' in messages and 'msg' in messages:
                chat_name = messages.get('chat_name', 'Unknown')
                msg_list = messages.get('msg', [])

                # 清理群名中的人数信息
                clean_name = clean_group_name(chat_name)
                formatted_messages[clean_name] = []

                for msg in msg_list:
                    try:
                        # 检查msg是否是对象
                        if hasattr(msg, 'type'):
                            formatted_messages[clean_name].append({
                                'type': getattr(msg, 'type', 'unknown'),
                                'content': getattr(msg, 'content', str(msg)),
                                'sender': getattr(msg, 'sender', ''),
                                'id': getattr(msg, 'id', ''),
                                'mtype': getattr(msg, 'mtype', None),
                                'sender_remark': getattr(msg, 'sender_remark', None),
                                'file_path': getattr(msg, 'file_path', None)
                            })
                        else:
                            # 如果msg是字符串或其他类型，转换为文本消息
                            formatted_messages[clean_name].append({
                                'type': 'text',
                                'content': str(msg),
                                'sender': '',
                                'id': '',
                                'mtype': None,
                                'sender_remark': None,
                                'file_path': None
                            })
                    except Exception as e:
                        logger.error(f"处理消息时出错: {str(e)}")
                        continue
        else:
            # wxauto库的处理方式 - 返回格式: Dict[str, List[Message]]
            if isinstance(messages, dict):
                for chat_name, msg_list in messages.items():
                    try:
                        # 清理群名中的人数信息
                        clean_name = clean_group_name(chat_name)
                        formatted_messages[clean_name] = []

                        for msg in msg_list:
                            try:
                                # 检查msg是否是对象
                                if hasattr(msg, 'type'):
                                    formatted_messages[clean_name].append({
                                        'type': getattr(msg, 'type', 'unknown'),
                                        'content': getattr(msg, 'content', str(msg)),
                                        'sender': getattr(msg, 'sender', ''),
                                        'id': getattr(msg, 'id', ''),
                                        'mtype': getattr(msg, 'mtype', None),
                                        'sender_remark': getattr(msg, 'sender_remark', None),
                                        'file_path': getattr(msg, 'file_path', None)
                                    })
                                else:
                                    # 如果msg是字符串或其他类型，转换为文本消息
                                    formatted_messages[clean_name].append({
                                        'type': 'text',
                                        'content': str(msg),
                                        'sender': '',
                                        'id': '',
                                        'mtype': None,
                                        'sender_remark': None,
                                        'file_path': None
                                    })
                            except Exception as e:
                                logger.error(f"处理消息时出错: {str(e)}")
                                continue
                    except Exception as e:
                        logger.error(f"处理聊天窗口消息失败: {str(e)}")
                        continue

        # 如果指定了who参数，只返回该聊天对象的消息
        if who:
            # 查找匹配的聊天对象（支持模糊匹配）
            target_messages = []
            clean_who = clean_group_name(who)

            for chat_name, msg_list in formatted_messages.items():
                if clean_who == chat_name or who == chat_name:
                    target_messages = msg_list
                    break

            # 限制消息数量
            if limit > 0 and len(target_messages) > limit:
                target_messages = target_messages[-limit:]

            return jsonify({
                'code': 0,
                'message': '获取监听消息成功',
                'data': {
                    'who': who,
                    'messages': target_messages,
                    'count': len(target_messages)
                }
            })
        else:
            # 返回所有消息
            return jsonify({
                'code': 0,
                'message': '获取监听消息成功',
                'data': {
                    'messages': formatted_messages
                }
            })

    except Exception as e:
        logger.error(f"获取监听消息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取监听消息失败: {str(e)}',
            'data': None
        }), 500

@chat_bp.route('/test-updated', methods=['GET'])
@require_api_key
def test_updated():
    """测试更新后的代码是否生效"""
    return jsonify({
        'code': 0,
        'message': '更新后的代码已生效',
        'data': {'version': 'updated'}
    })

@chat_bp.route('/listen/remove', methods=['POST'])
@require_api_key
def listen_remove():
    """移除消息监听"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        data = request.get_json()
        who = data.get('who')

        if not who:
            return jsonify({
                'code': 4001,
                'message': '缺少必要参数: who',
                'data': None
            }), 400

        # 使用与成功API完全相同的实现方式
        try:
            # 检查当前使用的库
            lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'
            logger.debug(f"移除监听，当前使用的库: {lib_name}")

            # 调用RemoveListenChat方法（与成功API相同）
            result = wx_instance.RemoveListenChat(who)

            # 检查结果
            if result is False:  # 明确返回False表示失败
                logger.warning(f"移除监听失败: {who}")
                return jsonify({
                    'code': 3001,
                    'message': f'移除监听失败: 未找到监听对象 {who}',
                    'data': None
                }), 404

            # 成功移除
            return jsonify({
                'code': 0,
                'message': '移除监听成功',
                'data': {'who': who}
            })

        except Exception as remove_error:
            logger.error(f"移除监听失败: {str(remove_error)}", exc_info=True)
            return jsonify({
                'code': 3001,
                'message': f'移除失败: {str(remove_error)}',
                'data': None
            }), 500

    except Exception as e:
        logger.error(f"移除监听失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'移除监听失败: {str(e)}',
            'data': None
        }), 500

