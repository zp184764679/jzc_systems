# -*- coding: utf-8 -*-
"""
智能部署工具 - 自动检测文件更改并打包部署
"""
import os
import sys
import time
import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading

class SmartDeployTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("智能部署工具 - 采购系统")
        self.root.geometry("900x700")

        # 项目路径
        self.project_root = Path(r'C:\Users\Admin\Desktop\采购')
        self.backend_path = self.project_root / 'backend'
        self.frontend_path = self.project_root / 'frontend'
        self.deploy_path = self.project_root / '部署工具'

        # 文件哈希缓存文件
        self.hash_cache_file = self.project_root / '.file_hashes.json'
        self.file_hashes = self.load_hash_cache()

        # 重要文件列表（需要特别监控的文件）
        self.important_files = {
            'backend': [
                'app.py',
                'config.py',
                'requirements.txt',
                'routes/*.py',
                'models/*.py',
                'services/*.py',
            ],
            'frontend': [
                'package.json',
                'vite.config.js',
                'src/pages/Login.jsx',
                'src/pages/**/*.jsx',
                'src/components/**/*.jsx',
                'src/App.jsx',
            ]
        }

        # 排除文件模式
        self.backend_excludes = [
            '__pycache__',
            '*.pyc',
            '.git',
            '.vscode',
            'node_modules',
            'logs',
            'venv',
            '*.log',
            '.env',
            'nul',
        ]

        self.frontend_excludes = [
            'node_modules',
            'dist',
            'build',
            '.vite',
            '__pycache__',
            '.git',
            '.vscode',
            '.DS_Store',
            '*.log',
        ]

        self.setup_ui()
        self.auto_check_enabled = False
        self.check_thread = None

    def load_hash_cache(self):
        """加载文件哈希缓存"""
        if self.hash_cache_file.exists():
            try:
                with open(self.hash_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_hash_cache(self):
        """保存文件哈希缓存"""
        try:
            with open(self.hash_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_hashes, f, indent=2)
        except Exception as e:
            self.log(f"保存哈希缓存失败: {e}", "error")

    def calculate_file_hash(self, file_path):
        """计算文件MD5哈希"""
        try:
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            return None

    def should_exclude(self, path, excludes):
        """检查路径是否应该被排除"""
        path_str = str(path)
        for pattern in excludes:
            if '*' in pattern:
                # 简单的通配符匹配
                pattern_parts = pattern.split('*')
                if all(part in path_str for part in pattern_parts if part):
                    return True
            else:
                if pattern in path_str:
                    return True
        return False

    def detect_changes(self):
        """检测文件更改"""
        changes = {
            'backend': {'added': [], 'modified': [], 'deleted': []},
            'frontend': {'added': [], 'modified': [], 'deleted': []}
        }

        # 检查后端文件
        if self.backend_path.exists():
            self.log("🔍 扫描后端文件...", "info")
            for file_path in self.backend_path.rglob('*'):
                if file_path.is_file() and not self.should_exclude(file_path, self.backend_excludes):
                    rel_path = str(file_path.relative_to(self.project_root))
                    current_hash = self.calculate_file_hash(file_path)

                    if current_hash:
                        old_hash = self.file_hashes.get(rel_path)

                        if old_hash is None:
                            changes['backend']['added'].append(rel_path)
                            self.log(f"  ➕ 新增: {rel_path}", "success")
                        elif old_hash != current_hash:
                            changes['backend']['modified'].append(rel_path)
                            self.log(f"  ✏️  修改: {rel_path}", "warning")

                        self.file_hashes[rel_path] = current_hash

        # 检查前端文件
        if self.frontend_path.exists():
            self.log("🔍 扫描前端文件...", "info")
            for file_path in self.frontend_path.rglob('*'):
                if file_path.is_file() and not self.should_exclude(file_path, self.frontend_excludes):
                    rel_path = str(file_path.relative_to(self.project_root))
                    current_hash = self.calculate_file_hash(file_path)

                    if current_hash:
                        old_hash = self.file_hashes.get(rel_path)

                        if old_hash is None:
                            changes['frontend']['added'].append(rel_path)
                            self.log(f"  ➕ 新增: {rel_path}", "success")
                        elif old_hash != current_hash:
                            changes['frontend']['modified'].append(rel_path)
                            self.log(f"  ✏️  修改: {rel_path}", "warning")

                        self.file_hashes[rel_path] = current_hash

        return changes

    def create_backend_package(self):
        """创建后端部署包"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = self.deploy_path / f'backend_deploy_{timestamp}.zip'

        self.log("📦 创建后端部署包...", "info")
        file_count = 0

        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in self.backend_path.rglob('*'):
                if item.is_file() and not self.should_exclude(item, self.backend_excludes):
                    rel_path = item.relative_to(self.project_root)
                    zipf.write(item, rel_path)
                    file_count += 1

                    if file_count % 10 == 0:
                        self.log(f"  已打包 {file_count} 个文件...", "info")

        size_mb = zip_filename.stat().st_size / 1024 / 1024
        self.log(f"✅ 后端部署包创建完成: {zip_filename.name}", "success")
        self.log(f"   文件数: {file_count}, 大小: {size_mb:.2f} MB", "info")

        return zip_filename

    def create_frontend_package(self):
        """创建前端部署包"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = self.deploy_path / f'frontend_deploy_{timestamp}.zip'

        self.log("📦 创建前端部署包...", "info")
        file_count = 0

        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in self.frontend_path.rglob('*'):
                if item.is_file() and not self.should_exclude(item, self.frontend_excludes):
                    rel_path = item.relative_to(self.project_root)
                    zipf.write(item, rel_path)
                    file_count += 1

                    if file_count % 10 == 0:
                        self.log(f"  已打包 {file_count} 个文件...", "info")

        size_mb = zip_filename.stat().st_size / 1024 / 1024
        self.log(f"✅ 前端部署包创建完成: {zip_filename.name}", "success")
        self.log(f"   文件数: {file_count}, 大小: {size_mb:.2f} MB", "info")

        return zip_filename

    def setup_ui(self):
        """设置UI界面"""
        # 标题
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)

        ttk.Label(
            title_frame,
            text="🚀 智能部署工具",
            font=("Arial", 16, "bold")
        ).pack(side=tk.LEFT)

        # 项目路径显示
        path_frame = ttk.LabelFrame(self.root, text="项目路径", padding="10")
        path_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(path_frame, text=f"后端: {self.backend_path}").pack(anchor=tk.W)
        ttk.Label(path_frame, text=f"前端: {self.frontend_path}").pack(anchor=tk.W)
        ttk.Label(path_frame, text=f"部署: {self.deploy_path}").pack(anchor=tk.W)

        # 控制按钮区
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)

        self.check_btn = ttk.Button(
            control_frame,
            text="🔍 检测文件更改",
            command=self.check_changes_handler
        )
        self.check_btn.pack(side=tk.LEFT, padx=5)

        self.pack_backend_btn = ttk.Button(
            control_frame,
            text="📦 打包后端",
            command=self.pack_backend_handler
        )
        self.pack_backend_btn.pack(side=tk.LEFT, padx=5)

        self.pack_frontend_btn = ttk.Button(
            control_frame,
            text="📦 打包前端",
            command=self.pack_frontend_handler
        )
        self.pack_frontend_btn.pack(side=tk.LEFT, padx=5)

        self.pack_all_btn = ttk.Button(
            control_frame,
            text="📦 打包全部",
            command=self.pack_all_handler
        )
        self.pack_all_btn.pack(side=tk.LEFT, padx=5)

        # 自动检测开关
        self.auto_check_var = tk.BooleanVar()
        auto_check = ttk.Checkbutton(
            control_frame,
            text="自动检测 (每30秒)",
            variable=self.auto_check_var,
            command=self.toggle_auto_check
        )
        auto_check.pack(side=tk.LEFT, padx=20)

        # 清空日志按钮
        clear_btn = ttk.Button(
            control_frame,
            text="🗑️ 清空日志",
            command=self.clear_log
        )
        clear_btn.pack(side=tk.RIGHT, padx=5)

        # 日志区域
        log_frame = ttk.LabelFrame(self.root, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=100,
            height=25,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置日志颜色标签
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("error", foreground="red")

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 初始日志
        self.log("=" * 80, "info")
        self.log("智能部署工具已启动", "success")
        self.log("=" * 80, "info")
        self.log("", "info")

    def log(self, message, level="info"):
        """添加日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_message, level)
        self.log_text.see(tk.END)
        self.root.update()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def check_changes_handler(self):
        """检测文件更改处理器"""
        self.status_var.set("正在检测文件更改...")
        self.log("=" * 80, "info")
        self.log("开始检测文件更改...", "info")

        try:
            changes = self.detect_changes()

            backend_total = len(changes['backend']['added']) + len(changes['backend']['modified'])
            frontend_total = len(changes['frontend']['added']) + len(changes['frontend']['modified'])

            self.log("", "info")
            self.log("📊 检测结果汇总:", "success")
            self.log(f"  后端: {backend_total} 个文件有更改", "info")
            self.log(f"  前端: {frontend_total} 个文件有更改", "info")

            if backend_total > 0 or frontend_total > 0:
                self.log("", "info")
                self.log("💡 提示: 发现文件更改，建议重新打包部署", "warning")
                self.save_hash_cache()
            else:
                self.log("", "info")
                self.log("✅ 没有检测到文件更改", "success")

            self.status_var.set("检测完成")

        except Exception as e:
            self.log(f"❌ 检测失败: {e}", "error")
            self.status_var.set("检测失败")

    def pack_backend_handler(self):
        """打包后端处理器"""
        self.status_var.set("正在打包后端...")
        self.log("=" * 80, "info")

        try:
            zip_file = self.create_backend_package()
            self.save_hash_cache()
            self.log("", "info")
            self.log(f"🎉 后端打包成功: {zip_file}", "success")
            self.status_var.set("后端打包完成")
            messagebox.showinfo("成功", f"后端部署包已创建:\n{zip_file.name}")
        except Exception as e:
            self.log(f"❌ 后端打包失败: {e}", "error")
            self.status_var.set("后端打包失败")
            messagebox.showerror("错误", f"后端打包失败:\n{e}")

    def pack_frontend_handler(self):
        """打包前端处理器"""
        self.status_var.set("正在打包前端...")
        self.log("=" * 80, "info")

        try:
            zip_file = self.create_frontend_package()
            self.save_hash_cache()
            self.log("", "info")
            self.log(f"🎉 前端打包成功: {zip_file}", "success")
            self.status_var.set("前端打包完成")
            messagebox.showinfo("成功", f"前端部署包已创建:\n{zip_file.name}")
        except Exception as e:
            self.log(f"❌ 前端打包失败: {e}", "error")
            self.status_var.set("前端打包失败")
            messagebox.showerror("错误", f"前端打包失败:\n{e}")

    def pack_all_handler(self):
        """打包全部处理器"""
        self.status_var.set("正在打包前端和后端...")
        self.log("=" * 80, "info")
        self.log("开始打包前端和后端...", "info")
        self.log("", "info")

        try:
            # 打包后端
            backend_zip = self.create_backend_package()
            self.log("", "info")

            # 打包前端
            frontend_zip = self.create_frontend_package()

            # 保存哈希缓存
            self.save_hash_cache()

            self.log("", "info")
            self.log("🎉 全部打包成功!", "success")
            self.log(f"  后端: {backend_zip.name}", "info")
            self.log(f"  前端: {frontend_zip.name}", "info")
            self.status_var.set("全部打包完成")

            messagebox.showinfo(
                "成功",
                f"部署包已创建:\n\n后端: {backend_zip.name}\n前端: {frontend_zip.name}"
            )
        except Exception as e:
            self.log(f"❌ 打包失败: {e}", "error")
            self.status_var.set("打包失败")
            messagebox.showerror("错误", f"打包失败:\n{e}")

    def toggle_auto_check(self):
        """切换自动检测"""
        if self.auto_check_var.get():
            self.auto_check_enabled = True
            self.check_thread = threading.Thread(target=self.auto_check_loop, daemon=True)
            self.check_thread.start()
            self.log("✅ 自动检测已启用 (每30秒)", "success")
        else:
            self.auto_check_enabled = False
            self.log("⏸️  自动检测已暂停", "warning")

    def auto_check_loop(self):
        """自动检测循环"""
        while self.auto_check_enabled:
            time.sleep(30)  # 每30秒检测一次
            if self.auto_check_enabled:
                self.root.after(0, self.check_changes_handler)

    def run(self):
        """运行GUI"""
        self.root.mainloop()

if __name__ == '__main__':
    tool = SmartDeployTool()
    tool.run()
