module.exports = {
  apps: [
    // ==================== WSL 服务 ====================
    {
      name: 'ollama',
      script: 'wsl.exe',
      args: '-d Ubuntu-22.04 -- ollama serve',
      interpreter: 'none',
      windowsHide: true,
      error_file: 'C:\\Users\\Admin\\Desktop\\logs\\ollama-error.log',
      out_file: 'C:\\Users\\Admin\\Desktop\\logs\\ollama-out.log',
      time: true,
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
      error_file: 'C:\\Users\\Admin\\Desktop\\logs\\celery-worker-error.log',
      out_file: 'C:\\Users\\Admin\\Desktop\\logs\\celery-worker-out.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
    },
  ],
};
