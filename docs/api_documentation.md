# WxAuto HTTP API 接口文档

## API 概述

本文档详细说明了WxAuto HTTP API的使用方法、请求格式和响应格式。所有接口都需要通过API密钥认证。

## 认证方式

所有API请求都需要在HTTP Header中包含API密钥：

```http
X-API-Key: your_api_key_here
```

## 通用响应格式

```json
{
    "code": 0,       // 状态码：0成功，非0失败
    "message": "",   // 响应消息
    "data": {}       // 响应数据
}
```

## 错误码说明

- 0: 成功
- 1001: 认证失败
- 1002: 参数错误
- 2001: 微信未初始化
- 2002: 微信已掉线
- 3001: 发送消息失败
- 3002: 获取消息失败
- 4001: 群操作失败
- 5001: 好友操作失败

## API 端点详细说明

### 1. 认证相关

#### 验证API密钥
```http
POST /api/auth/verify
```

请求头：
```http
X-API-Key: your_api_key_here
```

响应示例：
```json
{
    "code": 0,
    "message": "验证成功",
    "data": {
        "valid": true
    }
}
```

### 2. 微信基础功能

#### 初始化微信实例
```http
POST /api/wechat/initialize
```

响应示例：
```json
{
    "code": 0,
    "message": "初始化成功",
    "data": {
        "status": "connected"
    }
}
```

#### 获取微信状态
```http
GET /api/wechat/status
```

响应示例：
```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "status": "online",
        "last_active": "2025-04-23 10:30:00"
    }
}
```

### 3. 消息相关接口

#### 发送普通文本消息
```http
POST /api/message/send
```

请求体：
```json
{
    "receiver": "文件传输助手",
    "message": "这是一条测试消息",
    "at_list": ["张三", "李四"],  // 可选
    "clear": true  // 可选，是否清除输入框
}
```

响应示例：
```json
{
    "code": 0,
    "message": "发送成功",
    "data": {
        "message_id": "xxxxx"
    }
}
```

#### 发送打字机模式消息
```http
POST /api/message/send-typing
```

请求体：
```json
{
    "receiver": "文件传输助手",
    "message": "这是打字机模式消息\n这是第二行",
    "at_list": ["张三", "李四"],  // 可选
    "clear": true  // 可选
}
```

响应示例：
```json
{
    "code": 0,
    "message": "发送成功",
    "data": {
        "message_id": "xxxxx"
    }
}
```

#### 发送文件消息
```http
POST /api/message/send-file
```

请求体：
```json
{
    "receiver": "文件传输助手",
    "file_paths": [
        "D:/test/test1.txt",
        "D:/test/test2.txt"
    ]
}
```

响应示例：
```json
{
    "code": 0,
    "message": "发送成功",
    "data": {
        "success_count": 2,
        "failed_files": []
    }
}
```

#### 获取聊天记录
```http
POST /api/message/get-history
```

请求体：
```json
{
    "chat_name": "文件传输助手",
    "save_pic": false,    // 可选，是否保存图片
    "save_video": false,  // 可选，是否保存视频
    "save_file": false,   // 可选，是否保存文件
    "save_voice": false   // 可选，是否保存语音
}
```

响应示例：
```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "messages": [
            {
                "type": "text",
                "sender": "张三",
                "content": "测试消息",
                "time": "2025-04-23 10:30:00"
            }
        ]
    }
}
```

### 4. 群组相关接口

#### 获取群列表
```http
GET /api/group/list
```

响应示例：
```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "groups": [
            {
                "name": "测试群",
                "member_count": 100
            }
        ]
    }
}
```

#### 群管理操作
```http
POST /api/group/manage
```

请求体：
```json
{
    "group_name": "测试群",
    "action": "rename",  // rename/set_announcement/quit
    "params": {
        "new_name": "新群名"  // 根据action不同，参数不同
    }
}
```

响应示例：
```json
{
    "code": 0,
    "message": "操作成功",
    "data": {
        "success": true
    }
}
```

### 5. 好友相关接口

#### 获取好友列表
```http
GET /api/contact/list
```

响应示例：
```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "friends": [
            {
                "nickname": "张三",
                "remark": "张总",
                "tags": ["同事"]
            }
        ]
    }
}
```

#### 添加好友
```http
POST /api/contact/add
```

请求体：
```json
{
    "keywords": "wxid_xxxxx",  // 微信号/手机号/QQ号
    "message": "你好，我是...",
    "remark": "备注名",        // 可选
    "tags": ["同事", "朋友"]   // 可选
}
```

响应示例：
```json
{
    "code": 0,
    "message": "发送请求成功",
    "data": {
        "status": 1,  // 0:失败 1:成功 2:已是好友 3:被拉黑 4:未找到账号
        "message": "发送请求成功"
    }
}
```

## 注意事项

1. 所有接口调用都需要先调用初始化接口
2. 注意处理接口调用频率，避免触发微信限制
3. 文件相关操作需要确保文件路径正确且有访问权限
4. 建议在调用接口前先检查微信在线状态