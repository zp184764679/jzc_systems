# -*- coding: utf-8 -*-
# 采购系统项目文件重组脚本
# 自动化重组项目结构，整理重复和命名混乱的文件

$ErrorActionPreference = "Stop"
$baseDir = "C:\Users\Admin\Desktop\采购"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "采购系统项目文件重组脚本" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 创建备份
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "$baseDir\backup_$timestamp"
Write-Host "[1/10] 创建备份目录: $backupDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# ============================================
# 优先级1: 功能冲突 (高)
# ============================================

Write-Host "`n[2/10] 处理认证路由重复问题..." -ForegroundColor Green
# 备份app.py
Copy-Item "$baseDir\backend\app.py" "$backupDir\app.py.bak"
Write-Host "  ✓ 已备份 app.py" -ForegroundColor Gray

# 读取app.py并删除auth_bp蓝图 (第99-210行)
$appContent = Get-Content "$baseDir\backend\app.py" -Raw
if ($appContent -match "(?s)# ===== 内置认证蓝图.*?# ===== 结束内置认证蓝图 =====") {
    $newContent = $appContent -replace "(?s)# ===== 内置认证蓝图.*?# ===== 结束内置认证蓝图 =====", "# ✅ 认证功能已移至 routes/auth_routes.py"
    Set-Content "$baseDir\backend\app.py" $newContent -Encoding UTF8
    Write-Host "  ✓ 已删除app.py中的重复认证蓝图" -ForegroundColor Gray
} else {
    Write-Host "  ℹ️  app.py中未找到重复认证蓝图标记，跳过" -ForegroundColor DarkGray
}

Write-Host "`n[3/10] 重命名 re_routes.py 为 user_routes.py..." -ForegroundColor Green
if (Test-Path "$baseDir\backend\routes\re_routes.py") {
    Copy-Item "$baseDir\backend\routes\re_routes.py" "$backupDir\re_routes.py.bak"
    Move-Item "$baseDir\backend\routes\re_routes.py" "$baseDir\backend\routes\user_routes.py" -Force
    Write-Host "  ✓ 已重命名: re_routes.py → user_routes.py" -ForegroundColor Gray
} else {
    Write-Host "  ℹ️  re_routes.py 不存在，可能已重命名" -ForegroundColor DarkGray
}

Write-Host "`n[4/10] 废弃旧的 quote.py 模型..." -ForegroundColor Green
if (Test-Path "$baseDir\backend\models\quote.py") {
    Copy-Item "$baseDir\backend\models\quote.py" "$backupDir\quote.py.bak"
    Move-Item "$baseDir\backend\models\quote.py" "$baseDir\backend\models\_deprecated_quote.py.old" -Force
    Write-Host "  ✓ 已废弃: quote.py → _deprecated_quote.py.old" -ForegroundColor Gray
    Write-Host "  ⚠️  请统一使用 supplier_quote.py" -ForegroundColor Yellow
} else {
    Write-Host "  ℹ️  quote.py 不存在，跳过" -ForegroundColor DarkGray
}

# ============================================
# 优先级2: 代码整洁 (中)
# ============================================

Write-Host "`n[5/10] 删除重复的供应商类别路由..." -ForegroundColor Green
if (Test-Path "$baseDir\backend\routes\supplier_categories_api.py") {
    Copy-Item "$baseDir\backend\routes\supplier_categories_api.py" "$backupDir\supplier_categories_api.py.bak"
    Remove-Item "$baseDir\backend\routes\supplier_categories_api.py" -Force
    Write-Host "  ✓ 已删除: supplier_categories_api.py (请使用supplier_category_routes.py)" -ForegroundColor Gray
} else {
    Write-Host "  ℹ️  supplier_categories_api.py 已删除" -ForegroundColor DarkGray
}

Write-Host "`n[6/10] 删除重复的RFQ服务..." -ForegroundColor Green
if (Test-Path "$baseDir\backend\services\rfq_service_categories.py") {
    Copy-Item "$baseDir\backend\services\rfq_service_categories.py" "$backupDir\rfq_service_categories.py.bak"
    Move-Item "$baseDir\backend\services\rfq_service_categories.py" "$baseDir\backend\services\_deprecated_rfq_service_categories.py.old" -Force
    Write-Host "  ✓ 已废弃: rfq_service_categories.py" -ForegroundColor Gray
    Write-Host "  ⚠️  类别匹配功能应合并到 rfq_service.py" -ForegroundColor Yellow
} else {
    Write-Host "  ℹ️  rfq_service_categories.py 已处理" -ForegroundColor DarkGray
}

Write-Host "`n[7/10] 删除重复的编号生成器..." -ForegroundColor Green
if (Test-Path "$baseDir\backend\utils\quote_number.py") {
    Copy-Item "$baseDir\backend\utils\quote_number.py" "$backupDir\quote_number.py.bak"
    Remove-Item "$baseDir\backend\utils\quote_number.py" -Force
    Write-Host "  ✓ 已删除: quote_number.py (请使用code_generator.py)" -ForegroundColor Gray
} else {
    Write-Host "  ℹ️  quote_number.py 已删除" -ForegroundColor DarkGray
}

Write-Host "`n[8/10] 整理迁移脚本到 migrations/scripts/..." -ForegroundColor Green
$migrationsScriptsDir = "$baseDir\backend\migrations\scripts"
if (-not (Test-Path $migrationsScriptsDir)) {
    New-Item -ItemType Directory -Path $migrationsScriptsDir -Force | Out-Null
    Write-Host "  ✓ 已创建目录: migrations/scripts/" -ForegroundColor Gray
}

