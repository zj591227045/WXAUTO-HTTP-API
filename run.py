import sys
import traceback
import os
import subprocess
import atexit
import signal
from app import create_app
from app.logs import logger
from app.config import Config
from app.api_queue import start_queue_processors, stop_queue_processors

def check_dependencies():
    """检查依赖是否已安装"""
    # 获取配置的微信库
    wechat_lib = Config.WECHAT_LIB
    logger.info(f"配置的微信库: {wechat_lib}")

    # 检查wxauto库
    if wechat_lib == 'wxauto':
        try:
            # 尝试导入wxauto
            import wxauto
            logger.info("wxauto库已安装")
        except ImportError:
            logger.warning("wxauto库未安装，尝试安装...")
            try:
                # 尝试从PyPI安装
                subprocess.check_call([sys.executable, "-m", "pip", "install", "wxauto"])
                logger.info("wxauto库安装成功")
            except Exception as e:
                logger.error(f"wxauto库安装失败: {e}")
                logger.warning("尝试从GitHub克隆并安装wxauto...")
                try:
                    if not os.path.exists("wxauto_temp"):
                        subprocess.check_call(["git", "clone", "https://github.com/cluic/wxauto.git", "wxauto_temp"])

                    # 进入目录并安装
                    cwd = os.getcwd()
                    os.chdir("wxauto_temp")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
                    os.chdir(cwd)
                    logger.info("wxauto库从GitHub安装成功")
                except Exception as e:
                    logger.error(f"wxauto库从GitHub安装失败: {e}")
                    logger.error("无法安装wxauto库，程序无法继续运行")
                    sys.exit(1)

    # 检查wxautox库
    elif wechat_lib == 'wxautox':
        try:
            # 尝试导入wxautox
            import wxautox
            logger.info("wxautox库已安装")
        except ImportError:
            logger.error("wxautox库未安装，但配置要求使用wxautox")
            logger.error("请手动安装wxautox wheel文件，或者修改配置使用wxauto库")
            logger.error("如需使用wxauto库，请在.env文件中设置 WECHAT_LIB=wxauto")
            sys.exit(1)

    # 不支持的库
    else:
        logger.error(f"不支持的微信库: {wechat_lib}")
        logger.error("请在.env文件中设置 WECHAT_LIB=wxauto 或 WECHAT_LIB=wxautox")
        sys.exit(1)

# 退出时清理资源
def cleanup():
    """退出时清理资源"""
    logger.info("正在停止队列处理器...")
    stop_queue_processors()
    logger.info("资源清理完成")

# 注册退出处理函数
atexit.register(cleanup)

# 注册信号处理
def signal_handler(sig, frame):
    """信号处理函数"""
    logger.info(f"接收到信号 {sig}，正在退出...")
    cleanup()
    sys.exit(0)

# 注册SIGINT和SIGTERM信号处理
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    # 检查依赖
    check_dependencies()

    # 启动队列处理器
    start_queue_processors()
    logger.info("队列处理器已启动")

    # 创建应用
    app = create_app()
    logger.info("正在启动Flask应用...")

    if __name__ == '__main__':
        logger.info(f"监听地址: {app.config['HOST']}:{app.config['PORT']}")
        # 禁用 werkzeug 的重新加载器，避免可能的端口冲突
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'],
            use_reloader=False,
            threaded=True
        )
except Exception as e:
    logger.error(f"启动失败: {str(e)}")
    traceback.print_exc()
    # 确保清理资源
    cleanup()
    sys.exit(1)