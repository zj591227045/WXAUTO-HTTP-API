from wxautox import WeChat

def test_send_message():
    # 获取微信实例
    wx = WeChat()
    print("微信初始化成功")
    
    # 1. 测试普通发送消息
    who = '文件传输助手'
    msg = '''这是一条测试消息
这是第二行
这是第三行'''
    
    result = wx.SendMsg(msg, who=who)
    if result:
        print("普通消息发送成功")
    else:
        print("普通消息发送失败")
        
    # 2. 测试打字机模式发送消息
    typing_msg = '''这是打字机模式消息
测试换行功能
自动输入效果'''
    
    
    wx.SendTypingText(typing_msg, who=who)
    print("打字机模式消息发送完成")
    
    # 3. 测试群消息和@功能
    group_msg = '''大家好
{@张三}请查看任务进度
{@李四}请更新状态'''
    
    # 注意: 这里需要替换为实际的群名称
    group_name = '测试群'
    wx.SendTypingText(group_msg, who=group_name)
    print("群消息发送完成")

if __name__ == '__main__':
    try:
        test_send_message()
    except Exception as e:
        print(f"发生错误: {e}")