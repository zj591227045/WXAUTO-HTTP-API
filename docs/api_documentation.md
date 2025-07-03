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
- 3003: 文件下载失败
- 4001: 群操作失败
- 5001: 好友操作失败

## API 功能分类

### 基础功能
- 认证相关 (`/api/auth/`)
- 微信基础功能 (`/api/wechat/`)
- 系统功能 (`/api/system/`, `/api/health`)

### 消息功能
- 消息发送接收 (`/api/message/`)
- 消息监听 (`/api/message/listen/`)
- 消息操作 (`/api/message/`)
- 聊天窗口操作 (`/api/chat-window/`)

### 新增功能 (v2.0)
- Chat类操作 (`/api/chat/`)
- 群组管理 (`/api/group/`)
- 好友管理 (`/api/friend/`)
- WeChat类扩展 (`/api/wechat/`)
- 朋友圈功能 (`/api/moments/`)
- 辅助类功能 (`/api/auxiliary/`)

### Plus版本功能
标记为 "(Plus版)" 的功能需要wxautox库支持

## API 端点详细说明

### 1. 认证相关

#### 验证API密钥
```http
POST /api/auth/verify
```

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/auth/verify \
  -H "X-API-Key: test-key-2"
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

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/wechat/initialize \
  -H "X-API-Key: test-key-2"
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

CURL 示例:
```bash
curl -X GET http://10.255.0.90:5000/api/wechat/status \
  -H "X-API-Key: test-key-2"
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

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/message/send \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": "文件传输助手",
    "message": "这是一条测试消息",
    "at_list": ["张三", "李四"],
    "clear": true
  }'
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

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/message/send-typing \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": "文件传输助手",
    "message": "这是打字机模式消息\n这是第二行",
    "at_list": ["张三", "李四"],
    "clear": true
  }'
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

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/message/send-file \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": "文件传输助手",
    "file_paths": [
        "D:/test/test1.txt",
        "D:/test/test2.txt"
    ]
  }'
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

#### 下载文件
```http
POST /api/file/download
```

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/file/download \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "C:\\Code\\wxauto-ui\\wxauto文件\\部门信息表(1).xlsx"
  }'
```

请求体：
```json
{
    "file_path": "C:\\Code\\wxauto-ui\\wxauto文件\\部门信息表(1).xlsx"
}
```

响应说明：
- 成功时返回文件内容，Content-Type 为 application/octet-stream
- 失败时返回错误信息，格式如下：

```json
{
    "code": 3003,
    "message": "文件下载失败",
    "data": {
        "error": "文件不存在或无法访问"
    }
}
```

错误码：
- 3003: 文件下载失败，可能的原因：
  - 文件不存在
  - 文件路径无效
  - 文件访问权限不足
  - 其他文件系统错误

注意事项：
1. 文件路径必须使用双反斜杠(\\)作为分隔符
2. 确保文件路径有访问权限
3. 文件大小限制为100MB

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

#### 获取主窗口未读消息
```http
GET /api/message/get-next-new?savepic=false&savevideo=false&savefile=false&savevoice=false&parseurl=false
```

CURL 示例:
```bash
curl -X GET "http://10.255.0.90:5000/api/message/get-next-new?savepic=false&savevideo=false&savefile=false&savevoice=false&parseurl=false" \
  -H "X-API-Key: test-key-2"
```

查询参数：
- savepic: bool，是否保存图片（可选，默认false）
- savevideo: bool，是否保存视频（可选，默认false）
- savefile: bool，是否保存文件（可选，默认false）
- savevoice: bool，是否保存语音（可选，默认false）
- parseurl: bool，是否解析链接（可选，默认false）

响应示例：
```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "messages": {
            "张三": [
                {
                    "type": "text",
                    "content": "你好",
                    "sender": "张三",
                    "id": "123456",
                    "mtype": 1,
                    "sender_remark": "老张"
                }
            ]
        }
    }
}
```

### 4. 消息监听相关接口

#### 添加监听对象
```http
POST /api/message/listen/add
```

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/message/listen/add \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "who": "测试群",
    "savepic": false,
    "savevideo": false,
    "savefile": false,
    "savevoice": false,
    "parseurl": false,
    "exact": false
  }'
