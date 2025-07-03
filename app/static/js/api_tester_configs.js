/**
 * API测试器配置文件
 * 定义各个API端点的测试配置
 */

const API_TESTER_CONFIGS = {
    // 微信初始化
    'wechat-initialize': {
        endpoint: '/api/wechat/initialize',
        method: 'POST',
        parameters: []
    },

    // 获取微信状态
    'wechat-status': {
        endpoint: '/api/wechat/status',
        method: 'GET',
        parameters: []
    },

    // Chat类 - 获取下一条新消息
    'chat-get-next-new': {
        endpoint: '/api/chat/get-next-new',
        method: 'GET',
        parameters: []
    },

    // Chat类 - 添加消息监听
    'chat-listen-add': {
        endpoint: '/api/chat/listen/add',
        method: 'POST',
        parameters: [
            {
                name: 'who',
                label: '聊天对象',
                type: 'text',
                required: true,
                placeholder: '文件传输助手',
                description: '要添加监听的联系人或群组名称'
            }
        ]
    },

    // Chat类 - 获取监听消息
    'chat-listen-get': {
        endpoint: '/api/chat/listen/get',
        method: 'GET',
        parameters: [
            {
                name: 'who',
                label: '聊天对象',
                type: 'text',
                required: true,
                placeholder: '文件传输助手',
                description: '要获取消息的联系人或群组名称'
            },
            {
                name: 'limit',
                label: '消息数量',
                type: 'number',
                required: false,
                default: '10',
                placeholder: '10',
                description: '要获取的消息数量，默认10条'
            }
        ]
    },

    // Chat类 - 移除消息监听
    'chat-listen-remove': {
        endpoint: '/api/chat/listen/remove',
        method: 'POST',
        parameters: [
            {
                name: 'nickname',
                label: '聊天对象昵称',
                type: 'text',
                required: true,
                placeholder: '测试群',
                description: '要移除监听的联系人或群组名称'
            }
        ]
    },

    // Chat类 - 显示聊天窗口
    'chat-show': {
        endpoint: '/api/chat/show',
        method: 'POST',
        parameters: [
            {
                name: 'who',
                label: '聊天对象',
                type: 'text',
                required: true,
                placeholder: '请输入聊天对象名称',
                description: '输入要打开聊天窗口的联系人或群组名称'
            }
        ]
    },

    // Chat类 - 发送消息
    'chat-send-message': {
        endpoint: '/api/chat/send-message',
        method: 'POST',
        parameters: [
            {
                name: 'who',
                label: '聊天对象',
                type: 'text',
                required: true,
                placeholder: '文件传输助手',
                description: '输入要发送消息的联系人或群组名称'
            },
            {
                name: 'message',
                label: '消息内容',
                type: 'textarea',
                required: true,
                placeholder: 'Hello, 这是一条测试消息！',
                description: '支持文本消息，可以包含表情符号'
            },
            {
                name: 'at_list',
                label: '@用户列表',
                type: 'text',
                required: false,
                placeholder: '张三,李四,王五',
                description: '在群聊中@指定用户，多个用户用逗号分隔'
            }
        ]
    },

    // Chat类 - 发送文件
    'chat-send-file': {
        endpoint: '/api/chat/send-file',
        method: 'POST',
        parameters: [
            {
                name: 'who',
                label: '聊天对象',
                type: 'text',
                required: true,
                placeholder: '文件传输助手',
                description: '输入要发送文件的联系人或群组名称'
            },
            {
                name: 'file_paths',
                label: '文件路径列表',
                type: 'text',
                required: true,
                placeholder: 'C:\\Users\\用户名\\Desktop\\文件.txt',
                description: '输入要发送文件的完整路径，多个文件用逗号分隔'
            }
        ]
    },



    // Chat类 - 获取所有消息（监听模式）
    'chat-get-all-messages': {
        endpoint: '/api/chat/get-all-messages',
        method: 'GET',
        parameters: [
            {
                name: 'who',
                label: '聊天对象',
                type: 'text',
                required: true,
                placeholder: '文件传输助手',
                description: '要获取消息的联系人或群组名称（需要先添加到监听列表）'
            }
        ]
    },

    // 消息功能 - 发送普通消息 (兼容性接口)
    'message-send': {
        endpoint: '/api/message/send',
        method: 'POST',
        parameters: [
            {
                name: 'receiver',
                label: '接收者',
                type: 'text',
                required: true,
                placeholder: '文件传输助手',
                description: '接收者名称（联系人或群组名）'
            },
            {
                name: 'message',
                label: '消息内容',
                type: 'textarea',
                required: true,
                placeholder: '这是一条测试消息',
                description: '要发送的消息内容'
            },
            {
                name: 'at_list',
                label: '@用户列表',
                type: 'text',
                required: false,
                placeholder: '张三,李四',
                description: '@的用户列表（仅群组有效），多个用户用逗号分隔'
            },
            {
                name: 'clear',
                label: '清空输入框',
                type: 'select',
                required: false,
                options: [
                    { value: 'true', label: '是', selected: true },
                    { value: 'false', label: '否' }
                ],
                description: '发送后是否清空输入框'
            }
        ]
    },

    // 消息功能 - 发送文件 (兼容性接口)
    'message-send-file': {
        endpoint: '/api/message/send-file',
        method: 'POST',
        parameters: [
            {
                name: 'receiver',
                label: '接收者',
                type: 'text',
                required: true,
                placeholder: '文件传输助手',
                description: '接收者名称（联系人或群组名）'
            },
            {
                name: 'file_path',
                label: '文件路径',
                type: 'text',
                required: true,
                placeholder: 'C:\\Users\\用户名\\Desktop\\文件.txt',
                description: '要发送的文件完整路径'
            }
        ]
    },

    // 群组管理 - 获取群成员
    'group-get-members': {
        endpoint: '/api/group/get-members',
        method: 'POST',
        parameters: [
            {
                name: 'group_name',
                label: '群组名称',
                type: 'text',
                required: true,
                placeholder: '测试群',
                description: '要获取成员列表的群组名称'
            }
        ]
    },

    // 好友管理 - 获取好友列表
    'friend-get-list': {
        endpoint: '/api/friend/get-list',
        method: 'GET',
        parameters: []
    },

    // 好友管理 - 添加好友
    'friend-add': {
        endpoint: '/api/friend/add',
        method: 'POST',
        parameters: [
            {
                name: 'search_text',
                label: '搜索内容',
                type: 'text',
                required: true,
                placeholder: '微信号或手机号',
                description: '要添加的好友的微信号或手机号'
            },
            {
                name: 'remark',
                label: '验证消息',
                type: 'textarea',
                required: false,
                placeholder: '我是...',
                description: '发送给对方的验证消息'
            }
        ]
    },

    // WeChat扩展 - 获取联系人列表
    'wechat-get-contacts': {
        endpoint: '/api/wechat/get-contacts',
        method: 'GET',
        parameters: []
    },

    // 朋友圈 - 获取朋友圈消息
    'moments-get': {
        endpoint: '/api/moments/get',
        method: 'GET',
        parameters: [
            {
                name: 'limit',
                label: '获取数量',
                type: 'number',
                required: false,
                default: '10',
                placeholder: '10',
                description: '要获取的朋友圈消息数量'
            }
        ]
    },

    // 辅助功能 - 截图
    'auxiliary-screenshot': {
        endpoint: '/api/auxiliary/screenshot',
        method: 'POST',
        parameters: [
            {
                name: 'save_path',
                label: '保存路径',
                type: 'text',
                required: false,
                placeholder: 'C:\\Users\\用户名\\Desktop\\screenshot.png',
                description: '截图保存路径，不填则返回base64数据'
            }
        ]
    },

    // 演示用API
    'demo-status': {
        endpoint: '/api/demo/status',
        method: 'GET',
        parameters: [
            {
                name: 'status_type',
                label: '状态类型',
                type: 'select',
                required: false,
                options: [
                    { value: 'success', label: '成功状态', selected: true },
                    { value: 'error', label: '错误状态' },
                    { value: 'loading', label: '加载状态' }
                ],
                description: '选择要演示的状态类型'
            }
        ]
    },

    // 消息操作 - 转发消息
    'message-forward': {
        endpoint: '/api/message/forward',
        method: 'POST',
        parameters: [
            {
                name: 'message_id',
                label: '消息ID',
                type: 'text',
                required: true,
                placeholder: 'msg_001',
                description: '要转发的消息ID'
            },
            {
                name: 'to_contact',
                label: '转发目标',
                type: 'text',
                required: true,
                placeholder: '文件传输助手',
                description: '转发目标联系人或群组名称'
            }
        ]
    },

    // 消息操作 - 下载文件
    'message-download': {
        endpoint: '/api/message/download',
        method: 'POST',
        parameters: [
            {
                name: 'message_id',
                label: '消息ID',
                type: 'text',
                required: true,
                placeholder: 'msg_001',
                description: '要下载的文件消息ID'
            },
            {
                name: 'save_path',
                label: '保存路径',
                type: 'text',
                required: false,
                placeholder: 'C:\\Downloads\\',
                description: '文件保存路径，不填则使用默认路径'
            }
        ]
    },

    // 消息操作 - 点击消息
    'message-click': {
        endpoint: '/api/message/click',
        method: 'POST',
        parameters: [
            {
                name: 'message_id',
                label: '消息ID',
                type: 'text',
                required: true,
                placeholder: 'msg_001',
                description: '要点击的消息ID'
            }
        ]
    },

    // 消息操作 - 拍一拍
    'message-tickle': {
        endpoint: '/api/message/tickle',
        method: 'POST',
        parameters: [
            {
                name: 'contact',
                label: '联系人',
                type: 'text',
                required: true,
                placeholder: '张三',
                description: '要拍一拍的联系人名称'
            }
        ]
    },

    // 群组管理 - 添加群成员
    'group-add-members': {
        endpoint: '/api/group/add-members',
        method: 'POST',
        parameters: [
            {
                name: 'group_name',
                label: '群组名称',
                type: 'text',
                required: true,
                placeholder: '消息测试',
                description: '要添加成员的群组名称（支持group或group_name参数）'
            },
            {
                name: 'members',
                label: '成员列表',
                type: 'text',
                required: true,
                placeholder: '客服',
                description: '要添加的成员名称，支持单个成员或多个用逗号分隔'
            },
            {
                name: 'reason',
                label: '邀请理由',
                type: 'text',
                required: false,
                placeholder: '邀请您加入群聊',
                description: '添加成员时的邀请理由（可选）'
            }
        ]
    },

    // 群组管理 - 获取最近群聊
    'group-get-recent': {
        endpoint: '/api/group/get-recent',
        method: 'GET',
        parameters: [
            {
                name: 'limit',
                label: '获取数量',
                type: 'number',
                required: false,
                default: '10',
                placeholder: '10',
                description: '要获取的群聊数量'
            }
        ]
    },

    // 群组管理 - 获取群联系人
    'group-get-contact': {
        endpoint: '/api/group/get-contact',
        method: 'POST',
        parameters: [
            {
                name: 'group_name',
                label: '群组名称',
                type: 'text',
                required: true,
                placeholder: '测试群',
                description: '要获取联系人信息的群组名称'
            }
        ]
    },

    // 群组管理 - 获取通讯录群聊
    'group-get-contact-groups': {
        endpoint: '/api/group/get-contact-groups',
        method: 'GET',
        parameters: [
            {
                name: 'speed',
                label: '滚动速度',
                type: 'number',
                required: false,
                default: '1',
                placeholder: '1',
                description: '滚动速度，默认为1'
            },
            {
                name: 'interval',
                label: '滚动间隔',
                type: 'number',
                required: false,
                default: '0.1',
                placeholder: '0.1',
                description: '滚动时间间隔，默认为0.1秒'
            }
        ]
    },

    // 好友管理 - 获取好友详情
    'friend-get-details': {
        endpoint: '/api/friend/get-details',
        method: 'POST',
        parameters: [
            {
                name: 'n',
                label: '获取数量',
                type: 'number',
                required: false,
                placeholder: '10',
                description: '要获取的好友数量（可选）'
            },
            {
                name: 'tag',
                label: '标签筛选',
                type: 'text',
                required: false,
                placeholder: '同事',
                description: '按标签筛选好友（可选）'
            },
            {
                name: 'timeout',
                label: '超时时间',
                type: 'number',
                required: false,
                placeholder: '60000',
                description: '超时时间（毫秒，可选）'
            }
        ]
    },

    // 好友管理 - 添加好友
    'friend-add-new': {
        endpoint: '/api/friend/add-new',
        method: 'POST',
        parameters: [
            {
                name: 'search_text',
                label: '搜索内容',
                type: 'text',
                required: true,
                placeholder: '微信号或手机号',
                description: '要添加的好友的微信号或手机号'
            },
            {
                name: 'remark',
                label: '验证消息',
                type: 'textarea',
                required: false,
                placeholder: '我是...',
                description: '发送给对方的验证消息'
            }
        ]
    },

    // 好友管理 - 获取好友申请
    'friend-get-requests': {
        endpoint: '/api/friend/get-requests',
        method: 'GET',
        parameters: []
    },

    // WeChat扩展 - 获取联系人列表
    'wechat-get-contacts': {
        endpoint: '/api/wechat/get-contacts',
        method: 'GET',
        parameters: []
    },

    // WeChat扩展 - 获取用户信息
    'wechat-get-user-info': {
        endpoint: '/api/wechat/get-user-info',
        method: 'GET',
        parameters: []
    },

    // WeChat扩展 - 设置备注
    'wechat-set-remark': {
        endpoint: '/api/wechat/set-remark',
        method: 'POST',
        parameters: [
            {
                name: 'contact',
                label: '联系人',
                type: 'text',
                required: true,
                placeholder: '张三',
                description: '要设置备注的联系人名称'
            },
            {
                name: 'remark',
                label: '备注名',
                type: 'text',
                required: true,
                placeholder: '新备注',
                description: '要设置的备注名称'
            }
        ]
    },

    // WeChat扩展 - 打开聊天窗口
    'wechat-chat-with': {
        endpoint: '/api/wechat/chat-with',
        method: 'POST',
        parameters: [
            {
                name: 'who',
                label: '联系人名称',
                type: 'text',
                required: true,
                placeholder: '文件传输助手',
                description: '要打开聊天窗口的联系人或群组名称'
            },
            {
                name: 'exact',
                label: '精确匹配',
                type: 'select',
                required: false,
                default: 'false',
                options: [
                    { value: 'false', label: 'false' },
                    { value: 'true', label: 'true' }
                ],
                description: '是否精确匹配联系人名称，默认false'
            }
        ]
    },

    // WeChat扩展 - 获取会话列表
    'wechat-get-session': {
        endpoint: '/api/wechat/get-session',
        method: 'GET',
        parameters: []
    },

    // WeChat扩展 - 获取子窗口
    'wechat-get-sub-windows': {
        endpoint: '/api/wechat/get-sub-windows',
        method: 'GET',
        parameters: []
    },

    // 朋友圈 - 打开朋友圈
    'moments-open': {
        endpoint: '/api/moments/open',
        method: 'POST',
        parameters: []
    },

    // 朋友圈 - 获取朋友圈内容
    'moments-get-moments': {
        endpoint: '/api/moments/get-moments',
        method: 'GET',
        parameters: [
            {
                name: 'n',
                label: '获取数量',
                type: 'number',
                required: false,
                default: '10',
                placeholder: '10',
                description: '要获取的朋友圈内容数量'
            },
            {
                name: 'timeout',
                label: '超时时间',
                type: 'number',
                required: false,
                default: '10',
                placeholder: '10',
                description: '获取超时时间（秒）'
            }
        ]
    },

    // 朋友圈 - 点赞
    'moments-like': {
        endpoint: '/api/moments/like',
        method: 'POST',
        parameters: [
            {
                name: 'moment_index',
                label: '朋友圈索引',
                type: 'number',
                required: true,
                placeholder: '0',
                description: '要点赞的朋友圈索引（从0开始）'
            },
            {
                name: 'like',
                label: '点赞操作',
                type: 'select',
                required: false,
                default: 'true',
                options: [
                    { value: 'true', label: 'true (点赞)' },
                    { value: 'false', label: 'false (取消点赞)' }
                ],
                description: '是否点赞，true为点赞，false为取消点赞'
            }
        ]
    },

    // 朋友圈 - 评论
    'moments-comment': {
        endpoint: '/api/moments/comment',
        method: 'POST',
        parameters: [
            {
                name: 'moment_index',
                label: '朋友圈索引',
                type: 'number',
                required: true,
                placeholder: '0',
                description: '要评论的朋友圈索引（从0开始）'
            },
            {
                name: 'text',
                label: '评论内容',
                type: 'textarea',
                required: true,
                placeholder: '评论内容',
                description: '要发送的评论文字'
            }
        ]
    },

    // 辅助功能 - 截图
    'auxiliary-screenshot': {
        endpoint: '/api/auxiliary/screenshot',
        method: 'POST',
        parameters: [
            {
                name: 'save_path',
                label: '保存路径',
                type: 'text',
                required: false,
                placeholder: 'C:\\Users\\用户名\\Desktop\\screenshot.png',
                description: '截图保存路径，不填则返回base64数据'
            }
        ]
    },

    // 聊天窗口兼容 - 添加消息监听
    'message-listen-add': {
        endpoint: '/api/message/listen/add',
        method: 'POST',
        parameters: [
            {
                name: 'nickname',
                label: '联系人/群组',
                type: 'text',
                required: true,
                placeholder: '测试test',
                description: '要监听消息的联系人或群组名称'
            }
        ]
    },

    // 聊天窗口兼容 - 获取监听消息
    'message-listen-get': {
        endpoint: '/api/message/listen/get',
        method: 'GET',
        parameters: [
            {
                name: 'who',
                label: '联系人/群组',
                type: 'text',
                required: false,
                placeholder: '测试test',
                description: '要获取消息的联系人或群组名称'
            }
        ]
    },

    // 聊天窗口兼容 - 移除监听对象
    'message-listen-remove': {
        endpoint: '/api/message/listen/remove',
        method: 'POST',
        parameters: [
            {
                name: 'nickname',
                label: '联系人/群组昵称',
                type: 'text',
                required: true,
                placeholder: '测试群',
                description: '要移除监听的联系人或群组名称'
            }
        ]
    },

    // 辅助功能 - 点击会话
    'session-click': {
        endpoint: '/api/auxiliary/session/click',
        method: 'POST',
        parameters: [
            {
                name: 'session_name',
                label: '会话名称',
                type: 'text',
                required: true,
                placeholder: '文件传输助手',
                description: '要点击的会话名称'
            }
        ]
    },

    // 辅助功能 - 接受好友申请
    'accept-friend': {
        endpoint: '/api/auxiliary/new-friend/accept',
        method: 'POST',
        parameters: [
            {
                name: 'friend_name',
                label: '申请人名称',
                type: 'text',
                required: true,
                placeholder: '张三',
                description: '要接受的好友申请人名称'
            },
            {
                name: 'remark',
                label: '好友备注',
                type: 'text',
                required: false,
                placeholder: '同事',
                description: '设置好友备注（可选）'
            },
            {
                name: 'tags',
                label: '好友标签',
                type: 'text',
                required: false,
                placeholder: '工作,同事',
                description: '设置好友标签，多个标签用逗号分隔（可选）',
                transform: (value) => value ? value.split(',').map(tag => tag.trim()).filter(tag => tag) : undefined
            }
        ]
    },

    // 辅助功能 - 拒绝好友申请
    'reject-friend': {
        endpoint: '/api/auxiliary/new-friend/reject',
        method: 'POST',
        parameters: [
            {
                name: 'friend_name',
                label: '申请人名称',
                type: 'text',
                required: true,
                placeholder: '张三',
                description: '要拒绝的好友申请人名称'
            }
        ]
    },

    // 辅助功能 - 自动登录
    'auto-login': {
        endpoint: '/api/auxiliary/login/auto',
        method: 'POST',
        parameters: [
            {
                name: 'wxpath',
                label: '微信路径',
                type: 'text',
                required: false,
                placeholder: 'D:/Program Files/Tencent/WeChat/WeChat.exe',
                description: '微信客户端路径（可选，留空自动检测）'
            },
            {
                name: 'timeout',
                label: '超时时间（秒）',
                type: 'number',
                required: false,
                placeholder: '10',
                defaultValue: 10,
                min: 1,
                max: 60,
                description: '登录超时时间，默认10秒'
            }
        ]
    },

    // 辅助功能 - 获取登录二维码
    'qrcode-login': {
        endpoint: '/api/auxiliary/login/qrcode',
        method: 'POST',
        parameters: [
            {
                name: 'wxpath',
                label: '微信路径',
                type: 'text',
                required: false,
                placeholder: 'D:/Program Files/Tencent/WeChat/WeChat.exe',
                description: '微信客户端路径（可选，留空自动检测）'
            }
        ],
        customResponseHandler: (response, container) => {
            // 特殊处理二维码显示
            if (response.code === 0 && response.data && response.data.qrcode_data_url) {
                const resultDiv = container.querySelector('.api-result');
                if (resultDiv) {
                    // 添加二维码预览
                    const qrcodeHtml = `
                        <div class="mt-3">
                            <h6>二维码预览：</h6>
                            <img src="${response.data.qrcode_data_url}" alt="登录二维码"
                                 style="max-width: 300px; border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
                        </div>
                    `;
                    resultDiv.insertAdjacentHTML('beforeend', qrcodeHtml);
                }
            }
        }
    }
};

