"""
UI服务逻辑
专门用于启动和管理UI服务
"""

import os
import sys
import logging
import traceback

# 配置日志
logger = logging.getLogger(__name__)

def check_mutex():
    """检查互斥锁，确保同一时间只有一个UI实例在运行"""
    # 如果禁用互斥锁检查，则跳过
    if os.environ.get("WXAUTO_NO_MUTEX_CHECK") == "1":
        logger.info("已禁用互斥锁检查，跳过")
        return True

    try:
        # 导入互斥锁模块
        try:
            # 首先尝试从app包导入
            from app import app_mutex
            logger.info("成功从app包导入 app_mutex 模块")
        except ImportError:
            # 如果失败，尝试直接导入（兼容旧版本）
            import app_mutex
            logger.info("成功直接导入 app_mutex 模块")

        # 尝试获取UI互斥锁
        if not app_mutex.ui_mutex.acquire():
            logger.warning("另一个UI实例已在运行，将退出")
            # print("另一个UI实例已在运行，请不要重复启动")  # 注释掉，避免stdout问题
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showwarning("警告", "另一个UI实例已在运行，请不要重复启动")
            except:
                pass
            return False

        logger.info("成功获取UI互斥锁")
        return True
    except ImportError:
        logger.warning("无法导入互斥锁模块，跳过互斥锁检查")
        return True
    except Exception as e:
        logger.error(f"互斥锁检查失败: {str(e)}")
        logger.error(traceback.format_exc())
        return True

def check_dependencies():
    """检查依赖项"""
    try:
        # 导入config_manager模块
        try:
            # 首先尝试从app包导入
            from app import config_manager
            logger.info("成功从app包导入 config_manager 模块")
        except ImportError:
            # 如果失败，尝试直接导入（兼容旧版本）
            import config_manager
            logger.info("成功直接导入 config_manager 模块")

        # 确保目录存在
        config_manager.ensure_dirs()
        logger.info("已确保所有必要目录存在")
        return True
    except ImportError as e:
        logger.error(f"导入config_manager模块失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    except Exception as e:
        logger.error(f"检查依赖项时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def start_ui():
    """启动UI服务"""
    # 检查互斥锁
    if not check_mutex():
        sys.exit(0)

    # 检查依赖项
    if not check_dependencies():
        logger.error("依赖项检查失败，无法启动UI服务")
        sys.exit(1)

    # 导入app_ui模块
    try:
        try:
            # 首先尝试从app包导入
            from app import app_ui
            logger.info("成功从app包导入 app_ui 模块")
        except ImportError:
            # 如果失败，尝试直接导入（兼容旧版本）
            import app_ui
            logger.info("成功直接导入 app_ui 模块")

        # 启动UI
        logger.info("正在启动UI...")
        app_ui.main()
    except ImportError as e:
        logger.error(f"导入app_ui模块失败: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动UI时出错: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # 设置环境变量，标记为UI服务进程
    os.environ["WXAUTO_SERVICE_TYPE"] = "ui"

    # 启动UI服务
    start_ui()
