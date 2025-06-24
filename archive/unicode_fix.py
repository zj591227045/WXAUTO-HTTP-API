"""
Unicode编码修复模块
用于解决微信名称中包含Unicode表情符号导致的GBK编码错误问题
"""

import sys
import logging
import traceback

# 获取logger
logger = logging.getLogger(__name__)

def patch_print_function():
    """
    修补print函数，处理Unicode编码问题
    当遇到GBK编码错误时，使用UTF-8编码输出
    """
    try:
        # 保存原始的print函数
        original_print = print
        
        # 定义新的print函数
        def safe_print(*args, **kwargs):
            try:
                # 尝试使用原始print函数
                original_print(*args, **kwargs)
            except UnicodeEncodeError as e:
                # 如果是GBK编码错误，使用UTF-8编码输出
                if 'gbk' in str(e).lower():
                    # 将所有参数转换为字符串并连接
                    message = " ".join(str(arg) for arg in args)
                    # 使用sys.stdout.buffer直接写入UTF-8编码的字节
                    try:
                        if hasattr(sys.stdout, 'buffer'):
                            sys.stdout.buffer.write(message.encode('utf-8'))
                            sys.stdout.buffer.write(b'\n')
                            sys.stdout.buffer.flush()
                        else:
                            # 如果没有buffer属性，尝试使用logger
                            logger.info(message)
                    except Exception as inner_e:
                        # 如果还是失败，记录到日志
                        logger.error(f"安全打印失败: {str(inner_e)}")
                else:
                    # 如果不是GBK编码错误，重新抛出
                    raise
        
        # 替换全局print函数
        import builtins
        builtins.print = safe_print
        
        #logger.info("成功修补print函数，解决Unicode编码问题")
        return True
    except Exception as e:
        logger.error(f"修补print函数失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def patch_wechat_adapter():
    """
    修补WeChatAdapter类，处理Unicode编码问题
    在初始化微信实例时捕获并处理GBK编码错误
    """
    try:
        # 尝试导入WeChatAdapter类
        from app.wechat_adapter import WeChatAdapter
        
        # 保存原始的initialize方法
        original_initialize = WeChatAdapter.initialize
        
        # 定义新的initialize方法
        def patched_initialize(self):
            """初始化微信实例，添加Unicode编码处理"""
            try:
                # 先修补print函数，确保后续操作不会因编码问题失败
                patch_print_function()
                
                # 调用原始的initialize方法
                return original_initialize(self)
            except UnicodeEncodeError as e:
                if 'gbk' in str(e).lower():
                    logger.warning(f"捕获到GBK编码错误: {str(e)}")
                    logger.info("尝试修复Unicode编码问题...")
                    
                    # 修补print函数
                    patch_print_function()
                    
                    # 再次尝试调用原始的initialize方法
                    return original_initialize(self)
                else:
                    # 如果不是GBK编码错误，重新抛出
                    raise
        
        # 替换WeChatAdapter.initialize方法
        WeChatAdapter.initialize = patched_initialize
        
        logger.info("成功修补WeChatAdapter.initialize方法，解决Unicode编码问题")
        return True
    except ImportError:
        logger.warning("无法导入WeChatAdapter类，跳过修补")
        return False
    except Exception as e:
        logger.error(f"修补WeChatAdapter.initialize方法失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def apply_patches():
    """应用所有补丁"""
    logger.info("开始应用Unicode编码修复补丁...")
    
    # 修补print函数
    print_patched = patch_print_function()
    logger.info(f"print函数修补结果: {'成功' if print_patched else '失败'}")
    
    # 修补WeChatAdapter类
    adapter_patched = patch_wechat_adapter()
    logger.info(f"WeChatAdapter类修补结果: {'成功' if adapter_patched else '失败'}")
    
    return print_patched or adapter_patched  # 只要有一个成功就返回True

# 自动应用补丁
patched = apply_patches()
