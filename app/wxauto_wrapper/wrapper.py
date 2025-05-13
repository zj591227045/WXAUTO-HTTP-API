"""
wxauto包装器的主要接口
提供对wxauto库的所有主要功能的访问
"""

import os
import sys
import logging
from . import get_wxauto

# 配置日志
logger = logging.getLogger(__name__)

# 获取wxauto模块
wxauto = get_wxauto()

class WxAutoWrapper:
    """wxauto包装器类，提供对wxauto库的所有主要功能的访问"""
    
    def __init__(self):
        """初始化wxauto包装器"""
        self.wxauto = wxauto
        if not self.wxauto:
            logger.error("无法初始化wxauto包装器，wxauto模块不可用")
            raise ImportError("无法导入wxauto模块")
        
        # 记录wxauto模块信息
        logger.info(f"wxauto模块版本: {getattr(self.wxauto, 'VERSION', '未知')}")
        logger.info(f"wxauto模块路径: {self.wxauto.__file__}")
    
    def __getattr__(self, name):
        """获取wxauto模块的属性"""
        if self.wxauto:
            return getattr(self.wxauto, name)
        raise AttributeError(f"'WxAutoWrapper' object has no attribute '{name}', wxauto module is not available")

# 创建全局wxauto包装器实例
_wrapper_instance = None

def get_wrapper():
    """
    获取wxauto包装器实例
    
    Returns:
        WxAutoWrapper: wxauto包装器实例，如果初始化失败则返回None
    """
    global _wrapper_instance
    
    if _wrapper_instance:
        return _wrapper_instance
    
    try:
        _wrapper_instance = WxAutoWrapper()
        return _wrapper_instance
    except Exception as e:
        logger.error(f"初始化wxauto包装器失败: {str(e)}")
        return None

# 导出所有wxauto模块的函数和类
if wxauto:
    # 导出所有wxauto模块的属性
    for attr_name in dir(wxauto):
        if not attr_name.startswith('_'):
            globals()[attr_name] = getattr(wxauto, attr_name)