$migrationScripts = @(
    "clear_all_data.py",
    "clear_quotes.py",
    "create_notifications_table.py",
    "migrate_supplier_fields.py",
    "migrate_add_payment_terms.py",
    "update_database_schema.py"
)

foreach ($script in $migrationScripts) {
    $sourcePath = "$baseDir\backend\$script"
    if (Test-Path $sourcePath) {
        Copy-Item $sourcePath "$backupDir\$script.bak"
        Move-Item $sourcePath "$migrationsScriptsDir\$script" -Force
        Write-Host "  ✓ 已移动: $script → migrations/scripts/" -ForegroundColor Gray
    }
}

# ============================================
# 优先级3: 目录优化 (低)
# ============================================

Write-Host "`n[9/10] 合并 helpers 到 utils..." -ForegroundColor Green
if (Test-Path "$baseDir\backend\helpers\file_handler.py") {
    Copy-Item "$baseDir\backend\helpers\file_handler.py" "$backupDir\file_handler.py.bak"
    Move-Item "$baseDir\backend\helpers\file_handler.py" "$baseDir\backend\utils\file_handler.py" -Force
    Write-Host "  ✓ 已移动: helpers/file_handler.py → utils/file_handler.py" -ForegroundColor Gray

    # 尝试删除空的helpers目录
    if ((Get-ChildItem "$baseDir\backend\helpers" -Recurse | Where-Object { $_.PSIsContainer -eq $false }).Count -eq 1) {
        Remove-Item "$baseDir\backend\helpers" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ 已删除空目录: helpers/" -ForegroundColor Gray
    }
} else {
    Write-Host "  ℹ️  file_handler.py 已在 utils 目录" -ForegroundColor DarkGray
}

Write-Host "`n[10/10] 删除前端重复页面..." -ForegroundColor Green
if (Test-Path "$baseDir\frontend\src\pages\TransactionConfirm.jsx") {
    Copy-Item "$baseDir\frontend\src\pages\TransactionConfirm.jsx" "$backupDir\TransactionConfirm.jsx.bak"
    Remove-Item "$baseDir\frontend\src\pages\TransactionConfirm.jsx" -Force
    Write-Host "  ✓ 已删除: TransactionConfirm.jsx (请使用TransactionConfirmPage.jsx)" -ForegroundColor Gray
} else {
    Write-Host "  ℹ️  TransactionConfirm.jsx 已删除" -ForegroundColor DarkGray
}

# ============================================
# 完成报告
# ============================================

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "重组完成！" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ 备份位置: $backupDir" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 已完成的重组任务：" -ForegroundColor White
Write-Host "  1. ✓ 删除app.py中的重复认证蓝图" -ForegroundColor Gray
Write-Host "  2. ✓ 重命名 re_routes.py → user_routes.py" -ForegroundColor Gray
Write-Host "  3. ✓ 废弃 models/quote.py（使用supplier_quote.py）" -ForegroundColor Gray
Write-Host "  4. ✓ 删除 supplier_categories_api.py" -ForegroundColor Gray
Write-Host "  5. ✓ 废弃 rfq_service_categories.py" -ForegroundColor Gray
Write-Host "  6. ✓ 删除 utils/quote_number.py" -ForegroundColor Gray
Write-Host "  7. ✓ 移动迁移脚本到 migrations/scripts/" -ForegroundColor Gray
Write-Host "  8. ✓ 合并 helpers/file_handler.py 到 utils/" -ForegroundColor Gray
Write-Host "  9. ✓ 删除前端 TransactionConfirm.jsx" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  后续手动任务（需要代码审查）：" -ForegroundColor Yellow
Write-Host "  1. 更新所有导入路径" -ForegroundColor Gray
Write-Host "     - re_routes → user_routes" -ForegroundColor DarkGray
Write-Host "     - helpers.file_handler → utils.file_handler" -ForegroundColor DarkGray
Write-Host "  2. 将 rfq_service_categories.py 的功能合并到 rfq_service.py" -ForegroundColor Gray
Write-Host "  3. 检查前端路由是否引用了 TransactionConfirm" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 项目新结构概览：" -ForegroundColor White
Write-Host "  backend/" -ForegroundColor Cyan
Write-Host "    ├── models/ (16个，删除1个重复)" -ForegroundColor Gray
Write-Host "    ├── routes/ (13个，删除1个重复)" -ForegroundColor Gray
Write-Host "    ├── services/ (4个，废弃1个重复)" -ForegroundColor Gray
Write-Host "    ├── utils/ (7个，删除1个+新增1个)" -ForegroundColor Gray
Write-Host "    ├── tasks/" -ForegroundColor Gray
Write-Host "    ├── constants/" -ForegroundColor Gray
Write-Host "    └── migrations/" -ForegroundColor Gray
Write-Host "        └── scripts/ (6个迁移脚本)" -ForegroundColor Gray
Write-Host ""
Write-Host "🔄 建议下一步：" -ForegroundColor White
Write-Host "  1. 运行: python backend/app.py (测试后端)" -ForegroundColor Gray
Write-Host "  2. 检查导入错误并修复" -ForegroundColor Gray
Write-Host "  3. 前端测试: npm run dev" -ForegroundColor Gray
Write-Host ""
