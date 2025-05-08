"""
启动UI的辅助脚本
确保所有模块都能被正确导入
"""

import os
import sys
import subprocess

def main():
    # 获取当前脚本的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 确保当前目录在Python路径中
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 打印当前工作目录和Python路径，用于调试
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path}")
    
    # 尝试导入关键模块，验证路径设置是否正确
    try:
        import config_manager
        print("成功导入 config_manager 模块")
        
        # 确保目录存在
        config_manager.ensure_dirs()
        print("已确保所有必要目录存在")
        
        # 尝试导入app模块
        from app.config import Config
        print("成功导入 app.config 模块")
        
        from app.logs import logger
        print("成功导入 app.logs 模块")
        
        # 启动UI
        print("正在启动UI...")
        import app_ui
        app_ui.main()
        
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请确保在正确的目录中运行此脚本")
        sys.exit(1)

if __name__ == "__main__":
    main()
