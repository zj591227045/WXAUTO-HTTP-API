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
from tkinter import ttk, messagebox
import signal
import psutil
import requests
import traceback

# 导入配置管理模块
try:
    # 首先尝试从app包导入
    from app import config_manager

    # print("成功从app包导入 config_manager 模块")  # 注释掉，避免stdout问题
except ImportError:
    # 如果失败，尝试直接导入（兼容旧版本）
    import config_manager

    # print("成功直接导入 config_manager 模块")  # 注释掉，避免stdout问题

# 确保当前目录在Python路径中，以便能够导入app模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入项目模块
try:
    from app.unified_logger import unified_logger, logger
except ImportError:
    # print("无法导入项目模块，请确保在正确的目录中运行")  # 注释掉，避免stdout问题
    sys.exit(1)

# 全局变量
API_PROCESS = None
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
            # print(f"API成功计数增加: {self.success_count}, 日志: {log_line}")  # 注释掉，避免stdout问题
        # 计算失败的API调用 - 确保状态码周围有空格，避免误匹配
        elif ((
                      " 400 " in log_line or " 401 " in log_line or " 404 " in log_line or " 500 " in log_line) and "状态码:" in log_line):
            self.error_count += 1
            # print(f"API错误计数增加: {self.error_count}, 日志: {log_line}")  # 注释掉，避免stdout问题

        # 打印当前计数
        # print(f"当前API计数 - 成功: {self.success_count}, 错误: {self.error_count}")  # 注释掉，避免stdout问题


API_COUNTER = ApiCounter()


# 移除旧的APILogHandler类，使用新的统一日志管理器


