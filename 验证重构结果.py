#!/usr/bin/env python3
"""
验证日志系统重构结果
确保所有功能正常工作
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_unified_logger():
    """测试统一日志管理器"""
    print("=== 测试统一日志管理器 ===")
    
    try:
        from app.unified_logger import unified_logger, logger
        
        # 测试基本功能
        logger.set_lib_name("测试")
        logger.info("统一日志管理器测试")
        logger.warning("这是一条警告")
        logger.error("这是一条错误")
        
        print("✅ 统一日志管理器工作正常")
        return True
    except Exception as e:
        print(f"❌ 统一日志管理器测试失败: {e}")
        return False

def test_flask_app():
    """测试Flask应用"""
    print("\n=== 测试Flask应用 ===")
    
    try:
        from app import create_app
        app = create_app()
        print("✅ Flask应用创建成功")
        return True
    except Exception as e:
        print(f"❌ Flask应用测试失败: {e}")
        return False

def test_ui_components():
    """测试UI组件"""
    print("\n=== 测试UI组件 ===")
    
    try:
        import tkinter as tk
        from app.app_ui import WxAutoHttpUI
        
        # 创建隐藏的根窗口进行测试
        root = tk.Tk()
        root.withdraw()
        
        # 测试UI类导入
        print("✅ UI组件导入成功")
        
        root.destroy()
        return True
    except Exception as e:
        print(f"❌ UI组件测试失败: {e}")
        return False

def test_api_routes():
    """测试API路由"""
    print("\n=== 测试API路由 ===")
    
    try:
        from app.api.routes import api_bp
        from app.api.admin_routes import admin_bp
        from app.api.moments_routes import moments_bp
        
        print("✅ API路由导入成功")
        return True
    except Exception as e:
        print(f"❌ API路由测试失败: {e}")
        return False

def test_wechat_adapter():
    """测试微信适配器"""
    print("\n=== 测试微信适配器 ===")
    
    try:
        from app.wechat_adapter import WeChatAdapter
        from app.wechat import wechat_manager
        
        print("✅ 微信适配器导入成功")
        return True
    except Exception as e:
        print(f"❌ 微信适配器测试失败: {e}")
        return False

def test_log_format():
    """测试日志格式"""
    print("\n=== 测试日志格式 ===")
    
    try:
        from app.unified_logger import LogEntry, LogFormatter
        from datetime import datetime
        
        formatter = LogFormatter()
        
        # 测试单个日志
        entry1 = LogEntry(datetime.now(), "wxauto", "INFO", "测试消息")
        formatted1 = formatter.format_entry(entry1)
        
        # 测试重复日志
        entry2 = LogEntry(datetime.now(), "wxauto", "INFO", "重复消息")
        entry2.count = 3
        entry2.last_timestamp = datetime.now()
        formatted2 = formatter.format_entry(entry2)
        
        print(f"单个日志格式: {formatted1}")
        print(f"重复日志格式: {formatted2}")
        
        # 验证格式
        import re
        pattern = r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[.*?\] \[.*?\] .*'
        
        if re.match(pattern, formatted1) and re.match(pattern, formatted2):
            print("✅ 日志格式验证通过")
            return True
        else:
            print("❌ 日志格式验证失败")
            return False
    except Exception as e:
        print(f"❌ 日志格式测试失败: {e}")
        return False

def test_log_aggregation():
    """测试日志聚合"""
    print("\n=== 测试日志聚合 ===")
    
    try:
        from app.unified_logger import unified_logger, logger
        
        # 收集UI输出
        ui_logs = []
        def test_handler(log):
            ui_logs.append(log)
        
        unified_logger.add_ui_handler(test_handler)
        
        # 发送重复日志
        logger.set_lib_name("聚合测试")
        for i in range(3):
            logger.info("重复的测试消息")
            time.sleep(0.1)
        
        # 等待聚合
        time.sleep(6)
        
        # 移除处理器
        unified_logger.remove_ui_handler(test_handler)
        
        # 检查结果
        aggregated_logs = [log for log in ui_logs if "重复" in log and "次" in log]
        if aggregated_logs:
            print(f"✅ 日志聚合功能正常: {aggregated_logs[0]}")
            return True
        else:
            print("❌ 日志聚合功能异常")
            return False
    except Exception as e:
        print(f"❌ 日志聚合测试失败: {e}")
        return False

def test_file_output():
    """测试文件输出"""
    print("\n=== 测试文件输出 ===")
    
    try:
        from pathlib import Path
        from app.unified_logger import logger
        
        # 发送测试日志
        logger.set_lib_name("文件测试")
        logger.info("文件输出测试消息")
        
        # 检查日志文件
        log_dir = Path("data/api/logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("api_*.log"))
            if log_files:
                latest_log = max(log_files, key=os.path.getctime)
                print(f"✅ 日志文件存在: {latest_log}")
                
                # 检查文件内容
                try:
                    with open(latest_log, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "文件输出测试消息" in content:
                            print("✅ 日志文件内容正确")
                            return True
                        else:
                            print("❌ 日志文件内容不正确")
                            return False
                except Exception as e:
                    print(f"❌ 读取日志文件失败: {e}")
                    return False
            else:
                print("❌ 未找到日志文件")
                return False
        else:
            print("❌ 日志目录不存在")
            return False
    except Exception as e:
        print(f"❌ 文件输出测试失败: {e}")
        return False

def main():
    """主验证函数"""
    print("开始验证日志系统重构结果")
    print("=" * 60)
    
    tests = [
        test_unified_logger,
        test_flask_app,
        test_ui_components,
        test_api_routes,
        test_wechat_adapter,
        test_log_format,
        test_log_aggregation,
        test_file_output
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"验证结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！日志系统重构成功！")
        return 0
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())
