# make_celery.py
"""
独立的Celery应用初始化文件
用于 celery -A make_celery worker 命令启动
"""
import os
import sys
from celery import Celery
from dotenv import load_dotenv

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# 显式加载.env文件
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

# ⭐ 关键修复：强制设置环境变量到os.environ，确保app.py导入时能读取
if not os.environ.get('SQLALCHEMY_DATABASE_URI'):
    db_uri = 'mysql+pymysql://zhoupeng:ZPexak472008%40@127.0.0.1:3307/caigou?charset=utf8mb4'
    os.environ['SQLALCHEMY_DATABASE_URI'] = db_uri
    print(f'[make_celery] 强制设置 DATABASE_URI')

print(f'[make_celery] 环境变量 DATABASE_URI: {os.environ.get("SQLALCHEMY_DATABASE_URI", "NOT_SET")}')

# 创建Celery实例
celery = Celery(
    'caigou_tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
)

# 配置Celery
celery.conf.update(
    task_default_queue='default',
    worker_concurrency=2,
    task_time_limit=60,
    task_soft_time_limit=30,
    timezone='Asia/Shanghai',
    enable_utc=True,
    imports=(
        'tasks.notify_rfq',
        'tasks.classify_rfq_items',
    ),
)

# Flask上下文任务基类
class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        from app import app
        print(f'[Task] 任务执行时的 DATABASE_URI: {app.config.get("SQLALCHEMY_DATABASE_URI", "NOT_SET")}')
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask
