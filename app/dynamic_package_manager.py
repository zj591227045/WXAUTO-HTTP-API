"""
动态包管理器
用于在打包环境中动态安装和加载wxautox库
"""

import os
import sys
import subprocess
import importlib
import json
import shutil
import logging
import time
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class DynamicPackageManager:
    """管理EXE运行时动态安装及加载whl包的类"""

    def __init__(self, app_name="wxauto_http_api"):
        """
        初始化动态包管理器

        参数:
            app_name: 应用名称，用于创建存储安装包的目录
        """
        # 确定应用数据目录位置
        self.app_data_dir = os.path.join(os.getenv('LOCALAPPDATA') or os.path.expanduser('~'), app_name)

        # 创建必要的目录
        self.packages_dir = os.path.join(self.app_data_dir, "site-packages")
        self.wheels_dir = os.path.join(self.app_data_dir, "wheels")
        self.state_file = os.path.join(self.app_data_dir, "installed_packages.json")

        os.makedirs(self.packages_dir, exist_ok=True)
        os.makedirs(self.wheels_dir, exist_ok=True)

        # 将packages_dir添加到Python路径
        if self.packages_dir not in sys.path:
            sys.path.insert(0, self.packages_dir)
            #logger.info(f"【wxautox安装】已将包目录添加到Python路径: {self.packages_dir}")

        # 读取已安装的包信息
        self.installed_packages = self._load_installed_packages()
        #logger.info(f"【wxautox安装】已加载安装状态: {self.installed_packages}")

    def _load_installed_packages(self):
        """加载已安装包的信息"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    #logger.info(f"【wxautox安装】从状态文件加载数据: {data}")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                #logger.error(f"【wxautox安装】读取状态文件失败: {str(e)}")
                return {}
        #logger.info("【wxautox安装】状态文件不存在，返回空字典")
        return {}

    def _save_installed_packages(self):
        """保存已安装包的信息到状态文件"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.installed_packages, f, indent=4)
            #logger.info(f"【wxautox安装】已保存安装状态: {self.installed_packages}")
        except Exception as e:
            logger.error(f"【wxautox安装】保存状态文件失败: {str(e)}")

    def is_package_installed(self, package_name):
        """检查包是否已安装"""
        is_installed = package_name in self.installed_packages
        #logger.info(f"【wxautox安装】检查包 {package_name} 是否已安装: {is_installed}")

        # 如果状态文件显示已安装，再验证一下包是否真的存在
        if is_installed:
            # 对于wxautox，我们不尝试导入，因为它可能依赖win32ui
            if package_name == "wxautox":
                # 只检查包目录是否存在
                package_dir = os.path.join(self.packages_dir, package_name)
                if os.path.exists(package_dir):
                    #logger.info(f"【wxautox安装】包目录存在: {package_dir}")
                    # 检查__init__.py文件是否存在
                    init_file = os.path.join(package_dir, "__init__.py")
                    if os.path.exists(init_file):
                        #logger.info(f"【wxautox安装】__init__.py文件存在")
                        return True
                    else:
                        logger.warning(f"【wxautox安装】__init__.py文件不存在")
                else:
                    #logger.warning(f"【wxautox安装】包目录不存在: {package_dir}")
                    # 状态文件不准确，更新状态
                    del self.installed_packages[package_name]
                    self._save_installed_packages()
                    return False
            else:
                # 对于其他包，尝试导入来验证
                try:
                    # 尝试导入包来验证
                    importlib.import_module(package_name)
                    #logger.info(f"【wxautox安装】包 {package_name} 导入验证成功")
                    return True
                except ImportError:
                    #logger.warning(f"【wxautox安装】包 {package_name} 在状态文件中标记为已安装，但无法导入")
                    # 如果导入失败，检查包目录是否存在
                    package_dir = os.path.join(self.packages_dir, package_name)
                    if os.path.exists(package_dir):
                        logger.info(f"【wxautox安装】包目录存在: {package_dir}")
                        return True
                    else:
                        #logger.warning(f"【wxautox安装】包目录不存在: {package_dir}")
                        # 状态文件不准确，更新状态
                        del self.installed_packages[package_name]
                        self._save_installed_packages()
                        return False

        return is_installed

    def install_wheel(self, wheel_path):
        """
        安装指定的wheel文件

        参数:
            wheel_path: wheel文件的路径
        返回:
            成功安装返回True，否则返回False
        """
        #logger.info(f"【wxautox安装】开始安装wheel文件: {wheel_path}")
        wheel_file = os.path.basename(wheel_path)

        # 检查是否是wxautox wheel文件
        is_wxautox = 'wxautox-' in wheel_file
        if is_wxautox:
            logger.info(f"【wxautox安装】检测到wxautox wheel文件，将检查必要的依赖项")
            # 检查win32ui模块是否可用
            try:
                import win32ui
                logger.info(f"【wxautox安装】win32ui模块已可用")
            except ImportError:
                logger.warning(f"【wxautox安装】win32ui模块不可用，尝试从PyInstaller环境中查找")

                # 尝试从PyInstaller环境中查找win32ui模块
                pywin32_path = None
                for path in sys.path:
                    if 'pywin32_system32' in path:
                        pywin32_path = os.path.dirname(path)
                        break

                if pywin32_path:
                    logger.info(f"【wxautox安装】找到PyInstaller环境中的pywin32路径: {pywin32_path}")

                    # 将pywin32路径添加到Python路径
                    win32_path = os.path.join(pywin32_path, 'win32')
                    pywin32_system32_path = os.path.join(pywin32_path, 'pywin32_system32')

                    if win32_path not in sys.path:
                        sys.path.insert(0, win32_path)
                        logger.info(f"【wxautox安装】已将win32路径添加到Python路径: {win32_path}")

                    if pywin32_system32_path not in sys.path:
                        sys.path.insert(0, pywin32_system32_path)
                        logger.info(f"【wxautox安装】已将pywin32_system32路径添加到Python路径: {pywin32_system32_path}")

                    # 尝试再次导入win32ui
                    try:
                        import win32ui
                        logger.info(f"【wxautox安装】成功导入win32ui模块")
                    except ImportError as e:
                        logger.error(f"【wxautox安装】仍然无法导入win32ui模块: {str(e)}")

                        # 尝试复制PyInstaller环境中的pywin32文件到site-packages目录
                        try:
                            # 创建目标目录
                            win32_target = os.path.join(self.packages_dir, 'win32')
                            pywin32_system32_target = os.path.join(self.packages_dir, 'pywin32_system32')

                            os.makedirs(win32_target, exist_ok=True)
                            os.makedirs(pywin32_system32_target, exist_ok=True)

                            # 复制文件
                            for file in os.listdir(win32_path):
                                src_file = os.path.join(win32_path, file)
                                dst_file = os.path.join(win32_target, file)
                                if os.path.isfile(src_file) and not os.path.exists(dst_file):
                                    shutil.copy2(src_file, dst_file)
                                    logger.info(f"【wxautox安装】已复制win32文件: {file}")

                            for file in os.listdir(pywin32_system32_path):
                                src_file = os.path.join(pywin32_system32_path, file)
                                dst_file = os.path.join(pywin32_system32_target, file)
                                if os.path.isfile(src_file) and not os.path.exists(dst_file):
                                    shutil.copy2(src_file, dst_file)
                                    logger.info(f"【wxautox安装】已复制pywin32_system32文件: {file}")

                            # 将新路径添加到Python路径
                            if win32_target not in sys.path:
                                sys.path.insert(0, win32_target)

                            if pywin32_system32_target not in sys.path:
                                sys.path.insert(0, pywin32_system32_target)

                            # 再次尝试导入win32ui
                            try:
                                import win32ui
                                logger.info(f"【wxautox安装】成功导入win32ui模块")
                            except ImportError as e:
                                logger.error(f"【wxautox安装】复制文件后仍然无法导入win32ui模块: {str(e)}")
                                logger.warning(f"【wxautox安装】将继续安装wxautox，但可能无法正常工作")
                        except Exception as e:
                            logger.error(f"【wxautox安装】复制pywin32文件失败: {str(e)}")
                            logger.warning(f"【wxautox安装】将继续安装wxautox，但可能无法正常工作")
                else:
                    logger.warning(f"【wxautox安装】未找到PyInstaller环境中的pywin32路径")
                    logger.warning(f"【wxautox安装】将继续安装wxautox，但可能无法正常工作")

        # 复制wheel文件到wheels目录
        dest_wheel_path = os.path.join(self.wheels_dir, wheel_file)
        if os.path.abspath(wheel_path) != os.path.abspath(dest_wheel_path):
            try:
                shutil.copy2(wheel_path, dest_wheel_path)
                logger.info(f"【wxautox安装】已复制wheel文件到: {dest_wheel_path}")
            except Exception as e:
                logger.error(f"【wxautox安装】复制wheel文件失败: {str(e)}")
                return False

        try:
            # 在打包环境中，不能使用pip命令，改为直接解压wheel文件
            logger.info(f"【wxautox安装】使用直接解压方式安装wheel文件")

            # 尝试确定包名（从wheel文件名提取）
            package_name = wheel_file.split('-')[0].replace('_', '-')
            logger.info(f"【wxautox安装】提取的包名: {package_name}")

            # 创建临时目录
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info(f"【wxautox安装】创建临时目录: {temp_dir}")

                # 解压wheel文件到临时目录
                import zipfile
                with zipfile.ZipFile(dest_wheel_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                logger.info(f"【wxautox安装】已解压wheel文件到临时目录")

                # 查找包目录
                package_found = False
                for root, dirs, files in os.walk(temp_dir):
                    for dir_name in dirs:
                        if dir_name.lower() == package_name.lower() or dir_name.lower() == package_name.lower().replace('-', '_'):
                            src_package_dir = os.path.join(root, dir_name)
                            dst_package_dir = os.path.join(self.packages_dir, dir_name)

                            # 如果目标目录已存在，先删除
                            if os.path.exists(dst_package_dir):
                                logger.info(f"【wxautox安装】目标目录已存在，先删除: {dst_package_dir}")
                                shutil.rmtree(dst_package_dir)

                            # 复制包目录
                            logger.info(f"【wxautox安装】复制包目录: {src_package_dir} -> {dst_package_dir}")
                            shutil.copytree(src_package_dir, dst_package_dir)

                            # 记录安装信息
                            self.installed_packages[package_name] = {
                                "wheel_file": wheel_file,
                                "installed_path": dest_wheel_path,
                                "install_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "package_dir": dst_package_dir
                            }

                            package_found = True
                            break

                    # 如果找到了包目录，就不需要继续搜索了
                    if package_found:
                        break

                # 如果没有找到包目录，尝试查找.dist-info目录
                if not package_found:
                    logger.info(f"【wxautox安装】未找到包目录，尝试查找.dist-info目录")
                    dist_info_dirs = []
                    for root, dirs, files in os.walk(temp_dir):
                        for dir_name in dirs:
                            if dir_name.endswith('.dist-info'):
                                dist_info_dirs.append(os.path.join(root, dir_name))

                    if dist_info_dirs:
                        logger.info(f"【wxautox安装】找到.dist-info目录: {dist_info_dirs}")

                        # 复制所有文件到site-packages目录
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                if file.endswith('.py') or file.endswith('.pyd') or file.endswith('.dll'):
                                    src_file = os.path.join(root, file)
                                    rel_path = os.path.relpath(src_file, temp_dir)
                                    dst_file = os.path.join(self.packages_dir, rel_path)

                                    # 确保目标目录存在
                                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)

                                    # 复制文件
                                    logger.info(f"【wxautox安装】复制文件: {src_file} -> {dst_file}")
                                    shutil.copy2(src_file, dst_file)

                        # 记录安装信息
                        self.installed_packages[package_name] = {
                            "wheel_file": wheel_file,
                            "installed_path": dest_wheel_path,
                            "install_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "package_dir": os.path.join(self.packages_dir, package_name)
                        }

                        package_found = True

                # 如果仍然没有找到包，尝试直接复制所有Python文件
                if not package_found:
                    #logger.info(f"【wxautox安装】未找到包目录或.dist-info目录，尝试直接复制所有Python文件")

                    # 创建包目录
                    dst_package_dir = os.path.join(self.packages_dir, package_name)
                    os.makedirs(dst_package_dir, exist_ok=True)

                    # 复制所有Python文件
                    py_files_copied = False
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.endswith('.py') or file.endswith('.pyd') or file.endswith('.dll'):
                                src_file = os.path.join(root, file)
                                dst_file = os.path.join(dst_package_dir, file)

                                # 复制文件
                                #logger.info(f"【wxautox安装】复制文件: {src_file} -> {dst_file}")
                                shutil.copy2(src_file, dst_file)
                                py_files_copied = True

                    if py_files_copied:
                        # 创建__init__.py文件
                        init_file = os.path.join(dst_package_dir, "__init__.py")
                        if not os.path.exists(init_file):
                            #logger.info(f"【wxautox安装】创建__init__.py文件: {init_file}")
                            with open(init_file, 'w') as f:
                                f.write("# Auto-generated __init__.py\n")

                        # 记录安装信息
                        self.installed_packages[package_name] = {
                            "wheel_file": wheel_file,
                            "installed_path": dest_wheel_path,
                            "install_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "package_dir": dst_package_dir
                        }

                        package_found = True

                # 保存安装信息
                if package_found:
                    self._save_installed_packages()
                    #logger.info(f"【wxautox安装】安装成功")
                    return True
                else:
                    #logger.error(f"【wxautox安装】未能找到任何可安装的文件")
                    return False

        except Exception as e:
            logger.error(f"【wxautox安装】安装过程出错: {str(e)}")
            import traceback
            logger.error(f"【wxautox安装】错误详情: {traceback.format_exc()}")
            return False

    def install_dependency(self, package_name):
        """
        安装依赖包

        参数:
            package_name: 包名
        返回:
            成功安装返回True，否则返回False
        """
        #logger.info(f"【wxautox安装】尝试安装依赖包: {package_name}")

        try:
            # 使用pip安装包到指定目录
            cmd = [
                sys.executable,
                "-m", "pip",
                "install",
                "--target", self.packages_dir,
                "--no-cache-dir",
                package_name
            ]
            #logger.info(f"【wxautox安装】执行安装命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                #logger.info(f"【wxautox安装】依赖包 {package_name} 安装成功")
                return True
            else:
                logger.error(f"【wxautox安装】依赖包 {package_name} 安装失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"【wxautox安装】安装依赖包 {package_name} 时出错: {str(e)}")
            return False

    def import_package(self, package_name):
        """
        导入指定的包

        参数:
            package_name: 包名
        返回:
            导入的模块对象，失败则返回None
        """
        if not self.is_package_installed(package_name):
            logger.warning(f"【wxautox安装】包 {package_name} 未安装")
            return None

        # 如果是wxautox，确保依赖项可用
        if package_name == "wxautox":
            # 检查win32ui模块是否可用
            try:
                import win32ui
                #logger.info(f"【wxautox安装】win32ui模块已可用")
            except ImportError:
                logger.warning(f"【wxautox安装】win32ui模块不可用，尝试从PyInstaller环境中查找")

                # 尝试从PyInstaller环境中查找win32ui模块
                pywin32_path = None
                for path in sys.path:
                    if 'pywin32_system32' in path:
                        pywin32_path = os.path.dirname(path)
                        break

                if pywin32_path:
                    #logger.info(f"【wxautox安装】找到PyInstaller环境中的pywin32路径: {pywin32_path}")

                    # 将pywin32路径添加到Python路径
                    win32_path = os.path.join(pywin32_path, 'win32')
                    pywin32_system32_path = os.path.join(pywin32_path, 'pywin32_system32')

                    if win32_path not in sys.path:
                        sys.path.insert(0, win32_path)
                        #logger.info(f"【wxautox安装】已将win32路径添加到Python路径: {win32_path}")

                    if pywin32_system32_path not in sys.path:
                        sys.path.insert(0, pywin32_system32_path)
                        #logger.info(f"【wxautox安装】已将pywin32_system32路径添加到Python路径: {pywin32_system32_path}")

                    # 检查是否有复制的win32文件
                    win32_target = os.path.join(self.packages_dir, 'win32')
                    pywin32_system32_target = os.path.join(self.packages_dir, 'pywin32_system32')

                    if os.path.exists(win32_target) and win32_target not in sys.path:
                        sys.path.insert(0, win32_target)
                        #logger.info(f"【wxautox安装】已将复制的win32路径添加到Python路径: {win32_target}")

                    if os.path.exists(pywin32_system32_target) and pywin32_system32_target not in sys.path:
                        sys.path.insert(0, pywin32_system32_target)
                        #logger.info(f"【wxautox安装】已将复制的pywin32_system32路径添加到Python路径: {pywin32_system32_target}")

        # 尝试导入包
        try:
            # 刷新importlib的缓存以确保能找到新安装的模块
            importlib.invalidate_caches()

            #logger.info(f"【wxautox安装】尝试导入包: {package_name}")
            module = importlib.import_module(package_name)
            #logger.info(f"【wxautox安装】成功导入包: {package_name}")
            return module
        except ImportError as e:
            error_msg = str(e)
            logger.error(f"【wxautox安装】导入 {package_name} 失败: {error_msg}")

            # 检查是否是缺少依赖的问题
            if "No module named" in error_msg:
                # 提取缺少的模块名
                missing_module = error_msg.split("'")[1]
                logger.warning(f"【wxautox安装】检测到缺少依赖模块: {missing_module}")

                # 尝试安装缺少的依赖
                if self.install_dependency(missing_module):
                    #logger.info(f"【wxautox安装】成功安装依赖模块: {missing_module}，重新尝试导入 {package_name}")

                    # 刷新importlib的缓存
                    importlib.invalidate_caches()

                    # 再次尝试导入
                    try:
                        module = importlib.import_module(package_name)
                        #logger.info(f"【wxautox安装】成功导入包: {package_name}")
                        return module
                    except ImportError as e2:
                        logger.error(f"【wxautox安装】安装依赖后仍然无法导入 {package_name}: {str(e2)}")

            # 如果是wxautox导入失败，提供更详细的错误信息
            if package_name == "wxautox":
                logger.error(f"【wxautox安装】wxautox导入失败，可能是缺少依赖模块")

                # 尝试查找wxautox包的具体位置
                package_dir = os.path.join(self.packages_dir, package_name)
                if os.path.exists(package_dir):
                    #logger.info(f"【wxautox安装】wxautox包目录存在: {package_dir}")

                    # 列出包目录中的文件
                    files = os.listdir(package_dir)
                    #logger.info(f"【wxautox安装】wxautox包目录中的文件: {files}")

                    # 检查__init__.py文件
                    init_file = os.path.join(package_dir, "__init__.py")
                    if os.path.exists(init_file):
                        #logger.info(f"【wxautox安装】__init__.py文件存在")

                        # 尝试读取文件内容
                        try:
                            with open(init_file, 'r') as f:
                                content = f.read(1000)  # 只读取前1000个字符
                                #logger.info(f"【wxautox安装】__init__.py文件内容前1000个字符: {content}")

                                # 分析导入语句，找出可能的依赖
                                import re
                                imports = re.findall(r'import\s+(\w+)|from\s+(\w+)', content)
                                potential_deps = set()
                                for imp in imports:
                                    for name in imp:
                                        if name and name not in ['wxauto', 'elements', 'utils', package_name]:
                                            potential_deps.add(name)

                                if potential_deps:
                                    #logger.info(f"【wxautox安装】检测到可能的依赖: {', '.join(potential_deps)}")

                                    # 尝试安装这些依赖
                                    for dep in potential_deps:
                                        if self.install_dependency(dep):
                                            logger.info(f"【wxautox安装】成功安装可能的依赖: {dep}")
                                        else:
                                            logger.warning(f"【wxautox安装】安装可能的依赖失败: {dep}")

                                    # 再次尝试导入
                                    importlib.invalidate_caches()
                                    try:
                                        module = importlib.import_module(package_name)
                                        #logger.info(f"【wxautox安装】安装依赖后成功导入包: {package_name}")
                                        return module
                                    except ImportError as e3:
                                        logger.error(f"【wxautox安装】安装可能的依赖后仍然无法导入 {package_name}: {str(e3)}")
                        except Exception as read_error:
                            logger.error(f"【wxautox安装】读取__init__.py文件失败: {str(read_error)}")
                    else:
                        logger.warning(f"【wxautox安装】__init__.py文件不存在")
                else:
                    logger.warning(f"【wxautox安装】wxautox包目录不存在: {package_dir}")

            return None

    def install_and_import(self, wheel_path, package_name=None):
        """
        安装并导入包

        参数:
            wheel_path: wheel文件路径
            package_name: 可选，包名。如果未提供，将尝试从wheel文件名推断

        返回:
            导入的模块对象，失败则返回None
        """
        # 如果未提供package_name，尝试从wheel文件名推断
        if package_name is None:
            wheel_file = os.path.basename(wheel_path)
            package_name = wheel_file.split('-')[0].replace('_', '-')
            #logger.info(f"【wxautox安装】从文件名推断的包名: {package_name}")

        # 如果包已安装，尝试直接导入
        if self.is_package_installed(package_name):
            #logger.info(f"【wxautox安装】包 {package_name} 已安装，尝试直接导入")
            module = self.import_package(package_name)
            if module:
                return module
            else:
                logger.warning(f"【wxautox安装】包 {package_name} 已安装但导入失败，将尝试重新安装")

        # 安装并导入
        if self.install_wheel(wheel_path):
            #logger.info(f"【wxautox安装】包 {package_name} 安装成功，尝试导入")
            return self.import_package(package_name)

        logger.error(f"【wxautox安装】包 {package_name} 安装失败")
        return None

# 创建全局实例
package_manager = DynamicPackageManager()

def get_package_manager():
    """获取包管理器实例"""
    return package_manager
