"""
WeChat类相关API路由
实现WeChat类的所有方法
"""

from flask import Blueprint, jsonify, request
from app.auth import require_api_key
from app.unified_logger import logger
from app.wechat import wechat_manager

wechat_bp = Blueprint('wechat_extended', __name__)

@wechat_bp.route('/get-session', methods=['GET'])
@require_api_key
def get_session():
    """获取当前会话列表"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 调用GetSession方法
        sessions = wx_instance.GetSession()

        # 格式化会话列表
        formatted_sessions = []
        for session in sessions:
            formatted_session = {
                'name': getattr(session, 'name', ''),
                'time': getattr(session, 'time', ''),
                'content': getattr(session, 'content', ''),
                'ismute': getattr(session, 'ismute', False),
                'isnew': getattr(session, 'isnew', False),
                'new_count': getattr(session, 'new_count', 0),
                'info': getattr(session, 'info', {})
            }
            formatted_sessions.append(formatted_session)

        return jsonify({
            'code': 0,
            'message': '获取会话列表成功',
            'data': {
                'sessions': formatted_sessions
            }
        })
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取会话列表失败: {str(e)}',
            'data': None
        }), 500

@wechat_bp.route('/send-url-card', methods=['POST'])
@require_api_key
def send_url_card():
    """发送链接卡片 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    url = data.get('url')
    friends = data.get('friends', [])
    timeout = data.get('timeout', 10)

    if not url or not friends:
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
                'message': '当前库版本不支持发送链接卡片功能',
                'data': None
            }), 400

        # 调用SendUrlCard方法
        result = wx_instance.SendUrlCard(url=url, friends=friends, timeout=timeout)

        return jsonify({
            'code': 0,
            'message': '发送链接卡片成功',
            'data': {
                'url': url,
                'friends': friends,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"发送链接卡片失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'发送链接卡片失败: {str(e)}',
            'data': None
        }), 500

@wechat_bp.route('/chat-with', methods=['POST'])
@require_api_key
def chat_with():
    """打开聊天窗口"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    exact = data.get('exact', False)

    if not who:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 调用ChatWith方法
        result = wx_instance.ChatWith(who, exact=exact)

        return jsonify({
            'code': 0,
            'message': '打开聊天窗口成功',
            'data': {
                'who': who,
                'result': result
            }
        })
    except Exception as e:
        logger.error(f"打开聊天窗口失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'打开聊天窗口失败: {str(e)}',
            'data': None
        }), 500

@wechat_bp.route('/get-sub-window', methods=['GET'])
@require_api_key
def get_sub_window():
    """获取子窗口实例"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    nickname = request.args.get('nickname')

    if not nickname:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 调用GetSubWindow方法
        sub_window = wx_instance.GetSubWindow(nickname)

        return jsonify({
            'code': 0,
            'message': '获取子窗口成功',
            'data': {
                'nickname': nickname,
                'has_window': sub_window is not None
            }
        })
    except Exception as e:
        logger.error(f"获取子窗口失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取子窗口失败: {str(e)}',
            'data': None
        }), 500

@wechat_bp.route('/get-all-sub-windows', methods=['GET'])
@require_api_key
def get_all_sub_windows():
    """获取所有子窗口实例"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 调用GetAllSubWindow方法
        sub_windows = wx_instance.GetAllSubWindow()

        # 格式化子窗口列表
        formatted_windows = []
        for window in sub_windows:
            formatted_window = {
                'who': getattr(window, 'who', ''),
                'window_id': str(window) if window else None
            }
            formatted_windows.append(formatted_window)

        return jsonify({
            'code': 0,
            'message': '获取所有子窗口成功',
            'data': {
                'sub_windows': formatted_windows
            }
        })
    except Exception as e:
        logger.error(f"获取所有子窗口失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取所有子窗口失败: {str(e)}',
            'data': None
        }), 500

# 为了兼容性，添加别名路由
@wechat_bp.route('/get-sub-windows', methods=['GET'])
@require_api_key
def get_sub_windows_alias():
    """获取所有子窗口实例 - 别名路由"""
    return get_all_sub_windows()

@wechat_bp.route('/start-listening', methods=['POST'])
@require_api_key
def start_listening():
    """开始监听"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 调用StartListening方法
        wx_instance.StartListening()

        return jsonify({
            'code': 0,
            'message': '开始监听成功',
            'data': None
        })
    except Exception as e:
        logger.error(f"开始监听失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'开始监听失败: {str(e)}',
            'data': None
        }), 500

