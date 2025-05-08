// 全局变量
let socket = null;
let apiRequestCount = 0;
let queueLength = 0;

// 页面加载完成后执行
$(document).ready(function() {
    // 初始化WebSocket连接
    initWebSocket();
    
    // 初始化页面状态
    checkApiStatus();
    checkPluginStatus();
    getCurrentLib();
    getWeChatStatus();
    
    // 设置定时刷新
    setInterval(checkApiStatus, 10000);
    setInterval(getWeChatStatus, 5000);
    setInterval(getQueueStatus, 3000);
    
    // 绑定按钮事件
    bindButtonEvents();
});

// 初始化WebSocket连接
function initWebSocket() {
    // 获取当前URL的协议和主机部分
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    
    // 创建WebSocket连接
    socket = new WebSocket(`${protocol}//${host}/ws/logs`);
    
    // 连接打开时的处理
    socket.onopen = function(event) {
        addLogEntry('WebSocket连接已建立', 'success');
    };
    
    // 接收到消息时的处理
    socket.onmessage = function(event) {
        const logData = JSON.parse(event.data);
        addLogEntry(logData.message, logData.level);
    };
    
    // 连接关闭时的处理
    socket.onclose = function(event) {
        addLogEntry('WebSocket连接已关闭，5秒后尝试重连...', 'warning');
        setTimeout(initWebSocket, 5000);
    };
    
    // 连接错误时的处理
    socket.onerror = function(error) {
        addLogEntry('WebSocket连接错误', 'error');
    };
}

// 添加日志条目
function addLogEntry(message, level) {
    const logContainer = $('#log-container');
    const timestamp = new Date().toLocaleTimeString();
    const logClass = level ? `log-${level}` : '';
    
    // 创建日志条目
    const logEntry = $('<div></div>')
        .addClass('log-entry')
        .addClass(logClass)
        .text(`[${timestamp}] ${message}`);
    
    // 添加到日志容器
    logContainer.append(logEntry);
    
    // 滚动到底部
    logContainer.scrollTop(logContainer[0].scrollHeight);
    
    // 如果日志条目过多，删除旧的
    const maxLogEntries = 1000;
    const logEntries = $('.log-entry');
    if (logEntries.length > maxLogEntries) {
        logEntries.slice(0, logEntries.length - maxLogEntries).remove();
    }
}

// 检查API状态
function checkApiStatus() {
    $.ajax({
        url: '/admin/api/status',
        method: 'GET',
        success: function(response) {
            if (response.status === 'online') {
                $('#api-status').removeClass('status-offline status-warning').addClass('status-online');
                $('#api-status-text').text('在线');
            } else {
                $('#api-status').removeClass('status-online status-warning').addClass('status-offline');
                $('#api-status-text').text('离线');
            }
        },
        error: function() {
            $('#api-status').removeClass('status-online status-warning').addClass('status-offline');
            $('#api-status-text').text('离线');
        }
    });
}

// 检查插件状态
function checkPluginStatus() {
    $.ajax({
        url: '/admin/plugins/status',
        method: 'GET',
        success: function(response) {
            // 更新wxauto状态
            if (response.wxauto.installed) {
                $('#wxauto-status').removeClass('bg-danger bg-warning').addClass('bg-success').text('已安装');
                $('#wxauto-progress').css('width', '100%');
            } else {
                $('#wxauto-status').removeClass('bg-success bg-warning').addClass('bg-danger').text('未安装');
                $('#wxauto-progress').css('width', '0%');
            }
            
            // 更新wxautox状态
            if (response.wxautox.installed) {
                $('#wxautox-status').removeClass('bg-danger bg-warning').addClass('bg-success').text('已安装');
                $('#wxautox-progress').css('width', '100%');
            } else {
                $('#wxautox-status').removeClass('bg-success bg-warning').addClass('bg-danger').text('未安装');
                $('#wxautox-progress').css('width', '0%');
            }
        },
        error: function() {
            $('#wxauto-status').removeClass('bg-success bg-warning').addClass('bg-danger').text('检查失败');
            $('#wxautox-status').removeClass('bg-success bg-warning').addClass('bg-danger').text('检查失败');
        }
    });
}

// 获取当前使用的库
function getCurrentLib() {
    $.ajax({
        url: '/admin/config/current-lib',
        method: 'GET',
        success: function(response) {
            $('#current-lib').val(response.lib);
            
            // 设置单选按钮状态
            if (response.lib === 'wxauto') {
                $('#wxauto-select').prop('checked', true);
            } else if (response.lib === 'wxautox') {
                $('#wxautox-select').prop('checked', true);
            }
        }
    });
}

// 获取微信状态
function getWeChatStatus() {
    $.ajax({
        url: '/admin/wechat/status',
        method: 'GET',
        success: function(response) {
            $('#wechat-status').val(response.status);
        },
        error: function() {
            $('#wechat-status').val('未连接');
        }
    });
}