```

请求体：
```json
{
    "who": "测试群",
    "savepic": false,      // 可选，是否保存图片
    "savevideo": false,    // 可选，是否保存视频 
    "savefile": false,     // 可选，是否保存文件
    "savevoice": false,    // 可选，是否保存语音
    "parseurl": false,     // 可选，是否解析URL
    "exact": false         // 可选，是否精确匹配名称
}
```

响应示例：
```json
{
    "code": 0,
    "message": "添加监听成功",
    "data": {
        "who": "测试群"
    }
}
```

#### 添加当前聊天窗口到监听列表
```http
POST /api/message/listen/add-current
```

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/message/listen/add-current \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "savepic": false,
    "savevideo": false,
    "savefile": false,
    "savevoice": false,
    "parseurl": false
  }'
```

请求体：
```json
{
    "savepic": false,      // 可选，是否保存图片
    "savevideo": false,    // 可选，是否保存视频 
    "savefile": false,     // 可选，是否保存文件
    "savevoice": false,    // 可选，是否保存语音
    "parseurl": false      // 可选，是否解析URL
}
```

响应示例：
```json
{
    "code": 0,
    "message": "添加监听成功",
    "data": {
        "who": "测试群",
        "options": {
            "savepic": false,
            "savevideo": false,
            "savefile": false,
            "savevoice": false,
            "parseurl": false
        }
    }
}
```

错误码：
- 2001: 微信未初始化
- 3001: 添加监听失败，可能的原因：
  - 未找到当前聊天窗口
  - 当前窗口不是聊天窗口（例如：主窗口）
  - 其他添加监听失败的情况

注意事项：
1. 使用此API前，请确保已打开要监听的聊天窗口
2. 如果当前窗口是微信主窗口而不是聊天窗口，API将返回错误
3. 所有选项参数都是可选的，默认值为false

#### 获取监听消息
```http
GET /api/message/listen/get?who=测试群
```

CURL 示例:
```bash
curl -X GET "http://10.255.0.90:5000/api/message/listen/get?who=测试群" \
  -H "X-API-Key: test-key-2"
```

查询参数：
- who: string，要获取消息的对象（可选，不传则获取所有监听对象的消息）

响应示例：
```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "messages": {
            "测试群": [
                {
                    "type": "text",
                    "content": "新消息",
                    "sender": "张三",
                    "id": "123456",
                    "mtype": 1,
                    "sender_remark": "老张"
                }
            ]
        }
    }
}
```

#### 移除监听对象
```http
POST /api/message/listen/remove
```

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/message/listen/remove \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "who": "测试群"
  }'
```

请求体：
```json
{
    "who": "测试群"
}
```

响应示例：
```json
{
    "code": 0,
    "message": "移除监听成功",
    "data": {
        "who": "测试群"
    }
}
```

### 5. 聊天窗口操作接口

注意：以下接口需要先通过 `/api/message/listen/add` 将目标添加到监听列表。

#### 发送普通消息
```http
POST /api/chat-window/message/send
```

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/chat-window/message/send \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "who": "测试群",
    "message": "测试消息",
    "at_list": ["张三", "李四"],
    "clear": true
  }'
```

请求体：
```json
{
    "who": "测试群",
    "message": "测试消息",
    "at_list": ["张三", "李四"],  // 可选
    "clear": true                // 可选，是否清除输入框
}
```

响应示例：
```json
{
    "code": 0,
    "message": "发送成功",
    "data": {
        "message_id": "success"
    }
}
```

#### 发送打字机模式消息
```http
POST /api/chat-window/message/send-typing
```

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/chat-window/message/send-typing \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "who": "测试群",
    "message": "测试消息",
    "at_list": ["张三", "李四"],
    "clear": true
  }'
```

请求体和响应格式同上。

#### 发送文件
```http
POST /api/chat-window/message/send-file
```

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/chat-window/message/send-file \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "who": "测试群",
    "file_paths": [
        "D:/test/test1.txt",
        "D:/test/test2.txt"
    ]
  }'
```

请求体：
```json
{
    "who": "测试群",
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

#### @所有人
```http
POST /api/chat-window/message/at-all
```

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/chat-window/message/at-all \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "who": "测试群",
    "message": "请大家注意"
  }'
```

请求体：
```json
{
    "who": "测试群",
    "message": "请大家注意"  // 可选
}
```

响应示例：
```json
{
    "code": 0,
    "message": "发送成功",
    "data": {
        "message_id": "success"
    }
}
```

#### 获取聊天窗口信息
```http
GET /api/chat-window/info?who=测试群
```

CURL 示例:
```bash
curl -X GET "http://10.255.0.90:5000/api/chat-window/info?who=测试群" \
  -H "X-API-Key: test-key-2"
```

响应示例：
```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "member_count": 100,
        "name": "测试群",
        "members": ["张三", "李四"]
    }
}
```

