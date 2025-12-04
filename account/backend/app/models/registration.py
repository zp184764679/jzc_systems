from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

# Database configuration
# MySQL configuration
DB_USER = os.getenv('MYSQL_USER', 'app')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'app')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('MYSQL_DATABASE', 'account')
DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class RegistrationRequest(Base):
    __tablename__ = 'registration_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    emp_no = Column(String(50), nullable=False, unique=True, index=True)
    full_name = Column(String(100), nullable=False)
    username = Column(String(50))
    hashed_password = Column(String(255))
    email = Column(String(255))
    department = Column(String(100))
    department_id = Column(Integer)
    title = Column(String(100))
    position_id = Column(Integer)
    team = Column(String(100))
    team_id = Column(Integer)
    factory_name = Column(String(100))
    factory_id = Column(Integer)
    status = Column(String(20), nullable=False, default='pending', index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    reason = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'empNo': self.emp_no,
            'emp_no': self.emp_no,
            'fullName': self.full_name,
            'full_name': self.full_name,
            'username': self.username,
            'email': self.email,
            'factory': self.factory_name,
            'factory_id': self.factory_id,
            'department': self.department,
            'department_id': self.department_id,
            'title': self.title,
            'position_id': self.position_id,
            'team': self.team,
            'team_id': self.team_id,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'reason': self.reason
        }


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise
