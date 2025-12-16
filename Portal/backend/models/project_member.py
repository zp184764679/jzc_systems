"""
ProjectMember Model - 项目成员模型
包含角色和权限管理
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base
import enum


class MemberRole(str, enum.Enum):
    """成员角色枚举"""
    OWNER = 'owner'         # 所有者
    MANAGER = 'manager'     # 管理员
    MEMBER = 'member'       # 成员
    VIEWER = 'viewer'       # 查看者


class ProjectMember(Base):
    """项目成员表"""
    __tablename__ = 'project_members'

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 关联项目和用户
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True, comment='所属项目ID')
    user_id = Column(Integer, nullable=False, index=True, comment='用户ID')

    # 部门信息（冗余字段，方便查询）
    department = Column(String(100), comment='部门')

    # 角色
    role = Column(
        Enum(MemberRole),
        default=MemberRole.MEMBER,
        nullable=False,
        comment='项目角色'
    )

    # 权限配置（JSON格式存储）
    # 格式示例: {
    #   "can_edit_project": true,
    #   "can_create_tasks": true,
    #   "can_upload_files": true,
    #   "can_manage_members": false,
    #   "can_delete": false
    # }
    permissions = Column(JSON, comment='权限配置')

    # 时间戳
    joined_at = Column(DateTime, default=datetime.now, nullable=False, comment='加入时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关系
    # project = relationship('Project', back_populates='members')

    @staticmethod
    def get_default_permissions(role):
        """根据角色获取默认权限"""
        permissions_map = {
            MemberRole.OWNER: {
                "can_edit_project": True,
                "can_delete_project": True,
                "can_create_tasks": True,
                "can_assign_tasks": True,
                "can_upload_files": True,
                "can_delete_files": True,
                "can_manage_members": True,
                "can_delete": True,
            },
            MemberRole.MANAGER: {
                "can_edit_project": True,
                "can_delete_project": False,
                "can_create_tasks": True,
                "can_assign_tasks": True,
                "can_upload_files": True,
                "can_delete_files": True,
                "can_manage_members": True,
                "can_delete": False,
            },
            MemberRole.MEMBER: {
                "can_edit_project": False,
                "can_delete_project": False,
                "can_create_tasks": True,
                "can_assign_tasks": False,
                "can_upload_files": True,
                "can_delete_files": False,  # 仅能删除自己的文件
                "can_manage_members": False,
                "can_delete": False,
            },
            MemberRole.VIEWER: {
                "can_edit_project": False,
                "can_delete_project": False,
                "can_create_tasks": False,
                "can_assign_tasks": False,
                "can_upload_files": False,
                "can_delete_files": False,
                "can_manage_members": False,
                "can_delete": False,
            },
        }
        return permissions_map.get(role, permissions_map[MemberRole.VIEWER])

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'department': self.department,
            'role': self.role.value if isinstance(self.role, MemberRole) else self.role,
            'permissions': self.permissions or self.get_default_permissions(self.role),
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def has_permission(self, permission_name):
        """检查是否具有指定权限"""
        if not self.permissions:
            self.permissions = self.get_default_permissions(self.role)
        return self.permissions.get(permission_name, False)

    def __repr__(self):
        return f"<ProjectMember user_id={self.user_id} role={self.role}>"
