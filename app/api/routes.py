from flask import Blueprint, jsonify, request, g, Response, send_file
from app.auth import require_api_key
from app.unified_logger import logger
from app.wechat import wechat_manager
from app.system_monitor import get_system_resources
from app.api_queue import queue_task, get_queue_stats
from app.config import Config
import os
import time
from typing import Optional, List
from urllib.parse import quote
import functools

api_bp = Blueprint('api', __name__)

# 全局消息缓存 - 用于存储回调函数接收到的消息
_message_cache = {}

# 记录程序启动时间
start_time = time.time()

# 移除旧的日志处理器刷新函数，统一日志管理器会自动处理

@api_bp.before_request
def before_request():
    g.start_time = time.time()
    # 记录请求信息，但不记录详细的请求头和请求体
    logger.info(f"收到请求: {request.method} {request.path}")
    # 移除旧的日志处理器刷新代码，统一日志管理器会自动处理

    # 只在开发环境下记录请求体，且不记录请求头
    if Config.DEBUG and request.method in ['POST', 'PUT', 'PATCH']:
        try:
            if request.is_json:
                json_data = request.get_json(silent=True)
                if json_data is not None:
                    logger.debug(f"请求体: {json_data}")
        except Exception as e:
            logger.debug(f"无法解析请求体: {str(e)}")
        # 统一日志管理器会自动处理日志刷新

@api_bp.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        # 修改日志格式，确保API计数器能够正确识别 - 确保状态码周围有空格
        logger.info(f"请求处理完成: {request.method} {request.path} - 状态码: {response.status_code} - 耗时: {duration:.2f}秒")
        # 统一日志管理器会自动处理日志刷新
    return response

@api_bp.errorhandler(Exception)
def handle_error(error):
    # 记录未捕获的异常
    logger.error(f"未捕获的异常: {str(error)}", exc_info=True)
    return jsonify({
        'code': 5000,
        'message': '服务器内部错误',
        'data': None
    }), 500

# 初始化和验证相关接口
@api_bp.route('/auth/verify', methods=['POST'])
@require_api_key
def verify_api_key():
    return jsonify({
        'code': 0,
        'message': '验证成功',
        'data': {'valid': True}
    })

@api_bp.route('/wechat/initialize', methods=['POST'])
@require_api_key
def initialize_wechat():
    try:
        success = wechat_manager.initialize()
        if success:
            # 获取微信窗口名称
            wx_instance = wechat_manager.get_instance()
            window_name = ""
            try:
                # 使用适配器的get_window_name方法获取窗口名称（优先使用缓存）
                window_name = wx_instance.get_window_name()
                if window_name:
                    logger.info(f"初始化成功，获取到已登录窗口：{window_name}")

                # 注意：在wechat_adapter.py的initialize方法中已经添加了打开文件传输助手的逻辑
                # 这里不需要重复检查和打开，避免重复操作
                logger.debug("微信初始化完成，文件传输助手窗口已在适配器中处理")
            except Exception as e:
                logger.warning(f"获取窗口名称失败: {str(e)}")

            return jsonify({
                'code': 0,
                'message': '初始化成功',
                'data': {
                    'status': 'connected',
                    'window_name': window_name
                }
            })
        else:
            return jsonify({
                'code': 2001,
                'message': '初始化失败',
                'data': None
            }), 500
    except Exception as e:
        logger.error(f"初始化异常: {str(e)}")
        return jsonify({
            'code': 2001,
            'message': f'初始化失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/wechat/status', methods=['GET'])
@require_api_key
def get_wechat_status():
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    is_connected = wechat_manager.check_connection()

    # 获取微信窗口名称
    window_name = ""
    if is_connected:
        try:
            # 使用适配器的get_window_name方法获取窗口名称（优先使用缓存）
            window_name = wx_instance.get_window_name()
            if window_name:
                logger.debug(f"状态检查：获取到已登录窗口：{window_name}")
        except Exception as e:
            logger.warning(f"获取窗口名称失败: {str(e)}")

    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': {
            'status': 'online' if is_connected else 'offline',
            'window_name': window_name
        }
    })

def format_at_message(message: str, at_list: Optional[List[str]] = None) -> str:
    if not at_list:
        return message

    result = message
    if result and not result.endswith('\n'):
        result += '\n'

    for user in at_list:
        result += f"{{@{user}}}"
        if user != at_list[-1]:
            result += '\n'
    return result

# 消息相关接口
@api_bp.route('/message/send', methods=['POST'])
@require_api_key
def send_message():
    # 在队列处理前获取所有请求数据
    try:
        data = request.get_json()
        receiver = data.get('receiver')
        message = data.get('message')
        at_list = data.get('at_list', [])
        clear = "1" if data.get('clear', True) else "0"

        if not receiver or not message:
            return jsonify({
                'code': 1002,
                'message': '缺少必要参数',
                'data': None
            }), 400

        # 将任务加入队列处理
        result = _send_message_task(receiver, message, at_list, clear)

        # 处理队列任务返回的结果
        if isinstance(result, dict) and 'response' in result and 'status_code' in result:
            return jsonify(result['response']), result['status_code']

        # 如果返回的不是预期格式，返回错误
        logger.error(f"队列任务返回了意外的结果格式: {result}")
        return jsonify({
            'code': 3001,
            'message': '服务器内部错误',
            'data': None
        }), 500
    except Exception as e:
        logger.error(f"处理发送消息请求失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'处理请求失败: {str(e)}',
            'data': None
        }), 500

