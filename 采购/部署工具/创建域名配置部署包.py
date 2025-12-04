#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建域名配置版本的部署包

更新内容：
1. backend/.env: BACKEND_DOMAIN=http://api.jingzhicheng.com.cn
2. frontend/src/pages/Login.jsx: 使用域名替代IP:端口
"""

import os
import zipfile
from pathlib import Path
from datetime import datetime

def should_exclude(file_path, exclude_patterns):
    """检查文件是否应该被排除"""
    path_str = str(file_path)
    for pattern in exclude_patterns:
        if pattern in path_str:
            return True
    return False

def create_backend_package():
    """创建后端部署包"""
    print("\n" + "="*80)
    print("📦 创建后端部署包（域名配置版本）")
    print("="*80)

    root_dir = Path(r'C:\Users\Admin\Desktop\采购')
    backend_dir = root_dir / 'backend'
    output_dir = root_dir / '部署工具'

    # 后端排除规则
    excludes = [
        '__pycache__',
        '.pyc',
        '.git',
        '.vscode',
        'node_modules',
        'logs',
        'venv',
        '.log',
        '.pytest_cache',
        '.idea',
        'migrations',  # 可选：如果不需要迁移文件
    ]

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = output_dir / f'backend_domain_config_{timestamp}.zip'

    file_count = 0
    total_size = 0

    print(f"\n📂 扫描目录: {backend_dir}")

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in backend_dir.rglob('*'):
            if item.is_file() and not should_exclude(item, excludes):
                rel_path = item.relative_to(root_dir)
                zipf.write(item, rel_path)
                file_size = item.stat().st_size
                total_size += file_size
                file_count += 1

                # 显示关键文件
                if '.env' in item.name or 'app.py' in item.name:
                    print(f"  ✅ 包含关键文件: {rel_path} ({file_size:,} bytes)")

    # 获取zip文件大小
    zip_size = zip_filename.stat().st_size

    print(f"\n✅ 后端打包完成！")
    print(f"   文件数量: {file_count}")
    print(f"   原始大小: {total_size:,} bytes ({total_size/1024:.2f} KB)")
    print(f"   压缩后大小: {zip_size:,} bytes ({zip_size/1024:.2f} KB)")
    print(f"   压缩率: {(1 - zip_size/total_size)*100:.1f}%")
    print(f"   保存位置: {zip_filename}")

    return str(zip_filename)

def create_frontend_package():
    """创建前端部署包"""
    print("\n" + "="*80)
    print("📦 创建前端部署包（域名配置版本）")
    print("="*80)

    root_dir = Path(r'C:\Users\Admin\Desktop\采购')
    frontend_dir = root_dir / 'frontend'
    output_dir = root_dir / '部署工具'

    # 前端排除规则
    excludes = [
        'node_modules',
        'dist',
        'build',
        '.git',
        '.vscode',
        '.idea',
        '.DS_Store',
        '.vite',
        'coverage',
    ]

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = output_dir / f'frontend_domain_config_{timestamp}.zip'

    file_count = 0
    total_size = 0

    print(f"\n📂 扫描目录: {frontend_dir}")

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in frontend_dir.rglob('*'):
            if item.is_file() and not should_exclude(item, excludes):
                rel_path = item.relative_to(root_dir)
                zipf.write(item, rel_path)
                file_size = item.stat().st_size
                total_size += file_size
                file_count += 1

                # 显示关键文件
                if 'Login.jsx' in item.name:
                    print(f"  ✅ 包含关键文件: {rel_path} ({file_size:,} bytes)")

    # 获取zip文件大小
    zip_size = zip_filename.stat().st_size

    print(f"\n✅ 前端打包完成！")
    print(f"   文件数量: {file_count}")
    print(f"   原始大小: {total_size:,} bytes ({total_size/1024:.2f} KB)")
    print(f"   压缩后大小: {zip_size:,} bytes ({zip_size/1024:.2f} KB)")
    print(f"   压缩率: {(1 - zip_size/total_size)*100:.1f}%")
    print(f"   保存位置: {zip_filename}")

    return str(zip_filename)

def create_deployment_summary(backend_zip, frontend_zip):
    """创建部署摘要文档"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    summary = f"""================================================================================
【最新】域名配置版本部署包
================================================================================

创建时间: {timestamp}
版本说明: 企业微信域名配置版本

================================================================================
📦 生成的部署包
================================================================================

1. 后端部署包
   文件名: {Path(backend_zip).name}
   位置: {backend_zip}

2. 前端部署包
   文件名: {Path(frontend_zip).name}
   位置: {frontend_zip}

================================================================================
🔧 本次更新内容
================================================================================