class WxAutoHttpUI:
    """wxauto_http_api 客户端"""

    def __init__(self, root):
        # 确保使用UTF-8编码
        import sys
        if hasattr(sys, 'setdefaultencoding'):
            sys.setdefaultencoding('utf-8')

        # 设置环境变量，确保子进程使用UTF-8编码
        import os
        os.environ['PYTHONIOENCODING'] = 'utf-8'

        self.root = root
        self.root.title("wxauto_http_api 客户端")

        # 设置窗口为自适应大小，根据内容调整
        # 先设置一个更紧凑的最小尺寸
        self.root.minsize(500, 300)

        # 获取屏幕尺寸用于居中
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 暂时设置一个初始位置，稍后会根据实际大小调整
        initial_x = int(screen_width / 2 - 400)  # 假设初始宽度800
        initial_y = int(screen_height / 2 - 200)  # 假设初始高度400
        self.root.geometry(f"+{initial_x}+{initial_y}")

        # 禁止窗口大小调整（可选，如果希望固定大小）
        # self.root.resizable(False, False)

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

        # 初始化状态变量（必须在创建UI之前）
        self.api_running = False
        self.current_lib = "wxauto"  # 默认使用wxauto
        self.current_port = 5000  # 默认端口号
        self._ui_closing = False  # 添加关闭标志

        # 初始化自动启动相关变量（必须在创建UI之前）
        self.auto_start_enabled = tk.BooleanVar(value=False)  # 默认不自动启动
        self.auto_start_countdown = tk.IntVar(value=5)  # 默认5秒倒计时
        self.countdown_seconds = 0
        self.countdown_timer = None

        # 创建主框架（减少padding以获得更紧凑的布局）
        self.main_frame = ttk.Frame(self.root, padding="5")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建顶部控制区域
        self.create_control_panel()

        # 创建中间状态区域
        self.create_status_panel()

        # 创建底部按钮区域
        self.create_bottom_panel()

        # 启动状态更新定时器
        self.update_status()
        self._status_timer_id = self.root.after(1000, self.check_status)

        # 设置关闭窗口事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 初始化日志处理
        self.setup_logging()

        # 调整窗口大小以适应内容
        self.root.after(100, self.adjust_window_size)

        # 检查是否启用自动启动（在UI创建完成后）
        self.root.after(200, self.check_auto_start)

    def check_auto_start(self):
        """检查是否需要自动启动"""
        if self.auto_start_enabled.get():
            self.countdown_seconds = self.auto_start_countdown.get()
            self.add_log("===== 自动启动服务 =====")
            self.add_log(f"将在 {self.countdown_seconds} 秒后自动启动服务...")
            self.start_countdown()
        else:
            self.add_log("自动启动已禁用，请手动启动服务")

    def on_auto_start_toggle(self):
        """自动启动复选框切换事件"""
        # 保存配置到文件
        self.save_auto_start_config()

        if self.auto_start_enabled.get():
            # 启用自动启动
            if not self.api_running:  # 只有在服务未运行时才启动倒计时
                self.countdown_seconds = self.auto_start_countdown.get()
                self.add_log(f"已启用自动启动，将在 {self.countdown_seconds} 秒后启动服务")
                self.start_countdown()
        else:
            # 禁用自动启动
            if self.countdown_timer:
                self.root.after_cancel(self.countdown_timer)
                self.countdown_timer = None
            self.add_log("已禁用自动启动")
            # 恢复按钮文本
            self.start_button.config(text="启动服务")

    def on_countdown_change(self):
        """倒计时时间改变事件"""
        # 保存配置到文件
        self.save_auto_start_config()

        # 如果正在倒计时，重新开始
        if self.auto_start_enabled.get() and self.countdown_seconds > 0:
            if self.countdown_timer:
                self.root.after_cancel(self.countdown_timer)
            self.countdown_seconds = self.auto_start_countdown.get()
            self.add_log(f"倒计时时间已更改为 {self.countdown_seconds} 秒")
            self.start_countdown()

    def save_auto_start_config(self):
        """保存自动启动配置到文件"""
        try:
            # 加载当前配置
            config = config_manager.load_app_config()

            # 更新自动启动配置
            config['auto_start_enabled'] = self.auto_start_enabled.get()
            config['auto_start_countdown'] = self.auto_start_countdown.get()

            # 保存配置
            config_manager.save_app_config(config)

            self.add_log(f"自动启动配置已保存: 启用={self.auto_start_enabled.get()}, 倒计时={self.auto_start_countdown.get()}秒")
        except Exception as e:
            self.add_log(f"保存自动启动配置失败: {str(e)}")

    def create_control_panel(self):
        """创建顶部控制面板"""
        control_frame = ttk.LabelFrame(self.main_frame, text="控制面板", padding="5")
        control_frame.pack(fill=tk.X, pady=3)

        # 第一行：服务控制按钮（移到最上方）
        row1 = ttk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=2)

        # 服务控制区域
        service_frame = ttk.Frame(row1)
        service_frame.pack(side=tk.LEFT, padx=2)

        self.start_button = ttk.Button(service_frame, text="启动服务", command=self.start_api_service)
        self.start_button.pack(side=tk.LEFT, padx=3)
        self.stop_button = ttk.Button(service_frame, text="停止服务", command=self.stop_api_service)
        self.stop_button.pack(side=tk.LEFT, padx=3)
        self.config_button = ttk.Button(service_frame, text="插件配置", command=self.show_config_dialog)
        self.config_button.pack(side=tk.LEFT, padx=3)
        self.reload_button = ttk.Button(service_frame, text="重新配置", command=self.reload_config)
        self.reload_button.pack(side=tk.LEFT, padx=3)

        # 第二行：库选择
        row2 = ttk.Frame(control_frame)
        row2.pack(fill=tk.X, pady=2)

        # 库选择区域
        lib_frame = ttk.Frame(row2)
        lib_frame.pack(side=tk.LEFT, padx=2)

        ttk.Label(lib_frame, text="微信库选择:").pack(side=tk.LEFT, padx=5)
        self.lib_var = tk.StringVar(value="wxauto")
        self.wxauto_radio = ttk.Radiobutton(lib_frame, text="wxauto", variable=self.lib_var, value="wxauto",
                                            command=self.on_lib_change)
        self.wxauto_radio.pack(side=tk.LEFT, padx=5)
        self.wxautox_radio = ttk.Radiobutton(lib_frame, text="wxautox", variable=self.lib_var, value="wxautox",
                                             command=self.on_lib_change)
        self.wxautox_radio.pack(side=tk.LEFT, padx=5)

        # 初始化变量，但不在主界面显示
        self.port_var = tk.StringVar(value="5000")
        self.apikey_var = tk.StringVar(value="test-key-2")

        # 第三行：wxauto状态显示（移除API说明和查看日志按钮）
        row3 = ttk.Frame(control_frame)
        row3.pack(fill=tk.X, pady=5)

        # wxauto插件状态
        wxauto_frame = ttk.Frame(row3)
        wxauto_frame.pack(side=tk.LEFT, padx=5)  # 移除fill和expand，避免不必要的空白

        ttk.Label(wxauto_frame, text="wxauto状态:").pack(side=tk.LEFT, padx=5)
        self.wxauto_status = ttk.Label(wxauto_frame, text="检测中...", style="Bold.TLabel")
        self.wxauto_status.pack(side=tk.LEFT, padx=5)
        # 添加版本号显示
        self.wxauto_version = ttk.Label(wxauto_frame, text="", foreground="gray")
        self.wxauto_version.pack(side=tk.LEFT, padx=2)
        self.install_wxauto_button = ttk.Button(wxauto_frame, text="检查状态", command=self.check_wxauto_installation)
        self.install_wxauto_button.pack(side=tk.LEFT, padx=5)

        # 第四行：wxautox状态显示（单独一行）
        row4 = ttk.Frame(control_frame)
        row4.pack(fill=tk.X, pady=5)

        # wxautox插件状态
        wxautox_frame = ttk.Frame(row4)
        wxautox_frame.pack(side=tk.LEFT, padx=5)  # 移除fill和expand，避免不必要的空白

        ttk.Label(wxautox_frame, text="wxautox状态:").pack(side=tk.LEFT, padx=5)
        self.wxautox_status = ttk.Label(wxautox_frame, text="检测中...", style="Bold.TLabel")
        self.wxautox_status.pack(side=tk.LEFT, padx=5)
        # 添加版本号显示
        self.wxautox_version = ttk.Label(wxautox_frame, text="", foreground="gray")
        self.wxautox_version.pack(side=tk.LEFT, padx=2)
        # 使用ttk.Button与其他按钮保持一致的风格
        self.activate_wxautox_button = ttk.Button(
            wxautox_frame,
            text="激活wxautox",
            command=self.show_wxautox_activation
        )
        self.activate_wxautox_button.pack(side=tk.LEFT, padx=5)
        # 添加激活提示
        ttk.Label(wxautox_frame, text="请手动激活，重启软件生效", foreground="orange").pack(side=tk.LEFT, padx=5)


    def create_status_panel(self):
        """创建状态面板"""
        status_frame = ttk.LabelFrame(self.main_frame, text="服务状态", padding="5")
        status_frame.pack(fill=tk.X, pady=3)  # 改为fill=tk.X，不再expand=True，移除空白

        # 服务状态信息
        info_frame = ttk.Frame(status_frame)
        info_frame.pack(fill=tk.X, pady=5)

        # 第一行
        row1 = ttk.Frame(info_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="API服务状态:").grid(row=0, column=0, padx=(0,5), sticky=tk.W)
        self.api_status = ttk.Label(row1, text="未运行", style="Red.TLabel")
        self.api_status.grid(row=0, column=1, padx=(0,15), sticky=tk.W)

        ttk.Label(row1, text="监听地址:").grid(row=0, column=2, padx=(0,5), sticky=tk.W)
        self.api_address = ttk.Label(row1, text="--")
        self.api_address.grid(row=0, column=3, padx=(0,15), sticky=tk.W)

        ttk.Label(row1, text="当前库:").grid(row=0, column=4, padx=(0,5), sticky=tk.W)
        self.current_lib_label = ttk.Label(row1, text="wxauto", style="Bold.TLabel")
        self.current_lib_label.grid(row=0, column=5, padx=(0,5), sticky=tk.W)

        # 第二行
        row2 = ttk.Frame(info_frame)
        row2.pack(fill=tk.X, pady=2)

        ttk.Label(row2, text="CPU使用率:").grid(row=0, column=0, padx=(0,5), sticky=tk.W)
        self.cpu_usage = ttk.Label(row2, text="0%")
        self.cpu_usage.grid(row=0, column=1, padx=(0,15), sticky=tk.W)

        ttk.Label(row2, text="内存使用:").grid(row=0, column=2, padx=(0,5), sticky=tk.W)
        self.memory_usage = ttk.Label(row2, text="0 MB")
        self.memory_usage.grid(row=0, column=3, padx=(0,15), sticky=tk.W)

        ttk.Label(row2, text="运行时间:").grid(row=0, column=4, padx=(0,5), sticky=tk.W)
        self.uptime = ttk.Label(row2, text="00:00:00")
        self.uptime.grid(row=0, column=5, padx=(0,5), sticky=tk.W)

        # 第三行
        row3 = ttk.Frame(info_frame)
        row3.pack(fill=tk.X, pady=2)

        ttk.Label(row3, text="API请求数:").grid(row=0, column=0, padx=(0,5), sticky=tk.W)
        self.request_count = ttk.Label(row3, text="0", font=("TkDefaultFont", 10, "bold"))
        self.request_count.grid(row=0, column=1, padx=(0,15), sticky=tk.W)

        ttk.Label(row3, text="错误数:").grid(row=0, column=2, padx=(0,5), sticky=tk.W)
        self.error_count = ttk.Label(row3, text="0", font=("TkDefaultFont", 10, "bold"), foreground="red")
        self.error_count.grid(row=0, column=3, padx=(0,15), sticky=tk.W)

        ttk.Label(row3, text="微信连接:").grid(row=0, column=4, padx=(0,5), sticky=tk.W)
        self.wechat_status = ttk.Label(row3, text="未连接", style="Red.TLabel")
        self.wechat_status.grid(row=0, column=5, padx=(0,15), sticky=tk.W)

        # 添加微信窗口名称说明标签
        ttk.Label(row3, text="微信名称:").grid(row=0, column=6, padx=(0,5), sticky=tk.W)

        # 创建微信窗口名称标签（初始为空）
        self.wechat_window_name = ttk.Label(row3, text="", foreground="orange", font=("TkDefaultFont", 10, "bold"))
        self.wechat_window_name.grid(row=0, column=7, padx=(0,5), sticky=tk.W)

    def create_bottom_panel(self):
        """创建底部按钮面板"""
        bottom_frame = ttk.LabelFrame(self.main_frame, text="辅助功能", padding="2")  # 减少padding
        bottom_frame.pack(fill=tk.X, pady=0)  # 移除垂直间距

        # 底部按钮区域
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(side=tk.LEFT, padx=2)

        # API说明按钮（内嵌"必看"标识）
        self.api_doc_button = ttk.Button(button_frame, text="API说明 [必看]",
                                        command=self.show_api_documentation,
                                        width=12)  # 设置合理宽度避免文字挤压
        self.api_doc_button.pack(side=tk.LEFT, padx=3)

        # 查看日志按钮（增加间距）
        self.view_logs_button = ttk.Button(button_frame, text="查看日志", command=self.show_logs_page)
        self.view_logs_button.pack(side=tk.LEFT, padx=15)  # 增加左边距，拉开距离

        # 自动启动控制区域
        auto_start_frame = ttk.Frame(bottom_frame)
        auto_start_frame.pack(side=tk.RIGHT, padx=10)

        # 自动启动复选框
        self.auto_start_checkbox = ttk.Checkbutton(
            auto_start_frame,
            text="自动启动服务",
            variable=self.auto_start_enabled,
            command=self.on_auto_start_toggle
        )
        self.auto_start_checkbox.pack(side=tk.LEFT, padx=5)

        # 倒计时时间设置
        ttk.Label(auto_start_frame, text="倒计时:").pack(side=tk.LEFT, padx=(10, 2))
        self.countdown_spinbox = ttk.Spinbox(
            auto_start_frame,
            from_=1,
            to=30,
            width=5,
            textvariable=self.auto_start_countdown,
            command=self.on_countdown_change
        )
        self.countdown_spinbox.pack(side=tk.LEFT, padx=2)

        # 绑定键盘事件，当用户直接输入数字时也能保存配置
        self.countdown_spinbox.bind('<KeyRelease>', lambda e: self.root.after(500, self.on_countdown_change))
        self.countdown_spinbox.bind('<FocusOut>', lambda e: self.on_countdown_change())
        ttk.Label(auto_start_frame, text="秒").pack(side=tk.LEFT, padx=(2, 5))


    def adjust_window_size(self):
        """调整窗口大小以适应内容"""
        try:
            # 更新所有组件以确保正确计算大小
            self.root.update_idletasks()

            # 获取主框架的实际需要大小
            self.main_frame.update_idletasks()
            required_width = self.main_frame.winfo_reqwidth() + 30  # 减少边距
            required_height = self.main_frame.winfo_reqheight() + 50  # 减少边距

            # 设置更紧凑的尺寸范围
            min_width = 500  # 大幅减少最小宽度
            max_width = 700  # 减少最大宽度，使界面更紧凑
            min_height = 300
            max_height = 500

            # 限制窗口大小在合理范围内
            final_width = max(min_width, min(required_width, max_width))
            final_height = max(min_height, min(required_height, max_height))

            # 获取屏幕尺寸重新计算居中位置
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            # 计算居中位置
            center_x = int(screen_width / 2 - final_width / 2)
            center_y = int(screen_height / 2 - final_height / 2)

            # 设置窗口大小和位置
            self.root.geometry(f"{final_width}x{final_height}+{center_x}+{center_y}")

            # 禁止用户调整窗口大小，保持紧凑
            self.root.resizable(False, False)

        except Exception as e:
            # 如果自动调整失败，使用紧凑的默认尺寸
            self.root.geometry("600x400+100+100")
            self.root.resizable(False, False)
    def get_package_version(self, package_name):
        """获取包的版本号"""
        try:
            # 检查是否在打包环境中
            is_frozen = getattr(sys, 'frozen', False)

            if is_frozen:
                # 在打包环境中，尝试直接从模块获取版本信息
                try:
                    if package_name == 'wxauto':
                        import wxauto
                        # 尝试获取版本号的多种方式
                        version = getattr(wxauto, '__version__', None) or \
                                 getattr(wxauto, 'VERSION', None) or \
                                 getattr(wxauto, 'version', None)
                        if version:
                            return f"v{version}"
                        else:
                            return "v39.1.8"  # 已知的稳定版本
                    elif package_name == 'wxautox':
                        import wxautox
                        # 尝试获取版本号的多种方式
                        version = getattr(wxautox, '__version__', None) or \
                                 getattr(wxautox, 'VERSION', None) or \
                                 getattr(wxautox, 'version', None)
                        if version:
                            return f"v{version}"
                        else:
                            return "v39.1.36"  # 已知的稳定版本
                    return ""
                except ImportError:
                    return ""
            else:
                # 在开发环境中，使用pip show命令
                import subprocess
                result = subprocess.run(['pip', 'show', package_name],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            version = line.split(':', 1)[1].strip()
                            return f"v{version}"
                return ""
        except Exception:
            return ""








    def setup_logging(self):
        """设置日志处理"""
        # 确保日志目录存在
        config_manager.ensure_dirs()

        # 获取当前库名称
        try:
            config = config_manager.load_app_config()
            current_lib = config.get('wechat_lib', 'wxauto')
            logger.set_lib_name(current_lib)
        except Exception as e:
            logger.set_lib_name('wxauto')  # 默认使用wxauto

        # 记录日志系统初始化完成
        self.add_log("统一日志系统已初始化")



    def check_wxauto_status(self):
        """检查wxauto库的安装状态"""
        try:
            # 在打包环境中，避免直接导入库，防止冲突
            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                # 在打包环境中，简单检查包是否存在
                try:
                    import importlib.util
                    spec = importlib.util.find_spec('wxauto')
                    if spec is not None:
                        self.wxauto_status.config(text="已打包", style="Green.TLabel")
                        # 获取并显示版本号
                        version = self.get_package_version('wxauto')
                        self.wxauto_version.config(text=version)
                        return True
                    else:
                        self.wxauto_status.config(text="未打包", style="Red.TLabel")
                        self.wxauto_version.config(text="")
                        return False
                except Exception:
                    self.wxauto_status.config(text="已打包", style="Green.TLabel")
                    # 尝试获取版本号
                    version = self.get_package_version('wxauto')
                    self.wxauto_version.config(text=version)
                    return True  # 假设可用，避免阻止启动
            else:
                # 在开发环境中，尝试导入pip安装的wxauto包
                import wxauto
                self.wxauto_status.config(text="已安装", style="Green.TLabel")
                # 获取并显示版本号
                version = self.get_package_version('wxauto')
                self.wxauto_version.config(text=version)
                return True
        except ImportError as e:
            self.wxauto_status.config(text="未安装", style="Red.TLabel")
            self.wxauto_version.config(text="")
            self.add_log(f"无法导入wxauto库: {str(e)}")
            return False
        except Exception as e:
            self.wxauto_status.config(text="检查失败", style="Red.TLabel")
            self.wxauto_version.config(text="")
            self.add_log(f"检查wxauto状态时出现未知错误: {str(e)}")
            return False

    def check_wxautox_status(self):
        """检查wxautox库的可用状态（能否成功导入）"""
        try:
            # 初始化日志标志
            if not hasattr(self, '_wxautox_status_logged'):
                self._wxautox_status_logged = {}

            # 在打包环境中，避免使用subprocess检查，防止冲突
            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                # 在打包环境中，简单检查包是否存在
                try:
                    import importlib.util
                    spec = importlib.util.find_spec('wxautox')
                    if spec is not None:
                        # 检查状态是否已经更新，避免重复日志
                        current_status = self.wxautox_status.cget("text")
                        if current_status != "已打包":
                            self.wxautox_status.config(text="已打包", style="Green.TLabel")
                            # 获取并显示版本号
                            version = self.get_package_version('wxautox')
                            self.wxautox_version.config(text=version)
                            if not self._wxautox_status_logged.get('packed_available', False):
                                self.add_log("wxautox库在打包环境中可用")
                                self._wxautox_status_logged['packed_available'] = True
                        return True
                    else:
                        current_status = self.wxautox_status.cget("text")
                        if current_status != "未打包":
                            self.wxautox_status.config(text="未打包", style="Red.TLabel")
                            self.wxautox_version.config(text="")
                            if hasattr(self, 'wxautox_activation_status'):
                                self.wxautox_activation_status.config(text="未打包", style="Red.TLabel")
                            # 重置日志标志
                            self._wxautox_status_logged = {}
                        return False
                except Exception:
                    # 检查状态是否已经更新，避免重复日志
                    current_status = self.wxautox_status.cget("text")
                    if current_status != "已打包":
                        self.wxautox_status.config(text="已打包", style="Green.TLabel")
                        # 获取并显示版本号
                        version = self.get_package_version('wxautox')
                        self.wxautox_version.config(text=version)
                        if not self._wxautox_status_logged.get('packed_assumed', False):
                            self.add_log("wxautox库在打包环境中假设可用")
                            self._wxautox_status_logged['packed_assumed'] = True
                    return True  # 假设可用，避免阻止启动
            else:
                # 在开发环境中，使用subprocess来检查wxautox，避免影响主进程
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-c", "import wxautox; print('wxautox_available')"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=5  # 减少超时时间
                )

                if result.returncode == 0 and "wxautox_available" in result.stdout:
                    # 检查状态是否已经更新，避免重复日志
                    current_status = self.wxautox_status.cget("text")
                    if current_status != "可用":
                        self.wxautox_status.config(text="可用", style="Green.TLabel")
                        # 获取并显示版本号
                        version = self.get_package_version('wxautox')
                        self.wxautox_version.config(text=version)
                        if not self._wxautox_status_logged.get('dev_available', False):
                            self.add_log("wxautox库检测为可用")
                            self._wxautox_status_logged['dev_available'] = True
                    return True
                else:
                    current_status = self.wxautox_status.cget("text")
                    if current_status != "不可用":
                        self.wxautox_status.config(text="不可用", style="Red.TLabel")
                        self.wxautox_version.config(text="")
                        # 重置日志标志
                        self._wxautox_status_logged = {}
                    return False
        except subprocess.TimeoutExpired:
            self.wxautox_status.config(text="检查超时", style="Red.TLabel")
            self.wxautox_version.config(text="")
            if hasattr(self, 'wxautox_activation_status'):
                self.wxautox_activation_status.config(text="未知", style="Red.TLabel")
            return False
        except KeyboardInterrupt:
            # 处理用户中断
            self.wxautox_status.config(text="检查中断", style="Red.TLabel")
            self.wxautox_version.config(text="")
            if hasattr(self, 'wxautox_activation_status'):
                self.wxautox_activation_status.config(text="未知", style="Red.TLabel")
            return False
        except Exception as e:
            self.wxautox_status.config(text="检查失败", style="Red.TLabel")
            self.wxautox_version.config(text="")
            # 只在调试模式下记录详细错误
            if hasattr(self, '_debug_mode') and self._debug_mode:
                self.add_log(f"检查wxautox状态时出错: {str(e)}")
            return False







    def check_wxauto_installation(self):
        """检查wxauto安装状态并提供安装选项"""
        try:
            # 使用统一的库检测器
            from app.wechat_lib_detector import detector

            available, details = detector.detect_wxauto()
            if available:
                self.add_log(f"wxauto库检测成功: {details}")
                messagebox.showinfo("检查结果", f"wxauto库已正确安装并可用！\n\n详细信息: {details}\n\n如果遇到问题，可以尝试重新安装：\npip install --upgrade wxauto")
            else:
                self.add_log(f"wxauto库检测失败: {details}")
                result = messagebox.askyesno("wxauto不可用",
                                           f"wxauto库不可用。\n\n详细信息: {details}\n\n是否要安装wxauto库？\n\n注意：这将使用pip安装wxauto库。")
                if result:
                    self.install_wxauto()
        except Exception as e:
            self.add_log(f"检查wxauto状态时出错: {str(e)}")
            messagebox.showerror("检查错误", f"检查wxauto状态时出错:\n{str(e)}")

    def install_wxauto(self):
        """安装wxauto库"""
        # 禁用按钮，避免重复点击
        self.install_wxauto_button.config(state=tk.DISABLED)
        self.wxauto_status.config(text="安装中...", style="Bold.TLabel")
        self.add_log("正在安装wxauto库...")

        def install_thread():
            try:
                # 使用pip安装wxauto
                import subprocess
                import sys

                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "wxauto"],
                    capture_output=True,
                    text=True,
                    check=True
                )

                if result.returncode == 0:
                    self.root.after(0, lambda: self.add_log("wxauto库安装成功"))
                    self.root.after(0, lambda: self.check_wxauto_status())
                    self.root.after(0, lambda: messagebox.showinfo("安装成功", "wxauto库安装成功"))
                else:
                    self.root.after(0, lambda: self.add_log(f"wxauto库安装失败: {result.stderr}"))
                    self.root.after(0, lambda: self.wxauto_status.config(text="安装失败", style="Red.TLabel"))
                    self.root.after(0, lambda: messagebox.showerror("安装失败", f"wxauto库安装失败:\n{result.stderr}"))

            except subprocess.CalledProcessError as e:
                self.root.after(0, lambda: self.add_log(f"wxauto库安装过程出错: {e.stderr}"))
                self.root.after(0, lambda: self.wxauto_status.config(text="安装失败", style="Red.TLabel"))
                self.root.after(0, lambda: messagebox.showerror("安装失败", f"wxauto库安装过程出错:\n{e.stderr}"))
            except Exception as e:
                self.root.after(0, lambda: self.add_log(f"安装过程出错: {str(e)}"))
                self.root.after(0, lambda: self.wxauto_status.config(text="安装失败", style="Red.TLabel"))
                self.root.after(0, lambda: messagebox.showerror("安装失败", f"安装wxauto库失败: {str(e)}"))
            finally:
                # 恢复按钮状态
                self.root.after(0, lambda: self.install_wxauto_button.config(state=tk.NORMAL))

        # 在新线程中执行安装
        threading.Thread(target=install_thread, daemon=True).start()

    def show_wxautox_activation(self):
        """显示wxautox激活对话框"""
        # 创建激活对话框
        activation_dialog = tk.Toplevel(self.root)
        activation_dialog.title("wxautox激活")
        activation_dialog.geometry("450x300")
        activation_dialog.resizable(False, False)
        activation_dialog.transient(self.root)
        activation_dialog.grab_set()

        # 居中显示
        self.center_window(activation_dialog)

        # 创建主框架
        main_frame = ttk.Frame(activation_dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 添加标题
        title_label = ttk.Label(main_frame, text="wxautox激活", font=("TkDefaultFont", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # 添加说明
        import sys
        is_frozen = getattr(sys, 'frozen', False)

        if is_frozen:
            info_text = """请输入您的wxautox激活码。激活码将被保存。

✅ 打包环境激活支持：
- 当前版本支持在打包环境中直接激活
- 点击激活按钮即可完成激活
- 激活码将被安全保存在本地配置文件中
- 激活成功后无需重复输入"""
        else:
            info_text = """请输入您的wxautox激活码。激活码将被保存，
在每次启动服务时自动激活wxautox。

注意：
- 请确保已安装wxautox库 (pip install wxautox)
- 激活码将安全保存在本地配置文件中
- 激活成功后无需重复输入"""

        info_label = ttk.Label(main_frame, text=info_text, wraplength=400, justify="left")
        info_label.pack(pady=(0, 15))

        # 激活码输入框
        code_frame = ttk.Frame(main_frame)
        code_frame.pack(fill=tk.X, pady=10)

        ttk.Label(code_frame, text="激活码:").pack(side=tk.LEFT, padx=(0, 10))

        # 创建激活码输入变量
        activation_code_var = tk.StringVar()

        # 加载已保存的激活码
        try:
            from app.wxautox_activation import get_activation_code
            saved_code = get_activation_code()
            if saved_code:
                activation_code_var.set(saved_code)
        except Exception as e:
            self.add_log(f"加载已保存的激活码失败: {str(e)}")

        code_entry = ttk.Entry(code_frame, textvariable=activation_code_var, width=30, show="*")
        code_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 显示/隐藏激活码按钮
        show_code_var = tk.BooleanVar()
        def toggle_code_visibility():
            if show_code_var.get():
                code_entry.config(show="")
            else:
                code_entry.config(show="*")

        show_button = ttk.Checkbutton(code_frame, text="显示", variable=show_code_var, command=toggle_code_visibility)
        show_button.pack(side=tk.LEFT, padx=(10, 0))

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # 激活按钮
        def activate_action():
            code = activation_code_var.get().strip()
            if not code:
                messagebox.showerror("错误", "请输入激活码")
                return

            # 禁用按钮，显示进度
            activate_button.config(state=tk.DISABLED, text="激活中...")
            cancel_button.config(state=tk.DISABLED)

            def activate_thread():
                try:
                    from app.wxautox_activation import activate_wxautox, save_activation_code

                    # 保存激活码
                    save_activation_code(code)

                    # 执行激活
                    success, message, output = activate_wxautox(code)

                    # 在主线程中更新UI
                    if success:
                        self.root.after(0, lambda: self.add_log(f"wxautox激活成功: {message}"))
                        self.root.after(0, lambda: messagebox.showinfo("激活成功", "wxautox激活成功！"))
                        self.root.after(0, lambda: activation_dialog.destroy())
                    else:
                        self.root.after(0, lambda: self.add_log(f"wxautox激活失败: {message}"))
                        self.root.after(0, lambda: messagebox.showerror("激活失败", f"wxautox激活失败:\n{message}"))

                except Exception as e:
                    self.root.after(0, lambda: self.add_log(f"wxautox激活过程出错: {str(e)}"))
                    self.root.after(0, lambda: messagebox.showerror("激活错误", f"激活过程出错:\n{str(e)}"))
                finally:
                    # 恢复按钮状态
                    self.root.after(0, lambda: activate_button.config(state=tk.NORMAL, text="激活"))
                    self.root.after(0, lambda: cancel_button.config(state=tk.NORMAL))

            # 在新线程中执行激活
            threading.Thread(target=activate_thread, daemon=True).start()

        activate_button = ttk.Button(button_frame, text="激活", command=activate_action)
        activate_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=activation_dialog.destroy)
        cancel_button.pack(side=tk.RIGHT)

        # 焦点设置到输入框
        code_entry.focus_set()



    def show_api_documentation(self):
        """打开API文档页面"""
        import webbrowser
        try:
            # 获取当前配置的端口号
            config = config_manager.load_app_config()
            port = config.get('port', 5000)

            # 构建API文档URL
            api_docs_url = f"http://localhost:{port}/api-docs"

            # 在默认浏览器中打开API文档
            webbrowser.open(api_docs_url)
            self.add_log(f"已在浏览器中打开API文档: {api_docs_url}")

        except Exception as e:
            self.add_log(f"打开API文档失败: {str(e)}")
            # 如果打开失败，显示错误信息并提供手动访问的URL
            messagebox.showinfo("API文档",
                f"无法自动打开浏览器，请手动访问:\nhttp://localhost:5000/api-docs\n\n错误信息: {str(e)}")

    def show_logs_page(self):
        """打开日志查看页面"""
        import webbrowser
        try:
            # 获取当前配置的端口号
            config = config_manager.load_app_config()
            port = config.get('port', 5000)

            # 构建日志查看URL
            logs_url = f"http://localhost:{port}/logs"

            # 在默认浏览器中打开日志页面
            webbrowser.open(logs_url)
            self.add_log(f"已在浏览器中打开日志查看页面: {logs_url}")

        except Exception as e:
            self.add_log(f"打开日志页面失败: {str(e)}")
            # 如果打开失败，显示错误信息并提供手动访问的URL
            messagebox.showinfo("日志查看",
                f"无法自动打开浏览器，请手动访问:\nhttp://localhost:5000/logs\n\n错误信息: {str(e)}")

    def center_window(self, window):
        """将窗口居中显示"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def on_lib_change(self):
        """处理库选择变更"""
        selected_lib = self.lib_var.get()
        self.add_log(f"库选择变更: {selected_lib}")

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
            self.add_log(f"正在加载配置文件...")
            config = config_manager.load_app_config()
            self.add_log(f"当前配置: {config}")

            # 更新库配置
            old_lib = config.get('wechat_lib', 'wxauto')
            config['wechat_lib'] = selected_lib
            self.add_log(f"更新库配置: {old_lib} -> {selected_lib}")

            # 保存配置
            self.add_log(f"正在保存配置文件...")
            config_manager.save_app_config(config)

            # 验证配置是否成功保存
            try:
                new_config = config_manager.load_app_config()
                saved_lib = new_config.get('wechat_lib', 'wxauto')
                if saved_lib != selected_lib:
                    self.add_log(f"警告：配置保存后验证失败，期望值: {selected_lib}，实际值: {saved_lib}")
                    messagebox.showwarning("配置验证", f"配置可能未正确保存，请检查配置文件权限")
                else:
                    self.add_log(f"配置保存成功并验证通过: {saved_lib}")
            except Exception as ve:
                self.add_log(f"配置验证失败: {str(ve)}")

            # .env文件已弃用，现在只使用JSON配置文件
            self.add_log("配置已保存到JSON配置文件（.env文件已弃用）")

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

        # 如果使用wxautox，检查是否可用（不执行激活）
        if selected_lib == "wxautox":
            self.add_log("检查wxautox可用性...")
            if not self.check_wxautox_status():
                self.add_log("wxautox不可用，请先手动激活")
                if not messagebox.askyesno("wxautox不可用", "wxautox库不可用，可能需要激活。\n\n是否切换到wxauto库继续启动服务？"):
                    return
                else:
                    # 切换到wxauto库
                    self.lib_var.set("wxauto")
                    self.current_lib = "wxauto"
                    selected_lib = "wxauto"
                    self.add_log("已切换到wxauto库")
            else:
                self.add_log("wxautox可用，继续启动服务")

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
                # 注意：main.py 现在位于项目根目录，而不是app目录
                # 获取项目根目录
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                main_py_path = os.path.join(app_dir, "main.py")
                cmd = [sys.executable, main_py_path, "--service", "api"]

                # 添加调试参数，以获取更详细的日志
                if os.environ.get("WXAUTO_DEBUG") == "1":
                    cmd.append("--debug")

            # 记录启动命令
            self.add_log(f"启动命令: {' '.join(cmd)}")

            # 设置环境变量，确保子进程使用UTF-8编码
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSSTDIO'] = '0'  # 禁用旧版Windows标准IO处理

            # 在Windows系统上，设置控制台代码页为UTF-8
            if sys.platform == 'win32':
                # 尝试设置控制台代码页为65001 (UTF-8)
                try:
                    subprocess.run(['chcp', '65001'], shell=True, check=False)
                    self.add_log("已设置控制台代码页为UTF-8 (65001)")
                except Exception as e:
                    self.add_log(f"设置控制台代码页失败: {str(e)}")

            # 使用二进制模式创建进程，避免编码问题
            API_PROCESS = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=False,  # 使用二进制模式
                universal_newlines=False,  # 不使用通用换行符
                env=env  # 使用修改后的环境变量
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
            self.root.after(1000, lambda: threading.Thread(target=self._initialize_wechat_thread, args=(port,),
                                                           daemon=True).start())

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

        try:
            # 使用二进制模式读取进程输出
            for line_bytes in iter(API_PROCESS.stdout.readline, b''):
                if line_bytes:
                    try:
                        # 尝试使用不同的编码解码二进制数据
                        line_content = None
                        decode_success = False

                        # 尝试使用不同的编码解码
                        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']:
                            try:
                                decoded = line_bytes.decode(encoding)
                                if '�' not in decoded:
                                    line_content = decoded.strip()
                                    # print(f"成功使用 {encoding} 编码解码: {line_content}")  # 注释掉，避免stdout问题
                                    decode_success = True
                                    break
                            except UnicodeDecodeError:
                                continue

                        # 如果所有编码都失败，使用utf-8并替换无法解码的字符
                        if not decode_success:
                            line_content = line_bytes.decode('utf-8', errors='replace').strip()
                            # print(f"使用替换模式解码: {line_content}")  # 注释掉，避免stdout问题

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

                        # 使用统一日志管理器记录进程输出
                        self.add_log(line_content)
                    except UnicodeDecodeError as e:
                        # 如果遇到解码错误，记录错误信息
                        self.add_log(f"读取进程输出时遇到编码错误: {str(e)}")
                    except Exception as e:
                        # 捕获其他可能的异常
                        self.add_log(f"处理进程输出时出错: {str(e)}")

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
        except Exception as e:
            # 捕获读取进程输出时的异常
            self.add_log(f"读取进程输出时出错: {str(e)}")
            # 如果发生异常，尝试更新状态
            self.root.after(0, self.update_status_stopped)

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
        # 居中显示
        self.center_window(config_dialog)
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

        return "test-key-2"  # 默认API密钥

    def add_log(self, message):
        """添加日志到文件"""
        # 获取当前库名称
        lib_name = getattr(self, 'current_lib', 'wxauto')

        # 使用统一日志管理器记录日志到文件
        unified_logger.info(lib_name, message)

        # 检查日志中是否包含窗口名称信息，更新UI状态
        if "初始化成功，获取到已登录窗口：" in message:
            try:
                # 提取窗口名称
                window_name = message.split("初始化成功，获取到已登录窗口：")[1].strip()
                if window_name and hasattr(self, 'wechat_window_name'):
                    # 更新窗口名称标签
                    self.wechat_window_name.config(text=window_name, foreground="orange")
            except Exception:
                pass

    def check_status(self):
        """定时检查状态"""
        # 检查是否正在关闭
        if getattr(self, '_ui_closing', False):
            return

        # 使用静态计数器来控制不同检查的频率
        if not hasattr(self, '_check_counter'):
            self._check_counter = 0
        self._check_counter += 1

        # 每30秒检查一次插件状态，大幅减少检查频率
        if self._check_counter % 30 == 0:
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

        # 继续定时检查，使用1秒间隔（如果没有关闭）
        if not getattr(self, '_ui_closing', False):
            self._status_timer_id = self.root.after(1000, self.check_status)

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
                        self.root.after(0, lambda wn=window_name: self.wechat_window_name.config(text=wn,
                                                                                                 foreground="orange"))
                        # self.add_log(f"已连接到微信窗口: {window_name}")
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
                        self.root.after(0,
                                        lambda: self.wechat_window_name.config(text=window_name, foreground="orange"))
                        # 移除日志记录
                    elif self.wechat_window_name.cget("text") == "" or self.wechat_window_name.cget(
                            "text") == "获取中...":
                        # 如果窗口名称为空且当前显示为空或"获取中..."，才设置为"获取中..."
                        # 这样可以避免覆盖之前成功获取的名称
                        self.root.after(0,
                                        lambda: self.wechat_window_name.config(text="获取中...", foreground="orange"))

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
                        self.root.after(0,
                                        lambda: self.wechat_window_name.config(text=window_name, foreground="orange"))
                        # 移除日志记录
                    elif self.wechat_window_name.cget("text") == "" or self.wechat_window_name.cget(
                            "text") == "获取中...":
                        # 如果窗口名称为空且当前显示为空或"获取中..."，才设置为"获取中..."
                        # 这样可以避免覆盖之前成功获取的名称
                        self.root.after(0,
                                        lambda: self.wechat_window_name.config(text="获取中...", foreground="orange"))

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

            # 设置自动启动配置
            auto_start_enabled = config.get('auto_start_enabled', False)
            auto_start_countdown = config.get('auto_start_countdown', 5)
            self.auto_start_enabled.set(auto_start_enabled)
            self.auto_start_countdown.set(auto_start_countdown)
            self.add_log(f"自动启动配置: 启用={auto_start_enabled}, 倒计时={auto_start_countdown}秒")

            self.add_log("从配置文件加载配置成功")
        except Exception as e:
            self.add_log(f"从配置文件加载配置失败: {str(e)}")

            # 如果配置文件加载失败，使用默认值
            self.current_lib = 'wxauto'
            self.lib_var.set('wxauto')
            self.current_lib_label.config(text='wxauto')

            self.current_port = 5000
            self.port_var.set('5000')

            self.apikey_var.set('test-key-2')

        # 初始化按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        # 检查服务是否已在运行
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe' and proc.info.get('cmdline') and any(
                        'run.py' in cmd for cmd in proc.info['cmdline'] if cmd):
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
            # 更新启动按钮文本显示倒计时
            self.start_button.config(text=f"启动服务 ({self.countdown_seconds})")

            # 根据剩余秒数显示不同的提示
            if self.countdown_seconds == self.auto_start_countdown.get():
                self.add_log(f"【自动启动】{self.countdown_seconds} 秒后启动服务...")
            elif self.countdown_seconds == 3:
                self.add_log("【自动启动】3 秒后启动服务...")
            elif self.countdown_seconds == 2:
                self.add_log("【自动启动】2 秒后启动服务...")
            elif self.countdown_seconds == 1:
                self.add_log("【自动启动】1 秒后启动服务...")

            self.countdown_seconds -= 1
            self.countdown_timer = self.root.after(1000, self.start_countdown)
        else:
            # 恢复按钮文本
            self.start_button.config(text="启动服务")
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
        # 设置关闭标志，停止定时器
        self._ui_closing = True

        # 取消倒计时定时器
        if self.countdown_timer:
            try:
                self.root.after_cancel(self.countdown_timer)
                self.countdown_timer = None
            except:
                pass

        # 取消状态更新定时器
        if hasattr(self, '_status_timer_id'):
            try:
                self.root.after_cancel(self._status_timer_id)
            except:
                pass

        # 关闭统一日志管理器
        try:
            from app.unified_logger import unified_logger
            unified_logger.shutdown()
        except:
            pass

        if self.api_running:
            if messagebox.askyesno("确认", "API服务正在运行，是否关闭服务并退出？"):
                self.stop_api_service()
                self.root.destroy()
        else:
            self.root.destroy()


# 主函数
def main():
    """主函数，启动UI界面"""
    try:
        # 检查tkinter是否可用
        try:
            import tkinter as tk
            from tkinter import ttk, messagebox
            logger.info("tkinter模块导入成功")
        except ImportError as e:
            error_msg = f"无法导入tkinter模块: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            return

        # 创建根窗口
        try:
            root = tk.Tk()
            logger.info("tkinter根窗口创建成功")
        except Exception as e:
            error_msg = f"无法创建tkinter根窗口: {str(e)}"
            logger.error(error_msg)
            logger.error(f"详细错误: {traceback.format_exc()}")
            print(error_msg)
            return

        # 设置窗口属性
        try:
            root.title("wxauto_http_api 管理界面")
            root.geometry("1000x700")
            root.minsize(800, 600)
            logger.info("窗口属性设置成功")
        except Exception as e:
            logger.warning(f"设置窗口属性时出错: {str(e)}")

        # 创建应用实例
        try:
            app = WxAutoHttpUI(root)
            logger.info("应用实例创建成功")
        except Exception as e:
            error_msg = f"创建应用实例失败: {str(e)}"
            logger.error(error_msg)
            logger.error(f"详细错误: {traceback.format_exc()}")

            # 显示错误对话框
            try:
                messagebox.showerror("初始化错误", f"{error_msg}\n\n程序将退出")
            except:
                pass

            try:
                root.destroy()
            except:
                pass

            return

        # 启动主循环
        try:
            logger.info("开始启动UI主循环")
            root.mainloop()
            logger.info("UI主循环已结束")
        except Exception as e:
            error_msg = f"UI主循环出错: {str(e)}"
            logger.error(error_msg)
            logger.error(f"详细错误: {traceback.format_exc()}")

            # 尝试显示错误对话框
            try:
                messagebox.showerror("运行时错误", f"{error_msg}")
            except:
                pass

    except Exception as e:
        error_msg = f"主函数发生未知错误: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误: {traceback.format_exc()}")
        print(error_msg)

        # 在打包环境中，尝试显示错误对话框
        if getattr(sys, 'frozen', False):
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("严重错误", f"{error_msg}\n\n程序无法继续运行")
                root.destroy()
            except:
                pass


if __name__ == "__main__":
    # 确保当前目录在Python路径中
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    try:
        # 导入项目模块
        from app.unified_logger import logger

        # 启动UI
        main()
    except ImportError as e:
        # print(f"导入模块失败: {e}")  # 注释掉，避免stdout问题
        # print("请使用 start_ui.py 启动UI")  # 注释掉，避免stdout问题
        pass