#### 移除监听对象 (兼容接口)
```http
POST /api/message/listen/remove
```

<div class="api-test-container">
<div class="api-spec">

**请求体：**
```json
{
    "nickname": "测试群"
}
```

**响应示例：**
```json
{
    "code": 0,
    "message": "移除监听成功",
    "data": {
        "nickname": "测试群",
        "library": "wxauto"
    }
}
```

</div>
<div class="api-test">

**API测试工具**

<form id="messageListenRemoveForm">
<div class="form-group">
    <label>聊天对象昵称:</label>
    <input type="text" id="messageListenRemoveNickname" value="测试群" placeholder="请输入聊天对象昵称">
</div>
<button type="button" onclick="testMessageListenRemove()">移除监听对象</button>
</form>

<div class="curl-preview">
<strong>CURL预览:</strong>
<pre id="messageListenRemoveCurl">curl -X POST http://localhost:5000/api/message/listen/remove \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "测试群"
  }'</pre>
</div>

<div class="response-container">
<strong>响应结果:</strong>
<pre id="messageListenRemoveResponse">点击"移除监听对象"按钮查看响应</pre>
</div>

</div>
</div>

### 6. 群组相关接口

#### 获取群列表
```http
GET /api/group/list
```

CURL 示例:
```bash
curl -X GET http://10.255.0.90:5000/api/group/list \
  -H "X-API-Key: test-key-2"
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

CURL 示例:
```bash
# 重命名群
curl -X POST http://10.255.0.90:5000/api/group/manage \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "测试群",
    "action": "rename",
    "params": {
        "new_name": "新群名"
    }
  }'

# 退出群
curl -X POST http://10.255.0.90:5000/api/group/manage \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "测试群",
    "action": "quit"
  }'
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

### 7. 好友相关接口

#### 获取好友列表
```http
GET /api/contact/list
```

CURL 示例:
```bash
curl -X GET http://10.255.0.90:5000/api/contact/list \
  -H "X-API-Key: test-key-2"
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

CURL 示例:
```bash
curl -X POST http://10.255.0.90:5000/api/contact/add \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": "wxid_xxxxx",
    "message": "你好，我是...",
    "remark": "备注名",
    "tags": ["同事", "朋友"]
  }'
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

### 8. 健康检查接口

获取服务和微信连接状态。

```http
GET /api/health
```

CURL 示例:
```bash
curl -X GET http://10.255.0.90:5000/api/health \
  -H "X-API-Key: test-key-2"
```

响应示例：
```json
{
    "code": 0,
    "message": "服务正常",
    "data": {
        "status": "ok",
        "wechat_status": "connected",
        "uptime": 3600
    }
}
```

### 9. 系统监控接口

获取当前系统的CPU和内存使用情况。

```http
GET /api/system/resources
```

CURL 示例:
```bash
curl -X GET http://10.255.0.90:5000/api/system/resources \
  -H "X-API-Key: test-key-2"
```

响应示例：
```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "cpu": {
            "usage_percent": 45.2,
            "core_count": 8
        },
        "memory": {
            "total": 16384,          // 单位：MB
            "used": 8192,            // 单位：MB
            "free": 8192,            // 单位：MB
            "usage_percent": 50.0
        }
    }
}
```

响应说明：
- cpu.usage_percent: CPU总体使用率（百分比）
- cpu.core_count: CPU核心数
- memory.total: 总内存大小（MB）
- memory.used: 已使用内存（MB）
- memory.free: 空闲内存（MB）
- memory.usage_percent: 内存使用率（百分比）

注意事项：
1. 此接口返回的是系统级别的资源使用情况
2. CPU使用率为所有核心的平均值
3. 内存数据包含系统缓存

## 注意事项

1. 所有接口调用都需要先调用初始化接口
2. 注意处理接口调用频率，避免触发微信限制
3. 文件相关操作需要确保文件路径正确且有访问权限
4. 建议在调用接口前先检查微信在线状态

## 使用注意事项

1. 所有接口调用前请确保：
   - 已通过API密钥验证
   - 已调用初始化接口
   - 微信处于登录状态

2. 使用监听相关功能时：
   - 添加监听前请确认对象存在
   - 及时处理监听消息避免内存占用过大
   - 不再需要时记得移除监听

3. 发送消息时：
   - 注意消息频率，避免触发微信限制
   - 文件发送前确认路径正确且有访问权限
   - 使用打字机模式时预留合适的打字间隔

4. 异常处理：
   - 妥善处理各类错误码
   - 实现合适的重试机制
   - 保持日志记录便于问题排查