@queue_task(timeout=30)  # 使用队列处理请求，超时30秒
def _send_message_task(receiver, message, at_list, clear):
    """实际执行发送消息的队列任务"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return {
            'response': {
                'code': 2001,
                'message': '微信未初始化',
                'data': None
            },
            'status_code': 400
        }

    try:
        formatted_message = format_at_message(message, at_list)

        # 查找联系人
        chat_name = wx_instance.ChatWith(receiver)
        if not chat_name:
            return {
                'response': {
                    'code': 3001,
                    'message': f'找不到联系人: {receiver}',
                    'data': None
                },
                'status_code': 404
            }

        # 确认切换到了正确的聊天窗口
        if chat_name != receiver:
            return {
                'response': {
                    'code': 3001,
                    'message': f'联系人匹配错误，期望: {receiver}, 实际: {chat_name}',
                    'data': None
                },
                'status_code': 400
            }

        if at_list:
            wx_instance.SendMsg(formatted_message, clear=clear, at=at_list)
            wx_instance.SendMsg(message, clear=clear, at=at_list)
        else:
            wx_instance.SendMsg(message, clear=clear)

        return {
            'response': {
                'code': 0,
                'message': '发送成功',
                'data': {'message_id': 'success'}
            },
            'status_code': 200
        }
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        return {
            'response': {
                'code': 3001,
                'message': f'发送失败: {str(e)}',
                'data': None
            },
            'status_code': 500
        }

@api_bp.route('/message/send-typing', methods=['POST'])
@require_api_key
def send_typing_message():
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    receiver = data.get('receiver')
    message = data.get('message')
    at_list = data.get('at_list', [])
    clear = data.get('clear', True)

    if not receiver or not message:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        logger.debug(f"发送打字消息，当前使用的库: {lib_name}")

        # 查找联系人
        chat_name = wx_instance.ChatWith(receiver)
        if not chat_name:
            return jsonify({
                'code': 3001,
                'message': f'找不到联系人: {receiver}',
                'data': None
            }), 404

        # 确认切换到了正确的聊天窗口
        if chat_name != receiver:
            return jsonify({
                'code': 3001,
                'message': f'联系人匹配错误，期望: {receiver}, 实际: {chat_name}',
                'data': None
            }), 400

        # 处理@列表
        if at_list:
            if message and not message.endswith('\n'):
                message += '\n'
            for user in at_list:
                message += f"{{@{user}}}"
                if user != at_list[-1]:
                    message += '\n'

        # 根据不同的库使用不同的处理方法
        if lib_name == 'wxautox':
            # 对于wxautox库，使用SendTypingText方法
            wx_instance.SendTypingText(message, clear=clear)
        else:
            # 对于wxauto库，使用SendMsg方法代替SendTypingText方法
            if at_list:
                wx_instance.SendMsg(message, at=at_list)
            else:
                wx_instance.SendMsg(message)

        return jsonify({
            'code': 0,
            'message': '发送成功',
            'data': {'message_id': 'success'}
        })
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'发送失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/message/send-file', methods=['POST'])
@require_api_key
def send_file():
    # 在队列处理前获取所有请求数据
    try:
        data = request.get_json()
        receiver = data.get('receiver')
        file_paths = data.get('file_paths', [])

        if not receiver or not file_paths:
            return jsonify({
                'code': 1002,
                'message': '缺少必要参数',
                'data': None
            }), 400

        # 将任务加入队列处理
        result = _send_file_task(receiver, file_paths)

        # 处理队列任务返回的结果
        if isinstance(result, dict) and 'response' in result and 'status_code' in result:
            return jsonify(result['response']), result['status_code']

        # 如果返回的不是预期格式，返回错误
        logger.error(f"队列任务返回了意外的结果格式: {result}")
        return jsonify({
            'code': 3001,
            'message': '服务器内部错误',
            'data': None
        }), 500
    except Exception as e:
        logger.error(f"处理发送文件请求失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'处理请求失败: {str(e)}',
            'data': None
        }), 500

@queue_task(timeout=60)  # 使用队列处理请求，文件发送可能需要更长时间，设置60秒超时
def _send_file_task(receiver, file_paths):
    """实际执行发送文件的队列任务"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return {
            'response': {
                'code': 2001,
                'message': '微信未初始化',
                'data': None
            },
            'status_code': 400
        }

    failed_files = []
    success_count = 0

    try:
        # 查找联系人
        chat_name = wx_instance.ChatWith(receiver)
        if not chat_name:
            return {
                'response': {
                    'code': 3001,
                    'message': f'找不到联系人: {receiver}',
                    'data': None
                },
                'status_code': 404
            }

        # 确认切换到了正确的聊天窗口
        if chat_name != receiver:
            return {
                'response': {
                    'code': 3001,
                    'message': f'联系人匹配错误，期望: {receiver}, 实际: {chat_name}',
                    'data': None
                },
                'status_code': 400
            }

        for file_path in file_paths:
            if not os.path.exists(file_path):
                failed_files.append({
                    'path': file_path,
                    'reason': '文件不存在'
                })
                continue

            try:
                wx_instance.SendFiles(file_path)
                success_count += 1
            except Exception as e:
                failed_files.append({
                    'path': file_path,
                    'reason': str(e)
                })

        return {
            'response': {
                'code': 0 if not failed_files else 3001,
                'message': '发送完成' if not failed_files else '部分文件发送失败',
                'data': {
                    'success_count': success_count,
                    'failed_files': failed_files
                }
            },
            'status_code': 200
        }
    except Exception as e:
        logger.error(f"发送文件失败: {str(e)}")
        return {
            'response': {
                'code': 3001,
                'message': f'发送失败: {str(e)}',
                'data': None
            },
            'status_code': 500
        }

