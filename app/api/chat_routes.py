"""
Chat类相关API路由
实现Chat类的所有方法
"""

from flask import Blueprint, jsonify, request
from app.auth import require_api_key
from app.unified_logger import logger
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

        # 调试信息：检查chat_wnd的类型
        logger.debug(f"LoadMoreMessage - chat_wnd类型: {type(chat_wnd)}, 值: {chat_wnd}")

        # 检查chat_wnd是否是tuple，如果是则尝试获取正确的对象
        if isinstance(chat_wnd, tuple):
            logger.error(f"LoadMoreMessage - 检测到chat_wnd是tuple类型: {chat_wnd}")
            if len(chat_wnd) > 0:
                chat_wnd = chat_wnd[0]
                logger.info(f"LoadMoreMessage - 使用tuple的第一个元素: {type(chat_wnd)}")
            else:
                return jsonify({
                    'code': 3001,
                    'message': f'聊天窗口对象类型错误: {type(listen[who])}',
                    'data': None
                }), 500

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
            # wxautox的GetNextNewMessage只支持filter_mute参数
            params = {
                'filter_mute': False  # 默认不过滤免打扰消息
            }
        else:
            # wxauto的GetNextNewMessage可能不支持任何参数，使用空参数
            params = {}

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
            # wxauto库的处理方式 - 根据日志分析，wxauto实际返回字典格式，不是列表格式
            if isinstance(messages, dict):
                # wxauto返回字典格式: {'chat_name': '消息测试', 'chat_type': 'group', 'msg': [...]}
                if 'msg' in messages and isinstance(messages['msg'], list):
                    # 使用正确的chat_name，而不是硬编码的"新消息"
                    chat_name = messages.get('chat_name', '未知聊天')
                    clean_name = clean_group_name(chat_name)
                    formatted_messages = {clean_name: []}

                    for msg in messages['msg']:
                        try:
                            # 检查msg是否已经是字典格式（适配器已转换）
                            if isinstance(msg, dict):
                                # 已经是字典格式，直接使用
                                msg_data = msg
                            elif hasattr(msg, 'type'):
                                # 原始消息对象，需要转换
                                msg_data = {
                                    'type': getattr(msg, 'type', 'unknown'),
                                    'content': getattr(msg, 'content', str(msg)),
                                    'sender': getattr(msg, 'sender', ''),
                                    'time': getattr(msg, 'time', ''),
                                    'id': getattr(msg, 'id', ''),
                                    'mtype': getattr(msg, 'mtype', None),
                                    'sender_remark': getattr(msg, 'sender_remark', None),
                                    'file_path': getattr(msg, 'file_path', None)
                                }
                            else:
                                # 其他类型，转换为文本消息
                                msg_data = {
                                    'type': 'text',
                                    'content': str(msg),
                                    'sender': '',
                                    'time': '',
                                    'id': '',
                                    'mtype': None,
                                    'sender_remark': None,
                                    'file_path': None
                                }

                            formatted_messages[clean_name].append(msg_data)
                        except Exception as e:
                            logger.error(f"处理wxauto消息时出错: {str(e)}")
                            # 添加错误消息
                            formatted_messages[clean_name].append({
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
                    formatted_messages = {}
                    for chat_name, msg_list in messages.items():
                        if isinstance(msg_list, list):
                            # 清理群名中的人数信息
                            clean_name = clean_group_name(chat_name)
                            formatted_messages[clean_name] = []

                            for msg in msg_list:
                                try:
                                    # 处理消息对象
                                    if hasattr(msg, 'type'):
                                        msg_data = {
                                            'type': getattr(msg, 'type', 'unknown'),
                                            'content': getattr(msg, 'content', str(msg)),
                                            'sender': getattr(msg, 'sender', ''),
                                            'time': getattr(msg, 'time', ''),
                                            'id': getattr(msg, 'id', ''),
                                            'mtype': getattr(msg, 'mtype', None),
                                            'sender_remark': getattr(msg, 'sender_remark', None),
                                            'file_path': getattr(msg, 'file_path', None)
                                        }
                                    else:
                                        msg_data = {
                                            'type': 'text',
                                            'content': str(msg),
                                            'sender': '',
                                            'time': '',
                                            'id': '',
                                            'mtype': None,
                                            'sender_remark': None,
                                            'file_path': None
                                        }
                                    formatted_messages[clean_name].append(msg_data)
                                except Exception as e:
                                    logger.error(f"处理wxauto消息时出错: {str(e)}")
                                    # 添加错误消息
                                    formatted_messages[clean_name].append({
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
                            # 如果不是列表，直接使用原值
                            formatted_messages[chat_name] = msg_list
            elif isinstance(messages, list):
                # 如果wxauto确实返回列表格式（向后兼容）
                formatted_messages = {"新消息": []}

                for msg in messages:
                    try:
                        # 检查msg是否已经是字典格式（适配器已转换）
                        if isinstance(msg, dict):
                            # 已经是字典格式，直接使用
                            msg_data = msg
                        elif hasattr(msg, 'type'):
                            # 原始消息对象，需要转换
                            msg_data = {
                                'type': getattr(msg, 'type', 'unknown'),
                                'content': getattr(msg, 'content', str(msg)),
                                'sender': getattr(msg, 'sender', ''),
                                'time': getattr(msg, 'time', ''),
                                'id': getattr(msg, 'id', ''),
                                'mtype': getattr(msg, 'mtype', None),
                                'sender_remark': getattr(msg, 'sender_remark', None),
                                'file_path': getattr(msg, 'file_path', None)
                            }
                        else:
                            # 其他类型，转换为文本消息
                            msg_data = {
                                'type': 'text',
                                'content': str(msg),
                                'sender': '',
                                'time': '',
                                'id': '',
                                'mtype': None,
                                'sender_remark': None,
                                'file_path': None
                            }

                        formatted_messages["新消息"].append(msg_data)
                    except Exception as e:
                        logger.error(f"处理wxauto消息时出错: {str(e)}")
                        # 添加错误消息
                        formatted_messages["新消息"].append({
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
                # 其他情况，转换为字符串
                formatted_messages = {"消息": [{"type": "text", "content": str(messages)}]}

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

# 删除重复的监听路由 - 统一使用 /api/message/listen/* 路径

# 删除重复的监听获取路由 - 统一使用 /api/message/listen/get 路径

@chat_bp.route('/test-updated', methods=['GET'])
@require_api_key
def test_updated():
    """测试更新后的代码是否生效"""
    return jsonify({
        'code': 0,
        'message': '更新后的代码已生效',
        'data': {'version': 'updated'}
    })

# 删除重复的监听移除路由 - 统一使用 /api/message/listen/remove 路径

