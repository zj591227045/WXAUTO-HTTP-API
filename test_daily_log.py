#!/usr/bin/env python3
"""
测试动态日志文件功能
验证跨天日志文件自动切换功能
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# 导入动态日志处理器
from app.logs import DailyRotatingFileHandler
import app.config_manager as config_manager

def test_daily_rotating_handler():
    """测试动态日志文件处理器"""
    print("开始测试动态日志文件处理器...")
    
    # 确保日志目录存在
    config_manager.ensure_dirs()
    
    # 创建测试logger
    logger = logging.getLogger('test_daily_log')
    logger.setLevel(logging.DEBUG)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 创建动态日志文件处理器
    handler = DailyRotatingFileHandler(
        log_dir=str(config_manager.LOGS_DIR),
        filename_prefix="test",
        max_bytes=1024*1024,  # 1MB
        backup_count=3
    )
    
    # 设置格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(handler)
    
    # 测试当前日期的日志文件
    current_date = datetime.now().strftime('%Y%m%d')
    expected_file = config_manager.LOGS_DIR / f"test_{current_date}.log"
    
    print(f"当前日期: {current_date}")
    print(f"期望的日志文件: {expected_file}")
    
    # 写入一些测试日志
    logger.info("这是一条测试日志消息")
    logger.warning("这是一条警告消息")
    logger.error("这是一条错误消息")
    
    # 检查文件是否创建
    if expected_file.exists():
        print(f"✓ 日志文件已创建: {expected_file}")
        
        # 读取文件内容
        with open(expected_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"文件内容:\n{content}")
    else:
        print(f"✗ 日志文件未创建: {expected_file}")
    
    # 模拟日期变化（通过直接修改处理器的内部状态）
    print("\n模拟日期变化...")

    # 手动设置为明天的日期
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_date = tomorrow.strftime('%Y%m%d')

    # 强制重置处理器的日期，模拟跨天情况
    handler.current_date = None

    # 手动修改处理器的_get_current_log_file方法来模拟明天
    original_method = handler._get_current_log_file
    def mock_get_current_log_file():
        filename = f"{handler.filename_prefix}_{tomorrow_date}.log"
        return os.path.join(handler.log_dir, filename)

    handler._get_current_log_file = mock_get_current_log_file

    try:
        # 写入新的日志
        logger.info("这是模拟明天的日志消息")

        # 检查新的日志文件
        new_expected_file = config_manager.LOGS_DIR / f"test_{tomorrow_date}.log"
        print(f"明天的日期: {tomorrow_date}")
        print(f"期望的新日志文件: {new_expected_file}")

        if new_expected_file.exists():
            print(f"✓ 新日志文件已创建: {new_expected_file}")

            # 读取新文件内容
            with open(new_expected_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"新文件内容:\n{content}")
        else:
            print(f"✗ 新日志文件未创建: {new_expected_file}")

    finally:
        # 恢复原始方法
        handler._get_current_log_file = original_method
    
    # 清理测试文件
    print("\n清理测试文件...")
    for test_file in config_manager.LOGS_DIR.glob("test_*.log*"):
        try:
            test_file.unlink()
            print(f"已删除: {test_file}")
        except Exception as e:
            print(f"删除失败 {test_file}: {e}")
    
    # 关闭处理器
    handler.close()
    
    print("\n测试完成!")

def test_current_log_file_function():
    """测试获取当前日志文件的功能"""
    print("\n测试获取当前日志文件功能...")
    
    # 导入Config类
    from app.config import Config
    
    # 测试新的get_current_log_file方法
    current_log_file = Config.get_current_log_file()
    print(f"当前日志文件路径: {current_log_file}")
    
    # 验证文件名格式
    expected_pattern = f"api_{datetime.now().strftime('%Y%m%d')}.log"
    if expected_pattern in current_log_file:
        print(f"✓ 日志文件名格式正确: {expected_pattern}")
    else:
        print(f"✗ 日志文件名格式错误，期望包含: {expected_pattern}")

if __name__ == "__main__":
    test_daily_rotating_handler()
    test_current_log_file_function()
