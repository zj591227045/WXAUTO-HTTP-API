"""
微信自动化库适配器
支持wxauto和wxautox两种库的动态切换
"""

import importlib
import sys
import os
import threading
import time
import pythoncom
import logging
from typing import Optional, Union, List, Dict, Any



# 配置日志
try:
    from app.unified_logger import logger
except ImportError:
    # 如果无法导入统一日志管理器，则创建一个默认的logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("wechat_adapter")

class WeChatAdapter:
    """微信自动化库适配器，支持wxauto和wxautox"""

    def __init__(self, lib_name: str = 'wxauto', lazy_init: bool = False):
        """
        初始化适配器

        Args:
            lib_name: 指定使用的库名称，可选值: 'wxauto', 'wxautox'，默认为'wxauto'
            lazy_init: 是否延迟初始化，如果为True，则不立即导入库
        """
        self._instance = None
        self._lib_name = None
        self._requested_lib_name = lib_name  # 保存请求的库名称
        self._lock = threading.Lock()
        self._listen = {}  # 添加listen属性
        self._cached_window_name = ""  # 添加窗口名称缓存
        self._lazy_init = lazy_init
        self._initialized = False

        # 暂时禁用初始化日志，避免递归调用
        # logger.info(f"初始化WeChatAdapter，请求的库名称: {lib_name}，延迟初始化: {lazy_init}")
        # logger.info(f"当前工作目录: {os.getcwd()}")
        # logger.info(f"Python路径: {sys.path}")

        if not lazy_init:
            # 立即初始化
            self._perform_initialization()
        # else:
            # logger.info("使用延迟初始化模式，将在首次使用时导入库")

    def _perform_initialization(self):
        """执行实际的库导入和初始化"""
        if self._initialized:
            return

        # 根据指定的库名称导入相应的库
        if self._requested_lib_name.lower() == 'wxautox':
            logger.info("尝试导入wxautox库")
            if not self._try_import_wxautox():
                logger.error("无法导入wxautox库，将尝试回退到wxauto")
                if not self._try_import_wxauto():
                    logger.error("无法导入wxauto库")
                    raise ImportError("无法导入wxauto库，请确保已正确安装")
        else:  # 默认使用wxauto
            logger.info("尝试导入wxauto库")
            if not self._try_import_wxauto():
                logger.error("无法导入wxauto库")
                raise ImportError("无法导入wxauto库，请确保已正确安装")

        self._initialized = True
        logger.info(f"使用微信自动化库: {self._lib_name}")

    def _ensure_initialized(self):
        """确保适配器已初始化"""
        if not self._initialized:
            with self._lock:
                if not self._initialized:  # 双重检查
                    self._perform_initialization()

    @property
    def listen(self):
        """获取监听列表"""
        self._ensure_initialized()
        if self._instance:
            # 直接返回实例的listen属性
            return self._instance.listen
        return self._listen

    def _try_import_wxautox(self) -> bool:
        """尝试导入wxautox库"""
        try:
            # 在打包环境中，直接尝试导入，避免使用检测器（防止库冲突）
            import sys
            if getattr(sys, 'frozen', False):
                logger.info("打包环境中直接尝试导入wxautox库")
                try:
                    import wxautox
                    self._lib_name = "wxautox"
                    # 暂时禁用日志管理器更新，避免递归调用
                    # logger.set_lib_name("wxautox")
                    logger.info("成功导入wxautox库（打包环境直接导入）")
                    return True
                except ImportError as e:
                    logger.warning(f"打包环境中wxautox库导入失败: {str(e)}")
                    return False
                except Exception as e:
                    logger.error(f"打包环境中wxautox库导入异常: {str(e)}")
                    return False
            else:
                # 在开发环境中，使用统一的库检测器
                from app.wechat_lib_detector import detector

                available, details = detector.detect_wxautox()
                if available:
                    # 实际导入库
                    import wxautox
                    self._lib_name = "wxautox"
                    # 暂时禁用日志管理器更新，避免递归调用
                    # logger.set_lib_name("wxautox")
                    logger.info(f"成功导入wxautox库: {details}")
                    return True
                else:
                    logger.warning(f"wxautox库不可用: {details}")
                    return False
        except Exception as e:
            logger.error(f"尝试导入wxautox时出现未知错误: {str(e)}")
            return False

    def _try_import_wxauto(self) -> bool:
        """尝试导入wxauto库"""
        try:
            # 在打包环境中，直接尝试导入，避免使用检测器（防止库冲突）
            import sys
            if getattr(sys, 'frozen', False):
                logger.info("打包环境中直接尝试导入wxauto库")
                try:
                    import wxauto
                    self._lib_name = "wxauto"
                    # 暂时禁用日志管理器更新，避免递归调用
                    # logger.set_lib_name("wxauto")
                    logger.info("成功导入wxauto库（打包环境直接导入）")
                    return True
                except ImportError as e:
                    logger.warning(f"打包环境中wxauto库导入失败: {str(e)}")
                    return False
                except Exception as e:
                    logger.error(f"打包环境中wxauto库导入异常: {str(e)}")
                    return False
            else:
                # 在开发环境中，使用统一的库检测器
                from app.wechat_lib_detector import detector

                available, details = detector.detect_wxauto()
                if available:
                    # 实际导入库
                    import wxauto
                    self._lib_name = "wxauto"
                    # 暂时禁用日志管理器更新，避免递归调用
                    # logger.set_lib_name("wxauto")
                    logger.info(f"成功导入wxauto库: {details}")
                    return True
                else:
                    logger.warning(f"wxauto库不可用: {details}")
                    return False
        except Exception as e:
            logger.error(f"尝试导入wxauto时出现未知错误: {str(e)}")
            return False

    def initialize(self) -> bool:
        """初始化微信实例"""
        # 确保适配器已初始化
        self._ensure_initialized()

        with self._lock:
            if not self._instance:
                try:
                    # 初始化COM环境
                    pythoncom.CoInitialize()

                    if self._lib_name == "wxautox":
                        # 直接导入pip安装的wxautox包
                        from wxautox import WeChat
                        self._instance = WeChat()
                    else:  # wxauto
                        # 直接导入pip安装的wxauto包
                        from wxauto import WeChat

                        # 尝试创建WeChat实例，处理可能的Unicode编码错误
                        try:
                            self._instance = WeChat()
                            logger.info("成功创建wxauto.WeChat实例")
                        except UnicodeEncodeError as e:
                            if 'gbk' in str(e).lower():
                                logger.warning(f"捕获到GBK编码错误: {str(e)}")
                                logger.info("尝试修复Unicode编码问题...")

                                # 修补print函数，处理Unicode编码问题
                                original_print = print
                                def safe_print(*args, **kwargs):
                                    try:
                                        original_print(*args, **kwargs)
                                    except UnicodeEncodeError:
                                        # 如果是GBK编码错误，使用UTF-8编码输出
                                        try:
                                            import sys
                                            if hasattr(sys.stdout, 'buffer'):
                                                message = " ".join(str(arg) for arg in args)
                                                sys.stdout.buffer.write(message.encode('utf-8'))
                                                sys.stdout.buffer.write(b'\n')
                                                sys.stdout.buffer.flush()
                                        except Exception:
                                            pass

                                # 替换print函数
                                import builtins
                                builtins.print = safe_print

                                # 再次尝试创建WeChat实例
                                self._instance = WeChat()
                                logger.info("成功创建wxauto.WeChat实例（已修复Unicode编码问题）")
                            else:
                                # 如果不是GBK编码错误，重新抛出
                                raise

                    # 尝试获取窗口名称并保存
                    try:
                        # 在初始化时，WeChat类会自动打印窗口名称，我们需要手动获取
                        if hasattr(self._instance, "window_name"):
                            window_name = self._instance.window_name
                        elif hasattr(self._instance, "GetWindowName"):
                            window_name = self._instance.GetWindowName()
                        else:
                            window_name = ""

                        if window_name:
                            # 保存到缓存
                            self._cached_window_name = window_name
                            logger.info(f"微信实例初始化成功，获取到已登录窗口：{window_name}，使用库: {self._lib_name}")
                        else:
                            logger.info(f"微信实例初始化成功，但无法获取窗口名称，使用库: {self._lib_name}")

                        # 初始化完成后，自动打开"文件传输助手"窗口
                        try:
                            logger.info("正在打开文件传输助手窗口...")
                            self._instance.ChatWith("文件传输助手")
                            import time
                            time.sleep(1)  # 等待窗口打开
                            logger.info("文件传输助手窗口已打开")
                        except Exception as chat_e:
                            logger.error(f"打开文件传输助手窗口失败: {str(chat_e)}")
                    except Exception as e:
                        logger.warning(f"获取窗口名称失败: {str(e)}")
                        logger.info(f"微信实例初始化成功，使用库: {self._lib_name}")

                        # 即使获取窗口名称失败，也尝试打开文件传输助手窗口
                        try:
                            logger.info("正在打开文件传输助手窗口...")
                            self._instance.ChatWith("文件传输助手")
                            import time
                            time.sleep(1)  # 等待窗口打开
                            logger.info("文件传输助手窗口已打开")
                        except Exception as chat_e:
                            logger.error(f"打开文件传输助手窗口失败: {str(chat_e)}")

                    return True
                except Exception as e:
                    logger.error(f"微信初始化失败: {str(e)}")
                    # 出错时确保COM环境被清理
                    pythoncom.CoUninitialize()
                    return False
            return True

    def get_instance(self):
        """获取微信实例"""
        return self._instance

    def get_lib_name(self) -> str:
        """获取当前使用的库名称"""
        return self._lib_name

    def get_window_name(self) -> str:
        """获取微信窗口名称，优先使用缓存"""
        if not self._instance:
            return ""

        try:
            # 尝试多种方法获取窗口名称
            window_name = ""

            # 方法1：尝试从window_name属性获取
            if hasattr(self._instance, "window_name"):
                window_name = getattr(self._instance, "window_name", "")
                logger.debug(f"从window_name属性获取: {window_name}")

            # 方法2：尝试调用GetWindowName方法
            if not window_name and hasattr(self._instance, "GetWindowName"):
                try:
                    window_name = self._instance.GetWindowName()
                    logger.debug(f"从GetWindowName方法获取: {window_name}")
                except Exception as e:
                    logger.debug(f"调用GetWindowName方法失败: {str(e)}")

            # 方法3：尝试从nickname属性获取
            if not window_name and hasattr(self._instance, "nickname"):
                nickname = getattr(self._instance, "nickname", "")
                if nickname:
                    window_name = nickname
                    logger.debug(f"从nickname属性获取: {window_name}")

            # 方法4：尝试获取当前聊天窗口信息
            if not window_name:
                try:
                    chat_info = self._instance.ChatInfo()
                    if chat_info and isinstance(chat_info, dict):
                        # 尝试从聊天信息中获取名称
                        window_name = chat_info.get("nickname", "") or chat_info.get("name", "") or chat_info.get("title", "")
                        logger.debug(f"从ChatInfo方法获取: {window_name}")
                except Exception as e:
                    logger.debug(f"调用ChatInfo方法失败: {str(e)}")

            # 方法5：如果是Plus版本，尝试使用GetMyInfo方法
            if not window_name and self._lib_name == "wxautox":
                try:
                    if hasattr(self._instance, "GetMyInfo"):
                        my_info = self._instance.GetMyInfo()
                        if my_info and isinstance(my_info, dict):
                            window_name = my_info.get("nickname", "") or my_info.get("name", "")
                            logger.debug(f"从GetMyInfo方法获取: {window_name}")
                except Exception as e:
                    logger.debug(f"调用GetMyInfo方法失败: {str(e)}")

            # 如果获取到了新的窗口名称，更新缓存
            if window_name:
                self._cached_window_name = window_name
                logger.debug(f"成功获取窗口名称: {window_name}")
                return window_name

            # 如果没有获取到新的窗口名称，但缓存中有值，使用缓存
            if self._cached_window_name:
                logger.debug(f"使用缓存的窗口名称: {self._cached_window_name}")
                return self._cached_window_name

            # 如果都没有获取到，但微信实例存在，返回一个默认值表示连接正常
            logger.debug("无法获取具体窗口名称，但微信实例存在")
            return "微信"

        except Exception as e:
            logger.warning(f"获取窗口名称失败: {str(e)}")
            # 如果获取失败但缓存中有值，返回缓存
            if self._cached_window_name:
                logger.debug(f"获取失败，使用缓存的窗口名称: {self._cached_window_name}")
                return self._cached_window_name
            # 如果缓存也没有，但微信实例存在，返回默认值
            return "微信"

    def _safe_get_window_name(self) -> str:
        """安全地获取微信窗口名称，避免GetNextSiblingControl错误"""
        try:
            # 优先使用缓存
            if self._cached_window_name:
                return self._cached_window_name

            # 尝试最安全的方法获取窗口名称
            window_name = ""

            # 方法1：尝试从window_name属性获取（最安全）
            if hasattr(self._instance, "window_name"):
                try:
                    window_name = getattr(self._instance, "window_name", "")
                    if window_name:
                        self._cached_window_name = window_name
                        return window_name
                except Exception:
                    pass

            # 方法2：尝试从nickname属性获取（较安全）
            if hasattr(self._instance, "nickname"):
                try:
                    nickname = getattr(self._instance, "nickname", "")
                    if nickname:
                        window_name = nickname
                        self._cached_window_name = window_name
                        return window_name
                except Exception:
                    pass

            # 如果都失败了，返回缓存或默认值
            return self._cached_window_name or "微信"

        except Exception as e:
            logger.debug(f"安全获取窗口名称失败: {str(e)}")
            return self._cached_window_name or ""

    def _safe_get_session_list(self):
        """安全地获取会话列表，避免控件访问错误"""
        try:
            # 检查方法是否存在
            if not hasattr(self._instance, 'GetSessionList'):
                return None

            # 尝试调用GetSessionList方法
            return self._instance.GetSessionList()

        except Exception as e:
            error_str = str(e)
            # 如果是控件相关错误，不记录为错误级别
            if any(keyword in error_str for keyword in ["GetNextSiblingControl", "NoneType", "Control", "uiautomation"]):
                logger.debug(f"控件访问异常，跳过会话列表获取: {error_str}")
            else:
                logger.debug(f"获取会话列表异常: {error_str}")
            return None

    def check_connection(self) -> bool:
        """检查微信连接状态"""
        if not self._instance:
            logger.debug("微信实例未初始化")
            return False

        try:
            # 首先进行基本的实例检查
            if not hasattr(self._instance, '__class__'):
                logger.debug("微信实例对象无效")
                return False

            # 尝试获取窗口名称，这是最基本的检查
            # 使用更安全的方式，避免GetNextSiblingControl错误
            window_name = self._safe_get_window_name()
            logger.debug(f"获取到窗口名称: {window_name}")

            if not window_name:
                logger.debug("无法获取微信窗口名称，可能未登录")
                return False

            # 然后尝试获取会话列表，但不要求必须有会话
            # 使用更安全的方式调用GetSessionList
            try:
                sessions = self._safe_get_session_list()
                logger.debug(f"获取会话列表成功，类型: {type(sessions)}")

                # 只要能成功调用GetSessionList就认为连接正常，即使返回空列表
                if sessions is not None:
                    session_count = len(sessions) if isinstance(sessions, (dict, list)) else 0
                    logger.debug(f"微信连接检查成功，窗口名称: {window_name}, 会话数量: {session_count}")
                    return True
                else:
                    logger.debug("获取会话列表返回None")
                    # 即使会话列表为None，如果有窗口名称也认为连接正常
                    return True
            except Exception as session_e:
                logger.debug(f"获取会话列表失败: {str(session_e)}")
                # 如果获取会话列表失败，但有窗口名称，仍然认为连接正常
                # 因为可能是微信刚登录，还没有会话
                return True

        except Exception as e:
            # 检查是否是GetNextSiblingControl相关的错误
            error_str = str(e)
            if "GetNextSiblingControl" in error_str or "NoneType" in error_str:
                logger.debug(f"检测到控件访问错误，可能是微信窗口状态异常: {error_str}")
                # 对于这类错误，我们认为连接暂时不可用，但不记录为错误
                return False
            else:
                logger.debug(f"微信连接检查失败: {str(e)}")
                return False

    def __getattr__(self, name):
        """代理到实际的微信实例 - 简化版本，避免递归调用"""
        if self._instance is None:
            raise AttributeError(f"微信实例未初始化，无法调用 {name} 方法")

        # 直接代理到实际实例，暂时禁用所有特殊处理
        try:
            return getattr(self._instance, name)
        except AttributeError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def _handle_ChatWith(self, *args, **kwargs):
        """处理ChatWith方法的差异"""
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        # wxautox的ChatWith方法支持exact参数，而wxauto不支持
        if self._lib_name == "wxauto":
            # 从kwargs中移除exact参数，如果存在的话
            if 'exact' in kwargs:
                kwargs.pop("exact")

            # 调用原始方法
            result = self._instance.ChatWith(*args, **kwargs)
            return result
        else:
            # 直接调用原始方法
            return self._instance.ChatWith(*args, **kwargs)

    def _handle_SendMsg(self, *args, **kwargs):
        """处理SendMsg方法的差异"""
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        # wxauto和wxautox的SendMsg方法参数略有不同
        if self._lib_name == "wxauto":
            # wxauto的clear参数是布尔值，而wxautox是字符串
            if "clear" in kwargs and isinstance(kwargs["clear"], bool):
                kwargs["clear"] = "1" if kwargs["clear"] else "0"

        # 调用原始方法
        return self._instance.SendMsg(*args, **kwargs)

    def _handle_SendTypingText(self, *args, **kwargs):
        """处理SendTypingText方法的差异"""
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        # 检查库是否支持SendTypingText方法
        if self._lib_name == "wxautox":
            # wxautox支持SendTypingText方法
            if hasattr(self._instance, 'SendTypingText'):
                return self._instance.SendTypingText(*args, **kwargs)
            else:
                # 如果没有SendTypingText方法，使用SendMsg代替
                logger.warning("wxautox实例没有SendTypingText方法，使用SendMsg代替")
                return self._instance.SendMsg(*args, **kwargs)
        else:
            # wxauto不支持SendTypingText方法，使用SendMsg代替
            logger.debug("wxauto库不支持SendTypingText方法，使用SendMsg代替")
            # wxauto的clear参数是布尔值，而wxautox是字符串
            if "clear" in kwargs and isinstance(kwargs["clear"], bool):
                kwargs["clear"] = "1" if kwargs["clear"] else "0"
            return self._instance.SendMsg(*args, **kwargs)

    def _handle_SendFiles(self, *args, **kwargs):
        """处理SendFiles方法的差异"""
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        # 检查库是否支持SendFiles方法
        if hasattr(self._instance, 'SendFiles'):
            logger.debug(f"调用{self._lib_name}的SendFiles方法")
            return self._instance.SendFiles(*args, **kwargs)
        else:
            # 如果没有SendFiles方法，尝试使用SendFile方法
            if hasattr(self._instance, 'SendFile'):
                logger.debug(f"{self._lib_name}没有SendFiles方法，使用SendFile代替")
                return self._instance.SendFile(*args, **kwargs)
            else:
                logger.error(f"{self._lib_name}既没有SendFiles也没有SendFile方法")
                raise AttributeError(f"{self._lib_name}不支持文件发送功能")

    def _handle_GetNextNewMessage(self, *args, **kwargs):
        """处理GetNextNewMessage方法的参数兼容性和独立实现"""
        """处理GetNextNewMessage方法的差异"""
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        # 只有在使用wxauto库时才需要设置保存路径
        logger.debug(f"_handle_GetNextNewMessage: 当前库名称 = {self._lib_name}")
        if self._lib_name == "wxauto":
            # 确保使用正确的保存路径
            try:
                # 导入配置管理器
                import config_manager

                # 尝试导入wxauto.elements模块
                try:
                    # 首先尝试直接导入
                    from wxauto.elements import WxParam
                    logger.debug("成功直接导入wxauto.elements.WxParam")
                except ImportError as e:
                    logger.warning(f"直接导入wxauto.elements.WxParam失败: {str(e)}")

                    # 尝试使用与_try_import_wxauto相同的逻辑查找wxauto路径
                    import sys
                    import os

                    # 获取应用根目录
                    if getattr(sys, 'frozen', False):
                        # 如果是打包后的环境
                        app_root = os.path.dirname(sys.executable)
                        meipass = getattr(sys, '_MEIPASS', None)
                    else:
                        # 如果是开发环境
                        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                    # 尝试多种可能的wxauto路径
                    possible_paths = [
                        os.path.join(app_root, "wxauto"),
                        os.path.join(app_root, "app", "wxauto"),
                    ]

                    # 如果是打包环境，添加更多可能的路径
                    if getattr(sys, 'frozen', False) and meipass:
                        possible_paths.extend([
                            os.path.join(meipass, "wxauto"),
                            os.path.join(meipass, "app", "wxauto"),
                        ])

                    # 尝试从每个路径导入
                    WxParam = None
                    for wxauto_path in possible_paths:
                        if os.path.exists(wxauto_path) and os.path.isdir(wxauto_path):
                            # 检查wxauto路径下是否有wxauto子目录
                            wxauto_inner_path = os.path.join(wxauto_path, "wxauto")
                            elements_path = os.path.join(wxauto_inner_path, "elements.py")

                            if os.path.exists(elements_path):
                                logger.debug(f"找到elements.py文件: {elements_path}")

                                # 将wxauto/wxauto目录添加到路径
                                if wxauto_inner_path not in sys.path:
                                    sys.path.insert(0, wxauto_inner_path)

                                # 将wxauto目录添加到路径
                                if wxauto_path not in sys.path:
                                    sys.path.insert(0, wxauto_path)

                                try:
                                    # 尝试导入
                                    from wxauto.elements import WxParam
                                    logger.debug(f"成功从路径导入wxauto.elements.WxParam: {wxauto_path}")
                                    break
                                except ImportError as inner_e:
                                    logger.warning(f"从路径 {wxauto_path} 导入wxauto.elements.WxParam失败: {str(inner_e)}")

                    # 如果仍然无法导入，抛出异常
                    if WxParam is None:
                        raise ImportError("无法导入wxauto.elements.WxParam")

                # 确保目录存在
                config_manager.ensure_dirs()

                # 获取临时目录路径
                temp_dir = str(config_manager.TEMP_DIR.absolute())

                # 记录原始保存路径
                original_path = WxParam.DEFALUT_SAVEPATH
                logger.debug(f"原始wxauto保存路径: {original_path}")

                # 修改为新的保存路径
                WxParam.DEFALUT_SAVEPATH = temp_dir
                logger.debug(f"已修改wxauto保存路径为: {temp_dir}")
            except Exception as path_e:
                logger.error(f"设置wxauto保存路径失败: {str(path_e)}")
        else:
            logger.debug(f"使用{self._lib_name}库，跳过wxauto保存路径设置")

        # 根据不同的库调整参数
        if self._lib_name == "wxautox":
            # wxautox的GetNextNewMessage方法参数格式
            # 根据文档，wxautox只接受filter_mute参数
            logger.debug("使用wxautox库，调整参数格式")

            # 移除wxauto特有的参数，只保留filter_mute
            adjusted_kwargs = {}
            if 'filter_mute' in kwargs:
                adjusted_kwargs['filter_mute'] = kwargs['filter_mute']
            else:
                # 默认不过滤免打扰消息
                adjusted_kwargs['filter_mute'] = False

            logger.debug(f"wxautox调整后的参数: {adjusted_kwargs}")

            try:
                # 添加详细的调试信息
                logger.info(f"=== wxautox GetNextNewMessage 调试开始 ===")
                logger.info(f"调用参数: {adjusted_kwargs}")

                # 检查实例状态
                logger.info(f"微信实例类型: {type(self._instance)}")
                logger.info(f"微信实例是否有GetNextNewMessage方法: {hasattr(self._instance, 'GetNextNewMessage')}")

                # 检查监听状态
                if hasattr(self._instance, 'listen'):
                    listen_info = getattr(self._instance, 'listen', {})
                    logger.info(f"当前监听对象: {list(listen_info.keys()) if listen_info else '无'}")
                else:
                    logger.info("实例没有listen属性")

                # 新策略：直接从我们的消息缓存中获取消息，不调用原始的GetNextNewMessage
                logger.info("使用自定义缓存获取消息，避免GetNextNewMessage的阻塞问题...")

                # 检查是否有消息缓存
                if not hasattr(self, '_message_cache') or not self._message_cache:
                    logger.info("消息缓存为空，返回空结果")
                    return {}

                # 获取所有缓存的消息并清空缓存（避免重复获取）
                cached_messages = {}
                for chat_name, messages in self._message_cache.items():
                    if messages:  # 只返回有消息的聊天
                        cached_messages[chat_name] = messages.copy()
                        logger.info(f"从缓存获取到 {len(messages)} 条来自 {chat_name} 的消息")

                # 清空缓存（已读取的消息不再重复返回）
                self._message_cache.clear()
                logger.info("已清空消息缓存")

                if cached_messages:
                    # 转换为wxautox格式的返回结果
                    # wxautox返回格式: {'chat_name': 'name', 'chat_type': 'type', 'msg': [messages]}
                    for chat_name, messages in cached_messages.items():
                        logger.info(f"返回 {chat_name} 的 {len(messages)} 条消息")
                        # 返回第一个聊天的消息（如果有多个聊天，可以后续优化）
                        result = {
                            'chat_name': chat_name,
                            'chat_type': 'friend',  # 暂时假设是好友，后续可以优化
                            'msg': messages
                        }
                        logger.info(f"=== wxautox GetNextNewMessage 调试结束 ===")
                        return result

                logger.info("缓存中没有新消息，返回空结果")
                logger.info(f"=== wxautox GetNextNewMessage 调试结束 ===")
                return {}

            except Exception as e:
                error_str = str(e)
                logger.error(f"=== wxautox GetNextNewMessage 异常 ===")
                logger.error(f"异常类型: {type(e)}")
                logger.error(f"异常信息: {error_str}")
                logger.error(f"=== 异常详情结束 ===")
                return {}
        else:
            # wxauto不支持savevideo和parseurl参数
            # 从kwargs中移除不支持的参数
            if "savevideo" in kwargs:
                logger.debug("移除wxauto不支持的参数: savevideo")
                kwargs.pop("savevideo", None)
            if "parseurl" in kwargs:
                logger.debug("移除wxauto不支持的参数: parseurl")
                kwargs.pop("parseurl", None)

            try:
                # 直接调用原始方法，不使用任何缓存机制
                logger.debug(f"调用wxauto GetNextNewMessage方法，参数: {kwargs}")
                result = self._instance.GetNextNewMessage(*args, **kwargs)
                logger.debug(f"wxauto GetNextNewMessage返回结果: {type(result)}, 内容: {result}")
                return result if result else []

            except Exception as e:
                error_str = str(e)
                logger.debug(f"wxauto GetNextNewMessage调用失败: {error_str}")

                # 如果是"没有新消息"相关的错误，返回空结果
                if "没有新消息" in error_str or "no new message" in error_str.lower():
                    logger.debug("wxauto没有新消息")
                    return []

                # 其他错误也返回空列表
                logger.warning(f"wxauto GetNextNewMessage其他错误: {error_str}")
                return []



    # 彻底删除AddListenChat处理逻辑 - 统一使用直接调用
    def _handle_AddListenChat_COMPLETELY_REMOVED(self, *args, **kwargs):
        """处理AddListenChat方法的差异 - 简化版本，完全按照文档使用"""
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        # 初始化消息缓存（如果还没有）
        if not hasattr(self, '_message_cache'):
            self._message_cache = {}
            logger.debug("初始化消息缓存")

        # 根据不同的库处理参数
        if self._lib_name == "wxautox":
            # wxautox的AddListenChat方法需要nickname和callback参数
            logger.debug("使用wxautox库，调整AddListenChat参数格式")

            # 从kwargs中获取nickname或who参数
            who = kwargs.get('nickname') or kwargs.get('who') or (args[0] if args else None)
            logger.debug(f"AddListenChat参数检查: nickname={kwargs.get('nickname')}, who={kwargs.get('who')}, args={args}")
            if not who:
                raise ValueError("缺少必要参数: who/nickname")

            # 创建回调函数，将消息存储到我们自己的缓存中
            def message_callback(msg, chat):
                """消息回调函数，存储消息到缓存"""
                try:
                    logger.info(f"=== 收到新消息回调 ===")
                    logger.info(f"消息对象类型: {type(msg)}")
                    logger.info(f"聊天对象类型: {type(chat)}")
                    logger.info(f"聊天对象内容: {chat}")

                    # 获取消息内容
                    content = getattr(msg, 'content', str(msg))
                    sender = getattr(msg, 'sender', '未知发送者')
                    msg_type = getattr(msg, 'type', '未知类型')
                    msg_id = getattr(msg, 'id', '')
                    timestamp = getattr(msg, 'timestamp', None)

                    logger.info(f"消息发送者: {sender}")
                    logger.info(f"消息类型: {msg_type}")
                    logger.info(f"消息内容: {content[:100]}...")

                    # 获取聊天名称
                    chat_name = str(chat) if hasattr(chat, '__str__') else getattr(chat, 'who', str(chat))

                    # 清理群名中的人数信息
                    import re
                    clean_name = re.sub(r'\s*\(\d+\)$', '', chat_name)

                    # 初始化该聊天的消息列表
                    if clean_name not in self._message_cache:
                        self._message_cache[clean_name] = []

                    # 将消息添加到缓存
                    msg_data = {
                        'type': msg_type,
                        'content': content,
                        'sender': sender,
                        'id': msg_id,
                        'timestamp': timestamp,
                        'mtype': getattr(msg, 'mtype', None),
                        'sender_remark': getattr(msg, 'sender_remark', None),
                        'file_path': getattr(msg, 'file_path', None)
                    }

                    self._message_cache[clean_name].append(msg_data)
                    logger.info(f"消息已缓存到 {clean_name}: {content[:50]}...")

                    # 限制缓存大小，保留最新的100条消息
                    if len(self._message_cache[clean_name]) > 100:
                        self._message_cache[clean_name] = self._message_cache[clean_name][-100:]

                    logger.info(f"=== 消息回调结束 ===")
                except Exception as e:
                    logger.error(f"回调函数处理消息时出错: {str(e)}")
                    logger.error(f"异常类型: {type(e)}")
                    import traceback
                    logger.error(f"异常堆栈: {traceback.format_exc()}")

            # 调用wxautox的AddListenChat方法，使用正确的参数格式
            try:
                logger.info(f"=== wxautox AddListenChat 调试开始 ===")
                logger.info(f"目标监听对象: {who}")
                logger.info(f"微信实例类型: {type(self._instance)}")
                logger.info(f"微信实例是否有AddListenChat方法: {hasattr(self._instance, 'AddListenChat')}")

                # 检查当前监听状态
                if hasattr(self._instance, 'listen'):
                    current_listen = getattr(self._instance, 'listen', {})
                    logger.info(f"添加前的监听对象: {list(current_listen.keys()) if current_listen else '无'}")

                logger.info("开始调用AddListenChat...")
                result = self._instance.AddListenChat(nickname=who, callback=message_callback)
                logger.info(f"AddListenChat调用完成，返回结果: {result}")

                # 检查添加后的监听状态
                if hasattr(self._instance, 'listen'):
                    updated_listen = getattr(self._instance, 'listen', {})
                    logger.info(f"添加后的监听对象: {list(updated_listen.keys()) if updated_listen else '无'}")

                # 根据文档要求，添加监听后必须调用StartListening
                try:
                    if hasattr(self._instance, 'StartListening'):
                        logger.info("开始调用StartListening...")
                        self._instance.StartListening()
                        logger.info(f"StartListening调用完成，已自动启动监听服务")
                    else:
                        logger.warning("当前库不支持StartListening方法")
                except Exception as start_e:
                    logger.error(f"自动启动监听失败: {str(start_e)}")

                logger.info(f"=== wxautox AddListenChat 调试结束 ===")
                return result
            except Exception as e:
                logger.error(f"=== wxautox AddListenChat 异常 ===")
                logger.error(f"异常类型: {type(e)}")
                logger.error(f"异常信息: {str(e)}")
                logger.error(f"=== 异常详情结束 ===")
                raise
        else:
            # wxauto库的处理
            # wxauto不支持savevideo和parseurl参数
            if "savevideo" in kwargs:
                logger.debug("移除wxauto不支持的参数: savevideo")
                kwargs.pop("savevideo", None)
            if "parseurl" in kwargs:
                logger.debug("移除wxauto不支持的参数: parseurl")
                kwargs.pop("parseurl", None)

            try:
                # 调用原始方法
                logger.debug(f"调用AddListenChat方法，参数: {kwargs}")
                result = self._instance.AddListenChat(*args, **kwargs)

                # 自动启动监听
                try:
                    if hasattr(self._instance, 'StartListening'):
                        self._instance.StartListening()
                        logger.info(f"已自动启动监听服务")
                    else:
                        logger.warning("当前库不支持StartListening方法")
                except Exception as start_e:
                    logger.warning(f"自动启动监听失败: {str(start_e)}")

                return result
            except Exception as e:
                logger.error(f"调用AddListenChat方法失败: {str(e)}")
                # 如果是参数错误，尝试使用最基本的参数重试
                if "参数" in str(e) or "parameter" in str(e).lower() or "argument" in str(e).lower() or "unexpected keyword" in str(e).lower():
                    logger.warning("可能是参数错误，尝试使用基本参数重试")
                    # 只保留基本参数
                    basic_kwargs = {}
                    if "who" in kwargs:
                        basic_kwargs["who"] = kwargs["who"]

                    # wxauto支持的基本参数
                    if "savepic" in kwargs:
                        basic_kwargs["savepic"] = kwargs["savepic"]
                    if "savefile" in kwargs:
                        basic_kwargs["savefile"] = kwargs["savefile"]
                    if "savevoice" in kwargs:
                        basic_kwargs["savevoice"] = kwargs["savevoice"]

                    logger.debug(f"使用基本参数重试: {basic_kwargs}")
                    result = self._instance.AddListenChat(*args, **basic_kwargs)

                    # 自动启动监听（重试成功后）
                    try:
                        if hasattr(self._instance, 'StartListening'):
                            self._instance.StartListening()
                            logger.info(f"已自动启动监听服务")
                        else:
                            logger.warning("当前库不支持StartListening方法")
                    except Exception as start_e:
                        logger.warning(f"自动启动监听失败: {str(start_e)}")

                    return result
                # 重新抛出原始异常
                raise

    # 删除复杂的GetListenMessage处理逻辑 - 统一使用直接调用
    def _handle_GetListenMessage_DELETED(self, *args, **kwargs):
        """处理GetListenMessage方法的差异，并添加异常处理"""
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        # 只有在使用wxauto库时才需要设置保存路径
        logger.debug(f"_handle_GetListenMessage: 当前库名称 = {self._lib_name}")
        if self._lib_name == "wxauto":
            # 确保使用正确的保存路径
            try:
                # 导入配置管理器
                import config_manager

                # 尝试导入wxauto.elements模块
                try:
                    # 首先尝试直接导入
                    from wxauto.elements import WxParam
                    logger.debug("成功直接导入wxauto.elements.WxParam")
                except ImportError as e:
                    logger.warning(f"直接导入wxauto.elements.WxParam失败: {str(e)}")

                # 尝试使用与_try_import_wxauto相同的逻辑查找wxauto路径
                import sys
                import os

                # 获取应用根目录
                if getattr(sys, 'frozen', False):
                    # 如果是打包后的环境
                    app_root = os.path.dirname(sys.executable)
                    meipass = getattr(sys, '_MEIPASS', None)
                else:
                    # 如果是开发环境
                    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                # 尝试多种可能的wxauto路径
                possible_paths = [
                    os.path.join(app_root, "wxauto"),
                    os.path.join(app_root, "app", "wxauto"),
                ]

                # 如果是打包环境，添加更多可能的路径
                if getattr(sys, 'frozen', False) and meipass:
                    possible_paths.extend([
                        os.path.join(meipass, "wxauto"),
                        os.path.join(meipass, "app", "wxauto"),
                    ])

                # 尝试从每个路径导入
                WxParam = None
                for wxauto_path in possible_paths:
                    if os.path.exists(wxauto_path) and os.path.isdir(wxauto_path):
                        # 检查wxauto路径下是否有wxauto子目录
                        wxauto_inner_path = os.path.join(wxauto_path, "wxauto")
                        elements_path = os.path.join(wxauto_inner_path, "elements.py")

                        if os.path.exists(elements_path):
                            logger.debug(f"找到elements.py文件: {elements_path}")

                            # 将wxauto/wxauto目录添加到路径
                            if wxauto_inner_path not in sys.path:
                                sys.path.insert(0, wxauto_inner_path)

                            # 将wxauto目录添加到路径
                            if wxauto_path not in sys.path:
                                sys.path.insert(0, wxauto_path)

                            try:
                                # 尝试导入
                                from wxauto.elements import WxParam
                                logger.debug(f"成功从路径导入wxauto.elements.WxParam: {wxauto_path}")
                                break
                            except ImportError as inner_e:
                                logger.warning(f"从路径 {wxauto_path} 导入wxauto.elements.WxParam失败: {str(inner_e)}")

                # 如果仍然无法导入，抛出异常
                if WxParam is None:
                    raise ImportError("无法导入wxauto.elements.WxParam")

                # 确保目录存在
                config_manager.ensure_dirs()

                # 获取临时目录路径
                temp_dir = str(config_manager.TEMP_DIR.absolute())

                # 记录原始保存路径
                original_path = WxParam.DEFALUT_SAVEPATH
                logger.debug(f"原始wxauto保存路径: {original_path}")

                # 修改为新的保存路径
                WxParam.DEFALUT_SAVEPATH = temp_dir
                logger.debug(f"已修改wxauto保存路径为: {temp_dir}")
            except Exception as path_e:
                logger.error(f"设置wxauto保存路径失败: {str(path_e)}")
        else:
            logger.debug(f"使用{self._lib_name}库，跳过wxauto保存路径设置")

        # 根据不同的库使用不同的处理方法
        if self._lib_name == "wxautox":
            # 对于wxautox库，使用GetNewMessage方法
            try:
                who = args[0] if args else kwargs.get('who')

                # 记录调用信息，帮助调试
                logger.debug(f"调用wxautox GetNewMessage，参数: who={who}")

                # wxautox使用GetNewMessage方法获取新消息
                if who:
                    # 如果指定了who参数，获取特定聊天对象的消息
                    result = self._instance.GetNewMessage(who)
                else:
                    # 如果没有指定who参数，获取所有新消息
                    result = self._instance.GetNewMessage()

                # 记录返回类型，帮助调试
                logger.debug(f"wxautox GetNewMessage返回类型: {type(result)}")

                # 确保返回格式一致
                if result is None:
                    return {} if not who else []

                return result
            except Exception as e:
                # 捕获所有异常，避免崩溃
                import traceback
                logger.error(f"wxautox获取监听消息失败: {str(e)}")
                logger.error(f"错误详情: {traceback.format_exc()}")
                # 返回空字典或空列表，表示没有新消息
                return {} if not who else []
        else:
            # 对于wxauto库，使用更健壮的处理方法
            try:
                # wxauto的GetListenMessage只接受who参数，移除其他参数
                who = args[0] if args else kwargs.get('who')

                # 不再手动激活窗口，直接使用wxauto库的内置功能
                # wxauto的GetListenMessage方法内部会调用chat._show()来激活窗口
                logger.debug(f"使用wxauto库内置功能激活聊天窗口: {who if who else '所有窗口'}")

                # 不主动检测窗口句柄是否有效，直接尝试获取消息

                # 调用原始方法，只传递who参数
                if who:
                    result = self._instance.GetListenMessage(who)
                else:
                    result = self._instance.GetListenMessage()

                # 记录返回类型，帮助调试
                logger.debug(f"wxauto GetListenMessage返回类型: {type(result)}")

                # 检查是否指定了who参数
                who = args[0] if args else kwargs.get('who')

                # 如果指定了who参数且返回的是列表，这是正常的
                if who and isinstance(result, list):
                    logger.debug(f"wxauto GetListenMessage为{who}返回了列表，长度: {len(result)}")
                    return result
                # 如果没有指定who参数且返回的是字典，这是正常的
                elif not who and isinstance(result, dict):
                    logger.debug(f"wxauto GetListenMessage返回了字典，键数量: {len(result)}")
                    return result
                # 如果返回的是空值，这是正常的
                elif not result:
                    logger.debug("wxauto GetListenMessage返回了空值")
                    return {}
                # 其他情况可能是异常的
                else:
                    logger.warning(f"wxauto GetListenMessage返回了意外的类型: {type(result)}")
                    # 尝试转换为适当的格式
                    if isinstance(result, list) and not who:
                        # 如果没有指定who参数但返回了列表，尝试转换为字典
                        logger.warning("尝试将列表转换为字典")
                        return {}
                    elif isinstance(result, dict) and who:
                        # 如果指定了who参数但返回了字典，尝试提取相关消息
                        logger.warning("尝试从字典中提取指定聊天对象的消息")
                        for chat_wnd, msg_list in result.items():
                            if hasattr(chat_wnd, 'who') and chat_wnd.who == who:
                                return msg_list
                        return []
                    else:
                        # 无法处理的情况，返回空值
                        logger.error(f"无法处理的返回类型: {type(result)}")
                        return {} if not who else []

            except Exception as e:
                # 捕获所有异常，避免崩溃
                import traceback
                error_str = str(e)
                logger.error(f"wxauto获取监听消息失败: {error_str}")
                traceback.print_exc()

                # 检查是否是窗口激活失败的错误
                if "激活聊天窗口失败" in error_str or "SetWindowPos" in error_str or "无效的窗口句柄" in error_str or "Find Control Timeout" in error_str:
                    # 获取who参数
                    who = args[0] if args else kwargs.get('who')

                    if who:
                        logger.warning(f"检测到窗口激活失败，尝试重新添加监听对象: {who}")
                        try:
                            # 先尝试移除可能存在的无效监听对象
                            try:
                                self.RemoveListenChat(who)
                                logger.info(f"已移除无效的监听对象: {who}")
                            except Exception as remove_e:
                                logger.warning(f"移除无效监听对象失败: {str(remove_e)}")

                            # 尝试先打开聊天窗口
                            try:
                                self.ChatWith(who)
                                logger.info(f"已打开聊天窗口: {who}")
                                # 等待窗口打开
                                import time
                                time.sleep(0.5)
                            except Exception as chat_e:
                                logger.warning(f"打开聊天窗口失败: {str(chat_e)}")

                            # 重新添加监听对象
                            # 构建基本参数
                            add_params = {'who': who}
                            if 'savepic' in kwargs:
                                add_params['savepic'] = kwargs['savepic']
                            if 'savefile' in kwargs:
                                add_params['savefile'] = kwargs['savefile']
                            if 'savevoice' in kwargs:
                                add_params['savevoice'] = kwargs['savevoice']

                            self.AddListenChat(**add_params)
                            logger.info(f"已重新添加监听对象: {who}")

                            # 再次尝试获取消息
                            if who:
                                result = self._instance.GetNewMessage(who) if self._lib_name == "wxautox" else self._instance.GetListenMessage(who)
                            else:
                                result = self._instance.GetNewMessage() if self._lib_name == "wxautox" else self._instance.GetListenMessage()
                            return result
                        except Exception as retry_e:
                            logger.error(f"重新添加监听对象后获取消息仍然失败: {str(retry_e)}")
                    else:
                        # 如果没有指定who参数，尝试处理所有监听对象
                        logger.warning("未指定who参数，尝试处理所有监听对象")
                        try:
                            # 获取当前所有监听对象
                            listen_list = {}
                            try:
                                listen_list = self._instance.listen.copy()  # 复制一份以避免迭代过程中修改
                            except Exception as list_e:
                                logger.error(f"获取监听列表失败: {str(list_e)}")
                                return {}

                            # 如果监听列表为空，直接返回
                            if not listen_list:
                                logger.warning("监听列表为空")
                                return {}

                            # 遍历所有监听对象，尝试重新添加
                            for chat_who, chat_obj in listen_list.items():
                                try:
                                    # 先移除
                                    try:
                                        self.RemoveListenChat(chat_who)
                                        logger.info(f"已移除可能无效的监听对象: {chat_who}")
                                    except Exception as remove_e:
                                        logger.warning(f"移除监听对象失败: {str(remove_e)}")

                                    # 尝试先打开聊天窗口
                                    try:
                                        self.ChatWith(chat_who)
                                        logger.info(f"已打开聊天窗口: {chat_who}")
                                        # 等待窗口打开
                                        import time
                                        time.sleep(0.5)
                                    except Exception as chat_e:
                                        logger.warning(f"打开聊天窗口失败: {str(chat_e)}")

                                    # 重新添加
                                    chat_params = {
                                        'who': chat_who,
                                        'savepic': getattr(chat_obj, 'savepic', False),
                                        'savefile': getattr(chat_obj, 'savefile', False),
                                        'savevoice': getattr(chat_obj, 'savevoice', False)
                                    }
                                    self.AddListenChat(**chat_params)
                                    logger.info(f"已重新添加监听对象: {chat_who}")
                                except Exception as chat_e:
                                    logger.error(f"重新添加监听对象 {chat_who} 失败: {str(chat_e)}")
                                    continue

                            # 重新尝试获取所有监听对象的消息
                            try:
                                result = self._instance.GetNewMessage() if self._lib_name == "wxautox" else self._instance.GetListenMessage()
                                return result
                            except Exception as retry_e:
                                logger.error(f"重新添加所有监听对象后获取消息仍然失败: {str(retry_e)}")
                        except Exception as all_e:
                            logger.error(f"处理所有监听对象失败: {str(all_e)}")
                elif "激活聊天窗口失败" in traceback.format_exc() or "SetWindowPos" in traceback.format_exc() or "无效的窗口句柄" in traceback.format_exc():
                    # 获取who参数
                    who = args[0] if args else kwargs.get('who')

                    if who:
                        logger.warning(f"从堆栈跟踪中检测到窗口激活失败，尝试重新添加监听对象: {who}")
                        try:
                            # 先尝试移除可能存在的无效监听对象
                            try:
                                self.RemoveListenChat(who)
                                logger.info(f"已移除无效的监听对象: {who}")
                            except Exception as remove_e:
                                logger.warning(f"移除无效监听对象失败: {str(remove_e)}")

                            # 尝试先打开聊天窗口
                            try:
                                self.ChatWith(who)
                                logger.info(f"已打开聊天窗口: {who}")
                                # 等待窗口打开
                                import time
                                time.sleep(0.5)
                            except Exception as chat_e:
                                logger.warning(f"打开聊天窗口失败: {str(chat_e)}")

                            # 重新添加监听对象
                            # 构建基本参数
                            add_params = {'who': who}
                            if 'savepic' in kwargs:
                                add_params['savepic'] = kwargs['savepic']
                            if 'savefile' in kwargs:
                                add_params['savefile'] = kwargs['savefile']
                            if 'savevoice' in kwargs:
                                add_params['savevoice'] = kwargs['savevoice']

                            self.AddListenChat(**add_params)
                            logger.info(f"已重新添加监听对象: {who}")

                            # 再次尝试获取消息
                            if who:
                                result = self._instance.GetNewMessage(who) if self._lib_name == "wxautox" else self._instance.GetListenMessage(who)
                            else:
                                result = self._instance.GetNewMessage() if self._lib_name == "wxautox" else self._instance.GetListenMessage()
                            return result
                        except Exception as retry_e:
                            logger.error(f"重新添加监听对象后获取消息仍然失败: {str(retry_e)}")

                # 根据是否指定了who参数返回不同的空值
                who = args[0] if args else kwargs.get('who')
                return [] if who else {}

    # 删除复杂的RemoveListenChat处理逻辑 - 统一使用直接调用
    def _handle_RemoveListenChat_DELETED(self, *args, **kwargs):
        """处理RemoveListenChat方法的差异，并添加异常处理"""
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        # 根据不同的库使用不同的处理方法
        if self._lib_name == "wxautox":
            # 对于wxautox库，直接调用原始方法
            try:
                return self._instance.RemoveListenChat(*args, **kwargs)
            except Exception as e:
                # 捕获所有异常，避免崩溃
                import traceback
                logger.error(f"wxautox移除监听失败: {str(e)}")
                traceback.print_exc()
                # 返回False表示失败
                return False
        else:
            # 对于wxauto库，使用更健壮的处理方法
            try:
                # 获取要移除的聊天对象名称
                who = args[0] if args else kwargs.get('who')
                if not who:
                    logger.error("移除监听失败: 未指定聊天对象名称")
                    return False

                # 检查聊天对象是否在监听列表中
                if who in self._instance.listen:
                    # 获取聊天窗口对象
                    chat_wnd = self._instance.listen[who]

                    try:
                        # 尝试关闭聊天窗口
                        import win32gui
                        import win32con

                        # 使用win32gui.FindWindow直接查找窗口
                        chat_hwnd = win32gui.FindWindow('ChatWnd', who)
                        if chat_hwnd:
                            logger.debug(f"关闭聊天窗口: {who}")
                            win32gui.PostMessage(chat_hwnd, win32con.WM_CLOSE, 0, 0)
                    except Exception as e:
                        logger.error(f"关闭聊天窗口失败: {str(e)}")

                    # 从监听列表中删除
                    del self._instance.listen[who]
                    logger.debug(f"成功移除监听: {who}")
                    return True
                else:
                    logger.warning(f"未找到监听对象: {who}")
                    return False
            except Exception as e:
                # 捕获所有异常，避免崩溃
                import traceback
                logger.error(f"wxauto移除监听失败: {str(e)}")
                traceback.print_exc()
                # 返回False表示失败
                return False

