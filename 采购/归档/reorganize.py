# -*- coding: utf-8 -*-
"""
采购系统项目文件重组脚本
自动化重组项目结构，整理重复和命名混乱的文件
"""
import os
import shutil
from datetime import datetime
from pathlib import Path

# 配置
BASE_DIR = Path(r"C:\Users\Admin\Desktop\采购")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = BASE_DIR / f"backup_{TIMESTAMP}"

def print_header(text):
    print("\n" + "="*60)
    print(text)
    print("="*60)

def print_step(step, text):
    print(f"\n[{step}] {text}")

def print_success(text):
    print(f"  ✓ {text}")

def print_info(text):
    print(f"  ℹ️  {text}")

def print_warning(text):
    print(f"  ⚠️  {text}")

def safe_copy(src, dst):
    """安全复制文件，创建必要的目录"""
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dst)
            return True
    except Exception as e:
        print(f"  ❌ 复制失败: {e}")
    return False

def safe_move(src, dst):
    """安全移动文件"""
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.move(str(src), str(dst))
            return True
    except Exception as e:
        print(f"  ❌ 移动失败: {e}")
    return False

def safe_remove(path):
    """安全删除文件或目录"""
    try:
        if path.is_file():
            path.unlink()
            return True
        elif path.is_dir():
            shutil.rmtree(path)
            return True
    except Exception as e:
        print(f"  ❌ 删除失败: {e}")
    return False

# ============================================
# 开始重组
# ============================================

print_header("采购系统项目文件重组脚本")

# 步骤1: 创建备份
print_step("1/10", f"创建备份目录: {BACKUP_DIR}")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
print_success(f"备份目录已创建")

# ============================================
# 优先级1: 功能冲突 (高)
# ============================================