## 开发建议

1. 使用合适的HTTP客户端库
2. 实现请求重试和超时处理
3. 做好异常捕获和日志记录
4. 合理设置并发和队列处理
5. 定期检查微信状态保持连接

## 示例代码

### Python示例

```python
import requests

class WxAutoAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def initialize(self):
        response = requests.post(
            f"{self.base_url}/api/wechat/initialize",
            headers=self.headers
        )
        return response.json()
    
    def send_message(self, receiver, message, at_list=None):
        data = {
            'receiver': receiver,
            'message': message,
            'at_list': at_list or []
        }
        response = requests.post(
            f"{self.base_url}/api/message/send",
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def add_listen(self, who, **kwargs):
        data = {'who': who, **kwargs}
        response = requests.post(
            f"{self.base_url}/api/message/listen/add",
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def get_messages(self, who=None):
        params = {'who': who} if who else {}
        response = requests.get(
            f"{self.base_url}/api/message/listen/get",
            headers=self.headers,
            params=params
        )
        return response.json()

# 使用示例
api = WxAutoAPI('http://10.255.0.90:5000', 'your-api-key')

# 初始化
api.initialize()

# 发送消息
api.send_message('文件传输助手', '测试消息')

# 添加监听
api.add_listen('测试群', savepic=True)

# 获取消息
messages = api.get_messages('测试群')
print(messages)
```

### JavaScript示例

```javascript
class WxAutoAPI {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json'
        };
    }

    async initialize() {
        const response = await fetch(`${this.baseUrl}/api/wechat/initialize`, {
            method: 'POST',
            headers: this.headers
        });
        return response.json();
    }

    async sendMessage(receiver, message, atList = []) {
        const response = await fetch(`${this.baseUrl}/api/message/send`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                receiver,
                message,
                at_list: atList
            })
        });
        return response.json();
    }

    async addListen(who, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/message/listen/add`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                who,
                ...options
            })
        });
        return response.json();
    }

    async getMessages(who = null) {
        const url = new URL(`${this.baseUrl}/api/message/listen/get`);
        if (who) url.searchParams.set('who', who);
        
        const response = await fetch(url, {
            headers: this.headers
        });
        return response.json();
    }
}

// 使用示例
const api = new WxAutoAPI('http://10.255.0.90:5000', 'your-api-key');

async function demo() {
    // 初始化
    await api.initialize();

    // 发送消息
    await api.sendMessage('文件传输助手', '测试消息');

    // 添加监听
    await api.addListen('测试群', { savepic: true });

    // 获取消息
    const messages = await api.getMessages('测试群');
    console.log(messages);
}

