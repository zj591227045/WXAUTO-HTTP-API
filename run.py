import sys
import traceback
import os
import subprocess
import atexit
import signal
import logging
from app import create_app
from app.logs import logger
from app.config import Config
from app.api_queue import start_queue_processors, stop_queue_processors

# 配置 Werkzeug 日志
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)  # 只显示错误级别的日志

# 自定义 Werkzeug 日志格式处理器
class WerkzeugLogFilter(logging.Filter):
    def filter(self, record):
        # 移除 Werkzeug 日志中的时间戳
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # 移除类似 "127.0.0.1 - - [08/May/2025 12:04:46]" 这样的时间戳
            if '] "' in record.msg and ' - - [' in record.msg:
                parts = record.msg.split('] "', 1)
                if len(parts) > 1:
                    ip_part = parts[0].split(' - - [')[0]
                    request_part = parts[1]
                    record.msg = f"{ip_part} - {request_part}"
        return True

# 添加过滤器到 Werkzeug 日志处理器
for handler in werkzeug_logger.handlers:
    handler.addFilter(WerkzeugLogFilter())

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

            # 安装尝试顺序：PyPI -> GitHub -> 本地文件夹
            pypi_success = False
            github_success = False

            # 1. 尝试从PyPI安装
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "wxauto"])
                logger.info("wxauto库从PyPI安装成功")
                pypi_success = True
            except Exception as e:
                logger.error(f"从PyPI安装wxauto库失败: {e}")

            # 2. 如果PyPI安装失败，尝试从GitHub安装
            if not pypi_success:
                logger.warning("尝试从GitHub克隆并安装wxauto...")
                try:
                    # 使用临时目录
                    temp_dir = "wxauto_temp"
                    if os.path.exists(temp_dir):
                        # 如果临时目录已存在，先尝试更新
                        try:
                            cwd = os.getcwd()
                            os.chdir(temp_dir)
                            subprocess.check_call(["git", "pull"])
                            os.chdir(cwd)
                        except Exception:
                            # 如果更新失败，删除目录重新克隆
                            import shutil
                            shutil.rmtree(temp_dir, ignore_errors=True)
                            subprocess.check_call(["git", "clone", "https://github.com/cluic/wxauto.git", temp_dir])
                    else:
                        # 克隆仓库到临时目录
                        subprocess.check_call(["git", "clone", "https://github.com/cluic/wxauto.git", temp_dir])

                    # 进入目录并安装
                    cwd = os.getcwd()
                    os.chdir(temp_dir)
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
                    os.chdir(cwd)
                    logger.info("wxauto库从GitHub安装成功")
                    github_success = True
                except Exception as e:
                    logger.error(f"wxauto库从GitHub安装失败: {e}")

            # 3. 如果PyPI和GitHub安装都失败，尝试从本地wxauto文件夹安装
            if not pypi_success and not github_success:
                logger.warning("尝试从本地wxauto文件夹安装...")
                try:
                    if os.path.exists("wxauto") and os.path.isdir("wxauto"):
                        # 进入目录并安装
                        cwd = os.getcwd()
                        os.chdir("wxauto")
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
                        os.chdir(cwd)
                        logger.info("wxauto库从本地文件夹安装成功")
                    else:
                        logger.error("本地wxauto文件夹不存在")
                        logger.error("无法安装wxauto库，程序无法继续运行")
                        sys.exit(1)
                except Exception as e:
                    logger.error(f"wxauto库从本地文件夹安装失败: {e}")
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