"""
应用程序互斥锁模块
确保同一时间只能有一个UI实例和一个API服务实例在运行
"""

import os
import sys
import time
import logging
import tempfile
import atexit
import socket
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class AppMutex:
    """应用程序互斥锁"""
    
    def __init__(self, name, port=None):
        """
        初始化互斥锁
        
        Args:
            name (str): 互斥锁名称，用于区分不同的互斥锁
            port (int, optional): 如果指定，则使用端口锁定机制
        """
        self.name = name
        self.port = port
        self.lock_file = None
        self.lock_socket = None
        self.is_locked = False
    
    def acquire(self):
        """
        获取互斥锁
        
        Returns:
            bool: 是否成功获取互斥锁
        """
        # 如果指定了端口，则使用端口锁定机制
        if self.port is not None:
            return self._acquire_port_lock()
        
        # 否则使用文件锁定机制
        return self._acquire_file_lock()
    
    def _acquire_port_lock(self):
        """
        使用端口锁定机制获取互斥锁
        
        Returns:
            bool: 是否成功获取互斥锁
        """
        try:
            logger.info(f"尝试获取端口锁: {self.port}")
            self.lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 设置端口重用选项，避免TIME_WAIT状态导致的问题
            self.lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 尝试绑定端口
            try:
                self.lock_socket.bind(('localhost', self.port))
                self.lock_socket.listen(1)
                self.is_locked = True
                logger.info(f"成功获取端口锁: {self.port}")
                return True
            except socket.error as e:
                logger.warning(f"无法绑定端口 {self.port}: {str(e)}")
                
                # 尝试使用0.0.0.0地址绑定
                try:
                    self.lock_socket.close()
                    self.lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    self.lock_socket.bind(('0.0.0.0', self.port))
                    self.lock_socket.listen(1)
                    self.is_locked = True
                    logger.info(f"成功获取端口锁(0.0.0.0): {self.port}")
                    return True
                except socket.error as e2:
                    logger.warning(f"无法绑定端口(0.0.0.0) {self.port}: {str(e2)}")
                    self.lock_socket = None
                    return False
        except Exception as e:
            logger.error(f"获取端口锁时出错: {str(e)}")
            self.lock_socket = None
            return False
    
    def _acquire_file_lock(self):
        """
        使用文件锁定机制获取互斥锁
        
        Returns:
            bool: 是否成功获取互斥锁
        """
        try:
            # 在临时目录中创建锁文件
            temp_dir = tempfile.gettempdir()
            lock_file_path = os.path.join(temp_dir, f"{self.name}.lock")
            
            # 检查锁文件是否存在
            if os.path.exists(lock_file_path):
                # 检查锁文件是否过期（超过1小时）
                if time.time() - os.path.getmtime(lock_file_path) > 3600:
                    logger.warning(f"发现过期的锁文件: {lock_file_path}，将删除")
                    os.remove(lock_file_path)
                else:
                    logger.warning(f"发现有效的锁文件: {lock_file_path}，无法获取互斥锁")
                    return False
            
            # 创建锁文件
            self.lock_file = open(lock_file_path, 'w')
            self.lock_file.write(f"{os.getpid()}")
            self.lock_file.flush()
            self.is_locked = True
            
            # 注册退出时的清理函数
            atexit.register(self.release)
            
            logger.info(f"成功获取文件锁: {lock_file_path}")
            return True
        except Exception as e:
            logger.error(f"获取文件锁失败: {str(e)}")
            return False
    
    def release(self):
        """释放互斥锁"""
        if not self.is_locked:
            return
        
        # 释放端口锁
        if self.lock_socket is not None:
            try:
                self.lock_socket.close()
                logger.info(f"已释放端口锁: {self.port}")
            except Exception as e:
                logger.error(f"释放端口锁失败: {str(e)}")
            finally:
                self.lock_socket = None
        
        # 释放文件锁
        if self.lock_file is not None:
            try:
                lock_file_path = self.lock_file.name
                self.lock_file.close()
                if os.path.exists(lock_file_path):
                    os.remove(lock_file_path)
                logger.info(f"已释放文件锁: {lock_file_path}")
            except Exception as e:
                logger.error(f"释放文件锁失败: {str(e)}")
            finally:
                self.lock_file = None
        
        self.is_locked = False

# 创建UI互斥锁
ui_mutex = AppMutex("wxauto_http_api_ui")

# 创建API服务互斥锁（使用端口锁定机制）
def create_api_mutex(port=5000):
    """
    创建API服务互斥锁
    
    Args:
        port (int): API服务端口
    
    Returns:
        AppMutex: API服务互斥锁
    """
    return AppMutex("wxauto_http_api_api", port=port)
