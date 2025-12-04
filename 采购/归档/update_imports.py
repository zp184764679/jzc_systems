# -*- coding: utf-8 -*-
"""
自动更新导入路径脚本
更新重组后的所有导入路径
"""
import os
import re
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Admin\Desktop\采购\backend")

# 导入替换规则
REPLACEMENTS = [
    # re_routes → user_routes
    (r'from\s+routes\.re_routes\s+import', 'from routes.user_routes import'),
    (r'import\s+routes\.re_routes', 'import routes.user_routes'),

    # helpers.file_handler → utils.file_handler
    (r'from\s+helpers\.file_handler\s+import', 'from utils.file_handler import'),
    (r'import\s+helpers\.file_handler', 'import utils.file_handler'),

    # models.quote → models.supplier_quote (如果有的话)
    (r'from\s+models\.quote\s+import\s+Quote\b', 'from models.supplier_quote import SupplierQuote'),
    (r'import\s+models\.quote\b', 'import models.supplier_quote'),
]

def update_file_imports(file_path):
    """更新单个文件中的导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = []

        # 应用所有替换规则
        for pattern, replacement in REPLACEMENTS:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                changes.append((pattern, replacement, len(matches)))

        # 如果有变更，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes

        return None

    except Exception as e:
        print(f"  ❌ 处理失败 {file_path}: {e}")
        return None

def scan_and_update():
    """扫描并更新所有Python文件"""
    print("="*60)
    print("自动更新导入路径")
    print("="*60)

    updated_files = []
    total_changes = 0

    # 遍历所有Python文件（排除venv等）
    for py_file in BASE_DIR.rglob('*.py'):
        # 跳过虚拟环境和备份
        if 'venv' in str(py_file) or '__pycache__' in str(py_file) or 'backup_' in str(py_file):
            continue

        changes = update_file_imports(py_file)
        if changes:
            updated_files.append((py_file, changes))
            total_changes += sum(count for _, _, count in changes)

    # 打印结果
    print(f"\n✅ 扫描完成！")
    print(f"   更新文件数: {len(updated_files)}")
    print(f"   总替换次数: {total_changes}")

    if updated_files:
        print("\n📋 更新详情：\n")
        for file_path, changes in updated_files:
            rel_path = file_path.relative_to(BASE_DIR)
            print(f"✓ {rel_path}")
            for pattern, replacement, count in changes:
                print(f"  - {pattern.replace(r'\s+', ' ')} ({count}次)")
                print(f"    → {replacement}")
    else:
        print("\nℹ️  没有发现需要更新的导入")

    return len(updated_files)

if __name__ == '__main__':
    count = scan_and_update()
    print("\n" + "="*60)
    if count > 0:
        print(f"✅ 成功更新 {count} 个文件的导入路径！")
    else:
        print("✅ 所有导入路径已是最新！")
    print("="*60)