/**
 * 创建API测试器的便捷函数
 * @param {string} containerId - 容器ID
 * @param {string} configKey - 配置键名
 * @param {object} overrides - 覆盖配置
 */
function createApiTesterFromConfig(containerId, configKey, overrides = {}) {
    console.log(`🔧 创建API测试器: containerId=${containerId}, configKey=${configKey}`);

    const config = API_TESTER_CONFIGS[configKey];
    if (!config) {
        console.error(`❌ API配置 '${configKey}' 不存在`);
        return null;
    }

    console.log(`📋 找到配置:`, config);

    const finalConfig = { ...config, ...overrides };
    console.log(`⚙️ 最终配置:`, finalConfig);

    try {
        const tester = new UnifiedApiTester(containerId, finalConfig);
        console.log(`✅ 成功创建UnifiedApiTester实例`);
        return tester;
    } catch (error) {
        console.error(`❌ 创建UnifiedApiTester实例失败:`, error);
        return null;
    }
}

/**
 * 批量初始化页面中的所有API测试器
 */
function initializePageApiTesters() {
    console.log('开始初始化页面API测试工具...');

    // 查找所有带有 data-api-config 属性的容器
    const containers = document.querySelectorAll('[data-api-config]');
    console.log(`找到 ${containers.length} 个API测试工具容器`);

    containers.forEach(container => {
        const configKey = container.dataset.apiConfig;
        const overrides = {};

        console.log(`正在初始化容器: ${container.id}, 配置: ${configKey}`);

        // 检查配置是否存在
        if (!API_TESTER_CONFIGS[configKey]) {
            console.error(`配置 '${configKey}' 不存在于 API_TESTER_CONFIGS 中`);
            console.log('可用的配置键:', Object.keys(API_TESTER_CONFIGS));
            return;
        }

        // 从data属性中读取覆盖配置
        if (container.dataset.apiEndpoint) {
            overrides.endpoint = container.dataset.apiEndpoint;
        }
        if (container.dataset.apiMethod) {
            overrides.method = container.dataset.apiMethod;
        }

        try {
            const tester = createApiTesterFromConfig(container.id, configKey, overrides);
            if (tester) {
                console.log(`✅ 成功创建测试工具: ${container.id}`);
            } else {
                console.error(`❌ 创建测试工具失败: ${container.id}`);
            }
        } catch (error) {
            console.error(`❌ 创建测试工具时出错: ${container.id}`, error);
        }
    });

    console.log('API测试工具初始化完成');
}

// 页面加载完成后自动初始化
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保动态内容已加载
    setTimeout(initializePageApiTesters, 100);
});

// 导出给全局使用
window.API_TESTER_CONFIGS = API_TESTER_CONFIGS;
window.createApiTesterFromConfig = createApiTesterFromConfig;
window.initializePageApiTesters = initializePageApiTesters;
