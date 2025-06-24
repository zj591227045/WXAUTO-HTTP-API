# wxauto 完整文档

> 本文档抓取自 https://plus.wxauto.org/docs/
> 抓取时间: 2025-06-24 10:16:49

## 目录

* [wxauto(x)](#wxautox)
    * [什么是 wxauto？](#-wxauto)
    * [wxauto 的主要功能](#wxauto-)
    * [安装和使用](#)
    * [会封号吗](#)
    * [交流](#)
* [一、环境配置和安装](#)
    * [一、环境配置](#)
    * [二、安装](#)
        * [1. 开源版](#1-)
        * [2. ✨Plus版](#2-plus)
    * [三、测试运行](#)
* [三、核心类概念](#)
    * [Chat](#chat)
    * [WeChat](#wechat)
        * [初始化参数](#)
    * [Message](#message)
    * [WxResponse](#wxresponse)
    * [WxParam](#wxparam)
* [二、快速开始](#)
    * [快速开始](#)
        * [获取微信实例](#)
        * [发送消息](#)
        * [获取当前聊天窗口消息](#)
* [五、使用示例](#)
        * [1. 基本使用](#1-)
        * [2. 监听消息](#2-)
        * [3. 处理好友申请](#3-)
        * [4. 使用打字机模式发送消息](#4-)
        * [5. 获取多个微信客户端](#5-)
        * [6. 自动登录](#6-)
        * [7. 获取登录二维码](#7-)
        * [8. 合并转发消息](#8-)
* [六、常见问题](#)
    * [不同获取消息的方法有什么区别](#)
        * [监听模式](#)
            * [优点](#)
            * [缺点](#)
        * [全局模式](#)
    * [为什么会掉线](#)
                * [plus版本会掉线吗](#plus)
                * [如何规避](#)
    * [掉线怎么办](#)
    * [支持Linux/Mac吗](#linuxmac)
    * [Plus版本后台模式是什么](#plus)
    * [是否支持微信多开](#)
    * [为什么安装成功但是无法导入](#)
    * [支持企业微信吗](#)
    * [提示](#)
    * [有什么限制](#)
    * [会持续更新吗](#)
    * [可以最小化吗](#)
* [四、核心类方法文档](#)
* [Chat类](#chat)
    * [Chat 类属性](#chat-)
        * [聊天窗口类型 chat_type](#-chattype)
    * [Chat 类方法](#chat-)
        * [显示窗口 Show](#-show)
        * [获取聊天窗口信息 ChatInfo](#-chatinfo)
        * [✨@所有人 AtAll](#-atall)
        * [发送消息 SendMsg](#-sendmsg)
        * [✨发送文本消息（打字机模式）SendTypingText](#sendtypingtext)
        * [发送文件 SendFiles](#-sendfiles)
        * [✨发送自定义表情 SendEmotion](#-sendemotion)
        * [获取当前聊天窗口的所有消息 GetAllMessage](#-getallmessage)
        * [加载当前窗口更多聊天记录 LoadMoreMessage](#-loadmoremessage)
        * [✨添加群成员 AddGroupMembers](#-addgroupmembers)
        * [✨获取当前聊天群成员 GetGroupMembers](#-getgroupmembers)
        * [✨移除群成员 RemoveGroupMembers](#-removegroupmembers)
        * [✨从群聊中添加好友 AddFriendFromGroup](#-addfriendfromgroup)
        * [✨修改好友备注名或标签 ManageFriend](#-managefriend)
        * [✨管理当前群聊 ManageGroup](#-managegroup)
        * [关闭窗口 Close](#-close)
        * [✨合并转发消息 MergeForward](#-mergeforward)
        * [✨获取对话框 GetDialog](#-getdialog)
        * [✨移除置顶消息 GetTopMessage](#-gettopmessage)
* [Message类](#message)
        * [chat_info](#chatinfo)
        * [✨ get_all_text](#-getalltext)
        * [roll_into_view](#rollintoview)
    * [SystemMessage](#systemmessage)
    * [TickleMessage](#ticklemessage)
    * [TimeMessage](#timemessage)
    * [HumanMessage](#humanmessage)
        * [click](#click)
        * [select_option](#selectoption)
        * [quote](#quote)
        * [forward](#forward)
        * [✨tickle](#tickle)
        * [✨delete](#delete)
        * [✨download_head_image](#downloadheadimage)
    * [FriendMessage](#friendmessage)
        * [✨sender_info](#senderinfo)
        * [✨at](#at)
        * [✨add_friend](#addfriend)
        * [✨multi_select](#multiselect)
    * [SelfMessage](#selfmessage)
    * [TextMessage](#textmessage)
    * [QuoteMessage](#quotemessage)
        * [✨download_quote_image](#downloadquoteimage)
        * [✨click_quote](#clickquote)
    * [ImageMessage](#imagemessage)
        * [download](#download)
    * [VideoMessage](#videomessage)
    * [VoiceMessage](#voicemessage)
        * [to_text](#totext)
    * [FileMessage](#filemessage)
    * [✨LocationMessage](#locationmessage)
    * [✨LinkMessage](#linkmessage)
        * [✨get_url](#geturl)
    * [✨EmotionMessage](#emotionmessage)
    * [✨MergeMessage](#mergemessage)
        * [✨get_messages](#getmessages)
    * [✨PersonalCardMessage](#personalcardmessage)
    * [✨NoteMessage](#notemessage)
        * [✨get_content](#getcontent)
        * [✨save_files](#savefiles)
        * [✨to_markdown](#tomarkdown)
    * [OtherMessage](#othermessage)
* [WeChat类](#wechat)
    * [WeChat 类方法](#wechat-)
        * [概念](#)
        * [保持程序运行 KeepRunning](#-keeprunning)
        * [获取当前会话列表 GetSession](#-getsession)
        * [✨发送链接卡片 SendUrlCard](#-sendurlcard)
        * [打开聊天窗口 ChatWith](#-chatwith)
        * [获取子窗口实例 GetSubWindow](#-getsubwindow)
        * [获取所有子窗口实例 GetAllSubWindow](#-getallsubwindow)
        * [添加监听聊天窗口 AddListenChat](#-addlistenchat)
        * [移除监听聊天 RemoveListenChat](#-removelistenchat)
        * [开始监听 StartListening](#-startlistening)
        * [停止监听 StopListening](#-stoplistening)
        * [✨进入朋友圈 Moments](#-moments)
        * [获取下一个新消息 GetNextNewMessage](#-getnextnewmessage)
        * [✨获取好友列表 GetFriendDetails](#-getfrienddetails)
        * [✨获取新的好友申请列表 GetNewFriends](#-getnewfriends)
        * [✨添加新的好友 AddNewFriend](#-addnewfriend)
        * [✨获取最近群聊名称列表 GetAllRecentGroups](#-getallrecentgroups)
        * [切换到聊天页面 SwitchToChat](#-switchtochat)
        * [切换到联系人页面 SwitchToContact](#-switchtocontact)
        * [✨是否在线 IsOnline](#-isonline)
        * [✨获取我的信息 GetMyInfo](#-getmyinfo)
        * [✨获取通讯录群聊列表 GetContactGroups](#-getcontactgroups)
* [✨朋友圈类](#)
    * [MomentsWnd](#momentswnd)
        * [GetMoments](#getmoments)
        * [Refresh](#refresh)
        * [close](#close)
    * [Moments](#moments)
        * [获取朋友圈内容](#)
        * [SaveImages](#saveimages)
        * [Like](#like)
        * [Comment](#comment)
* [其他类](#)
        * [SessionElement](#sessionelement)
            * [double_click](#doubleclick)
            * [✨hide](#hide)
            * [✨select_option](#selectoption)
        * [NewFriendElement](#newfriendelement)
            * [accept](#accept)
            * [✨reply](#reply)
            * [✨get_account](#getaccount)
        * [✨LoginWnd](#loginwnd)
            * [login](#login)
            * [get_qrcode](#getqrcode)
            * [reopen](#reopen)
            * [open](#open)
        * [WeChatImage](#wechatimage)
            * [ocr](#ocr)
            * [save](#save)
        * [✨WeChatDialog](#wechatdialog)

---

# wxauto(x)

探索以下部分，了解如何使用 wxauto：

文档中标题前缀为✨标志的，为Plus版本特有方法，开源版无法调用

## 什么是 wxauto？

wxauto 是我在2020年开发的一个基于 UIAutomation 的开源 Python 微信自动化库，最初只是一个简单的脚本，只能获取消息和发送消息，经历了2年多的停滞，期间很多网友留言说需要更多的功能，所以在2023年针对新版微信重新开发了 wxauto，增加了更多的功能，即使 Python 初学者也可以简单上手自动化微信操作。目前已实现很多日常的微信操作的自动化，如自动发送消息、自动添加好友、自动回复、自动获取聊天记录、图片、文件等功能，后续还会根据反馈更新更多功能。

## wxauto 的主要功能

* 消息发送：支持发送文字、图片、文件、@群好友、引用消息等功能
* 聊天记录：可获取好友的聊天记录内容
* 监听消息：实时获取指定监听好友（群）的新消息
* 其他定制功能：根据需求定制自动化流程，满足各种特殊需求。

## 安装和使用

安装 wxauto 非常简单，在命令行输入以下命令即可：

```bash
pip install wxauto
```

接下来，可以按照以下步骤进行基本配置和使用：

引入 wxauto 库：

```python
from wxauto import WeChat
```

初始化微信对象：

```python
wx = WeChat()
```

发送消息：

```python
# 给文件传输助手发送消息
wx.SendMsg('这是通过wxauto发给你的消息！', '文件传输助手')
```

就这么简单几步，你就可以开始使用 wxauto 了！

## 会封号吗

不封号。

该项目基于Windows官方API开发，不涉及任何侵入、破解、抓包微信客户端应用，完全以人操作微信的行为执行操作

但是如果你有以下行为，即使手动操作也有风控的风险：

* 曾用hook类或webhook类微信工具，如dll注入、itchat及其衍生产品
* 频繁且大量的发送消息、添加好友等，导致风控
* 高频率发送机器人特征明显的消息，导致被人举报，致使行为风控
* 扫码手机与电脑客户端不在同一个城市，导致异地风控
* 低权重账号做太多动作，低权重账号可能包括：新注册账号长期未登录或不活跃账号未实名认证账号未绑定银行卡账号曾被官方处罚的账号…
* 新注册账号
* 长期未登录或不活跃账号
* 未实名认证账号
* 未绑定银行卡账号
* 曾被官方处罚的账号
* …

## 交流

有任何问题或建议，欢迎加作者好友，备注wxauto

# 一、环境配置和安装

## 一、环境配置

| 环境 | 版本 || --- | --- | --- | --- || Python | 3.9-3.12 || OS | Windows10+, Windows Server2016+ || 微信 | 3.9.8+（不支持4.0） |

## 二、安装

### 1. 开源版

### 2. ✨Plus版

```bash
pip install wxautox

# 或指定python版本安装：
py -3.12 -m pip install wxautox
```

注意

仅支持 Python3.9 至 3.12

激活：

```shell
wxautox -a 激活码
```

## 三、测试运行

```python
from wxauto import WeChat   # 开源版
# from wxautox import WeChat   # ✨Plus版

# 初始化微信实例
wx = WeChat()

# 发送消息
wx.SendMsg("你好", who="文件传输助手")

# 获取当前聊天窗口消息
msgs = wx.GetAllMessage()

for msg in msgs:
    print('==' * 30)
    print(f"{msg.sender}: {msg.content}")
```

Success

✅ 如果测试运行成功，恭喜您，环境配置完成！



# 二、快速开始

## 快速开始

### 获取微信实例

```python
from wxauto import WeChat

# 初始化微信实例
wx = WeChat()
```

### 发送消息

```python
# 发送消息
wx.SendMsg("你好", who="文件传输助手")
```

### 获取当前聊天窗口消息

```python
# 获取当前聊天窗口消息
msgs = wx.GetAllMessage()

for msg in msgs:
    print('==' * 30)
    print(f"{msg.sender}: {msg.content}")
```

✅ 恭喜，你已经成功进行了自动化操作，接下来你可以继续探索更多功能。

# 五、使用示例

### 1. 基本使用

```python
from wxautox import WeChat

# 初始化微信实例
wx = WeChat()

# 发送消息
wx.SendMsg("你好", who="张三")

# 获取当前聊天窗口消息
msgs = wx.GetAllMessage()
for msg in msgs:
    print(f"消息内容: {msg.content}, 消息类型: {msg.type}")
```

### 2. 监听消息

```python
from wxautox import WeChat
from wxautox.msgs import FriendMessage
import time

wx = WeChat()

# 消息处理函数
def on_message(msg, chat):
    # 示例1：将消息记录到本地文件
    with open('msgs.txt', 'a', encoding='utf-8') as f:
        f.write(msg.content + '\n')

    # 示例2：自动下载图片和视频
    if msg.type in ('image', 'video'):
        print(msg.download())

    # 示例3：自动回复收到
    if isinstance(msg, FriendMessage):
        time.sleep(len(msg.content))
        msg.quote('收到')

    ...# 其他处理逻辑，配合Message类的各种方法，可以实现各种功能

# 添加监听，监听到的消息用on_message函数进行处理
wx.AddListenChat(nickname="张三", callback=on_message)

# 保持程序运行
wx.KeepRunning()
```

```python
# ... 程序运行一段时间后 ...

# 移除监听
wx.RemoveListenChat(nickname="张三")
```

### 3. 处理好友申请

```python
from wxautox import WeChat

wx = WeChat()

# 获取新的好友申请
newfriends = wx.GetNewFriends(acceptable=True)

# 处理好友申请
tags = ['同学', '技术群']
for friend in newfriends:
    remark = f'备注_{friend.name}'
    friend.accept(remark=remark, tags=tags)  # 接受好友请求，并设置备注和标签
```

### 4. 使用打字机模式发送消息

```python
from wxautox import WeChat

wx = WeChat()

# 普通文本发送
wx.SendTypingText("你好，这是一条测试消息", who="张三")

# 使用@功能和换行
wx.SendTypingText("各位好：\n{@张三} 请负责前端部分\n{@李四} 请负责后端部分", who="项目群")
```

### 5. 获取多个微信客户端

```python
from wxautox import get_wx_clients

# 获取所有微信客户端
clients = get_wx_clients()
for client in clients:
    print(f"微信客户端: {client}")
```

### 6. 自动登录

```python
from wxautox import LoginWnd

wxpath = "D:/path/to/WeChat.exe"

# 创建登录窗口
loginwnd = LoginWnd(wxpath)

# 登录微信
loginwnd.login()
```

### 7. 获取登录二维码

```python
from wxautox import LoginWnd

wxpath = "D:/path/to/WeChat.exe"

# 创建登录窗口
loginwnd = LoginWnd(wxpath)

# 获取登录二维码图片路径
qrcode_path = loginwnd.get_qrcode()
print(qrcode)
```

### 8. 合并转发消息

```python
from wxautox import WeChat
from wxautox.msgs import HumanMessage

wx = WeChat()

# 打开指定聊天窗口
wx.ChatWith("工作群")

# 获取消息列表
msgs = wx.GetAllMessage()

# 多选最后五条消息
n = 0
for msg in msgs[::-1]:
    if n >= 5:
        break
    if isinstance(msg, HumanMessage):
        n += 1
        msg.multi_select()

# 执行合并转发
targets = [
    '张三',
    '李四
]
wx.MergeForward(targets)
```

# 六、常见问题

## 不同获取消息的方法有什么区别

wxauto中，有以下获取消息的方法，除GetAllMessage之外，其余方法均用于获取新消息

| 方法 | 说明 || --- | --- | --- | --- || GetAllMessage | 获取当前聊天页面中已加载的消息 || GetNextNewMessage | 获取微信主窗口中，其中一个未设置消息免打扰窗口的新消息 || AddListenMessage | 获取监听模式下聊天窗口的新消息 |

### 监听模式

AddListenMessage

调用AddListenMessage方法将目标聊天窗口独立出去加入监听列表，获取新消息，并触发回调函数来处理每一条消息

#### 优点

* 准确
* 读取速度快

#### 缺点

* 数量限制，最多设置40个监听对象

### 全局模式

GetNextNewMessage

获取所有微信主窗口中，未被设置为消息免打扰的窗口中的新消息

* 没有数量限制，无差别获取所有窗口新消息

* 必须进行UI操作，速度可能相较监听模式慢些该方法原理是获取会话列表中，聊天对象头像上的未读消息角标数字来判断新消息数，然后切换到该聊天窗口，获取新消息

必须进行UI操作，速度可能相较监听模式慢些

该方法原理是获取会话列表中，聊天对象头像上的未读消息角标数字来判断新消息数，然后切换到该聊天窗口，获取新消息

## 为什么会掉线

掉线是微信3.9.9及以后的版本中加入的机制，客户端频繁操作导致的

##### plus版本会掉线吗

会，手动操作频繁也会掉线，是微信客户端的机制

##### 如何规避

* 加延迟时间
* 用3.9.8版本客户端
* plus版本提供自动登录、获取二维码操作

## 掉线怎么办

掉线是微信客户端在3.9.9+版本以后新增的安全机制，主要发生在微信号在陌生电脑设备登录后触发，不会涉及封号，没有完美解决方案，以下提供两个思路：

* 微信号在同一台电脑养至可快速登录，几乎不会掉线，再进行wxauto托管
* 想办法使用3.9.8版本微信客户端，完全不掉线（绕过微信版本检测的风险自行承担）
* plus版本提供掉线检测、二维码获取、自动登录等方法

## 支持Linux/Mac吗

不支持，基于windows官方API开发，只支持windows系统

## Plus版本后台模式是什么

后台模式即不依赖鼠标移动，绝大部分场景无需将微信调到前台窗口即可进行操作，但是有些操作必须要微信在前台才可以操作成功，例如获取发送者详情信息等；

大部分场景下：

* 不抢占鼠标
* 执行速度快
* 窗口不必在桌面顶部也能操作

## 是否支持微信多开

wxauto项目不支持一切违反官方用户协议的操作，不建议、不支持、不提供微信多开的方法或行为。

但是如果你自行使用其他方法多开微信，plus版本可用WeChat(nickname='xxx')来区分，但wxauto不承担由你自行多开的行为导致的风险，也不保证所有功能的正常调用。

## 为什么安装成功但是无法导入

检查下安装wxautox的环境与你运行环境是否同一个python环境。

PyCharm默认会给你的项目创建一个虚拟环境，需要在虚拟环境中安装才可以调用

如果不清楚如何使用虚拟环境安装，可问 AI “怎么用pycharm的虚拟环境安装本地离线whl包”

## 支持企业微信吗

不支持。法律风险较高，影响腾讯收入，严抓

如果你的企业开启了在个人微信中接受企业消息的功能，可以在个人微信手动将企业微信群拖出来使用wxauto监听模式进行操作

## 提示

该项目为模拟操作，即模拟用户鼠标键盘操作微信客户端的行为，系统、网络、硬件等个体差异较大，

## 有什么限制

* 不可以发布到公共平台
* 不可以做违法的事情
* 个人或内部使用，不允许商业软件厂商进行集成

## 会持续更新吗

订阅期为1年，订阅期内更新免费，订阅过期后不提供更新服务，已获取的版本仍可继续使用

## 可以最小化吗

可以但是不建议。

wxauto项目本身是ui自动化，最小化会导致窗口ui绘制更新慢，自动化效率低

# 三、核心类概念

## Chat

Chat 类代表一个微信聊天窗口实例，提供了与聊天相关的操作方法，用于对微信聊天窗口进行各种操作，后续文档以变量名chat作为该类对象。

## WeChat

WeChat 类是本项目的主要入口点，它继承自 Chat 类，代表微信主窗口实例，用于对微信主窗口进行各种操作，后续文档以变量名wx作为该类对象。

### 初始化参数

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || nickname | str | None | 微信昵称，用于定位特定的微信窗口 || debug | bool | False | 是否开启调试模式 |

```python
wx = WeChat(nickname="张三")
```

## Message

Message类代表微信聊天中的消息，分为两个概念：

* 消息内容类型（type）：文本消息、图片消息、文件消息、语音消息、卡片消息等等
* 消息来源类型（attr）：系统消息、时间消息、自己发送的消息、对方发来的消息

```python
# 导入你想要的消息类型
from wxautox.msgs import (
    Message,
    TextMessage,
    FriendMessage,
    FriendTextMessage,
    ...
)

# 假设你获取到了一个消息对象
msg: Message = ...

# 如果是对方发来的消息，则回复收到
if isinstance(msg, FriendMessage):
    msg.reply("收到")
```

| type↓ attr→ | 自己的消息SelfMessage | 对方的消息FriendMessage || --- | --- | --- | --- | --- || 文本消息TextMessage | SelfTextMessage | FriendTextMessage || 引用消息QuoteMessage | SelfQuoteMessage | FriendQuoteMessage || 语音消息VoiceMessage | SelfVoiceMessage | FriendVoiceMessage || 图片消息ImageMessage | SelfImageMessage | FriendImageMessage || 视频消息VideoMessage | SelfVideoMessage | FriendVideoMessage || 文件消息FileMessage | SelfFileMessage | FriendFileMessage || 位置消息LocationMessage | SelfLocationMessage | FriendLocationMessage || 链接消息LinkMessage | SelfLinkMessage | FriendLinkMessage || 表情消息EmotionMessage | SelfEmotionMessage | FriendEmotionMessage || 合并消息MergeMessage | SelfMergeMessage | FriendMergeMessage || 名片消息PersonalCardMessage | SelfPersonalCardMessage | FriendPersonalCardMessage || 其他消息OtherMessage | SelfOtherMessage | FriendOtherMessage |

## WxResponse

该类用于该项目多个方法的返回值

```python
# 这里假设result为某个方法的WxResponse类型返回值
result: WxResponse = ...

# 判断是否成功
if result:
    data = result['data'] # 成功，获取返回数据，大多数情况下为None
else:
    print(result['message'])  # 该方法调用失败，打印错误信息
```

## WxParam

* ENABLE_FILE_LOGGER ( bool ) ：是否启用日志文件，默认True
* DEFAULT_SAVE_PATH ( str ) ：下载文件/图片默认保存路径，默认为当前工作目录下的wxautox文件下载文件夹
* ✨MESSAGE_HASH ( bool ) ：是否启用消息哈希值用于辅助判断消息，开启后会稍微影响性能，默认False
* DEFAULT_MESSAGE_XBIAS ( int ) ：头像到消息X偏移量，用于消息定位，点击消息等操作，默认51
* FORCE_MESSAGE_XBIAS ( bool ) ：是否强制重新自动获取X偏移量，如果设置为True，则每次启动都会重新获取，默认False
* LISTEN_INTERVAL ( int ) ：监听消息时间间隔，单位秒，默认1
* ✨LISTENER_EXCUTOR_WORKERS ( int ) ：监听执行器线程池大小，根据自身需求和设备性能设置，默认4
* SEARCH_CHAT_TIMEOUT ( int ) ：搜索聊天对象超时时间，单位秒，默认5

```python
from wxautox import WxParam

WxParam.LISTENER_EXCUTOR_WORKERS = 8
...
```

# 四、核心类方法文档

## Chat类

### Chat 类属性

在了解Chat类的方法之前，我想先介绍一下为什么要做这个类。 wxauto(x)这个项目的原理是模拟人工对微信客户端的操作，拿取到的所有信息都是人眼可见的部分， 所以当我们想监听某个人或群消息的时候，需要把这个人的聊天窗口独立出来，以确保UI元素不会因为微信主窗口切换聊天而丢失， 同时也不需要每来一条信息都切换聊天窗口去获取。 所以，Chat类就是用来创建一个独立的聊天窗口，并获取这个聊天窗口的信息。

### 聊天窗口类型 chat_type

获取当前聊天窗口的类型，返回值为字符串，取值范围如下：

* friend：好友
* group：群聊
* service：客服
* official：公众号

```python
chat_type = chat.chat_type
```

### Chat 类方法

### 显示窗口 Show

```python
chat.Show()
```

### 获取聊天窗口信息 ChatInfo

```python
info = chat.ChatInfo()
```

返回值：

* 类型：dict
* 描述：聊天窗口信息
* 返回值示例：

```python
# 好友
{'chat_type': 'friend', 'chat_name': '张三'}  

# 群聊
{'group_member_count': 500, 'chat_type': 'group', 'chat_name': '工作群'}  

# 客服
{'company': '@肯德基', 'chat_type': 'service', 'chat_name': '店长xxx'} 

# 公众号
{'chat_type': 'official', 'chat_name': '肯德基'} 
```

### ✨@所有人 AtAll

```python
group = '工作群'
content = """
通知：
下午xxxx
xxxx
"""

wx.AtAll(content, group)
```

msg (str): 发送的消息

​ who (str, optional): 发送给谁. Defaults to None.

​ exact (bool, optional): 是否精确匹配. Defaults to False.

参数：

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || msg | str | None | 发送的消息 || who | str | None | 发送给谁 || exact | bool | False | 是否精确匹配 |

* 类型：WxResponse
* 描述：是否发送成功

### 发送消息 SendMsg

```python
wx.SendMsg(msg="你好", who="张三", clear=True, at="李四", exact=False)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || msg | str | 必填 | 消息内容 || who | str | None | 发送对象，不指定则发送给当前聊天对象，当子窗口时，该参数无效 || clear | bool | True | 发送后是否清空编辑框 || at | Union[str, List[str]] | None | @对象，不指定则不@任何人 || exact | bool | False | 搜索who好友时是否精确匹配，当子窗口时，该参数无效 |

### ✨发送文本消息（打字机模式）SendTypingText

```python
wx.SendTypingText(msg="你好", who="张三", clear=True, exact=False)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || msg | str | 必填 | 要发送的文本消息 || who | str | None | 发送对象，不指定则发送给当前聊天对象，当子窗口时，该参数无效 || clear | bool | True | 是否清除原本的内容 || exact | bool | False | 搜索who好友时是否精确匹配，当子窗口时，该参数无效 |

示例：

```python
# 换行及@功能
wx.SendTypingText('各位下午好\n{@张三}负责xxx\n{@李四}负责xxxx', who='工作群')
```

### 发送文件 SendFiles

```python
wx.SendFiles(filepath="C:/文件.txt", who="张三", exact=False)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || filepath | str|list | 必填 | 要复制文件的绝对路径 || who | str | None | 发送对象，不指定则发送给当前聊天对象，当子窗口时，该参数无效 || exact | bool | False | 搜索who好友时是否精确匹配，当子窗口时，该参数无效 |

### ✨发送自定义表情 SendEmotion

```python
wx.SendEmotion(emotion_index=0, who="张三", exact=False)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || emotion_index | str | 必填 | 表情索引，从0开始 || who | str | None | 发送对象，不指定则发送给当前聊天对象，当子窗口时，该参数无效 || exact | bool | False | 搜索who好友时是否精确匹配，当子窗口时，该参数无效 |

### 获取当前聊天窗口的所有消息 GetAllMessage

```python
messages = wx.GetAllMessage()
```

* 类型：List[Message]
* 描述：当前聊天窗口的所有消息

### 加载当前窗口更多聊天记录 LoadMoreMessage

```python
wx.LoadMoreMessage()
```

### ✨添加群成员 AddGroupMembers

```python
wx.AddGroupMembers(group="技术交流群", members=["张三", "李四"], reason="交流技术")
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || group | str | None | 群名 || members | Union[str, List[str]] | None | 成员名或成员名列表 || reason | str | None | 申请理由，当群主开启验证时需要，不填写则取消申请 |

* 描述：是否添加成功

### ✨获取当前聊天群成员 GetGroupMembers

```python
members = wx.GetGroupMembers()
```

* 类型：List[str]
* 描述：当前聊天群成员列表

### ✨移除群成员 RemoveGroupMembers

```python
wx.RemoveGroupMembers(group="群名", members=["成员名1", "成员名2"])
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || group | str | None | 群名 || members | str | None | 成员名 |

* 描述：是否移除成功

### ✨从群聊中添加好友 AddFriendFromGroup

```python
index = 5  # 申请群里索引值为5的成员为好友
remark = "备注名"
tags = ["标签1", "标签2"]
result = wx.AddFriendFromGroup(index=index, remark=remark, tags=tags)
if result:
    print("成功发起申请")
else:
    print(f"申请失败：{result['message']}")
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || index | int | None | 群聊索引 || who | str | None | 群名，当Chat对象时该参数无效，仅WeChat对象有效 || addmsg | str | None | 申请理由，当群主开启验证时需要，不填写则取消申请 || remark | str | None | 添加好友后的备注名 || tags | list | None | 添加好友后的标签 || permission | Literal[‘朋友圈’, ‘仅聊天’] | ‘仅聊天’ | 添加好友后的权限 || exact | bool | False | 是否精确匹配群聊名 |

### ✨修改好友备注名或标签 ManageFriend

```python
wx.ManageFriend(remark="新备注名")
wx.ManageFriend(tags=["标签1", "标签2"])
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || remark | str | None | 备注名 || tags | List[str] | None | 标签列表 |

* 描述：是否成功修改备注名或标签

### ✨管理当前群聊 ManageGroup

```python
wx.ManageGroup(name="新群名")
wx.ManageGroup(remark="新备注名")
wx.ManageGroup(myname="新群昵称")
wx.ManageGroup(notice="新群公告")
wx.ManageGroup(quit=True)   # 谨慎使用
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || name | str | None | 群名称 || remark | str | None | 备注名 || myname | str | None | 我的群昵称 || notice | str | None | 群公告 || quit | bool | False | 是否退出群，当该项为True时，其他参数无效 |

### 关闭窗口 Close

```python
wx.Close()
```

### ✨合并转发消息 MergeForward

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || targets | Union[List[str], str] | None | 要转发的对象 |

* 描述：是否成功转发

### ✨获取对话框 GetDialog

```python
if dialog := wx.GetDialog():
    dialog.click_button("确定")
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || wait | int | 3 | 隐性等待时间 |

* 类型：WeChatDialog
* 描述：对话框对象，如果不存在则返回None

### ✨移除置顶消息 GetTopMessage

```python
if top_messages := wx.GetTopMessage():
    for top_message in top_messages:
        print(f"移除置顶消息: {top_message.content}")
        top_message.remove()
```

参数：无

* 类型：List[TopMsg]

## Message类

消息类中，有两个固定属性：

* attr：消息属性，即消息的来源属性system：系统消息time：时间消息tickle：拍一拍消息self：自己发送的消息friend：好友消息other：其他消息
* system：系统消息
* time：时间消息
* tickle：拍一拍消息
* self：自己发送的消息
* friend：好友消息
* other：其他消息
* type：消息类型，即消息的内容属性text：文本消息quote：引用消息voice：语音消息image：图片消息video：视频消息file：文件消息location：位置消息link：链接消息emotion：表情消息merge：合并转发消息personal_card：个人名片消息note: 笔记消息other：其他消息
* text：文本消息
* quote：引用消息
* voice：语音消息
* image：图片消息
* video：视频消息
* file：文件消息
* location：位置消息
* link：链接消息
* emotion：表情消息
* merge：合并转发消息
* personal_card：个人名片消息
* note: 笔记消息

而self和friend又可以跟消息类型所组合，所以所有消息类别如下：

|  | 自己发送的消息SelfMessage | 对方发来的消息FriendMessage || --- | --- | --- | --- | --- || 文本消息TextMessage | SelfTextMessage | FriendTextMessage || 引用消息QuoteMessage | SelfQuoteMessage | FriendQuoteMessage || 语音消息VoiceMessage | SelfVoiceMessage | FriendVoiceMessage || 图片消息ImageMessage | SelfImageMessage | FriendImageMessage || 视频消息VideoMessage | SelfVideoMessage | FriendVideoMessage || 文件消息FileMessage | SelfFileMessage | FriendFileMessage || ✨位置消息LocationMessage | SelfLocationMessage | FriendLocationMessage || ✨链接消息LinkMessage | SelfLinkMessage | FriendLinkMessage || ✨表情消息EmotionMessage | SelfEmotionMessage | FriendEmotionMessage || ✨合并消息MergeMessage | SelfMergeMessage | FriendMergeMessage || ✨名片消息PersonalCardMessage | SelfPersonalCardMessage | FriendPersonalCardMessage || ✨笔记消息NoteMessage | SelfNoteMessage | FriendNoteMessage || 其他消息OtherMessage | SelfOtherMessage | FriendOtherMessage |

简单的使用示例：

```python
from wxautox.msgs import *

... # 省略获取消息对象的过程

# 假设你获取到了一个消息对象
msg = ...

# 当消息为好友消息时，回复收到
# 方法一：
if msg.attr == 'friend':
    msg.reply('收到')

# 方法二：
if isinstance(msg, FriendMessage):
    msg.reply('收到')
```

消息基类，所有消息类型都继承自该类

属性（所有消息类型都包含以下属性）：

| 属性名 | 类型 | 描述 || --- | --- | --- | --- | --- || type | str | 消息内容类型 || attr | str | 消息来源类型 || info | Dict | 消息的详细信息 || id | str | 消息UI ID（不重复，切换UI后会变） || ✨hash | str | 消息hash值（可能重复，切换UI后不变） || sender | str | 消息发送者 || content | str | 消息内容 |

### chat_info

获取该消息所属聊天窗口的信息

```python
chat_info = msg.chat_info()
```

### ✨ get_all_text

获取消息中所有文本内容

```python
text_list = msg.get_all_text()
```

### roll_into_view

将消息滚动到视野内

```python
msg.roll_into_view()
```

### SystemMessage

系统消息，没有特殊用法

固定属性：

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || attr | str | system | 消息属性 |

### TickleMessage

拍一拍消息，继承自SystemMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || attr | str | tickle | 消息属性 |

特有属性：

| 属性 | 类型 | 描述 || --- | --- | --- | --- | --- || tickle_list | str | 拍一拍消息列表 |

### TimeMessage

时间消息

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || attr | str | time | 消息属性 |

| 属性 | 类型 | 描述 || --- | --- | --- | --- | --- || time | str | 时间 YYYY-MM-DD HH:MM:SS |

### HumanMessage

人发送的消息，即自己或好友、群友发送的消息

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || attr | str | friend | 消息属性 |

### click

点击该消息，一般特殊消息才会有作用，比如图片消息、视频消息等

```python
msg.click()
```

### select_option

右键该消息，弹出右键菜单，并选择指定选项

```python
msg.select_option("复制")
```

* 描述：操作结果

### quote

引用该消息，并回复

```python
msg.quote("回复内容")
```

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || text | str | 无 | 引用内容 || at | Union[List[str], str] | 无 | @用户列表 || timeout | int | 3 | 超时时间，单位为秒 |

### forward

转发该消息

```python
msg.forward("转发对象名称")
```

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || targets | Union[List[str], str] | 无 | 转发对象名称 || timeout | int | 3 | 超时时间，单位为秒 |

### ✨tickle

拍一拍该消息发送人

```python
msg.tickle()
```

### ✨delete

删除该消息

```python
msg.delete()
```

### ✨download_head_image

下载该消息发送人的头像

```python
msg.download_head_image()
```

* 类型：Path
* 描述：下载路径Path对象

### FriendMessage

好友、群友发送的消息，即聊天页面中，左侧人员发送的消息。继承自HumanMessage

### ✨sender_info

获取发送人信息

```python
msg.sender_info()
```

* 类型：Dict[str, str]

### ✨at

@该消息发送人

```python
msg.at('xxxxxx')
```

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || content | str | 必填 | 要发送的内容 || quote | bool | False | 是否引用该消息 |

### ✨add_friend

添加该消息的发送人为好友

```python
msg.add_friend()
```

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || addmsg | str | None | 添加好友时的附加消息，默认为None || remark | str | None | 添加好友后的备注，默认为None || tags | list | None | 添加好友后的标签，默认为None || permission | Literal[‘朋友圈’, ‘仅聊天’] | ‘朋友圈’ | 添加好友后的权限，默认为’朋友圈’ || timeout | int | 3 | 搜索好友的超时时间，默认为3秒 |

### ✨multi_select

多选该消息，仅作合并转发使用，如果不进行合并转发，请勿调用该方法

```python
msg.multi_select()
```

返回值：无

### SelfMessage

自己发送的消息，即聊天页面中，右侧自己发送的消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || attr | str | self | 消息属性 |

### TextMessage

文本消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | text | 消息属性 |

### QuoteMessage

引用消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | quote | 消息属性 |

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || quote_content | str | 引用消息内容 | 引用消息内容 |

### ✨download_quote_image

下载引用消息中的图片，返回图片路径

```python
msg.download_quote_image()
```

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || dir_path | str | None | 下载路径，默认为None || timeout | int | 10 | 超时时间，默认为10秒 |

返回值： Path: 视频路径，成功时返回该类型

### ✨click_quote

点击引用框体

```python
msg.click_quote()
```

### ImageMessage

图片消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | image | 消息属性 |

### download

下载图片，返回图片路径

```python
msg.download()
```

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || dir_path | Union[str, Path] | None | 下载图片的目录，不填则默认WxParam.DEFAULT_SAVE_PATH || timeout | int | 10 | 下载超时时间 |

* Path: 图片路径，成功时返回该类型
* WxResponse: 下载结果，失败时返回该类型

### VideoMessage

视频消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | video | 消息属性 |

下载视频，返回视频路径

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || dir_path | Union[str, Path] | None | 下载视频的目录，不填则默认WxParam.DEFAULT_SAVE_PATH || timeout | int | 10 | 下载超时时间 |

* Path: 视频路径，成功时返回该类型

### VoiceMessage

### to_text

将语音消息转换为文本，返回文本内容

```python
msg.to_text()
```

### FileMessage

文件消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | file | 消息属性 |

下载文件，返回文件路径

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || dir_path | Union[str, Path] | None | 下载文件的目录，不填则默认WxParam.DEFAULT_SAVE_PATH || timeout | int | 10 | 下载超时时间 |

* Path: 文件路径，成功时返回该类型

### ✨LocationMessage

位置消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | location | 消息属性 |

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || ✨address | str | 地址信息 | 该消息卡片的地址信息 |

### ✨LinkMessage

链接消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | link | 消息属性 |

### ✨get_url

获取链接地址

```python
msg.get_url()
```

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || timeout | int | 10 | 下载超时时间 |

* str: 链接地址

### ✨EmotionMessage

表情消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | emotion | 消息属性 |

### ✨MergeMessage

合并消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | merge | 消息属性 |

### ✨get_messages

获取合并消息中的所有消息

```python
msg.get_messages()
```

* List[str]: 合并消息中的所有消息

### ✨PersonalCardMessage

名片消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | personal_card | 消息属性 |

添加好友

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || addmsg | str | None | 添加好友时的附加消息 || remark | str | None | 添加好友后的备注 || tags | List[str] | None | 添加好友后的标签 || permission | Literal[‘朋友圈’, ‘仅聊天’] | ‘朋友圈’ | 添加好友后的权限 || timeout | int | 3 | 搜索好友的超时时间 |

* WxResponse: 是否添加成功

### ✨NoteMessage

笔记消息。继承自HumanMessage

| 属性名 | 类型 | 属性值 | 描述 || --- | --- | --- | --- | --- | --- || type | str | note | 消息属性 |

### ✨get_content

获取笔记内容

```python
from pathlib import Path

note_content_list = msg.get_content()
for content in note_content_list:
    if isintance(content, str):
        # 文本内容
        print(content)
    elif isintance(content, Path):
        # 文件路径，文件、视频、图片等
        print('文件路径：', content)
```

### ✨save_files

保存笔记中的文件

```python
msg.save_files()
```

| 参数名 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || dir_path | Union[str, Path] | None | 保存路径 |

* WxResponse: 是否保存成功，若成功则data为保存的文件路径列表

### ✨to_markdown

将笔记转换为Markdown格式

```python
msg.to_markdown()
```

* Path: markdown文件路径

### OtherMessage

其他暂未支持解析的消息类型

## WeChat类

## WeChat 类方法

### 概念

为确保您可以理解该文档的一些内容，这里先简单介绍一下 wxauto(x) 的设计思路，如下图所示，wxauto(x) 将微信窗口拆解为三部分：

* 导航栏（NavigationBox）：下图蓝色框内部分
* 会话列表（SessionBox）：下图绿色框内部分会话列表项（SessionElement）：会话列表中每一个会话的元素，如好友、群聊、公众号等
* 会话列表项（SessionElement）：会话列表中每一个会话的元素，如好友、群聊、公众号等
* 聊天框（Chat）：下图红色框内部分

```python
from wxautox import WeChat

wx = WeChat()
```

### 保持程序运行 KeepRunning

由于wxautox使用守护线程来监听消息，当程序仅用于监听模式时，主线程会退出，因此需要调用此方法来保持程序运行

```python
from wxautox import WeChat

wx = WeChat()
wx.AddListenChat('张三', callback=lambda msg, chat: ...)

# 保持程序运行，确保正常监听
wx.KeepRunning()
```

### 获取当前会话列表 GetSession

```python
sessions = wx.GetSession()
for session in sessions:
    print(session.info)
```

* 类型：List[SessionElement]
* 描述：当前会话列表

### ✨发送链接卡片 SendUrlCard

```python
wx.SendUrlCard(url="https://example.com", friends="张三", timeout=10)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || url | str | 必填 | 链接地址 || friends | Union[str, List[str]] | None | 发送对象，可以是单个用户名或用户名列表 || timeout | int | 10 | 等待时间（秒） |

* 描述：发送结果

### 打开聊天窗口 ChatWith

```python
wx.ChatWith(who="张三", exact=False)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || who | str | 必填 | 要聊天的对象 || exact | bool | False | 搜索好友时是否精确匹配 |

### 获取子窗口实例 GetSubWindow

```python
chat = wx.GetSubWindow(nickname="张三")
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || nickname | str | 必填 | 要获取的子窗口的昵称 |

* 类型：Chat
* 描述：子窗口实例

### 获取所有子窗口实例 GetAllSubWindow

```python
chats = wx.GetAllSubWindow()
```

* 类型：List[Chat]
* 描述：所有子窗口实例的列表

### 添加监听聊天窗口 AddListenChat

```python
def on_message(msg, chat):
    print(f"收到来自 {chat} 的消息: {msg.content}")

wx.AddListenChat(nickname="张三", callback=on_message)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || nickname | str | 必填 | 要监听的聊天对象 || callback | Callable[[Message, Chat], None] | 必填 | 回调函数，参数为(Message对象, Chat对象) |

* 成功时：类型：Chat描述：该监的听子窗口实例
* 描述：该监的听子窗口实例
* 失败时：类型：WxResponse描述：执行结果，成功时包含监听名称
* 描述：执行结果，成功时包含监听名称

成功时：

失败时：

### 移除监听聊天 RemoveListenChat

```python
wx.RemoveListenChat(nickname="张三")
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || nickname | str | 必填 | 要移除的监听聊天对象 |

* 描述：执行结果

### 开始监听 StartListening

```python
wx.StartListening()
```

### 停止监听 StopListening

```python
wx.StopListening()
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || remove | bool | True | 是否移出所有子窗口 |

### ✨进入朋友圈 Moments

```python
moments = wx.Moments(timeout=3)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || timeout | int | 3 | 等待时间（秒） |

* 类型：MomentsWnd
* 描述：朋友圈窗口实例

### 获取下一个新消息 GetNextNewMessage

```python
messages = wx.GetNextNewMessage(filter_mute=False)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || filter_mute | bool | False | 是否过滤掉免打扰消息 |

* 类型：Dict[str, List[Message]
* 描述：消息列表，键为聊天名称，值为消息列表
* 示例：{'chat_name': 'wxauto交流', 'chat_type': 'group', 'msg': [ <wxautox - TimeMessage(2025年5月2...) at 0x227379555d0>, <wxautox - FriendImageMessage([图片]) at 0x2273795ca10>, <wxautox - FriendTextMessage(/[微笑]) at 0x22737967c50>, <wxautox - FriendTextMessage(你点击发送会自动...) at 0x227366c4f50>, ... ] }

```python
{'chat_name': 'wxauto交流',
  'chat_type': 'group',
  'msg': [
      <wxautox - TimeMessage(2025年5月2...) at 0x227379555d0>,
      <wxautox - FriendImageMessage([图片]) at 0x2273795ca10>,
      <wxautox - FriendTextMessage(/[微笑]) at 0x22737967c50>,
      <wxautox - FriendTextMessage(你点击发送会自动...) at 0x227366c4f50>, 
      ...
    ]
}
```

### ✨获取好友列表 GetFriendDetails

```python
# 获取前10个好友详情信息
messages = wx.GetFriendDetails(n=10)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || n | int | None | 获取前n个好友详情信息 || tag | str | None | 从指定拼音首字母开始 || timeout | int | 0xFFFFF | 获取超时时间（秒） |

* 类型：List[dict]
* 描述：好友详情信息列表

Warning

* 该方法运行时间较长，约0.5~1秒一个好友的速度，好友多的话可将n设置为一个较小的值，先测试一下
* 如果遇到企业微信的好友且为已离职状态，可能导致微信卡死，需重启（此为微信客户端BUG）
* 该方法未经过大量测试，可能存在未知问题，如有问题请微信群内反馈

### ✨获取新的好友申请列表 GetNewFriends

```python
newfriends = wx.GetNewFriends(acceptable=True)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || acceptable | bool | True | 是否过滤掉已接受的好友申请 |

* 类型：List[NewFriendElement]
* 描述：新的好友申请列表

```python
newfriends = wx.GetNewFriends(acceptable=True)
tags = ['标签1', '标签2']
for friend in newfriends:
    remark = f'备注{friend.name}'
    friend.accept(remark=remark, tags=tags)  # 接受好友请求，并设置备注和标签
```

### ✨添加新的好友 AddNewFriend

```python
wx.AddNewFriend(keywords="张三", addmsg="我是小明", remark="老张", tags=["同学"], permission="朋友圈", timeout=5)
```

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || keywords | str | 必填 | 搜索关键词，可以是昵称、微信号、手机号等 || addmsg | str | None | 添加好友时的附加消息 || remark | str | None | 添加好友后的备注 || tags | List[str] | None | 添加好友后的标签 || permission | Literal[‘朋友圈’, ‘仅聊天’] | ‘朋友圈’ | 添加好友后的权限 || timeout | int | 5 | 搜索好友的超时时间（秒） |

* 描述：添加好友的结果

### ✨获取最近群聊名称列表 GetAllRecentGroups

```python
groups = wx.GetAllRecentGroups()
if groups:
    print(groups)
else:
    print('获取失败')
```

* 类型：WxResponse | List[str]: 失败时返回WxResponse，成功时返回所有最近群聊列表

### 切换到聊天页面 SwitchToChat

```python
wx.SwitchToChat()
```

### 切换到联系人页面 SwitchToContact

```python
wx.SwitchToContact()
```

### ✨是否在线 IsOnline

```python
wx.IsOnline()
```

* 类型：bool

### ✨获取我的信息 GetMyInfo

获取自己的微信号等信息

```python
wx.GetMyInfo()
```

### ✨获取通讯录群聊列表 GetContactGroups

获取通讯录中的群聊列表

```python
wx.GetContactGroups()
```

Note

自动化操作个体差异较大，根据实际情况调整以下参数，速度不合适可能导致漏掉部分群聊

| 参数 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || speed | int | 1 | 滚动速度 || interval | float | 0.1 | 滚动时间间隔 |

## ✨朋友圈类

## MomentsWnd

朋友圈窗口对象，即的是朋友圈的窗口对象，提供对朋友圈窗口的各种操作，如获取朋友圈内容、刷新、关闭等功能。

```python
from wxautox import WeChat

wx = WeChat()
pyq = wx.Moments()   # 打开朋友圈并获取朋友圈窗口对象（如果为None则说明你没开启朋友圈，需要在手机端设置）
```

### GetMoments

获取朋友圈内容

```python
# 获取当前页面的朋友圈内容
moments = pyq.GetMoments()

# 通过`next_page`参数获取下一页的朋友圈内容
moments = pyq.GetMoments(next_page=True)
```

| 参数 | 类型 | 说明 | 说明 || --- | --- | --- | --- | --- | --- || next_page | bool | False | 是否翻页后再获取 || speed1 | int | 3 | 翻页时的滚动速度，根据自己的情况进行调整，建议3-10自行调整 || speed2 | int | 1 | 翻页最后时的速度，避免翻页过多导致遗漏所以一般比speed1慢，建议1-3 |

返回值：List[Moments]

### Refresh

刷新朋友圈

```python
pyq.Refresh()
```

### close

关闭朋友圈

```python
pyq.close()
```

## Moments

朋友圈内容对象，即的是朋友圈的内容对象，提供对朋友圈的各种操作，如获取朋友圈内容、点赞、评论等功能。

```python
# 获取朋友圈对象
moments = pyq.GetMoments()

# 获取第一条朋友圈
moment = moments[0]
```

### 获取朋友圈内容

```python
# 获取朋友圈内容
info = moment.info
# {
#     'type': 'moment',            # 类型，分为`朋友圈`和`广告`
#     'id': '4236572776458165',    # ID
#     'sender': '天天鲜花2号客服',   # 发送者
#     'content': '客订花束',        # 内容，就是朋友圈的文字内容，如果没有文字内容则为空字符串
#     'time': '4分钟前',            # 发送时间
#     'img_count': 3,              # 图片数量
#     'comments': [],              # 评论
#     'addr': '',                  # 发送位置
#     'likes': []                  # 点赞
# }

moment.sender
# '天天鲜花2号客服'

moment.content
# '客订花束'

moment.time
# '4分钟前'

# info中所有的键值对都可以通过对象的属性来获取，就不一一列举了
...
```

### SaveImages

保存朋友圈图片

| 参数 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || save_index | int | list | None | 保存图片的索引，可以是一个整数或者一个列表，如果为None则保存所有图片 || savepath | str | None | 绝对路径，包括文件名和后缀，例如：“D:/Images/微信图片_xxxxxx.jpg”，如果为None则保存到默认路径 |

返回值：List[str]，保存的图片的绝对路径列表

```python
# 获取朋友圈图片
images = moment.SaveImages()
# [
#     'D:/Images/微信图片_xxxxxx1.jpg',
#     'D:/Images/微信图片_xxxxxx2.jpg',
#     'D:/Images/微信图片_xxxxxx3.jpg',
#     ...
# ]
```

### Like

点赞朋友圈

| 参数 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || like | bool | True | True点赞，False取消赞 |

```python
# 点赞
moment.Like()
# 取消赞
moment.Like(False)
```

### Comment

评论朋友圈

| 参数 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || text | str | 必填 | 评论内容 |

```python
# 评论
moment.Comment('评论内容')
```

## 其他类

该类用于该项目的一些参数，在获取WeChat实例前，可以通过修改该类的属性来修改默认参数

| 属性 | 类型 | 默认值 | 描述 || --- | --- | --- | --- | --- | --- || ENABLE_FILE_LOGGER | bool | True | 是否启用日志文件 || DEFAULT_SAVE_PATH | str | ./wxautox | 下载文件/图片默认保存路径 || ✨MESSAGE_HASH | bool | False | 是否启用消息哈希值用于辅助判断消息，开启后会稍微影响性能 || DEFAULT_MESSAGE_XBIAS | int | 51 | 头像到消息X偏移量，用于消息定位，点击消息等操作 || FORCE_MESSAGE_XBIAS | bool | False | 是否强制重新自动获取X偏移量，如果设置为True，则每次启动都会重新获取，系统设置了分辨率缩放时开启 || LISTEN_INTERVAL | int | 1 | 监听消息时间间隔，单位秒 || ✨LISTENER_EXCUTOR_WORKERS | int | 4 | 监听执行器线程池大小，根据自身需求和设备性能设置 || SEARCH_CHAT_TIMEOUT | int | 5 | 搜索聊天对象超时时间，单位秒 || ✨NOTE_LOAD_TIMEOUT | int | 30 | 微信笔记加载超时时间，单位秒 |

```python
from wxautox import WxParam

# 设置8个监听线程
WxParam.LISTENER_EXCUTOR_WORKERS = 8
...
```

### SessionElement

| 属性 | 类型 | 描述（以上图为例） || --- | --- | --- | --- | --- || name | str | 会话名（wxauto三群） || time | str | 时间（2025-05-14 14:41） || content | str | 消息内容（[10条]天道酬勤：这..） || ismute | bool | 是否消息免打扰（True） || isnew | bool | 是否有新消息（True） || new_count | int | 新消息数量（10） || info | Dict[str, Any] | 会话信息（包含了上述所有属性的dict） |

```python
from wxauto import WeChat

wx = WeChat()
sessions = wx.GetSession()
session = sessions[0]  # 获取第一个会话
```

点击会话，即切换到这个聊天窗口

```python
session.click()
```

#### double_click

双击会话，即将这个聊天窗口独立出去

```python
session.double_click()
```

删除会话

返回值：WxResponse

```python
session.delete()
```

#### ✨hide

隐藏会话

```python
session.hide()
```

#### ✨select_option

选择会话选项，即右键点击会话，然后选择某个选项

| 参数名 | 类型 | 说明 || --- | --- | --- | --- | --- || option | str | 选项名称，例如“置顶”、“标为未读”等 |

### NewFriendElement

| 属性 | 类型 | 描述（以上图为例） || --- | --- | --- | --- | --- || name | str | 对方名（诸葛孔明） || msg | str | 申请信息（wxautox） || acceptable | bool | 是否可接受（True） |

#### accept

同意添加好友

| 参数名 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || remark | str | None | 备注 || tags | list | None | 标签 || permission | str | ‘朋友圈’ | 朋友圈权限，可选值：‘全部’、‘仅聊天’ |

删除好友申请

#### ✨reply

回复好友申请

| 参数名 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || text | str | 必填 | 回复信息 |

#### ✨get_account

获取申请添加的好友的账号信息

| 参数名 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || wait | int | 5 | 等待时间 |

返回值：str

### ✨LoginWnd

该类用于微信登录、获取二维码等操作

```python
from wxautox import LoginWnd

wxlogin = LoginWnd(app_path="...")
```

| 参数名 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || app_path | str | None | 微信客户端路径 |

属性：无

#### login

登录微信

| 参数名 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || timeout | int | 10 | 登录超时时间 |

#### get_qrcode

获取二维码

| 参数名 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || path | str | None | 二维码图片的保存路径，None即本地目录下的wxauto_qrcode文件夹 |

返回值：str，二维码图片的路径

#### reopen

重新打开微信，为了避免各种弹窗影响操作，建议调用该方法后再执行login或get_qrcode

#### open

启动微信，建议在初始化的时候传入app_path参数，否则可能会启动失败

### WeChatImage

```python
from wxautox.ui.component import WeChatImage

imgwnd = WeChatImage()
```

微信图片/视频窗口类，用于处理微信图片或图片窗口的各种操作

#### ocr

识别图片中的文字，仅支持图片，不支持视频

| 参数名 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || wait | int | 10 | 隐性等待时间 |

返回值：str，识别到的文字

#### save

保存图片/视频

| 参数名 | 类型 | 默认值 | 说明 || --- | --- | --- | --- | --- | --- || dir_path | str | None | 保存的目录路径，None即本地路径下自动生成 || timeout | int | 10 | 保存超时时间 |

返回值：Path，保存的文件路径

关闭图片/视频窗口

### ✨WeChatDialog

微信对话框对象，用于处理微信对话框的各种操作

选择对话框中的选项，如“确定”、“取消”等

返回值：WxResponse对象

关闭对话框

