# WxAuto HTTP API 使用文档

## 接口认证

所有API请求都需要在请求头中包含API密钥：
```http
X-API-Key: test-key-2
```

## API接口示例

### 1. API密钥验证

验证API密钥是否有效。

```bash
curl -X POST http://10.255.0.90:5000/api/auth/verify \
  -H "X-API-Key: test-key-2"
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

#### 2.1 初始化微信

初始化微信实例，建议在使用其他接口前先调用此接口。

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

#### 2.2 获取微信状态

检查微信连接状态。

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
        "status": "online"
    }
}
```

### 3. 消息相关接口

#### 3.1 发送普通文本消息

发送普通文本消息到指定联系人或群组。

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

参数说明：
- receiver: 接收者（联系人或群组名称）
- message: 消息内容
- at_list: （可选）需要@的群成员列表
- clear: （可选）是否清除输入框，默认为true

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

#### 3.2 发送打字机模式消息

使用打字机模式发送消息（模拟真人打字效果）。

```bash
curl -X POST http://10.255.0.90:5000/api/message/send-typing \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": "文件传输助手",
    "message": "这是一条打字机模式消息\n这是第二行",
    "at_list": ["张三"],
    "clear": true
  }'
```

参数说明同普通消息发送。

#### 3.3 发送文件

发送一个或多个文件。

```bash
curl -X POST http://10.255.0.90:5000/api/message/send-file \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": "文件传输助手",
    "file_paths": [
        "D:/test/file1.txt",
        "D:/test/image.jpg"
    ]
  }'
```

参数说明：
- receiver: 接收者
- file_paths: 要发送的文件路径列表

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

### 4. 群组相关接口

#### 4.1 获取群列表

获取当前账号的群聊列表。

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
            {"name": "测试群1"},
            {"name": "测试群2"}
        ]
    }
}
```

#### 4.2 群组管理

执行群组管理操作（如重命名、退群等）。

```bash
curl -X POST http://10.255.0.90:5000/api/group/manage \
  -H "X-API-Key: test-key-2" \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "测试群",
    "action": "rename",
    "params": {
        "new_name": "新群名称"
    }
  }'
```

支持的操作类型：
- rename: 重命名群组
- quit: 退出群组

### 5. 联系人相关接口

#### 5.1 获取好友列表

获取当前账号的好友列表。

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
            {"nickname": "张三"},
            {"nickname": "李四"}
        ]
    }
}
```

### 6. 健康检查接口

获取服务和微信连接状态。

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

## 错误码说明

- 0: 成功
- 1001: 认证失败（API密钥无效）
- 1002: 参数错误
- 2001: 微信未初始化
- 2002: 微信已掉线
- 3001: 发送消息失败
- 3002: 获取消息失败
- 4001: 群操作失败
- 5001: 好友操作失败
- 5000: 服务器内部错误

## 使用建议

1. 在使用其他接口前，先调用初始化接口
2. 使用健康检查接口监控服务状态
3. 合理处理错误码，做好重试机制
4. 注意文件发送时的路径正确性
5. 群发消息时建议加入适当延时

## PowerShell示例

如果您使用PowerShell，可以使用以下格式发送请求：

```powershell
$headers = @{
    "X-API-Key" = "test-key-2"
    "Content-Type" = "application/json"
}

$body = @{
    receiver = "文件传输助手"
    message = "测试消息"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://10.255.0.90:5000/api/message/send" -Headers $headers -Body $body
```

## Python示例

使用Python requests库的示例：

```python
import requests

API_KEY = "test-key-2"
BASE_URL = "http://10.255.0.90:5000/api"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# 发送消息示例
response = requests.post(
    f"{BASE_URL}/message/send",
    headers=headers,
    json={
        "receiver": "文件传输助手",
        "message": "测试消息"
    }
)

print(response.json())