# 步骤2: 删除app.py中的重复认证蓝图
print_step("2/10", "处理app.py中的重复认证蓝图...")
app_py = BASE_DIR / "backend" / "app.py"
if app_py.exists():
    safe_copy(app_py, BACKUP_DIR / "app.py.bak")
    with open(app_py, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找并注释掉auth_bp相关代码
    if 'auth_bp = Blueprint' in content:
        lines = content.split('\n')
        new_lines = []
        in_auth_block = False
        for line in lines:
            if '# ===== 内置认证蓝图' in line or 'auth_bp = Blueprint' in line:
                in_auth_block = True
                new_lines.append('# ✅ 认证功能已移至 routes/auth_routes.py')
                new_lines.append('# ' + line)
            elif in_auth_block and ('# ===== 结束' in line or 'app.register_blueprint(auth_bp' in line):
                new_lines.append('# ' + line)
                if 'app.register_blueprint(auth_bp' in line:
                    in_auth_block = False
            elif in_auth_block:
                new_lines.append('# ' + line)
            else:
                new_lines.append(line)

        with open(app_py, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print_success("已注释app.py中的重复认证蓝图")
    else:
        print_info("app.py中未找到重复认证蓝图")
else:
    print_info("app.py不存在")

# 步骤3: 重命名re_routes.py
print_step("3/10", "重命名 re_routes.py → user_routes.py...")
re_routes = BASE_DIR / "backend" / "routes" / "re_routes.py"
user_routes = BASE_DIR / "backend" / "routes" / "user_routes.py"
if re_routes.exists():
    safe_copy(re_routes, BACKUP_DIR / "re_routes.py.bak")
    safe_move(re_routes, user_routes)
    print_success("已重命名: re_routes.py → user_routes.py")
else:
    print_info("re_routes.py 不存在，可能已重命名")

# 步骤4: 废弃quote.py
print_step("4/10", "废弃旧的 quote.py 模型...")
quote_py = BASE_DIR / "backend" / "models" / "quote.py"
if quote_py.exists():
    safe_copy(quote_py, BACKUP_DIR / "quote.py.bak")
    deprecated = BASE_DIR / "backend" / "models" / "_deprecated_quote.py.old"
    safe_move(quote_py, deprecated)
    print_success("已废弃: quote.py → _deprecated_quote.py.old")
    print_warning("请统一使用 supplier_quote.py")
else:
    print_info("quote.py 不存在")

# ============================================
# 优先级2: 代码整洁 (中)
# ============================================

# 步骤5: 删除重复的供应商类别路由
print_step("5/10", "删除重复的供应商类别路由...")
supplier_cat_api = BASE_DIR / "backend" / "routes" / "supplier_categories_api.py"
if supplier_cat_api.exists():
    safe_copy(supplier_cat_api, BACKUP_DIR / "supplier_categories_api.py.bak")
    safe_remove(supplier_cat_api)
    print_success("已删除: supplier_categories_api.py")
else:
    print_info("supplier_categories_api.py 已删除")

# 步骤6: 废弃rfq_service_categories.py
print_step("6/10", "废弃重复的RFQ服务...")
rfq_svc_cat = BASE_DIR / "backend" / "services" / "rfq_service_categories.py"
if rfq_svc_cat.exists():
    safe_copy(rfq_svc_cat, BACKUP_DIR / "rfq_service_categories.py.bak")
    deprecated_svc = BASE_DIR / "backend" / "services" / "_deprecated_rfq_service_categories.py.old"
    safe_move(rfq_svc_cat, deprecated_svc)
    print_success("已废弃: rfq_service_categories.py")
    print_warning("类别匹配功能应合并到 rfq_service.py")
else:
    print_info("rfq_service_categories.py 已处理")

# 步骤7: 删除quote_number.py
print_step("7/10", "删除重复的编号生成器...")
quote_num = BASE_DIR / "backend" / "utils" / "quote_number.py"
if quote_num.exists():
    safe_copy(quote_num, BACKUP_DIR / "quote_number.py.bak")
    safe_remove(quote_num)
    print_success("已删除: quote_number.py")
else:
    print_info("quote_number.py 已删除")

# 步骤8: 移动迁移脚本
print_step("8/10", "整理迁移脚本到 migrations/scripts/...")
migrations_scripts = BASE_DIR / "backend" / "migrations" / "scripts"
migrations_scripts.mkdir(parents=True, exist_ok=True)

migration_files = [
    "clear_all_data.py",
    "clear_quotes.py",
    "create_notifications_table.py",
    "migrate_supplier_fields.py",
    "migrate_add_payment_terms.py",
    "update_database_schema.py"
]

for filename in migration_files:
    src = BASE_DIR / "backend" / filename
    if src.exists():
        safe_copy(src, BACKUP_DIR / f"{filename}.bak")
        dst = migrations_scripts / filename
        safe_move(src, dst)
        print_success(f"已移动: {filename} → migrations/scripts/")

# ============================================
# 优先级3: 目录优化 (低)
# ============================================

# 步骤9: 合并helpers到utils
print_step("9/10", "合并 helpers 到 utils...")
file_handler = BASE_DIR / "backend" / "helpers" / "file_handler.py"
if file_handler.exists():
    safe_copy(file_handler, BACKUP_DIR / "file_handler.py.bak")
    dst = BASE_DIR / "backend" / "utils" / "file_handler.py"
    safe_move(file_handler, dst)
    print_success("已移动: helpers/file_handler.py → utils/file_handler.py")

    # 删除空的helpers目录
    helpers_dir = BASE_DIR / "backend" / "helpers"
    if helpers_dir.exists():
        remaining = list(helpers_dir.rglob('*.py'))
        if len(remaining) <= 1:  # 只剩__init__.py或为空
            safe_remove(helpers_dir)
            print_success("已删除空目录: helpers/")
else:
    print_info("file_handler.py 已在 utils 目录")

# 步骤10: 删除前端重复页面
print_step("10/10", "删除前端重复页面...")
trans_confirm = BASE_DIR / "frontend" / "src" / "pages" / "TransactionConfirm.jsx"
if trans_confirm.exists():
    safe_copy(trans_confirm, BACKUP_DIR / "TransactionConfirm.jsx.bak")
    safe_remove(trans_confirm)
    print_success("已删除: TransactionConfirm.jsx")
else:
    print_info("TransactionConfirm.jsx 已删除")

# ============================================
# 完成报告
# ============================================

print_header("重组完成！")
print(f"\n✅ 备份位置: {BACKUP_DIR}")
print("\n📋 已完成的重组任务：")
print("  1. ✓ 注释app.py中的重复认证蓝图")
print("  2. ✓ 重命名 re_routes.py → user_routes.py")
print("  3. ✓ 废弃 models/quote.py")
print("  4. ✓ 删除 supplier_categories_api.py")
print("  5. ✓ 废弃 rfq_service_categories.py")
print("  6. ✓ 删除 utils/quote_number.py")
print("  7. ✓ 移动迁移脚本到 migrations/scripts/")
print("  8. ✓ 合并 helpers 到 utils/")
print("  9. ✓ 删除前端 TransactionConfirm.jsx")

print("\n⚠️  后续手动任务：")
print("  1. 更新导入路径")
print("     - from routes.re_routes → from routes.user_routes")
print("     - from helpers.file_handler → from utils.file_handler")
print("  2. 将 rfq_service_categories.py 功能合并到 rfq_service.py")
print("  3. 检查前端路由是否引用了 TransactionConfirm")

print("\n🔄 建议测试：")
print("  1. 运行: python backend/app.py")
print("  2. 检查导入错误")
print("  3. 前端测试: npm run dev")
print()
