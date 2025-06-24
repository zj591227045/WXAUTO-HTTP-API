"""
wxauto_http_api 主入口点
负责解析命令行参数并决定启动UI还是API服务
"""

import os
import sys
import io
import logging
import argparse
import traceback

# 设置标准输出和标准错误的编码为UTF-8
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception as e:
    print(f"设置标准输出编码失败: {str(e)}")

# 设置环境变量，确保Python使用UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'  # 禁用旧版Windows标准IO处理

# 配置日志
import os

# 确保日志目录存在
os.makedirs('data/logs', exist_ok=True)

# 创建日志处理器
# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# 配置根日志记录器 - 只使用控制台处理器，不创建额外的日志文件
# 详细的日志会由app/logs.py模块处理
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(console_handler)

# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)

def setup_environment():
    """设置环境变量"""
    # 记录启动环境信息
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

def main():
    """主函数，解析命令行参数并启动相应的服务"""
    # 设置环境
    setup_environment()

    # 记录命令行参数
    logger.info(f"命令行参数: {sys.argv}")

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="wxauto_http_api")
    parser.add_argument("--service", choices=["ui", "api"], default="ui",
                      help="指定要启动的服务类型: ui 或 api")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--no-mutex-check", action="store_true", help="禁用互斥锁检查")

    # 在打包环境中，可能会有额外的参数，如main.py
    if getattr(sys, 'frozen', False) and len(sys.argv) > 1 and sys.argv[1].endswith('.py'):
        # 移除第一个参数（可能是main.py）
        logger.info(f"检测到打包环境中的脚本参数: {sys.argv[1]}，将移除")
        args = parser.parse_args(sys.argv[2:])
    else:
        args = parser.parse_args()

    # 记录解析后的参数
    logger.info(f"解析后的参数: service={args.service}, debug={args.debug}, no_mutex_check={args.no_mutex_check}")

    # 设置环境变量，标记服务类型
    os.environ["WXAUTO_SERVICE_TYPE"] = args.service

    # 设置调试模式
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        os.environ["WXAUTO_DEBUG"] = "1"
        logger.debug("已启用调试模式")

    # 设置互斥锁检查
    if args.no_mutex_check:
        os.environ["WXAUTO_NO_MUTEX_CHECK"] = "1"
        logger.info("已禁用互斥锁检查")

    # 导入fix_path模块
    try:
        # 先尝试直接导入
        try:
            # 尝试从app目录导入
            sys.path.insert(0, os.path.join(os.getcwd(), "app"))
            from app import fix_path
            app_root = fix_path.fix_paths()
            logger.info(f"路径修复完成，应用根目录: {app_root}")
        except ImportError:
            # 如果直接导入失败，尝试创建一个简单的fix_paths函数
            logger.warning("无法导入fix_path模块，将使用内置的路径修复函数")

            def fix_paths():
                """简单的路径修复函数"""
                app_root = os.getcwd()

                # 确保wxauto目录在Python路径中
                wxauto_path = os.path.join(app_root, "wxauto")
                if os.path.exists(wxauto_path) and wxauto_path not in sys.path:
                    sys.path.insert(0, wxauto_path)
                    logger.info(f"已将wxauto目录添加到Python路径: {wxauto_path}")

                # 确保app目录在Python路径中
                app_path = os.path.join(app_root, "app")
                if os.path.exists(app_path) and app_path not in sys.path:
                    sys.path.insert(0, app_path)
                    logger.info(f"已将app目录添加到Python路径: {app_path}")

                return app_root

            app_root = fix_paths()
            logger.info(f"使用内置路径修复函数，应用根目录: {app_root}")
    except Exception as e:
        logger.error(f"路径修复时出错: {str(e)}")
        logger.error(traceback.format_exc())

    # 导入Unicode编码修复模块
    try:
        logger.info("尝试导入Unicode编码修复模块")
        from app import unicode_fix
        logger.info("成功导入Unicode编码修复模块")
    except ImportError as e:
        logger.warning(f"导入Unicode编码修复模块失败: {str(e)}")
        logger.warning("这可能会导致在处理包含Unicode表情符号的微信名称时出现问题")
    except Exception as e:
        logger.error(f"应用Unicode编码修复时出错: {str(e)}")
        logger.error(traceback.format_exc())

    # 检查微信自动化库是否可用
    try:
        logger.info("检查微信自动化库...")

        # 检查wxauto
        try:
            import wxauto
            logger.info("wxauto库可用")
        except ImportError:
            logger.warning("wxauto库不可用")

        # 检查wxautox
        try:
            import wxautox
            logger.info("wxautox库可用")
        except ImportError:
            logger.warning("wxautox库不可用")

    except Exception as e:
        logger.error(f"检查微信自动化库时出错: {str(e)}")
        logger.error(traceback.format_exc())

    # 根据服务类型启动相应的服务
    if args.service == "ui":
        logger.info("正在启动UI服务...")
        try:
            from app.ui_service import start_ui
            start_ui()
        except ImportError as e:
            logger.error(f"导入UI服务模块失败: {str(e)}")
            logger.error(traceback.format_exc())
            sys.exit(1)
        except Exception as e:
            logger.error(f"启动UI服务时出错: {str(e)}")
            logger.error(traceback.format_exc())
            sys.exit(1)
    elif args.service == "api":
        logger.info("正在启动API服务...")
        try:
            from app.api_service import start_api
            start_api()
        except ImportError as e:
            logger.error(f"导入API服务模块失败: {str(e)}")
            logger.error(traceback.format_exc())
            sys.exit(1)
        except Exception as e:
            logger.error(f"启动API服务时出错: {str(e)}")
            logger.error(traceback.format_exc())
            sys.exit(1)

if __name__ == "__main__":
    main()
