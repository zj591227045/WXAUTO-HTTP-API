#!/usr/bin/env python3
"""
单文件打包脚本
专门用于创建单个exe文件
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def build_onefile():
    """
    使用PyInstaller打包为单个exe文件
    """
    print("=" * 60)
    print("开始单文件打包")
    print("=" * 60)
    
    # 确保输出目录存在
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # 构建PyInstaller命令
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",  # 单文件模式
        "--windowed",  # 无控制台窗口
        "--name", "wxauto_http_api",
        "--icon", "icons/wxauto_icon.ico",
    ]

    # 添加版本信息
    version_info = [
        "--version-file", "build_tools/version_info.txt"
    ]
    cmd.extend(version_info)
    
    # 添加Flask和Web框架的隐藏导入
    flask_imports = [
        "flask", "flask.app", "flask.blueprints", "flask.json", "flask.logging", 
        "flask.sessions", "flask.templating", "flask.wrappers", "flask_restful", 
        "flask_limiter", "flask_limiter.util", "werkzeug", "werkzeug.serving", 
        "werkzeug.utils", "jinja2", "jinja2.runtime", "markupsafe", "itsdangerous", "click"
    ]
    
    for imp in flask_imports:
        cmd.extend(["--hidden-import", imp])
    
    # 添加Windows系统相关的隐藏导入
    win_imports = [
        "win32api", "win32con", "win32gui", "win32ui", "win32wnet", 
        "win32com", "win32com.client", "pythoncom", "pywintypes"
    ]
    
    for imp in win_imports:
        cmd.extend(["--hidden-import", imp])
    
    # 添加微信自动化库
    wechat_imports = ["wxauto", "wxautox"]
    for imp in wechat_imports:
        cmd.extend(["--hidden-import", imp])
    
    # 添加网络请求相关
    network_imports = [
        "requests", "requests.adapters", "requests.auth", "requests.cookies", 
        "requests.models", "requests.sessions", "urllib3", "urllib3.poolmanager", 
        "urllib3.util", "certifi", "idna", "charset_normalizer"
    ]
    
    for imp in network_imports:
        cmd.extend(["--hidden-import", imp])
    
    # 添加配置和工具库
    tool_imports = [
        "tenacity", "dotenv", "pyyaml", "yaml", "json", "logging", 
        "logging.handlers", "psutil", "pyperclip", "comtypes", 
        "uiautomation", "PIL", "PIL.Image", "PIL.ImageDraw", "PIL.ImageFont"
    ]
    
    for imp in tool_imports:
        cmd.extend(["--hidden-import", imp])
    
    # 添加JWT和认证相关
    auth_imports = [
        "jose", "jose.jwt", "jose.exceptions", "cryptography", 
        "cryptography.fernet", "cryptography.hazmat"
    ]
    
    for imp in auth_imports:
        cmd.extend(["--hidden-import", imp])
    
    # 添加编码支持
    encoding_imports = [
        "encodings", "encodings.utf_8", "encodings.gbk", "encodings.gb2312", 
        "encodings.gb18030", "encodings.big5", "encodings.latin_1"
    ]
    
    for imp in encoding_imports:
        cmd.extend(["--hidden-import", imp])
    
    # 添加数据文件
    data_files = [
        ("data", "data"),
        ("app", "app"),
        ("icons", "icons"),
        ("requirements.txt", "."),
    ]
    
    for src, dst in data_files:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
    
    # 添加pywin32的DLL文件
    try:
        import win32api
        
        # 获取pywin32的安装路径
        pywin32_path = os.path.dirname(win32api.__file__)
        pywin32_system32_path = os.path.join(os.path.dirname(pywin32_path), 'pywin32_system32')
        
        if os.path.exists(pywin32_system32_path):
            for file in os.listdir(pywin32_system32_path):
                if file.endswith('.dll'):
                    cmd.extend(["--add-binary", f"{os.path.join(pywin32_system32_path, file)}{os.pathsep}."])
                    print(f"添加pywin32 DLL文件: {file}")
    except (ImportError, AttributeError) as e:
        print(f"无法添加pywin32 DLL文件: {e}")
    
    # 添加入口点
    cmd.append("main.py")
    
    # 执行打包命令
    print(f"执行命令: {' '.join(cmd[:10])}... (命令太长，已截断)")
    print("正在打包，请稍候...")
    
    try:
        subprocess.check_call(cmd)
        print(f"\n✓ 打包成功！输出文件: {dist_dir / 'wxauto_http_api.exe'}")
        
        # 检查文件大小
        exe_path = dist_dir / "wxauto_http_api.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"文件大小: {size_mb:.1f} MB")
        
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="单文件打包脚本")
    parser.add_argument("--test-deps", action="store_true", help="测试依赖后再打包")
    args = parser.parse_args()
    
    if args.test_deps:
        print("首先测试依赖...")
        try:
            subprocess.check_call([sys.executable, "test_build_dependencies.py"])
        except subprocess.CalledProcessError:
            print("依赖测试失败，请先解决依赖问题")
            return
    
    success = build_onefile()
    
    if success:
        print("\n" + "=" * 60)
        print("打包完成！")
        print("=" * 60)
        print("可执行文件位置: dist/wxauto_http_api.exe")
        print("建议测试exe文件是否能正常运行")
    else:
        print("\n" + "=" * 60)
        print("打包失败！")
        print("=" * 60)
        print("请检查错误信息并修复问题")

if __name__ == "__main__":
    main()
