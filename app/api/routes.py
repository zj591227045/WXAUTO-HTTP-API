from flask import Blueprint, jsonify, request, g
from app.auth import require_api_key
from app.logs import logger
from app.wechat import wechat_manager
from app.system_monitor import get_system_resources
import os
import time
from typing import Optional, List

api_bp = Blueprint('api', __name__)

# 记录程序启动时间
start_time = time.time()

@api_bp.before_request
def before_request():
    g.start_time = time.time()
    logger.info(f"收到请求: {request.method} {request.path}")
    logger.debug(f"请求头: {dict(request.headers)}")
    if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
        logger.debug(f"请求体: {request.get_json()}")

@api_bp.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        logger.info(f"请求处理完成: {request.method} {request.path} - 状态码: {response.status_code} - 耗时: {duration:.2f}秒")
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
            return jsonify({
                'code': 0,
                'message': '初始化成功',
                'data': {'status': 'connected'}
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
    return jsonify({
        'code': 0,
        'message': '获取成功',
        'data': {
            'status': 'online' if is_connected else 'offline'
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
    clear = "1" if data.get('clear', True) else "0"
    
    if not receiver or not message:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400
        
    try:
        formatted_message = format_at_message(message, at_list)
        
        # 使用精确匹配模式查找联系人
        chat_name = wx_instance.ChatWith(receiver, exact=True)
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
            
        if at_list:
            wx_instance.SendMsg(formatted_message, clear=clear, at=at_list)
            wx_instance.SendMsg(message, clear=clear, at=at_list)
        else:
            wx_instance.SendMsg(message, clear=clear)
            
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
        # 使用精确匹配模式查找联系人
        chat_name = wx_instance.ChatWith(receiver, exact=True)
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
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400
    
    data = request.get_json()
    receiver = data.get('receiver')
    file_paths = data.get('file_paths', [])
    
    if not receiver or not file_paths:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400
    
    failed_files = []
    success_count = 0
    
    try:
        # 使用精确匹配模式查找联系人
        chat_name = wx_instance.ChatWith(receiver, exact=True)
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
        
        return jsonify({
            'code': 0 if not failed_files else 3001,
            'message': '发送完成' if not failed_files else '部分文件发送失败',
            'data': {
                'success_count': success_count,
                'failed_files': failed_files
            }
        })
    except Exception as e:
        logger.error(f"发送文件失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'发送失败: {str(e)}',
            'data': None
        }), 500

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

        messages = wx_instance.GetNextNewMessage(
            savepic=savepic,
            savevideo=savevideo,
            savefile=savefile,
            savevoice=savevoice,
            parseurl=parseurl
        )
        
        if not messages:
            return jsonify({
                'code': 0,
                'message': '没有新消息',
                'data': {'messages': {}}
            })
            
        formatted_messages = {}
        for chat_name, msg_list in messages.items():
            formatted_messages[chat_name] = [{
                'type': msg.type,
                'content': msg.content,
                'sender': msg.sender,
                'id': msg.id,
                'mtype': getattr(msg, 'mtype', None),
                'sender_remark': getattr(msg, 'sender_remark', None)
            } for msg in msg_list]
            
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
        wx_instance.AddListenChat(
            who=who,
            savepic=data.get('savepic', False),
            savevideo=data.get('savevideo', False),
            savefile=data.get('savefile', False),
            savevoice=data.get('savevoice', False),
            parseurl=data.get('parseurl', False),
            exact=data.get('exact', False)
        )
        
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
        messages = wx_instance.GetListenMessage(who)
        
        if not messages:
            return jsonify({
                'code': 0,
                'message': '没有新消息',
                'data': {'messages': {}}
            })
            
        formatted_messages = {}
        for chat_wnd, msg_list in messages.items():
            formatted_messages[chat_wnd.who] = [{
                'type': msg.type,
                'content': msg.content,
                'sender': msg.sender,
                'id': msg.id,
                'mtype': getattr(msg, 'mtype', None),
                'sender_remark': getattr(msg, 'sender_remark', None)
            } for msg in msg_list]
            
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'messages': formatted_messages
            }
        })
    except Exception as e:
        logger.error(f"获取监听消息失败: {str(e)}")
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
        wx_instance.RemoveListenChat(who)
        return jsonify({
            'code': 0,
            'message': '移除监听成功',
            'data': {'who': who}
        })
    except Exception as e:
        logger.error(f"移除监听失败: {str(e)}")
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
        if who not in wx_instance.listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404
            
        chat_wnd = wx_instance.listen[who]
        if at_list:
            chat_wnd.SendMsg(message, clear=clear, at=at_list)
        else:
            chat_wnd.SendMsg(message, clear=clear)
            
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
        if who not in wx_instance.listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404
            
        chat_wnd = wx_instance.listen[who]
        if at_list:
            if message and not message.endswith('\n'):
                message += '\n'
            for user in at_list:
                message += f"{{@{user}}}"
                if user != at_list[-1]:
                    message += '\n'
        chat_wnd.SendTypingText(message, clear=clear)
            
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
        if who not in wx_instance.listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404
            
        chat_wnd = wx_instance.listen[who]
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
                chat_wnd.SendFiles(file_path)
                success_count += 1
            except Exception as e:
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
        logger.error(f"发送文件失败: {str(e)}")
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
        if who not in wx_instance.listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404
            
        chat_wnd = wx_instance.listen[who]
        chat_wnd.AtAll(message)
            
        return jsonify({
            'code': 0,
            'message': '发送成功',
            'data': {'message_id': 'success'}
        })
    except Exception as e:
        logger.error(f"发送@所有人消息失败: {str(e)}")
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
        if who not in wx_instance.listen:
            return jsonify({
                'code': 3001,
                'message': f'聊天窗口 {who} 未在监听列表中',
                'data': None
            }), 404
            
        chat_wnd = wx_instance.listen[who]
        info = chat_wnd.ChatInfo()
            
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': info
        })
    except Exception as e:
        logger.error(f"获取聊天窗口信息失败: {str(e)}")
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
    
    if wx_instance:
        wx_status = "connected" if wechat_manager.check_connection() else "disconnected"
    
    return jsonify({
        'code': 0,
        'message': '服务正常',
        'data': {
            'status': 'ok',
            'wechat_status': wx_status,
            'uptime': int(time.time() - start_time)
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

        # 添加到监听列表
        wx_instance.AddListenChat(
            who=current_chat,
            savepic=savepic,
            savevideo=savevideo,
            savefile=savefile,
            savevoice=savevoice,
            parseurl=parseurl
        )
        
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