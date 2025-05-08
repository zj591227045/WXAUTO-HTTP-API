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
    if current_chat:
        wx.AddListenChat(current_chat, savepic=True, savefile=True, savevoice=True)
        print(f"成功添加监听: {current_chat}")

        # 不尝试发送消息，只测试监听功能
        print("跳过发送测试消息，直接测试监听功能")

        # 尝试获取监听消息
        print("尝试获取监听消息...")
        messages = wx.GetListenMessage()
        print(f"获取监听消息结果: {messages}")

        print("测试完成")
    else:
        print("未找到当前聊天窗口，请先打开一个聊天窗口")
        sys.exit(1)

except Exception as e:
    print(f"测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
