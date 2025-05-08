# wxauto_http_api

基于wxauto的微信HTTP API接口，支持通过HTTP API调用微信功能，同时支持可选的wxautox扩展功能。

## 功能特点

- 内置wxauto微信自动化库
- 可选支持wxautox扩展功能（需单独安装）
- 提供完整的HTTP API接口
- 支持消息发送、接收、文件传输等功能
- 支持群聊、好友管理等功能

## 安装说明

### 前置条件

- Python 3.7+
- Windows操作系统
- 微信PC客户端已登录

### 安装步骤

1. 克隆本仓库

```bash
git clone https://github.com/yourusername/wxauto_http_api.git
cd wxauto_http_api
```

2. 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装wxauto和其他依赖
python install_deps.py

# 如需使用wxautox（可选）
# pip install wxautox-x.x.x.x-cpxxx-cpxxx-xxx.whl
```

或者直接运行应用，程序会自动检测并安装所需依赖：

```bash
python run.py
```

> **注意**: 本项目会自动安装所需的 wxauto 库，按照以下顺序尝试安装：
> 1. 首先尝试从 PyPI 安装
> 2. 如果 PyPI 安装失败，尝试从 GitHub 克隆并安装
> 3. 如果 GitHub 安装也失败，将使用本地 wxauto 文件夹进行安装
>
> 这种机制确保了即使在网络受限的环境中，只要有本地 wxauto 文件夹，程序也能正常运行。

## 使用说明

### 启动服务

```bash
python run.py
```

默认情况下，服务将在 `http://0.0.0.0:5000` 上启动。

### API密钥配置

在 `.env` 文件中配置API密钥：

```
API_KEYS=your_api_key1,your_api_key2
SECRET_KEY=your_secret_key
```

### API接口说明

#### 初始化微信

```
POST /api/wechat/initialize
```

#### 发送消息

```
POST /api/message/send
```

请求体：

```json
{
    "receiver": "接收者名称",
    "message": "消息内容",
    "at_list": ["@的人1", "@的人2"],
    "clear": true
}
```

#### 获取新消息

```
GET /api/message/get-next-new?savepic=true&savevideo=true&savefile=true&savevoice=true&parseurl=true
```

更多API接口请参考代码或API文档。

## 库的选择

本项目支持两种微信自动化库：

- **wxauto**: 开源的微信自动化库，功能相对基础，默认内置
- **wxautox**: 增强版的微信自动化库，提供更多功能，需单独安装

您可以通过以下方式选择使用哪个库：

1. **安装时选择**：运行 `python install_deps.py` 时，会提示您选择使用哪个库
2. **手动配置**：在 `.env` 文件中设置 `WECHAT_LIB` 参数

```bash
# 在.env文件中添加以下配置
# 使用wxauto库
WECHAT_LIB=wxauto

# 或者使用wxautox库
WECHAT_LIB=wxautox
```

如果您选择使用wxautox库，需要确保已正确安装：

```bash
# 如果您有wxautox的wheel文件
pip install wxautox-x.x.x.x-cpxxx-cpxxx-xxx.whl
```

**注意**：程序会严格按照您的选择使用指定的库，不会自动切换。如果您选择了wxautox但未安装，程序将无法启动。

## 自定义配置

在 `.env` 文件中可以进行更多配置：

```
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

## 注意事项

- 请确保微信PC客户端已登录
- 使用过程中请勿关闭微信窗口
- API密钥请妥善保管，避免泄露

## 许可证

MIT License
