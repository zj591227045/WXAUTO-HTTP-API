"""
wxauto_http_api 管理界面
提供插件管理、服务状态监控、日志查看等功能
"""

import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import importlib
import json
import queue
import signal
import psutil
import logging
import requests
from datetime import datetime
from pathlib import Path

# 导入配置管理模块
import config_manager

# 确保当前目录在Python路径中，以便能够导入app模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入项目模块
try:
    from app.config import Config
    from app.logs import logger
except ImportError:
    print("无法导入项目模块，请确保在正确的目录中运行")
    sys.exit(1)

# 全局变量
API_PROCESS = None
LOG_QUEUE = queue.Queue()
CONFIG_MODIFIED = False

# API调用计数器
class ApiCounter:
    def __init__(self):
        self.success_count = 0
        self.error_count = 0

    def reset(self):
        self.success_count = 0
        self.error_count = 0

    def count_request(self, log_line):
        # 只处理请求完成的日志，避免重复计数
        if "请求处理完成:" not in log_line:
            return

        # 忽略状态检查和获取未读消息的API调用
        if "GET /api/wechat/status" in log_line or "GET /api/message/get-next-new" in log_line:
            return

        # 计算成功的API调用 - 确保状态码周围有空格，避免误匹配
        if (" 200 " in log_line or " 201 " in log_line) and "状态码:" in log_line:
            self.success_count += 1
            print(f"API成功计数增加: {self.success_count}, 日志: {log_line}")
        # 计算失败的API调用 - 确保状态码周围有空格，避免误匹配
        elif ((" 400 " in log_line or " 401 " in log_line or " 404 " in log_line or " 500 " in log_line) and "状态码:" in log_line):
            self.error_count += 1
            print(f"API错误计数增加: {self.error_count}, 日志: {log_line}")

        # 打印当前计数
        print(f"当前API计数 - 成功: {self.success_count}, 错误: {self.error_count}")

API_COUNTER = ApiCounter()

class APILogHandler(logging.Handler):
    """API日志处理器，用于捕获API日志并发送到UI"""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        """发送日志记录到队列"""
        try:
            # 只包含日志级别和消息，不包含时间戳（时间戳会在UI中添加）
            # 检查消息中是否已经包含时间戳格式的内容，如果有则移除
            message = record.getMessage()

            # 移除消息开头可能存在的时间戳格式 (yyyy-mm-dd HH:MM:SS)
            message = self._remove_timestamp(message)

            # 只保留日志级别和消息内容
            formatted_msg = f"{record.levelname} - {message}"
            self.log_queue.put(formatted_msg)
        except Exception:
            pass

    def _remove_timestamp(self, message):
        """移除消息中可能存在的时间戳格式"""
        # 尝试移除常见的时间戳格式
        import re

        # 移除类似 "2025-05-08 11:50:17,850" 这样的时间戳
        message = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(,\d{3})? - ', '', message)

        # 移除类似 "[2025-05-08 11:50:17]" 这样的时间戳
        message = re.sub(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] ', '', message)

        # 移除类似 "2025-05-08 12:04:46" 这样的时间戳（Flask日志格式）
        message = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - ', '', message)

        # 移除类似 "127.0.0.1 - - [08/May/2025 12:04:46]" 这样的Werkzeug日志格式
        if ' - - [' in message and '] "' in message:
            parts = message.split('] "', 1)
            if len(parts) > 1:
                ip_part = parts[0].split(' - - [')[0]
                request_part = parts[1]
                message = f"{ip_part} - {request_part}"

        return message

