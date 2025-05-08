"""
图片处理工具
用于处理wxauto保存图片时的路径问题
"""

import os
import time
import glob
import logging
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 可能的图片保存位置
POSSIBLE_SAVE_LOCATIONS = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Pictures"),
    os.path.expanduser("~/Downloads"),
    os.path.join(os.getcwd(), "wxauto文件"),
    os.path.join(os.getcwd(), "data", "api", "temp")
]

def find_actual_image_path(expected_path, created_after=None, max_wait_seconds=3):
    """
    查找图片的实际保存路径
    
    Args:
        expected_path (str): wxauto返回的预期路径
        created_after (float, optional): 文件创建时间必须晚于此时间戳
        max_wait_seconds (int, optional): 最长等待时间（秒）
        
    Returns:
        str: 实际的文件路径，如果找不到则返回原始路径
    """
    if not expected_path:
        logger.warning("预期路径为空")
        return expected_path
    
    # 如果文件存在于预期位置，直接返回
    if os.path.exists(expected_path) and os.path.getsize(expected_path) > 0:
        logger.debug(f"文件存在于预期位置: {expected_path}")
        return expected_path
    
    # 设置创建时间过滤器
    if created_after is None:
        created_after = time.time() - 60  # 默认查找最近60秒内创建的文件
    
    # 获取文件名
    file_name = os.path.basename(expected_path)
    
    # 等待一段时间，看文件是否会出现
    end_time = time.time() + max_wait_seconds
    while time.time() < end_time:
        # 检查预期位置
        if os.path.exists(expected_path) and os.path.getsize(expected_path) > 0:
            logger.debug(f"文件已出现在预期位置: {expected_path}")
            return expected_path
        
        # 检查其他可能的位置
        for location in POSSIBLE_SAVE_LOCATIONS:
            if not os.path.exists(location):
                continue
                
            # 精确匹配文件名
            exact_path = os.path.join(location, file_name)
            if os.path.exists(exact_path) and os.path.getsize(exact_path) > 0:
                file_time = os.path.getmtime(exact_path)
                if file_time >= created_after:
                    logger.info(f"文件找到于替代位置: {exact_path}")
                    return exact_path
            
            # 查找相似文件名（时间戳可能不完全匹配）
            pattern = os.path.join(location, "微信图片_*.jpg")
            for file_path in glob.glob(pattern):
                file_time = os.path.getmtime(file_path)
                if file_time >= created_after:
                    logger.info(f"找到可能匹配的文件: {file_path}")
                    return file_path
        
        # 短暂等待后重试
        time.sleep(0.5)
    
    # 如果找不到，记录警告并返回原始路径
    logger.warning(f"无法找到文件的实际位置，返回预期路径: {expected_path}")
    return expected_path

def save_image_with_verification(wx_instance, msg_item):
    """
    保存图片并验证实际保存位置
    
    Args:
        wx_instance: wxauto的WeChat实例
        msg_item: 消息项控件
        
    Returns:
        str: 实际的文件路径
    """
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 调用原始的_download_pic方法
        expected_path = wx_instance._download_pic(msg_item)
        
        # 验证实际保存位置
        actual_path = find_actual_image_path(expected_path, created_after=start_time)
        
        return actual_path
    except Exception as e:
        logger.error(f"保存图片时出错: {str(e)}")
        return None

def process_image_paths(messages):
    """
    处理消息中的图片路径，确保它们指向实际文件
    
    Args:
        messages (dict): wxauto返回的消息字典
        
    Returns:
        dict: 处理后的消息字典
    """
    if not messages:
        return messages
    
    # 记录开始时间
    start_time = time.time()
    
    # 处理每个聊天的消息
    for chat_name, msg_list in messages.items():
        for i, msg in enumerate(msg_list):
            # 检查是否为图片消息
            if hasattr(msg, 'content') and msg.content and isinstance(msg.content, str):
                if msg.content.startswith("[图片]"):
                    # 这是一个未保存的图片消息
                    logger.debug(f"跳过未保存的图片消息: {msg.content}")
                    continue
                    
                # 检查内容是否为图片路径
                if "微信图片_" in msg.content and (msg.content.endswith(".jpg") or msg.content.endswith(".png")):
                    # 验证实际保存位置
                    actual_path = find_actual_image_path(msg.content, created_after=start_time)
                    
                    # 更新消息内容
                    if actual_path != msg.content:
                        logger.info(f"更新图片路径: {msg.content} -> {actual_path}")
                        msg.content = actual_path
                        # 如果消息有info属性，也更新它
                        if hasattr(msg, 'info') and isinstance(msg.info, list) and len(msg.info) > 1:
                            msg.info[1] = actual_path
    
    return messages