1. 后端配置更新 (backend/.env)
   ---------------------------------------------------------------
   修改前: BACKEND_DOMAIN=http://61.145.212.28:5001
   修改后: BACKEND_DOMAIN=http://api.jingzhicheng.com.cn

   原因: 企业微信OAuth2.0要求回调域名必须是域名，不能是IP地址

2. 前端配置更新 (frontend/src/pages/Login.jsx)
   ---------------------------------------------------------------
   修改前:
   const apiBaseURL = window.location.hostname === 'localhost'
     ? "http://localhost:5001"
     : `http://${{window.location.hostname}}:5001`;

   修改后:
   const apiBaseURL = window.location.hostname === 'localhost'
     ? "http://localhost:5001"
     : "http://api.jingzhicheng.com.cn";

   原因: 前端API调用需要指向域名而不是IP地址

================================================================================
📋 部署前的必要准备工作
================================================================================

⚠️ 重要：在部署这些包之前，必须先完成以下配置：

步骤1: 配置DNS解析
---------------------------------------------------------------
登录域名管理后台（如阿里云、腾讯云等）

添加A记录:
  主机记录: api
  记录类型: A
  记录值: 61.145.212.28
  TTL: 600秒

完成后，api.jingzhicheng.com.cn 将解析到 61.145.212.28

验证方法:
  ping api.jingzhicheng.com.cn
  # 应该解析到 61.145.212.28


步骤2: 配置服务器Nginx
---------------------------------------------------------------
SSH登录服务器后，编辑Nginx配置:

sudo nano /etc/nginx/sites-available/caigou

添加以下配置:

```nginx
# 前端服务（端口9000）
server {{
    listen 9000;
    server_name 61.145.212.28;

    root /home/username/caigou_system/frontend/dist;
    index index.html;

    location / {{
        try_files $uri $uri/ /index.html;
    }}
}}

# API服务（端口80，使用域名）
server {{
    listen 80;
    server_name api.jingzhicheng.com.cn;

    # API代理到后端
    location /api/ {{
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # 健康检查
    location /health {{
        return 200 "OK";
        add_header Content-Type text/plain;
    }}
}}
```

测试并重启Nginx:
  sudo nginx -t
  sudo systemctl restart nginx


步骤3: 开放服务器端口80
---------------------------------------------------------------
确保防火墙开放了80端口:

CentOS/RHEL:
  sudo firewall-cmd --zone=public --add-port=80/tcp --permanent
  sudo firewall-cmd --reload

Ubuntu:
  sudo ufw allow 80/tcp
  sudo ufw reload


步骤4: 配置企业微信后台
---------------------------------------------------------------
1. 登录企业微信管理后台: https://work.weixin.qq.com/

2. 进入"应用管理" → 找到你的应用（AGENT_ID: 1000010）

3. 配置"网页授权及JS-SDK":
   授权回调域: api.jingzhicheng.com.cn
   （注意：不要加 http:// 和端口号，只填域名）

4. 保存配置

================================================================================
🚀 部署步骤
================================================================================

完成上述准备工作后，按以下步骤部署：

步骤1: 上传部署包
---------------------------------------------------------------
使用WinSCP上传两个zip文件到服务器:
  - {Path(backend_zip).name}
  - {Path(frontend_zip).name}

上传到服务器目录: /home/username/


步骤2: 部署后端
---------------------------------------------------------------
SSH登录服务器后:

# 解压后端
cd /home/username
unzip {Path(backend_zip).name}

# 进入后端目录
cd ~/caigou_system/backend

# 确认.env配置正确
cat .env | grep BACKEND_DOMAIN
# 应该显示: BACKEND_DOMAIN=http://api.jingzhicheng.com.cn

# 安装依赖（如果需要）
pip install -r requirements.txt

# 停止旧服务
pkill -f "python.*app.py"

# 启动新服务
nohup python app.py > logs/app.log 2>&1 &

# 查看日志
tail -f logs/app.log


步骤3: 部署前端
---------------------------------------------------------------
# 解压前端
cd /home/username
unzip {Path(frontend_zip).name}

# 进入前端目录
cd ~/caigou_system/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 确认Nginx配置正确并重启
sudo nginx -t
sudo systemctl restart nginx


步骤4: 验证部署
---------------------------------------------------------------
1. 测试DNS解析:
   ping api.jingzhicheng.com.cn
   # 应该解析到 61.145.212.28

2. 测试Nginx健康检查:
   curl http://api.jingzhicheng.com.cn/health
   # 应该返回 "OK"

3. 测试API端点:
   curl http://api.jingzhicheng.com.cn/api/v1/auth/wework/qr-authorize
   # 应该返回授权URL

4. 测试前端访问:
   在浏览器访问: http://61.145.212.28:9000/login
   点击"企业微信扫码登录"
   应该能正常弹出二维码

================================================================================
🧪 测试清单
================================================================================

