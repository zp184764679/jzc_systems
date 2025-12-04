#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机加工报价系统 - GUI启动器
一键启动前后端，并检测服务状态
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Toplevel
import subprocess
import threading
import time
import os
import sys
import socket
import requests
from pathlib import Path
import psutil
from collections import deque
from queue import Queue, Empty


class LogWindow:
    """日志查看窗口"""
    def __init__(self, parent, title, service_name, log_queue):
        self.window = Toplevel(parent)
        self.window.title(title)
        self.window.geometry("800x600")
        self.service_name = service_name
        self.log_queue = log_queue
        self.running = True

        # 创建工具栏
        toolbar = tk.Frame(self.window, bg='#34495e', height=40)
        toolbar.pack(fill=tk.X, padx=0, pady=0)
        toolbar.pack_propagate(False)

        tk.Label(
            toolbar,
            text=f"📋 {title}",
            font=('Microsoft YaHei UI', 11, 'bold'),
            fg='white',
            bg='#34495e'
        ).pack(side=tk.LEFT, padx=15, pady=10)

        # 清空日志按钮
        clear_btn = tk.Button(
            toolbar,
            text="🗑 清空",
            command=self.clear_log,
            font=('Microsoft YaHei UI', 9),
            bg='#e74c3c',
            fg='white',
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor='hand2'
        )
        clear_btn.pack(side=tk.RIGHT, padx=10, pady=5)

        # 自动滚动开关
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_check = tk.Checkbutton(
            toolbar,
            text="自动滚动",
            variable=self.auto_scroll_var,
            font=('Microsoft YaHei UI', 9),
            fg='white',
            bg='#34495e',
            selectcolor='#2c3e50',
            activebackground='#34495e',
            activeforeground='white'
        )
        auto_scroll_check.pack(side=tk.RIGHT, padx=10)

        # 日志文本框
        text_frame = tk.Frame(self.window, padx=5, pady=5)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            text_frame,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white',
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 颜色标签
        self.log_text.tag_config('stdout', foreground='#d4d4d4')
        self.log_text.tag_config('stderr', foreground='#f48771')
        self.log_text.tag_config('info', foreground='#4ec9b0')
        self.log_text.tag_config('success', foreground='#4ec9b0')
        self.log_text.tag_config('warning', foreground='#dcdcaa')
        self.log_text.tag_config('error', foreground='#f48771')

        # 启动日志更新线程
        self.update_thread = threading.Thread(target=self.update_log, daemon=True)
        self.update_thread.start()

        # 窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def update_log(self):
        """更新日志内容（后台线程）"""
        while self.running:
            try:
                # 从队列中获取日志
                log_type, message = self.log_queue.get(timeout=0.1)

                # 在主线程中更新UI
                self.window.after(0, self._append_log, log_type, message)
            except Empty:
                time.sleep(0.1)
            except Exception as e:
                print(f"日志更新错误: {e}")

    def _append_log(self, log_type, message):
        """添加日志（在主线程中调用）"""
        try:
            self.log_text.insert(tk.END, message, log_type)
            if self.auto_scroll_var.get():
                self.log_text.see(tk.END)
        except:
            pass

    def on_closing(self):
        """关闭窗口"""
        self.running = False
        self.window.destroy()


class ServiceLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("机加工报价系统 - 启动器")
        self.root.geometry("900x650")
        self.root.resizable(True, True)

        # 项目路径
        self.project_root = Path(r"C:\Users\Admin\Desktop\报价")
        self.backend_path = self.project_root / "backend"
        self.frontend_path = self.project_root / "frontend"

        # 进程管理
        self.processes = {
            'backend': None,
            'frontend': None
        }

        # 日志队列
        self.log_queues = {
            'backend': Queue(),
            'frontend': Queue()
        }

        # 日志窗口
        self.log_windows = {
            'backend': None,
            'frontend': None
        }

        # 日志读取线程
        self.log_threads = {
            'backend': None,
            'frontend': None
        }

        # 服务状态
        self.service_status = {
            'redis': {'status': 'unknown', 'label': None, 'indicator': None},
            'celery': {'status': 'unknown', 'label': None, 'indicator': None},
            'ollama': {'status': 'unknown', 'label': None, 'indicator': None},
            'backend': {'status': 'stopped', 'label': None, 'indicator': None},
            'frontend': {'status': 'stopped', 'label': None, 'indicator': None}
        }

        # 创建UI
        self.create_ui()

        # 启动状态监控线程
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
        self.monitor_thread.start()

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_ui(self):
        """创建用户界面"""

        # 标题
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🚀 机加工报价系统 - 启动控制台",
            font=('Microsoft YaHei UI', 16, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=15)

        # 主容器
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === 服务状态区域 ===
        status_frame = tk.LabelFrame(main_frame, text="📊 服务状态", font=('Microsoft YaHei UI', 11, 'bold'), padx=15, pady=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        services = [
            ('redis', 'Redis 数据库', '6379'),
            ('celery', 'Celery 任务队列', '-'),
            ('ollama', 'Ollama 大模型', '11434'),
            ('backend', '后端 API', '8001'),
            ('frontend', '前端界面', '8000')
        ]

        for idx, (key, name, port) in enumerate(services):
            row_frame = tk.Frame(status_frame)
            row_frame.pack(fill=tk.X, pady=5)

            # 状态指示器
            indicator = tk.Canvas(row_frame, width=20, height=20, highlightthickness=0)
            indicator.pack(side=tk.LEFT, padx=(0, 10))
            indicator.create_oval(2, 2, 18, 18, fill='gray', outline='gray', tags='circle')
            self.service_status[key]['indicator'] = indicator

            # 服务名称
            name_label = tk.Label(row_frame, text=name, font=('Microsoft YaHei UI', 10), width=15, anchor='w')
            name_label.pack(side=tk.LEFT, padx=(0, 10))

            # 端口
            port_label = tk.Label(row_frame, text=f"Port: {port}", font=('Microsoft YaHei UI', 9), fg='gray', width=12, anchor='w')
            port_label.pack(side=tk.LEFT, padx=(0, 10))

            # 状态文本
            status_label = tk.Label(row_frame, text="检查中...", font=('Microsoft YaHei UI', 9), fg='orange', width=12, anchor='w')
            status_label.pack(side=tk.LEFT)
            self.service_status[key]['label'] = status_label

            # 日志按钮（仅对前后端）
            if key in ['backend', 'frontend']:
                log_btn = tk.Button(
                    row_frame,
                    text="📋 查看日志",
                    command=lambda k=key, n=name: self.show_log_window(k, n),
                    font=('Microsoft YaHei UI', 9),
                    bg='#3498db',
                    fg='white',
                    relief=tk.FLAT,
                    padx=10,
                    pady=3,
                    cursor='hand2'
                )
                log_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # === 控制按钮区域 ===
        control_frame = tk.LabelFrame(main_frame, text="🎮 启动控制", font=('Microsoft YaHei UI', 11, 'bold'), padx=15, pady=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill=tk.X)

        # 启动所有按钮
        self.start_all_btn = tk.Button(
            button_frame,
            text="▶ 启动所有服务",
            command=self.start_all_services,
            font=('Microsoft YaHei UI', 10, 'bold'),
            bg='#27ae60',
            fg='white',
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.start_all_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 停止所有按钮
        self.stop_all_btn = tk.Button(
            button_frame,
            text="⏹ 停止所有服务",
            command=self.stop_all_services,
            font=('Microsoft YaHei UI', 10, 'bold'),
            bg='#e74c3c',
            fg='white',
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.stop_all_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 刷新状态按钮
        refresh_btn = tk.Button(
            button_frame,
            text="🔄 刷新状态",
            command=self.refresh_status,
            font=('Microsoft YaHei UI', 10),
            bg='#3498db',
            fg='white',
            relief=tk.RAISED,
            bd=2,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        refresh_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 分隔线
        separator = ttk.Separator(control_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=10)

        # 单独控制按钮
        individual_frame = tk.Frame(control_frame)
        individual_frame.pack(fill=tk.X)

        self.backend_btn = tk.Button(
            individual_frame,
            text="启动后端",
            command=self.toggle_backend,
            font=('Microsoft YaHei UI', 9),
            bg='#95a5a6',
            fg='white',
            padx=15,
            pady=5,
            width=12
        )
        self.backend_btn.pack(side=tk.LEFT, padx=5)

        self.frontend_btn = tk.Button(
            individual_frame,
            text="启动前端",
            command=self.toggle_frontend,
            font=('Microsoft YaHei UI', 9),
            bg='#95a5a6',
            fg='white',
            padx=15,
            pady=5,
            width=12
        )
        self.frontend_btn.pack(side=tk.LEFT, padx=5)

        # 快捷访问按钮
        access_frame = tk.Frame(control_frame)
        access_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(access_frame, text="快捷访问：", font=('Microsoft YaHei UI', 9)).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            access_frame,
            text="🌐 前端页面",
            command=lambda: os.system('start http://localhost:8000'),
            font=('Microsoft YaHei UI', 9),
            padx=10,
            pady=3
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            access_frame,
            text="📚 API文档",
            command=lambda: os.system('start http://localhost:8001/docs'),
            font=('Microsoft YaHei UI', 9),
            padx=10,
            pady=3
        ).pack(side=tk.LEFT, padx=2)

        # === 简化的日志区域 ===
        log_frame = tk.LabelFrame(main_frame, text="📝 操作日志", font=('Microsoft YaHei UI', 11, 'bold'), padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white',
            wrap=tk.WORD,
            height=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 日志颜色标签
        self.log_text.tag_config('info', foreground='#4ec9b0')
        self.log_text.tag_config('success', foreground='#4ec9b0')
        self.log_text.tag_config('warning', foreground='#dcdcaa')
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('time', foreground='#858585')

        self.log("启动器已就绪，等待操作...", "info")
        self.log("提示：点击服务状态右侧的「查看日志」按钮可查看前后端详细日志", "info")

    def log(self, message, level='info'):
        """添加操作日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'time')
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.update()

    def show_log_window(self, service, service_name):
        """显示日志窗口"""
        # 如果窗口已存在，则激活它
        if self.log_windows[service] and self.log_windows[service].window.winfo_exists():
            self.log_windows[service].window.lift()
            self.log_windows[service].window.focus_force()
        else:
            # 创建新窗口
            title = f"{service_name} - 实时日志"
            self.log_windows[service] = LogWindow(
                self.root,
                title,
                service,
                self.log_queues[service]
            )

    def read_process_output(self, service, stream, stream_type):
        """读取进程输出（后台线程）"""
        try:
            for line in iter(stream.readline, b''):
                if line:
                    try:
                        text = line.decode('utf-8', errors='ignore')
                        self.log_queues[service].put((stream_type, text))
                    except:
                        pass
        except:
            pass
        finally:
            stream.close()

    def update_service_status(self, service, status, message):
        """更新服务状态"""
        self.service_status[service]['status'] = status

        # 更新指示器颜色
        indicator = self.service_status[service]['indicator']
        color_map = {
            'online': '#27ae60',
            'running': '#27ae60',
            'stopped': '#95a5a6',
            'offline': '#e74c3c',
            'unknown': '#f39c12'
        }
        color = color_map.get(status, 'gray')
        indicator.itemconfig('circle', fill=color, outline=color)

        # 更新状态文本
        label = self.service_status[service]['label']
        label.config(text=message, fg=color)

    def check_port(self, port):
        """检查端口是否被占用"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0

    def check_redis(self):
        """检查Redis服务"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
            r.ping()
            return True
        except:
            return self.check_port(6379)

    def check_celery(self):
        """检查Celery服务"""
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('celery' in str(arg).lower() for arg in cmdline):
                        return True
                except:
                    continue
            return False
        except:
            return False

    def check_ollama(self):
        """检查Ollama服务"""
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            return response.status_code == 200
        except:
            return False

    def check_backend(self):
        """检查后端服务"""
        try:
            response = requests.get('http://localhost:8001/health', timeout=2)
            return response.status_code == 200
        except:
            return False

    def check_frontend(self):
        """检查前端服务"""
        # 尝试IPv4
        if self.check_port(8000):
            return True
        # 尝试IPv6
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('::1', 8000))
            sock.close()
            return result == 0
        except:
            return False

    def monitor_services(self):
        """监控服务状态（后台线程）"""
        while self.monitoring:
            try:
                # 检查Redis
                if self.check_redis():
                    self.update_service_status('redis', 'online', '✓ 在线')
                else:
                    self.update_service_status('redis', 'offline', '✗ 离线')

                # 检查Celery
                if self.check_celery():
                    self.update_service_status('celery', 'online', '✓ 运行中')
                else:
                    self.update_service_status('celery', 'offline', '✗ 未运行')

                # 检查Ollama
                if self.check_ollama():
                    self.update_service_status('ollama', 'online', '✓ 在线')
                else:
                    self.update_service_status('ollama', 'offline', '✗ 离线')

                # 检查后端（优先检查端口，支持检测外部启动的服务）
                if self.check_backend():
                    # 服务在运行
                    if self.processes['backend'] and self.processes['backend'].poll() is None:
                        self.update_service_status('backend', 'running', '✓ 运行中')
                    else:
                        # 外部启动的服务
                        self.update_service_status('backend', 'running', '✓ 运行中(外部)')
                else:
                    # 服务未运行
                    if self.processes['backend'] and self.processes['backend'].poll() is None:
                        # 进程存在但服务未就绪
                        self.update_service_status('backend', 'running', '⚠ 启动中...')
                    else:
                        self.update_service_status('backend', 'stopped', '⚪ 已停止')

                # 检查前端（优先检查端口，支持检测外部启动的服务）
                if self.check_frontend():
                    # 服务在运行
                    if self.processes['frontend'] and self.processes['frontend'].poll() is None:
                        self.update_service_status('frontend', 'running', '✓ 运行中')
                    else:
                        # 外部启动的服务
                        self.update_service_status('frontend', 'running', '✓ 运行中(外部)')
                else:
                    # 服务未运行
                    if self.processes['frontend'] and self.processes['frontend'].poll() is None:
                        # 进程存在但服务未就绪
                        self.update_service_status('frontend', 'running', '⚠ 启动中...')
                    else:
                        self.update_service_status('frontend', 'stopped', '⚪ 已停止')

                time.sleep(3)  # 每3秒检查一次
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(5)

    def refresh_status(self):
        """手动刷新状态"""
        self.log("正在刷新服务状态...", "info")

    def start_backend(self):
        """启动后端服务"""
        if self.processes['backend'] and self.processes['backend'].poll() is None:
            self.log("后端服务已在运行中", "warning")
            return

        # 检查端口是否已被占用
        if self.check_port(8001):
            self.log("警告：端口 8001 已被占用，后端可能已在运行", "warning")
            self.log("提示：如需重启，请先手动停止占用端口的进程", "info")
            return

        try:
            self.log("正在启动后端服务...", "info")

            # 检查虚拟环境
            venv_python = self.backend_path / "venv" / "Scripts" / "python.exe"
            if not venv_python.exists():
                self.log("错误：未找到虚拟环境，请先运行: python -m venv venv", "error")
                return

            # 启动后端（隐藏CMD窗口）
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            self.processes['backend'] = subprocess.Popen(
                [str(venv_python), "main.py"],
                cwd=str(self.backend_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # 启动日志读取线程
            threading.Thread(
                target=self.read_process_output,
                args=('backend', self.processes['backend'].stdout, 'stdout'),
                daemon=True
            ).start()

            threading.Thread(
                target=self.read_process_output,
                args=('backend', self.processes['backend'].stderr, 'stderr'),
                daemon=True
            ).start()

            self.log("后端服务启动命令已执行，等待服务就绪...", "success")
            self.log("提示：点击「查看日志」按钮查看后端详细日志", "info")
            self.backend_btn.config(text="停止后端", bg='#e74c3c')

        except Exception as e:
            self.log(f"启动后端失败: {str(e)}", "error")

    def start_frontend(self):
        """启动前端服务"""
        if self.processes['frontend'] and self.processes['frontend'].poll() is None:
            self.log("前端服务已在运行中", "warning")
            return

        # 检查端口是否已被占用
        if self.check_port(8000):
            self.log("警告：端口 8000 已被占用，前端可能已在运行", "warning")
            self.log("提示：如需重启，请先手动停止占用端口的进程", "info")
            return

        try:
            self.log("正在启动前端服务...", "info")

            # 检查 node_modules
            if not (self.frontend_path / "node_modules").exists():
                self.log("警告：未找到 node_modules，请先运行: npm install", "warning")

            # 启动前端（隐藏CMD窗口）
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            self.processes['frontend'] = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(self.frontend_path),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # 启动日志读取线程
            threading.Thread(
                target=self.read_process_output,
                args=('frontend', self.processes['frontend'].stdout, 'stdout'),
                daemon=True
            ).start()

            threading.Thread(
                target=self.read_process_output,
                args=('frontend', self.processes['frontend'].stderr, 'stderr'),
                daemon=True
            ).start()

            self.log("前端服务启动命令已执行，等待服务就绪...", "success")
            self.log("提示：点击「查看日志」按钮查看前端详细日志", "info")
            self.frontend_btn.config(text="停止前端", bg='#e74c3c')

        except Exception as e:
            self.log(f"启动前端失败: {str(e)}", "error")

    def stop_backend(self):
        """停止后端服务"""
        if self.processes['backend']:
            try:
                self.log("正在停止后端服务...", "info")
                self.processes['backend'].terminate()
                self.processes['backend'].wait(timeout=5)
                self.processes['backend'] = None
                self.log("后端服务已停止", "success")
                self.backend_btn.config(text="启动后端", bg='#95a5a6')
            except:
                self.processes['backend'].kill()
                self.processes['backend'] = None
                self.log("后端服务已强制停止", "warning")

    def stop_frontend(self):
        """停止前端服务"""
        if self.processes['frontend']:
            try:
                self.log("正在停止前端服务...", "info")
                self.processes['frontend'].terminate()
                self.processes['frontend'].wait(timeout=5)
                self.processes['frontend'] = None
                self.log("前端服务已停止", "success")
                self.frontend_btn.config(text="启动前端", bg='#95a5a6')
            except:
                self.processes['frontend'].kill()
                self.processes['frontend'] = None
                self.log("前端服务已强制停止", "warning")

    def toggle_backend(self):
        """切换后端服务状态"""
        if self.processes['backend'] and self.processes['backend'].poll() is None:
            self.stop_backend()
        else:
            self.start_backend()

    def toggle_frontend(self):
        """切换前端服务状态"""
        if self.processes['frontend'] and self.processes['frontend'].poll() is None:
            self.stop_frontend()
        else:
            self.start_frontend()

    def start_all_services(self):
        """启动所有服务"""
        self.log("=" * 50, "info")
        self.log("开始启动所有服务...", "info")
        self.log("=" * 50, "info")

        # 检查依赖服务
        if not self.check_redis():
            self.log("警告: Redis 未运行，某些功能可能不可用", "warning")

        if not self.check_ollama():
            self.log("警告: Ollama 未运行，OCR功能将不可用", "warning")

        if not self.check_celery():
            self.log("提示: Celery 未运行，异步任务功能不可用", "warning")

        # 启动后端
        if not (self.processes['backend'] and self.processes['backend'].poll() is None):
            self.start_backend()
            time.sleep(2)  # 等待后端启动

        # 启动前端
        if not (self.processes['frontend'] and self.processes['frontend'].poll() is None):
            self.start_frontend()

        self.log("=" * 50, "info")
        self.log("所有服务启动完成！", "success")
        self.log("前端地址: http://localhost:8000", "info")
        self.log("后端API: http://localhost:8001/docs", "info")
        self.log("=" * 50, "info")

    def stop_all_services(self):
        """停止所有服务"""
        self.log("=" * 50, "info")
        self.log("正在停止所有服务...", "info")
        self.log("=" * 50, "info")

        self.stop_backend()
        self.stop_frontend()

        self.log("所有服务已停止", "success")

    def on_closing(self):
        """窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出启动器吗？\n\n运行中的服务将被停止。"):
            self.monitoring = False
            self.stop_all_services()
            self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = ServiceLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
