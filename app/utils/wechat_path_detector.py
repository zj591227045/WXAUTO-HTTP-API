"""
微信路径检测工具
用于检测微信安装路径
"""

import os
import winreg
from typing import Optional, List
from app.unified_logger import logger


def get_wechat_install_paths() -> List[str]:
    """
    获取微信可能的安装路径列表
    
    Returns:
        List[str]: 微信可能的安装路径列表
    """
    paths = []
    
    # 1. 从注册表获取微信安装路径
    registry_path = get_wechat_path_from_registry()
    if registry_path:
        paths.append(registry_path)
    
    # 2. 常见的微信安装路径
    common_paths = [
        r"C:\Program Files\Tencent\WeChat\WeChat.exe",
        r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
        r"D:\Program Files\Tencent\WeChat\WeChat.exe",
        r"D:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
        r"E:\Program Files\Tencent\WeChat\WeChat.exe",
        r"E:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
        # 用户自定义安装路径
        os.path.expanduser(r"~\AppData\Local\Programs\Tencent\WeChat\WeChat.exe"),
        os.path.expanduser(r"~\Documents\WeChat Files\WeChat.exe"),
    ]
    
    # 添加常见路径到列表
    for path in common_paths:
        if path not in paths:
            paths.append(path)
    
    # 3. 从环境变量PATH中查找
    path_env_paths = find_wechat_in_path()
    for path in path_env_paths:
        if path not in paths:
            paths.append(path)
    
    return paths


def get_wechat_path_from_registry() -> Optional[str]:
    """
    从Windows注册表获取微信安装路径
    
    Returns:
        Optional[str]: 微信安装路径，如果未找到则返回None
    """
    try:
        # 尝试从不同的注册表位置获取微信路径
        registry_keys = [
            # 微信的卸载信息
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WeChat"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\WeChat"),
            # 微信的应用路径
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WeChat.exe"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\WeChat.exe"),
            # 腾讯相关注册表项
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tencent\WeChat"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Tencent\WeChat"),
        ]
        
        for hkey, subkey in registry_keys:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    # 尝试获取不同的值
                    value_names = ["InstallLocation", "DisplayIcon", "UninstallString", "", "Path"]
                    
                    for value_name in value_names:
                        try:
                            value, _ = winreg.QueryValueEx(key, value_name)
                            if value and isinstance(value, str):
                                # 处理路径
                                if value.lower().endswith('.exe'):
                                    if os.path.exists(value):
                                        logger.info(f"从注册表找到微信路径: {value}")
                                        return value
                                else:
                                    # 如果是目录，尝试添加WeChat.exe
                                    wechat_exe = os.path.join(value, "WeChat.exe")
                                    if os.path.exists(wechat_exe):
                                        logger.info(f"从注册表找到微信路径: {wechat_exe}")
                                        return wechat_exe
                        except FileNotFoundError:
                            continue
                        except Exception as e:
                            logger.debug(f"读取注册表值 {value_name} 失败: {str(e)}")
                            continue
                            
            except FileNotFoundError:
                continue
            except Exception as e:
                logger.debug(f"打开注册表项 {subkey} 失败: {str(e)}")
                continue
                
    except Exception as e:
        logger.warning(f"从注册表获取微信路径时出错: {str(e)}")
    
    return None


def find_wechat_in_path() -> List[str]:
    """
    在系统PATH环境变量中查找微信
    
    Returns:
        List[str]: 找到的微信路径列表
    """
    paths = []
    
    try:
        # 获取PATH环境变量
        path_env = os.environ.get('PATH', '')
        path_dirs = path_env.split(os.pathsep)
        
        for path_dir in path_dirs:
            if path_dir and os.path.exists(path_dir):
                wechat_exe = os.path.join(path_dir, "WeChat.exe")
                if os.path.exists(wechat_exe):
                    paths.append(wechat_exe)
                    logger.info(f"在PATH中找到微信: {wechat_exe}")
                    
    except Exception as e:
        logger.warning(f"在PATH中查找微信时出错: {str(e)}")
    
    return paths


def get_best_wechat_path() -> Optional[str]:
    """
    获取最佳的微信安装路径
    
    Returns:
        Optional[str]: 最佳的微信安装路径，如果未找到则返回None
    """
    paths = get_wechat_install_paths()
    
    # 验证路径并返回第一个有效的路径
    for path in paths:
        if path and os.path.exists(path) and os.path.isfile(path):
            logger.info(f"找到有效的微信路径: {path}")
            return path
    
    logger.warning("未找到有效的微信安装路径")
    return None


def validate_wechat_path(path: str) -> bool:
    """
    验证微信路径是否有效

    Args:
        path (str): 微信路径

    Returns:
        bool: 路径是否有效
    """
    if not path:
        logger.debug("微信路径为空")
        return False

    try:
        logger.debug(f"验证微信路径: {path}")

        # 检查文件是否存在
        if not os.path.exists(path):
            logger.debug(f"文件不存在: {path}")
            return False

        # 检查是否是文件
        if not os.path.isfile(path):
            logger.debug(f"不是文件: {path}")
            return False

        # 检查文件名是否正确
        if not path.lower().endswith('wechat.exe'):
            logger.debug(f"文件名不正确: {path}")
            return False

        # 检查文件大小（微信exe文件通常不会太小）
        file_size = os.path.getsize(path)
        logger.debug(f"微信文件大小: {file_size} bytes")
        if file_size < 100 * 1024:  # 小于100KB可能不是真正的微信程序
            logger.debug(f"文件太小，可能不是微信程序: {file_size} bytes")
            return False

        logger.debug(f"微信路径验证成功: {path}")
        return True

    except Exception as e:
        logger.warning(f"验证微信路径时出错: {str(e)}")
        return False
