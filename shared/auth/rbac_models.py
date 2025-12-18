"""
RBAC Models - Role-Based Access Control Data Models
Provides fine-grained permission control for all subsystems
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Table, Index, JSON, UniqueConstraint, BigInteger
)
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import relationship
from .models import AuthBase


# Helper: MySQL BIGINT UNSIGNED type for user_id foreign keys
# This matches the users.id column type in MySQL
UserIdType = BigInteger().with_variant(BIGINT(unsigned=True), 'mysql')


# Association table for Role-Permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    AuthBase.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('created_by', Integer, nullable=True)
)


# Association table for User-Role many-to-many relationship
user_roles = Table(
    'user_roles',
    AuthBase.metadata,
    Column('user_id', UserIdType, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('created_by', UserIdType, nullable=True),  # Reference to user who assigned the role
    Column('expires_at', DateTime, nullable=True)  # Optional role expiration
)


class Role(AuthBase):
    """
    Role model for RBAC
    Roles define a set of permissions that can be assigned to users
    """
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., 'hr_admin', 'scm_viewer'
    name = Column(String(100), nullable=False)  # Display name
    description = Column(Text, nullable=True)

    # Role type: system (built-in) or custom (user-defined)
    role_type = Column(String(20), default='custom')  # 'system' | 'custom'

    # Role level for hierarchy (higher = more powerful)
    level = Column(Integer, default=0)

    # Which module this role belongs to (null = global)
    module = Column(String(50), nullable=True, index=True)  # 'hr', 'crm', 'scm', etc.

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

    # Relationships
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')

    __table_args__ = (
        Index('ix_roles_module_code', 'module', 'code'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'role_type': self.role_type,
            'level': self.level,
            'module': self.module,
            'is_active': self.is_active,
            'permission_count': len(self.permissions) if self.permissions else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Permission(AuthBase):
    """
    Permission model - defines specific actions that can be controlled
    """
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'hr:employee:read'
    name = Column(String(100), nullable=False)  # Display name
    description = Column(Text, nullable=True)

    # Permission category for organization
    category = Column(String(50), nullable=True, index=True)  # 'employee', 'department', 'report'

    # Which module this permission belongs to
    module = Column(String(50), nullable=False, index=True)  # 'hr', 'crm', 'scm', 'portal'

    # Action type
    action = Column(String(20), nullable=False)  # 'read', 'create', 'update', 'delete', 'export', 'approve'

    # Resource this permission controls
    resource = Column(String(50), nullable=False)  # 'employee', 'customer', 'order'

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')

    __table_args__ = (
        Index('ix_permissions_module_resource', 'module', 'resource'),
        Index('ix_permissions_module_action', 'module', 'action'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'module': self.module,
            'action': self.action,
            'resource': self.resource,
            'is_active': self.is_active
        }


class DataPermissionRule(AuthBase):
    """
    Data-level permission rules
    Controls which data records a user/role can access
    """
    __tablename__ = 'data_permission_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Can apply to user or role
    rule_type = Column(String(20), nullable=False)  # 'user' | 'role'
    user_id = Column(UserIdType, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=True)

    # Which module and resource this rule applies to
    module = Column(String(50), nullable=False, index=True)
    resource = Column(String(50), nullable=False)

    # Filter condition (JSON format)
    # e.g., {"department_id": [1, 2, 3]} or {"factory_id": "${user.factory_id}"}
    condition = Column(JSON, nullable=False)

    # Priority for rule evaluation (higher = evaluated first)
    priority = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

    __table_args__ = (
        Index('ix_data_perm_user', 'user_id', 'module', 'resource'),
        Index('ix_data_perm_role', 'role_id', 'module', 'resource'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rule_type': self.rule_type,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'module': self.module,
            'resource': self.resource,
            'condition': self.condition,
            'priority': self.priority,
            'is_active': self.is_active
        }


class MenuPermission(AuthBase):
    """
    Menu/Feature visibility permissions
    Controls which menus and features are visible to users
    """
    __tablename__ = 'menu_permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'hr:menu:salary'
    name = Column(String(100), nullable=False)

    # Menu hierarchy
    parent_code = Column(String(100), nullable=True)  # For nested menus

    # Which module this menu belongs to
    module = Column(String(50), nullable=False, index=True)

    # Menu path in frontend
    path = Column(String(200), nullable=True)

    # Icon class
    icon = Column(String(50), nullable=True)

    # Sort order
    sort_order = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_menu_perm_module', 'module', 'sort_order'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'parent_code': self.parent_code,
            'module': self.module,
            'path': self.path,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'is_active': self.is_active
        }


# Association table for Role-MenuPermission
role_menus = Table(
    'role_menus',
    AuthBase.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('menu_id', Integer, ForeignKey('menu_permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


def init_rbac_tables():
    """Create all RBAC tables"""
    from . import models
    engine = models.auth_engine
    if engine is None:
        raise RuntimeError("Database engine not initialized. Call init_auth_db first.")

    AuthBase.metadata.create_all(engine, tables=[
        Role.__table__,
        Permission.__table__,
        role_permissions,
        user_roles,
        DataPermissionRule.__table__,
        MenuPermission.__table__,
        role_menus
    ])


def init_default_roles_and_permissions():
    """Initialize default system roles and permissions"""
    from .models import AuthSessionLocal

    session = AuthSessionLocal()
    try:
        # Check if already initialized
        existing_roles = session.query(Role).filter_by(role_type='system').count()
        if existing_roles > 0:
            return  # Already initialized

        # Default system roles
        default_roles = [
            # Global roles
            {'code': 'super_admin', 'name': '超级管理员', 'description': '系统最高权限', 'role_type': 'system', 'level': 100, 'module': None},
            {'code': 'admin', 'name': '管理员', 'description': '系统管理员', 'role_type': 'system', 'level': 50, 'module': None},
            {'code': 'user', 'name': '普通用户', 'description': '普通用户权限', 'role_type': 'system', 'level': 10, 'module': None},

            # HR roles
            {'code': 'hr_admin', 'name': 'HR管理员', 'description': '人力资源管理员', 'role_type': 'system', 'level': 40, 'module': 'hr'},
            {'code': 'hr_manager', 'name': 'HR经理', 'description': '人力资源经理', 'role_type': 'system', 'level': 30, 'module': 'hr'},
            {'code': 'hr_viewer', 'name': 'HR查看者', 'description': '仅查看人事信息', 'role_type': 'system', 'level': 10, 'module': 'hr'},

            # CRM roles
            {'code': 'crm_admin', 'name': 'CRM管理员', 'description': '客户关系管理员', 'role_type': 'system', 'level': 40, 'module': 'crm'},
            {'code': 'sales_manager', 'name': '销售经理', 'description': '销售团队经理', 'role_type': 'system', 'level': 30, 'module': 'crm'},
            {'code': 'sales_rep', 'name': '销售代表', 'description': '销售人员', 'role_type': 'system', 'level': 20, 'module': 'crm'},

            # SCM roles
            {'code': 'scm_admin', 'name': '仓库管理员', 'description': '仓库管理员', 'role_type': 'system', 'level': 40, 'module': 'scm'},
            {'code': 'warehouse_keeper', 'name': '仓管员', 'description': '仓库操作员', 'role_type': 'system', 'level': 20, 'module': 'scm'},

            # Quotation roles
            {'code': 'quote_admin', 'name': '报价管理员', 'description': '报价系统管理员', 'role_type': 'system', 'level': 40, 'module': 'quotation'},
            {'code': 'quoter', 'name': '报价员', 'description': '负责产品报价', 'role_type': 'system', 'level': 20, 'module': 'quotation'},

            # Procurement roles
            {'code': 'procurement_admin', 'name': '采购管理员', 'description': '采购系统管理员', 'role_type': 'system', 'level': 40, 'module': 'caigou'},
            {'code': 'buyer', 'name': '采购员', 'description': '负责采购执行', 'role_type': 'system', 'level': 20, 'module': 'caigou'},

            # EAM roles
            {'code': 'eam_admin', 'name': '设备管理员', 'description': '设备资产管理员', 'role_type': 'system', 'level': 40, 'module': 'eam'},
            {'code': 'maintenance_tech', 'name': '维护技术员', 'description': '设备维护人员', 'role_type': 'system', 'level': 20, 'module': 'eam'},

            # MES roles
            {'code': 'mes_admin', 'name': 'MES管理员', 'description': '生产执行管理员', 'role_type': 'system', 'level': 40, 'module': 'mes'},
            {'code': 'production_planner', 'name': '生产计划员', 'description': '负责生产排程', 'role_type': 'system', 'level': 30, 'module': 'mes'},
            {'code': 'shop_floor', 'name': '车间操作员', 'description': '车间生产人员', 'role_type': 'system', 'level': 20, 'module': 'mes'},

            # SHM roles
            {'code': 'shm_admin', 'name': '出货管理员', 'description': '出货系统管理员', 'role_type': 'system', 'level': 40, 'module': 'shm'},
            {'code': 'shipper', 'name': '发货员', 'description': '负责出货操作', 'role_type': 'system', 'level': 20, 'module': 'shm'},
        ]

        for role_data in default_roles:
            role = Role(**role_data)
            session.add(role)

        # Default permissions for each module
        modules_permissions = {
            'hr': [
                ('hr:employee:read', '查看员工', '员工', 'read'),
                ('hr:employee:create', '创建员工', '员工', 'create'),
                ('hr:employee:update', '编辑员工', '员工', 'update'),
                ('hr:employee:delete', '删除员工', '员工', 'delete'),
                ('hr:employee:export', '导出员工', '员工', 'export'),
                ('hr:department:read', '查看部门', '部门', 'read'),
                ('hr:department:manage', '管理部门', '部门', 'update'),
                ('hr:salary:read', '查看薪资', '薪资', 'read'),
                ('hr:salary:manage', '管理薪资', '薪资', 'update'),
            ],
            'crm': [
                ('crm:customer:read', '查看客户', '客户', 'read'),
                ('crm:customer:create', '创建客户', '客户', 'create'),
                ('crm:customer:update', '编辑客户', '客户', 'update'),
                ('crm:customer:delete', '删除客户', '客户', 'delete'),
                ('crm:customer:export', '导出客户', '客户', 'export'),
                ('crm:order:read', '查看订单', '订单', 'read'),
                ('crm:order:create', '创建订单', '订单', 'create'),
                ('crm:order:manage', '管理订单', '订单', 'update'),
            ],
            'scm': [
                ('scm:inventory:read', '查看库存', '库存', 'read'),
                ('scm:inventory:update', '调整库存', '库存', 'update'),
                ('scm:inbound:create', '入库操作', '入库', 'create'),
                ('scm:outbound:create', '出库操作', '出库', 'create'),
                ('scm:material:read', '查看物料', '物料', 'read'),
                ('scm:material:manage', '管理物料', '物料', 'update'),
            ],
            'quotation': [
                ('quote:quote:read', '查看报价', '报价', 'read'),
                ('quote:quote:create', '创建报价', '报价', 'create'),
                ('quote:quote:update', '编辑报价', '报价', 'update'),
                ('quote:quote:delete', '删除报价', '报价', 'delete'),
                ('quote:quote:export', '导出报价', '报价', 'export'),
                ('quote:bom:manage', '管理BOM', 'BOM', 'update'),
            ],
            'caigou': [
                ('caigou:pr:read', '查看采购申请', '采购申请', 'read'),
                ('caigou:pr:create', '创建采购申请', '采购申请', 'create'),
                ('caigou:pr:approve', '审批采购申请', '采购申请', 'approve'),
                ('caigou:po:read', '查看采购订单', '采购订单', 'read'),
                ('caigou:po:create', '创建采购订单', '采购订单', 'create'),
                ('caigou:supplier:manage', '管理供应商', '供应商', 'update'),
            ],
            'eam': [
                ('eam:equipment:read', '查看设备', '设备', 'read'),
                ('eam:equipment:create', '创建设备', '设备', 'create'),
                ('eam:equipment:update', '编辑设备', '设备', 'update'),
                ('eam:maintenance:read', '查看维护记录', '维护', 'read'),
                ('eam:maintenance:create', '创建维护工单', '维护', 'create'),
            ],
            'mes': [
                ('mes:workorder:read', '查看工单', '工单', 'read'),
                ('mes:workorder:create', '创建工单', '工单', 'create'),
                ('mes:workorder:update', '编辑工单', '工单', 'update'),
                ('mes:report:create', '生产报工', '报工', 'create'),
                ('mes:schedule:read', '查看排程', '排程', 'read'),
                ('mes:schedule:manage', '管理排程', '排程', 'update'),
            ],
            'shm': [
                ('shm:shipment:read', '查看出货单', '出货单', 'read'),
                ('shm:shipment:create', '创建出货单', '出货单', 'create'),
                ('shm:shipment:update', '编辑出货单', '出货单', 'update'),
                ('shm:shipment:ship', '执行出货', '出货单', 'update'),
            ],
            'portal': [
                ('portal:user:read', '查看用户', '用户', 'read'),
                ('portal:user:create', '创建用户', '用户', 'create'),
                ('portal:user:update', '编辑用户', '用户', 'update'),
                ('portal:user:delete', '删除用户', '用户', 'delete'),
                ('portal:role:manage', '管理角色', '角色', 'update'),
                ('portal:audit:read', '查看审计日志', '审计', 'read'),
                ('portal:system:manage', '系统管理', '系统', 'update'),
            ],
            'account': [
                ('account:user:read', '查看用户', '用户', 'read'),
                ('account:user:create', '创建用户', '用户', 'create'),
                ('account:user:update', '编辑用户', '用户', 'update'),
                ('account:user:delete', '删除用户', '用户', 'delete'),
                ('account:registration:approve', '审批注册', '注册', 'approve'),
            ],
        }

        for module, perms in modules_permissions.items():
            for code, name, resource, action in perms:
                permission = Permission(
                    code=code,
                    name=name,
                    module=module,
                    resource=resource,
                    action=action,
                    category=resource
                )
                session.add(permission)

        session.commit()
        print("Default roles and permissions initialized successfully")

    except Exception as e:
        session.rollback()
        print(f"Error initializing roles and permissions: {e}")
        raise
    finally:
        session.close()
