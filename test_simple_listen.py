#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试listen API
"""

import requests
import json

BASE_URL = "http://localhost:5000"
api_key = "123456aA"

HEADERS = {
    'Content-Type': 'application/json',
    'X-API-Key': api_key
}

def test_chat_listen_get():
    """测试chat listen get API"""
    url = f"{BASE_URL}/api/chat/listen/get"
    
    print("测试 /api/chat/listen/get (不带who参数)")
    response = requests.get(url, headers=HEADERS)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    print("\n测试 /api/chat/listen/get (带who参数)")
    response = requests.get(url, headers=HEADERS, params={'who': 'test'})
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")

if __name__ == "__main__":
    test_chat_listen_get()