@api_bp.route('/message/get-next-new', methods=['GET'])
@require_api_key
def get_next_new_message():
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        logger.error("微信未初始化")
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 更灵活的布尔值处理
        def parse_bool(value):
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                value = value.lower()
                if value in ('true', '1', 'yes', 'y', 'on'):
                    return True
                if value in ('false', '0', 'no', 'n', 'off'):
                    return False
            return False

        # 获取参数并设置默认值
        savepic = parse_bool(request.args.get('savepic', 'false'))
        savevideo = parse_bool(request.args.get('savevideo', 'false'))
        savefile = parse_bool(request.args.get('savefile', 'false'))
        savevoice = parse_bool(request.args.get('savevoice', 'false'))
        parseurl = parse_bool(request.args.get('parseurl', 'false'))

        logger.debug(f"处理参数: savepic={savepic}, savevideo={savevideo}, savefile={savefile}, savevoice={savevoice}, parseurl={parseurl}")

        # 获取当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        logger.debug(f"当前使用的库: {lib_name}")

        # 根据不同的库构建不同的参数
        if lib_name == 'wxautox':
            # wxautox的GetNextNewMessage只支持filter_mute参数
            params = {
                'filter_mute': False  # 默认不过滤免打扰消息
            }
            logger.debug(f"使用wxautox参数: {params}")
        else:
            # wxauto的GetNextNewMessage可能不支持任何参数，使用空参数
            params = {}
            logger.debug(f"使用wxauto参数: {params}")

        # 不再设置wxauto保存路径，避免导入错误
        logger.debug("跳过wxauto保存路径设置，使用默认路径")

        # 调用GetNextNewMessage方法
        try:
            messages = wx_instance.GetNextNewMessage(**params)
        except Exception as e:
            logger.error(f"获取新消息失败: {str(e)}")
            # 如果出现异常，返回空字典表示没有新消息
            messages = {}

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

        # 检查当前使用的库
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'

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
                logger.warning(f"wxautox返回了意外的消息格式: {type(messages)}")
        else:
            # wxauto处理 - 根据日志分析，wxauto实际返回字典格式，不是列表格式
            if isinstance(messages, dict):
                # wxauto返回字典格式: {'chat_name': '消息测试', 'chat_type': 'group', 'msg': [...]}
                if 'msg' in messages and isinstance(messages['msg'], list):
                    # 使用正确的chat_name，而不是硬编码的"新消息"
                    chat_name = messages.get('chat_name', '未知聊天')
                    clean_name = clean_group_name(chat_name)
                    formatted_messages[clean_name] = []

                    for msg in messages['msg']:
                        try:
                            # 检查msg是否已经是字典格式（适配器已转换）
                            if isinstance(msg, dict):
                                # 已经是字典格式，直接使用
                                msg_data = {
                                    'type': msg.get('type', 'unknown'),
                                    'content': msg.get('content', str(msg)),
                                    'sender': msg.get('sender', ''),
                                    'time': msg.get('time', ''),
                                    'id': msg.get('id', ''),
                                    'mtype': msg.get('mtype', None),
                                    'sender_remark': msg.get('sender_remark', None),
                                    'file_path': msg.get('file_path', None)
                                }
                            else:
                                # 原始消息对象，需要转换
                                # 检查消息类型
                                if hasattr(msg, 'type') and getattr(msg, 'type', '') in ['image', 'file', 'video', 'voice']:
                                    # 检查文件是否存在且大小大于0
                                    if hasattr(msg, 'file_path') and getattr(msg, 'file_path', ''):
                                        try:
                                            file_path = getattr(msg, 'file_path', '')
                                            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                                                logger.warning(f"文件不存在或大小为0: {file_path}")
                                        except Exception as e:
                                            logger.error(f"检查文件失败: {str(e)}")

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
                    for chat_name, msg_list in messages.items():
                        if isinstance(msg_list, list):
                            # 清理群名中的人数信息
                            clean_name = clean_group_name(chat_name)
                            formatted_messages[clean_name] = []

                            for msg in msg_list:
                                try:
                                    # 检查消息类型
                                    if hasattr(msg, 'type') and getattr(msg, 'type', '') in ['image', 'file', 'video', 'voice']:
                                        # 检查文件是否存在且大小大于0
                                        if hasattr(msg, 'file_path') and getattr(msg, 'file_path', ''):
                                            try:
                                                file_path = getattr(msg, 'file_path', '')
                                                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                                                    logger.warning(f"文件不存在或大小为0: {file_path}")
                                            except Exception as e:
                                                logger.error(f"检查文件失败: {str(e)}")

                                    formatted_messages[clean_name].append({
                                        'type': getattr(msg, 'type', 'unknown'),
                                        'content': getattr(msg, 'content', str(msg)),
                                        'sender': getattr(msg, 'sender', ''),
                                        'time': getattr(msg, 'time', ''),
                                        'id': getattr(msg, 'id', ''),
                                        'mtype': getattr(msg, 'mtype', None),
                                        'sender_remark': getattr(msg, 'sender_remark', None),
                                        'file_path': getattr(msg, 'file_path', None)
                                    })
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
            elif isinstance(messages, list):
                # 如果wxauto确实返回列表格式（向后兼容）
                formatted_messages["新消息"] = []

                for msg in messages:
                    try:
                        # 检查msg是否已经是字典格式（适配器已转换）
                        if isinstance(msg, dict):
                            # 已经是字典格式，直接使用
                            msg_data = {
                                'type': msg.get('type', 'unknown'),
                                'content': msg.get('content', str(msg)),
                                'sender': msg.get('sender', ''),
                                'time': msg.get('time', ''),
                                'id': msg.get('id', ''),
                                'mtype': msg.get('mtype', None),
                                'sender_remark': msg.get('sender_remark', None),
                                'file_path': msg.get('file_path', None)
                            }
                        else:
                            # 原始消息对象，需要转换
                            # 检查消息类型
                            if hasattr(msg, 'type') and getattr(msg, 'type', '') in ['image', 'file', 'video', 'voice']:
                                # 检查文件是否存在且大小大于0
                                if hasattr(msg, 'file_path') and getattr(msg, 'file_path', ''):
                                    try:
                                        file_path = getattr(msg, 'file_path', '')
                                        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                                            logger.warning(f"文件不存在或大小为0: {file_path}")
                                    except Exception as e:
                                        logger.error(f"检查文件失败: {str(e)}")

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
                # 其他格式，转换为字符串
                formatted_messages = {"消息": [{"type": "text", "content": str(messages)}]}

        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'messages': formatted_messages
            }
        })
    except Exception as e:
        logger.error(f"获取新消息失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3002,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/message/listen/add', methods=['POST'])
@require_api_key
def add_listen_chat():
    """添加消息监听 - 按照官方文档实现"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    if not data:
        return jsonify({
            'code': 1002,
            'message': '请求数据不能为空',
            'data': None
        }), 400

    # 获取必要参数
    nickname = data.get('nickname')
    if not nickname:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数: nickname',
            'data': None
        }), 400

    try:
        # 获取原始微信实例（绕过WeChatAdapter的复杂处理）
        original_instance = wx_instance._instance if hasattr(wx_instance, '_instance') else wx_instance
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'

        logger.info(f"添加监听对象: {nickname}, 使用库: {lib_name}")
        logger.info(f"wx_instance类型: {type(wx_instance)}")
        logger.info(f"original_instance类型: {type(original_instance)}")
        logger.info(f"是否有_instance属性: {hasattr(wx_instance, '_instance')}")
        logger.info(f"original_instance是否等于wx_instance: {original_instance is wx_instance}")

        # 统一处理：创建消息缓存（如果不存在）
        if not hasattr(original_instance, '_api_message_cache'):
            original_instance._api_message_cache = {}

        if lib_name == 'wxautox':
            # wxautox实现
            def message_callback(msg, chat):
                """wxautox的消息回调函数，统一使用全局缓存"""
                try:
                    logger.info(f"wxautox收到消息: {msg}, 来自聊天: {chat}")

                    # 将wxautox消息对象转换为可序列化的字典格式
                    serializable_msg = {
                        'type': getattr(msg, 'type', 'unknown'),
                        'content': getattr(msg, 'content', str(msg)),
                        'sender': getattr(msg, 'sender', ''),
                        'id': getattr(msg, 'id', ''),
                        'mtype': getattr(msg, 'mtype', None),
                        'sender_remark': getattr(msg, 'sender_remark', None),
                        'file_path': getattr(msg, 'file_path', None),
                        'time': getattr(msg, 'time', None)
                    }

                    # 将消息存储到全局缓存中
                    if nickname not in _message_cache:
                        _message_cache[nickname] = []
                    _message_cache[nickname].append(serializable_msg)

                    logger.info(f"已将消息转换并存储到缓存: {serializable_msg}")
                except Exception as e:
                    logger.error(f"回调函数处理消息时出错: {str(e)}")

            # 调用AddListenChat
            result = original_instance.AddListenChat(nickname=nickname, callback=message_callback)

            # 调试信息：检查AddListenChat的返回值类型
            logger.debug(f"wxautox AddListenChat返回值类型: {type(result)}, 值: {result}")

            # 检查listen字典中的对象类型
            if hasattr(original_instance, 'listen') and nickname in original_instance.listen:
                chat_obj = original_instance.listen[nickname]
                logger.debug(f"wxautox listen[{nickname}]的类型: {type(chat_obj)}, 值: {chat_obj}")

            # 调用StartListening（按照文档要求）
            if hasattr(original_instance, 'StartListening'):
                original_instance.StartListening()
                logger.info("已调用StartListening")
        else:
            # wxauto实现 - 需要提供callback参数
            def message_callback(msg, chat):
                """wxauto的消息回调函数，接收msg和chat两个参数"""
                try:
                    logger.info(f"wxauto收到消息: {msg}, 来自聊天: {chat}")

                    # 将wxauto消息对象转换为可序列化的字典格式
                    serializable_msg = {
                        'type': getattr(msg, 'type', 'unknown'),
                        'content': getattr(msg, 'content', str(msg)),
                        'sender': getattr(msg, 'sender', ''),
                        'id': getattr(msg, 'id', ''),
                        'mtype': getattr(msg, 'mtype', None),
                        'sender_remark': getattr(msg, 'sender_remark', None),
                        'file_path': getattr(msg, 'file_path', None),
                        'time': getattr(msg, 'time', None)
                    }

                    # 将消息存储到全局缓存中
                    if nickname not in _message_cache:
                        _message_cache[nickname] = []
                    _message_cache[nickname].append(serializable_msg)

                    logger.info(f"已将消息转换并存储到缓存: {serializable_msg}")
                except Exception as e:
                    logger.error(f"wxauto回调函数处理消息时出错: {str(e)}")

            result = original_instance.AddListenChat(nickname, message_callback)

            # 调试信息：检查AddListenChat的返回值类型
            logger.debug(f"AddListenChat返回值类型: {type(result)}, 值: {result}")

            # 检查listen字典中的对象类型
            if hasattr(original_instance, 'listen') and nickname in original_instance.listen:
                chat_obj = original_instance.listen[nickname]
                logger.debug(f"listen[{nickname}]的类型: {type(chat_obj)}, 值: {chat_obj}")

        logger.info(f"成功添加监听对象: {nickname}")

        return jsonify({
            'code': 0,
            'message': '添加监听成功',
            'data': {
                'nickname': nickname,
                'library': lib_name
            }
        })
    except Exception as e:
        logger.error(f"添加监听失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'添加监听失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/message/listen/get', methods=['GET'])
@require_api_key
def get_listen_messages():
    """获取监听消息 - 统一处理wxauto和wxautox"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'
        logger.info(f"获取监听消息，使用库: {lib_name}")

        # 统一从全局消息缓存获取消息
        messages = {}
        if _message_cache:
            logger.info(f"缓存中的聊天对象: {list(_message_cache.keys())}")

            # 找到第一个有消息的聊天对象
            for chat_name, msg_list in _message_cache.items():
                if msg_list:  # 如果有消息
                    messages = {chat_name: msg_list}
                    logger.info(f"返回 {chat_name} 的 {len(msg_list)} 条消息")
                    # 清空缓存（消息已被消费）
                    _message_cache[chat_name] = []
                    break

        if not messages:
            logger.info("缓存中没有新消息")
            messages = {}

        # 直接返回消息，不需要复杂的格式化
        return jsonify({
            'code': 0,
            'message': '获取消息成功' if messages else '没有新消息',
            'data': {'messages': messages}
        })

    except Exception as e:
        logger.error(f"获取监听消息失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3002,
            'message': f'获取监听消息失败: {str(e)}',
            'data': None
        }), 500


