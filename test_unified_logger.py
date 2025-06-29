#!/usr/bin/env python3
"""
测试统一日志管理器
验证重构后的日志系统功能
"""

import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_logging():
    """测试基本日志功能"""
    print("=== 测试基本日志功能 ===")
    
    from app.unified_logger import unified_logger, logger
    
    # 测试不同级别的日志
    logger.set_lib_name("wxauto")
    logger.info("这是一条INFO日志")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志")
    logger.debug("这是一条DEBUG日志")
    
    # 切换库名称
    logger.set_lib_name("wxautox")
    logger.info("切换到wxautox库")
    
    # 切换到Flask
    logger.set_lib_name("Flask")
    logger.info("Flask服务启动")
    
    print("基本日志功能测试完成")

def test_log_aggregation():
    """测试日志聚合功能"""
    print("\n=== 测试日志聚合功能 ===")
    
    from app.unified_logger import unified_logger, logger
    
    logger.set_lib_name("wxauto")
    
    # 发送重复日志
    for i in range(5):
        logger.info("这是一条重复的日志消息")
        time.sleep(0.1)
    
    # 发送不同的日志
    logger.info("这是一条不同的日志消息")
    
    # 等待聚合处理
    print("等待5秒以查看聚合效果...")
    time.sleep(6)
    
    print("日志聚合功能测试完成")

def test_ui_integration():
    """测试UI集成"""
    print("\n=== 测试UI集成 ===")
    
    from app.unified_logger import unified_logger
    
    # 模拟UI处理器
    ui_logs = []
    
    def mock_ui_handler(formatted_log):
        ui_logs.append(formatted_log)
        print(f"UI收到日志: {formatted_log}")
    
    # 添加UI处理器
    unified_logger.add_ui_handler(mock_ui_handler)
    
    # 发送测试日志
    from app.unified_logger import logger
    logger.set_lib_name("测试")
    logger.info("测试UI集成")
    logger.warning("这是一条警告")
    
    # 等待处理
    time.sleep(1)
    
    # 移除UI处理器
    unified_logger.remove_ui_handler(mock_ui_handler)
    
    print(f"UI处理器收到 {len(ui_logs)} 条日志")
    print("UI集成测试完成")

def test_file_output():
    """测试文件输出"""
    print("\n=== 测试文件输出 ===")
    
    from app.unified_logger import logger
    import os
    from pathlib import Path
    
    # 检查日志文件是否存在
    log_dir = Path("data/api/logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("api_*.log"))
        if log_files:
            latest_log = max(log_files, key=os.path.getctime)
            print(f"找到日志文件: {latest_log}")
            
            # 读取最后几行
            try:
                with open(latest_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print("日志文件最后5行:")
                    for line in lines[-5:]:
                        print(f"  {line.strip()}")
            except Exception as e:
                print(f"读取日志文件失败: {e}")
        else:
            print("未找到日志文件")
    else:
        print("日志目录不存在")
    
    # 发送测试日志
    logger.set_lib_name("文件测试")
    logger.info("测试文件输出功能")
    
    print("文件输出测试完成")

def test_format_consistency():
    """测试格式一致性"""
    print("\n=== 测试格式一致性 ===")
    
    from app.unified_logger import LogEntry, LogFormatter
    from datetime import datetime
    
    formatter = LogFormatter()
    
    # 测试单个日志条目
    entry1 = LogEntry(datetime.now(), "wxauto", "INFO", "测试消息")
    formatted1 = formatter.format_entry(entry1)
    print(f"单个日志: {formatted1}")
    
    # 测试重复日志条目
    entry2 = LogEntry(datetime.now(), "wxauto", "INFO", "测试消息")
    entry2.count = 3
    entry2.last_timestamp = datetime.now()
    formatted2 = formatter.format_entry(entry2)
    print(f"重复日志: {formatted2}")
    
    # 验证格式
    expected_pattern = r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[.*?\] \[.*?\] .*'
    import re
    
    if re.match(expected_pattern, formatted1):
        print("✓ 单个日志格式正确")
    else:
        print("✗ 单个日志格式错误")
    
    if re.match(expected_pattern, formatted2):
        print("✓ 重复日志格式正确")
    else:
        print("✗ 重复日志格式错误")
    
    print("格式一致性测试完成")

def main():
    """主测试函数"""
    print("开始测试统一日志管理器")
    print("=" * 50)
    
    try:
        test_basic_logging()
        test_log_aggregation()
        test_ui_integration()
        test_file_output()
        test_format_consistency()
        
        print("\n" + "=" * 50)
        print("所有测试完成！")
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
