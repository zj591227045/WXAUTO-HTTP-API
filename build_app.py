"""
打包应用程序
使用PyInstaller将应用程序打包为Windows可执行文件
"""

import os
import sys
import shutil
import subprocess
import argparse
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

    # 添加单文件选项
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    # 添加数据文件
    data_files = [
        (".env", "."),
        ("data", "data"),
        ("app", "app"),
        ("icons", "icons"),
        ("fix_path.py", "."),
        ("config_manager.py", "."),
        ("fix_dependencies.py", "."),
        ("requirements.txt", "."),
        ("app_ui.py", "."),
        ("app_mutex.py", "."),
        ("ui_service.py", "."),
        ("api_service.py", "."),
        ("main.py", "."),
        ("run.py", "."),
        ("start_ui.bat", "."),
        ("start_api.bat", "."),
        ("start_api_packaged.bat", "."),
        ("initialize_wechat.bat", "."),
        ("create_icon.py", "."),
        ("wxauto", "wxauto")
    ]

    for src, dst in data_files:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])

    # 排除wxautox库
    cmd.extend(["--exclude-module", "wxautox"])

    # 添加名称
    cmd.extend(["--name", app_name])

    # 添加入口点
    cmd.append("main.py")

    # 执行命令
    print(f"执行命令: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    print(f"打包完成，输出目录: {dist_dir / app_name}")

    # 复制wxautox wheel文件到输出目录
    wheel_files = [f for f in os.listdir() if f.startswith("wxautox-") and f.endswith(".whl")]
    if wheel_files:
        wheel_file = wheel_files[0]
        wheel_dest = dist_dir / app_name / wheel_file
        shutil.copy2(wheel_file, wheel_dest)
        print(f"已复制wxautox wheel文件到输出目录: {wheel_dest}")

    return dist_dir / app_name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="打包应用程序")
    parser.add_argument("--debug", action="store_true", help="是否为调试模式")
    parser.add_argument("--onefile", action="store_true", help="是否打包为单个文件")
    args = parser.parse_args()

    build_app(debug=args.debug, onefile=args.onefile)