@api_bp.route('/message/listen/remove', methods=['POST'])
@require_api_key
def remove_listen_chat():
    """移除监听对象 - 统一处理wxauto和wxautox"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    if not data or 'nickname' not in data:
        return jsonify({
            'code': 1001,
            'message': '缺少必要参数: nickname',
            'data': None
        }), 400

    nickname = data['nickname']

    try:
        # 获取原始微信实例（绕过WeChatAdapter的复杂处理）
        original_instance = wx_instance._instance if hasattr(wx_instance, '_instance') else wx_instance
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'

        logger.info(f"移除监听对象: {nickname}, 使用库: {lib_name}")

        # 统一调用RemoveListenChat方法
        if hasattr(original_instance, 'RemoveListenChat'):
            result = original_instance.RemoveListenChat(nickname)
            logger.info(f"RemoveListenChat调用结果: {result}")
        else:
            logger.warning(f"{lib_name}库不支持RemoveListenChat方法")

        # 从全局缓存中移除
        if nickname in _message_cache:
            del _message_cache[nickname]
            logger.info(f"已从缓存中移除监听对象: {nickname}")

        return jsonify({
            'code': 0,
            'message': '移除监听成功',
            'data': {
                'nickname': nickname,
                'library': lib_name
            }
        })

    except Exception as e:
        logger.error(f"移除监听失败: {str(e)}")
        return jsonify({
            'code': 3003,
            'message': f'移除监听失败: {str(e)}',
            'data': None
        }), 500



    except Exception as e:
        logger.error(f"获取监听消息失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3002,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500



@api_bp.route('/chat-window/message/send', methods=['POST'])
@require_api_key
def chat_window_send_message():
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message = data.get('message')
    at_list = data.get('at_list', [])
    clear = data.get('clear', True)

    if not who or not message:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        logger.debug(f"发送消息，当前使用的库: {lib_name}")

        # 安全地获取listen属性
        listen = {}
        try:
            listen = wx_instance.listen
        except Exception as e:
            logger.error(f"获取监听列表失败: {str(e)}")
            return jsonify({
                'code': 3001,
                'message': f'获取监听列表失败: {str(e)}',
                'data': None
            }), 500

        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 调试信息：检查chat_wnd的类型
        logger.debug(f"chat_wnd类型: {type(chat_wnd)}, 值: {chat_wnd}")

        # 检查chat_wnd是否是tuple，如果是则尝试获取正确的对象
        if isinstance(chat_wnd, tuple):
            logger.error(f"检测到chat_wnd是tuple类型: {chat_wnd}")
            # 如果是tuple，可能需要取第一个元素或进行其他处理
            if len(chat_wnd) > 0:
                chat_wnd = chat_wnd[0]
                logger.info(f"使用tuple的第一个元素: {type(chat_wnd)}")
            else:
                return jsonify({
                    'code': 3001,
                    'message': f'聊天窗口对象类型错误: {type(listen[who])}',
                    'data': None
                }), 500

        # 进一步检查chat_wnd是否有SendMsg方法
        if not hasattr(chat_wnd, 'SendMsg'):
            logger.error(f"chat_wnd对象没有SendMsg方法: {type(chat_wnd)}")
            # 尝试重新获取聊天窗口
            try:
                # 先移除旧的监听对象
                wx_instance.RemoveListenChat(who)
                logger.info(f"已移除无效的监听对象: {who}")

                # 重新添加监听对象
                wx_instance.AddListenChat(who)
                logger.info(f"已重新添加监听对象: {who}")

                # 重新获取聊天窗口对象
                listen = wx_instance.listen
                if listen and who in listen:
                    chat_wnd = listen[who]
                    logger.info(f"重新获取的chat_wnd类型: {type(chat_wnd)}")
                else:
                    return jsonify({
                        'code': 3001,
                        'message': f'重新添加监听对象后仍无法获取聊天窗口: {who}',
                        'data': None
                    }), 500
            except Exception as e:
                logger.error(f"重新添加监听对象失败: {str(e)}")
                return jsonify({
                    'code': 3001,
                    'message': f'聊天窗口对象无效，重新添加失败: {str(e)}',
                    'data': None
                }), 500

        # 根据不同的库使用不同的处理方法
        if lib_name == 'wxautox':
            # 对于wxautox库，直接调用方法，包含clear参数
            if at_list:
                chat_wnd.SendMsg(message, clear=clear, at=at_list)
            else:
                chat_wnd.SendMsg(message, clear=clear)
        else:
            # 对于wxauto库，不传递clear参数
            try:
                # 使用_handle_chat_window_method方法调用SendMsg
                if hasattr(wx_instance, '_handle_chat_window_method'):
                    if at_list:
                        wx_instance._handle_chat_window_method(chat_wnd, 'SendMsg', message, at=at_list)
                    else:
                        wx_instance._handle_chat_window_method(chat_wnd, 'SendMsg', message)
                else:
                    # 如果没有_handle_chat_window_method方法，直接调用
                    if at_list:
                        chat_wnd.SendMsg(message, at=at_list)
                    else:
                        chat_wnd.SendMsg(message)
            except Exception as e:
                logger.error(f"发送消息失败: {str(e)}")
                raise

        return jsonify({
            'code': 0,
            'message': '发送成功',
            'data': {'message_id': 'success'}
        })
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3001,
            'message': f'发送失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/chat-window/message/send-typing', methods=['POST'])
@require_api_key
def chat_window_send_typing_message():
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message = data.get('message')
    at_list = data.get('at_list', [])
    clear = data.get('clear', True)

    if not who or not message:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        logger.debug(f"发送打字消息，当前使用的库: {lib_name}")

        # 安全地获取listen属性
        listen = {}
        try:
            listen = wx_instance.listen
        except Exception as e:
            logger.error(f"获取监听列表失败: {str(e)}")
            return jsonify({
                'code': 3001,
                'message': f'获取监听列表失败: {str(e)}',
                'data': None
            }), 500

        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 处理@列表
        if at_list:
            if message and not message.endswith('\n'):
                message += '\n'
            for user in at_list:
                message += f"{{@{user}}}"
                if user != at_list[-1]:
                    message += '\n'

        # 根据不同的库使用不同的处理方法
        if lib_name == 'wxautox':
            # 对于wxautox库，直接调用SendTypingText方法，包含clear参数
            chat_wnd.SendTypingText(message, clear=clear)
        else:
            # 对于wxauto库，使用SendMsg方法代替SendTypingText方法，不传递clear参数
            try:
                # 使用_handle_chat_window_method方法调用SendMsg
                if hasattr(wx_instance, '_handle_chat_window_method'):
                    # wxauto库不支持SendTypingText方法，使用SendMsg代替
                    wx_instance._handle_chat_window_method(chat_wnd, 'SendMsg', message)
                else:
                    # 如果没有_handle_chat_window_method方法，直接调用SendMsg
                    chat_wnd.SendMsg(message)
            except Exception as e:
                logger.error(f"发送打字消息失败: {str(e)}")
                raise

        return jsonify({
            'code': 0,
            'message': '发送成功',
            'data': {'message_id': 'success'}
        })
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3001,
            'message': f'发送失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/chat-window/message/send-file', methods=['POST'])
@require_api_key
def chat_window_send_file():
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    file_paths = data.get('file_paths', [])

    if not who or not file_paths:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        logger.debug(f"发送文件，当前使用的库: {lib_name}")

        # 安全地获取listen属性
        listen = {}
        try:
            listen = wx_instance.listen
        except Exception as e:
            logger.error(f"获取监听列表失败: {str(e)}")
            return jsonify({
                'code': 3001,
                'message': f'获取监听列表失败: {str(e)}',
                'data': None
            }), 500

        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]
        success_count = 0
        failed_files = []

        for file_path in file_paths:
            if not os.path.exists(file_path):
                failed_files.append({
                    'path': file_path,
                    'reason': '文件不存在'
                })
                continue

            try:
                # 根据不同的库使用不同的处理方法
                if lib_name == 'wxautox':
                    # 对于wxautox库，直接调用方法
                    chat_wnd.SendFiles(file_path)
                else:
                    # 对于wxauto库，使用更健壮的处理方法
                    if hasattr(wx_instance, '_handle_chat_window_method'):
                        wx_instance._handle_chat_window_method(chat_wnd, 'SendFiles', file_path)
                    else:
                        # 如果没有_handle_chat_window_method方法，直接调用
                        chat_wnd.SendFiles(file_path)

                success_count += 1
            except Exception as e:
                logger.error(f"发送文件失败: {file_path} - {str(e)}")
                failed_files.append({
                    'path': file_path,
                    'reason': str(e)
                })

        return jsonify({
            'code': 0 if not failed_files else 3001,
            'message': '发送完成' if not failed_files else '部分文件发送失败',
            'data': {
                'success_count': success_count,
                'failed_files': failed_files
            }
        })
    except Exception as e:
        logger.error(f"发送文件失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3001,
            'message': f'发送失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/chat-window/message/at-all', methods=['POST'])
@require_api_key
def chat_window_at_all():
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    message = data.get('message')

    if not who:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        logger.debug(f"发送@所有人消息，当前使用的库: {lib_name}")

        # 安全地获取listen属性
        listen = {}
        try:
            listen = wx_instance.listen
        except Exception as e:
            logger.error(f"获取监听列表失败: {str(e)}")
            return jsonify({
                'code': 3001,
                'message': f'获取监听列表失败: {str(e)}',
                'data': None
            }), 500

        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 根据不同的库使用不同的处理方法
        if lib_name == 'wxautox':
            # 对于wxautox库，直接调用方法
            chat_wnd.AtAll(message)
        else:
            # 对于wxauto库，使用更健壮的处理方法
            try:
                # 使用_handle_chat_window_method方法调用AtAll
                if hasattr(wx_instance, '_handle_chat_window_method'):
                    wx_instance._handle_chat_window_method(chat_wnd, 'AtAll', message)
                else:
                    # 如果没有_handle_chat_window_method方法，直接调用
                    chat_wnd.AtAll(message)
            except Exception as e:
                logger.error(f"发送@所有人消息失败: {str(e)}")
                raise

        return jsonify({
            'code': 0,
            'message': '发送成功',
            'data': {'message_id': 'success'}
        })
    except Exception as e:
        logger.error(f"发送@所有人消息失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3001,
            'message': f'发送失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/chat-window/info', methods=['GET'])
@require_api_key
def get_chat_window_info():
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
        logger.debug(f"获取聊天窗口信息，当前使用的库: {lib_name}")

        # 安全地获取listen属性
        listen = {}
        try:
            listen = wx_instance.listen
        except Exception as e:
            logger.error(f"获取监听列表失败: {str(e)}")
            return jsonify({
                'code': 3001,
                'message': f'获取监听列表失败: {str(e)}',
                'data': None
            }), 500

        if not listen or who not in listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404

        chat_wnd = listen[who]

        # 根据不同的库使用不同的处理方法
        if lib_name == 'wxautox':
            # 对于wxautox库，直接调用方法
            info = chat_wnd.ChatInfo()
        else:
            # 对于wxauto库，使用更健壮的处理方法
            try:
                # 使用_handle_chat_window_method方法调用ChatInfo
                if hasattr(wx_instance, '_handle_chat_window_method'):
                    info = wx_instance._handle_chat_window_method(chat_wnd, 'ChatInfo')
                else:
                    # 如果没有_handle_chat_window_method方法，直接调用
                    info = chat_wnd.ChatInfo()
            except Exception as e:
                logger.error(f"获取聊天窗口信息失败: {str(e)}")
                raise

        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': info
        })
    except Exception as e:
        logger.error(f"获取聊天窗口信息失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3001,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

# 群组相关接口
@api_bp.route('/group/list', methods=['GET'])
@require_api_key
def get_group_list():
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        groups = wx_instance.get_group_list()
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'groups': groups
            }
        })
    except Exception as e:
        return jsonify({
            'code': 4001,
            'message': f'获取群列表失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/group/manage', methods=['POST'])
@require_api_key
def manage_group():
    global wx_instance
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    group_name = data.get('group_name')
    action = data.get('action')
    params = data.get('params', {})

    if not group_name or not action:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        if action == 'rename':
            new_name = params.get('new_name')
            if not new_name:
                return jsonify({
                    'code': 1002,
                    'message': '缺少新群名称',
                    'data': None
                }), 400
            # 执行重命名操作
            wx_instance.ChatWith(group_name)
            wx_instance.RenameGroup(new_name)
        elif action == 'quit':
            # 退出群聊
            wx_instance.ChatWith(group_name)
            wx_instance.QuitGroup()

        return jsonify({
            'code': 0,
            'message': '操作成功',
            'data': {'success': True}
        })
    except Exception as e:
        return jsonify({
            'code': 4001,
            'message': f'群操作失败: {str(e)}',
            'data': None
        }), 500

# 联系人相关接口
@api_bp.route('/contact/list', methods=['GET'])
@require_api_key
def get_contact_list():
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        contacts = wx_instance.get_friend_list()
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'friends': contacts
            }
        })
    except Exception as e:
        return jsonify({
            'code': 5001,
            'message': f'获取好友列表失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    wx_instance = wechat_manager.get_instance()
    wx_status = "not_initialized"
    wx_lib = "unknown"

    if wx_instance:
        wx_status = "connected" if wechat_manager.check_connection() else "disconnected"

        # 获取当前使用的库名称 - 不依赖微信实例初始化
        try:
            # 方法1: 尝试从适配器获取库名称
            if hasattr(wx_instance, 'get_lib_name'):
                lib_name = wx_instance.get_lib_name()
                if lib_name:
                    wx_lib = lib_name
                else:
                    # 如果适配器还没初始化，从配置获取
                    from app.config import Config
                    wx_lib = Config.WECHAT_LIB
            else:
                # 如果没有get_lib_name方法，从配置获取
                from app.config import Config
                wx_lib = Config.WECHAT_LIB
        except Exception:
            # 如果所有方法都失败，尝试检测可用的库
            try:
                # 简单检测：尝试导入库来确定当前可用的库
                try:
                    import wxautox
                    wx_lib = "wxautox"
                except ImportError:
                    try:
                        import wxauto
                        wx_lib = "wxauto"
                    except ImportError:
                        wx_lib = "unknown"
            except Exception:
                wx_lib = "unknown"

    return jsonify({
        'code': 0,
        'message': '服务正常',
        'data': {
            'status': 'ok',
            'wechat_status': wx_status,
            'uptime': int(time.time() - start_time),
            'wx_lib': wx_lib
        }
    })

@api_bp.route('/system/resources', methods=['GET'])
@require_api_key
def get_resources():
    """获取系统资源使用情况"""
    try:
        resources = get_system_resources()
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': resources
        })
    except Exception as e:
        logger.error(f"获取系统资源信息失败: {str(e)}")
        return jsonify({
            'code': 5000,
            'message': f'获取系统资源信息失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/message/listen/add-current', methods=['POST'])
@require_api_key
def add_current_chat_to_listen():
    """将当前打开的聊天窗口添加到监听列表"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        logger.error("微信未初始化")
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        data = request.get_json() or {}

        # 更灵活的布尔值处理
        def parse_bool(value, default=False):
            if value is None:
                return default
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                value = value.lower()
                if value in ('true', '1', 'yes', 'y', 'on'):
                    return True
                if value in ('false', '0', 'no', 'n', 'off'):
                    return False
            return default

        # 获取参数并设置默认值
        savepic = parse_bool(data.get('savepic'), False)
        savevideo = parse_bool(data.get('savevideo'), False)
        savefile = parse_bool(data.get('savefile'), False)
        savevoice = parse_bool(data.get('savevoice'), False)
        parseurl = parse_bool(data.get('parseurl'), False)

        logger.debug(f"处理参数: savepic={savepic}, savevideo={savevideo}, savefile={savefile}, savevoice={savevoice}, parseurl={parseurl}")

        # 获取当前聊天窗口
        current_chat = wx_instance.GetCurrentWindowName()
        if not current_chat:
            return jsonify({
                'code': 3001,
                'message': '未找到当前聊天窗口',
                'data': None
            }), 404

        # 如果窗口名称以 "微信" 开头，说明不是聊天窗口
        if current_chat.startswith('微信'):
            return jsonify({
                'code': 3001,
                'message': '当前窗口不是聊天窗口',
                'data': None
            }), 400

        # 获取当前使用的库
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'
        logger.debug(f"添加当前聊天窗口到监听列表，当前使用的库: {lib_name}")

        # 根据不同的库构建不同的参数
        if lib_name == 'wxautox':
            # wxautox支持所有参数
            params = {
                'who': current_chat,
                'savepic': savepic,
                'savevideo': savevideo,
                'savefile': savefile,
                'savevoice': savevoice,
                'parseurl': parseurl
            }
            logger.debug(f"使用wxautox参数: {params}")
        else:
            # wxauto不支持savevideo和parseurl参数
            params = {
                'who': current_chat,
                'savepic': savepic,
                'savefile': savefile,
                'savevoice': savevoice
            }
            logger.debug(f"使用wxauto参数: {params}")

        # 添加到监听列表
        wx_instance.AddListenChat(**params)

        return jsonify({
            'code': 0,
            'message': '添加监听成功',
            'data': {
                'who': current_chat,
                'options': {
                    'savepic': savepic,
                    'savevideo': savevideo,
                    'savefile': savefile,
                    'savevoice': savevoice,
                    'parseurl': parseurl
                }
            }
        })
    except Exception as e:
        logger.error(f"添加当前聊天窗口到监听列表失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3001,
            'message': f'添加监听失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/message/listen/reactivate', methods=['POST'])
