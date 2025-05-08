import sys
import os
import time

# 添加wxauto库到Python路径
sys.path.append(os.path.abspath('wxauto'))

try:
    # 尝试导入wxauto库
    from wxauto.wxauto import WeChat
    
    # 创建WeChat实例
    wx = WeChat()
    print("成功创建WeChat实例")
    
    # 使用指定的聊天窗口名称
    chat_name = "张杰"
    print(f"将使用指定的聊天窗口: {chat_name}")
    
    # 尝试打开指定的聊天窗口
    try:
        wx.ChatWith(chat_name)
        current_chat = chat_name
        print(f"成功打开聊天窗口: {chat_name}")
    except Exception as e:
        print(f"打开聊天窗口 {chat_name} 失败: {str(e)}")
        sys.exit(1)
    
    # 添加监听
    try:
        wx.AddListenChat(current_chat, savepic=True, savefile=True, savevoice=True)
        print(f"成功添加监听: {current_chat}")
    except Exception as e:
        print(f"添加监听失败: {str(e)}")
        sys.exit(1)
    
    # 多次调用GetListenMessage方法，测试稳定性
    print("开始压力测试GetListenMessage方法...")
    for i in range(10):
        print(f"第{i+1}次调用GetListenMessage...")
        try:
            messages = wx.GetListenMessage()
            print(f"获取监听消息成功，结果长度: {len(messages) if isinstance(messages, dict) else 0}")
        except Exception as e:
            print(f"获取监听消息失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 短暂等待
        time.sleep(0.5)
    
    print("压力测试完成，没有出现递归深度超出限制的错误")
    
except Exception as e:
    print(f"测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
