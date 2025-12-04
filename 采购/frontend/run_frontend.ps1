# 运行前端启动脚本（Windows PowerShell 版）
Set-Location $PSScriptRoot

if (!(Test-Path "node_modules")) {
  npm install
}

npm run dev