// 获取队列状态
function getQueueStatus() {
    $.ajax({
        url: '/admin/queue/status',
        method: 'GET',
        success: function(response) {
            apiRequestCount = response.total_requests;
            queueLength = response.queue_length;
            
            $('#api-requests').val(apiRequestCount);
            $('#queue-length').val(queueLength);
        }
    });
}

// 绑定按钮事件
function bindButtonEvents() {
    // 安装/修复wxauto
    $('#install-wxauto').click(function() {
        $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> 安装中...');
        
        $.ajax({
            url: '/admin/plugins/install-wxauto',
            method: 'POST',
            success: function(response) {
                addLogEntry(response.message, 'success');
                checkPluginStatus();
            },
            error: function(xhr) {
                addLogEntry('安装wxauto失败: ' + xhr.responseJSON.message, 'error');
            },
            complete: function() {
                $('#install-wxauto').prop('disabled', false).html('<i class="bi bi-download"></i> 安装/修复 wxauto');
            }
        });
    });
    
    // 上传wxautox按钮点击
    $('#upload-wxautox').click(function() {
        $('#wxautox-file').click();
    });
    
    // 文件选择改变
    $('#wxautox-file').change(function() {
        if (this.files.length > 0) {
            uploadWxautox(this.files[0]);
        }
    });
    
    // 应用库选择
    $('#apply-lib-select').click(function() {
        const selectedLib = $('input[name="lib-select"]:checked').val();
        if (!selectedLib) {
            addLogEntry('请先选择一个库', 'warning');
            return;
        }
        
        $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> 应用中...');
        
        $.ajax({
            url: '/admin/config/set-lib',
            method: 'POST',
            data: JSON.stringify({ lib: selectedLib }),
            contentType: 'application/json',
            success: function(response) {
                addLogEntry(response.message, 'success');
                getCurrentLib();
            },
            error: function(xhr) {
                addLogEntry('设置库失败: ' + xhr.responseJSON.message, 'error');
            },
            complete: function() {
                $('#apply-lib-select').prop('disabled', false).html('<i class="bi bi-check-circle"></i> 应用选择');
            }
        });
    });
    
    // 启动服务
    $('#start-service').click(function() {
        controlService('start');
    });
    
    // 停止服务
    $('#stop-service').click(function() {
        controlService('stop');
    });
    
    // 重启服务
    $('#restart-service').click(function() {
        controlService('restart');
    });
    
    // 重载配置
    $('#reload-config').click(function() {
        $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> 重载中...');
        
        $.ajax({
            url: '/admin/config/reload',
            method: 'POST',
            success: function(response) {
                addLogEntry(response.message, 'success');
                getCurrentLib();
                checkPluginStatus();
            },
            error: function(xhr) {
                addLogEntry('重载配置失败: ' + xhr.responseJSON.message, 'error');
            },
            complete: function() {
                $('#reload-config').prop('disabled', false).html('<i class="bi bi-arrow-repeat"></i> 重载配置');
            }
        });
    });
    
    // 清空日志
    $('#clear-logs').click(function() {
        $('#log-container').empty();
        addLogEntry('日志已清空', 'info');
    });
}

// 上传wxautox文件
function uploadWxautox(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    $('#upload-wxautox').prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> 上传中...');
    
    $.ajax({
        url: '/admin/plugins/upload-wxautox',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            addLogEntry(response.message, 'success');
            checkPluginStatus();
        },
        error: function(xhr) {
            addLogEntry('上传wxautox失败: ' + xhr.responseJSON.message, 'error');
        },
        complete: function() {
            $('#upload-wxautox').prop('disabled', false).html('<i class="bi bi-upload"></i> 上传并安装 wxautox');
            $('#wxautox-file').val('');
        }
    });
}

// 控制服务
function controlService(action) {
    const buttonMap = {
        'start': $('#start-service'),
        'stop': $('#stop-service'),
        'restart': $('#restart-service')
    };
    
    const textMap = {
        'start': '启动中...',
        'stop': '停止中...',
        'restart': '重启中...'
    };
    
    const iconMap = {
        'start': '<i class="bi bi-play-fill"></i> 启动服务',
        'stop': '<i class="bi bi-stop-fill"></i> 停止服务',
        'restart': '<i class="bi bi-arrow-clockwise"></i> 重启服务'
    };
    
    // 禁用所有按钮
    Object.values(buttonMap).forEach(btn => btn.prop('disabled', true));
    buttonMap[action].html(`<span class="spinner-border spinner-border-sm"></span> ${textMap[action]}`);
    
    $.ajax({
        url: `/admin/service/${action}`,
        method: 'POST',
        success: function(response) {
            addLogEntry(response.message, 'success');
            checkApiStatus();
        },
        error: function(xhr) {
            addLogEntry(`${action}服务失败: ` + xhr.responseJSON.message, 'error');
        },
        complete: function() {
            // 恢复所有按钮
            Object.entries(buttonMap).forEach(([key, btn]) => {
                btn.prop('disabled', false).html(iconMap[key]);
            });
        }
    });
}
