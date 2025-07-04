"""
微信自动化库检测模块
统一处理wxauto和wxautox库的检测逻辑，适配开发环境和打包环境
"""

import sys
import os
import subprocess
import importlib
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class WeChatLibDetector:
    """微信自动化库检测器"""
    
    def __init__(self):
        self._detection_cache = {}
        self._is_frozen = getattr(sys, 'frozen', False)
        
    def is_frozen_environment(self) -> bool:
        """检查是否为打包环境"""
        return self._is_frozen
    
    def detect_wxauto(self) -> Tuple[bool, str]:
        """
        检测wxauto库是否可用
        
        Returns:
            Tuple[bool, str]: (是否可用, 详细信息)
        """
        if 'wxauto' in self._detection_cache:
            return self._detection_cache['wxauto']
        
        try:
            # 方法1: 直接导入检测
            import wxauto
            # 尝试访问主要类
            _ = wxauto.WeChat
            result = (True, f"wxauto库可用，版本: {getattr(wxauto, '__version__', '未知')}")
            logger.info("wxauto库检测成功 - 直接导入")
        except ImportError as e:
            result = (False, f"wxauto库导入失败: {str(e)}")
            logger.warning(f"wxauto库检测失败: {str(e)}")
        except AttributeError as e:
            result = (False, f"wxauto库不完整: {str(e)}")
            logger.warning(f"wxauto库不完整: {str(e)}")
        except Exception as e:
            result = (False, f"wxauto库检测时出现未知错误: {str(e)}")
            logger.error(f"wxauto库检测时出现未知错误: {str(e)}")
        
        self._detection_cache['wxauto'] = result
        return result
    
    def detect_wxautox(self) -> Tuple[bool, str]:
        """
        检测wxautox库是否可用

        Returns:
            Tuple[bool, str]: (是否可用, 详细信息)
        """
        if 'wxautox' in self._detection_cache:
            return self._detection_cache['wxautox']

        # 在打包环境中，优先使用直接导入
        if self._is_frozen:
            result = self._detect_wxautox_direct()
        else:
            # 在开发环境中，由于wxautox可能存在I/O冲突，优先使用subprocess
            result = self._detect_wxautox_subprocess()
            # 如果subprocess失败，再尝试直接导入
            if not result[0]:
                result = self._detect_wxautox_direct()

        self._detection_cache['wxautox'] = result
        return result
    
    def _detect_wxautox_direct(self) -> Tuple[bool, str]:
        """直接导入检测wxautox"""
        try:
            # wxautox可能会修改sys.stdout，需要保护标准输出
            import sys
            import io

            # 在打包环境中提供更详细的调试信息
            if self._is_frozen:
                logger.info("打包环境中检测wxautox - 开始直接导入")

                # 检查sys.path中是否有wxautox相关路径
                wxautox_paths = [path for path in sys.path if 'wxautox' in path.lower()]
                if wxautox_paths:
                    logger.info(f"找到wxautox相关路径: {wxautox_paths}")
                else:
                    logger.warning("sys.path中未找到wxautox相关路径")

            # 在打包环境中使用特殊的检测策略
            if self._is_frozen:
                return self._detect_wxautox_frozen_environment()

            # 保存原始的stdout和stderr
            original_stdout = sys.stdout
            original_stderr = sys.stderr

            try:
                # 临时重定向输出，避免wxautox干扰
                sys.stdout = io.StringIO()
                sys.stderr = io.StringIO()

                import wxautox

                # 在打包环境中记录更多信息
                if self._is_frozen:
                    logger.info(f"wxautox模块导入成功，路径: {getattr(wxautox, '__file__', '未知')}")

                # 尝试访问主要类
                wechat_class = wxautox.WeChat

                # 恢复原始输出
                sys.stdout = original_stdout
                sys.stderr = original_stderr

                result = (True, f"wxautox库可用，版本: {getattr(wxautox, '__version__', '未知')}")
                logger.info("wxautox库检测成功 - 直接导入")
                return result

            except Exception as inner_e:
                # 确保恢复原始输出
                sys.stdout = original_stdout
                sys.stderr = original_stderr

                # 在打包环境中提供更详细的错误信息
                if self._is_frozen:
                    logger.error(f"打包环境中wxautox导入内部错误: {str(inner_e)}")
                    logger.error(f"错误类型: {type(inner_e).__name__}")

                raise inner_e

        except ImportError as e:
            error_msg = f"wxautox库导入失败: {str(e)}"
            if self._is_frozen:
                logger.error(f"打包环境中{error_msg}")
                # 检查是否是模块未找到的问题
                if "No module named 'wxautox'" in str(e):
                    error_msg += " (可能wxautox未正确打包到exe中)"
            result = (False, error_msg)
            logger.warning(f"wxautox库直接导入失败: {str(e)}")
            return result
        except AttributeError as e:
            result = (False, f"wxautox库不完整: {str(e)}")
            logger.warning(f"wxautox库不完整: {str(e)}")
            return result
        except Exception as e:
            # 对于I/O错误等问题，记录但不视为致命错误
            if "I/O operation on closed file" in str(e):
                result = (False, f"wxautox库存在I/O冲突，建议使用subprocess检测: {str(e)}")
                logger.warning(f"wxautox库存在I/O冲突: {str(e)}")
            else:
                error_msg = f"wxautox库检测时出现未知错误: {str(e)}"
                if self._is_frozen:
                    logger.error(f"打包环境中{error_msg}")
                result = (False, error_msg)
                logger.error(error_msg)
            return result

    def _detect_wxautox_frozen_environment(self) -> Tuple[bool, str]:
        """在打包环境中使用特殊策略检测wxautox"""
        try:
            import sys
            import io

            logger.info("打包环境中使用安全策略检测wxautox")

            # 在打包环境中使用更安全的检测策略，避免闪退
            try:
                # 保存原始的stdout和stderr
                original_stdout = sys.stdout
                original_stderr = sys.stderr

                # 临时重定向输出，避免wxautox干扰
                sys.stdout = io.StringIO()
                sys.stderr = io.StringIO()

                # 只尝试导入，不创建实例
                import wxautox

                # 恢复原始输出
                sys.stdout = original_stdout
                sys.stderr = original_stderr

                # 检查关键类是否存在
                if hasattr(wxautox, 'WeChat'):
                    logger.info("打包环境中wxautox库导入成功，WeChat类存在")
                    return (True, f"wxautox库可用，版本: {getattr(wxautox, '__version__', '未知')}")
                else:
                    logger.warning("打包环境中wxautox库导入成功但WeChat类不存在")
                    return (False, "wxautox库不完整，WeChat类不存在")

            except ImportError as e:
                logger.info(f"打包环境中wxautox库导入失败: {str(e)}")
                return (False, f"wxautox库导入失败: {str(e)}")
            except Exception as e:
                # 确保恢复原始输出
                try:
                    sys.stdout = original_stdout
                    sys.stderr = original_stderr
                except:
                    pass

                logger.warning(f"打包环境中wxautox检测出错: {str(e)}")
                return (False, f"wxautox库检测出错: {str(e)}")

        except Exception as e:
            logger.error(f"打包环境中wxautox安全检测策略失败: {str(e)}")
            return (False, f"wxautox库检测失败: {str(e)}")

    def _detect_wxautox_frozen_environment_with_timeout(self) -> Tuple[bool, str]:
        """在打包环境中使用超时保护的检测策略"""
        try:
            import threading
            import time

            logger.info("打包环境中使用超时保护策略检测wxautox")

            # 使用线程和超时机制来避免卡住
            result_container = {'result': None, 'error': None}

            def import_wxautox_with_timeout():
                """在单独线程中导入wxautox，避免主线程卡住"""
                try:
                    import io
                    # 保存原始的stdout和stderr
                    original_stdout = sys.stdout
                    original_stderr = sys.stderr

                    try:
                        # 临时重定向输出，避免wxautox干扰
                        sys.stdout = io.StringIO()
                        sys.stderr = io.StringIO()

                        logger.info("步骤1: 尝试导入wxautox主模块（带超时保护）")

                        # 尝试导入wxautox
                        import wxautox

                        # 恢复输出以便记录日志
                        sys.stdout = original_stdout
                        sys.stderr = original_stderr

                        logger.info("步骤1成功: wxautox主模块导入成功")

                        # 重新重定向输出
                        sys.stdout = io.StringIO()
                        sys.stderr = io.StringIO()

                        # 检测关键组件
                        logger.info("步骤2: 检测wxautox.WeChat类")
                        try:
                            wechat_class = wxautox.WeChat
                            logger.info("步骤2成功: wxautox.WeChat类可访问")
                        except AttributeError as attr_e:
                            logger.error(f"步骤2失败: wxautox.WeChat类不存在 - {str(attr_e)}")
                            raise attr_e
                        except Exception as other_e:
                            logger.error(f"步骤2失败: wxautox.WeChat类访问异常 - {type(other_e).__name__}: {str(other_e)}")
                            raise other_e

                        # 恢复原始输出
                        sys.stdout = original_stdout
                        sys.stderr = original_stderr

                        result_container['result'] = (True, "wxautox库在打包环境中可用（基本功能）")
                        logger.info("打包环境中wxautox检测成功 - 使用超时保护策略")

                    except Exception as inner_e:
                        # 确保恢复原始输出
                        sys.stdout = original_stdout
                        sys.stderr = original_stderr

                        logger.error(f"步骤1失败: wxautox主模块导入异常 - {type(inner_e).__name__}: {str(inner_e)}")
                        import traceback
                        logger.error(f"详细错误堆栈: {traceback.format_exc()}")

                        # 分析具体的错误类型
                        if "No module named 'wxautox'" in str(inner_e):
                            result_container['result'] = (False, "wxautox库未正确打包到exe中")
                        elif "DLL load failed" in str(inner_e):
                            result_container['result'] = (False, f"wxautox库DLL依赖问题: {str(inner_e)}")
                        else:
                            result_container['result'] = (False, f"wxautox库导入错误: {str(inner_e)}")

                except Exception as e:
                    result_container['error'] = str(e)

            # 启动导入线程
            import_thread = threading.Thread(target=import_wxautox_with_timeout)
            import_thread.daemon = True
            import_thread.start()

            # 等待最多10秒
            import_thread.join(timeout=10.0)

            if import_thread.is_alive():
                # 线程仍在运行，说明导入卡住了
                logger.error("wxautox导入超时（10秒），可能存在死锁或初始化问题")
                return (False, "wxautox库导入超时，可能存在兼容性问题")

            # 检查结果
            if result_container['result']:
                return result_container['result']
            elif result_container['error']:
                logger.error(f"wxautox导入线程异常: {result_container['error']}")
                return (False, f"wxautox库检测异常: {result_container['error']}")
            else:
                logger.error("wxautox导入线程未返回结果")
                return (False, "wxautox库检测未完成")

        except Exception as e:
            logger.error(f"打包环境中wxautox特殊检测策略失败: {str(e)}")
            return (False, f"wxautox库检测失败: {str(e)}")

    def _detect_wxautox_subprocess(self) -> Tuple[bool, str]:
        """使用subprocess检测wxautox（推荐在开发环境中使用）"""
        try:
            # 使用subprocess检测，避免wxautox的I/O干扰
            result = subprocess.run(
                [sys.executable, "-c", "import wxautox; print('wxautox_import_success')"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=10
            )

            if result.returncode == 0 and "wxautox_import_success" in result.stdout:
                logger.info("wxautox库检测成功 - subprocess")
                return (True, "wxautox库可用 (subprocess检测)")
            else:
                # 分析具体的错误原因
                error_msg = result.stderr.strip() if result.stderr else "未知错误"

                if "ModuleNotFoundError" in error_msg:
                    return (False, "wxautox库未安装，请使用: pip install wxautox")
                elif "ImportError" in error_msg:
                    return (False, f"wxautox库导入错误: {error_msg}")
                else:
                    logger.warning(f"wxautox库subprocess检测失败: {error_msg}")
                    return (False, f"wxautox库不可用: {error_msg}")

        except subprocess.TimeoutExpired:
            logger.warning("wxautox库导入超时")
            return (False, "wxautox库导入超时，可能存在兼容性问题")
        except FileNotFoundError:
            logger.warning("无法找到Python解释器")
            return (False, "无法找到Python解释器，subprocess检测失败")
        except Exception as e:
            logger.warning(f"wxautox库subprocess检测时出现问题: {str(e)}")
            return (False, f"wxautox库subprocess检测失败: {str(e)}")
    
    def check_package_installed(self, package_name: str) -> Tuple[bool, str]:
        """
        仅检查包是否通过pip安装，不实际导入

        Args:
            package_name: 包名

        Returns:
            Tuple[bool, str]: (是否安装, 详细信息)
        """
        try:
            import importlib.util
            import sys

            # 检查包是否在sys.modules中（已导入）
            if package_name in sys.modules:
                return (True, f"{package_name}包已导入")

            # 使用importlib.util.find_spec检查包是否存在
            spec = importlib.util.find_spec(package_name)
            if spec is not None:
                return (True, f"{package_name}包已安装，路径: {spec.origin or '内置模块'}")
            else:
                return (False, f"{package_name}包未安装")

        except Exception as e:
            return (False, f"{package_name}包检查失败: {str(e)}")

    def detect_all_libraries_safe(self) -> Dict[str, Tuple[bool, str]]:
        """
        安全检测所有微信自动化库（仅检查包存在性，不实际导入）

        Returns:
            Dict[str, Tuple[bool, str]]: 库名 -> (是否安装, 详细信息)
        """
        results = {}

        # 仅检查包是否安装，不实际导入
        results['wxauto'] = self.check_package_installed('wxauto')
        results['wxautox'] = self.check_package_installed('wxautox')

        return results

    def detect_all_libraries(self) -> Dict[str, Tuple[bool, str]]:
        """
        检测所有微信自动化库（完整检测，可能导致冲突）

        Returns:
            Dict[str, Tuple[bool, str]]: 库名 -> (是否可用, 详细信息)
        """
        results = {}

        # 检测wxauto
        results['wxauto'] = self.detect_wxauto()

        # 检测wxautox
        results['wxautox'] = self.detect_wxautox()

        return results
    
    def get_available_libraries(self) -> list:
        """
        获取所有可用的库列表
        
        Returns:
            list: 可用的库名列表
        """
        results = self.detect_all_libraries()
        return [lib_name for lib_name, (available, _) in results.items() if available]
    
    def get_preferred_library(self, preference: Optional[str] = None) -> Optional[str]:
        """
        获取首选的库

        Args:
            preference (str, optional): 首选库名

        Returns:
            str: 首选的可用库名，如果没有可用库则返回None
        """
        available_libs = self.get_available_libraries()

        if not available_libs:
            return None

        # 如果指定了首选库且可用，返回首选库
        if preference and preference in available_libs:
            return preference

        # 否则按优先级返回：wxautox > wxauto
        if 'wxautox' in available_libs:
            return 'wxautox'
        elif 'wxauto' in available_libs:
            return 'wxauto'

        return None

    def validate_library_choice(self, lib_name: str) -> Tuple[bool, str]:
        """
        验证库选择是否有效

        Args:
            lib_name (str): 库名

        Returns:
            Tuple[bool, str]: (是否有效, 详细信息)
        """
        if lib_name not in ['wxauto', 'wxautox']:
            return False, f"不支持的库名: {lib_name}，支持的库: wxauto, wxautox"

        available_libs = self.get_available_libraries()
        if lib_name not in available_libs:
            return False, f"库 {lib_name} 不可用，可用的库: {', '.join(available_libs) if available_libs else '无'}"

        return True, f"库 {lib_name} 可用"

    def get_library_switch_recommendation(self, current_lib: str) -> Optional[str]:
        """
        获取库切换建议

        Args:
            current_lib (str): 当前使用的库

        Returns:
            str: 建议切换到的库，如果没有建议则返回None
        """
        available_libs = self.get_available_libraries()

        # 如果当前库不可用，建议切换到可用的库
        if current_lib not in available_libs:
            if available_libs:
                # 优先推荐wxautox，其次wxauto
                if 'wxautox' in available_libs:
                    return 'wxautox'
                elif 'wxauto' in available_libs:
                    return 'wxauto'

        return None
    
    def clear_cache(self):
        """清除检测缓存"""
        self._detection_cache.clear()
        logger.debug("库检测缓存已清除")

    def get_wxautox_detection_strategy(self) -> str:
        """
        获取wxautox的推荐检测策略

        Returns:
            str: 推荐的检测策略描述
        """
        if self._is_frozen:
            return "打包环境: 使用保护性直接导入"
        else:
            return "开发环境: 优先使用subprocess检测，避免I/O冲突"

    def test_wxautox_compatibility(self) -> Dict[str, Tuple[bool, str]]:
        """
        全面测试wxautox的兼容性

        Returns:
            Dict[str, Tuple[bool, str]]: 各种检测方法的结果
        """
        results = {}

        # 测试直接导入
        results['direct'] = self._detect_wxautox_direct()

        # 测试subprocess导入（仅在开发环境）
        if not self._is_frozen:
            results['subprocess'] = self._detect_wxautox_subprocess()

        return results
    
    def get_detection_summary(self) -> str:
        """
        获取检测结果摘要（在打包环境中避免库冲突）

        Returns:
            str: 检测结果摘要
        """
        if self._is_frozen:
            # 在打包环境中，使用安全检测方法，避免同时导入两个库
            results = self.detect_all_libraries_safe()
            summary_lines = [
                f"环境类型: 打包环境",
                "库安装状态:"
            ]

            for lib_name, (installed, details) in results.items():
                status = "✓ 已安装" if installed else "✗ 未安装"
                summary_lines.append(f"  {lib_name}: {status} - {details}")

            # 获取已安装的库
            installed_libs = [lib for lib, (installed, _) in results.items() if installed]
            if installed_libs:
                summary_lines.append(f"已安装库: {', '.join(installed_libs)}")
                summary_lines.append("注意: 为避免库冲突，实际可用性在初始化时确定")
            else:
                summary_lines.append("警告: 没有安装微信自动化库")

            summary_lines.append("打包环境说明: 使用延迟初始化避免库冲突")
        else:
            # 在开发环境中，可以安全地进行完整检测
            results = self.detect_all_libraries()
            summary_lines = [
                f"环境类型: 开发环境",
                "库检测结果:"
            ]

            for lib_name, (available, details) in results.items():
                status = "✓ 可用" if available else "✗ 不可用"
                summary_lines.append(f"  {lib_name}: {status} - {details}")

            available_libs = [lib for lib, (available, _) in results.items() if available]
            if available_libs:
                summary_lines.append(f"可用库: {', '.join(available_libs)}")
            else:
                summary_lines.append("警告: 没有可用的微信自动化库")

        return "\n".join(summary_lines)

    def is_wxautox_io_conflict(self) -> bool:
        """
        检查wxautox是否存在I/O冲突问题

        Returns:
            bool: 是否存在I/O冲突
        """
        if 'wxautox' not in self._detection_cache:
            self.detect_wxautox()

        if 'wxautox' in self._detection_cache:
            available, details = self._detection_cache['wxautox']
            return "I/O operation on closed file" in details

        return False


# 创建全局检测器实例
detector = WeChatLibDetector()
