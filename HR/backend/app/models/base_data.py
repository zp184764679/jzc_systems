from app import db
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional


class Department(db.Model):
    """部门表"""
    __tablename__ = 'departments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='部门编码')
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='部门名称')
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('departments.id'), comment='上级部门ID')
    manager_id: Mapped[Optional[int]] = mapped_column(Integer, comment='部门负责人ID')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='部门描述')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment='排序顺序')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 自引用关系
    children = relationship('Department', backref=db.backref('parent', remote_side=[id]))

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'parent_id': self.parent_id,
            'manager_id': self.manager_id,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Department {self.code} - {self.name}>'


class Position(db.Model):
    """职位表"""
    __tablename__ = 'positions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='职位编码')
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='职位名称')
    level: Mapped[Optional[int]] = mapped_column(Integer, comment='职级(1-10)')
    category: Mapped[Optional[str]] = mapped_column(String(50), comment='职位类别(管理/技术/销售/行政等)')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='职位描述')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment='排序顺序')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'level': self.level,
            'category': self.category,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Position {self.code} - {self.name}>'


class Team(db.Model):
    """团队/班组表"""
    __tablename__ = 'teams'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='团队编码')
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='团队名称')
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('departments.id'), comment='所属部门ID')
    leader_id: Mapped[Optional[int]] = mapped_column(Integer, comment='团队负责人ID')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='团队描述')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment='排序顺序')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    department = relationship('Department', backref='teams')

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'leader_id': self.leader_id,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Team {self.code} - {self.name}>'


class Factory(db.Model):
    """工厂/厂区表"""
    __tablename__ = 'factories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='工厂编码')
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='工厂名称')
    city: Mapped[Optional[str]] = mapped_column(String(100), comment='所在城市')
    address: Mapped[Optional[str]] = mapped_column(String(255), comment='详细地址')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='工厂描述')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment='排序顺序')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'city': self.city,
            'address': self.address,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Factory {self.code} - {self.name}>'
