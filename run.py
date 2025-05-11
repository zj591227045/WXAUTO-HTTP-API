import sys
import traceback
import os
import subprocess
import atexit
import signal
import logging
import argparse
from app import create_app
from app.logs import logger
from app.config import Config
from app.api_queue import start_queue_processors, stop_queue_processors

# 导入互斥锁模块
try:
    import app_mutex
except ImportError:
    logger.warning("无法导入互斥锁模块，跳过互斥锁检查")

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
            # 确保本地wxauto文件夹在Python路径中
            wxauto_path = os.path.join(os.getcwd(), "wxauto")
            if wxauto_path not in sys.path:
                sys.path.insert(0, wxauto_path)

            # 尝试直接从本地文件夹导入wxauto
            import wxauto
            logger.info(f"成功从本地文件夹导入wxauto: {wxauto_path}")
        except ImportError as e:
            logger.error(f"无法从本地文件夹导入wxauto: {str(e)}")
            logger.error("请确保wxauto文件夹存在且包含正确的wxauto模块")
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
    # 记录启动环境信息
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"当前工作目录: {os.getcwd()}")
    logger.info(f"Python路径: {sys.path}")
    logger.info(f"是否在PyInstaller环境中运行: {getattr(sys, 'frozen', False)}")
    logger.info(f"进程类型: API服务")

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="启动wxauto_http_api API服务")
    parser.add_argument("--no-mutex-check", action="store_true", help="禁用互斥锁检查")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    args = parser.parse_args()

    # 如果启用调试模式，设置更详细的日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.info("已启用调试模式")

    # 检查互斥锁
    if not args.no_mutex_check and 'app_mutex' in globals():
        try:
            # 获取端口号
            port = Config.PORT
            logger.info(f"API服务端口: {port}")

            # 创建API服务互斥锁
            api_mutex = app_mutex.create_api_mutex(port)

            # 尝试获取API服务互斥锁
            if not api_mutex.acquire():
                logger.warning(f"端口 {port} 已被占用，API服务可能已在运行")
                sys.exit(0)

            logger.info(f"成功获取API服务互斥锁，端口: {port}")
        except Exception as e:
            logger.error(f"互斥锁检查失败: {str(e)}")
            logger.error(traceback.format_exc())
            # 继续执行，不要因为互斥锁检查失败而退出

    # 检查依赖
    try:
        check_dependencies()
    except Exception as e:
        logger.error(f"依赖检查失败: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(2)  # 返回码2表示依赖检查失败

    # 启动队列处理器
    try:
        start_queue_processors()
        logger.info("队列处理器已启动")
    except Exception as e:
        logger.error(f"启动队列处理器失败: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(3)  # 返回码3表示队列处理器启动失败

    # 创建应用
    try:
        app = create_app()
        logger.info("正在启动Flask应用...")
    except Exception as e:
        logger.error(f"创建Flask应用失败: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(4)  # 返回码4表示创建Flask应用失败

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