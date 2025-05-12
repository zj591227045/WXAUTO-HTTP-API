# 🚀 wxauto_http_api

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg?cacheSeconds=2592000)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)

</div>

基于wxauto的微信HTTP API接口，提供简单易用的HTTP API调用微信功能，同时支持可选的wxautox扩展功能。通过本项目，您可以轻松地将微信集成到您的应用程序中。

## ✨ 功能特点

- 📱 **内置wxauto微信自动化库**：开箱即用，无需额外安装
- 🚀 **可选支持wxautox扩展功能**：提供更强大的功能和更高的稳定性（需单独安装）
- 🌐 **完整的HTTP API接口**：简单易用的RESTful API
- 💬 **丰富的消息功能**：支持文本、图片、文件、视频等多种消息类型
- 👥 **群聊和好友管理**：支持群聊创建、成员管理、好友添加等功能
- 🔄 **实时消息监听**：支持实时获取新消息
- 🖥️ **图形化管理界面**：提供直观的服务管理和配置界面

## 🔧 安装说明

### 前置条件

- **Python 3.7+**：确保已安装Python 3.7或更高版本
- **Windows操作系统**：目前仅支持Windows平台
- **微信PC客户端**：确保已安装并登录微信PC客户端，建议使用微信3.9版本

### 安装步骤

1. **克隆本仓库**

```bash
git clone https://github.com/yourusername/wxauto_http_api.git
cd wxauto_http_api
```

2. **安装依赖**

```bash
# 安装基础依赖
pip install -r requirements.txt
```

3. **启动应用**

```bash
# 启动图形界面
python main.py --service ui
# 或者直接双击 start_ui.bat
```

## 🚀 使用说明

### 启动方式

本项目提供两种启动方式：

1. **图形界面模式**（推荐）

```bash
# 方式1：使用Python命令
python main.py --service ui

# 方式2：直接双击批处理文件
start_ui.bat
```

2. **仅API服务模式**

```bash
# 方式1：使用Python命令
python main.py --service api

# 方式2：直接双击批处理文件
start_api.bat
```

默认情况下，API服务将在 `http://0.0.0.0:5000` 上启动。

### 图形界面功能

图形界面提供以下功能：

- **服务管理**：启动/停止API服务
- **库选择**：选择使用wxauto或wxautox库
- **插件管理**：安装/更新wxautox库
- **配置管理**：修改端口、API密钥等配置
- **日志查看**：实时查看API服务日志
- **状态监控**：监控服务状态、资源使用情况

### API密钥配置

有两种方式配置API密钥：

1. **通过图形界面配置**：
   - 点击"插件配置"按钮
   - 在弹出的对话框中设置API密钥

2. **通过配置文件配置**：
   - 在 `.env` 文件中添加以下内容：
   ```
   API_KEYS=your_api_key1,your_api_key2
   ```

### 📚 API接口说明

所有API请求都需要在请求头中包含API密钥：

```
X-API-Key: your_api_key
```

#### 初始化微信

```http
POST /api/wechat/initialize
```

#### 发送消息

```http
POST /api/message/send
Content-Type: application/json

{
    "receiver": "接收者名称",
    "message": "消息内容",
    "at_list": ["@的人1", "@的人2"],
    "clear": true
}
```

#### 获取新消息

```http
GET /api/message/get-next-new?savepic=true&savevideo=true&savefile=true&savevoice=true&parseurl=true
```

#### 添加监听对象

```http
POST /api/message/listen/add
Content-Type: application/json

{
    "who": "群名称或好友名称",
    "savepic": true
}
```

#### 获取监听消息

```http
GET /api/message/listen/get?who=群名称或好友名称
```

更多API接口请在图形界面中点击"API说明"按钮查看详细文档。

## 🔄 库的选择

本项目支持两种微信自动化库：

- **wxauto** 📱：开源的微信自动化库，功能相对基础，**默认内置**
- **wxautox** 🚀：增强版的微信自动化库，提供更多功能和更高的稳定性，**需单独安装**

### 选择使用哪个库

您可以通过以下方式选择使用哪个库：

1. **通过图形界面选择**（推荐）：
   - 在图形界面中选择"wxauto"或"wxautox"单选按钮
   - 点击"重载配置"按钮使配置生效

2. **通过配置文件选择**：
   - 在 `.env` 文件中设置 `WECHAT_LIB` 参数
   ```bash
   # 使用wxauto库
   WECHAT_LIB=wxauto

   # 或者使用wxautox库
   WECHAT_LIB=wxautox
   ```

### 安装wxautox库

如果您选择使用wxautox库，有以下几种安装方式：

1. **通过图形界面安装**（推荐）：
   - 启动程序后，在图形界面点击"安装wxautox"按钮
   - 选择您已下载的wxautox wheel文件（位于 `lib` 目录或您自己下载的位置）
   - 系统将自动安装并配置wxautox库

2. **通过命令行安装**：
   ```bash
   # 如果您有wxautox的wheel文件
   pip install lib/wxautox-x.x.x.x-cpxxx-cpxxx-xxx.whl
   ```

> **注意**：程序会严格按照您的选择使用指定的库。如果您选择了wxautox但未安装，程序会自动降级使用wxauto库。

## ⚙️ 自定义配置

### 通过图形界面配置

推荐使用图形界面进行配置，点击"插件配置"按钮可以修改以下配置：

- **端口号**：API服务监听的端口号
- **API密钥**：访问API所需的密钥

### 通过配置文件配置

您也可以在 `.env` 文件中进行更多高级配置：

```ini
# API配置
API_KEYS=your_api_key1,your_api_key2
SECRET_KEY=your_secret_key

# 服务配置
PORT=5000

# 微信监控配置
WECHAT_CHECK_INTERVAL=60
WECHAT_AUTO_RECONNECT=true
WECHAT_RECONNECT_DELAY=30
WECHAT_MAX_RETRY=3
```

## 📁 项目结构

```
wxauto_http_api/
├── app/                # 应用程序核心代码
│   ├── api/            # API接口实现
│   ├── config.py       # 配置模块
│   ├── logs.py         # 日志模块
│   ├── plugin_manager.py # 插件管理模块
│   └── wechat/         # 微信功能实现
├── build_tools/        # 打包工具
├── data/               # 数据文件
│   ├── api/            # API数据
│   └── logs/           # 日志文件
├── docs/               # 文档
├── lib/                # 第三方库
├── wxauto/             # wxauto库
├── .env                # 环境变量配置
├── main.py             # 主入口点
├── requirements.txt    # 依赖项列表
├── start_api.bat       # 启动API服务的批处理文件
└── start_ui.bat        # 启动UI服务的批处理文件
```

## ⚠️ 注意事项

- **微信客户端**：请确保微信PC客户端已登录
- **窗口状态**：使用过程中请勿关闭微信窗口
- **安全性**：API密钥请妥善保管，避免泄露
- **兼容性**：本项目仅支持Windows操作系统
- **依赖项**：确保已安装所有必要的依赖项

## 📝 许可证

[MIT License](LICENSE)

## 🤝 贡献

欢迎提交问题和功能请求！如果您想贡献代码，请提交拉取请求。
