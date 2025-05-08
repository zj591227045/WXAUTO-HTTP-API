import os
import sys
import time
from pathlib import Path

# 确保本地wxauto文件夹在Python路径中
wxauto_path = os.path.join(os.getcwd(), "wxauto")
if wxauto_path not in sys.path:
    sys.path.insert(0, wxauto_path)

# 导入wxauto
from wxauto import WeChat
from wxauto.elements import WeChatImage, WxParam

# 创建data/api/temp目录（如果不存在）
temp_dir = os.path.join(os.getcwd(), "data", "api", "temp")
os.makedirs(temp_dir, exist_ok=True)

# 打印当前的默认保存路径
print(f"当前默认保存路径: {WxParam.DEFALUT_SAVEPATH}")

# 修改默认保存路径为data/api/temp
original_path = WxParam.DEFALUT_SAVEPATH
WxParam.DEFALUT_SAVEPATH = temp_dir
print(f"修改后的默认保存路径: {WxParam.DEFALUT_SAVEPATH}")

# 初始化微信实例
wx = WeChat()
print(f"微信窗口名称: {wx.nickname}")

# 测试获取新消息并保存图片
try:
    print("尝试获取新消息并保存图片...")
    messages = wx.GetNextNewMessage(savepic=True, savefile=True, savevoice=True)

    if messages:
        print(f"获取到消息: {messages}")
        for chat_name, msg_list in messages.items():
            print(f"聊天: {chat_name}")
            for msg in msg_list:
                print(f"  类型: {msg.type}, 发送者: {msg.sender}, 内容: {msg.content}")

                # 检查内容是否为图片路径
                if msg.content and os.path.exists(msg.content):
                    print(f"  图片已保存到: {msg.content}")

                    # 检查图片是否在预期目录中
                    if temp_dir in msg.content:
                        print("  图片保存在正确的目录中")
                    else:
                        print(f"  警告: 图片未保存在预期目录 {temp_dir} 中")
    else:
        print("没有获取到新消息")
except Exception as e:
    print(f"获取消息时出错: {str(e)}")
    import traceback
    traceback.print_exc()

# 恢复原始默认保存路径
WxParam.DEFALUT_SAVEPATH = original_path
print(f"恢复默认保存路径: {WxParam.DEFALUT_SAVEPATH}")
