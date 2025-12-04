# tasks/__init__.py
# 让 Celery 能发现本包中的任务
from .notify_rfq import send_rfq_notification  # 让包被导入时注册任务