class WxAutoHttpUI:
    """wxauto_http_api 管理界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("wxauto_http_api 管理界面")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)

        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", padding=6, relief="flat", background="#e1e1e1")
        self.style.configure("TLabel", background="#f0f0f0")
        self.style.configure("Green.TLabel", foreground="green")
        self.style.configure("Red.TLabel", foreground="red")
        self.style.configure("Bold.TLabel", font=("TkDefaultFont", 9, "bold"))

        # 添加强调按钮样式
        try:
            # 尝试使用更现代的样式
            self.style.configure("Accent.TButton",
                                padding=8,
                                relief="raised",
                                background="#4a86e8",
                                foreground="#ffffff",
                                font=("TkDefaultFont", 10, "bold"))

            # 设置鼠标悬停效果
            self.style.map("Accent.TButton",
                        background=[('active', '#3a76d8'), ('pressed', '#2a66c8')],
                        relief=[('pressed', 'sunken')])
        except Exception:
            # 如果样式设置失败，使用基本样式
            self.style.configure("Accent.TButton",
                                padding=8,
                                font=("TkDefaultFont", 10, "bold"))

        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建顶部控制区域
        self.create_control_panel()

        # 创建中间状态区域
        self.create_status_panel()

        # 创建日志区域
        self.create_log_panel()

        # 初始化状态
        self.api_running = False
        self.current_lib = "wxauto"  # 默认使用wxauto
        self.current_port = 5000     # 默认端口号

        # 启动状态更新定时器
        self.update_status()
        self.root.after(1000, self.check_status)

        # 设置关闭窗口事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 初始化日志处理
        self.setup_logging()

        # 设置自动启动服务的倒计时
        self.countdown_seconds = 5
        self.add_log("===== 自动启动服务 =====")
        self.add_log(f"将在 {self.countdown_seconds} 秒后自动启动服务...")
        self.start_countdown()

    def create_control_panel(self):
        """创建顶部控制面板"""
        control_frame = ttk.LabelFrame(self.main_frame, text="控制面板", padding="10")
        control_frame.pack(fill=tk.X, pady=5)

        # 第一行：库选择和服务控制
        row1 = ttk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=5)

        # 库选择区域
        lib_frame = ttk.Frame(row1)
        lib_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(lib_frame, text="微信库选择:").pack(side=tk.LEFT, padx=5)
        self.lib_var = tk.StringVar(value="wxauto")
        self.wxauto_radio = ttk.Radiobutton(lib_frame, text="wxauto", variable=self.lib_var, value="wxauto", command=self.on_lib_change)
        self.wxauto_radio.pack(side=tk.LEFT, padx=5)
        self.wxautox_radio = ttk.Radiobutton(lib_frame, text="wxautox", variable=self.lib_var, value="wxautox", command=self.on_lib_change)
        self.wxautox_radio.pack(side=tk.LEFT, padx=5)

        # 初始化变量，但不在主界面显示
        self.port_var = tk.StringVar(value="5000")
        self.apikey_var = tk.StringVar(value="test-key-2")

        # 服务控制区域
        service_frame = ttk.Frame(row1)
        service_frame.pack(side=tk.RIGHT, padx=5)

        self.start_button = ttk.Button(service_frame, text="启动服务", command=self.start_api_service)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(service_frame, text="停止服务", command=self.stop_api_service)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.config_button = ttk.Button(service_frame, text="插件配置", command=self.show_config_dialog)
        self.config_button.pack(side=tk.LEFT, padx=5)
        self.reload_button = ttk.Button(service_frame, text="重载配置", command=self.reload_config)
        self.reload_button.pack(side=tk.LEFT, padx=5)

        # 第二行：插件管理
        row2 = ttk.Frame(control_frame)
        row2.pack(fill=tk.X, pady=5)

        # wxauto插件状态
        wxauto_frame = ttk.Frame(row2)
        wxauto_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Label(wxauto_frame, text="wxauto状态:").pack(side=tk.LEFT, padx=5)
        self.wxauto_status = ttk.Label(wxauto_frame, text="检测中...", style="Bold.TLabel")
        self.wxauto_status.pack(side=tk.LEFT, padx=5)
        self.install_wxauto_button = ttk.Button(wxauto_frame, text="安装/修复", command=self.install_wxauto)
        self.install_wxauto_button.pack(side=tk.LEFT, padx=5)
        self.api_doc_button = ttk.Button(wxauto_frame, text="API说明", command=self.show_api_documentation)
        self.api_doc_button.pack(side=tk.LEFT, padx=5)

        # wxautox插件状态
        wxautox_frame = ttk.Frame(row2)
        wxautox_frame.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)

        ttk.Label(wxautox_frame, text="wxautox状态:").pack(side=tk.LEFT, padx=5)
        self.wxautox_status = ttk.Label(wxautox_frame, text="检测中...", style="Bold.TLabel")
        self.wxautox_status.pack(side=tk.LEFT, padx=5)
        # 使用ttk.Button与其他按钮保持一致的风格
        self.install_wxautox_button = ttk.Button(
            wxautox_frame,
            text="安装wxautox",
            command=self.show_wxautox_install
        )
        self.install_wxautox_button.pack(side=tk.LEFT, padx=5)

    def create_status_panel(self):
        """创建状态面板"""
        status_frame = ttk.LabelFrame(self.main_frame, text="服务状态", padding="10")
        status_frame.pack(fill=tk.X, pady=5)

        # 服务状态信息
        info_frame = ttk.Frame(status_frame)
        info_frame.pack(fill=tk.X, pady=5)

        # 第一行
        row1 = ttk.Frame(info_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="API服务状态:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.api_status = ttk.Label(row1, text="未运行", style="Red.TLabel")
        self.api_status.grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(row1, text="监听地址:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.api_address = ttk.Label(row1, text="--")
        self.api_address.grid(row=0, column=3, padx=5, sticky=tk.W)

        ttk.Label(row1, text="当前库:").grid(row=0, column=4, padx=5, sticky=tk.W)
        self.current_lib_label = ttk.Label(row1, text="wxauto", style="Bold.TLabel")
        self.current_lib_label.grid(row=0, column=5, padx=5, sticky=tk.W)

        # 第二行
        row2 = ttk.Frame(info_frame)
        row2.pack(fill=tk.X, pady=2)

        ttk.Label(row2, text="CPU使用率:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.cpu_usage = ttk.Label(row2, text="0%")
        self.cpu_usage.grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(row2, text="内存使用:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.memory_usage = ttk.Label(row2, text="0 MB")
        self.memory_usage.grid(row=0, column=3, padx=5, sticky=tk.W)

        ttk.Label(row2, text="运行时间:").grid(row=0, column=4, padx=5, sticky=tk.W)
        self.uptime = ttk.Label(row2, text="00:00:00")
        self.uptime.grid(row=0, column=5, padx=5, sticky=tk.W)

        # 第三行
        row3 = ttk.Frame(info_frame)
        row3.pack(fill=tk.X, pady=2)

        ttk.Label(row3, text="API请求数:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.request_count = ttk.Label(row3, text="0", font=("TkDefaultFont", 10, "bold"))
        self.request_count.grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(row3, text="错误数:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.error_count = ttk.Label(row3, text="0", font=("TkDefaultFont", 10, "bold"), foreground="red")
        self.error_count.grid(row=0, column=3, padx=5, sticky=tk.W)

        ttk.Label(row3, text="微信连接:").grid(row=0, column=4, padx=5, sticky=tk.W)
        self.wechat_status = ttk.Label(row3, text="未连接", style="Red.TLabel")
        self.wechat_status.grid(row=0, column=5, padx=5, sticky=tk.W)

        # 添加微信窗口名称说明标签
        ttk.Label(row3, text="微信名称:").grid(row=0, column=6, padx=5, sticky=tk.W)

        # 创建微信窗口名称标签（初始为空）
        self.wechat_window_name = ttk.Label(row3, text="", foreground="orange", font=("TkDefaultFont", 10, "bold"))
        self.wechat_window_name.grid(row=0, column=7, padx=5, sticky=tk.W)

    def create_log_panel(self):
        """创建日志面板"""
        log_frame = ttk.LabelFrame(self.main_frame, text="API日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # 添加日志滚动事件处理
        self.log_text.bind("<MouseWheel>", self.on_log_scroll)

        # 底部按钮和状态栏
        button_frame = ttk.Frame(log_frame)
        button_frame.pack(fill=tk.X, pady=5)

        # 左侧状态指示
        status_frame = ttk.Frame(button_frame)
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 新日志指示器
        self.new_log_indicator = ttk.Label(status_frame, text="", foreground="red")
        self.new_log_indicator.pack(side=tk.LEFT, padx=5)

        # 跳转到最新日志按钮
        self.goto_latest_button = ttk.Button(status_frame, text="查看最新日志", command=self.scroll_to_latest)
        self.goto_latest_button.pack(side=tk.LEFT, padx=5)

        # 自动滚动选项
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.auto_scroll_check = ttk.Checkbutton(
            status_frame,
            text="自动滚动",
            variable=self.auto_scroll_var,
            command=self.toggle_auto_scroll
        )
        self.auto_scroll_check.pack(side=tk.LEFT, padx=5)

        # 过滤器按钮
        self.filter_button = ttk.Button(status_frame, text="日志过滤", command=self.show_filter_dialog)
        self.filter_button.pack(side=tk.LEFT, padx=5)

        # 过滤器设置
        self.filter_settings = {
            'hide_status_check': tk.BooleanVar(value=False),  # 隐藏状态检查日志
            'hide_debug': tk.BooleanVar(value=False),         # 隐藏DEBUG级别日志
            'custom_filter': tk.StringVar(value="")           # 自定义过滤关键词
        }

        # 加载过滤器设置
        self.load_filter_settings()

        # 右侧操作按钮
        self.clear_log_button = ttk.Button(button_frame, text="清空日志", command=self.clear_log)
        self.clear_log_button.pack(side=tk.RIGHT, padx=5)

        self.save_log_button = ttk.Button(button_frame, text="保存日志", command=self.save_log)
        self.save_log_button.pack(side=tk.RIGHT, padx=5)

    def on_log_scroll(self, event=None):
        """处理日志滚动事件"""
        # 清除新日志指示
        self.new_log_indicator.config(text="")

        # 检查是否滚动到底部
        current_position = self.log_text.yview()
        if current_position[1] > 0.99:
            # 如果用户手动滚动到底部，启用自动滚动
            self.auto_scroll_var.set(True)
        else:
            # 如果用户向上滚动，禁用自动滚动
            self.auto_scroll_var.set(False)

    def toggle_auto_scroll(self):
        """切换自动滚动状态"""
        if self.auto_scroll_var.get():
            # 如果启用了自动滚动，立即滚动到底部
            self.scroll_to_latest()

    def scroll_to_latest(self):
        """滚动到最新日志"""
        self.log_text.see(tk.END)
        self.new_log_indicator.config(text="")
        self.auto_scroll_var.set(True)

    def load_filter_settings(self):
        """从配置文件加载过滤器设置"""
        try:
            # 加载配置
            config = config_manager.load_log_filter_config()

            # 更新UI变量
            self.filter_settings['hide_status_check'].set(config.get('hide_status_check', False))
            self.filter_settings['hide_debug'].set(config.get('hide_debug', False))
            self.filter_settings['custom_filter'].set(config.get('custom_filter', ""))

            self.add_log("日志过滤器设置已加载")
        except Exception as e:
            self.add_log(f"加载日志过滤器设置失败: {str(e)}")

    def save_filter_settings(self):
        """保存过滤器设置到配置文件"""
        try:
            # 从UI变量获取当前设置
            config = {
                'hide_status_check': self.filter_settings['hide_status_check'].get(),
                'hide_debug': self.filter_settings['hide_debug'].get(),
                'custom_filter': self.filter_settings['custom_filter'].get()
            }

            # 保存配置
            config_manager.save_log_filter_config(config)

            self.add_log("日志过滤器设置已保存")
        except Exception as e:
            self.add_log(f"保存日志过滤器设置失败: {str(e)}")

    def show_filter_dialog(self):
        """显示日志过滤设置对话框"""
        filter_dialog = tk.Toplevel(self.root)
        filter_dialog.title("日志过滤设置")
        filter_dialog.geometry("400x300")
        filter_dialog.resizable(False, False)
        filter_dialog.transient(self.root)  # 设置为主窗口的子窗口
        filter_dialog.grab_set()  # 模态对话框

        # 创建设置框架
        settings_frame = ttk.Frame(filter_dialog, padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        # 添加过滤选项
        ttk.Label(settings_frame, text="日志过滤设置", font=("TkDefaultFont", 12, "bold")).pack(pady=10)

        # 隐藏状态检查日志
        ttk.Checkbutton(
            settings_frame,
            text="隐藏微信状态检查日志 (GET /api/wechat/status)",
            variable=self.filter_settings['hide_status_check']
        ).pack(anchor=tk.W, pady=5)

        # 隐藏DEBUG级别日志
        ttk.Checkbutton(
            settings_frame,
            text="隐藏DEBUG级别日志",
            variable=self.filter_settings['hide_debug']
        ).pack(anchor=tk.W, pady=5)

        # 自定义过滤
        custom_frame = ttk.Frame(settings_frame)
        custom_frame.pack(fill=tk.X, pady=5)

        ttk.Label(custom_frame, text="自定义过滤关键词:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(
            custom_frame,
            textvariable=self.filter_settings['custom_filter'],
            width=30
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Label(settings_frame, text="多个关键词用逗号分隔，包含任一关键词的日志将被隐藏",
                 font=("TkDefaultFont", 8)).pack(anchor=tk.W, pady=2)

        # 说明文本
        ttk.Separator(settings_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(settings_frame, text="注意: 过滤器设置将自动保存，并在下次启动时自动加载",
                 wraplength=380).pack(pady=5)

        # 按钮区域
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # 应用按钮
        ttk.Button(
            button_frame,
            text="应用并保存",
            command=lambda: [self.save_filter_settings(), filter_dialog.destroy(), self.refresh_log_display()]
        ).pack(side=tk.RIGHT, padx=5)

        # 取消按钮
        ttk.Button(
            button_frame,
            text="取消",
            command=filter_dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def refresh_log_display(self):
        """根据过滤设置刷新日志显示"""
        # 获取当前日志内容
        self.log_text.config(state=tk.NORMAL)
        current_log = self.log_text.get(1.0, tk.END)
        self.log_text.delete(1.0, tk.END)

        # 按行处理并应用过滤
        for line in current_log.split('\n'):
            if line and not self.should_filter_log(line):
                self.log_text.insert(tk.END, line + '\n')

        self.log_text.config(state=tk.DISABLED)

    def should_filter_log(self, log_line):
        """判断是否应该过滤掉某行日志"""
        # 检查是否是微信状态检查日志
        if self.filter_settings['hide_status_check'].get():
            if "GET /api/wechat/status" in log_line:
                return True

        # 检查是否是DEBUG级别日志
        if self.filter_settings['hide_debug'].get():
            if " - DEBUG - " in log_line:
                return True

        # 过滤掉HTTP服务器处理请求的堆栈日志
        if any(pattern in log_line for pattern in [
            "BaseHTTPRequestHandler.handle",
            "handle_one_request",
            "self.run_wsgi",
            "execute(self.server.app)",
            "File \"C:\\Users\\jackson\\AppData\\Local\\miniconda3\\envs\\wxauto-api"
        ]):
            return True

        # 检查自定义过滤关键词
        custom_filters = self.filter_settings['custom_filter'].get().strip()
        if custom_filters:
            keywords = [k.strip() for k in custom_filters.split(',') if k.strip()]
            for keyword in keywords:
                if keyword in log_line:
                    return True

        return False

    def setup_logging(self):
        """设置日志处理"""
        # 确保日志目录存在
        config_manager.ensure_dirs()

        # 添加队列处理器到logger
        self.log_handler = APILogHandler(LOG_QUEUE)

        # 检查logger类型，如果是WeChatLibAdapter，需要获取原始logger
        try:
            from app.logs import WeChatLibAdapter
            if isinstance(logger, WeChatLibAdapter):
                # 获取原始logger
                original_logger = logger.logger
                # 添加处理器到原始logger
                original_logger.addHandler(self.log_handler)

                # 添加文件处理器，将日志保存到文件
                try:
                    # 生成日志文件名
                    timestamp = datetime.now().strftime("%Y%m%d")
                    log_file = config_manager.LOGS_DIR / f"api_{timestamp}.log"

                    # 创建文件处理器 - 文件中使用完整时间戳格式
                    file_handler = logging.FileHandler(log_file, encoding='utf-8')
                    # 使用与UI相同的时间戳格式
                    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                                               '%Y-%m-%d %H:%M:%S'))
                    original_logger.addHandler(file_handler)

                    self.add_log(f"日志将保存到: {log_file}")
                except Exception as e:
                    self.add_log(f"设置日志文件失败: {str(e)}")
            else:
                # 直接添加处理器到logger
                logger.addHandler(self.log_handler)

                # 添加文件处理器，将日志保存到文件
                try:
                    # 生成日志文件名
                    timestamp = datetime.now().strftime("%Y%m%d")
                    log_file = config_manager.LOGS_DIR / f"api_{timestamp}.log"

                    # 创建文件处理器 - 文件中使用完整时间戳格式
                    file_handler = logging.FileHandler(log_file, encoding='utf-8')
                    # 使用与UI相同的时间戳格式
                    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                                               '%Y-%m-%d %H:%M:%S'))
                    logger.addHandler(file_handler)

                    self.add_log(f"日志将保存到: {log_file}")
                except Exception as e:
                    self.add_log(f"设置日志文件失败: {str(e)}")
        except ImportError:
            # 如果无法导入WeChatLibAdapter，直接使用logger
            logger.addHandler(self.log_handler)

            # 添加文件处理器，将日志保存到文件
            try:
                # 生成日志文件名
                timestamp = datetime.now().strftime("%Y%m%d")
                log_file = config_manager.LOGS_DIR / f"api_{timestamp}.log"

                # 创建文件处理器 - 文件中使用完整时间戳格式
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                # 使用与UI相同的时间戳格式
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                                           '%Y-%m-%d %H:%M:%S'))
                logger.addHandler(file_handler)

                self.add_log(f"日志将保存到: {log_file}")
            except Exception as e:
                self.add_log(f"设置日志文件失败: {str(e)}")

        # 启动日志更新线程
        self.root.after(100, self.update_log)

    def update_log(self):
        """更新日志显示"""
        if not LOG_QUEUE.empty():
            # 获取当前滚动位置
            current_position = self.log_text.yview()
            # 判断用户是否已经滚动到底部
            at_bottom = current_position[1] > 0.99 or self.auto_scroll_var.get()

            self.log_text.config(state=tk.NORMAL)

            has_new_visible_logs = False
            while not LOG_QUEUE.empty():
                msg = LOG_QUEUE.get()

                # 更新API调用计数
                global API_COUNTER
                old_success = API_COUNTER.success_count
                old_error = API_COUNTER.error_count

                API_COUNTER.count_request(msg)

                # 更新UI显示 - 每次都更新，确保显示最新的计数
                self.request_count.config(text=str(API_COUNTER.success_count))
                self.error_count.config(text=str(API_COUNTER.error_count))

                # 如果计数发生变化，添加日志
                if old_success != API_COUNTER.success_count or old_error != API_COUNTER.error_count:
                    self.add_log(f"API计数更新 - 成功: {API_COUNTER.success_count}, 错误: {API_COUNTER.error_count}")

                # 应用过滤器
                if not self.should_filter_log(msg):
                    # 添加统一格式的时间戳，但不再添加库信息（因为日志中已经包含）
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # 检查消息中是否已经包含库信息标记 [wxauto] 或 [wxautox]
                    if "[wxauto]" in msg or "[wxautox]" in msg:
                        # 已经包含库信息，只添加时间戳
                        formatted_msg = f"[{timestamp}] {msg}"
                    else:
                        # 不包含库信息，添加时间戳和库信息
                        lib_name = getattr(self, 'current_lib', 'wxauto')  # 默认使用wxauto
                        formatted_msg = f"[{timestamp}] [{lib_name}] {msg}"

                    self.log_text.insert(tk.END, formatted_msg + "\n")
                    has_new_visible_logs = True

            # 限制日志显示数量为最新的200条
            log_content = self.log_text.get(1.0, tk.END)
            log_lines = log_content.split('\n')
            if len(log_lines) > 201:  # 加1是因为split后最后一个元素是空字符串
                # 计算需要删除的行数
                lines_to_delete = len(log_lines) - 201
                # 删除多余的行
                self.log_text.delete(1.0, f"{lines_to_delete + 1}.0")

            # 只有当用户当前在查看最新内容或启用了自动滚动时，才自动滚动到底部
            if at_bottom and has_new_visible_logs:
                self.log_text.see(tk.END)
            elif has_new_visible_logs:
                # 显示新日志指示
                self.new_log_indicator.config(text="↓ 有新日志", foreground="red")

            self.log_text.config(state=tk.DISABLED)

        self.root.after(100, self.update_log)

    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def save_log(self):
        """保存日志到文件"""
        # 确保日志目录存在
        config_manager.ensure_dirs()

        # 生成默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"api_log_{timestamp}.txt"
        default_path = config_manager.LOGS_DIR / default_filename

        # 打开文件保存对话框
        file_path = filedialog.asksaveasfilename(
            initialdir=config_manager.LOGS_DIR,
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return  # 用户取消了保存

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.log_text.get(1.0, tk.END))

            self.add_log(f"日志已保存到 {file_path}")
            messagebox.showinfo("保存成功", f"日志已保存到:\n{file_path}")
        except Exception as e:
            self.add_log(f"保存日志失败: {str(e)}")
            messagebox.showerror("保存失败", f"保存日志失败: {str(e)}")

    def check_wxauto_status(self):
        """检查wxauto库的安装状态"""
        try:
            # 确保本地wxauto文件夹在Python路径中
            import sys
            import os
            wxauto_path = os.path.join(os.getcwd(), "wxauto")
            if wxauto_path not in sys.path:
                sys.path.insert(0, wxauto_path)

            # 直接从本地文件夹导入
            import wxauto
            self.wxauto_status.config(text="已安装", style="Green.TLabel")
            return True
        except ImportError as e:
            self.wxauto_status.config(text="未安装", style="Red.TLabel")
            self.add_log(f"wxauto导入失败: {str(e)}")
            return False

    def check_wxautox_status(self):
        """检查wxautox库的安装状态"""
        try:
            import wxautox
            self.wxautox_status.config(text="已安装", style="Green.TLabel")
            return True
        except ImportError:
            self.wxautox_status.config(text="未安装", style="Red.TLabel")
            return False

    def install_wxauto(self):
        """检查本地wxauto文件夹"""
        # 禁用按钮，避免重复点击
        self.install_wxauto_button.config(state=tk.DISABLED)
        self.wxauto_status.config(text="检查中...", style="Bold.TLabel")
        self.add_log("正在检查本地wxauto文件夹...")

        def check_thread():
            try:
                # 检查本地wxauto文件夹是否存在
                wxauto_path = os.path.join(os.getcwd(), "wxauto")
                if os.path.exists(wxauto_path) and os.path.isdir(wxauto_path):
                    # 检查wxauto文件夹中是否包含必要的文件
                    init_file = os.path.join(wxauto_path, "wxauto", "__init__.py")
                    wxauto_file = os.path.join(wxauto_path, "wxauto", "wxauto.py")

                    if os.path.exists(init_file) and os.path.exists(wxauto_file):
                        # 确保本地wxauto文件夹在Python路径中
                        import sys
                        if wxauto_path not in sys.path:
                            sys.path.insert(0, wxauto_path)

                        # 尝试导入
                        try:
                            import wxauto
                            self.root.after(0, lambda: self.add_log(f"成功从本地文件夹导入wxauto: {wxauto_path}"))
                            self.root.after(0, lambda: self.wxauto_status.config(text="已安装", style="Green.TLabel"))
                        except ImportError as e:
                            self.root.after(0, lambda: self.add_log(f"从本地文件夹导入wxauto失败: {str(e)}"))
                            self.root.after(0, lambda: self.wxauto_status.config(text="导入失败", style="Red.TLabel"))
                            self.root.after(0, lambda: messagebox.showerror("导入失败",
                                f"从本地文件夹导入wxauto失败: {str(e)}\n\n请确保wxauto文件夹包含正确的wxauto模块"))
                    else:
                        self.root.after(0, lambda: self.add_log(f"wxauto文件夹结构不完整，缺少必要文件"))
                        self.root.after(0, lambda: self.wxauto_status.config(text="结构不完整", style="Red.TLabel"))
                        self.root.after(0, lambda: messagebox.showerror("文件夹结构不完整",
                            f"wxauto文件夹结构不完整，缺少必要文件\n\n请确保wxauto文件夹包含完整的wxauto模块"))
                else:
                    self.root.after(0, lambda: self.add_log(f"本地wxauto文件夹不存在: {wxauto_path}"))
                    self.root.after(0, lambda: self.wxauto_status.config(text="文件夹不存在", style="Red.TLabel"))
                    self.root.after(0, lambda: messagebox.showerror("文件夹不存在",
                        f"本地wxauto文件夹不存在: {wxauto_path}\n\n请确保项目根目录下存在wxauto文件夹"))
            except Exception as e:
                self.root.after(0, lambda: self.add_log(f"检查过程出错: {str(e)}"))
                self.root.after(0, lambda: self.wxauto_status.config(text="检查失败", style="Red.TLabel"))
                self.root.after(0, lambda: messagebox.showerror("检查失败", f"检查wxauto文件夹失败: {str(e)}"))
            finally:
                # 恢复按钮状态
                self.root.after(0, lambda: self.install_wxauto_button.config(state=tk.NORMAL))

        # 在新线程中运行检查过程
        threading.Thread(target=check_thread, daemon=True).start()

    def show_wxautox_install(self):
        """显示wxautox安装说明"""
        # 创建一个新窗口显示详细的安装说明
        install_info = tk.Toplevel(self.root)
        install_info.title("wxautox安装向导")
        install_info.geometry("500x400")
        install_info.resizable(True, True)
        install_info.transient(self.root)
        install_info.grab_set()

        # 确保窗口在屏幕中央
        install_info.update_idletasks()
        width = install_info.winfo_width()
        height = install_info.winfo_height()
        x = (install_info.winfo_screenwidth() // 2) - (width // 2)
        y = (install_info.winfo_screenheight() // 2) - (height // 2)
        install_info.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        # 创建主框架
        main_frame = tk.Frame(install_info, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 添加标题
        title_label = tk.Label(main_frame, text="wxautox安装向导", font=("TkDefaultFont", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # 添加详细说明
        info_text = """wxautox是付费增强库，需要单独购买并安装。