demo().catch(console.error);
```

---

## 新增API功能 (v2.0)

### Chat类操作 (`/api/chat/`)

#### 显示聊天窗口
```http
POST /api/chat/show
```

请求体：
```json
{
    "who": "测试群"
}
```

#### 加载更多聊天记录
```http
POST /api/chat/load-more-messages
```

请求体：
```json
{
    "who": "测试群"
}
```

#### 获取所有消息
```http
GET /api/chat/get-all-messages?who=测试群
```

#### 关闭聊天窗口
```http
POST /api/chat/close
```

请求体：
```json
{
    "who": "测试群"
}
```

#### 发送自定义表情 (Plus版)
```http
POST /api/chat/send-emotion
```

请求体：
```json
{
    "who": "测试群",
    "emotion_index": 1
}
```

#### 合并转发消息 (Plus版)
```http
POST /api/chat/merge-forward
```

请求体：
```json
{
    "who": "测试群",
    "message_ids": ["msg1", "msg2"],
    "to_friends": ["好友1", "好友2"]
}
```

#### 获取对话框 (Plus版)
```http
GET /api/chat/get-dialog?who=测试群
```

#### 获取置顶消息 (Plus版)
```http
GET /api/chat/get-top-message?who=测试群
```

#### 添加监听对象
```http
POST /api/chat/listen/add
```

<div class="api-test-container">
<div class="api-spec">

**请求体：**
```json
{
    "nickname": "测试群"
}
```

**响应示例：**
```json
{
    "code": 0,
    "message": "添加监听成功",
    "data": {
        "nickname": "测试群",
        "library": "wxauto"
    }
}
```

</div>
<div class="api-test">

**API测试工具**

<form id="chatListenAddForm">
<div class="form-group">
    <label>聊天对象昵称:</label>
    <input type="text" id="chatListenAddNickname" value="测试群" placeholder="请输入聊天对象昵称">
</div>
<button type="button" onclick="testChatListenAdd()">添加监听对象</button>
</form>

<div class="curl-preview">
<strong>CURL预览:</strong>
<pre id="chatListenAddCurl">curl -X POST http://localhost:5000/api/chat/listen/add \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "测试群"
  }'</pre>
</div>

<div class="response-container">
<strong>响应结果:</strong>
<pre id="chatListenAddResponse">点击"添加监听对象"按钮查看响应</pre>
</div>

</div>
</div>

#### 获取监听消息
```http
GET /api/chat/listen/get
```

<div class="api-test-container">
<div class="api-spec">

**响应示例：**
```json
{
    "code": 0,
    "message": "获取消息成功",
    "data": {
        "messages": {
            "测试群": [
                {
                    "type": "text",
                    "content": "测试消息",
                    "sender": "发送者",
                    "id": "msg123",
                    "time": "2025-06-27 23:17"
                }
            ]
        }
    }
}
```

</div>
<div class="api-test">

**API测试工具**

<form id="chatListenGetForm">
<button type="button" onclick="testChatListenGet()">获取监听消息</button>
</form>

<div class="curl-preview">
<strong>CURL预览:</strong>
<pre id="chatListenGetCurl">curl -X GET http://localhost:5000/api/chat/listen/get \
  -H "X-API-Key: test-key-2"</pre>
</div>

<div class="response-container">
<strong>响应结果:</strong>
<pre id="chatListenGetResponse">点击"获取监听消息"按钮查看响应</pre>
</div>

</div>
</div>

#### 移除监听对象
```http
POST /api/chat/listen/remove
```

<div class="api-test-container">
<div class="api-spec">

**请求体：**
```json
{
    "nickname": "测试群"
}
```

**响应示例：**
```json
{
    "code": 0,
    "message": "移除监听成功",
    "data": {
        "nickname": "测试群",
        "library": "wxauto"
    }
}
```

</div>
<div class="api-test">

**API测试工具**

<form id="chatListenRemoveForm">
<div class="form-group">
    <label>聊天对象昵称:</label>
    <input type="text" id="chatListenRemoveNickname" value="测试群" placeholder="请输入聊天对象昵称">
</div>
<button type="button" onclick="testChatListenRemove()">移除监听对象</button>
</form>

<div class="curl-preview">
<strong>CURL预览:</strong>
<pre id="chatListenRemoveCurl">curl -X POST http://localhost:5000/api/chat/listen/remove \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "测试群"
  }'</pre>
</div>

<div class="response-container">
<strong>响应结果:</strong>
<pre id="chatListenRemoveResponse">点击"移除监听对象"按钮查看响应</pre>
</div>

</div>
</div>

### 群组管理 (`/api/group/`)

#### 添加群成员 (Plus版)
```http
POST /api/group/add-members
```

请求体：
```json
{
    "group": "测试群",
    "members": ["好友1", "好友2"],
    "reason": "邀请理由"
}
```

#### 获取群成员列表 (Plus版)
```http
GET /api/group/get-members?who=测试群
```

或者使用POST方法：
```http
POST /api/group/get-members
```

请求体：
```json
{
    "group_name": "测试群"
}
```

#### 移除群成员 (Plus版)
```http
POST /api/group/remove-members
```

请求体：
```json
{
    "group": "测试群",
    "members": ["成员1", "成员2"]
}
```

#### 管理群聊 (Plus版)
```http
POST /api/group/manage
```

请求体：
```json
{
    "who": "测试群",
    "name": "新群名",
    "remark": "群备注",
    "myname": "我的群昵称",
    "notice": "群公告",
    "quit": false
}
```

#### 获取最近群聊列表 (Plus版)
```http
GET /api/group/get-recent-groups
```

别名路由（兼容性）：
```http
GET /api/group/get-recent?limit=10
```

**参数说明**：
- 此接口无需参数，获取所有最近聊天中的群聊

**响应示例**：
```json
{
    "code": 0,
    "message": "获取最近群聊成功",
    "data": {
        "groups": [
            ["群聊名称1", "未读消息数"],
            ["群聊名称2", "未读消息数"]
        ]
    }
}
```

#### 获取通讯录群聊列表 (Plus版)
```http
GET /api/group/get-contact-groups?speed=1&interval=0.1
```

**参数说明**：
- `speed` (可选): 滚动速度，默认为1
- `interval` (可选): 滚动时间间隔，默认为0.1秒

**响应示例**：
```json
{
    "code": 0,
    "message": "获取通讯录群聊成功",
    "data": {
        "groups": ["群聊1", "群聊2", "群聊3"]
    }
}
```

**注意**：此接口获取的是通讯录中的群聊，不是最近聊天中的群聊。如果通讯录中没有群聊，将返回空列表。要获取最近聊天中的群聊，请使用 `get-recent-groups` 接口。

### 好友管理 (`/api/friend/`)

#### 获取好友详情 (Plus版)
```http
GET /api/friend/get-details?n=10&tag=标签&timeout=60000
```

或者使用POST方法：
```http
POST /api/friend/get-details
```

请求体：
```json
{
    "n": 10,
    "tag": "标签",
    "timeout": 60000
}
```

#### 获取新好友申请 (Plus版)
```http
GET /api/friend/get-new-friends?acceptable=true
```

别名路由（兼容性）：
```http
GET /api/friend/get-new-requests?acceptable=true
```

#### 添加新好友 (Plus版)
```http
POST /api/friend/add-new-friend
```

请求体：
```json
{
    "keywords": "搜索关键词",
    "addmsg": "添加好友消息",
    "remark": "好友备注",
    "tags": ["标签1", "标签2"],
    "permission": "朋友圈",
    "timeout": 5
}
```

#### 管理好友 (Plus版)
```http
POST /api/friend/manage
```

请求体：
```json
{
    "who": "好友名",
    "remark": "新备注",
    "tags": ["新标签"]
}
```

#### 从群聊添加好友 (Plus版)
```http
POST /api/friend/add-from-group
```

请求体：
```json
{
    "who": "群名",
    "index": 1,
    "addmsg": "添加好友消息",
    "remark": "好友备注",
    "tags": ["标签"],
    "permission": "仅聊天",
    "exact": false
}
```

### WeChat类扩展 (`/api/wechat/`)

#### 获取会话列表
```http
GET /api/wechat/get-session
```

#### 发送链接卡片 (Plus版)
```http
POST /api/wechat/send-url-card
```

请求体：
```json
{
    "url": "https://example.com",
    "friends": ["好友1", "好友2"],
    "timeout": 10
}
```

#### 打开聊天窗口
```http
POST /api/wechat/chat-with
```

请求体：
```json
{
    "who": "好友名",
    "exact": false
}
```

#### 获取子窗口
```http
GET /api/wechat/get-sub-window?nickname=好友名
```

#### 获取所有子窗口
```http
GET /api/wechat/get-all-sub-windows
```

别名路由（兼容性）：
```http
GET /api/wechat/get-sub-windows
```

#### 开始监听
```http
POST /api/wechat/start-listening
```

#### 停止监听
```http
POST /api/wechat/stop-listening
```

请求体：
```json
{
    "remove": true
}
```

#### 切换到聊天页面
```http
POST /api/wechat/switch-to-chat
```

#### 切换到联系人页面
```http
POST /api/wechat/switch-to-contact
```

#### 检查在线状态 (Plus版)
```http
GET /api/wechat/is-online
```

#### 获取个人信息 (Plus版)
```http
GET /api/wechat/get-my-info
```

#### 保持程序运行
```http
POST /api/wechat/keep-running
```

请求体：
```json
{
    "timeout": 0
}
```

### 消息操作 (`/api/message/`)

#### 点击消息
```http
POST /api/message/click
```

请求体：
```json
{
    "who": "测试群",
    "message_id": "消息ID"
}
```

#### 引用回复消息
```http
POST /api/message/quote
```

请求体：
```json
{
    "who": "测试群",
    "message_id": "消息ID",
    "reply_text": "回复内容"
}
```

#### 转发消息
```http
POST /api/message/forward
```

请求体：
```json
{
    "who": "测试群",
    "message_id": "消息ID",
    "to_friends": ["好友1", "好友2"]
}
```

#### 拍一拍 (Plus版)
```http
POST /api/message/tickle
```

请求体：
```json
{
    "who": "测试群",
    "message_id": "消息ID"
}
```

#### 删除消息 (Plus版)
```http
POST /api/message/delete
```

请求体：
```json
{
    "who": "测试群",
    "message_id": "消息ID"
}
```

#### 下载图片/文件
```http
POST /api/message/download
```

请求体：
```json
{
    "who": "测试群",
    "message_id": "消息ID",
    "save_path": "保存路径"
}
```

#### 语音转文字
```http
POST /api/message/to-text
```

请求体：
```json
{
    "who": "测试群",
    "message_id": "语音消息ID"
}
```

#### 右键菜单操作
```http
POST /api/message/select-option
```

请求体：
```json
{
    "who": "测试群",
    "message_id": "消息ID",
    "option": "菜单选项"
}
```

### 朋友圈功能 (`/api/moments/`) - Plus版

#### 进入朋友圈
```http
POST /api/moments/open
```

#### 获取朋友圈内容
```http
GET /api/moments/get-moments?n=10&timeout=10
```

#### 保存朋友圈图片
```http
POST /api/moments/save-images
```

请求体：
```json
{
    "moment_index": 0,
    "save_path": "保存路径"
}
```

#### 点赞朋友圈
```http
POST /api/moments/like
```

请求体：
```json
{
    "moment_index": 0
}
```

### 辅助类功能 (`/api/auxiliary/`)

#### 点击会话
```http
POST /api/auxiliary/session/click
```

请求体：
```json
{
    "session_name": "会话名"
}
```

#### 接受好友申请 (Plus版)
```http
POST /api/auxiliary/new-friend/accept
```

请求体：
```json
{
    "friend_name": "申请人名",
    "remark": "好友备注",
    "tags": ["标签"]
}
```

#### 拒绝好友申请 (Plus版)
```http
POST /api/auxiliary/new-friend/reject
```

请求体：
```json
{
    "friend_name": "申请人名"
}
```

#### 自动登录 (Plus版)
```http
POST /api/auxiliary/login/auto
```

自动登录微信，仅可自动登录的微信有效。

请求体：
```json
{
    "wxpath": "D:/path/to/WeChat.exe",
    "timeout": 10
}
```

参数说明：
- `wxpath`: 微信客户端路径（可选，不提供时自动检测）
- `timeout`: 登录超时时间，单位秒（默认10秒）

响应示例：
```json
{
    "code": 0,
    "message": "自动登录执行完成",
    "data": {
        "wxpath": "D:/path/to/WeChat.exe",
        "timeout": 10,
        "login_result": true,
        "success": true
    }
}
```

#### 获取登录二维码 (Plus版)
```http
POST /api/auxiliary/login/qrcode
```

获取登录二维码，返回base64编码的二维码图片。

请求体：
```json
{
    "wxpath": "D:/path/to/WeChat.exe"
}
```

参数说明：
- `wxpath`: 微信客户端路径（可选，不提供时自动检测）

响应示例：
```json
{
    "code": 0,
    "message": "获取登录二维码成功",
    "data": {
        "wxpath": "D:/path/to/WeChat.exe",
        "qrcode_path": "/path/to/qrcode.png",
        "qrcode_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
        "qrcode_data_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
        "mime_type": "image/png"
    }
}
```

返回数据说明：
- `qrcode_path`: 二维码图片文件路径
- `qrcode_base64`: 二维码图片的base64编码
- `qrcode_data_url`: 可直接在HTML中使用的data URL格式
- `mime_type`: 图片MIME类型

## 版本兼容性说明

### 基础版本 (wxauto)
- 支持所有基础消息功能
- 支持监听功能
- 支持基本的聊天窗口操作

### Plus版本 (wxautox)
- 支持所有基础功能
- 支持群组管理功能
- 支持好友管理功能
- 支持朋友圈功能
- 支持高级消息操作

## 使用建议

1. **功能检查**: 使用Plus版功能前，建议先检查当前库版本
2. **错误处理**: 所有API都有完善的错误处理，请根据错误码进行相应处理
3. **监听管理**: 合理使用监听功能，避免监听过多对象影响性能
4. **文件操作**: 文件路径使用绝对路径，确保有足够的访问权限

## 更新日志

### v2.0 (2025-06-24)
- 新增Chat类完整API支持
- 新增群组管理功能
- 新增好友管理功能
- 新增朋友圈功能
- 新增消息操作功能
- 新增辅助类功能
- 完善错误处理和文档

<script>
// 从配置文件读取服务器地址和API密钥
let serverConfig = {
    baseUrl: 'http://localhost:5000',
    apiKey: 'test-key-2'
};

// 尝试从配置文件加载配置
fetch('/api/config/get')
    .then(response => response.json())
    .then(data => {
        if (data.code === 0) {
            serverConfig.baseUrl = `http://${data.data.host}:${data.data.port}`;
            serverConfig.apiKey = data.data.api_key;
            updateAllCurlPreviews();
        }
    })
    .catch(error => {
        console.log('使用默认配置');
    });

