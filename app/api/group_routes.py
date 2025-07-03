"""
群组管理相关API路由
实现群组相关的所有方法
"""

from flask import Blueprint, jsonify, request
from app.auth import require_api_key
from app.unified_logger import logger
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
    # 支持两种参数格式：group 或 group_name
    group = data.get('group') or data.get('group_name')
    members = data.get('members', [])
    reason = data.get('reason')

    # 如果members是字符串，转换为列表
    if isinstance(members, str):
        members = [members]

    if not group or not members:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数：group/group_name 和 members',
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

@group_bp.route('/get-members', methods=['GET', 'POST'])
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

    # 支持GET和POST两种方法
    if request.method == 'GET':
        # GET方法：从查询参数获取
        who = request.args.get('who')
    else:
        # POST方法：从JSON请求体获取
        data = request.get_json()
        if not data:
            return jsonify({
                'code': 1002,
                'message': '请求体不能为空',
                'data': None
            }), 400
        # 支持group_name或who参数
        who = data.get('group_name') or data.get('who')

    if not who:
        return jsonify({
            'code': 1002,
            'message': '缺少必要参数：who 或 group_name',
            'data': None
        }), 400

    try:
        # 检查当前使用的库 - 使用更可靠的检测方法
        lib_name = None

        # 方法1: 检查适配器的库名称
        if hasattr(wechat_manager, '_adapter') and hasattr(wechat_manager._adapter, 'get_lib_name'):
            try:
                lib_name = wechat_manager._adapter.get_lib_name()
            except:
                pass

        # 方法2: 检查实例的_lib_name属性
        if not lib_name:
            lib_name = getattr(wx_instance, '_lib_name', None)

        # 方法3: 通过实例类型判断
        if not lib_name:
            instance_type = str(type(wx_instance))
            if 'wxautox' in instance_type:
                lib_name = 'wxautox'
            elif 'wxauto' in instance_type:
                lib_name = 'wxauto'

        # 方法4: 检查是否有GetGroupMembers方法（最终检查）
        if not hasattr(wx_instance, 'GetGroupMembers'):
            return jsonify({
                'code': 3001,
                'message': '当前微信实例不支持获取群成员功能',
                'data': None
            }), 400

        logger.info(f"检测到的库名称: {lib_name}")

        # 使用正确的方法获取群成员
        try:
            # 先切换到群聊页面
            logger.info(f"切换到群聊页面: {who}")
            result = wx_instance.ChatWith(who)
            logger.info(f"切换结果: {result}")

            # 等待页面加载
            import time
            time.sleep(0.5)

            # 直接调用GetGroupMembers
            members = wx_instance.GetGroupMembers()
            logger.info(f"获取群成员: {len(members) if members else 0}个")

            # 检查结果
            if members is None:
                return jsonify({
                    'code': 3001,
                    'message': f'无法获取群 {who} 的成员列表，请确保群聊存在且可访问',
                    'data': None
                }), 404

        except Exception as e:
            logger.error(f"获取群成员失败: {str(e)}")
            return jsonify({
                'code': 3001,
                'message': f'获取群成员失败: {str(e)}',
                'data': None
            }), 500

        return jsonify({
            'code': 0,
            'message': '获取群成员成功',
            'data': {
                'group': who,
                'members': members
            }
        })
    except Exception as e:
        logger.error("wxautox", f"获取群成员失败: {str(e)}")
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
        logger.error("wxautox", f"移除群成员失败: {str(e)}")
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
        logger.error("wxautox", f"群聊管理失败: {str(e)}")
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
        logger.error("wxautox", f"获取最近群聊失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取最近群聊失败: {str(e)}',
            'data': None
        }), 500

# 为了兼容性，添加简化的路由别名
@group_bp.route('/get-recent', methods=['GET'])
@require_api_key
def get_recent_groups_alias():
    """获取最近群聊名称列表 (Plus版) - 别名路由"""
    return get_recent_groups()

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
        logger.error("wxautox", f"获取通讯录群聊失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取通讯录群聊失败: {str(e)}',
            'data': None
        }), 500