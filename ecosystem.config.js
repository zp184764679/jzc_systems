module.exports = {
  apps: [
    // ==================== 后端服务 ====================
    {
      name: 'portal-backend',
      cwd: './Portal/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 3002 }
    },
    {
      name: 'hr-backend',
      cwd: './HR/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 8003 }
    },
    {
      name: 'account-backend',
      cwd: './account/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 8004 }
    },
    {
      name: 'quotation-backend',
      cwd: './报价/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 8001 }
    },
    {
      name: 'caigou-backend',
      cwd: './采购/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 5001 }
    },
    {
      name: 'crm-backend',
      cwd: './CRM/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 8002 }
    },
    {
      name: 'scm-backend',
      cwd: './SCM/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 8005 }
    },
    {
      name: 'shm-backend',
      cwd: './SHM/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 8006 }
    },
    {
      name: 'eam-backend',
      cwd: './EAM/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 8008 }
    },
    {
      name: 'mes-backend',
      cwd: './MES/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 8007 }
    },
    {
      name: 'dashboard-backend',
      cwd: './Dashboard/backend',
      script: 'main.py',
      interpreter: './venv/bin/python3',
      env: { PORT: 8100 }
    },
    {
      name: 'docs-strapi',
      cwd: './DocPublisher/strapi',
      script: 'node_modules/@strapi/strapi/bin/strapi.js',
      args: 'develop',
      env: { PORT: 1337, NODE_ENV: 'development' }
    },

    // ==================== 前端服务 (开发环境) ====================
    {
      name: 'portal-frontend',
      cwd: './Portal',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 3001 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'hr-frontend',
      cwd: './HR/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 6002 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'account-frontend',
      cwd: './account/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 6003 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'quotation-frontend',
      cwd: './报价/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 6001 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'caigou-frontend',
      cwd: './采购/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 5000 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'crm-frontend',
      cwd: './CRM/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 6004 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'scm-frontend',
      cwd: './SCM/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 7000 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'shm-frontend',
      cwd: './SHM/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 7500 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'eam-frontend',
      cwd: './EAM/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 7200 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'mes-frontend',
      cwd: './MES/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 7800 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'dashboard-frontend',
      cwd: './Dashboard/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 6100 --host',
      env: { NODE_ENV: 'development' }
    },
    {
      name: 'docs-frontend',
      cwd: './DocPublisher/frontend',
      script: 'node_modules/vite/bin/vite.js',
      args: '--port 6200 --host',
      env: { NODE_ENV: 'development' }
    },

    // ==================== WSL 服务 ====================
    {
      name: 'ollama',
      script: 'wsl.exe',
      args: '-d Ubuntu-22.04 -- ollama serve',
      interpreter: 'none',
      windowsHide: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
    },
    {
      name: 'celery-worker',
      script: 'wsl.exe',
      args: '-d Ubuntu-22.04 -- bash -c "cd /home/aaa/采购 && source venv/bin/activate && celery -A celery_app worker --loglevel=info"',
      interpreter: 'none',
      windowsHide: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
    },
  ],
};
