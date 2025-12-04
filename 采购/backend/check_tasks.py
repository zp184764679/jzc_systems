from celery import Celery

celery_app = Celery(
    'caigou_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

# 检查最新任务
result = celery_app.AsyncResult('3b2b6526-bf35-4311-a316-d3a48e53a04d')
print(f'任务状态: {result.state}')
print(f'任务信息: {result.info}')
print(f'任务完成: {result.ready()}')
if result.failed():
    print(f'错误: {result.traceback}')
