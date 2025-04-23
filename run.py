import sys
import traceback
from app import create_app
from app.logs import logger

try:
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
    sys.exit(1)