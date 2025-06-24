"""
启动UI的辅助脚本
确保所有模块都能被正确导入
"""

import os
import sys
import subprocess
import traceback
import logging
import argparse

# 配置基本的控制台日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('startup_log.txt', 'w', 'utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 记录启动信息
logger.info("启动UI脚本开始执行")
logger.info(f"Python版本: {sys.version}")
logger.info(f"当前工作目录: {os.getcwd()}")
logger.info(f"Python路径: {sys.path}")
logger.info(f"是否在PyInstaller环境中运行: {getattr(sys, 'frozen', False)}")

# 导入路径修复模块
try:
    logger.info("尝试导入路径修复模块")
    import fix_path
    app_root = fix_path.fix_paths()
    logger.info(f"路径修复完成，应用根目录: {app_root}")
except ImportError as e:
    logger.error(f"导入路径修复模块失败: {str(e)}")
    logger.error(traceback.format_exc())
except Exception as e:
    logger.error(f"路径修复时出错: {str(e)}")
    logger.error(traceback.format_exc())

# 导入Unicode编码修复模块
try:
    logger.info("尝试导入Unicode编码修复模块")
    import app.unicode_fix
    logger.info("成功导入Unicode编码修复模块")
except ImportError as e:
    logger.warning(f"导入Unicode编码修复模块失败: {str(e)}")
    logger.warning("这可能会导致在处理包含Unicode表情符号的微信名称时出现问题")
except Exception as e:
    logger.error(f"应用Unicode编码修复时出错: {str(e)}")
    logger.error(traceback.format_exc())

def main():
    try:
        # 获取当前脚本的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"当前脚本目录: {current_dir}")

        # 确保当前目录在Python路径中
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            logger.info(f"已添加当前目录到Python路径: {current_dir}")

        # 记录当前工作目录和Python路径
        logger.info(f"当前工作目录: {os.getcwd()}")
        logger.info(f"Python路径: {sys.path}")

        # 尝试导入关键模块，验证路径设置是否正确
        try:
            logger.info("尝试导入config_manager模块")
            import config_manager
            logger.info("成功导入 config_manager 模块")

            # 确保目录存在
            logger.info("确保必要目录存在")
            config_manager.ensure_dirs()
            logger.info("已确保所有必要目录存在")

            # 尝试导入app模块
            logger.info("尝试导入app.config模块")
            from app.config import Config
            logger.info("成功导入 app.config 模块")

            logger.info("尝试导入app.logs模块")
            from app.logs import logger as app_logger
            logger.info("成功导入 app.logs 模块")

            # 启动UI
            logger.info("正在启动UI...")
            import app_ui
            app_ui.main()

        except ImportError as e:
            logger.error(f"导入模块失败: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"导入模块失败: {e}")
            print("请确保在正确的目录中运行此脚本")
            # 创建一个错误对话框
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("启动错误", f"导入模块失败: {e}\n\n请确保在正确的目录中运行此脚本")
            except:
                pass
            sys.exit(1)
    except Exception as e:
        logger.error(f"启动UI时出错: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"启动UI时出错: {e}")
        # 创建一个错误对话框
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动错误", f"启动UI时出错: {e}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="启动wxauto_http_api管理界面")
    parser.add_argument("--no-mutex-check", action="store_true", help="禁用互斥锁检查")
    parser.add_argument("--no-auto-start", action="store_true", help="禁用自动启动API服务")
    args = parser.parse_args()

    # 检查互斥锁
    if not args.no_mutex_check:
        try:
            # 导入互斥锁模块
            import app_mutex

            # 尝试获取UI互斥锁
            if not app_mutex.ui_mutex.acquire():
                logger.warning("另一个UI实例已在运行，将退出")
                print("另一个UI实例已在运行，请不要重复启动")
                try:
                    import tkinter as tk
                    from tkinter import messagebox
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showwarning("警告", "另一个UI实例已在运行，请不要重复启动")
                except:
                    pass
                sys.exit(0)

            logger.info("成功获取UI互斥锁")
        except ImportError:
            logger.warning("无法导入互斥锁模块，跳过互斥锁检查")
        except Exception as e:
            logger.error(f"互斥锁检查失败: {str(e)}")

    # 设置环境变量，用于控制自动启动
    if args.no_auto_start:
        os.environ["WXAUTO_NO_AUTO_START"] = "1"
        logger.info("已禁用自动启动API服务")

    # 启动主程序
    main()
