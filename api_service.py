"""
API服务逻辑
专门用于启动和管理API服务
"""

import os
import sys
import logging
import traceback

# 配置日志
logger = logging.getLogger(__name__)

def check_mutex():
    """检查互斥锁，确保同一时间只有一个API服务实例在运行"""
    # 如果禁用互斥锁检查，则跳过
    if os.environ.get("WXAUTO_NO_MUTEX_CHECK") == "1":
        logger.info("已禁用互斥锁检查，跳过")
        return True

    try:
        # 导入互斥锁模块
        import app_mutex

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

        # 检查wxauto是否可用
        try:
            import wxauto
            logger.info("wxauto库已安装")
        except ImportError:
            logger.warning("wxauto库未安装，将尝试从本地目录导入")

            # 尝试从本地目录导入
            wxauto_path = os.path.join(os.getcwd(), "wxauto")
            if os.path.exists(wxauto_path) and os.path.isdir(wxauto_path):
                if wxauto_path not in sys.path:
                    sys.path.insert(0, wxauto_path)
                try:
                    import wxauto
                    logger.info(f"成功从本地目录导入wxauto: {wxauto_path}")
                except ImportError as e:
                    logger.error(f"从本地目录导入wxauto失败: {str(e)}")
                    return False
            else:
                logger.error("wxauto库未安装且本地目录不存在")
                return False

        # 检查wxautox是否可用（可选）
        try:
            import wxautox
            logger.info("wxautox库已安装")
        except ImportError:
            logger.info("wxautox库未安装，将使用wxauto库")

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
    # 检查互斥锁
    if not check_mutex():
        sys.exit(0)

    # 检查依赖项
    if not check_dependencies():
        logger.error("依赖项检查失败，无法启动API服务")
        sys.exit(1)

    # 启动队列处理器
    if not start_queue_processors():
        logger.error("队列处理器启动失败，无法启动API服务")
        sys.exit(1)

    # 创建并启动Flask应用
    try:
        # 导入Flask应用创建函数
        from app import create_app

        # 创建应用
        app = create_app()
        logger.info("正在启动Flask应用...")

        # 启动Flask应用
        logger.info(f"监听地址: {app.config['HOST']}:{app.config['PORT']}")
        # 禁用 werkzeug 的重新加载器，避免可能的端口冲突
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'],
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

if __name__ == "__main__":
    # 设置环境变量，标记为API服务进程
    os.environ["WXAUTO_SERVICE_TYPE"] = "api"

    # 启动API服务
    start_api()
