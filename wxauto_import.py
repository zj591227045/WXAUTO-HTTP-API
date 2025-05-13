"""
wxauto导入辅助模块
用于确保wxauto库能够被正确导入
"""

import os
import sys
import importlib
import logging

# 配置日志
logger = logging.getLogger(__name__)

def ensure_wxauto_importable():
    """
    确保wxauto库能够被正确导入
    
    Returns:
        bool: 是否成功导入wxauto库
    """
    # 记录当前Python路径
    logger.info(f"当前Python路径: {sys.path}")
    
    # 获取应用根目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的环境
        app_root = os.path.dirname(sys.executable)
        logger.info(f"检测到打包环境，应用根目录: {app_root}")
        
        # 在打包环境中，确保_MEIPASS目录也在Python路径中
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            logger.info(f"PyInstaller _MEIPASS目录: {meipass}")
            if meipass not in sys.path:
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
    
    # 尝试多种可能的wxauto路径
    possible_paths = [
        os.path.join(app_root, "wxauto"),  # 标准路径
        os.path.join(app_root, "app", "wxauto"),  # 可能的子目录
    ]
    
    # 如果是打包环境，添加更多可能的路径
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            possible_paths.extend([
                os.path.join(meipass, "wxauto"),  # PyInstaller临时目录中的wxauto
                os.path.join(meipass, "app", "wxauto"),  # PyInstaller临时目录中的app/wxauto
            ])
    
    # 记录所有可能的路径
    logger.info(f"可能的wxauto路径: {possible_paths}")
    
    # 尝试从每个路径导入
    for wxauto_path in possible_paths:
        if os.path.exists(wxauto_path) and os.path.isdir(wxauto_path):
            logger.info(f"找到wxauto路径: {wxauto_path}")
            
            # 检查wxauto路径下是否有wxauto子目录
            wxauto_inner_path = os.path.join(wxauto_path, "wxauto")
            if os.path.exists(wxauto_inner_path) and os.path.isdir(wxauto_inner_path):
                logger.info(f"找到wxauto内部目录: {wxauto_inner_path}")
                
                # 将wxauto/wxauto目录添加到路径
                if wxauto_inner_path not in sys.path:
                    sys.path.insert(0, wxauto_inner_path)
                    logger.info(f"已将wxauto/wxauto目录添加到Python路径: {wxauto_inner_path}")
            
            # 将wxauto目录添加到路径
            if wxauto_path not in sys.path:
                sys.path.insert(0, wxauto_path)
                logger.info(f"已将wxauto目录添加到Python路径: {wxauto_path}")
            
            # 尝试导入
            try:
                import wxauto
                logger.info(f"成功从路径导入wxauto: {wxauto_path}")
                return True
            except ImportError as e:
                logger.warning(f"从路径 {wxauto_path} 导入wxauto失败: {str(e)}")
                # 继续尝试下一个路径
    
    # 如果所有路径都失败，尝试直接导入
    try:
        logger.info("所有路径尝试失败，尝试直接导入wxauto")
        import wxauto
        logger.info("成功直接导入wxauto")
        return True
    except ImportError as e:
        logger.error(f"wxauto导入失败: {str(e)}")
        return False

def get_wxauto():
    """
    获取wxauto模块
    
    Returns:
        module: wxauto模块，如果导入失败则返回None
    """
    if ensure_wxauto_importable():
        try:
            import wxauto
            return wxauto
        except ImportError:
            logger.error("无法导入wxauto模块")
            return None
    return None

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 确保wxauto库能够被正确导入
    if ensure_wxauto_importable():
        print("wxauto库已成功导入")
        sys.exit(0)
    else:
        print("wxauto库导入失败")
        sys.exit(1)