// 更新所有CURL预览
function updateAllCurlPreviews() {
    // 更新Chat监听相关的CURL预览
    updateCurlPreview('chatListenAddCurl', 'POST', '/api/chat/listen/add', {
        nickname: document.getElementById('chatListenAddNickname')?.value || '测试群'
    });

    updateCurlPreview('chatListenGetCurl', 'GET', '/api/chat/listen/get');

    updateCurlPreview('chatListenRemoveCurl', 'POST', '/api/chat/listen/remove', {
        nickname: document.getElementById('chatListenRemoveNickname')?.value || '测试群'
    });

    // 更新Message监听相关的CURL预览
    updateCurlPreview('messageListenRemoveCurl', 'POST', '/api/message/listen/remove', {
        nickname: document.getElementById('messageListenRemoveNickname')?.value || '测试群'
    });
}

// 更新CURL预览
function updateCurlPreview(elementId, method, endpoint, data = null) {
    const element = document.getElementById(elementId);
    if (!element) return;

    let curl = `curl -X ${method} ${serverConfig.baseUrl}${endpoint} \\\n  -H "X-API-Key: ${serverConfig.apiKey}"`;

    if (data) {
        curl += ` \\\n  -H "Content-Type: application/json" \\\n  -d '${JSON.stringify(data, null, 2)}'`;
    }

    element.textContent = curl;
}

