"""
API服务逻辑
专门用于启动和管理API服务
"""

import os
import sys
import logging
import traceback
import atexit
import signal

# 导入统一日志管理器
from app.unified_logger import logger

# 设置API服务的库名称
logger.set_lib_name("Flask")

# 退出时清理资源
def cleanup():
    """退出时清理资源"""
    try:
        from app.unified_logger import unified_logger
        logger.info("正在关闭统一日志管理器...")
        unified_logger.shutdown()
        print("统一日志管理器已关闭")  # 使用 print 因为 logger 可能已经关闭
    except Exception as e:
        print(f"关闭统一日志管理器时出错: {str(e)}")

# 注册退出处理函数
atexit.register(cleanup)

# 注册信号处理
def signal_handler(sig, frame):
    """信号处理函数"""
    logger.info(f"API服务接收到信号 {sig}，正在退出...")
    cleanup()
    sys.exit(0)

# 注册SIGINT和SIGTERM信号处理
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def check_mutex():
    """检查互斥锁，确保同一时间只有一个API服务实例在运行"""
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

        # 导入配置模块
        from app.config import Config
        port = Config.PORT
        logger.info(f"API服务端口: {port}")

        # 创建API服务互斥锁
        api_mutex = app_mutex.create_api_mutex(port)

        # 尝试获取API服务互斥锁
        if not api_mutex.acquire():
            logger.warning(f"端口 {port} 已被占用，API服务可能已在运行")
            return False

        logger.info(f"成功获取API服务互斥锁，端口: {port}")
        return True
    except ImportError as e:
        logger.warning(f"无法导入互斥锁模块或配置模块: {str(e)}")
        logger.warning(traceback.format_exc())
        return True
    except Exception as e:
        logger.error(f"互斥锁检查失败: {str(e)}")
        logger.error(traceback.format_exc())
        return True

def check_dependencies():
    """检查依赖项"""
    try:
        # 尝试导入必要的模块
        import flask
        import requests
        import psutil
        import sys

        # 在打包环境中跳过微信自动化库检测，避免库冲突
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            logger.info("打包环境中跳过微信自动化库检测，避免库冲突")
            logger.info("微信自动化库将在实际使用时进行检测和初始化")
        else:
            # 使用统一的库检测器检查微信自动化库
            from app.wechat_lib_detector import detector

            # 检测所有可用的库
            available_libs = detector.get_available_libraries()
            if not available_libs:
                logger.error("没有检测到可用的微信自动化库")
                logger.error("请安装wxauto或wxautox库: pip install wxauto wxautox")
                return False

            logger.info(f"检测到可用的微信自动化库: {', '.join(available_libs)}")

            # 显示检测摘要
            summary = detector.get_detection_summary()
            logger.info(f"库检测摘要:\n{summary}")

        logger.info("依赖项检查成功")
        return True
    except ImportError as e:
        logger.error(f"依赖项检查失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    except Exception as e:
        logger.error(f"检查依赖项时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def start_queue_processors():
    """启动队列处理器"""
    try:
        # 导入队列处理器模块
        try:
            from app.api_queue import start_queue_processors as start_queue

            # 启动队列处理器
            start_queue()
            logger.info("队列处理器已启动")
            return True
        except ImportError as e:
            # 如果找不到队列处理器模块，记录警告但继续执行
            logger.warning(f"导入队列处理器模块失败: {str(e)}")
            logger.warning("将继续执行，但某些功能可能不可用")
            return True
    except Exception as e:
        logger.error(f"启动队列处理器时出错: {str(e)}")
        logger.error(traceback.format_exc())
        # 即使队列处理器启动失败，也继续执行
        logger.warning("将继续执行，但某些功能可能不可用")
        return True

def start_api():
    """启动API服务"""
    try:
        logger.info("===== 开始启动API服务 =====")

        # 检查互斥锁
        logger.info("正在检查互斥锁...")
        if not check_mutex():
            logger.info("互斥锁检查失败，退出")
            sys.exit(0)
        logger.info("互斥锁检查通过")

        # 检查依赖项
        logger.info("正在检查依赖项...")
        if not check_dependencies():
            logger.error("依赖项检查失败，无法启动API服务")
            sys.exit(1)
        logger.info("依赖项检查通过")

        # 启动队列处理器
        logger.info("正在启动队列处理器...")
        if not start_queue_processors():
            logger.error("队列处理器启动失败，无法启动API服务")
            sys.exit(1)
        logger.info("队列处理器启动成功")

        # 创建并启动Flask应用
        try:
            # 记录当前环境信息
            logger.info(f"当前工作目录: {os.getcwd()}")
            logger.info(f"Python路径: {sys.path}")

            # 确保app目录在Python路径中
            app_dir = os.path.join(os.getcwd(), "app")
            if os.path.exists(app_dir) and app_dir not in sys.path:
                sys.path.insert(0, app_dir)
                logger.info(f"已将app目录添加到Python路径: {app_dir}")

            # 导入Flask应用创建函数
            logger.info("正在尝试导入Flask应用创建函数...")
            try:
                # 首先尝试从app包导入
                from app import create_app
                logger.info("成功从app包导入Flask应用创建函数")
            except ImportError as e:
                logger.warning(f"从app包导入Flask应用创建函数失败: {str(e)}")
                logger.warning(traceback.format_exc())

                # 尝试直接导入
                try:
                    import create_app
                    logger.info("成功直接导入Flask应用创建函数")
                except ImportError:
                    # 尝试直接导入app模块
                    try:
                        import app
                        logger.info("成功导入app模块")

                        # 尝试从app模块中获取create_app函数
                        if hasattr(app, 'create_app'):
                            create_app = app.create_app
                            logger.info("成功从app模块中获取create_app函数")
                        else:
                            # 尝试从app.__init__模块导入
                            try:
                                from app.__init__ import create_app
                                logger.info("成功从app.__init__模块导入create_app函数")
                            except ImportError:
                                logger.error("app模块中没有create_app函数")
                                sys.exit(1)
                    except ImportError as e:
                        logger.error(f"导入app模块失败: {str(e)}")
                        logger.error(traceback.format_exc())
                        sys.exit(1)

            # 创建应用
            logger.info("正在创建Flask应用...")
            app = create_app()
            logger.info("成功创建Flask应用")

            # 获取配置信息
            host = app.config.get('HOST', '0.0.0.0')
            port = app.config.get('PORT', 5000)
            debug = app.config.get('DEBUG', False)

            logger.info(f"正在启动Flask应用...")
            logger.info(f"监听地址: {host}:{port}")
            logger.info(f"调试模式: {debug}")

            # 禁用 werkzeug 的重新加载器，避免可能的端口冲突
            app.run(
                host=host,
                port=port,
                debug=debug,
                use_reloader=False,
                threaded=True
            )
        except ImportError as e:
            logger.error(f"导入Flask应用创建函数失败: {str(e)}")
            logger.error(traceback.format_exc())
            sys.exit(1)
        except Exception as e:
            logger.error(f"启动Flask应用时出错: {str(e)}")
            logger.error(traceback.format_exc())
            sys.exit(1)
    except Exception as e:
        logger.error(f"API服务启动过程中发生未捕获的异常: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # 设置环境变量，标记为API服务进程
    os.environ["WXAUTO_SERVICE_TYPE"] = "api"

    # 启动API服务
    start_api()
