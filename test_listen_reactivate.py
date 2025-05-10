#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time
import sys

# 配置信息
API_BASE_URL = "http://localhost:5000/api"
API_KEY = "test-key-2"  # 使用默认的API密钥

# 请求头
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def print_response(response):
    """打印响应内容"""
    try:
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"解析响应失败: {str(e)}")
        print(f"原始响应: {response.text}")

def initialize_wechat():
    """初始化微信"""
    print("\n=== 初始化微信 ===")
    # 发送空的JSON数据
    data = {}
    response = requests.post(f"{API_BASE_URL}/wechat/initialize", headers=headers, json=data)
    print_response(response)
    return response.status_code == 200

def add_listen_chat(who):
    """添加监听对象"""
    print(f"\n=== 添加监听对象: {who} ===")
    data = {
        "who": who,
        "savepic": True,
        "savefile": True,
        "savevoice": True
    }
    response = requests.post(f"{API_BASE_URL}/message/listen/add", headers=headers, json=data)
    print_response(response)
    return response.status_code == 200

def get_listen_messages(who=None):
    """获取监听消息"""
    print(f"\n=== 获取监听消息 {f'(who={who})' if who else ''} ===")
    params = {}
    if who:
        params["who"] = who
    response = requests.get(f"{API_BASE_URL}/message/listen/get", headers=headers, params=params)
    print_response(response)
    return response.status_code == 200

def remove_listen_chat(who):
    """移除监听对象"""
    print(f"\n=== 移除监听对象: {who} ===")
    data = {
        "who": who
    }
    response = requests.post(f"{API_BASE_URL}/message/listen/remove", headers=headers, json=data)
    print_response(response)
    return response.status_code == 200

def reactivate_listen_chat(who):
    """重新激活监听对象"""
    print(f"\n=== 重新激活监听对象: {who} ===")
    data = {
        "who": who,
        "savepic": True,
        "savefile": True,
        "savevoice": True
    }
    response = requests.post(f"{API_BASE_URL}/message/listen/reactivate", headers=headers, json=data)
    print_response(response)
    return response.status_code == 200

def check_wechat_status():
    """检查微信状态"""
    print("\n=== 检查微信状态 ===")
    response = requests.get(f"{API_BASE_URL}/health", headers=headers)
    print_response(response)

    if response.status_code == 200:
        data = response.json()
        if data.get('data', {}).get('wechat_status') == 'connected':
            print("微信已连接")
            return True

    return False

def test_listen_reactivate():
    """测试监听对象重新激活功能"""
    # 检查微信状态
    if not check_wechat_status():
        # 尝试初始化微信
        if not initialize_wechat():
            print("初始化微信失败，测试终止")
            return False

    # 测试对象
    test_who = "文件传输助手"  # 替换为您要测试的聊天对象

    # 先移除可能存在的监听对象
    remove_listen_chat(test_who)

    # 添加监听对象
    if not add_listen_chat(test_who):
        print("添加监听对象失败，测试终止")
        return False

    # 获取监听消息
    get_listen_messages(test_who)

    # 模拟关闭聊天窗口
    print("\n=== 请手动关闭聊天窗口: {} ===".format(test_who))
    input("关闭窗口后按回车继续...")

    # 多次获取监听消息，测试错误日志捕获
    for i in range(5):
        print(f"\n=== 第 {i+1} 次测试窗口激活失败情况 ===")
        get_listen_messages(test_who)
        time.sleep(1)  # 等待1秒

    # 手动测试重新激活功能
    print("\n=== 手动测试重新激活功能 ===")
    reactivate_listen_chat(test_who)

    # 再次获取监听消息，检查是否恢复正常
    print("\n=== 再次获取监听消息，检查是否恢复正常 ===")
    get_listen_messages(test_who)

    return True

if __name__ == "__main__":
    try:
        test_listen_reactivate()
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
