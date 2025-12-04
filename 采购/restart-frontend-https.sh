#!/bin/bash
echo "正在重启前端服务以启用HTTPS..."
sudo systemctl restart caigou-frontend.service
sleep 3
sudo systemctl status caigou-frontend.service --no-pager
echo ""
echo "检查5000端口..."
ss -tlnp | grep :5000
echo ""
echo "完成！现在可以通过 https://61.145.212.28:5000 访问"
