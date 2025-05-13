from flask import Blueprint, jsonify, request, g, Response, send_file
from app.auth import require_api_key
from app.logs import logger
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

# 记录程序启动时间
start_time = time.time()

@api_bp.before_request
def before_request():
    g.start_time = time.time()
    # 记录请求信息，但不记录详细的请求头和请求体
    logger.info(f"收到请求: {request.method} {request.path}")
    # 确保日志立即刷新
    for handler in logger.logger.handlers:
        handler.flush()

    # 只在开发环境下记录请求体，且不记录请求头
    if Config.DEBUG and request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
        logger.debug(f"请求体: {request.get_json()}")
        # 确保日志立即刷新
        for handler in logger.logger.handlers:
            handler.flush()

@api_bp.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        # 修改日志格式，确保API计数器能够正确识别 - 确保状态码周围有空格
        logger.info(f"请求处理完成: {request.method} {request.path} - 状态码: {response.status_code} - 耗时: {duration:.2f}秒")
        # 确保日志立即刷新
        for handler in logger.logger.handlers:
            handler.flush()
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
                # 这里不需要重复打开，但可以检查是否已经打开
                try:
                    current_chat = wx_instance._instance.CurrentChat()
                    if current_chat != "文件传输助手":
                        logger.info("当前聊天窗口不是文件传输助手，尝试打开文件传输助手窗口...")
                        wx_instance._instance.ChatWith("文件传输助手")
                        import time
                        time.sleep(0.5)
                        logger.info("文件传输助手窗口已打开")
                except Exception as chat_e:
                    logger.warning(f"检查或打开文件传输助手窗口失败: {str(chat_e)}")
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

        # 使用正确的参数调用 SendTypingText
        if at_list:
            if message and not message.endswith('\n'):
                message += '\n'
            for user in at_list:
                message += f"{{@{user}}}"
                if user != at_list[-1]:
                    message += '\n'
        chat_name.SendTypingText(message, clear=clear)

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
            # wxautox支持所有参数
            params = {
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
                'savepic': savepic,
                'savefile': savefile,
                'savevoice': savevoice
            }
            logger.debug(f"使用wxauto参数: {params}")

        # 确保保存路径设置正确
        try:
            import config_manager
            from wxauto.elements import WxParam
            temp_dir = str(config_manager.TEMP_DIR.absolute())
            # 记录原始保存路径
            original_path = WxParam.DEFALUT_SAVEPATH
            logger.debug(f"原始wxauto保存路径: {original_path}")
            # 修改为新的保存路径
            WxParam.DEFALUT_SAVEPATH = temp_dir
            logger.debug(f"已修改wxauto保存路径为: {temp_dir}")
        except Exception as path_e:
            logger.error(f"设置wxauto保存路径失败: {str(path_e)}")

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

        formatted_messages = {}
        for chat_name, msg_list in messages.items():
            # 清理群名中的人数信息
            clean_name = clean_group_name(chat_name)
            formatted_messages[clean_name] = []

            for msg in msg_list:
                # 检查消息类型
                if msg.type in ['image', 'file', 'video', 'voice']:
                    # 检查文件是否存在且大小大于0
                    if hasattr(msg, 'file_path') and msg.file_path:
                        try:
                            if not os.path.exists(msg.file_path) or os.path.getsize(msg.file_path) == 0:
                                logger.warning(f"文件不存在或大小为0: {msg.file_path}")
                                # 记录文件不存在的警告，但不重试下载
                                logger.warning("文件不存在或大小为0，但不重试下载")
                        except Exception as e:
                            logger.error(f"检查文件失败: {str(e)}")

                formatted_messages[clean_name].append({
                    'type': msg.type,
                    'content': msg.content,
                    'sender': msg.sender,
                    'id': msg.id,
                    'mtype': getattr(msg, 'mtype', None),
                    'sender_remark': getattr(msg, 'sender_remark', None),
                    'file_path': getattr(msg, 'file_path', None)
                })

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
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        logger.debug(f"当前使用的库: {lib_name}")

        # 根据不同的库构建不同的参数
        if lib_name == 'wxautox':
            # wxautox支持所有参数
            params = {
                'who': who,
                'savepic': data.get('savepic', False),
                'savevideo': data.get('savevideo', False),
                'savefile': data.get('savefile', False),
                'savevoice': data.get('savevoice', False),
                'parseurl': data.get('parseurl', False)
            }
            logger.debug(f"使用wxautox参数: {params}")
        else:
            # wxauto不支持savevideo和parseurl参数
            params = {
                'who': who,
                'savepic': data.get('savepic', False),
                'savefile': data.get('savefile', False),
                'savevoice': data.get('savevoice', False)
            }
            logger.debug(f"使用wxauto参数: {params}")

        # 调用AddListenChat方法
        wx_instance.AddListenChat(**params)

        return jsonify({
            'code': 0,
            'message': '添加监听成功',
            'data': {'who': who}
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
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    who = request.args.get('who')  # 可选参数

    try:
        # 获取当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        logger.debug(f"获取监听消息，当前使用的库: {lib_name}")

        # 获取请求参数
        savepic = request.args.get('savepic', 'true').lower() in ('true', '1', 'yes', 'y', 'on')
        savevideo = request.args.get('savevideo', 'false').lower() in ('true', '1', 'yes', 'y', 'on')
        savefile = request.args.get('savefile', 'true').lower() in ('true', '1', 'yes', 'y', 'on')
        savevoice = request.args.get('savevoice', 'true').lower() in ('true', '1', 'yes', 'y', 'on')
        parseurl = request.args.get('parseurl', 'false').lower() in ('true', '1', 'yes', 'y', 'on')

        # 根据不同的库构建不同的参数
        if lib_name == 'wxautox':
            # wxautox的GetListenMessage方法只接受who参数
            params = {
                'who': who
            }
            logger.debug(f"使用wxautox参数: {params}")
        else:
            # wxauto不支持savevideo和parseurl参数
            params = {
                'who': who,
                'savepic': savepic,
                'savefile': savefile,
                'savevoice': savevoice
            }
            logger.debug(f"使用wxauto参数: {params}")

        # 如果指定了who参数，检查该对象是否在监听列表中
        if who:
            try:
                listen_list = wx_instance.listen

                # 检查是否在监听列表中
                if who not in listen_list:
                    logger.warning(f"聊天对象 {who} 不在监听列表中，尝试自动添加")
                    # 自动添加到监听列表
                    add_params = params.copy()
                    wx_instance.AddListenChat(**add_params)
                    logger.info(f"已自动添加聊天对象 {who} 到监听列表")
                else:
                    # 对象已在监听列表中，不做任何操作
                    logger.debug(f"聊天对象 {who} 已在监听列表中，直接获取消息")
            except Exception as check_e:
                logger.error(f"检查或添加监听对象失败: {str(check_e)}")
                # 继续执行，让后续代码处理可能的错误

        # 调用GetListenMessage方法
        try:
            messages = wx_instance.GetListenMessage(**params)
        except Exception as e:
            error_str = str(e)
            logger.error(f"调用GetListenMessage方法失败: {error_str}")

            # 检查是否是窗口激活失败的错误
            if "激活聊天窗口失败" in error_str or "SetWindowPos" in error_str or "无效的窗口句柄" in error_str:
                logger.warning(f"检测到窗口激活失败，尝试重新添加监听对象: {who}")

                if who:
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

                    # 再次尝试获取消息
                    try:
                        messages = wx_instance.GetListenMessage(**params)
                    except Exception as e:
                        logger.error(f"重新添加监听对象后获取消息仍然失败: {str(e)}")
                        messages = {}
                else:
                    messages = {}
            else:
                messages = {}

        if not messages:
            return jsonify({
                'code': 0,
                'message': '没有新消息',
                'data': {'messages': {}}
            })

        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')

        # 辅助函数：清理群名中的人数信息
        def clean_group_name(name):
            # 匹配群名后面的 (数字) 模式
            import re
            return re.sub(r'\s*\(\d+\)$', '', name)

        # 初始化格式化消息字典
        formatted_messages = {}

        # 检查messages的类型，处理不同的返回格式
        if isinstance(messages, list):
            # 如果返回的是列表（指定了who参数时可能发生）
            logger.debug(f"GetListenMessage返回了列表，长度: {len(messages)}")

            if who:
                # 如果指定了who参数，将消息列表添加到该聊天对象下
                try:
                    # 清理群名中的人数信息
                    clean_who = clean_group_name(who)
                    formatted_messages[clean_who] = []
                    for msg in messages:
                        try:
                            # 格式化单条消息
                            formatted_msg = {
                                'type': getattr(msg, 'type', 'unknown'),
                                'content': getattr(msg, 'content', ''),
                                'sender': getattr(msg, 'sender', ''),
                                'id': getattr(msg, 'id', ''),
                                'mtype': getattr(msg, 'mtype', None),
                                'sender_remark': getattr(msg, 'sender_remark', None)
                            }
                            formatted_messages[clean_who].append(formatted_msg)
                        except Exception as msg_e:
                            logger.error(f"格式化消息失败: {str(msg_e)}")
                            # 继续处理下一条消息
                            continue
                except Exception as e:
                    logger.error(f"处理消息列表失败: {str(e)}")
            else:
                # 如果没有指定who参数但返回了列表，这是一种异常情况
                logger.warning("GetListenMessage返回了列表，但未指定who参数")
        elif isinstance(messages, dict):
            # 如果返回的是字典（未指定who参数时应该发生）
            logger.debug(f"GetListenMessage返回了字典，键数量: {len(messages)}")

            # 根据不同的库使用不同的格式化方法
            if lib_name == 'wxautox':
                # 对于wxautox库，使用原有的格式化方法
                for chat_wnd, msg_list in messages.items():
                    try:
                        chat_name = getattr(chat_wnd, 'who', str(chat_wnd))
                        # 清理群名中的人数信息
                        clean_name = clean_group_name(chat_name)
                        formatted_messages[clean_name] = [{
                            'type': msg.type,
                            'content': msg.content,
                            'sender': msg.sender,
                            'id': msg.id,
                            'mtype': getattr(msg, 'mtype', None),
                            'sender_remark': getattr(msg, 'sender_remark', None)
                        } for msg in msg_list]
                    except Exception as e:
                        logger.error(f"格式化wxautox消息失败: {str(e)}")
                        continue
            else:
                # 对于wxauto库，使用更健壮的格式化方法
                try:
                    # 遍历消息并格式化
                    for chat_wnd, msg_list in messages.items():
                        try:
                            # 获取聊天窗口名称
                            chat_name = getattr(chat_wnd, 'who', str(chat_wnd))
                            # 清理群名中的人数信息
                            clean_name = clean_group_name(chat_name)
                            formatted_messages[clean_name] = []

                            # 遍历消息列表
                            for msg in msg_list:
                                try:
                                    # 格式化单条消息
                                    formatted_msg = {
                                        'type': getattr(msg, 'type', 'unknown'),
                                        'content': getattr(msg, 'content', ''),
                                        'sender': getattr(msg, 'sender', ''),
                                        'id': getattr(msg, 'id', ''),
                                        'mtype': getattr(msg, 'mtype', None),
                                        'sender_remark': getattr(msg, 'sender_remark', None)
                                    }
                                    formatted_messages[clean_name].append(formatted_msg)
                                except Exception as msg_e:
                                    logger.error(f"格式化消息失败: {str(msg_e)}")
                                    # 继续处理下一条消息
                                    continue
                        except Exception as chat_e:
                            logger.error(f"处理聊天窗口消息失败: {str(chat_e)}")
                            # 继续处理下一个聊天窗口
                            continue
                except Exception as format_e:
                    logger.error(f"格式化消息列表失败: {str(format_e)}")
                    # 如果格式化失败，返回空消息列表
                    formatted_messages = {}
        else:
            # 如果返回的既不是列表也不是字典，记录错误
            logger.error(f"GetListenMessage返回了意外的类型: {type(messages)}")

        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'messages': formatted_messages
            }
        })
    except Exception as e:
        logger.error(f"获取监听消息失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3002,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/message/listen/remove', methods=['POST'])
@require_api_key
def remove_listen_chat():
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
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        logger.debug(f"移除监听，当前使用的库: {lib_name}")

        # 调用RemoveListenChat方法，现在已经在适配器中添加了异常处理
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
    except Exception as e:
        logger.error(f"移除监听失败: {str(e)}", exc_info=True)
        return jsonify({
            'code': 3001,
            'message': f'移除失败: {str(e)}',
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
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
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
    global wx_instance
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        groups = wx_instance.GetGroupList()
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'groups': [{'name': group} for group in groups]
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
    global wx_instance
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        contacts = wx_instance.GetFriendList()
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'friends': [{'nickname': contact} for contact in contacts]
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
        # 获取当前使用的库名称
        wx_lib = getattr(wx_instance, '_lib_name', 'wxauto')

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
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
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
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
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