安装步骤:
1. 点击下方的【开始安装】按钮
2. 在文件选择对话框中找到并选择wxautox的wheel文件
   (文件名格式为: wxautox-x.x.x.x-cpxxx-cpxxx-xxx.whl)
3. 系统将自动安装并配置wxautox库
4. 安装完成后，重启服务即可使用wxautox库

您也可以通过命令行手动安装:
pip install wxautox-x.x.x.x-cpxxx-cpxxx-xxx.whl"""

        # 创建滚动文本区域
        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        text_scroll = tk.Scrollbar(text_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        info_area = tk.Text(text_frame, wrap=tk.WORD, height=12, width=50,
                           font=("TkDefaultFont", 10),
                           yscrollcommand=text_scroll.set)
        info_area.insert(tk.END, info_text)
        info_area.config(state=tk.DISABLED)  # 设置为只读
        info_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        text_scroll.config(command=info_area.yview)

        # 添加文档链接
        link_frame = tk.Frame(main_frame)
        link_frame.pack(fill=tk.X, pady=(5, 15))

        link_label = tk.Label(link_frame, text="更多信息请访问: ", font=("TkDefaultFont", 9))
        link_label.pack(side=tk.LEFT)

        # 创建一个可点击的链接
        link_button = tk.Label(
            link_frame,
            text="https://docs.wxauto.org/",
            fg="blue",
            cursor="hand2",
            font=("TkDefaultFont", 9, "underline")
        )
        link_button.pack(side=tk.LEFT)

        # 添加点击事件
        def open_url(event):
            import webbrowser
            webbrowser.open_new("https://docs.wxauto.org/")

        link_button.bind("<Button-1>", open_url)

        # 添加按钮框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # 添加安装按钮 - 使用ttk.Button与主界面按钮保持一致
        install_button = ttk.Button(
            button_frame,
            text="开始安装",
            command=lambda: [install_info.destroy(), self.select_wxautox_file()]
        )
        install_button.pack(side=tk.LEFT, padx=(0, 10))

        # 添加取消按钮 - 使用ttk.Button与主界面按钮保持一致
        cancel_button = ttk.Button(
            button_frame,
            text="取消",
            command=install_info.destroy
        )
        cancel_button.pack(side=tk.LEFT)

    def select_wxautox_file(self):
        """选择并安装wxautox wheel文件"""
        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(
            title="选择wxautox wheel文件",
            filetypes=[("Wheel文件", "*.whl"), ("所有文件", "*.*")],
            initialdir=os.getcwd()
        )

        if not file_path:
            return  # 用户取消了选择

        # 检查文件名是否包含wxautox
        if 'wxautox-' not in os.path.basename(file_path):
            messagebox.showerror("错误", "所选文件不是wxautox wheel文件")
            return

        # 显示安装中对话框
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("wxautox安装中...")
        progress_dialog.geometry("400x200")
        progress_dialog.resizable(False, False)
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()

        # 居中显示
        progress_dialog.update_idletasks()
        width = progress_dialog.winfo_width()
        height = progress_dialog.winfo_height()
        x = (progress_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (progress_dialog.winfo_screenheight() // 2) - (height // 2)
        progress_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        # 创建主框架
        main_frame = ttk.Frame(progress_dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建进度提示
        ttk.Label(main_frame, text="正在安装wxautox，请稍候...", font=("TkDefaultFont", 12)).pack(pady=20)

        # 创建进度条
        progress = ttk.Progressbar(main_frame, mode="indeterminate", length=300)
        progress.pack(pady=10)
        progress.start()

        # 创建进度文本
        progress_var = tk.StringVar(value="安装准备中...")
        progress_label = ttk.Label(main_frame, textvariable=progress_var, font=("TkDefaultFont", 10))
        progress_label.pack(pady=10)

        # 在新线程中执行安装
        def install_thread():
            try:
                # 更新进度
                self.root.after(0, lambda: progress_var.set("正在安装wxautox..."))

                # 导入插件管理模块
                from app import plugin_manager

                # 安装wxautox
                success, message = plugin_manager.install_wxautox(file_path)

                # 在主线程中更新UI
                if success:
                    self.root.after(0, lambda: progress_var.set("安装成功！"))
                    self.root.after(0, lambda: self.add_log(f"wxautox安装成功: {message}"))
                    self.root.after(0, lambda: self.check_wxautox_status())
                    self.root.after(0, lambda: progress.stop())  # 停止进度条
                    self.root.after(1000, lambda: progress_dialog.destroy())
                    self.root.after(1200, lambda: messagebox.showinfo("安装成功",
                                                                   "wxautox库安装成功，已自动配置为使用wxautox库。\n\n"
                                                                   "如需立即使用，请重启服务。"))
                else:
                    self.root.after(0, lambda: progress_var.set("安装失败！"))
                    self.root.after(0, lambda: self.add_log(f"wxautox安装失败: {message}"))
                    self.root.after(0, lambda: progress.stop())  # 停止进度条
                    self.root.after(1000, lambda: progress_dialog.destroy())
                    self.root.after(1200, lambda: messagebox.showerror("安装失败", f"wxautox库安装失败:\n{message}"))
            except Exception as e:
                self.root.after(0, lambda: progress_var.set("安装出错！"))
                self.root.after(0, lambda: self.add_log(f"wxautox安装过程出错: {str(e)}"))
                self.root.after(0, lambda: progress.stop())  # 停止进度条
                self.root.after(1000, lambda: progress_dialog.destroy())
                self.root.after(1200, lambda: messagebox.showerror("安装错误", f"wxautox安装过程出错:\n{str(e)}"))

        # 启动安装线程
        threading.Thread(target=install_thread, daemon=True).start()

    def show_api_documentation(self):
        """显示API功能说明和对比"""
        # 创建一个新窗口
        api_window = tk.Toplevel(self.root)
        api_window.title("微信API功能说明")
        api_window.geometry("900x600")
        api_window.minsize(800, 500)

        # 创建一个Notebook（选项卡控件）
        notebook = ttk.Notebook(api_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建API概述选项卡
        overview_frame = ttk.Frame(notebook, padding=10)
        notebook.add(overview_frame, text="API概述")

        overview_text = """
        wxauto_http_api 提供了基于HTTP的微信自动化接口，支持两种微信自动化库：

        1. wxauto: 开源的微信自动化库，功能相对基础，默认内置
        2. wxautox: 增强版的付费微信自动化库，提供更多高级功能，需单独安装

        wxautox 相比 wxauto 的主要优势：
        • 完善和修复了 wxauto 存在的许多问题
        • 提供更高效的性能，大部分场景不再需要移动鼠标
        • 增加了更多高级功能，如自定义表情包发送、URL卡片发送、群管理等
        • 提供专属技术支持

        所有API接口都需要通过API密钥认证，在HTTP请求头中添加：
        X-API-Key: your_api_key_here

        API响应格式统一为JSON：
        {
            "code": 0,       // 状态码：0成功，非0失败
            "message": "",   // 响应消息
            "data": {}       // 响应数据
        }

        注意：wxautox 是完全兼容 wxauto 的，您可以保留现有 wxauto 项目，
        只需将 `from wxauto import WeChat` 更换为 `from wxautox import WeChat` 即可完成迁移。
        """

        overview_label = ttk.Label(overview_frame, text=overview_text, wraplength=850, justify="left")
        overview_label.pack(fill=tk.BOTH, expand=True)

        # 创建功能对比选项卡
        compare_frame = ttk.Frame(notebook, padding=10)
        notebook.add(compare_frame, text="功能对比")

        # 创建一个滚动区域
        compare_canvas = tk.Canvas(compare_frame)
        scrollbar = ttk.Scrollbar(compare_frame, orient="vertical", command=compare_canvas.yview)
        scrollable_frame = ttk.Frame(compare_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: compare_canvas.configure(
                scrollregion=compare_canvas.bbox("all")
            )
        )

        compare_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        compare_canvas.configure(yscrollcommand=scrollbar.set)

        compare_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 创建功能对比表格
        headers = ["功能类别", "API接口", "功能描述", "wxauto", "wxautox"]
        for i, header in enumerate(headers):
            ttk.Label(scrollable_frame, text=header, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=i, padx=5, pady=5, sticky="w")

        # 功能对比数据（根据官方文档 https://docs.wxauto.org/plus/about）
        comparison_data = [
            # 基础功能
            ["基础功能", "/api/wechat/initialize", "初始化微信实例", "✓", "✓"],
            ["基础功能", "/api/wechat/status", "获取微信状态", "✓", "✓"],

            # 消息发送
            ["消息类", "/api/message/send", "发送普通文本消息", "✓", "✓"],
            ["消息类", "/api/message/send-typing", "发送打字机模式消息", "✗", "✓"],
            ["消息类", "/api/message/send-file", "发送文件消息", "✓", "✓"],
            ["消息类", "/api/message/send-image", "发送图片消息", "✓", "✓"],
            ["消息类", "/api/message/send-video", "发送视频消息", "✓", "✓"],
            ["消息类", "/api/message/send-emotion", "发送自定义表情包", "✗", "✓"],
            ["消息类", "/api/message/send-card", "通过URL发送卡片", "✗", "✓"],
            ["消息类", "/api/message/send-at", "发送@群好友", "✓", "✓"],
            ["消息类", "/api/message/send-at-all", "发送@所有人", "✓", "✓"],
            ["消息类", "/api/message/quote", "引用消息", "✓", "✓"],
            ["消息类", "/api/message/quote-at", "引用时@", "✗", "✓"],

            # 消息获取
            ["消息类", "/api/message/get-history", "获取历史消息", "✓", "✓"],
            ["消息类", "/api/message/get-new", "获取新消息", "✓", "✓"],
            ["消息类", "/api/message/listen/add", "监听消息", "✓", "✓"],
            ["消息类", "/api/message/listen/get", "获取监听消息", "✓", "✓"],
            ["消息类", "/api/message/listen/remove", "移除监听", "✓", "✓"],
            ["消息类", "/api/message/get-card-url", "获取卡片消息链接", "✗", "✓"],
            ["消息类", "/api/message/get-location", "获取位置信息", "✗", "✓"],
            ["消息类", "/api/message/add-friend-from-msg", "通过消息添加好友", "✗", "✓"],
            ["消息类", "/api/message/get-details", "通过消息获取详情", "✗", "✓"],

            # 好友管理
            ["好友管理", "/api/contact/get-friends", "获取好友列表", "✓", "✓"],
            ["好友管理", "/api/contact/add-friend", "发送好友请求", "✓", "✓"],
            ["好友管理", "/api/contact/accept-friend", "接受好友请求", "✓", "✓"],
            ["好友管理", "/api/contact/set-remark", "修改备注", "✗", "✓"],
            ["好友管理", "/api/contact/add-tag", "增加标签", "✗", "✓"],
            ["好友管理", "/api/contact/set-disturb", "消息免打扰", "✗", "✓"],

            # 群管理
            ["群管理", "/api/group/get-groups", "获取群列表", "✗", "✓"],
            ["群管理", "/api/group/invite", "邀请入群", "✗", "✓"],
            ["群管理", "/api/group/get-members", "获取群成员", "✓", "✓"],
            ["群管理", "/api/group/set-name", "修改群名", "✗", "✓"],
            ["群管理", "/api/group/set-remark", "修改群备注", "✗", "✓"],
            ["群管理", "/api/group/set-announcement", "修改群公告", "✗", "✓"],
            ["群管理", "/api/group/set-nickname", "修改我在本群昵称", "✗", "✓"],
            ["群管理", "/api/group/set-disturb", "消息免打扰", "✗", "✓"],

            # 朋友圈和公众号
            ["朋友圈", "/api/moments/functions", "朋友圈相关功能", "✗", "✓"],
            ["公众号", "/api/official/menu", "跳转公众号菜单", "✗", "✓"],

            # 其他功能
            ["其他", "/api/system/resources", "获取系统资源", "✓", "✓"],
            ["其他", "/api/admin/reload-config", "重载配置", "✓", "✓"],
            ["其他", "/api/system/background-mode", "后台模式", "✗", "✓"],
            ["其他", "BUG修复", "修复开源版本的BUG", "✗", "✓"],
        ]

        for i, row in enumerate(comparison_data, 1):
            bg_color = "#f0f0f0" if i % 2 == 0 else "#ffffff"
            for j, cell in enumerate(row):
                if j >= 3:  # 对于wxauto和wxautox列，使用特殊颜色
                    fg_color = "green" if cell == "✓" else "red"
                    ttk.Label(scrollable_frame, text=cell, foreground=fg_color, background=bg_color).grid(row=i, column=j, padx=5, pady=2, sticky="w")
                else:
                    ttk.Label(scrollable_frame, text=cell, background=bg_color).grid(row=i, column=j, padx=5, pady=2, sticky="w")

        # 创建API调用示例选项卡
        example_frame = ttk.Frame(notebook, padding=10)
        notebook.add(example_frame, text="API调用示例")

        # 创建一个Notebook（选项卡控件）用于不同的示例
        example_notebook = ttk.Notebook(example_frame)
        example_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建CURL示例选项卡
        curl_frame = ttk.Frame(example_notebook, padding=5)
        example_notebook.add(curl_frame, text="CURL示例")

        curl_text = scrolledtext.ScrolledText(curl_frame, wrap=tk.WORD)
        curl_text.pack(fill=tk.BOTH, expand=True)

        curl_code = '''
# 1. 验证API密钥
curl -X POST http://localhost:5000/api/auth/verify \\
  -H "X-API-Key: your-api-key"

# 2. 初始化微信实例
curl -X POST http://localhost:5000/api/wechat/initialize \\
  -H "X-API-Key: your-api-key"

# 3. 获取微信状态
curl -X GET http://localhost:5000/api/wechat/status \\
  -H "X-API-Key: your-api-key"

# 4. 发送普通文本消息
curl -X POST http://localhost:5000/api/message/send \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "receiver": "文件传输助手",
    "message": "这是一条测试消息",
    "at_list": ["张三", "李四"],
    "clear": true
  }'

# 5. 发送文件消息
curl -X POST http://localhost:5000/api/message/send-file \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "receiver": "文件传输助手",
    "file_paths": [
      "D:/test/test1.txt",
      "D:/test/test2.txt"
    ]
  }'

# 6. 添加监听对象
curl -X POST http://localhost:5000/api/message/listen/add \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "who": "测试群",
    "savepic": true,
    "savevideo": false,
    "savefile": false,
    "savevoice": false,
    "parseurl": false
  }'

# 7. 获取监听消息
curl -X GET "http://localhost:5000/api/message/listen/get?who=测试群" \\
  -H "X-API-Key: your-api-key"

# 8. 移除监听对象
curl -X POST http://localhost:5000/api/message/listen/remove \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "who": "测试群"
  }'

# 9. 获取系统资源
curl -X GET http://localhost:5000/api/system/resources \\
  -H "X-API-Key: your-api-key"
'''

        curl_text.insert(tk.END, curl_code)
        curl_text.config(state=tk.DISABLED)

        # 创建Python示例选项卡
        python_frame = ttk.Frame(example_notebook, padding=5)
        example_notebook.add(python_frame, text="Python示例")

        python_text = scrolledtext.ScrolledText(python_frame, wrap=tk.WORD)
        python_text.pack(fill=tk.BOTH, expand=True)

        python_code = '''
import requests

# API基础URL和密钥
base_url = "http://localhost:5000"
api_key = "your-api-key"
headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

# 1. 初始化微信
response = requests.post(
    f"{base_url}/api/wechat/initialize",
    headers=headers
)
print("初始化结果:", response.json())

# 2. 发送消息
response = requests.post(
    f"{base_url}/api/message/send",
    headers=headers,
    json={
        "receiver": "文件传输助手",
        "message": "这是一条测试消息",
        "at_list": ["张三", "李四"]
    }
)
print("发送消息结果:", response.json())

# 3. 添加监听
response = requests.post(
    f"{base_url}/api/message/listen/add",
    headers=headers,
    json={
        "who": "测试群",
        "savepic": True
    }
)
print("添加监听结果:", response.json())

# 4. 获取监听消息
response = requests.get(
    f"{base_url}/api/message/listen/get",
    headers=headers,
    params={"who": "测试群"}
)
print("监听消息:", response.json())
'''

        python_text.insert(tk.END, python_code)
        python_text.config(state=tk.DISABLED)

        # 创建JavaScript示例选项卡
        js_frame = ttk.Frame(example_notebook, padding=5)
        example_notebook.add(js_frame, text="JavaScript示例")

        js_text = scrolledtext.ScrolledText(js_frame, wrap=tk.WORD)
        js_text.pack(fill=tk.BOTH, expand=True)

        js_code = '''
// API基础URL和密钥
const baseUrl = "http://localhost:5000";
const apiKey = "your-api-key";
const headers = {
    "X-API-Key": apiKey,
    "Content-Type": "application/json"
};

// 1. 初始化微信
fetch(`${baseUrl}/api/wechat/initialize`, {
    method: "POST",
    headers: headers
})
.then(response => response.json())
.then(data => console.log("初始化结果:", data))
.catch(error => console.error("初始化错误:", error));

// 2. 发送消息
fetch(`${baseUrl}/api/message/send`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({
        receiver: "文件传输助手",
        message: "这是一条测试消息",
        at_list: ["张三", "李四"]
    })
})
.then(response => response.json())
.then(data => console.log("发送消息结果:", data))
.catch(error => console.error("发送消息错误:", error));

// 3. 添加监听
fetch(`${baseUrl}/api/message/listen/add`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({
        who: "测试群",
        savepic: true
    })
})
.then(response => response.json())
.then(data => console.log("添加监听结果:", data))
.catch(error => console.error("添加监听错误:", error));

// 4. 获取监听消息
fetch(`${baseUrl}/api/message/listen/get?who=测试群`, {
    headers: headers
})
.then(response => response.json())
.then(data => console.log("监听消息:", data))
.catch(error => console.error("获取监听消息错误:", error));
'''

        js_text.insert(tk.END, js_code)
        js_text.config(state=tk.DISABLED)

        # 设置默认选项卡
        example_notebook.select(0)

        # 设置默认选项卡
        notebook.select(0)

    def on_lib_change(self):
        """处理库选择变更"""
        selected_lib = self.lib_var.get()

        # 检查所选库是否已安装
        if selected_lib == "wxauto" and not self.check_wxauto_status():
            messagebox.showwarning("库未安装", "wxauto库未安装，请先安装")
            self.lib_var.set(self.current_lib)
            return

        if selected_lib == "wxautox" and not self.check_wxautox_status():
            messagebox.showwarning("库未安装", "wxautox库未安装，请先安装")
            self.lib_var.set(self.current_lib)
            return

        try:
            # 加载当前配置
            config = config_manager.load_app_config()

            # 更新库配置
            config['wechat_lib'] = selected_lib

            # 保存配置
            config_manager.save_app_config(config)

            # 标记配置已修改
            global CONFIG_MODIFIED
            CONFIG_MODIFIED = True

            # 更新UI
            self.current_lib = selected_lib
            self.current_lib_label.config(text=selected_lib)

            self.add_log(f"已更新微信库配置: {selected_lib}")
        except Exception as e:
            self.add_log(f"更新微信库配置失败: {str(e)}")
            messagebox.showerror("错误", f"更新微信库配置失败: {str(e)}")

        # 如果服务正在运行，提示需要重启
        if self.api_running:
            messagebox.showinfo("需要重启", "库已切换，需要重启服务才能生效")

    # 这些方法已被移除，配置现在通过插件配置对话框进行管理

    def start_api_service(self):
        """启动API服务"""
        global API_PROCESS

        if self.api_running:
            messagebox.showinfo("提示", "服务已经在运行中")
            return

        # 检查所选库是否已安装
        selected_lib = self.lib_var.get()
        if selected_lib == "wxauto" and not self.check_wxauto_status():
            messagebox.showwarning("库未安装", "wxauto库未安装，请先安装")
            return

        if selected_lib == "wxautox" and not self.check_wxautox_status():
            messagebox.showwarning("库未安装", "wxautox库未安装，请先安装")
            return

        # 从配置文件获取端口号
        try:
            config = config_manager.load_app_config()
            port = config.get('port', 5000)

            # 更新UI显示
            self.port_var.set(str(port))

            if port < 1 or port > 65535:
                messagebox.showwarning("端口错误", "配置文件中的端口号必须在1-65535之间")
                return
        except Exception as e:
            self.add_log(f"读取端口配置失败: {str(e)}")
            messagebox.showwarning("配置错误", f"读取端口配置失败: {str(e)}")
            return

        # 启动服务
        try:
            # 在打包环境中，使用不同的启动方式
            if getattr(sys, 'frozen', False):
                # 如果是打包后的环境，直接使用可执行文件启动API服务
                executable = sys.executable
                cmd = [executable, "--service", "api", "--debug"]
            else:
                # 如果是开发环境，使用Python解释器启动main.py
                cmd = [sys.executable, "main.py", "--service", "api"]

                # 添加调试参数，以获取更详细的日志
                if os.environ.get("WXAUTO_DEBUG") == "1":
                    cmd.append("--debug")

            # 记录启动命令
            self.add_log(f"启动命令: {' '.join(cmd)}")

            API_PROCESS = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # 启动日志读取线程
            threading.Thread(target=self.read_process_output, daemon=True).start()

            # 更新状态
            self.api_running = True
            self.api_status.config(text="运行中", style="Green.TLabel")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

            # 记录启动时间
            self.start_time = time.time()

            # 记录当前端口
            self.current_port = port

            # 重置API调用计数
            global API_COUNTER
            API_COUNTER.reset()
            self.request_count.config(text="0")
            self.error_count.config(text="0")

            # 添加日志
            self.add_log(f"API服务已启动，监听地址: 0.0.0.0:{port}")

            # 更新UI中的监听地址显示
            self.api_address.config(text=f"0.0.0.0:{port}")

            # 等待服务启动完成
            time.sleep(2)

            # 自动初始化微信
            self.add_log("正在自动初始化微信...")

            # 使用线程执行初始化，避免阻塞UI
            # 延迟1秒执行初始化，确保API服务已完全启动
            self.root.after(1000, lambda: threading.Thread(target=self._initialize_wechat_thread, args=(port,), daemon=True).start())

        except Exception as e:
            messagebox.showerror("启动失败", f"启动API服务失败: {str(e)}")

    def stop_api_service(self):
        """停止API服务"""
        global API_PROCESS

        if not self.api_running:
            messagebox.showinfo("提示", "服务未在运行")
            return

        try:
            # 停止服务
            if API_PROCESS:
                if sys.platform == 'win32':
                    # Windows下使用taskkill强制终止进程
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(API_PROCESS.pid)])
                else:
                    # Linux/Mac下使用kill信号
                    os.kill(API_PROCESS.pid, signal.SIGTERM)

                API_PROCESS = None

            # 更新状态
            self.api_running = False
            self.api_status.config(text="未运行", style="Red.TLabel")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.wechat_status.config(text="未连接", style="Red.TLabel")

            # 添加日志
            self.add_log("API服务已停止")

        except Exception as e:
            messagebox.showerror("停止失败", f"停止API服务失败: {str(e)}")

    def read_process_output(self):
        """读取进程输出并添加到日志"""
        global API_PROCESS

        if not API_PROCESS:
            return

        for line in iter(API_PROCESS.stdout.readline, ''):
            if line:
                # 处理行内容，移除可能存在的时间戳
                line_content = line.strip()

                # 移除常见的时间戳格式
                # 使用与APILogHandler._remove_timestamp相同的逻辑
                import re

                # 移除类似 "2025-05-08 11:50:17,850" 这样的时间戳
                line_content = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(,\d{3})? - ', '', line_content)

                # 移除类似 "[2025-05-08 11:50:17]" 这样的时间戳
                line_content = re.sub(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] ', '', line_content)

                # 移除类似 "2025-05-08 12:04:46" 这样的时间戳（Flask日志格式）
                line_content = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - ', '', line_content)

                # 移除类似 "127.0.0.1 - - [08/May/2025 12:04:46]" 这样的Werkzeug日志格式
                if ' - - [' in line_content and '] "' in line_content:
                    parts = line_content.split('] "', 1)
                    if len(parts) > 1:
                        ip_part = parts[0].split(' - - [')[0]
                        request_part = parts[1]
                        line_content = f"{ip_part} - {request_part}"

                self.add_log(line_content)

            # 检查进程是否还在运行
            if API_PROCESS:
                if isinstance(API_PROCESS, subprocess.Popen):
                    # 如果是subprocess.Popen对象，使用poll()方法
                    if API_PROCESS.poll() is not None:
                        self.add_log(f"API服务已退出，返回码: {API_PROCESS.returncode}")
                        self.root.after(0, self.update_status_stopped)
                        break
                else:
                    # 如果是psutil.Process对象，检查是否存在
                    try:
                        if not psutil.pid_exists(API_PROCESS.pid):
                            self.add_log(f"API服务已退出")
                            self.root.after(0, self.update_status_stopped)
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        self.add_log(f"API服务已退出")
                        self.root.after(0, self.update_status_stopped)
                        break

    def update_status_stopped(self):
        """更新状态为已停止"""
        self.api_running = False
        self.api_status.config(text="未运行", style="Red.TLabel")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.wechat_status.config(text="未连接", style="Red.TLabel")

    def reload_config(self):
        """重载配置"""
        if not self.api_running:
            messagebox.showinfo("提示", "服务未在运行，无需重载配置")
            return

        # 显示加载中状态
        self.reload_button.config(state=tk.DISABLED)
        self.add_log("正在重载配置...")

        # 使用线程执行HTTP请求，避免阻塞UI
        threading.Thread(target=self._reload_config_thread, daemon=True).start()

    def _reload_config_thread(self):
        """在线程中执行配置重载"""
        try:
            # 发送重载配置请求
            reload_url = f"http://localhost:{self.current_port}/api/admin/reload-config"
            response = requests.post(
                reload_url,
                headers={"X-API-Key": self.get_api_key()},
                timeout=3  # 3秒超时
            )

            if response.status_code == 200:
                # 在主线程中更新UI
                self.root.after(0, lambda: self.add_log("配置重载成功"))
                self.root.after(0, lambda: messagebox.showinfo("成功", "配置已重载"))
                # 重置配置修改标志
                global CONFIG_MODIFIED
                CONFIG_MODIFIED = False
            else:
                self.root.after(0, lambda: self.add_log(f"配置重载失败: {response.text}"))
                self.root.after(0, lambda: messagebox.showerror("失败", f"重载配置失败: {response.text}"))

        except requests.exceptions.Timeout:
            self.root.after(0, lambda: self.add_log("配置重载超时"))
            self.root.after(0, lambda: messagebox.showerror("失败", "重载配置超时，服务可能未响应"))
        except Exception as e:
            self.root.after(0, lambda: self.add_log(f"配置重载失败: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("失败", f"重载配置失败: {str(e)}"))
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.reload_button.config(state=tk.NORMAL))

    def show_config_dialog(self):
        """显示插件配置对话框"""
        # 创建配置对话框
        config_dialog = tk.Toplevel(self.root)
        config_dialog.title("插件配置")
        config_dialog.geometry("400x300")
        config_dialog.resizable(False, False)
        config_dialog.transient(self.root)  # 设置为主窗口的子窗口
        config_dialog.grab_set()  # 模态对话框

        # 创建设置框架
        settings_frame = ttk.Frame(config_dialog, padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        # 添加标题
        ttk.Label(settings_frame, text="插件配置设置", font=("TkDefaultFont", 12, "bold")).pack(pady=10)

        # 端口设置区域
        port_frame = ttk.Frame(settings_frame)
        port_frame.pack(fill=tk.X, pady=10)

        ttk.Label(port_frame, text="端口号:").pack(side=tk.LEFT, padx=5)
        port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10)
        port_entry.pack(side=tk.LEFT, padx=5)

        # API Key设置区域
        apikey_frame = ttk.Frame(settings_frame)
        apikey_frame.pack(fill=tk.X, pady=10)

        ttk.Label(apikey_frame, text="API Key:").pack(side=tk.LEFT, padx=5)
        apikey_entry = ttk.Entry(apikey_frame, textvariable=self.apikey_var, width=30)
        apikey_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 说明文本
        ttk.Separator(settings_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(settings_frame, text="注意: 配置将在保存后自动应用，但需要重启服务才能生效",
                 wraplength=380).pack(pady=5)

        # 按钮区域
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # 保存按钮
        ttk.Button(
            button_frame,
            text="保存配置",
            command=lambda: [self.save_config(), config_dialog.destroy()]
        ).pack(side=tk.RIGHT, padx=5)

        # 取消按钮
        ttk.Button(
            button_frame,
            text="取消",
            command=config_dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def save_config(self):
        """保存配置到配置文件"""
        try:
            # 获取当前配置
            port = self.port_var.get().strip()
            api_key = self.apikey_var.get().strip()

            # 验证输入
            if not port:
                messagebox.showwarning("警告", "端口号不能为空")
                return

            if not api_key:
                messagebox.showwarning("警告", "API Key不能为空")
                return

            try:
                port = int(port)
                if port < 1 or port > 65535:
                    messagebox.showwarning("警告", "端口号必须在1-65535之间")
                    return
            except ValueError:
                messagebox.showwarning("警告", "端口号必须是数字")
                return

            # 加载当前配置
            config = config_manager.load_app_config()

            # 更新配置
            config['port'] = port
            config['api_keys'] = [api_key]

            # 保存配置
            config_manager.save_app_config(config)

            # 标记配置已修改
            global CONFIG_MODIFIED
            CONFIG_MODIFIED = True

            # 提示用户
            self.add_log(f"配置已保存 - 端口: {port}, API Key: {api_key}")
            messagebox.showinfo("成功", "配置已保存，请重载配置使其生效")
        except Exception as e:
            self.add_log(f"保存配置失败: {str(e)}")
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")

    def get_api_key(self):
        """获取当前API密钥"""
        # 优先使用UI中设置的API Key
        api_key = self.apikey_var.get().strip()
        if api_key:
            return api_key

        # 如果UI中没有设置，从配置文件中读取
        try:
            config = config_manager.load_app_config()
            api_keys = config.get('api_keys', [])
            if api_keys:
                return api_keys[0]
        except Exception as e:
            self.add_log(f"从配置文件读取API Key失败: {str(e)}")

        # 如果配置文件中没有，从.env文件中读取
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("API_KEYS="):
                        keys = line.strip()[9:].split(",")
                        if keys:
                            return keys[0]

        return "test-key-2"  # 默认API密钥

    def add_log(self, message):
        """添加日志到日志区域"""
        # 使用完整的时间戳格式，精确到秒
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 检查消息中是否已经包含库信息标记 [wxauto] 或 [wxautox]
        if "[wxauto]" in message or "[wxautox]" in message:
            # 已经包含库信息，只添加时间戳
            log_message = f"[{timestamp}] {message}"
        else:
            # 不包含库信息，添加时间戳和库信息
            lib_name = getattr(self, 'current_lib', 'wxauto')  # 默认使用wxauto
            log_message = f"[{timestamp}] [{lib_name}] {message}"

        # 检查日志中是否包含窗口名称信息
        if "初始化成功，获取到已登录窗口：" in message:
            try:
                # 提取窗口名称
                window_name = message.split("初始化成功，获取到已登录窗口：")[1].strip()
                if window_name and hasattr(self, 'wechat_window_name'):
                    # 更新窗口名称标签
                    self.wechat_window_name.config(text=window_name, foreground="orange")
                    print(f"从日志中提取到窗口名称: {window_name}")
            except Exception as e:
                print(f"从日志中提取窗口名称失败: {str(e)}")

        # 应用过滤器，如果应该过滤掉，则不显示
        if self.should_filter_log(log_message):
            return

        # 获取当前滚动位置
        current_position = self.log_text.yview()

        # 判断用户是否已经滚动到底部
        # 如果第二个值接近1.0，表示用户正在查看最新内容
        at_bottom = current_position[1] > 0.99 or self.auto_scroll_var.get()

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message + "\n")

        # 限制日志显示数量为最新的200条
        log_content = self.log_text.get(1.0, tk.END)
        log_lines = log_content.split('\n')
        if len(log_lines) > 201:  # 加1是因为split后最后一个元素是空字符串
            # 计算需要删除的行数
            lines_to_delete = len(log_lines) - 201
            # 删除多余的行
            self.log_text.delete(1.0, f"{lines_to_delete + 1}.0")

        # 只有当用户当前在查看最新内容或启用了自动滚动时，才自动滚动到底部
        if at_bottom:
            self.log_text.see(tk.END)

        self.log_text.config(state=tk.DISABLED)

        # 添加一个状态指示，显示有新日志
        if not at_bottom and hasattr(self, 'new_log_indicator'):
            self.new_log_indicator.config(text="↓ 有新日志", foreground="red")

    def check_status(self):
        """定时检查状态"""
        # 使用静态计数器来控制不同检查的频率
        if not hasattr(self, '_check_counter'):
            self._check_counter = 0
        self._check_counter += 1

        # 每5秒检查一次插件状态，减少不必要的检查
        if self._check_counter % 5 == 0:
            self.check_wxauto_status()
            self.check_wxautox_status()

        # 如果服务在运行，检查服务状态
        if self.api_running and API_PROCESS:
            # 检查进程是否还在运行
            try:
                if isinstance(API_PROCESS, subprocess.Popen):
                    # 如果是subprocess.Popen对象，使用poll()方法
                    if API_PROCESS.poll() is not None:
                        self.update_status_stopped()
                        return
                else:
                    # 如果是psutil.Process对象，检查是否存在
                    if not psutil.pid_exists(API_PROCESS.pid):
                        self.update_status_stopped()
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.update_status_stopped()
                return

            # 更新资源使用情况 - 每秒更新一次
            try:
                process = psutil.Process(API_PROCESS.pid)

                # CPU使用率 - 不使用interval参数，避免阻塞
                cpu_percent = process.cpu_percent(interval=None)
                self.cpu_usage.config(text=f"{cpu_percent:.1f}%")

                # 内存使用 - 每2秒更新一次，减少系统调用
                if self._check_counter % 2 == 0:
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    self.memory_usage.config(text=f"{memory_mb:.1f} MB")

                # 运行时间
                uptime_seconds = int(time.time() - self.start_time)
                hours, remainder = divmod(uptime_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.uptime.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

                # 检查微信连接状态 - 每3秒检查一次，减少API调用
                if self._check_counter % 3 == 0:
                    self.check_wechat_connection()

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                # 进程不存在或无法访问，更新状态
                self.update_status_stopped()
                return
            except Exception as e:
                # 其他错误，记录日志但不中断
                if self._check_counter % 10 == 0:  # 限制错误日志频率
                    self.add_log(f"状态检查错误: {str(e)}")

        # 如果配置已修改，提示重载
        if CONFIG_MODIFIED and self.api_running:
            self.reload_button.config(style="Bold.TButton")
        else:
            self.reload_button.config(style="TButton")

        # 继续定时检查，使用1秒间隔
        self.root.after(1000, self.check_status)

    def check_wechat_connection(self):
        """检查微信连接状态"""
        # 使用线程执行HTTP请求，避免阻塞UI
        threading.Thread(target=self._check_wechat_connection_thread, daemon=True).start()

    def _initialize_wechat_thread(self, port):
        """在线程中执行微信初始化"""
        # 最多尝试3次
        max_retries = 3
        retry_delay = 2  # 秒

        for attempt in range(1, max_retries + 1):
            try:
                self.add_log(f"微信初始化尝试 {attempt}/{max_retries}...")

                response = requests.post(
                    f"http://localhost:{port}/api/wechat/initialize",
                    headers={"X-API-Key": self.get_api_key()},
                    timeout=10
                )

                if response.status_code == 200 and response.json().get("code") == 0:
                    init_data = response.json()
                    self.add_log("微信自动初始化成功")

                    # 获取微信窗口名称
                    window_name = init_data.get("data", {}).get("window_name", "")

                    # 在主线程中更新UI
                    self.root.after(0, lambda: self.wechat_status.config(text="已连接", style="Green.TLabel"))

                    # 无论如何都显示窗口名称（如果有）
                    if window_name:
                        # 更新窗口名称标签
                        self.root.after(0, lambda wn=window_name: self.wechat_window_name.config(text=wn, foreground="orange"))
                        self.add_log(f"已连接到微信窗口: {window_name}")
                    else:
                        # 窗口名称为空，设置为空字符串
                        self.root.after(0, lambda: self.wechat_window_name.config(text=""))

                    # 初始化成功，退出重试循环
                    # 不要立即检查微信连接状态，等待下一个定时检查周期
                    return
                else:
                    error_msg = response.json().get("message", "未知错误")
                    self.add_log(f"微信自动初始化失败: {error_msg}")

                    if attempt == max_retries:
                        # 最后一次尝试失败，更新UI
                        self.root.after(0, lambda: self.wechat_status.config(text="初始化失败", style="Red.TLabel"))
                        # 清除窗口名称（如果存在）
                        if hasattr(self, 'wechat_window_name'):
                            self.root.after(0, lambda: self.wechat_window_name.config(text=""))
                    else:
                        # 等待一段时间后重试
                        self.add_log(f"将在 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
            except Exception as e:
                self.add_log(f"微信自动初始化请求失败: {str(e)}")

                if attempt == max_retries:
                    # 最后一次尝试失败，更新UI
                    self.root.after(0, lambda: self.wechat_status.config(text="初始化失败", style="Red.TLabel"))
                else:
                    # 等待一段时间后重试
                    self.add_log(f"将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)

    def _check_wechat_connection_thread(self):
        """在线程中执行微信连接状态检查"""
        try:
            api_url = f"http://localhost:{self.current_port}/api/wechat/status"
            # 添加超时设置，避免长时间阻塞
            response = requests.get(
                api_url,
                headers={"X-API-Key": self.get_api_key()},
                timeout=2  # 2秒超时
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and data.get("data", {}).get("status") == "online":
                    # 获取微信窗口名称
                    window_name = data.get("data", {}).get("window_name", "")

                    # 使用after方法在主线程中更新UI
                    # 设置连接状态
                    self.root.after(0, lambda: self.wechat_status.config(text="已连接", style="Green.TLabel"))

                    # 无论如何都显示窗口名称（如果有）
                    if window_name:
                        # 更新窗口名称标签
                        self.root.after(0, lambda: self.wechat_window_name.config(text=window_name, foreground="orange"))
                        self.root.after(0, lambda: self.add_log(f"已连接到微信窗口: {window_name}"))
                    elif self.wechat_window_name.cget("text") == "":
                        # 如果窗口名称为空，尝试设置为"获取中..."
                        self.root.after(0, lambda: self.wechat_window_name.config(text="获取中...", foreground="orange"))

                    # 更新API地址
                    self.root.after(0, lambda: self.api_address.config(text=f"0.0.0.0:{self.current_port}"))
                    return
                else:
                    self.root.after(0, lambda: self.wechat_status.config(text="未连接", style="Red.TLabel"))
                    # 清除窗口名称（如果存在）
                    if hasattr(self, 'wechat_window_name'):
                        self.root.after(0, lambda: self.wechat_window_name.config(text=""))
            elif response.status_code == 400:
                # 微信未初始化，自动调用初始化接口
                self.root.after(0, lambda: self.add_log("检测到微信未初始化，正在自动初始化..."))
                self.root.after(0, lambda: self.wechat_status.config(text="正在初始化...", style="Bold.TLabel"))

                # 调用初始化接口
                init_url = f"http://localhost:{self.current_port}/api/wechat/initialize"
                init_response = requests.post(
                    init_url,
                    headers={"X-API-Key": self.get_api_key()},
                    timeout=5  # 初始化可能需要更长时间，设置5秒超时
                )

                if init_response.status_code == 200 and init_response.json().get("code") == 0:
                    init_data = init_response.json()
                    self.root.after(0, lambda: self.add_log("微信自动初始化成功"))

                    # 获取微信窗口名称
                    window_name = init_data.get("data", {}).get("window_name", "")

                    # 设置连接状态
                    self.root.after(0, lambda: self.wechat_status.config(text="已连接", style="Green.TLabel"))

                    # 不要立即检查微信连接状态，等待下一个定时检查周期

                    # 无论如何都显示窗口名称（如果有）
                    if window_name:
                        # 更新窗口名称标签
                        self.root.after(0, lambda: self.wechat_window_name.config(text=window_name, foreground="orange"))
                        self.root.after(0, lambda: self.add_log(f"已连接到微信窗口: {window_name}"))
                    elif self.wechat_window_name.cget("text") == "" or self.wechat_window_name.cget("text") == "获取中...":
                        # 如果窗口名称为空，尝试设置为"获取中..."
                        self.root.after(0, lambda: self.wechat_window_name.config(text="获取中...", foreground="orange"))

                    # 更新API地址
                    self.root.after(0, lambda: self.api_address.config(text=f"0.0.0.0:{self.current_port}"))
                else:
                    error_msg = init_response.json().get("message", "未知错误")
                    self.root.after(0, lambda: self.add_log(f"微信自动初始化失败: {error_msg}"))
                    self.root.after(0, lambda: self.wechat_status.config(text="初始化失败", style="Red.TLabel"))
                    # 清除窗口名称（如果存在）
                    if hasattr(self, 'wechat_window_name'):
                        self.root.after(0, lambda: self.wechat_window_name.config(text=""))
            else:
                self.root.after(0, lambda: self.wechat_status.config(text="未连接", style="Red.TLabel"))

        except requests.exceptions.Timeout:
            # 请求超时，不记录日志，静默失败
            self.root.after(0, lambda: self.wechat_status.config(text="连接超时", style="Red.TLabel"))
        except Exception as e:
            self.root.after(0, lambda: self.add_log(f"检查微信连接状态出错: {str(e)}"))
            self.root.after(0, lambda: self.wechat_status.config(text="未连接", style="Red.TLabel"))

    def update_status(self):
        """初始化状态"""
        try:
            # 从配置文件加载配置
            config = config_manager.load_app_config()

            # 设置微信库
            lib_name = config.get('wechat_lib', 'wxauto')
            self.current_lib = lib_name
            self.lib_var.set(lib_name)
            self.current_lib_label.config(text=lib_name)

            # 设置端口
            port = config.get('port', 5000)
            self.current_port = port
            self.port_var.set(str(port))

            # 设置API Key
            api_keys = config.get('api_keys', ['test-key-2'])
            if api_keys:
                self.apikey_var.set(api_keys[0])

            self.add_log("从配置文件加载配置成功")
        except Exception as e:
            self.add_log(f"从配置文件加载配置失败: {str(e)}")

            # 如果配置文件加载失败，尝试从.env文件加载
            env_file = ".env"
            if os.path.exists(env_file):
                with open(env_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                    # 读取库配置
                    for line in lines:
                        if line.strip().startswith("WECHAT_LIB="):
                            lib_name = line.strip()[11:].strip()
                            self.current_lib = lib_name
                            self.lib_var.set(lib_name)
                            self.current_lib_label.config(text=lib_name)

                    # 读取端口配置
                    for line in lines:
                        if line.strip().startswith("PORT="):
                            try:
                                port = int(line.strip()[5:].strip())
                                self.current_port = port
                                self.port_var.set(str(port))
                            except ValueError:
                                pass

                    # 读取API Key配置
                    for line in lines:
                        if line.strip().startswith("API_KEYS="):
                            keys = line.strip()[9:].split(",")
                            if keys:
                                self.apikey_var.set(keys[0])

        # 初始化按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        # 检查服务是否已在运行
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe' and any('run.py' in cmd for cmd in proc.info['cmdline'] if cmd):
                    # 找到了运行中的服务
                    global API_PROCESS
                    API_PROCESS = proc
                    self.api_running = True
                    self.api_status.config(text="运行中", style="Green.TLabel")
                    self.start_button.config(state=tk.DISABLED)
                    self.stop_button.config(state=tk.NORMAL)
                    self.start_time = proc.create_time()
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def start_countdown(self):
        """开始倒计时"""
        if self.countdown_seconds > 0:
            # 根据剩余秒数显示不同的提示
            if self.countdown_seconds == 5:
                self.add_log("【自动启动】5 秒后启动服务...")
            elif self.countdown_seconds == 3:
                self.add_log("【自动启动】3 秒后启动服务...")
            elif self.countdown_seconds == 2:
                self.add_log("【自动启动】2 秒后启动服务...")
            elif self.countdown_seconds == 1:
                self.add_log("【自动启动】1 秒后启动服务...")

            self.countdown_seconds -= 1
            self.root.after(1000, self.start_countdown)
        else:
            self.add_log("【自动启动】倒计时结束，准备启动服务...")
            self.auto_start_service()

    def auto_start_service(self):
        """自动启动服务"""
        # 如果服务已经在运行，不需要再启动
        if self.api_running:
            self.add_log("【自动启动】服务已在运行，无需再次启动")
            return

        # 检查当前选中的框架是否已安装
        current_lib = self.lib_var.get()
        is_installed = False

        if current_lib == "wxauto":
            is_installed = self.check_wxauto_status()
        elif current_lib == "wxautox":
            is_installed = self.check_wxautox_status()

        # 如果已安装，自动启动服务
        if is_installed:
            self.add_log(f"【自动启动】检测到 {current_lib} 已安装")
            self.add_log("【自动启动】正在启动服务...")
            self.start_api_service()
        else:
            self.add_log(f"【自动启动】当前选中的框架 {current_lib} 未安装")
            self.add_log("【自动启动】请先安装框架后手动启动服务")

    def on_close(self):
        """关闭窗口时的处理"""
        if self.api_running:
            if messagebox.askyesno("确认", "API服务正在运行，是否关闭服务并退出？"):
                self.stop_api_service()
                self.root.destroy()
        else:
            self.root.destroy()

# 主函数
def main():
    root = tk.Tk()
    app = WxAutoHttpUI(root)
    root.mainloop()

if __name__ == "__main__":
    # 确保当前目录在Python路径中
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    try:
        # 导入项目模块
        from app.config import Config
        from app.logs import logger

        # 启动UI
        main()
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请使用 start_ui.py 启动UI")