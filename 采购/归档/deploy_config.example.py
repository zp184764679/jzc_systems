# -*- coding: utf-8 -*-
"""
部署配置文件（示例）
复制此文件为 deploy_config.py 并填写你的服务器信息
"""

# 服务器SSH配置
SERVER_CONFIG = {
    'host': '61.145.212.28',
    'port': 22,
    'username': '',  # 👈 填写SSH用户名，例如：'root' 或 'admin'
    'password': '',  # 👈 填写SSH密码（不推荐，建议使用密钥）

    # 或者使用SSH密钥（推荐）
    # 'key_filename': r'C:\Users\YourName\.ssh\id_rsa',  # SSH私钥路径
}

# 路径配置
LOCAL_PATH = r'C:\Users\Admin\Desktop\采购\backend'  # 本地backend目录
REMOTE_PATH = '/opt/采购/backend'  # 服务器上的目标路径

# Flask服务配置
FLASK_CONFIG = {
    'restart_command': 'cd {remote_path} && nohup python3 app.py > flask.log 2>&1 &',
    'check_port': 5001,
}
