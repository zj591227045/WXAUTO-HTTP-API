"""
wxauto安装脚本
用于在打包环境中安装wxauto库
"""

import os
import sys
import shutil
import logging
import importlib.util
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

def find_wxauto_paths():
    """
    查找所有可能的wxauto路径
    
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
                os.path.join(app_root, "wxauto"),
                os.path.join(app_root, "app", "wxauto"),
            ])
    else:
        # 如果是开发环境
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.info(f"检测到开发环境，应用根目录: {app_root}")
        possible_paths.extend([
            os.path.join(app_root, "wxauto"),
            os.path.join(app_root, "app", "wxauto"),
        ])
    
    # 记录所有可能的路径
    logger.info(f"可能的wxauto路径: {possible_paths}")
    
    # 过滤出存在的路径
    existing_paths = [path for path in possible_paths if os.path.exists(path) and os.path.isdir(path)]
    logger.info(f"存在的wxauto路径: {existing_paths}")
    
    return existing_paths

def install_wxauto():
    """
    安装wxauto库
    
    Returns:
        bool: 是否安装成功
    """
    # 查找所有可能的wxauto路径
    wxauto_paths = find_wxauto_paths()
    
    if not wxauto_paths:
        logger.error("找不到wxauto路径，无法安装wxauto库")
        return False
    
    # 尝试从每个路径安装
    for wxauto_path in wxauto_paths:
        logger.info(f"尝试从路径安装wxauto: {wxauto_path}")
        
        # 检查wxauto路径下是否有wxauto子目录
        wxauto_inner_path = os.path.join(wxauto_path, "wxauto")
        if os.path.exists(wxauto_inner_path) and os.path.isdir(wxauto_inner_path):
            logger.info(f"找到wxauto内部目录: {wxauto_inner_path}")
            
            # 检查是否包含必要的文件
            wxauto_file = os.path.join(wxauto_inner_path, "wxauto.py")
            elements_file = os.path.join(wxauto_inner_path, "elements.py")
            init_file = os.path.join(wxauto_inner_path, "__init__.py")
            
            if os.path.exists(wxauto_file) and os.path.exists(elements_file):
                logger.info(f"找到必要的wxauto文件: {wxauto_file}, {elements_file}")
                
                # 确保wxauto路径在Python路径中
                if wxauto_path not in sys.path:
                    sys.path.insert(0, wxauto_path)
                    logger.info(f"已将wxauto路径添加到Python路径: {wxauto_path}")
                
                # 尝试导入wxauto
                try:
                    # 使用importlib.util.spec_from_file_location动态导入模块
                    spec = importlib.util.spec_from_file_location("wxauto.wxauto", wxauto_file)
                    if spec:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        logger.info(f"成功导入wxauto模块: {module}")
                        return True
                    else:
                        logger.warning(f"无法从文件创建模块规范: {wxauto_file}")
                except Exception as e:
                    logger.error(f"导入wxauto模块失败: {str(e)}")
    
    logger.error("所有路径都无法安装wxauto库")
    return False

def ensure_wxauto_installed():
    """
    确保wxauto库已安装
    
    Returns:
        bool: 是否已安装
    """
    # 首先尝试直接导入
    try:
        import wxauto
        logger.info("wxauto库已安装")
        return True
    except ImportError:
        logger.warning("无法直接导入wxauto库，尝试安装")
        
        # 尝试安装
        return install_wxauto()

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 确保wxauto库已安装
    if ensure_wxauto_installed():
        print("wxauto库已成功安装")
        sys.exit(0)
    else:
        print("wxauto库安装失败")
        sys.exit(1)
