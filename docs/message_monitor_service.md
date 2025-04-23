# 微信消息监控服务实现规划

## 1. 功能概述

实现一个基于Python的UI程序，提供以下核心功能：

1. 自动监控新的未读会话
2. 自动管理监听列表
3. 实时获取最新消息
4. 监控微信接口状态
5. 可视化界面展示

## 2. 技术栈选择

- UI框架：PyQt6（现代、稳定、跨平台）
- 网络请求：requests
- 状态管理：自定义状态管理器
- 定时任务：APScheduler
- 日志管理：logging
- 配置管理：Python dotenv

## 3. 系统架构设计

### 3.1 核心模块

1. **MonitorService模块**
   - 负责消息监控的核心逻辑
   - 维护监听列表
   - 定时任务调度
   - 与WxAuto HTTP API交互

2. **UI模块**
   - 主窗口界面
   - 消息列表展示
   - 状态监控面板
   - 配置管理界面

3. **数据管理模块**
   - 监听对象管理
   - 消息历史记录
   - 配置信息存储

### 3.2 数据结构设计

```python
# 监听对象数据结构
class ListenTarget:
    who: str                    # 监听对象名称
    last_message_time: datetime # 最后一条消息时间
    added_time: datetime        # 加入监听的时间
    message_count: int          # 消息计数
    is_active: bool            # 是否活跃

# 消息数据结构
class Message:
    id: str               # 消息ID
    type: str            # 消息类型
    content: str         # 消息内容
    sender: str          # 发送者
    time: datetime       # 消息时间
    chat_name: str       # 会话名称
```

## 4. 具体实现方案

### 4.1 定时任务实现

```python
class MonitorScheduler:
    def __init__(self):
        self.scheduler = APScheduler()
        self.listen_targets = {}
        
    def start(self):
        # 每30秒检查新的未读会话
        self.scheduler.add_job(self.check_new_chats, 'interval', seconds=30)
        # 每5秒获取监听列表的最新消息
        self.scheduler.add_job(self.check_listen_messages, 'interval', seconds=5)
        # 每分钟检查不活跃的监听对象
        self.scheduler.add_job(self.clean_inactive_targets, 'interval', minutes=1)
```

### 4.2 监听对象管理

- 最多同时监听30个对象
- 超过30分钟无新消息自动移除
- 使用优先队列管理监听对象
- 按最后活跃时间排序

### 4.3 UI界面设计

1. **主窗口布局**
   - 状态栏：显示微信连接状态、监听对象数量
   - 监听列表：显示当前监听的对象
   - 消息面板：实时显示最新消息
   - 配置面板：可调整监听参数

2. **功能区域**
   - 手动添加/移除监听对象
   - 查看历史消息
   - 导出消息记录
   - 调整监控参数

## 5. 实现步骤

### 5.1 第一阶段：核心服务（3天）

1. 实现MonitorService
   - 消息监控核心逻辑
   - 监听对象管理
   - API接口封装

2. 实现定时任务
   - 新会话检查
   - 消息轮询
   - 超时清理

### 5.2 第二阶段：UI开发（4天）

1. 设计并实现主窗口
2. 实现消息展示功能
3. 实现状态监控面板
4. 添加配置管理界面

### 5.3 第三阶段：功能完善（3天）

1. 添加消息存储功能
2. 实现消息导出功能
3. 添加过滤和搜索功能
4. 优化性能和资源占用

## 6. 关键代码结构

### 6.1 监控服务核心

```python
class MessageMonitorService:
    def __init__(self):
        self.scheduler = MonitorScheduler()
        self.api_client = WxAutoApiClient()
        self.listen_targets = PriorityQueue(maxsize=30)
        
    async def check_new_chats(self):
        # 获取新的未读会话
        new_messages = await self.api_client.get_next_new_message()
        for chat in new_messages:
            if not self.is_full():
                await self.add_listen_target(chat)
                
    async def check_listen_messages(self):
        # 获取监听列表的最新消息
        messages = await self.api_client.get_listen_messages()
        self.update_message_status(messages)
        
    def clean_inactive_targets(self):
        # 清理不活跃的监听对象
        current_time = datetime.now()
        for target in self.listen_targets:
            if (current_time - target.last_message_time).seconds > 1800:
                self.remove_listen_target(target)
```

### 6.2 UI主窗口

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.monitor_service = MessageMonitorService()
        self.init_ui()
        
    def init_ui(self):
        # 初始化UI组件
        self.status_bar = self.statusBar()
        self.create_main_layout()
        self.create_message_panel()
        self.create_config_panel()
```

## 7. 异常处理

1. **网络异常**
   - 自动重试机制
   - 错误状态显示
   - 断线重连

2. **资源管理**
   - 内存使用监控
   - 消息缓存清理
   - 文件句柄管理

3. **微信状态**
   - 定期检查连接
   - 自动重新初始化
   - 状态变化通知

## 8. 性能优化

1. **消息处理**
   - 使用异步处理
   - 批量处理消息
   - 消息缓存机制

2. **资源利用**
   - 合理设置轮询间隔
   - 优化数据结构
   - 内存使用控制

## 9. 测试计划

1. **单元测试**
   - 核心功能测试
   - 异常处理测试
   - 边界条件测试

2. **集成测试**
   - UI功能测试
   - 系统稳定性测试
   - 性能压力测试

## 10. 部署说明

1. **环境要求**
   - Python 3.11+
   - Windows系统
   - 微信客户端

2. **依赖安装**
   ```
   pip install PyQt6
   pip install APScheduler
   pip install requests
   ```

3. **配置说明**
   - API密钥配置
   - 监控参数设置
   - 日志级别设置

## 11. 后续优化方向

1. 添加消息关键词监控
2. 支持自定义消息处理规则
3. 添加消息统计分析功能
4. 优化UI交互体验
5. 添加多语言支持

## 12. 注意事项

1. 微信API限制
   - 遵守接口调用频率
   - 处理接口超时
   - 错误重试策略

2. 资源管理
   - 控制内存使用
   - 及时清理缓存
   - 优化性能

3. 用户体验
   - 界面响应及时
   - 状态提示清晰
   - 操作简单直观