// 通用API调用函数
async function callAPI(method, endpoint, data = null) {
    const options = {
        method: method,
        headers: {
            'X-API-Key': serverConfig.apiKey,
            'Content-Type': 'application/json'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${serverConfig.baseUrl}${endpoint}`, options);
        return await response.json();
    } catch (error) {
        return {
            code: -1,
            message: `请求失败: ${error.message}`,
            data: null
        };
    }
}

// Chat监听相关测试函数
async function testChatListenAdd() {
    const nickname = document.getElementById('chatListenAddNickname').value;
    if (!nickname) {
        alert('请输入聊天对象昵称');
        return;
    }

    updateCurlPreview('chatListenAddCurl', 'POST', '/api/chat/listen/add', { nickname });

    const result = await callAPI('POST', '/api/chat/listen/add', { nickname });
    document.getElementById('chatListenAddResponse').textContent = JSON.stringify(result, null, 2);
}

async function testChatListenGet() {
    const result = await callAPI('GET', '/api/chat/listen/get');
    document.getElementById('chatListenGetResponse').textContent = JSON.stringify(result, null, 2);
}

async function testChatListenRemove() {
    const nickname = document.getElementById('chatListenRemoveNickname').value;
    if (!nickname) {
        alert('请输入聊天对象昵称');
        return;
    }

    updateCurlPreview('chatListenRemoveCurl', 'POST', '/api/chat/listen/remove', { nickname });

    const result = await callAPI('POST', '/api/chat/listen/remove', { nickname });
    document.getElementById('chatListenRemoveResponse').textContent = JSON.stringify(result, null, 2);
}

// Message监听相关测试函数
async function testMessageListenRemove() {
    const nickname = document.getElementById('messageListenRemoveNickname').value;
    if (!nickname) {
        alert('请输入聊天对象昵称');
        return;
    }

    updateCurlPreview('messageListenRemoveCurl', 'POST', '/api/message/listen/remove', { nickname });

    const result = await callAPI('POST', '/api/message/listen/remove', { nickname });
    document.getElementById('messageListenRemoveResponse').textContent = JSON.stringify(result, null, 2);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    updateAllCurlPreviews();

    // 监听输入框变化，实时更新CURL预览
    const inputs = ['chatListenAddNickname', 'chatListenRemoveNickname', 'messageListenRemoveNickname'];
    inputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', updateAllCurlPreviews);
        }
    });
});
</script>

<style>
.api-test-container {
    display: flex;
    gap: 20px;
    margin: 20px 0;
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
}

.api-spec {
    flex: 1;
    padding: 20px;
    background-color: #f8f9fa;
}

.api-test {
    flex: 1;
    padding: 20px;
    background-color: #fff;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.form-group input, .form-group select, .form-group textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.form-group textarea {
    height: 80px;
    resize: vertical;
}

button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

button:hover {
    background-color: #0056b3;
}

.curl-preview {
    margin: 15px 0;
}

.curl-preview pre {
    background-color: #f1f1f1;
    padding: 10px;
    border-radius: 4px;
    font-size: 12px;
    overflow-x: auto;
}

.response-container {
    margin-top: 15px;
}

.response-container pre {
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    padding: 10px;
    border-radius: 4px;
    font-size: 12px;
    max-height: 300px;
    overflow-y: auto;
}

@media (max-width: 768px) {
    .api-test-container {
        flex-direction: column;
    }
}
</style>