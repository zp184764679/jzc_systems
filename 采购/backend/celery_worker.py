# celery_worker.py
from app import app
from extensions import celery, init_celery

# 初始化Celery并绑定Flask上下文
init_celery(app)

# 导入任务模块确保任务被注册
try:
    from tasks import classification_tasks
except ImportError:
    pass

# 暴露celery实例给celery命令
__all__ = ['celery']