@require_api_key
def reactivate_listen_chat():
    """重新激活监听对象，用于处理窗口激活失败的情况"""
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
        # 获取当前使用的库
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'
        logger.debug(f"重新激活监听对象，当前使用的库: {lib_name}")

        # 获取请求参数
        savepic = data.get('savepic', True)
        savevideo = data.get('savevideo', False)
        savefile = data.get('savefile', True)
        savevoice = data.get('savevoice', True)
        parseurl = data.get('parseurl', False)

        # 根据不同的库构建不同的参数
        if lib_name == 'wxautox':
            # wxautox支持所有参数
            params = {
                'who': who,
                'savepic': savepic,
                'savevideo': savevideo,
                'savefile': savefile,
                'savevoice': savevoice,
                'parseurl': parseurl
            }
        else:
            # wxauto不支持savevideo和parseurl参数
            params = {
                'who': who,
                'savepic': savepic,
                'savefile': savefile,
                'savevoice': savevoice
            }

        # 无论窗口是否有效，都执行重新添加的操作
        logger.info(f"准备重新激活聊天对象: {who}")

        # 先移除监听对象
        try:
            wx_instance.RemoveListenChat(who)
            logger.info(f"已移除监听对象: {who}")
        except Exception as e:
            logger.warning(f"移除监听对象失败: {str(e)}")

        # 尝试打开聊天窗口
        try:
            wx_instance.ChatWith(who)
            logger.info(f"已打开聊天窗口: {who}")
            # 等待窗口打开
            import time
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"打开聊天窗口失败: {str(e)}")

        # 重新添加监听对象
        wx_instance.AddListenChat(**params)
        logger.info(f"已重新添加监听对象: {who}")

        return jsonify({
            'code': 0,
            'message': '重新激活监听对象成功',
            'data': {'who': who}
        })
    except Exception as e:
        logger.error(f"重新激活监听对象失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3001,
            'message': f'重新激活失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/file/download', methods=['POST'])
