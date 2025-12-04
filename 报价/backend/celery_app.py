# celery_app.py
"""
Celery应用配置
"""
from celery import Celery
from config.settings import settings

# 创建Celery实例
celery_app = Celery(
    'quote_system',
    broker=settings.REDIS_URL or 'redis://localhost:6379/0',
    backend=settings.REDIS_URL or 'redis://localhost:6379/0'
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 自动发现任务
celery_app.autodiscover_tasks(['services'])
