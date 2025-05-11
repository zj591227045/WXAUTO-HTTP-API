"""
修复路径模块
用于在打包环境中修复路径问题
"""

import os
import sys
import logging

# 配置日志
logger = logging.getLogger(__name__)

def fix_paths():
    """
    修复路径问题
    在打包环境中，确保所有必要的路径都被正确设置
    """
    # 记录当前环境信息
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"当前工作目录: {os.getcwd()}")
    logger.info(f"Python路径: {sys.path}")
    logger.info(f"是否在PyInstaller环境中运行: {getattr(sys, 'frozen', False)}")
    
    # 获取应用根目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的环境
        app_root = os.path.dirname(sys.executable)
        logger.info(f"检测到打包环境，应用根目录: {app_root}")
        
        # 在打包环境中，确保_MEIPASS目录也在Python路径中
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass and meipass not in sys.path:
            sys.path.insert(0, meipass)
            logger.info(f"已将_MEIPASS目录添加到Python路径: {meipass}")
    else:
        # 如果是开发环境
        app_root = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"检测到开发环境，应用根目录: {app_root}")
    
    # 确保应用根目录在Python路径中
    if app_root not in sys.path:
        sys.path.insert(0, app_root)
        logger.info(f"已将应用根目录添加到Python路径: {app_root}")
    
    # 确保wxauto目录在Python路径中
    wxauto_path = os.path.join(app_root, "wxauto")
    if os.path.exists(wxauto_path) and wxauto_path not in sys.path:
        sys.path.insert(0, wxauto_path)
        logger.info(f"已将wxauto目录添加到Python路径: {wxauto_path}")
    
    # 设置工作目录为应用根目录
    os.chdir(app_root)
    logger.info(f"已将工作目录设置为应用根目录: {app_root}")
    
    # 再次记录环境信息，确认修改已生效
    logger.info(f"修复后的工作目录: {os.getcwd()}")
    logger.info(f"修复后的Python路径: {sys.path}")
    
    return app_root

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 修复路径
    fix_paths()