@require_api_key
def download_file():
    """下载文件接口"""
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({
                'code': 1002,
                'message': '参数错误',
                'data': {'error': '缺少file_path参数'}
            }), 400

        file_path = data['file_path']
        if not os.path.exists(file_path):
            return jsonify({
                'code': 3003,
                'message': '文件下载失败',
                'data': {'error': '文件不存在'}
            }), 404

        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > 100 * 1024 * 1024:  # 100MB限制
            return jsonify({
                'code': 3003,
                'message': '文件下载失败',
                'data': {'error': '文件大小超过100MB限制'}
            }), 400

        # 获取文件名
        filename = os.path.basename(file_path)

        # 读取文件内容
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # 设置响应头
        response = Response(
            file_content,
            mimetype='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        return response

    except PermissionError:
        return jsonify({
            'code': 3003,
            'message': '文件下载失败',
            'data': {'error': '文件访问权限不足'}
        }), 403
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3003,
            'message': '文件下载失败',
            'data': {'error': str(e)}
        }), 500


@api_bp.route('/system/queue-stats', methods=['GET'])
@require_api_key
def get_queue_status():
    """获取队列状态"""
    try:
        stats = get_queue_stats()
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': stats
        })
    except Exception as e:
        logger.error(f"获取队列状态失败: {str(e)}")
        return jsonify({
            'code': 5002,
            'message': f'获取队列状态失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/config/get-api-settings', methods=['GET'])
def get_api_settings():
    """获取API测试工具的配置设置（仅限localhost访问）"""
    try:
        # 安全检查：仅允许localhost访问
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()

        # 允许的本地IP地址
        allowed_ips = ['127.0.0.1', '::1', 'localhost']

        if client_ip not in allowed_ips and not client_ip.startswith('127.') and not client_ip.startswith('192.168.'):
            logger.warning(f"配置API访问被拒绝，来源IP: {client_ip}")
            return jsonify({
                'code': 4003,
                'message': '访问被拒绝：此API仅限本地访问',
                'data': None
            }), 403

        # 使用现有的Config类
        host = Config.HOST
        port = Config.PORT

        # 如果host是0.0.0.0，则使用localhost
        if host == '0.0.0.0':
            host = 'localhost'

        base_url = f"http://{host}:{port}"

        # 获取API密钥（取第一个）
        api_keys = Config.get_api_keys()
        api_key = api_keys[0] if api_keys else 'test-key-2'

        return jsonify({
            'code': 0,
            'message': '获取API设置成功',
            'data': {
                'base_url': base_url,
                'api_key': api_key,
                'host': host,
                'port': port
            }
        })

    except Exception as e:
        logger.error(f"获取API设置失败: {str(e)}")
        return jsonify({
            'code': 5003,
            'message': f'获取API设置失败: {str(e)}',
            'data': {
                'base_url': 'http://localhost:5000',
                'api_key': 'test-key-2'
            }
        }), 200  # 返回200但提供默认值


# Chat类监听相关API - 与message监听API保持一致
@api_bp.route('/chat/listen/add', methods=['POST'])
@require_api_key
def chat_listen_add():
    """Chat类添加监听对象 - 与/api/message/listen/add功能相同"""
    return add_listen_chat()


@api_bp.route('/chat/listen/get', methods=['GET'])
@require_api_key
def chat_listen_get():
    """Chat类获取监听消息 - 与/api/message/listen/get功能相同"""
    return get_listen_messages()


@api_bp.route('/chat/listen/remove', methods=['POST'])
@require_api_key
def chat_listen_remove():
    """Chat类移除监听对象 - 与/api/message/listen/remove功能相同"""
    return remove_listen_chat()