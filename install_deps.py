"""
安装依赖脚本
用于安装wxauto和wxautox库
"""

import os
import sys
import subprocess
import time

def install_package(package):
    """安装指定的包"""
    print(f"正在安装 {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"{package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{package} 安装失败: {e}")
        return False

def install_wxauto():
    """安装wxauto库"""
    print("正在安装wxauto库...")

    # 安装尝试顺序：PyPI -> GitHub -> 本地文件夹

    # 1. 尝试从PyPI安装
    try:
        result = install_package("wxauto")
        if result:
            print("wxauto库从PyPI安装成功")
            return True
    except Exception as e:
        print(f"从PyPI安装wxauto库失败: {e}")

    # 2. 如果PyPI安装失败，尝试从GitHub克隆并安装
    print("从PyPI安装失败，尝试从GitHub克隆并安装...")
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
        print("wxauto库从GitHub安装成功")
        return True
    except Exception as e:
        print(f"从GitHub安装wxauto库失败: {e}")

    # 3. 如果PyPI和GitHub安装都失败，尝试从本地wxauto文件夹安装
    print("从GitHub安装失败，尝试从本地wxauto文件夹安装...")
    try:
        if os.path.exists("wxauto") and os.path.isdir("wxauto"):
            # 进入目录并安装
            cwd = os.getcwd()
            os.chdir("wxauto")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
            os.chdir(cwd)
            print("wxauto库从本地文件夹安装成功")
            return True
        else:
            print("本地wxauto文件夹不存在")
            return False
    except Exception as e:
        print(f"从本地文件夹安装wxauto库失败: {e}")
        return False

def install_wxautox():
    """安装wxautox库"""
    print("正在安装wxautox库...")
    try:
        # 检查是否有本地的wxautox wheel文件
        wheel_files = [f for f in os.listdir() if f.startswith("wxautox-") and f.endswith(".whl")]
        if wheel_files:
            wheel_file = wheel_files[0]
            print(f"找到本地wxautox wheel文件: {wheel_file}")
            result = install_package(wheel_file)
            return result
        else:
            print("未找到本地wxautox wheel文件，wxautox库安装失败")
            return False
    except Exception as e:
        print(f"wxautox库安装失败: {e}")
        return False

def install_dependencies():
    """安装所有依赖"""
    print("正在安装依赖...")

    # 安装requirements.txt中的依赖
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("基础依赖安装成功")
    except subprocess.CalledProcessError as e:
        print(f"基础依赖安装失败: {e}")

    # 询问用户选择使用哪个库
    print("\n请选择要使用的微信自动化库:")
    print("1. wxauto (开源免费库)")
    print("2. wxautox (付费增强库)")
    choice = input("请输入选择 [1/2] (默认: 1): ").strip()

    if choice == "2":
        # 用户选择wxautox
        wheel_files = [f for f in os.listdir() if f.startswith("wxautox-") and f.endswith(".whl")]
        if wheel_files:
            print(f"\n发现wxautox wheel文件: {wheel_files[0]}")
            install = input("是否安装wxautox? [y/n] (默认: y): ").strip().lower()
            if install != "n":
                wxautox_installed = install_wxautox()
                if wxautox_installed:
                    print("wxautox库安装成功")
                    # 更新.env文件，设置WECHAT_LIB=wxautox
                    update_env_file("wxautox")
                else:
                    print("wxautox库安装失败，将安装wxauto作为备选")
                    wxauto_installed = install_wxauto()
                    if wxauto_installed:
                        print("wxauto库安装成功")
                        # 更新.env文件，设置WECHAT_LIB=wxauto
                        update_env_file("wxauto")
                    else:
                        print("错误: wxauto库安装失败，程序无法正常运行")
                        sys.exit(1)
            else:
                print("跳过wxautox安装，将安装wxauto")
                wxauto_installed = install_wxauto()
                if wxauto_installed:
                    print("wxauto库安装成功")
                    # 更新.env文件，设置WECHAT_LIB=wxauto
                    update_env_file("wxauto")
                else:
                    print("错误: wxauto库安装失败，程序无法正常运行")
                    sys.exit(1)
        else:
            print("\n未发现wxautox wheel文件")
            print("无法安装wxautox，将安装wxauto作为备选")
            wxauto_installed = install_wxauto()
            if wxauto_installed:
                print("wxauto库安装成功")
                # 更新.env文件，设置WECHAT_LIB=wxauto
                update_env_file("wxauto")
            else:
                print("错误: wxauto库安装失败，程序无法正常运行")
                sys.exit(1)
    else:
        # 用户选择wxauto或默认选择
        wxauto_installed = install_wxauto()
        if wxauto_installed:
            print("wxauto库安装成功")
            # 更新.env文件，设置WECHAT_LIB=wxauto
            update_env_file("wxauto")
        else:
            print("错误: wxauto库安装失败，程序无法正常运行")
            sys.exit(1)

    print("\n依赖安装完成")
    print("您可以通过修改.env文件中的WECHAT_LIB参数来切换使用的库")
    print("WECHAT_LIB=wxauto 使用wxauto库")
    print("WECHAT_LIB=wxautox 使用wxautox库")

def update_env_file(lib_name):
    """更新.env文件中的WECHAT_LIB参数"""
    env_file = ".env"

    # 读取现有的.env文件
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 检查是否已有WECHAT_LIB参数
        has_lib_param = False
        for i, line in enumerate(lines):
            if line.strip().startswith("WECHAT_LIB="):
                lines[i] = f"WECHAT_LIB={lib_name}\n"
                has_lib_param = True
                break

        # 如果没有WECHAT_LIB参数，添加一个
        if not has_lib_param:
            lines.append(f"\n# 微信库选择 (wxauto 或 wxautox)\nWECHAT_LIB={lib_name}\n")

        # 写回.env文件
        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
    else:
        # 创建新的.env文件
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"# 微信库选择 (wxauto 或 wxautox)\nWECHAT_LIB={lib_name}\n")

if __name__ == "__main__":
    install_dependencies()
