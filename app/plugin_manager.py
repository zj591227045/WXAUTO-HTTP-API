"""
插件管理模块
用于管理wxauto和wxautox库的安装和卸载
"""

import os
import sys
import subprocess
import tempfile
import shutil
import logging
import importlib
from pathlib import Path
import config_manager

# 配置日志
logger = logging.getLogger(__name__)

# 导入动态包管理器
try:
    from dynamic_package_manager import get_package_manager
    package_manager = get_package_manager()
    logger.info("成功导入动态包管理器")
except ImportError as e:
    logger.warning(f"导入动态包管理器失败: {str(e)}")
    package_manager = None

def check_wxauto_status():
    """
    检查wxauto库的安装状态

    Returns:
        bool: 是否已安装
    """
    try:
        # 确保本地wxauto文件夹在Python路径中
        wxauto_path = os.path.join(os.getcwd(), "wxauto")
        if wxauto_path not in sys.path:
            sys.path.insert(0, wxauto_path)

        # 尝试导入
        import wxauto
        logger.info(f"成功从本地文件夹导入wxauto: {wxauto_path}")
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
    # 首先尝试使用动态包管理器检查
    if package_manager:
        #logger.info("使用动态包管理器检查wxautox状态")
        is_installed = package_manager.is_package_installed("wxautox")
        if is_installed:
            #logger.info("动态包管理器报告wxautox已安装")
            return True

    # 如果动态包管理器不可用或报告未安装，尝试直接导入
    try:
        import wxautox
        logger.info("wxautox库已安装")
        return True
    except ImportError:
        logger.warning("wxautox库未安装")
        return False

def install_wxautox(wheel_file_path):
    """
    安装wxautox库

    Args:
        wheel_file_path (str): wheel文件路径

    Returns:
        tuple: (成功状态, 消息)
    """
    logger.info(f"开始安装wxautox: {wheel_file_path}")

    # 验证文件是否存在
    if not os.path.exists(wheel_file_path):
        return False, f"文件不存在: {wheel_file_path}"

    # 验证文件是否是wheel文件
    if not wheel_file_path.endswith('.whl'):
        return False, "文件不是有效的wheel文件"

    # 验证文件名是否包含wxautox
    if 'wxautox-' not in os.path.basename(wheel_file_path):
        return False, "文件不是wxautox wheel文件"

    # 优先使用动态包管理器安装
    if package_manager:
        logger.info("使用动态包管理器安装wxautox")
        try:
            module = package_manager.install_and_import(wheel_file_path, "wxautox")
            if module:
                #logger.info("动态包管理器成功安装并导入wxautox")

                # 更新配置文件
                update_config_for_wxautox()

                return True, "wxautox库安装成功"
            else:
                logger.error("动态包管理器安装wxautox失败")
                return False, "动态包管理器安装wxautox失败"
        except Exception as e:
            logger.error(f"动态包管理器安装wxautox出错: {str(e)}")
            # 如果动态包管理器失败，继续尝试传统方法

    # 如果动态包管理器不可用或失败，使用传统方法
    try:
        # 使用pip安装wheel文件
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", wheel_file_path],
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
            'installed': wxauto_status,
            'path': os.path.join(os.getcwd(), "wxauto") if wxauto_status else None
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
    # 首先尝试使用动态包管理器
    if package_manager:
        logger.info("使用动态包管理器获取wxautox版本")
        module = package_manager.import_package("wxautox")
        if module:
            version = getattr(module, 'VERSION', '未知版本')
            logger.info(f"动态包管理器获取到wxautox版本: {version}")
            return version

    # 如果动态包管理器不可用或失败，尝试直接导入
    try:
        import wxautox
        version = getattr(wxautox, 'VERSION', '未知版本')
        logger.info(f"直接导入获取到wxautox版本: {version}")
        return version
    except ImportError:
        logger.warning("无法导入wxautox，无法获取版本号")
        return None
