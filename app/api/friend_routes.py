"""
好友管理相关API路由
实现好友相关的所有方法
"""

from flask import Blueprint, jsonify, request
from app.auth import require_api_key
from app.unified_logger import logger
from app.wechat import wechat_manager

friend_bp = Blueprint('friend', __name__)

@friend_bp.route('/get-details', methods=['GET', 'POST'])
@require_api_key
def get_friend_details():
    """获取好友详情信息 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name != 'wxautox':
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持获取好友详情功能',
                'data': None
            }), 400

        # 支持GET和POST两种方法获取参数
        if request.method == 'GET':
            # GET方法：从查询参数获取
            n = request.args.get('n', type=int)
            tag = request.args.get('tag')
            timeout = request.args.get('timeout', 0xFFFFF, type=int)
        else:
            # POST方法：从JSON请求体获取
            data = request.get_json()
            if not data:
                data = {}  # 允许空请求体，使用默认参数
            n = data.get('n', type=int) if data.get('n') is not None else None
            tag = data.get('tag')
            timeout = data.get('timeout', 0xFFFFF)

        # 构建参数
        params = {'timeout': timeout}
        if n is not None:
            params['n'] = n
        if tag:
            params['tag'] = tag

        # 调用GetFriendDetails方法
        friends = wx_instance.GetFriendDetails(**params)

        return jsonify({
            'code': 0,
            'message': '获取好友详情成功',
            'data': {
                'friends': friends if friends else []
            }
        })
    except Exception as e:
        logger.error(f"获取好友详情失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取好友详情失败: {str(e)}',
            'data': None
        }), 500

@friend_bp.route('/get-new-friends', methods=['GET'])
@require_api_key
def get_new_friends():
    """获取新的好友申请列表 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name != 'wxautox':
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持获取新好友申请功能',
                'data': None
            }), 400

        # 获取参数
        acceptable = request.args.get('acceptable', 'true').lower() == 'true'

        # 调用GetNewFriends方法
        new_friends = wx_instance.GetNewFriends(acceptable=acceptable)

        # 格式化新好友申请
        formatted_friends = []
        for friend in new_friends:
            formatted_friend = {
                'name': getattr(friend, 'name', ''),
                'msg': getattr(friend, 'msg', ''),
                'acceptable': getattr(friend, 'acceptable', False)
            }
            formatted_friends.append(formatted_friend)

        return jsonify({
            'code': 0,
            'message': '获取新好友申请成功',
            'data': {
                'new_friends': formatted_friends
            }
        })
    except Exception as e:
        logger.error(f"获取新好友申请失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取新好友申请失败: {str(e)}',
            'data': None
        }), 500

# 为了兼容性，添加别名路由
@friend_bp.route('/get-new-requests', methods=['GET'])
@require_api_key
def get_new_requests_alias():
    """获取新的好友申请列表 (Plus版) - 别名路由"""
    return get_new_friends()

# 添加更多兼容性别名路由
@friend_bp.route('/get-requests', methods=['GET'])
@require_api_key
def get_requests_alias():
    """获取新的好友申请列表 (Plus版) - 兼容性别名路由"""
    return get_new_friends()

@friend_bp.route('/add-new', methods=['POST'])
@require_api_key
def add_new_friend_alias():
    """添加新的好友 (Plus版) - 兼容性路由，支持search_text参数"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    # 兼容性处理：支持search_text参数，映射到keywords
    keywords = data.get('keywords') or data.get('search_text')
    addmsg = data.get('addmsg') or data.get('remark')  # 兼容remark参数
    remark = data.get('remark')
    tags = data.get('tags', [])
    permission = data.get('permission', '朋友圈')
    timeout = data.get('timeout', 5)

    if not keywords:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数：search_text 或 keywords',
            'data': None
        }), 400

    try:
        # 检查当前使用的库
        lib_name = getattr(wx_instance, '_lib_name', 'wxauto')
        if lib_name != 'wxautox':
            return jsonify({
                'code': 3001,
                'message': '当前库版本不支持添加新好友功能',
                'data': None
            }), 400

        # 构建参数
        params = {
            'keywords': keywords,
            'timeout': timeout
        }
        if addmsg:
            params['addmsg'] = addmsg
        if remark:
            params['remark'] = remark
        if tags:
            params['tags'] = tags
        if permission:
            params['permission'] = permission

        # 调用AddNewFriend方法
        result = wx_instance.AddNewFriend(**params)

        return jsonify({
            'code': 0,
            'message': '添加好友请求已发送',
            'data': {
                'search_text': keywords,  # 返回兼容性字段名
                'keywords': keywords,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"添加新好友失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'添加新好友失败: {str(e)}',
            'data': None
        }), 500

@friend_bp.route('/add-new-friend', methods=['POST'])
@require_api_key
def add_new_friend():
    """添加新的好友 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    keywords = data.get('keywords')
    addmsg = data.get('addmsg')
    remark = data.get('remark')
    tags = data.get('tags', [])
    permission = data.get('permission', '朋友圈')
    timeout = data.get('timeout', 5)

    if not keywords:
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
                'message': '当前库版本不支持添加新好友功能',
                'data': None
            }), 400

        # 构建参数
        params = {
            'keywords': keywords,
            'timeout': timeout
        }
        if addmsg:
            params['addmsg'] = addmsg
        if remark:
            params['remark'] = remark
        if tags:
            params['tags'] = tags
        if permission:
            params['permission'] = permission

        # 调用AddNewFriend方法
        result = wx_instance.AddNewFriend(**params)

        return jsonify({
            'code': 0,
            'message': '添加好友请求已发送',
            'data': {
                'keywords': keywords,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"添加新好友失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'添加新好友失败: {str(e)}',
            'data': None
        }), 500

@friend_bp.route('/manage', methods=['POST'])
@require_api_key
def manage_friend():
    """修改好友备注名或标签 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    remark = data.get('remark')
    tags = data.get('tags')

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
                'message': '当前库版本不支持好友管理功能',
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

        # 构建参数
        params = {}
        if remark:
            params['remark'] = remark
        if tags:
            params['tags'] = tags

        # 调用ManageFriend方法
        result = chat_wnd.ManageFriend(**params)

        return jsonify({
            'code': 0,
            'message': '好友管理成功',
            'data': {
                'friend': who,
                'params': params,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"好友管理失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'好友管理失败: {str(e)}',
            'data': None
        }), 500

@friend_bp.route('/add-from-group', methods=['POST'])
@require_api_key
def add_friend_from_group():
    """从群聊中添加好友 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')  # 群名
    index = data.get('index')  # 群成员索引
    addmsg = data.get('addmsg')
    remark = data.get('remark')
    tags = data.get('tags', [])
    permission = data.get('permission', '仅聊天')
    exact = data.get('exact', False)

    if not who or index is None:
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
                'message': '当前库版本不支持从群聊添加好友功能',
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

        # 构建参数
        params = {
            'index': index,
            'permission': permission,
            'exact': exact
        }
        if addmsg:
            params['addmsg'] = addmsg
        if remark:
            params['remark'] = remark
        if tags:
            params['tags'] = tags

        # 调用AddFriendFromGroup方法
        result = chat_wnd.AddFriendFromGroup(**params)

        return jsonify({
            'code': 0,
            'message': '从群聊添加好友成功',
            'data': {
                'group': who,
                'index': index,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"从群聊添加好友失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'从群聊添加好友失败: {str(e)}',
            'data': None
        }), 500