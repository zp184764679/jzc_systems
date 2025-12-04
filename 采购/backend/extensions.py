# -*- coding: utf-8 -*-
"""
全局扩展模块
负责初始化数据库、迁移、序列化、异步任务等。
"""

import os
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from celery import Celery

# -----------------------
# Flask 扩展实例
# -----------------------
db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()

# 创建 Celery 实例时指定默认 broker（避免独立启动时使用默认的 RabbitMQ）
celery = Celery(
    __name__,
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
)


# -----------------------
# 初始化数据库
# -----------------------
def init_db(app):
    """初始化 SQLAlchemy"""
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)


# -----------------------
# 初始化 Celery 异步任务
# -----------------------
def init_celery(app):
    """
    将 Celery 绑定到 Flask 上下文
    （任务中可以直接使用 db、模型、日志等 Flask 对象）
    """
    broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    celery.conf.update(
        broker_url=broker,
        result_backend=backend,
        task_default_queue=os.getenv("CELERY_TASK_DEFAULT_QUEUE", "default"),
        worker_concurrency=int(os.getenv("CELERY_WORKER_CONCURRENCY", "2")),
        task_time_limit=int(os.getenv("CELERY_TASK_TIME_LIMIT", "60")),
        task_soft_time_limit=int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "30")),
        timezone="Asia/Shanghai",
        enable_utc=True,
        imports=(
            "tasks.notify_rfq",
            "tasks.classify_rfq_items",
        ),
    )

    class ContextTask(celery.Task):
        """Celery 任务运行时自动进入 Flask 应用上下文"""
        def __call__(self, *args, **kwargs):
            from app import app as flask_app
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
