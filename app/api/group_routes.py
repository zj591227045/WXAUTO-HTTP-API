"""
群组管理相关API路由
实现群组相关的所有方法
"""

from flask import Blueprint, jsonify, request
from app.auth import require_api_key
from app.logs import logger
from app.wechat import wechat_manager

group_bp = Blueprint('group', __name__)

@group_bp.route('/add-members', methods=['POST'])
@require_api_key
def add_group_members():
    """添加群成员 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    group = data.get('group')
    members = data.get('members', [])
    reason = data.get('reason')

    if not group or not members:
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
                'message': '当前库版本不支持添加群成员功能',
                'data': None
            }), 400

        # 调用AddGroupMembers方法
        if reason:
            result = wx_instance.AddGroupMembers(group=group, members=members, reason=reason)
        else:
            result = wx_instance.AddGroupMembers(group=group, members=members)

        return jsonify({
            'code': 0,
            'message': '添加群成员成功',
            'data': {
                'group': group,
                'members': members,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"添加群成员失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'添加群成员失败: {str(e)}',
            'data': None
        }), 500

@group_bp.route('/get-members', methods=['GET'])
@require_api_key
def get_group_members():
    """获取群成员列表 (Plus版)"""
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
                'message': '当前库版本不支持获取群成员功能',
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

        # 获取群成员
        members = chat_wnd.GetGroupMembers()

        return jsonify({
            'code': 0,
            'message': '获取群成员成功',
            'data': {
                'group': who,
                'members': members
            }
        })
    except Exception as e:
        logger.error(f"获取群成员失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取群成员失败: {str(e)}',
            'data': None
        }), 500

@group_bp.route('/remove-members', methods=['POST'])
@require_api_key
def remove_group_members():
    """移除群成员 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    group = data.get('group')
    members = data.get('members', [])

    if not group or not members:
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
                'message': '当前库版本不支持移除群成员功能',
                'data': None
            }), 400

        # 调用RemoveGroupMembers方法
        result = wx_instance.RemoveGroupMembers(group=group, members=members)

        return jsonify({
            'code': 0,
            'message': '移除群成员成功',
            'data': {
                'group': group,
                'members': members,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"移除群成员失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'移除群成员失败: {str(e)}',
            'data': None
        }), 500

@group_bp.route('/manage', methods=['POST'])
@require_api_key
def manage_group():
    """管理群聊 (Plus版)"""
    wx_instance = wechat_manager.get_instance()
    if not wx_instance:
        return jsonify({
            'code': 2001,
            'message': '微信未初始化',
            'data': None
        }), 400

    data = request.get_json()
    who = data.get('who')
    name = data.get('name')
    remark = data.get('remark')
    myname = data.get('myname')
    notice = data.get('notice')
    quit_group = data.get('quit', False)

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
                'message': '当前库版本不支持群聊管理功能',
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
        if name:
            params['name'] = name
        if remark:
            params['remark'] = remark
        if myname:
            params['myname'] = myname
        if notice:
            params['notice'] = notice
        if quit_group:
            params['quit'] = True

        # 调用ManageGroup方法
        result = chat_wnd.ManageGroup(**params)

        return jsonify({
            'code': 0,
            'message': '群聊管理成功',
            'data': {
                'group': who,
                'params': params,
                'result': str(result) if result else None
            }
        })
    except Exception as e:
        logger.error(f"群聊管理失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'群聊管理失败: {str(e)}',
            'data': None
        }), 500

@group_bp.route('/get-recent-groups', methods=['GET'])
@require_api_key
def get_recent_groups():
    """获取最近群聊名称列表 (Plus版)"""
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
                'message': '当前库版本不支持获取最近群聊功能',
                'data': None
            }), 400

        # 调用GetAllRecentGroups方法
        groups = wx_instance.GetAllRecentGroups()

        return jsonify({
            'code': 0,
            'message': '获取最近群聊成功',
            'data': {
                'groups': groups if groups else []
            }
        })
    except Exception as e:
        logger.error(f"获取最近群聊失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取最近群聊失败: {str(e)}',
            'data': None
        }), 500

@group_bp.route('/get-contact-groups', methods=['GET'])
@require_api_key
def get_contact_groups():
    """获取通讯录群聊列表 (Plus版)"""
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
                'message': '当前库版本不支持获取通讯录群聊功能',
                'data': None
            }), 400

        # 获取参数
        speed = request.args.get('speed', 1, type=int)
        interval = request.args.get('interval', 0.1, type=float)

        # 调用GetContactGroups方法
        groups = wx_instance.GetContactGroups(speed=speed, interval=interval)

        return jsonify({
            'code': 0,
            'message': '获取通讯录群聊成功',
            'data': {
                'groups': groups if groups else []
            }
        })
    except Exception as e:
        logger.error(f"获取通讯录群聊失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取通讯录群聊失败: {str(e)}',
            'data': None
        }), 500