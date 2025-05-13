"""
打包应用程序
使用PyInstaller将应用程序打包为Windows可执行文件
"""

import os
import sys
import shutil
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

    # 添加wxauto模块及其子模块
    cmd.extend([
        "--hidden-import", "wxauto",
        "--hidden-import", "wxauto.wxauto",
        "--hidden-import", "wxauto.elements",
        "--hidden-import", "wxauto.languages",
        "--hidden-import", "wxauto.utils",
        "--hidden-import", "wxauto.color",
        "--hidden-import", "wxauto.errors",
        "--hidden-import", "wxauto.uiautomation",
    ])

    # 添加wxauto_wrapper模块及其子模块
    cmd.extend([
        "--hidden-import", "app.wxauto_wrapper",
        "--hidden-import", "app.wxauto_wrapper.wrapper",
    ])

    # 添加wxautox可能需要的依赖
    cmd.extend([
        "--hidden-import", "tenacity",
        "--hidden-import", "requests",
        "--hidden-import", "urllib3",
        "--hidden-import", "certifi",
        "--hidden-import", "idna",
        "--hidden-import", "charset_normalizer",
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
        ("dynamic_package_manager.py", "."),
        ("wxauto_import.py", "."),  # 添加wxauto导入辅助模块
    ]

    # 特殊处理wxauto文件夹
    wxauto_path = os.path.join(os.getcwd(), "wxauto")
    if os.path.exists(wxauto_path) and os.path.isdir(wxauto_path):
        print(f"找到wxauto文件夹: {wxauto_path}")
        # 添加wxauto文件夹
        data_files.append(("wxauto", "wxauto"))

        # 检查wxauto/wxauto子目录
        wxauto_inner_path = os.path.join(wxauto_path, "wxauto")
        if os.path.exists(wxauto_inner_path) and os.path.isdir(wxauto_inner_path):
            print(f"找到wxauto内部目录: {wxauto_inner_path}")
            # 确保wxauto/wxauto目录中的所有文件都被包含
            for root, dirs, files in os.walk(wxauto_inner_path):
                for file in files:
                    if file.endswith('.py'):
                        rel_dir = os.path.relpath(root, wxauto_path)
                        src_file = os.path.join(root, file)
                        dst_dir = os.path.join("wxauto", rel_dir)
                        data_files.append((src_file, dst_dir))
                        print(f"添加wxauto模块文件: {src_file} -> {dst_dir}")

            # 直接将wxauto模块复制到site-packages目录
            print("将wxauto模块复制到site-packages目录，确保能够被正确导入")
            cmd.extend([
                "--add-data", f"{wxauto_path}{os.pathsep}.",
            ])
    else:
        print("警告: 找不到wxauto文件夹，将无法包含wxauto库")

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
