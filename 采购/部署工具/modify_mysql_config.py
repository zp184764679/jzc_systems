# -*- coding: utf-8 -*-
"""
自动修改MySQL配置文件
添加bind-address = 0.0.0.0
"""
import os
import shutil
from datetime import datetime

MY_INI_PATH = r"C:\ProgramData\MySQL\MySQL Server 9.0\my.ini"

print("=" * 60)
print("🔧 修改MySQL配置文件")
print("=" * 60)
print()

# 检查文件是否存在
if not os.path.exists(MY_INI_PATH):
    print(f"❌ 未找到配置文件: {MY_INI_PATH}")
    exit(1)

# 备份配置文件
backup_path = f"{MY_INI_PATH}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
try:
    shutil.copy2(MY_INI_PATH, backup_path)
    print(f"✅ 已备份到: {backup_path}")
except Exception as e:
    print(f"⚠️  备份失败: {e}")

# 读取配置文件
try:
    with open(MY_INI_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
except UnicodeDecodeError:
    with open(MY_INI_PATH, 'r', encoding='gbk') as f:
        content = f.read()

# 检查是否已有bind-address配置
if 'bind-address' in content:
    print("⚠️  配置文件中已存在bind-address配置")
    print("当前配置:")
    for line in content.split('\n'):
        if 'bind-address' in line:
            print(f"  {line}")
    print()
    response = input("是否要更新配置? (y/n): ")
    if response.lower() != 'y':
        print("取消修改")
        exit(0)
    # 更新现有配置
    content = content.replace('bind-address = 127.0.0.1', 'bind-address = 0.0.0.0')
    content = content.replace('bind-address=127.0.0.1', 'bind-address = 0.0.0.0')
else:
    # 在port=3306后面添加配置
    content = content.replace(
        'port=3306',
        'port=3306\n\n# Allow connections from any IP address (0.0.0.0 = all interfaces)\nbind-address = 0.0.0.0\nmysqlx-bind-address = 0.0.0.0'
    )

# 写入配置文件
try:
    with open(MY_INI_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ MySQL配置文件已更新")
    print()
    print("已添加配置:")
    print("  bind-address = 0.0.0.0")
    print("  mysqlx-bind-address = 0.0.0.0")
    print()
    print("⚠️  需要重启MySQL服务才能生效!")
except PermissionError:
    print("❌ 权限不足,无法修改配置文件")
    print()
    print("请使用以下方法之一:")
    print("1. 以管理员身份运行此脚本")
    print("2. 手动修改配置文件:")
    print(f"   文件: {MY_INI_PATH}")
    print("   在 [mysqld] 部分添加:")
    print("   bind-address = 0.0.0.0")
    print("   mysqlx-bind-address = 0.0.0.0")
    exit(1)
except Exception as e:
    print(f"❌ 写入失败: {e}")
    exit(1)

print()
print("=" * 60)
