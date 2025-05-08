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
    from app.logs import logger
except ImportError:
    # 如果无法导入app.logs，则创建一个默认的logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("wechat_adapter")

class WeChatAdapter:
    """微信自动化库适配器，支持wxauto和wxautox"""

    def __init__(self, lib_name: str = 'wxauto'):
        """
        初始化适配器

        Args:
            lib_name: 指定使用的库名称，可选值: 'wxauto', 'wxautox'，默认为'wxauto'
        """
        self._instance = None
        self._lib_name = None
        self._lock = threading.Lock()

        # 根据指定的库名称导入相应的库
        if lib_name.lower() == 'wxautox':
            if not self._try_import_wxautox():
                logger.error("无法导入wxautox库")
                raise ImportError("无法导入wxautox库，请确保已正确安装")
        else:  # 默认使用wxauto
            if not self._try_import_wxauto():
                logger.error("无法导入wxauto库")
                raise ImportError("无法导入wxauto库，请确保已正确安装")

        logger.info(f"使用微信自动化库: {self._lib_name}")

    def _try_import_wxautox(self) -> bool:
        """尝试导入wxautox库"""
        try:
            import wxautox
            self._lib_name = "wxautox"
            return True
        except ImportError:
            logger.warning("无法导入wxautox库")
            return False

    def _try_import_wxauto(self) -> bool:
        """尝试导入wxauto库"""
        try:
            import wxauto
            self._lib_name = "wxauto"
            return True
        except ImportError:
            logger.warning("无法导入wxauto库")
            return False

    def initialize(self) -> bool:
        """初始化微信实例"""
        with self._lock:
            if not self._instance:
                try:
                    # 初始化COM环境
                    pythoncom.CoInitialize()

                    if self._lib_name == "wxautox":
                        from wxautox import WeChat
                        self._instance = WeChat()
                    else:  # wxauto
                        from wxauto import WeChat
                        self._instance = WeChat()

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
                            logger.info(f"微信实例初始化成功，获取到已登录窗口：{window_name}，使用库: {self._lib_name}")
                        else:
                            logger.info(f"微信实例初始化成功，但无法获取窗口名称，使用库: {self._lib_name}")
                    except Exception as e:
                        logger.warning(f"获取窗口名称失败: {str(e)}")
                        logger.info(f"微信实例初始化成功，使用库: {self._lib_name}")

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

    def check_connection(self) -> bool:
        """检查微信连接状态"""
        if not self._instance:
            return False

        try:
            # 两个库都支持GetSessionList方法
            self._instance.GetSessionList()
            return True
        except Exception as e:
            logger.error(f"微信连接检查失败: {str(e)}")
            return False

    def __getattr__(self, name):
        """代理到实际的微信实例"""
        if self._instance is None:
            raise AttributeError(f"微信实例未初始化，无法调用 {name} 方法")

        # 检查是否需要特殊处理的方法
        handler = getattr(self, f"_handle_{name}", None)
        if handler:
            return handler

        # 直接代理到实际实例
        return getattr(self._instance, name)

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

    def _handle_GetNextNewMessage(self, *args, **kwargs):
        """处理GetNextNewMessage方法的差异"""
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        # wxauto不支持savevideo和parseurl参数
        if self._lib_name == "wxauto":
            # 从kwargs中移除不支持的参数
            kwargs.pop("savevideo", None)
            kwargs.pop("parseurl", None)

        # 调用原始方法
        return self._instance.GetNextNewMessage(*args, **kwargs)

    def _handle_AddListenChat(self, *args, **kwargs):
        """处理AddListenChat方法的差异"""
        if not self._instance:
            raise AttributeError("微信实例未初始化")

        # wxauto不支持savevideo和parseurl参数
        if self._lib_name == "wxauto":
            # 从kwargs中移除不支持的参数
            kwargs.pop("savevideo", None)
            kwargs.pop("parseurl", None)

        # 调用原始方法
        return self._instance.AddListenChat(*args, **kwargs)

# 导入配置
try:
    from app.config import Config
    # 创建全局适配器实例
    wechat_adapter = WeChatAdapter(lib_name=Config.WECHAT_LIB)
except ImportError:
    # 如果无法导入配置，则使用默认值
    wechat_adapter = WeChatAdapter(lib_name='wxauto')
