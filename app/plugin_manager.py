"""
插件管理模块
用于管理wxauto和wxautox库的安装和卸载
"""

import sys
import subprocess
import logging
import importlib
import config_manager

# 配置日志
logger = logging.getLogger(__name__)

def check_wxauto_status():
    """
    检查wxauto库的安装状态

    Returns:
        bool: 是否已安装
    """
    try:
        # 尝试导入pip安装的wxauto包
        import wxauto
        logger.info("成功导入wxauto库")
        return True
    except ImportError as e:
        logger.warning(f"无法导入wxauto库: {str(e)}")
        return False

def check_wxautox_status():
    """
    检查wxautox库的安装状态

    Returns:
        bool: 是否已安装
    """
    try:
        # 使用统一的库检测器
        from app.wechat_lib_detector import detector

        available, details = detector.detect_wxautox()
        if available:
            logger.info(f"wxautox库检测成功: {details}")
            return True
        else:
            logger.warning(f"wxautox库检测失败: {details}")
            return False
    except Exception as e:
        logger.warning(f"检查wxautox库时出错: {str(e)}")
        return False

def install_wxautox():
    """
    安装wxautox库（使用pip）

    Returns:
        tuple: (成功状态, 消息)
    """
    logger.info("开始安装wxautox库")

    try:
        # 使用pip安装wxautox包
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "wxautox"],
            capture_output=True,
            text=True,
            check=True
        )

        # 检查安装结果
        if result.returncode == 0:
            logger.info("wxautox库安装成功")

            # 尝试导入验证
            try:
                import wxautox
                importlib.reload(wxautox)  # 重新加载模块，确保使用最新版本
                logger.info("wxautox库导入验证成功")

                # 更新配置文件
                update_config_for_wxautox()

                return True, "wxautox库安装成功"
            except ImportError as e:
                logger.error(f"wxautox库安装后导入失败: {str(e)}")
                return False, f"wxautox库安装后导入失败: {str(e)}"
        else:
            logger.error(f"wxautox库安装失败: {result.stderr}")
            return False, f"wxautox库安装失败: {result.stderr}"
    except subprocess.CalledProcessError as e:
        logger.error(f"wxautox库安装过程出错: {e.stderr}")
        return False, f"wxautox库安装过程出错: {e.stderr}"
    except Exception as e:
        logger.error(f"wxautox库安装过程出现未知错误: {str(e)}")
        return False, f"wxautox库安装过程出现未知错误: {str(e)}"

def update_config_for_wxautox():
    """
    更新配置文件，设置使用wxautox库
    """
    try:
        # 加载当前配置
        config = config_manager.load_app_config()

        # 更新库配置
        config['wechat_lib'] = 'wxautox'

        # 保存配置
        config_manager.save_app_config(config)

        logger.info("已更新配置文件，设置使用wxautox库")
    except Exception as e:
        logger.error(f"更新配置文件失败: {str(e)}")

def get_plugins_status():
    """
    获取插件状态

    Returns:
        dict: 插件状态信息
    """
    wxauto_status = check_wxauto_status()
    wxautox_status = check_wxautox_status()

    return {
        'wxauto': {
            'installed': wxauto_status
        },
        'wxautox': {
            'installed': wxautox_status,
            'version': get_wxautox_version() if wxautox_status else None
        }
    }

def get_wxautox_version():
    """
    获取wxautox版本号

    Returns:
        str: 版本号，如果未安装则返回None
    """
    try:
        import wxautox
        version = getattr(wxautox, 'VERSION', '未知版本')
        logger.info(f"获取到wxautox版本: {version}")
        return version
    except ImportError:
        logger.warning("无法导入wxautox，无法获取版本号")
        return None
