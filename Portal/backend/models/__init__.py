"""
Project Management Models
Uses separate database from auth system for project-specific data
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'cncplan')

# Create database URL
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{DB_HOST}/{MYSQL_DATABASE}?charset=utf8mb4"

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Create session factory
SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))

# Create base class for models
Base = declarative_base()

def init_db():
    """Initialize database - create all tables"""
    from models.project import Project
    from models.project_phase import ProjectPhase
    from models.task import Task
    from models.project_file import ProjectFile
    from models.project_member import ProjectMember
    from models.project_notification import ProjectNotification
    from models.issue import Issue

    Base.metadata.create_all(bind=engine)
    print("Project management database tables created successfully")

def get_db():
    """Get database session - use with dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
