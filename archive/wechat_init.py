"""
微信初始化模块
用于在应用启动时初始化微信相关配置
"""

import os
import logging
from pathlib import Path
import config_manager

logger = logging.getLogger(__name__)

def setup_wxauto_paths():
    """
    设置wxauto库的文件保存路径
    将默认的保存路径修改为data/api/temp
    """
    try:
        # 导入wxauto库
        from wxauto.elements import WxParam

        # 确保目录存在
        config_manager.ensure_dirs()

        # 获取临时目录路径
        temp_dir = str(config_manager.TEMP_DIR.absolute())

        # 记录原始保存路径
        original_path = WxParam.DEFALUT_SAVEPATH
        logger.info(f"原始wxauto保存路径: {original_path}")

        # 修改为新的保存路径
        WxParam.DEFALUT_SAVEPATH = temp_dir
        logger.info(f"已修改wxauto保存路径为: {temp_dir}")

        return True
    except ImportError:
        logger.warning("无法导入wxauto库，跳过路径设置")
        return False
    except Exception as e:
        logger.error(f"设置wxauto路径时出错: {str(e)}")
        return False

def initialize():
    """
    初始化微信相关配置
    """
    # 设置wxauto路径
    setup_wxauto_paths()

    # 可以在这里添加其他初始化操作

    logger.info("微信初始化配置完成")
