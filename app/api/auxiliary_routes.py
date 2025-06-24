"""
辅助类相关API路由
实现SessionElement、NewFriendElement、LoginWnd等辅助类功能
"""

from flask import Blueprint, jsonify, request
from app.auth import require_api_key
from app.logs import logger
from app.wechat import wechat_manager

auxiliary_bp = Blueprint('auxiliary', __name__)

@auxiliary_bp.route('/session/click', methods=['POST'])
@require_api_key
def click_session():
    """点击会话元素"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    session_name = data.get('session_name')

    if not session_name:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数',
            'data': None
        }), 400

    try:
        # 获取会话列表
        sessions = wx_instance.GetSession()
        target_session = None

        for session in sessions:
            if getattr(session, 'name', '') == session_name:
                target_session = session
                break

        if not target_session:
            return jsonify({
                'code': 3001,
                'message': f'未找到会话: {session_name}',
                'data': None
            }), 404

        # 点击会话
        target_session.click()

        return jsonify({
            'code': 0,
            'message': '点击会话成功',
            'data': {
                'session_name': session_name
            }
        })
    except Exception as e:
        logger.error(f"点击会话失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'点击会话失败: {str(e)}',
            'data': None
        }), 500

@auxiliary_bp.route('/new-friend/accept', methods=['POST'])
@require_api_key
def accept_new_friend():
    """接受新好友申请 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    friend_name = data.get('friend_name')
    remark = data.get('remark')
    tags = data.get('tags', [])

    if not friend_name:
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
                'message': '当前库版本不支持新好友申请功能',
                'data': None
            }), 400

        # 获取新好友申请列表
        new_friends = wx_instance.GetNewFriends()
        target_friend = None

        for friend in new_friends:
            if getattr(friend, 'name', '') == friend_name:
                target_friend = friend
                break

        if not target_friend:
            return jsonify({
                'code': 3001,
                'message': f'未找到好友申请: {friend_name}',
                'data': None
            }), 404

        # 构建参数
        params = {}
        if remark:
            params['remark'] = remark
        if tags:
            params['tags'] = tags

        # 接受好友申请
        result = target_friend.accept(**params)

        return jsonify({
            'code': 0,
            'message': '接受好友申请成功',
            'data': {
                'friend_name': friend_name,
                'remark': remark,
                'tags': tags,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"接受好友申请失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'接受好友申请失败: {str(e)}',
            'data': None
        }), 500

@auxiliary_bp.route('/new-friend/reject', methods=['POST'])
@require_api_key
def reject_new_friend():
    """拒绝新好友申请 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    friend_name = data.get('friend_name')

    if not friend_name:
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
                'message': '当前库版本不支持新好友申请功能',
                'data': None
            }), 400

        # 获取新好友申请列表
        new_friends = wx_instance.GetNewFriends()
        target_friend = None

        for friend in new_friends:
            if getattr(friend, 'name', '') == friend_name:
                target_friend = friend
                break

        if not target_friend:
            return jsonify({
                'code': 3001,
                'message': f'未找到好友申请: {friend_name}',
                'data': None
            }), 404

        # 拒绝好友申请
        result = target_friend.reject()

        return jsonify({
            'code': 0,
            'message': '拒绝好友申请成功',
            'data': {
                'friend_name': friend_name,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"拒绝好友申请失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'拒绝好友申请失败: {str(e)}',
            'data': None
        }), 500