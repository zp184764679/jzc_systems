# config/database.py
"""
数据库配置和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .settings import settings

# 创建数据库引擎 - 添加连接池配置
if "sqlite" in settings.DATABASE_URL:
    # SQLite不支持连接池，但需要禁用同线程检查
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )
else:
    # MySQL/PostgreSQL使用连接池
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,           # 连接池大小
        max_overflow=20,        # 超出pool_size后最多可创建的连接数
        pool_pre_ping=True,     # 每次取连接时检查连接是否有效
        pool_recycle=1200,      # 连接回收时间（秒）
        echo=settings.DEBUG
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    from models import material, process, drawing, product, quote, bom, process_route  # noqa
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库初始化完成")
