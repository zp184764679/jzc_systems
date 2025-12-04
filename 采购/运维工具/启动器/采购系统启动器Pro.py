"""
采购系统 - 超详细启动器 Pro Max
特性：
- 🚫 无CMD窗口，完全GUI化
- 📊 实时详细日志和状态监控
- 🔍 详细的错误诊断和提示
- 🎨 美观的现代化界面
- 📈 启动进度和性能监控
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import os
import sys
import threading
import time
import psutil
import socket
import json
from datetime import datetime
from pathlib import Path

class UltraDetailedServiceLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("采购系统启动器 Pro Max - v3.0")
        self.root.geometry("1200x850")
        self.root.resizable(True, True)

        # 设置主题色
        self.colors = {
            'primary': '#2c3e50',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'info': '#3498db',
            'dark': '#1e1e1e',
            'light': '#ecf0f1',
            'backend': '#3498db',
            'frontend': '#2ecc71',
            'celery': '#e67e22',
            'redis': '#e74c3c',
            'mysql': '#f39c12'
        }

        # 服务进程字典
        self.processes = {
            'backend': None,
            'frontend': None,
            'celery': None,
            'redis': None,
            'mysql': None
        }

        # 服务状态缓存
        self.service_status = {}

        # 服务配置
        self.service_config = {
            'mysql': {
                'name': '🗄️ MySQL 数据库',
                'port': 3306,
                'process_names': ['mysqld.exe', 'mysqld'],
                'cmd_pattern': 'mysql',
                'color': self.colors['mysql'],
                'priority': 1,
                'startup_time': 3,
                'description': '核心数据库服务，存储所有业务数据',
                'health_check': self.check_mysql_health
            },
            'redis': {
                'name': '💾 Redis 缓存',
                'port': 6379,
                'process_names': ['redis-server.exe', 'redis-server'],
                'cmd_pattern': 'redis',
                'color': self.colors['redis'],
                'priority': 2,
                'startup_time': 2,
                'description': 'Celery任务队列和缓存服务',
                'health_check': self.check_redis_health
            },
            'backend': {
                'name': '🔧 后端服务 Flask',
                'port': 5001,
                'process_names': ['python.exe', 'python'],
                'cmd_pattern': 'app.py',
                'color': self.colors['backend'],
                'priority': 3,
                'startup_time': 5,
                'description': '提供REST API接口和业务逻辑',
                'health_check': self.check_backend_health
            },
            'celery': {
                'name': '⚙️ Celery 任务队列',
                'port': None,
                'process_names': ['python.exe', 'python'],
                'cmd_pattern': 'start_celery.py',
                'color': self.colors['celery'],
                'priority': 4,
                'startup_time': 5,
                'description': '异步任务处理：RFQ发送、AI分类等',
                'health_check': self.check_celery_health
            },
            'frontend': {
                'name': '🌐 前端服务 React',
                'port': 3000,
                'process_names': ['node.exe', 'node'],
                'cmd_pattern': 'vite',
                'color': self.colors['frontend'],
                'priority': 5,
                'startup_time': 8,
                'description': 'React前端界面服务（Vite开发服务器）',
                'health_check': self.check_frontend_health
            }
        }

        # 项目路径
        self.project_root = Path(r"C:\Users\Admin\Desktop\采购")
        self.backend_path = self.project_root / "backend"
        self.frontend_path = self.project_root / "frontend"

        # 日志缓冲
        self.log_buffer = []
        self.max_log_buffer = 1000

        # 创建界面
        self.create_modern_ui()

        # 启动状态监控
        self.monitor_services()

        # 首次检测
        self.detailed_check_all_services()

        # 显示欢迎信息
        self.show_welcome_message()

    def create_modern_ui(self):
        """创建现代化界面"""
        # ==================== 顶部标题栏 ====================
        title_frame = tk.Frame(self.root, bg=self.colors['primary'], height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🚀 采购系统启动器 Pro Max",
            font=("Microsoft YaHei UI", 20, "bold"),
            bg=self.colors['primary'],
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=30, pady=20)

        version_label = tk.Label(
            title_frame,
            text="v3.0 Ultra",
            font=("Consolas", 10),
            bg=self.colors['primary'],
            fg="#95a5a6"
        )
        version_label.pack(side=tk.LEFT, pady=20)

        # 系统信息按钮
        info_btn = tk.Button(
            title_frame,
            text="ℹ️ 系统信息",
            font=("Microsoft YaHei UI", 10),
            bg=self.colors['info'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_system_info
        )
        info_btn.pack(side=tk.RIGHT, padx=30, pady=20)

        # ==================== 主内容区 ====================
        main_frame = tk.Frame(self.root, bg=self.colors['light'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 左侧服务控制面板
        left_panel = tk.Frame(main_frame, bg="white", relief=tk.RAISED, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.create_service_control_panel(left_panel)

        # 右侧日志面板
        right_panel = tk.Frame(main_frame, bg="white", relief=tk.RAISED, bd=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_log_panel(right_panel)

        # ==================== 底部状态栏 ====================
        self.create_status_bar()

    def create_service_control_panel(self, parent):
        """创建服务控制面板"""
        # 标题
        header = tk.Label(
            parent,
            text="🎛️ 服务控制中心",
            font=("Microsoft YaHei UI", 14, "bold"),
            bg="white",
            fg=self.colors['primary']
        )
        header.pack(pady=15, padx=15, anchor="w")

        # 服务列表
        services_frame = tk.Frame(parent, bg="white")
        services_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.service_widgets = {}

        for service_key in ['mysql', 'redis', 'backend', 'celery', 'frontend']:
            config = self.service_config[service_key]
            self.create_service_card(services_frame, service_key, config)

        # 批量操作区域
        self.create_batch_operations(parent)

    def create_service_card(self, parent, service_key, config):
        """创建服务卡片"""
        # 卡片容器
        card = tk.Frame(parent, bg="white", relief=tk.SOLID, bd=1)
        card.pack(fill=tk.X, pady=8)

        # 左侧色条
        color_bar = tk.Frame(card, bg=config['color'], width=5)
        color_bar.pack(side=tk.LEFT, fill=tk.Y)

        # 内容区域
        content = tk.Frame(card, bg="white")
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=12)

        # 顶部：名称和状态
        top_row = tk.Frame(content, bg="white")
        top_row.pack(fill=tk.X)

        name_label = tk.Label(
            top_row,
            text=config['name'],
            font=("Microsoft YaHei UI", 11, "bold"),
            bg="white",
            fg=self.colors['primary']
        )
        name_label.pack(side=tk.LEFT)

        status_label = tk.Label(
            top_row,
            text="⚪ 检测中",
            font=("Microsoft YaHei UI", 9),
            bg="white",
            fg="#95a5a6"
        )
        status_label.pack(side=tk.RIGHT)

        # 中间：描述
        desc_label = tk.Label(
            content,
            text=config['description'],
            font=("Microsoft YaHei UI", 8),
            bg="white",
            fg="#7f8c8d",
            wraplength=350,
            justify=tk.LEFT
        )
        desc_label.pack(fill=tk.X, pady=(5, 8))

        # 详细信息
        info_label = tk.Label(
            content,
            text="",
            font=("Consolas", 8),
            bg="white",
            fg="#95a5a6",
            justify=tk.LEFT
        )
        info_label.pack(fill=tk.X)

        # 底部：按钮组
        btn_row = tk.Frame(content, bg="white")
        btn_row.pack(fill=tk.X, pady=(8, 0))

        start_btn = tk.Button(
            btn_row,
            text="▶️ 启动",
            font=("Microsoft YaHei UI", 9),
            bg=config['color'],
            fg="white",
            width=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.start_service_detailed(service_key)
        )
        start_btn.pack(side=tk.LEFT, padx=(0, 5))

        stop_btn = tk.Button(
            btn_row,
            text="⏹️ 停止",
            font=("Microsoft YaHei UI", 9),
            bg="#95a5a6",
            fg="white",
            width=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.stop_service_detailed(service_key)
        )
        stop_btn.pack(side=tk.LEFT, padx=5)

        restart_btn = tk.Button(
            btn_row,
            text="🔄 重启",
            font=("Microsoft YaHei UI", 9),
            bg="#34495e",
            fg="white",
            width=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.restart_service_detailed(service_key)
        )
        restart_btn.pack(side=tk.LEFT, padx=5)

        detail_btn = tk.Button(
            btn_row,
            text="🔍 详情",
            font=("Microsoft YaHei UI", 9),
            bg=self.colors['info'],
            fg="white",
            width=8,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.show_service_details(service_key)
        )
        detail_btn.pack(side=tk.LEFT, padx=5)

        # 保存widgets引用
        self.service_widgets[service_key] = {
            'card': card,
            'status': status_label,
            'info': info_label,
            'start_btn': start_btn,
            'stop_btn': stop_btn,
            'restart_btn': restart_btn
        }

    def create_batch_operations(self, parent):
        """创建批量操作区域"""
        batch_frame = tk.LabelFrame(
            parent,
            text="⚡ 快速操作",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg="white",
            fg=self.colors['primary']
        )
        batch_frame.pack(fill=tk.X, padx=15, pady=15)

        btn_container = tk.Frame(batch_frame, bg="white")
        btn_container.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_container,
            text="🚀 启动所有服务",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.colors['success'],
            fg="white",
            height=2,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.start_all_services_detailed
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            btn_container,
            text="⏹️ 停止所有服务",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.colors['danger'],
            fg="white",
            height=2,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.stop_all_services_detailed
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            btn_container,
            text="🔄 刷新状态",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.colors['info'],
            fg="white",
            height=2,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.detailed_check_all_services
        ).pack(fill=tk.X, pady=2)

    def create_log_panel(self, parent):
        """创建日志面板"""
        # 标题栏
        header_frame = tk.Frame(parent, bg="white")
        header_frame.pack(fill=tk.X, padx=15, pady=15)

        tk.Label(
            header_frame,
            text="📋 实时日志",
            font=("Microsoft YaHei UI", 14, "bold"),
            bg="white",
            fg=self.colors['primary']
        ).pack(side=tk.LEFT)

        tk.Button(
            header_frame,
            text="🗑️ 清空",
            font=("Microsoft YaHei UI", 9),
            bg=self.colors['danger'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.clear_log
        ).pack(side=tk.RIGHT)

        tk.Button(
            header_frame,
            text="💾 导出",
            font=("Microsoft YaHei UI", 9),
            bg=self.colors['info'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.export_log
        ).pack(side=tk.RIGHT, padx=5)

        # 日志文本区域
        log_container = tk.Frame(parent, bg="white")
        log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.log_text = scrolledtext.ScrolledText(
            log_container,
            font=("Consolas", 9),
            bg=self.colors['dark'],
            fg="#d4d4d4",
            insertbackground="white",
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置日志颜色标签
        self.log_text.tag_config("SUCCESS", foreground="#27ae60")
        self.log_text.tag_config("ERROR", foreground="#e74c3c")
        self.log_text.tag_config("WARNING", foreground="#f39c12")
        self.log_text.tag_config("INFO", foreground="#3498db")
        self.log_text.tag_config("DEBUG", foreground="#95a5a6")

    def create_status_bar(self):
        """创建状态栏"""
        status_frame = tk.Frame(self.root, bg=self.colors['primary'], height=35)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)

        self.status_bar_label = tk.Label(
            status_frame,
            text="💻 系统就绪",
            font=("Microsoft YaHei UI", 9),
            bg=self.colors['primary'],
            fg="white",
            anchor="w"
        )
        self.status_bar_label.pack(side=tk.LEFT, padx=15, fill=tk.Y)

        self.time_label = tk.Label(
            status_frame,
            text="",
            font=("Consolas", 9),
            bg=self.colors['primary'],
            fg="#95a5a6",
            anchor="e"
        )
        self.time_label.pack(side=tk.RIGHT, padx=15, fill=tk.Y)

        # 更新时间
        self.update_time()

    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    def log(self, message, level="INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"

        # 添加到缓冲区
        self.log_buffer.append((log_entry, level))
        if len(self.log_buffer) > self.max_log_buffer:
            self.log_buffer.pop(0)

        # 显示在界面
        self.log_text.insert(tk.END, f"{log_entry}\n", level)
        self.log_text.see(tk.END)

    def log_section(self, title):
        """添加分隔符"""
        separator = "=" * 60
        self.log(separator, "DEBUG")
        self.log(title, "INFO")
        self.log(separator, "DEBUG")

    def update_status_bar(self, message):
        """更新状态栏"""
        self.status_bar_label.config(text=message)

    def show_welcome_message(self):
        """显示欢迎信息"""
        self.log_section("🎉 欢迎使用采购系统启动器 Pro Max v3.0")
        self.log(f"📂 项目根目录: {self.project_root}", "INFO")
        self.log(f"🔧 后端路径: {self.backend_path}", "INFO")
        self.log(f"🌐 前端路径: {self.frontend_path}", "INFO")
        self.log("", "INFO")
        self.log("✨ 特性:", "INFO")
        self.log("  • 🚫 无CMD窗口，完全GUI化", "INFO")
        self.log("  • 📊 实时详细日志和状态监控", "INFO")
        self.log("  • 🔍 智能服务检测和健康检查", "INFO")
        self.log("  • 🎨 现代化美观界面", "INFO")
        self.log_section("准备就绪，开始检测服务状态...")

    # ==================== 服务检测方法 ====================

    def check_port(self, port):
        """检查端口是否被占用"""
        if port is None:
            return False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except:
            return False

    def find_process_by_pattern(self, process_names, cmd_pattern, exclude_pattern=None):
        """通过进程名和命令行模式查找进程"""
        found_processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info', 'cpu_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['name'] in process_names:
                        cmdline = ' '.join(pinfo['cmdline']) if pinfo['cmdline'] else ''
                        cmdline_lower = cmdline.lower()

                        if cmd_pattern.lower() in cmdline_lower:
                            if exclude_pattern and exclude_pattern.lower() in cmdline_lower:
                                continue
                            found_processes.append(proc)
                except:
                    continue
        except:
            pass
        return found_processes

    def check_service_status(self, service_key):
        """详细检查服务状态"""
        config = self.service_config[service_key]
        status = {
            'running': False,
            'pid': None,
            'port': config['port'],
            'port_listening': False,
            'memory_mb': 0,
            'cpu_percent': 0,
            'uptime': None,
            'health': 'unknown'
        }

        # 1. 检查通过启动器启动的进程
        if self.processes[service_key] and self.processes[service_key].poll() is None:
            try:
                proc = psutil.Process(self.processes[service_key].pid)
                status['running'] = True
                status['pid'] = proc.pid
                status['memory_mb'] = proc.memory_info().rss / 1024 / 1024
                status['cpu_percent'] = proc.cpu_percent()
                status['uptime'] = time.time() - proc.create_time()
            except:
                self.processes[service_key] = None

        # 2. 检查端口
        if config['port']:
            status['port_listening'] = self.check_port(config['port'])
            if status['port_listening'] and not status['running']:
                # 端口被占用但不是我们启动的，查找进程
                try:
                    for conn in psutil.net_connections():
                        if conn.laddr.port == config['port'] and conn.status == 'LISTEN':
                            proc = psutil.Process(conn.pid)
                            status['running'] = True
                            status['pid'] = conn.pid
                            status['memory_mb'] = proc.memory_info().rss / 1024 / 1024
                            status['cpu_percent'] = proc.cpu_percent()
                            status['uptime'] = time.time() - proc.create_time()
                            break
                except:
                    pass

        # 3. 检查进程名和命令行
        if not status['running']:
            exclude = 'celery' if service_key == 'backend' else None
            processes = self.find_process_by_pattern(
                config['process_names'],
                config['cmd_pattern'],
                exclude_pattern=exclude
            )
            if processes:
                proc = processes[0]
                status['running'] = True
                status['pid'] = proc.pid
                try:
                    status['memory_mb'] = proc.memory_info().rss / 1024 / 1024
                    status['cpu_percent'] = proc.cpu_percent()
                    status['uptime'] = time.time() - proc.create_time()
                except:
                    pass

        # 4. 健康检查
        if status['running'] and config.get('health_check'):
            try:
                status['health'] = config['health_check']()
            except:
                status['health'] = 'unknown'

        return status

    def check_mysql_health(self):
        """MySQL健康检查"""
        try:
            result = subprocess.run(
                'mysql -u root -pexak472008 -e "SELECT 1" 2>nul',
                shell=True,
                capture_output=True,
                timeout=3
            )
            return 'healthy' if result.returncode == 0 else 'unhealthy'
        except:
            return 'unknown'

    def check_redis_health(self):
        """Redis健康检查"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('127.0.0.1', 6379))
            sock.send(b'PING\r\n')
            response = sock.recv(1024)
            sock.close()
            return 'healthy' if b'PONG' in response else 'unhealthy'
        except:
            return 'unhealthy'

    def check_backend_health(self):
        """后端健康检查"""
        try:
            import urllib.request
            response = urllib.request.urlopen('http://localhost:5001/api/health', timeout=3)
            return 'healthy' if response.getcode() == 200 else 'unhealthy'
        except:
            return 'unhealthy'

    def check_celery_health(self):
        """Celery健康检查"""
        # Celery没有简单的健康检查，只检查进程存在
        return 'healthy'

    def check_frontend_health(self):
        """前端健康检查"""
        try:
            import urllib.request
            response = urllib.request.urlopen('http://localhost:3000', timeout=3)
            return 'healthy' if response.getcode() == 200 else 'unhealthy'
        except:
            return 'unhealthy'

    def detailed_check_all_services(self):
        """详细检查所有服务"""
        self.log_section("🔍 开始详细检测所有服务状态...")
        self.update_status_bar("🔍 正在检测服务...")

        for service_key in self.service_config.keys():
            config = self.service_config[service_key]
            status = self.check_service_status(service_key)
            self.service_status[service_key] = status

            # 更新界面
            self.update_service_ui(service_key, status, config)

            # 记录日志
            if status['running']:
                uptime_str = self.format_uptime(status['uptime']) if status['uptime'] else 'N/A'
                self.log(
                    f"✅ {config['name']}: 运行中 | PID: {status['pid']} | "
                    f"内存: {status['memory_mb']:.1f}MB | CPU: {status['cpu_percent']:.1f}% | "
                    f"运行时长: {uptime_str} | 健康: {status['health']}",
                    "SUCCESS"
                )
            else:
                self.log(f"⚪ {config['name']}: 未运行", "WARNING")

        self.log_section("✅ 状态检测完成")
        self.update_status_bar("✅ 状态检测完成")

    def update_service_ui(self, service_key, status, config):
        """更新服务UI"""
        widgets = self.service_widgets[service_key]

        if status['running']:
            # 运行中
            health_emoji = {
                'healthy': '🟢',
                'unhealthy': '🟡',
                'unknown': '⚪'
            }.get(status['health'], '⚪')

            widgets['status'].config(text=f"{health_emoji} 运行中", fg=self.colors['success'])

            info_parts = []
            if status['port']:
                info_parts.append(f"端口: {status['port']}")
            if status['pid']:
                info_parts.append(f"PID: {status['pid']}")
            if status['memory_mb']:
                info_parts.append(f"内存: {status['memory_mb']:.1f}MB")
            if status['uptime']:
                info_parts.append(f"运行: {self.format_uptime(status['uptime'])}")

            widgets['info'].config(text=" | ".join(info_parts))

            # 禁用启动按钮
            widgets['start_btn'].config(state=tk.DISABLED)
            widgets['stop_btn'].config(state=tk.NORMAL)
            widgets['restart_btn'].config(state=tk.NORMAL)
        else:
            # 未运行
            widgets['status'].config(text="⚪ 未启动", fg="#95a5a6")
            widgets['info'].config(text="")

            # 启用启动按钮
            widgets['start_btn'].config(state=tk.NORMAL)
            widgets['stop_btn'].config(state=tk.DISABLED)
            widgets['restart_btn'].config(state=tk.DISABLED)

    def format_uptime(self, seconds):
        """格式化运行时长"""
        if seconds is None:
            return "N/A"

        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    # ==================== 服务启动方法 ====================

    def start_service_detailed(self, service_key):
        """详细启动服务"""
        config = self.service_config[service_key]
        status = self.check_service_status(service_key)

        if status['running']:
            self.log(f"⚠️  {config['name']} 已在运行中 (PID: {status['pid']})", "WARNING")
            messagebox.showwarning("警告", f"{config['name']} 已在运行中")
            return

        self.log_section(f"🚀 开始启动 {config['name']}")
        self.log(f"📝 描述: {config['description']}", "INFO")
        self.log(f"⏱️  预计启动时间: {config['startup_time']}秒", "INFO")
        self.update_status_bar(f"🚀 正在启动 {config['name']}...")

        # 在新线程中启动
        threading.Thread(
            target=self._start_service_thread,
            args=(service_key,),
            daemon=True
        ).start()

    def _start_service_thread(self, service_key):
        """启动服务线程"""
        config = self.service_config[service_key]

        try:
            if service_key == "mysql":
                self._start_mysql()
            elif service_key == "redis":
                self._start_redis()
            elif service_key == "backend":
                self._start_backend()
            elif service_key == "celery":
                self._start_celery()
            elif service_key == "frontend":
                self._start_frontend()

            # 等待服务启动
            self.log(f"⏳ 等待 {config['name']} 完全启动...", "INFO")

            for i in range(config['startup_time']):
                time.sleep(1)
                self.log(f"   {i+1}/{config['startup_time']} 秒...", "DEBUG")

            # 检查启动结果
            status = self.check_service_status(service_key)

            # 详细验证启动状态
            success = False
            if status['running']:
                # 第1步：检查进程存在
                self.log(f"✅ 进程已启动 (PID: {status['pid']})", "SUCCESS")

                # 第2步：检查端口（如果服务需要端口）
                if config['port']:
                    if status['port_listening']:
                        self.log(f"✅ 端口 {config['port']} 正在监听", "SUCCESS")
                    else:
                        self.log(f"⚠️  端口 {config['port']} 未监听，服务可能未完全启动", "WARNING")

                # 第3步：健康检查
                if config.get('health_check'):
                    health = status.get('health', 'unknown')
                    if health == 'healthy':
                        self.log(f"✅ 健康检查通过", "SUCCESS")
                        success = True
                    elif health == 'unhealthy':
                        self.log(f"❌ 健康检查失败 - 服务未正常响应", "ERROR")
                    else:
                        self.log(f"⚠️  健康检查状态未知", "WARNING")
                        # 如果没有健康检查但进程和端口都正常，也算成功
                        if not config['port'] or status['port_listening']:
                            success = True
                else:
                    # 没有健康检查的服务，进程存在即认为成功
                    success = True

                if success:
                    self.log(f"✅ {config['name']} 启动成功！", "SUCCESS")
                    if config['port']:
                        self.log(f"🌐 访问地址: http://localhost:{config['port']}", "INFO")
                else:
                    self.log(f"❌ {config['name']} 启动后验证失败", "ERROR")
                    self.log(f"💡 建议：检查日志窗口中的错误信息", "INFO")
            else:
                self.log(f"❌ {config['name']} 启动失败 - 进程未运行", "ERROR")
                self.log(f"💡 建议：手动启动并查看错误信息", "INFO")

            # 刷新界面
            self.root.after(100, lambda: self.update_service_ui(service_key, status, config))

        except Exception as e:
            self.log(f"❌ 启动失败: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")

    def _start_mysql(self):
        """启动MySQL"""
        self.log("🔧 尝试启动MySQL80服务...", "INFO")
        try:
            result = subprocess.run(
                'net start MySQL80',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.log("✅ MySQL80服务启动命令执行成功", "SUCCESS")
            else:
                self.log(f"⚠️  MySQL80启动失败，尝试MySQL90...", "WARNING")
                result = subprocess.run(
                    'net start MySQL90',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    self.log("✅ MySQL90服务启动命令执行成功", "SUCCESS")
                else:
                    raise Exception("MySQL服务启动失败")
        except Exception as e:
            self.log(f"❌ MySQL启动失败: {e}", "ERROR")
            raise

    def _start_redis(self):
        """启动Redis"""
        self.log("🔧 启动Redis服务...", "INFO")
        cmd = 'redis-server'
        self.processes['redis'] = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        self.log(f"✅ Redis进程已启动 (PID: {self.processes['redis'].pid})", "SUCCESS")

    def _start_backend(self):
        """启动Backend"""
        self.log(f"🔧 启动Backend服务... (路径: {self.backend_path})", "INFO")
        cmd = f'cd /d "{self.backend_path}" && python app.py'
        self.processes['backend'] = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        self.log(f"✅ Backend进程已启动 (PID: {self.processes['backend'].pid})", "SUCCESS")

    def _start_celery(self):
        """启动Celery"""
        self.log(f"🔧 启动Celery服务... (路径: {self.backend_path})", "INFO")
        # 使用专用启动脚本
        cmd = f'cd /d "{self.backend_path}" && python start_celery.py'
        self.processes['celery'] = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        self.log(f"✅ Celery进程已启动 (PID: {self.processes['celery'].pid})", "SUCCESS")

    def _start_frontend(self):
        """启动Frontend"""
        self.log(f"🔧 启动Frontend服务... (路径: {self.frontend_path})", "INFO")
        cmd = f'cd /d "{self.frontend_path}" && npm start'
        self.processes['frontend'] = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        self.log(f"✅ Frontend进程已启动 (PID: {self.processes['frontend'].pid})", "SUCCESS")

    # ==================== 服务停止方法 ====================

    def stop_service_detailed(self, service_key):
        """详细停止服务"""
        config = self.service_config[service_key]
        status = self.check_service_status(service_key)

        if not status['running']:
            self.log(f"⚠️  {config['name']} 未在运行", "WARNING")
            return

        self.log_section(f"⏹️  开始停止 {config['name']}")
        self.update_status_bar(f"⏹️  正在停止 {config['name']}...")

        threading.Thread(
            target=self._stop_service_thread,
            args=(service_key,),
            daemon=True
        ).start()

    def _stop_service_thread(self, service_key):
        """停止服务线程"""
        config = self.service_config[service_key]
        status = self.service_status.get(service_key, {})

        try:
            if service_key == "mysql":
                self._stop_mysql()
            else:
                self._stop_process(service_key, status.get('pid'))

            time.sleep(2)

            # 验证是否停止
            new_status = self.check_service_status(service_key)
            if not new_status['running']:
                self.log(f"✅ {config['name']} 已成功停止", "SUCCESS")
            else:
                self.log(f"⚠️  {config['name']} 可能未完全停止", "WARNING")

            self.root.after(100, lambda: self.update_service_ui(service_key, new_status, config))

        except Exception as e:
            self.log(f"❌ 停止失败: {e}", "ERROR")

    def _stop_mysql(self):
        """停止MySQL"""
        self.log("🔧 尝试停止MySQL80服务...", "INFO")
        try:
            result = subprocess.run('net stop MySQL80', shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log("✅ MySQL80服务停止成功", "SUCCESS")
            else:
                self.log("⚠️  MySQL80停止失败，尝试MySQL90...", "WARNING")
                subprocess.run('net stop MySQL90', shell=True, capture_output=True, text=True, timeout=10)
        except:
            pass

    def _stop_process(self, service_key, pid):
        """停止进程"""
        if pid:
            self.log(f"🔧 终止进程 PID: {pid}", "INFO")
            try:
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)

                # 先终止子进程
                for child in children:
                    try:
                        self.log(f"   终止子进程: {child.pid}", "DEBUG")
                        child.terminate()
                    except:
                        pass

                # 终止主进程
                parent.terminate()

                # 等待进程结束
                try:
                    parent.wait(timeout=5)
                    self.log("✅ 进程已正常终止", "SUCCESS")
                except psutil.TimeoutExpired:
                    parent.kill()
                    self.log("⚠️  进程被强制终止", "WARNING")

            except Exception as e:
                self.log(f"❌ 终止进程失败: {e}", "ERROR")

        self.processes[service_key] = None

    def restart_service_detailed(self, service_key):
        """重启服务"""
        config = self.service_config[service_key]
        self.log_section(f"🔄 重启 {config['name']}")

        def restart_thread():
            self.stop_service_detailed(service_key)
            time.sleep(3)
            self.start_service_detailed(service_key)

        threading.Thread(target=restart_thread, daemon=True).start()

    # ==================== 批量操作 ====================

    def start_all_services_detailed(self):
        """详细启动所有服务"""
        self.log_section("🚀 开始启动所有服务...")
        self.log("📋 启动顺序: MySQL → Redis → Backend → Celery → Frontend", "INFO")

        def start_sequence():
            services = ['mysql', 'redis', 'backend', 'celery', 'frontend']
            for i, service in enumerate(services):
                status = self.check_service_status(service)
                if not status['running']:
                    config = self.service_config[service]
                    self.log(f"[{i+1}/{len(services)}] 启动 {config['name']}...", "INFO")
                    self.start_service_detailed(service)
                    time.sleep(config['startup_time'] + 2)
                else:
                    self.log(f"[{i+1}/{len(services)}] {self.service_config[service]['name']} 已在运行，跳过", "INFO")

            self.log_section("✅ 所有服务启动流程完成！")
            self.log("", "INFO")
            self.log("📱 访问地址:", "INFO")
            self.log("   前端: http://localhost:3000", "INFO")
            self.log("   后端: http://localhost:5001", "INFO")
            self.log("", "INFO")
            self.log("👤 管理员账户:", "INFO")
            self.log("   用户名: 周鹏", "INFO")
            self.log("   密码: exak472008", "INFO")
            self.log("", "INFO")
            self.log("👤 测试用户:", "INFO")
            self.log("   用户名: exzzz", "INFO")
            self.log("   密码: exak472008", "INFO")

        threading.Thread(target=start_sequence, daemon=True).start()

    def stop_all_services_detailed(self):
        """详细停止所有服务"""
        if not messagebox.askyesno("确认", "确定要停止所有服务吗？"):
            return

        self.log_section("⏹️  开始停止所有服务...")

        def stop_sequence():
            services = ['frontend', 'celery', 'backend', 'redis', 'mysql']
            for service in services:
                status = self.check_service_status(service)
                if status['running']:
                    self.stop_service_detailed(service)
                    time.sleep(2)

            self.log_section("✅ 所有服务已停止！")

        threading.Thread(target=stop_sequence, daemon=True).start()

    # ==================== 工具方法 ====================

    def show_service_details(self, service_key):
        """显示服务详情"""
        config = self.service_config[service_key]
        status = self.check_service_status(service_key)

        details = f"""
【服务详情】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

服务名称: {config['name']}
描述: {config['description']}
优先级: {config['priority']}

【当前状态】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

运行状态: {'🟢 运行中' if status['running'] else '⚪ 未运行'}
进程ID: {status['pid'] or 'N/A'}
监听端口: {status['port'] or 'N/A'}
端口状态: {'🟢 监听中' if status['port_listening'] else '⚪ 未监听'}

【性能指标】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

内存使用: {status['memory_mb']:.2f} MB
CPU使用率: {status['cpu_percent']:.1f}%
运行时长: {self.format_uptime(status['uptime']) if status['uptime'] else 'N/A'}
健康状态: {status['health']}

【配置信息】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

进程名: {', '.join(config['process_names'])}
匹配模式: {config['cmd_pattern']}
预计启动时间: {config['startup_time']}秒
        """

        messagebox.showinfo(f"{config['name']} - 详细信息", details)

    def show_system_info(self):
        """显示系统信息"""
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.project_root))

        info = f"""
【系统信息】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CPU核心数: {cpu_count}
CPU使用率: {cpu_percent}%

内存总量: {memory.total / 1024 / 1024 / 1024:.2f} GB
内存使用: {memory.used / 1024 / 1024 / 1024:.2f} GB ({memory.percent}%)
内存可用: {memory.available / 1024 / 1024 / 1024:.2f} GB

磁盘总量: {disk.total / 1024 / 1024 / 1024:.2f} GB
磁盘使用: {disk.used / 1024 / 1024 / 1024:.2f} GB ({disk.percent}%)
磁盘可用: {disk.free / 1024 / 1024 / 1024:.2f} GB

【项目信息】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目路径: {self.project_root}
后端路径: {self.backend_path}
前端路径: {self.frontend_path}

Python版本: {sys.version.split()[0]}
        """

        messagebox.showinfo("系统信息", info)

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_buffer.clear()
        self.log("📝 日志已清空", "INFO")

    def export_log(self):
        """导出日志"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.project_root / "运维工具" / f"启动器日志_{timestamp}.txt"

        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                for log_entry, level in self.log_buffer:
                    f.write(f"{log_entry}\n")

            self.log(f"✅ 日志已导出到: {log_file}", "SUCCESS")
            messagebox.showinfo("导出成功", f"日志已导出到:\n{log_file}")
        except Exception as e:
            self.log(f"❌ 导出失败: {e}", "ERROR")
            messagebox.showerror("导出失败", str(e))

    def monitor_services(self):
        """后台监控服务状态"""
        def update_status():
            while True:
                try:
                    time.sleep(3)
                    for service_key in self.service_config.keys():
                        status = self.check_service_status(service_key)
                        config = self.service_config[service_key]
                        self.service_status[service_key] = status
                        self.root.after(0, lambda k=service_key, s=status, c=config: self.update_service_ui(k, s, c))
                except:
                    pass

        thread = threading.Thread(target=update_status, daemon=True)
        thread.start()

    def on_closing(self):
        """关闭窗口"""
        if messagebox.askokcancel("退出", "确定要退出启动器吗？\n\n注意：已启动的服务将继续在后台运行。"):
            self.root.destroy()

def main():
    root = tk.Tk()
    app = UltraDetailedServiceLauncher(root)

    # 窗口居中
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    # 设置关闭处理
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.mainloop()

if __name__ == "__main__":
    main()
