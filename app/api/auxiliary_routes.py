"""
辅助类相关API路由
实现SessionElement、NewFriendElement、LoginWnd等辅助类功能
"""

from flask import Blueprint, jsonify, request
from app.auth import require_api_key
from app.unified_logger import logger
from app.wechat import wechat_manager
from app.utils.wechat_path_detector import get_best_wechat_path, validate_wechat_path
import base64
import os

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
        logger.error(f"[wxautox] 点击会话失败: {str(e)}")
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
        logger.error(f"[wxautox] 接受好友申请失败: {str(e)}")
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
        logger.error(f"[wxautox] 拒绝好友申请失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'拒绝好友申请失败: {str(e)}',
            'data': None
        }), 500


@auxiliary_bp.route('/login/auto', methods=['POST'])
@require_api_key
def auto_login():
    """自动登录微信 (Plus版)"""
    try:
        # 检查wxautox库是否可用（直接尝试导入，不依赖当前实例）
        try:
            from wxautox import LoginWnd
            import pythoncom
            # 如果能成功导入，说明wxautox库可用
        except ImportError:
            return jsonify({
                'code': 3001,
                'message': '自动登录功能需要wxautox库支持',
                'data': None
            }), 400

        # 获取请求参数
        data = request.get_json() or {}
        wxpath = data.get('wxpath')
        timeout = data.get('timeout', 10)

        logger.info(f"[wxautox] 自动登录请求参数: wxpath={wxpath}, timeout={timeout}")

        # 如果没有提供微信路径，尝试自动检测
        if not wxpath:
            wxpath = get_best_wechat_path()
            logger.info(f"[wxautox] 自动检测到微信路径: {wxpath}")
            if not wxpath:
                return jsonify({
                    'code': 1002,
                    'message': '未找到微信安装路径，请手动指定wxpath参数',
                    'data': None
                }), 400

        # 验证微信路径
        logger.info(f"[wxautox] 验证微信路径: {wxpath}")
        if not validate_wechat_path(wxpath):
            logger.error(f"[wxautox] 微信路径验证失败: {wxpath}")
            return jsonify({
                'code': 1002,
                'message': f'无效的微信路径: {wxpath}',
                'data': None
            }), 400

        # wxautox库已在前面检查并导入

        # 初始化COM环境
        try:
            pythoncom.CoInitialize()
        except:
            pass  # 如果已经初始化过，忽略错误

        try:
            # 创建登录窗口
            loginwnd = LoginWnd(wxpath)

            # 执行自动登录
            login_result = loginwnd.login(timeout=timeout)
        finally:
            # 清理COM环境
            try:
                pythoncom.CoUninitialize()
            except:
                pass

        return jsonify({
            'code': 0,
            'message': '自动登录执行完成',
            'data': {
                'wxpath': wxpath,
                'timeout': timeout,
                'login_result': login_result,
                'success': login_result is True
            }
        })

    except Exception as e:
        logger.error(f"[wxautox] 自动登录失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'自动登录失败: {str(e)}',
            'data': None
        }), 500


@auxiliary_bp.route('/login/qrcode', methods=['POST'])
@require_api_key
def get_login_qrcode():
    """获取登录二维码 (Plus版)"""
    try:
        # 检查wxautox库是否可用（直接尝试导入，不依赖当前实例）
        try:
            from wxautox import LoginWnd
            import pythoncom
            # 如果能成功导入，说明wxautox库可用
        except ImportError:
            return jsonify({
                'code': 3001,
                'message': '获取登录二维码功能需要wxautox库支持',
                'data': None
            }), 400

        # 获取请求参数
        data = request.get_json() or {}
        wxpath = data.get('wxpath')

        logger.info(f"[wxautox] 获取二维码请求参数: wxpath={wxpath}")

        # 如果没有提供微信路径，尝试自动检测
        if not wxpath:
            wxpath = get_best_wechat_path()
            logger.info(f"[wxautox] 自动检测到微信路径: {wxpath}")
            if not wxpath:
                return jsonify({
                    'code': 1002,
                    'message': '未找到微信安装路径，请手动指定wxpath参数',
                    'data': None
                }), 400

        # 验证微信路径
        logger.info(f"[wxautox] 验证微信路径: {wxpath}")
        if not validate_wechat_path(wxpath):
            logger.error(f"[wxautox] 微信路径验证失败: {wxpath}")
            return jsonify({
                'code': 1002,
                'message': f'无效的微信路径: {wxpath}',
                'data': None
            }), 400

        # 导入wxautox库
        try:
            from wxautox import LoginWnd
            import pythoncom
        except ImportError:
            return jsonify({
                'code': 3001,
                'message': 'wxautox库未安装或不可用',
                'data': None
            }), 400

        # 初始化COM环境
        try:
            pythoncom.CoInitialize()
        except:
            pass  # 如果已经初始化过，忽略错误

        try:
            # 创建登录窗口
            loginwnd = LoginWnd(wxpath)

            # 获取二维码图片路径
            qrcode_path = loginwnd.get_qrcode()

            if not qrcode_path or not os.path.exists(qrcode_path):
                return jsonify({
                    'code': 3001,
                    'message': '获取二维码失败或二维码文件不存在',
                    'data': None
                }), 500

            # 读取二维码图片并转换为base64
            with open(qrcode_path, 'rb') as f:
                qrcode_data = f.read()

            # 转换为base64编码
            qrcode_base64 = base64.b64encode(qrcode_data).decode('utf-8')

            # 获取文件扩展名以确定MIME类型
            file_ext = os.path.splitext(qrcode_path)[1].lower()
            if file_ext == '.png':
                mime_type = 'image/png'
            elif file_ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            else:
                mime_type = 'image/png'  # 默认为PNG

            # 构建data URL格式的base64字符串
            qrcode_data_url = f"data:{mime_type};base64,{qrcode_base64}"

            return jsonify({
                'code': 0,
                'message': '获取登录二维码成功',
                'data': {
                    'wxpath': wxpath,
                    'qrcode_path': qrcode_path,
                    'qrcode_base64': qrcode_base64,
                    'qrcode_data_url': qrcode_data_url,
                    'mime_type': mime_type
                }
            })
        finally:
            # 清理COM环境
            try:
                pythoncom.CoUninitialize()
            except:
                pass

    except Exception as e:
        logger.error(f"[wxautox] 获取登录二维码失败: {str(e)}")
        return jsonify({
            'code': 3001,
            'message': f'获取登录二维码失败: {str(e)}',
            'data': None
        }), 500