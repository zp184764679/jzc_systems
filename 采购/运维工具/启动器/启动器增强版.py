"""
采购系统 - 服务启动器增强版
一键启动/停止所有服务：后端、前端、Celery、Redis、MySQL
支持智能检测系统中已运行的服务
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import sys
import threading
import time
import psutil
import socket
from datetime import datetime

class EnhancedServiceLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("采购系统 - 服务启动器 Pro")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)

        # 服务进程字典（通过启动器启动的）
        self.processes = {
            'backend': None,
            'frontend': None,
            'celery': None,
            'redis': None,
            'mysql': None
        }

        # 服务配置
        self.service_config = {
            'backend': {
                'name': '🔧 后端服务 (Flask)',
                'port': 5001,
                'process_names': ['python.exe', 'python'],
                'cmd_pattern': 'app.py',
                'color': '#3498db'
            },
            'frontend': {
                'name': '🌐 前端服务 (React)',
                'port': 3000,
                'process_names': ['node.exe', 'node'],
                'cmd_pattern': 'react-scripts',
                'color': '#2ecc71'
            },
            'celery': {
                'name': '⚙️ Celery 任务队列',
                'port': None,
                'process_names': ['python.exe', 'python', 'celery.exe', 'celery'],
                'cmd_pattern': 'celery worker',  # 匹配 celery worker 命令
                'color': '#e67e22'
            },
            'redis': {
                'name': '💾 Redis 缓存',
                'port': 6379,
                'process_names': ['redis-server.exe', 'redis-server'],
                'cmd_pattern': 'redis',
                'color': '#e74c3c'
            },
            'mysql': {
                'name': '🗄️ MySQL 数据库',
                'port': 3306,
                'process_names': ['mysqld.exe', 'mysqld'],
                'cmd_pattern': 'mysql',
                'color': '#f39c12'
            }
        }

        # 项目路径
        self.project_root = r"C:\Users\Admin\Desktop\采购"
        self.backend_path = os.path.join(self.project_root, "backend")
        self.frontend_path = os.path.join(self.project_root, "frontend")

        # 创建界面
        self.create_widgets()

        # 启动状态监控
        self.monitor_services()

        # 首次检测
        self.check_all_services()

    def create_widgets(self):
        """创建界面组件"""
        # 顶部标题
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=70)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🚀 采购系统服务启动器 Pro",
            font=("Microsoft YaHei UI", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=20)

        # 主内容区
        main_frame = tk.Frame(self.root, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # 服务控制区域
        control_frame = tk.LabelFrame(
            main_frame,
            text="🎛️ 服务控制面板",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg="white",
            padx=15,
            pady=15
        )
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # 创建服务控制行
        self.status_labels = {}
        self.port_labels = {}
        self.pid_labels = {}

        for service_key, config in self.service_config.items():
            service_frame = tk.Frame(control_frame, bg="white")
            service_frame.pack(fill=tk.X, pady=5)

            # 服务名称
            name_label = tk.Label(
                service_frame,
                text=config['name'],
                font=("Microsoft YaHei UI", 10, "bold"),
                bg="white",
                width=22,
                anchor="w"
            )
            name_label.pack(side=tk.LEFT, padx=(0, 10))

            # 状态指示
            status_label = tk.Label(
                service_frame,
                text="⚪ 检测中...",
                font=("Microsoft YaHei UI", 9),
                bg="white",
                fg="#95a5a6",
                width=12
            )
            status_label.pack(side=tk.LEFT, padx=5)
            self.status_labels[service_key] = status_label

            # 端口/进程信息
            info_label = tk.Label(
                service_frame,
                text="",
                font=("Consolas", 8),
                bg="white",
                fg="#7f8c8d",
                width=18,
                anchor="w"
            )
            info_label.pack(side=tk.LEFT, padx=5)
            self.port_labels[service_key] = info_label

            # 启动按钮
            start_btn = tk.Button(
                service_frame,
                text="▶️ 启动",
                font=("Microsoft YaHei UI", 9),
                bg=config['color'],
                fg="white",
                width=7,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda k=service_key: self.start_service(k)
            )
            start_btn.pack(side=tk.LEFT, padx=2)

            # 停止按钮
            stop_btn = tk.Button(
                service_frame,
                text="⏹️ 停止",
                font=("Microsoft YaHei UI", 9),
                bg="#95a5a6",
                fg="white",
                width=7,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda k=service_key: self.stop_service(k)
            )
            stop_btn.pack(side=tk.LEFT, padx=2)

            # 重启按钮
            restart_btn = tk.Button(
                service_frame,
                text="🔄 重启",
                font=("Microsoft YaHei UI", 9),
                bg="#34495e",
                fg="white",
                width=7,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda k=service_key: self.restart_service(k)
            )
            restart_btn.pack(side=tk.LEFT, padx=2)

        # 批量操作按钮
        batch_frame = tk.Frame(control_frame, bg="white")
        batch_frame.pack(fill=tk.X, pady=(15, 5))

        tk.Button(
            batch_frame,
            text="🚀 启动所有服务",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg="#27ae60",
            fg="white",
            height=2,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.start_all_services
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        tk.Button(
            batch_frame,
            text="⏹️ 停止所有服务",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg="#c0392b",
            fg="white",
            height=2,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.stop_all_services
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        tk.Button(
            batch_frame,
            text="🔄 刷新状态",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg="#3498db",
            fg="white",
            height=2,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.check_all_services
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

        # 日志区域
        log_frame = tk.LabelFrame(
            main_frame,
            text="📋 运行日志",
            font=("Microsoft YaHei UI", 12, "bold"),
            bg="white",
            padx=10,
            pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            height=15
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 底部状态栏
        self.status_bar = tk.Label(
            self.root,
            text="💻 系统就绪 | 正在检测服务状态...",
            font=("Microsoft YaHei UI", 9),
            bg="#34495e",
            fg="white",
            anchor="w",
            padx=10
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # 初始日志
        self.log("=" * 60)
        self.log("📊 采购系统服务启动器 Pro v2.0")
        self.log("=" * 60)
        self.log(f"📂 项目路径: {self.project_root}")
        self.log(f"🔧 后端路径: {self.backend_path}")
        self.log(f"🌐 前端路径: {self.frontend_path}")
        self.log("=" * 60)

    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def update_status_bar(self, message):
        """更新状态栏"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_bar.config(text=f"{message} | {timestamp}")

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
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    pinfo = proc.info
                    if pinfo['name'] in process_names:
                        cmdline = ' '.join(pinfo['cmdline']) if pinfo['cmdline'] else ''
                        cmdline_lower = cmdline.lower()

                        # 检查是否匹配目标模式
                        if cmd_pattern.lower() in cmdline_lower:
                            # 检查是否需要排除
                            if exclude_pattern and exclude_pattern.lower() in cmdline_lower:
                                continue
                            found_processes.append(proc)
                except:
                    continue
        except:
            pass
        return found_processes

    def check_service_status(self, service_key):
        """检查服务状态"""
        config = self.service_config[service_key]

        # 1. 先检查通过启动器启动的进程
        if self.processes[service_key] and self.processes[service_key].poll() is None:
            try:
                proc = psutil.Process(self.processes[service_key].pid)
                return True, proc.pid
            except:
                self.processes[service_key] = None

        # 2. 检查端口
        if config['port'] and self.check_port(config['port']):
            # 尝试找到占用端口的进程
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port == config['port'] and conn.status == 'LISTEN':
                        return True, conn.pid
            except:
                pass
            return True, None

        # 3. 检查进程名和命令行
        # 后端需要排除celery进程
        exclude = 'celery' if service_key == 'backend' else None
        processes = self.find_process_by_pattern(
            config['process_names'],
            config['cmd_pattern'],
            exclude_pattern=exclude
        )
        if processes:
            return True, processes[0].pid

        return False, None

    def check_all_services(self):
        """检查所有服务状态"""
        self.log("🔍 开始检测所有服务状态...")

        for service_key in self.service_config.keys():
            is_running, pid = self.check_service_status(service_key)
            config = self.service_config[service_key]

            if is_running:
                self.status_labels[service_key].config(text="🟢 运行中", fg="#27ae60")
                port_info = f"端口: {config['port']}" if config['port'] else ""
                pid_info = f"PID: {pid}" if pid else ""
                info = f"{port_info} {pid_info}".strip()
                self.port_labels[service_key].config(text=info)
                self.log(f"  ✅ {config['name']}: 运行中 {info}")
            else:
                self.status_labels[service_key].config(text="⚪ 未启动", fg="#95a5a6")
                self.port_labels[service_key].config(text="")
                self.log(f"  ⚪ {config['name']}: 未启动")

        self.log("✅ 状态检测完成")
        self.update_status_bar("✅ 状态检测完成")

    def start_service(self, service_name):
        """启动单个服务"""
        is_running, pid = self.check_service_status(service_name)
        if is_running:
            self.log(f"⚠️ {self.service_config[service_name]['name']} 已在运行中 (PID: {pid})")
            messagebox.showwarning("警告", f"{self.service_config[service_name]['name']} 已在运行中")
            return

        self.log(f"🚀 正在启动 {self.service_config[service_name]['name']}...")

        try:
            if service_name == "backend":
                cmd = f'cd /d "{self.backend_path}" && python app.py'
                self.processes['backend'] = subprocess.Popen(
                    cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.log("✅ 后端服务启动成功 (http://localhost:5001)")

            elif service_name == "frontend":
                cmd = f'cd /d "{self.frontend_path}" && npm start'
                self.processes['frontend'] = subprocess.Popen(
                    cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.log("✅ 前端服务启动成功 (http://localhost:3000)")

            elif service_name == "celery":
                # 使用python -m celery启动（更可靠）
                cmd = f'cd /d "{self.backend_path}" && python -m celery -A celery_app.celery worker --loglevel=info --pool=solo'
                self.processes['celery'] = subprocess.Popen(
                    cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.log("✅ Celery 任务队列启动成功")

            elif service_name == "redis":
                cmd = 'redis-server'
                self.processes['redis'] = subprocess.Popen(
                    cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.log("✅ Redis 服务启动成功 (端口: 6379)")

            elif service_name == "mysql":
                # MySQL 通常作为Windows服务运行
                # 尝试MySQL80（新安装的8.0版本）
                try:
                    result = subprocess.run('net start MySQL80', shell=True, check=True, capture_output=True, text=True)
                    self.log("✅ MySQL 数据库启动成功 (端口: 3306)")
                except:
                    # 如果MySQL80失败，尝试MySQL90
                    try:
                        subprocess.run('net start MySQL90', shell=True, check=True, capture_output=True)
                        self.log("✅ MySQL 数据库启动成功 (端口: 3306)")
                    except:
                        self.log("❌ MySQL 启动失败，请检查MySQL服务名称或手动启动")
                        messagebox.showerror("错误", "MySQL启动失败\n\n可能原因：\n1. MySQL未安装\n2. 服务名称不是MySQL80或MySQL90\n3. 需要管理员权限")

            self.update_status_bar(f"✅ {self.service_config[service_name]['name']} 启动中...")
            # 根据不同服务调整检测延迟
            if service_name == "frontend":
                delay = 5000  # 前端需要5秒
            elif service_name == "celery":
                delay = 3000  # Celery需要3秒
            else:
                delay = 2000  # 其他服务2秒
            self.root.after(delay, self.check_all_services)

        except Exception as e:
            self.log(f"❌ 启动失败: {e}")
            self.update_status_bar(f"❌ {service_name} 启动失败")
            messagebox.showerror("启动失败", f"无法启动 {self.service_config[service_name]['name']}\n\n错误: {e}")

    def stop_service(self, service_name):
        """停止单个服务"""
        is_running, pid = self.check_service_status(service_name)

        if not is_running:
            self.log(f"⚠️ {self.service_config[service_name]['name']} 未在运行")
            return

        self.log(f"⏹️ 正在停止 {self.service_config[service_name]['name']}...")

        try:
            if service_name == "mysql":
                # MySQL 特殊处理 - 尝试MySQL80或MySQL90
                try:
                    subprocess.run('net stop MySQL80', shell=True, check=True, capture_output=True)
                    self.log(f"✅ MySQL 数据库已停止")
                except:
                    try:
                        subprocess.run('net stop MySQL90', shell=True, check=True, capture_output=True)
                        self.log(f"✅ MySQL 数据库已停止")
                    except:
                        self.log(f"❌ MySQL 停止失败")
            else:
                # 其他服务：终止进程
                if pid:
                    try:
                        parent = psutil.Process(pid)
                        children = parent.children(recursive=True)

                        for child in children:
                            try:
                                child.terminate()
                            except:
                                pass

                        parent.terminate()

                        try:
                            parent.wait(timeout=5)
                        except:
                            parent.kill()

                        self.log(f"✅ {self.service_config[service_name]['name']} 已停止")
                    except Exception as e:
                        self.log(f"❌ 停止失败: {e}")

                self.processes[service_name] = None

            self.update_status_bar(f"✅ {self.service_config[service_name]['name']} 已停止")
            # 刷新状态
            self.root.after(1000, self.check_all_services)

        except Exception as e:
            self.log(f"❌ 停止失败: {e}")
            messagebox.showerror("停止失败", f"无法停止 {self.service_config[service_name]['name']}\n\n错误: {e}")

    def restart_service(self, service_name):
        """重启服务"""
        self.log(f"🔄 重启 {self.service_config[service_name]['name']}...")
        self.stop_service(service_name)
        time.sleep(2)
        self.start_service(service_name)

    def start_all_services(self):
        """启动所有服务"""
        self.log("=" * 60)
        self.log("🚀 开始启动所有服务...")
        self.log("=" * 60)

        def start_sequence():
            services = ['mysql', 'redis', 'backend', 'celery', 'frontend']
            for i, service in enumerate(services):
                is_running, _ = self.check_service_status(service)
                if not is_running:
                    self.start_service(service)
                    if i < len(services) - 1:
                        time.sleep(3)

            self.log("=" * 60)
            self.log("✅ 所有服务启动流程完成！")
            self.log("=" * 60)

        threading.Thread(target=start_sequence, daemon=True).start()

    def stop_all_services(self):
        """停止所有服务"""
        if not messagebox.askyesno("确认", "确定要停止所有服务吗？"):
            return

        self.log("=" * 60)
        self.log("⏹️ 开始停止所有服务...")
        self.log("=" * 60)

        for service in ['frontend', 'celery', 'backend', 'redis', 'mysql']:
            is_running, _ = self.check_service_status(service)
            if is_running:
                self.stop_service(service)
                time.sleep(1)

        self.log("=" * 60)
        self.log("✅ 所有服务已停止！")
        self.log("=" * 60)

    def monitor_services(self):
        """后台监控服务状态"""
        def update_status():
            while True:
                try:
                    for service_key in self.service_config.keys():
                        is_running, pid = self.check_service_status(service_key)
                        config = self.service_config[service_key]

                        if is_running:
                            self.status_labels[service_key].config(text="🟢 运行中", fg="#27ae60")
                            port_info = f"端口: {config['port']}" if config['port'] else ""
                            pid_info = f"PID: {pid}" if pid else ""
                            info = f"{port_info} {pid_info}".strip()
                            self.port_labels[service_key].config(text=info)
                        else:
                            self.status_labels[service_key].config(text="⚪ 未启动", fg="#95a5a6")
                            self.port_labels[service_key].config(text="")
                except:
                    pass

                time.sleep(3)

        thread = threading.Thread(target=update_status, daemon=True)
        thread.start()

    def on_closing(self):
        """关闭窗口时的处理"""
        if messagebox.askokcancel("退出", "确定要退出启动器吗？\n\n注意：已启动的服务将继续在后台运行。"):
            self.root.destroy()

def main():
    root = tk.Tk()
    app = EnhancedServiceLauncher(root)

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