# 添加对聊天窗口方法的特殊处理
    def _handle_chat_window_method(self, chat_wnd, method_name, *args, **kwargs):
        """处理聊天窗口方法的调用，添加异常处理"""
        if not chat_wnd:
            raise AttributeError(f"聊天窗口对象为空，无法调用 {method_name} 方法")

        # 获取方法
        method = getattr(chat_wnd, method_name, None)
        if not method:
            raise AttributeError(f"聊天窗口对象没有 {method_name} 方法")

        try:
            # 调用方法
            return method(*args, **kwargs)
        except Exception as e:
            # 捕获所有异常，避免崩溃
            import traceback
            logger.error(f"调用聊天窗口方法 {method_name} 失败: {str(e)}")
            traceback.print_exc()
            # 重新抛出异常，让上层处理
            raise

    def get_friend_list(self):
        """
        获取好友列表
        
        Returns:
            list: 好友昵称列表
        """
        if not self._instance:
            raise AttributeError("微信实例未初始化")
        
        try:
            # 使用GetAllFriends方法获取好友详细信息
            return self._instance.GetAllFriends()
        except Exception as e:
            logger.error(f"获取好友列表失败: {str(e)}")
            # 重新抛出异常，让上层处理
            raise

    def get_group_list(self):
        """
        获取群聊列表
        
        Returns:
            list: 群聊名称列表，每个元素为包含群名称和人数的字典
        """
        if not self._instance:
            raise AttributeError("微信实例未初始化")
        
        try:
            # 使用GetAllGroups方法获取群组详细信息
            groups_info = self._instance.GetAllGroups()
            
            # 提取群聊名称和人数
            group_list = []
            for group in groups_info:
                group_list.append({
                    'name': group['name'],
                    'member_count': group['member_count']
                })
            
            logger.debug(f"获取到 {len(group_list)} 个群聊")
            return group_list
        except Exception as e:
            logger.error(f"获取群聊列表失败: {str(e)}")
            # 重新抛出异常，让上层处理
            raise

    def GetNextNewMessage(self, *args, **kwargs):
        """
        获取下一条新消息 - 独立实现，无缓存机制

        支持wxauto和wxautox两种库的不同参数格式：
        - wxauto: savepic, savefile, savevoice (不支持savevideo, parseurl)
        - wxautox: filter_mute

        Returns:
            wxauto: list - 消息列表
            wxautox: dict - {'chat_name': str, 'chat_type': str, 'msg': list}
        """
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        logger.debug(f"GetNextNewMessage调用，库: {self._lib_name}, 参数: args={args}, kwargs={kwargs}")

        try:
            if self._lib_name == "wxautox":
                # wxautox只支持filter_mute参数
                adjusted_kwargs = {}
                if 'filter_mute' in kwargs:
                    adjusted_kwargs['filter_mute'] = kwargs['filter_mute']
                else:
                    adjusted_kwargs['filter_mute'] = False  # 默认值

                logger.debug(f"wxautox调用参数: {adjusted_kwargs}")
                result = self._instance.GetNextNewMessage(**adjusted_kwargs)
                logger.debug(f"wxautox返回结果类型: {type(result)}")
                return result if result else {}

            else:  # wxauto
                # wxauto的GetNextNewMessage可能不支持任何参数，尝试无参数调用
                logger.info("=== wxauto GetNextNewMessage 开始调用 ===")
                logger.debug("wxauto调用参数: 无参数")
                result = self._instance.GetNextNewMessage()
                logger.info(f"=== wxauto返回结果类型: {type(result)} ===")
                logger.info(f"=== wxauto返回结果内容: {result} ===")

                # 处理wxauto返回的消息对象，转换为可序列化的格式
                if result:
                    logger.debug(f"wxauto原始返回结果: {result}")
                    logger.debug(f"wxauto返回结果类型: {type(result)}")

                    # 检查result的结构
                    if isinstance(result, (list, tuple)):
                        logger.debug(f"result是列表/元组，长度: {len(result)}")
                        for i, item in enumerate(result):
                            logger.debug(f"  item[{i}]: type={type(item)}, value={item}")
                    elif isinstance(result, dict):
                        logger.debug(f"result是字典，键: {list(result.keys())}")
                        for key, value in result.items():
                            logger.debug(f"  {key}: type={type(value)}, value={value}")

                    serializable_result = []

                    # 如果result是字典格式（可能是wxautox格式或wxauto的特殊返回）
                    if isinstance(result, dict):
                        logger.debug("处理字典格式的result")
                        logger.debug(f"字典键: {list(result.keys())}")

                        # 检查是否是wxautox格式 {chat_name: [messages]}
                        if all(isinstance(v, list) for v in result.values()):
                            logger.debug("检测到wxautox格式，直接返回")
                            return result
                        else:
                            # 可能是wxauto的特殊格式，保持字典格式并转换消息对象
                            logger.debug("检测到wxauto字典格式，保持字典结构并转换消息对象")
                            # 如果字典包含消息相关的键，尝试提取消息
                            if 'msg' in result:
                                # 假设msg键包含消息列表
                                messages = result.get('msg', [])
                                if isinstance(messages, list):
                                    # 转换消息对象为可序列化格式，但保持字典结构
                                    serializable_messages = []
                                    for msg in messages:
                                        try:
                                            msg_dict = {
                                                'type': getattr(msg, 'type', 'unknown'),
                                                'content': getattr(msg, 'content', str(msg)),
                                                'sender': getattr(msg, 'sender', ''),
                                                'time': getattr(msg, 'time', ''),
                                                'id': getattr(msg, 'id', ''),
                                                'mtype': getattr(msg, 'mtype', None),
                                                'sender_remark': getattr(msg, 'sender_remark', None),
                                                'file_path': getattr(msg, 'file_path', None)
                                            }
                                            serializable_messages.append(msg_dict)
                                        except Exception as e:
                                            logger.error(f"转换字典中的消息对象失败: {str(e)}")

                                    # 保持字典格式，只替换msg部分
                                    serializable_result = result.copy()
                                    serializable_result['msg'] = serializable_messages
                                    logger.debug(f"wxauto字典格式转换完成，保持chat_name: {result.get('chat_name', '未知')}")
                                    return serializable_result
                            # 否则直接返回字典让API层处理
                            return result

                    # 如果result是列表格式
                    elif isinstance(result, (list, tuple)):
                        logger.debug("处理列表格式的result")
                        for i, msg in enumerate(result):
                            try:
                                logger.debug(f"处理消息 {i}: type={type(msg)}, value={msg}")

                                # 将消息对象转换为字典
                                msg_dict = {
                                    'type': getattr(msg, 'type', 'unknown'),
                                    'content': getattr(msg, 'content', str(msg)),
                                    'sender': getattr(msg, 'sender', ''),
                                    'time': getattr(msg, 'time', ''),
                                    'id': getattr(msg, 'id', ''),
                                    'mtype': getattr(msg, 'mtype', None),
                                    'sender_remark': getattr(msg, 'sender_remark', None),
                                    'file_path': getattr(msg, 'file_path', None)
                                }
                                serializable_result.append(msg_dict)
                                logger.debug(f"转换消息: {msg_dict}")
                            except Exception as e:
                                logger.error(f"转换wxauto消息对象失败: {str(e)}")
                                # 添加错误消息
                                serializable_result.append({
                                    'type': 'error',
                                    'content': f'消息转换错误: {str(e)}',
                                    'sender': '',
                                    'time': '',
                                    'id': '',
                                    'mtype': None,
                                    'sender_remark': None,
                                    'file_path': None
                                })

                    else:
                        # 其他类型，直接转换为字符串
                        logger.debug(f"未知格式的result: {type(result)}")
                        serializable_result = [{"type": "text", "content": str(result)}]

                    logger.debug(f"wxauto转换后结果: {serializable_result}")
                    return serializable_result
                else:
                    return []

        except Exception as e:
            error_str = str(e)
            logger.error(f"GetNextNewMessage调用失败: {error_str}")

            # 如果是"没有新消息"相关的错误，返回空结果
            if "没有新消息" in error_str or "no new message" in error_str.lower():
                logger.debug("没有新消息")
                return {} if self._lib_name == "wxautox" else []

            # 其他错误也返回空结果，避免中断程序
            logger.warning(f"GetNextNewMessage其他错误，返回空结果: {error_str}")
            return {} if self._lib_name == "wxautox" else []


# 导入配置
try:
    from app.config import Config
    # 创建全局适配器实例（使用延迟初始化避免库冲突）
    wechat_adapter = WeChatAdapter(lib_name=Config.WECHAT_LIB, lazy_init=True)
except ImportError as e:
    # 如果无法导入配置，则使用默认值
    wechat_adapter = WeChatAdapter(lib_name='wxauto', lazy_init=True)
