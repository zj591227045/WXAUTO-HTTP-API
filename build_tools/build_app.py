"""
打包应用程序
使用PyInstaller将应用程序打包为Windows可执行文件
"""

import os
import sys
import subprocess
import argparse
import importlib
from pathlib import Path

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import PyInstaller
        print(f"PyInstaller已安装，版本: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller安装完成")

    try:
        from PIL import Image, ImageDraw, ImageFont
        print("Pillow已安装")
    except ImportError:
        print("Pillow未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
        print("Pillow安装完成")

    # 检查pywin32是否已安装
    try:
        import win32ui
        print("PyWin32已安装")
    except ImportError:
        print("PyWin32未安装或win32ui模块不可用，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
        # 安装后运行pywin32的post-install脚本
        try:
            import site
            site_packages = site.getsitepackages()[0]
            post_install_script = os.path.join(site_packages, 'pywin32_system32', 'scripts', 'pywin32_postinstall.py')
            if os.path.exists(post_install_script):
                print("运行pywin32安装后脚本...")
                subprocess.check_call([sys.executable, post_install_script, "-install"])
            else:
                print("找不到pywin32安装后脚本，可能需要手动运行")
        except Exception as e:
            print(f"运行pywin32安装后脚本失败: {e}")
        print("PyWin32安装完成")

    # 检查wxautox可能需要的依赖
    dependencies = ["tenacity", "requests", "urllib3", "certifi", "idna", "charset_normalizer"]
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print(f"{dep}已安装")
        except ImportError:
            print(f"{dep}未安装，正在安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"{dep}安装完成")

def create_icon():
    """创建图标"""
    try:
        import create_icon
        icon_path = create_icon.create_wechat_style_icon()
        print(f"图标已创建: {icon_path}")
        return icon_path
    except Exception as e:
        print(f"创建图标失败: {e}")
        return None

def build_app(debug=False, onefile=False):
    """
    打包应用程序

    Args:
        debug (bool): 是否为调试模式
        onefile (bool): 是否打包为单个文件
    """
    # 检查依赖
    check_dependencies()

    # 创建图标
    icon_path = create_icon()
    if not icon_path:
        print("警告: 未能创建图标，将使用默认图标")
        icon_path = "icons/wxauto_icon.ico"

    # 确保输出目录存在
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    # 构建命令
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--additional-hooks-dir", "hooks",  # 添加自定义hook目录
    ]

    # 添加图标
    if os.path.exists(icon_path):
        cmd.extend(["--icon", icon_path])

    # 添加调试选项
    if debug:
        cmd.append("--debug")
        cmd.append("--console")
        app_name = "wxauto_http_api_debug"
    else:
        cmd.append("--windowed")
        app_name = "wxauto_http_api"

    # 默认使用单文件模式
    if onefile or not onefile:  # 强制使用单文件模式
        cmd.append("--onefile")
        print("使用单文件打包模式")

    # 添加Flask和Web框架相关的隐藏导入
    cmd.extend([
        "--hidden-import", "flask",
        "--hidden-import", "flask.app",
        "--hidden-import", "flask.blueprints",
        "--hidden-import", "flask.json",
        "--hidden-import", "flask.logging",
        "--hidden-import", "flask.sessions",
        "--hidden-import", "flask.templating",
        "--hidden-import", "flask.wrappers",
        "--hidden-import", "flask_restful",
        "--hidden-import", "flask_limiter",
        "--hidden-import", "flask_limiter.util",
        "--hidden-import", "werkzeug",
        "--hidden-import", "werkzeug.serving",
        "--hidden-import", "werkzeug.utils",
        "--hidden-import", "jinja2",
        "--hidden-import", "jinja2.runtime",
        "--hidden-import", "markupsafe",
        "--hidden-import", "itsdangerous",
        "--hidden-import", "click",
    ])

    # 确保包含pywin32的所有必要组件
    cmd.extend([
        "--hidden-import", "win32api",
        "--hidden-import", "win32con",
        "--hidden-import", "win32gui",
        "--hidden-import", "win32ui",
        "--hidden-import", "win32wnet",
        "--hidden-import", "win32com",
        "--hidden-import", "win32com.client",
        "--hidden-import", "pythoncom",
        "--hidden-import", "pywintypes",
    ])

    # 添加微信自动化库的隐藏导入（通过pip包管理）
    # 只导入主模块，避免子模块导入错误
    cmd.extend([
        "--hidden-import", "wxauto",
        "--hidden-import", "wxautox",
    ])

    # wxauto_wrapper已不再使用，移除相关导入

    # 添加网络请求和HTTP相关依赖
    cmd.extend([
        "--hidden-import", "requests",
        "--hidden-import", "requests.adapters",
        "--hidden-import", "requests.auth",
        "--hidden-import", "requests.cookies",
        "--hidden-import", "requests.models",
        "--hidden-import", "requests.sessions",
        "--hidden-import", "urllib3",
        "--hidden-import", "urllib3.poolmanager",
        "--hidden-import", "urllib3.util",
        "--hidden-import", "certifi",
        "--hidden-import", "idna",
        "--hidden-import", "charset_normalizer",
    ])

    # 添加配置和工具库依赖
    cmd.extend([
        "--hidden-import", "tenacity",
        "--hidden-import", "dotenv",
        "--hidden-import", "pyyaml",
        "--hidden-import", "yaml",
        "--hidden-import", "json",
        "--hidden-import", "logging",
        "--hidden-import", "logging.handlers",
        "--hidden-import", "psutil",
        "--hidden-import", "pyperclip",
        "--hidden-import", "comtypes",
        "--hidden-import", "uiautomation",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageDraw",
        "--hidden-import", "PIL.ImageFont",
    ])

    # 添加JWT和认证相关依赖
    cmd.extend([
        "--hidden-import", "jose",
        "--hidden-import", "jose.jwt",
        "--hidden-import", "jose.exceptions",
        "--hidden-import", "cryptography",
        "--hidden-import", "cryptography.fernet",
        "--hidden-import", "cryptography.hazmat",
    ])

    # 添加JWT和认证相关依赖
    cmd.extend([
        "--hidden-import", "jose",
        "--hidden-import", "jose.jwt",
        "--hidden-import", "jose.exceptions",
        "--hidden-import", "cryptography",
        "--hidden-import", "cryptography.fernet",
        "--hidden-import", "cryptography.hazmat",
    ])

    # 添加编码模块，确保UTF-8编码支持
    cmd.extend([
        "--hidden-import", "encodings",
        "--hidden-import", "encodings.utf_8",
        "--hidden-import", "encodings.gbk",
        "--hidden-import", "encodings.gb2312",
        "--hidden-import", "encodings.gb18030",
        "--hidden-import", "encodings.big5",
        "--hidden-import", "encodings.latin_1",
    ])

    # 添加pywin32的DLL文件
    try:
        import site
        import win32api

        # 获取pywin32的安装路径
        site_packages = site.getsitepackages()[0]
        pywin32_path = os.path.dirname(win32api.__file__)

        # 添加pywin32的DLL文件
        pywin32_system32_path = os.path.join(os.path.dirname(pywin32_path), 'pywin32_system32')
        if os.path.exists(pywin32_system32_path):
            for file in os.listdir(pywin32_system32_path):
                if file.endswith('.dll'):
                    cmd.extend(["--add-binary", f"{os.path.join(pywin32_system32_path, file)}{os.pathsep}."])
                    print(f"添加pywin32 DLL文件: {file}")
    except (ImportError, AttributeError) as e:
        print(f"无法添加pywin32 DLL文件: {e}")

    # 添加数据文件
    data_files = [
        (".env", "."),
        ("data", "data"),
        ("app", "app"),
        ("icons", "icons"),
        ("requirements.txt", "."),
        ("main.py", "."),
    ]

    # wxauto和wxautox库现在通过pip包管理，无需特殊处理文件夹

    for src, dst in data_files:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])

    # 不再排除wxautox库，允许其被打包

    # 添加名称
    cmd.extend(["--name", app_name])

    # 添加入口点
    cmd.append("main.py")

    # 执行命令
    print(f"执行命令: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    print(f"打包完成，输出目录: {dist_dir / app_name}")

    return dist_dir / app_name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="打包应用程序")
    parser.add_argument("--debug", action="store_true", help="是否为调试模式")
    parser.add_argument("--onefile", action="store_true", help="是否打包为单个文件")
    args = parser.parse_args()

    build_app(debug=args.debug, onefile=args.onefile)