☐ DNS解析正常（ping api.jingzhicheng.com.cn 解析到 61.145.212.28）
☐ Nginx配置正确（curl http://api.jingzhicheng.com.cn/health 返回 "OK"）
☐ API端点可访问（curl 授权URL成功）
☐ 后端配置正确（BACKEND_DOMAIN使用域名）
☐ 企业微信配置正确（授权回调域 = api.jingzhicheng.com.cn）
☐ 前端能访问API（浏览器F12查看Network请求）
☐ 扫码登录正常（能弹出二维码并成功登录）

================================================================================
📊 完整通信流程
================================================================================

修改后的流程:

1. 用户访问前端
   http://61.145.212.28:9000/login

2. 点击"企业微信扫码登录"
   前端请求: http://api.jingzhicheng.com.cn/api/v1/auth/wework/qr-authorize

3. Nginx接收请求
   api.jingzhicheng.com.cn:80 → 代理到 localhost:5001

4. 后端返回授权URL
   包含回调地址: http://api.jingzhicheng.com.cn/api/v1/auth/wework/callback

5. 跳转到企业微信
   用户扫码授权

6. 企业微信回调
   回调地址: http://api.jingzhicheng.com.cn/api/v1/auth/wework/callback
   ✅ 域名符合要求！

7. Nginx代理
   api.jingzhicheng.com.cn:80 → localhost:5001

8. 后端处理
   获取用户信息，完成登录

9. 登录成功！

================================================================================
🆘 故障排查
================================================================================

问题1: DNS解析不生效
---------------------------------------------------------------
解决方法:
1. 等待DNS生效（最多24小时）
2. 清除本地DNS缓存:
   Windows: ipconfig /flushdns
   Linux: sudo systemd-resolve --flush-caches

问题2: curl能访问，浏览器不能
---------------------------------------------------------------
解决方法:
清除浏览器缓存: Ctrl+Shift+Delete

问题3: 还是显示CORS错误
---------------------------------------------------------------
解决方法:
检查后端app.py的CORS配置，确保包含域名:
   origins=["http://api.jingzhicheng.com.cn", ...]

问题4: 企业微信回调失败
---------------------------------------------------------------
解决方法:
1. 确认企业微信后台配置的域名正确
2. 确认域名能从外网访问
3. 检查Nginx日志: tail -f /var/log/nginx/error.log

问题5: 提示"redirect_uri域名与后台配置不一致"
---------------------------------------------------------------
解决方法:
后端生成的redirect_uri必须与企业微信后台配置的域名一致

================================================================================
📝 重要提示
================================================================================

1. 域名必须备案（如果服务器在中国大陆）

2. 企业微信回调域名配置注意事项:
   - 只填写域名，不要加 http:// 或 https://
   - 不要加端口号
   - 只填写: api.jingzhicheng.com.cn

3. 部署顺序很重要:
   第一步: 配置DNS
   第二步: 配置Nginx
   第三步: 配置企业微信后台
   第四步: 部署后端和前端

4. 建议先在本地测试DNS解析成功后再部署

================================================================================
✅ 部署完成后
================================================================================

完成部署并测试成功后，企业微信扫码登录功能应该能正常工作了！

关键改变:
❌ 旧方案: 使用IP地址 61.145.212.28:5001 → 企业微信不接受
✅ 新方案: 使用域名 api.jingzhicheng.com.cn → 企业微信接受

================================================================================
"""

    # 保存摘要文件
    output_dir = Path(r'C:\Users\Admin\Desktop\采购\部署工具')
    summary_file = output_dir / f'域名配置部署摘要_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f"\n📄 部署摘要已保存: {summary_file}")

    return str(summary_file)

def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 开始创建域名配置版本的部署包")
    print("="*80)
    print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 创建后端包
        backend_zip = create_backend_package()

        # 创建前端包
        frontend_zip = create_frontend_package()

        # 创建部署摘要
        summary_file = create_deployment_summary(backend_zip, frontend_zip)

        # 最终总结
        print("\n" + "="*80)
        print("✅ 所有部署包创建完成！")
        print("="*80)
        print(f"\n📦 生成的文件:")
        print(f"   1. 后端: {Path(backend_zip).name}")
        print(f"   2. 前端: {Path(frontend_zip).name}")
        print(f"   3. 摘要: {Path(summary_file).name}")
        print(f"\n📂 文件位置: C:\\Users\\Admin\\Desktop\\采购\\部署工具\\")
        print(f"\n⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "="*80)
        print("📋 下一步:")
        print("="*80)
        print("1. 先完成DNS和Nginx配置（详见摘要文件）")
        print("2. 使用WinSCP上传这两个zip文件到服务器")
        print("3. 按照摘要文件中的步骤进行部署")
        print("4. 配置企业微信后台")
        print("5. 测试验证")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
