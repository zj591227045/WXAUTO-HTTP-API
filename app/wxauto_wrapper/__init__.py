"""
wxauto包装器
提供对wxauto库的统一访问接口，无论是在开发环境还是打包环境中
"""

import os
import sys
import logging
import importlib.util
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 全局变量，用于存储已导入的wxauto模块
_wxauto_module = None

def _find_module_path(module_name, possible_paths):
    """
    在可能的路径中查找模块
    
    Args:
        module_name (str): 模块名称
        possible_paths (list): 可能的路径列表
        
    Returns:
        str: 模块路径，如果找不到则返回None
    """
    for path in possible_paths:
        if not os.path.exists(path):
            continue
            
        # 检查是否是目录
        if os.path.isdir(path):
            # 检查是否包含__init__.py文件
            init_file = os.path.join(path, "__init__.py")
            if os.path.exists(init_file):
                return path
                
            # 检查是否包含模块名称的子目录
            subdir = os.path.join(path, module_name)
            if os.path.exists(subdir) and os.path.isdir(subdir):
                # 检查子目录是否包含__init__.py文件
                sub_init_file = os.path.join(subdir, "__init__.py")
                if os.path.exists(sub_init_file):
                    return subdir
        
        # 检查是否是.py文件
        py_file = f"{path}.py"
        if os.path.exists(py_file):
            return py_file
    
    return None

def _get_possible_paths():
    """
    获取可能的wxauto路径
    
    Returns:
        list: 可能的wxauto路径列表
    """
    possible_paths = []
    
    # 获取应用根目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的环境
        app_root = os.path.dirname(sys.executable)
        logger.info(f"检测到打包环境，应用根目录: {app_root}")
        
        # 在打包环境中，确保_MEIPASS目录也在Python路径中
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            logger.info(f"PyInstaller _MEIPASS目录: {meipass}")
            possible_paths.extend([
                os.path.join(meipass, "wxauto"),
                os.path.join(meipass, "app", "wxauto"),
                os.path.join(meipass, "site-packages", "wxauto"),
                os.path.join(app_root, "wxauto"),
                os.path.join(app_root, "app", "wxauto"),
            ])
    else:
        # 如果是开发环境
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logger.info(f"检测到开发环境，应用根目录: {app_root}")
        possible_paths.extend([
            os.path.join(app_root, "wxauto"),
            os.path.join(app_root, "app", "wxauto"),
        ])
    
    # 添加Python路径中的所有目录
    for path in sys.path:
        possible_paths.append(os.path.join(path, "wxauto"))
    
    # 记录所有可能的路径
    logger.info(f"可能的wxauto路径: {possible_paths}")
    
    return possible_paths

def _import_module(module_path, module_name):
    """
    从指定路径导入模块
    
    Args:
        module_path (str): 模块路径
        module_name (str): 模块名称
        
    Returns:
        module: 导入的模块，如果导入失败则返回None
    """
    try:
        # 如果是目录，则导入整个包
        if os.path.isdir(module_path):
            # 确保目录在Python路径中
            if module_path not in sys.path:
                sys.path.insert(0, os.path.dirname(module_path))
                logger.info(f"已将目录添加到Python路径: {os.path.dirname(module_path)}")
            
            # 导入模块
            spec = importlib.util.find_spec(module_name)
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.info(f"成功导入模块: {module_name}")
                return module
        
        # 如果是.py文件，则直接导入
        elif module_path.endswith('.py'):
            # 确保目录在Python路径中
            dir_path = os.path.dirname(module_path)
            if dir_path not in sys.path:
                sys.path.insert(0, dir_path)
                logger.info(f"已将目录添加到Python路径: {dir_path}")
            
            # 导入模块
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.info(f"成功从文件导入模块: {module_path}")
                return module
    except Exception as e:
        logger.error(f"导入模块失败: {str(e)}")
    
    return None

def get_wxauto():
    """
    获取wxauto模块
    
    Returns:
        module: wxauto模块，如果导入失败则返回None
    """
    global _wxauto_module
    
    # 如果已经导入过，则直接返回
    if _wxauto_module:
        return _wxauto_module
    
    # 获取可能的wxauto路径
    possible_paths = _get_possible_paths()
    
    # 查找wxauto模块路径
    module_path = _find_module_path("wxauto", possible_paths)
    if not module_path:
        logger.error("找不到wxauto模块路径")
        return None
    
    # 导入wxauto模块
    _wxauto_module = _import_module(module_path, "wxauto")
    
    # 如果导入失败，尝试直接导入
    if not _wxauto_module:
        try:
            import wxauto
            _wxauto_module = wxauto
            logger.info("成功直接导入wxauto模块")
        except ImportError as e:
            logger.error(f"直接导入wxauto模块失败: {str(e)}")
    
    return _wxauto_module

# 导出所有wxauto模块的属性
wxauto = get_wxauto()
if wxauto:
    # 导出所有wxauto模块的属性
    for attr_name in dir(wxauto):
        if not attr_name.startswith('_'):
            globals()[attr_name] = getattr(wxauto, attr_name)
else:
    logger.error("无法导入wxauto模块，功能将不可用")
