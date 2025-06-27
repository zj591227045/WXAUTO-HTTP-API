#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新后的监听API端点
测试 /api/chat/listen/get 和 /api/message/listen/get 端点
验证它们是否正确使用了GetNextNewMessage方法
"""

import requests
import json
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 读取配置文件
try:
    config_path = os.path.join(os.path.dirname(__file__), 'data', 'api', 'config', 'app_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 从配置文件读取服务器地址和API密钥
    server_port = config.get('port', 5000)
    api_keys = config.get('api_keys', [])
    api_key = api_keys[0] if api_keys else 'your-api-key-here'

    BASE_URL = f"http://localhost:{server_port}"

except Exception as e:
    print(f"无法加载配置文件: {e}")
    # 使用默认值
    BASE_URL = "http://localhost:5000"
    api_key = "123456aA"

# API端点
CHAT_LISTEN_GET_URL = f"{BASE_URL}/api/chat/listen/get"
MESSAGE_LISTEN_GET_URL = f"{BASE_URL}/api/message/listen/get"

# 请求头
HEADERS = {
    'Content-Type': 'application/json',
    'X-API-Key': api_key
}

def test_api_endpoint(url, params=None, description=""):
    """测试API端点"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"URL: {url}")
    if params:
        print(f"参数: {params}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应数据:")
                print(json.dumps(data, ensure_ascii=False, indent=2))
                
                # 检查响应格式
                if 'code' in data and 'message' in data and 'data' in data:
                    print("✅ 响应格式正确")
                    
                    if data['code'] == 0:
                        print("✅ API调用成功")
                        
                        # 检查数据结构
                        if 'messages' in data['data']:
                            print("✅ 包含messages字段")
                            messages = data['data']['messages']
                            
                            if isinstance(messages, dict):
                                print(f"✅ messages是字典格式，包含{len(messages)}个聊天对象")
                                
                                # 检查消息格式
                                for chat_name, msg_list in messages.items():
                                    print(f"  聊天对象: {chat_name}, 消息数量: {len(msg_list)}")
                                    if msg_list and len(msg_list) > 0:
                                        first_msg = msg_list[0]
                                        required_fields = ['type', 'content', 'sender', 'id']
                                        missing_fields = [field for field in required_fields if field not in first_msg]
                                        if not missing_fields:
                                            print(f"  ✅ 消息格式正确")
                                        else:
                                            print(f"  ❌ 消息缺少字段: {missing_fields}")
                            elif isinstance(messages, list):
                                print(f"✅ messages是列表格式，包含{len(messages)}条消息")
                            else:
                                print(f"❌ messages格式异常: {type(messages)}")
                        else:
                            print("❌ 缺少messages字段")
                    else:
                        print(f"⚠️  API返回错误: {data['message']}")
                else:
                    print("❌ 响应格式不正确")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"原始响应: {response.text}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    """主测试函数"""
    print("开始测试更新后的监听API端点")
    print(f"服务器地址: {BASE_URL}")
    print(f"API密钥: {api_key[:10]}...")
    
    # 测试1: /api/chat/listen/get - 不指定who参数
    test_api_endpoint(
        CHAT_LISTEN_GET_URL,
        params={},
        description="Chat Listen Get - 获取所有监听消息"
    )
    
    # 测试2: /api/chat/listen/get - 指定who参数
    test_api_endpoint(
        CHAT_LISTEN_GET_URL,
        params={'who': '测试用户', 'limit': 5},
        description="Chat Listen Get - 获取指定用户消息"
    )
    
    # 测试3: /api/chat/listen/get - 带参数
    test_api_endpoint(
        CHAT_LISTEN_GET_URL,
        params={
            'savepic': 'true',
            'savefile': 'true',
            'savevoice': 'true',
            'filter_mute': 'false'
        },
        description="Chat Listen Get - 带保存参数"
    )
    
    # 测试4: /api/message/listen/get - 不指定who参数
    test_api_endpoint(
        MESSAGE_LISTEN_GET_URL,
        params={},
        description="Message Listen Get - 获取所有监听消息"
    )
    
    # 测试5: /api/message/listen/get - 指定who参数
    test_api_endpoint(
        MESSAGE_LISTEN_GET_URL,
        params={'who': '测试用户'},
        description="Message Listen Get - 获取指定用户消息"
    )
    
    # 测试6: /api/message/listen/get - 带参数
    test_api_endpoint(
        MESSAGE_LISTEN_GET_URL,
        params={
            'savepic': 'true',
            'savevideo': 'false',
            'savefile': 'true',
            'savevoice': 'true',
            'parseurl': 'false',
            'filter_mute': 'false'
        },
        description="Message Listen Get - 带保存参数"
    )
    
    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