@wechat_bp.route('/stop-listening', methods=['POST'])
@require_api_key
def stop_listening():
    """停止监听"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json() or {}
    remove = data.get('remove', True)

    try:
        # 调用StopListening方法
        wx_instance.StopListening(remove=remove)

        return jsonify({
            'code': 0,
            'message': '停止监听成功',
            'data': {'remove': remove}
        })
    except Exception as e:
        logger.error(f"停止监听失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'停止监听失败: {str(e)}',
            'data': None
        }), 500

@wechat_bp.route('/switch-to-chat', methods=['POST'])
@require_api_key
def switch_to_chat():
    """切换到聊天页面"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 调用SwitchToChat方法
        wx_instance.SwitchToChat()

        return jsonify({
            'code': 0,
            'message': '切换到聊天页面成功',
            'data': None
        })
    except Exception as e:
        logger.error(f"切换到聊天页面失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'切换到聊天页面失败: {str(e)}',
            'data': None
        }), 500

@wechat_bp.route('/switch-to-contact', methods=['POST'])
@require_api_key
def switch_to_contact():
    """切换到联系人页面"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 调用SwitchToContact方法
        wx_instance.SwitchToContact()

        return jsonify({
            'code': 0,
            'message': '切换到联系人页面成功',
            'data': None
        })
    except Exception as e:
        logger.error(f"切换到联系人页面失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'切换到联系人页面失败: {str(e)}',
            'data': None
        }), 500

@wechat_bp.route('/is-online', methods=['GET'])
@require_api_key
def is_online():
    """检查是否在线 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'
        if lib_name != 'wxautox':
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持在线状态检查功能',
                'data': None
            }), 400

        # 调用IsOnline方法
        online = wx_instance.IsOnline()

        return jsonify({
            'code': 0,
            'message': '获取在线状态成功',
            'data': {
                'online': online
            }
        })
    except Exception as e:
        logger.error(f"获取在线状态失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取在线状态失败: {str(e)}',
            'data': None
        }), 500

@wechat_bp.route('/get-my-info', methods=['GET'])
@require_api_key
def get_my_info():
    """获取我的信息 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = wx_instance.get_lib_name() if hasattr(wx_instance, 'get_lib_name') else 'wxauto'
        if lib_name != 'wxautox':
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持获取个人信息功能',
                'data': None
            }), 400

        # 调用GetMyInfo方法
        my_info = wx_instance.GetMyInfo()

        # 格式化个人信息
        formatted_info = {
            'nickname': getattr(my_info, 'nickname', ''),
            'wxid': getattr(my_info, 'wxid', ''),
            'phone': getattr(my_info, 'phone', ''),
            'email': getattr(my_info, 'email', ''),
            'signature': getattr(my_info, 'signature', ''),
            'region': getattr(my_info, 'region', ''),
            'avatar': getattr(my_info, 'avatar', '')
        }

        return jsonify({
            'code': 0,
            'message': '获取个人信息成功',
            'data': {
                'my_info': formatted_info
            }
        })
    except Exception as e:
        logger.error(f"获取个人信息失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取个人信息失败: {str(e)}',
            'data': None
        }), 500

@wechat_bp.route('/keep-running', methods=['POST'])
@require_api_key
def keep_running():
    """保持程序运行"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json() or {}
    timeout = data.get('timeout', 0)

    try:
        # 调用KeepRunning方法
        if timeout > 0:
            wx_instance.KeepRunning(timeout)
        else:
            wx_instance.KeepRunning()

        return jsonify({
            'code': 0,
            'message': '保持运行设置成功',
            'data': {
                'timeout': timeout
            }
        })
    except Exception as e:
        logger.error(f"保持运行设置失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'保持运行设置失败: {str(e)}',
            'data': None
        }), 500