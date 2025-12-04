"""
报价系统启动器 - 系统托盘版本
无窗口运行，显示在系统托盘
"""
import os
import sys
import subprocess
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw

# 获取项目根目录（launcher.pyw现在在启动器/子文件夹中）
PROJECT_DIR = Path(__file__).parent.parent.absolute()
BACKEND_DIR = PROJECT_DIR / "backend"
FRONTEND_DIR = PROJECT_DIR / "frontend"

class QuoteSystemLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.icon = None
        self.is_running = False

    def create_icon_image(self):
        """创建托盘图标"""
        # 创建一个简单的图标
        width = 64
        height = 64
        color1 = (52, 152, 219)  # 蓝色
        color2 = (46, 204, 113)  # 绿色

        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle(
            [width // 4, height // 4, width * 3 // 4, height * 3 // 4],
            fill=color2
        )

        return image

    def start_backend(self):
        """启动后端服务"""
        try:
            backend_main = BACKEND_DIR / "main.py"
            venv_python = BACKEND_DIR / "venv" / "Scripts" / "python.exe"

            # 优先使用虚拟环境的Python
            if venv_python.exists():
                python_cmd = str(venv_python)
            else:
                python_cmd = "python"

            # Windows下使用pythonw.exe隐藏窗口，如果是.pyw则用python.exe
            if venv_python.exists():
                python_cmd = python_cmd.replace("python.exe", "pythonw.exe")

            # 启动后端（隐藏窗口）
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            self.backend_process = subprocess.Popen(
                [python_cmd, str(backend_main)],
                cwd=str(BACKEND_DIR),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            return True
        except Exception as e:
            messagebox.showerror("错误", f"启动后端失败: {str(e)}")
            return False

    def start_frontend(self):
        """启动前端服务"""
        try:
            # 启动前端开发服务器（隐藏窗口）
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            self.frontend_process = subprocess.Popen(
                ["npm.cmd", "run", "dev"],
                cwd=str(FRONTEND_DIR),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
                shell=True
            )

            return True
        except Exception as e:
            messagebox.showerror("错误", f"启动前端失败: {str(e)}")
            return False

    def stop_services(self):
        """停止所有服务"""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process = None

        if self.frontend_process:
            self.frontend_process.terminate()
            # 额外杀死npm相关进程
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "node.exe"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            except:
                pass
            self.frontend_process = None

        self.is_running = False

    def start_all(self, icon_obj=None, item=None):
        """启动所有服务"""
        if self.is_running:
            return

        def start_thread():
            # 先启动后端
            if self.start_backend():
                time.sleep(3)  # 等待后端启动
                # 再启动前端
                if self.start_frontend():
                    self.is_running = True
                    time.sleep(2)  # 等待前端启动
                    # 打开浏览器
                    subprocess.Popen(
                        ["cmd", "/c", "start", "http://localhost:5173"],
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )

        threading.Thread(target=start_thread, daemon=True).start()

    def stop_all(self, icon_obj=None, item=None):
        """停止所有服务"""
        self.stop_services()

    def open_browser(self, icon_obj=None, item=None):
        """打开浏览器"""
        subprocess.Popen(
            ["cmd", "/c", "start", "http://localhost:5173"],
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def quit_app(self, icon_obj=None, item=None):
        """退出程序"""
        self.stop_services()
        if self.icon:
            self.icon.stop()

    def run(self):
        """运行托盘程序"""
        # 创建托盘菜单
        menu = pystray.Menu(
            pystray.MenuItem("启动服务", self.start_all, default=True),
            pystray.MenuItem("停止服务", self.stop_all),
            pystray.MenuItem("打开浏览器", self.open_browser),
            pystray.MenuItem("退出", self.quit_app)
        )

        # 创建托盘图标
        self.icon = pystray.Icon(
            "报价系统",
            self.create_icon_image(),
            "机加工报价系统",
            menu
        )

        # 自动启动服务
        threading.Thread(target=lambda: self.start_all(), daemon=True).start()

        # 运行托盘图标
        self.icon.run()

if __name__ == "__main__":
    # 确保只运行一个实例
    import psutil
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid and 'launcher.pyw' in ' '.join(proc.info['cmdline'] or []):
                # 已经有实例在运行
                sys.exit(0)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    launcher = QuoteSystemLauncher()
    launcher.run()
