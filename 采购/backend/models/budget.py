# -*- coding: utf-8 -*-
"""
采购预算模型
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR, TEXT, DECIMAL
from extensions import db


class BudgetPeriodType(Enum):
    """预算周期类型"""
    MONTHLY = 'monthly'      # 月度
    QUARTERLY = 'quarterly'  # 季度
    ANNUAL = 'annual'        # 年度


class BudgetStatus(Enum):
    """预算状态"""
    DRAFT = 'draft'                    # 草稿
    PENDING_APPROVAL = 'pending_approval'  # 待审批
    APPROVED = 'approved'              # 已批准
    ACTIVE = 'active'                  # 执行中
    CLOSED = 'closed'                  # 已关闭
    EXCEEDED = 'exceeded'              # 已超支


BUDGET_PERIOD_LABELS = {
    'monthly': '月度',
    'quarterly': '季度',
    'annual': '年度',
}

BUDGET_STATUS_LABELS = {
    'draft': '草稿',
    'pending_approval': '待审批',
    'approved': '已批准',
    'active': '执行中',
    'closed': '已关闭',
    'exceeded': '已超支',
}


class Budget(db.Model):
    """采购预算"""
    __tablename__ = "budgets"
    __table_args__ = (
        db.Index('idx_budget_year', 'year'),
        db.Index('idx_budget_period', 'period_type', 'period_value'),
        db.Index('idx_budget_department', 'department'),
        db.Index('idx_budget_status', 'status'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    budget_code = db.Column(VARCHAR(50), unique=True, nullable=False, index=True)

    # 预算基本信息
    name = db.Column(VARCHAR(200), nullable=False)
    description = db.Column(TEXT, nullable=True)

    # 预算周期
    period_type = db.Column(VARCHAR(20), nullable=False, default='annual')  # monthly/quarterly/annual
    year = db.Column(db.Integer, nullable=False)
    period_value = db.Column(db.Integer, nullable=True)  # 月份(1-12)或季度(1-4)，年度为空

    # 部门
    department = db.Column(VARCHAR(100), nullable=True)  # 部门，空表示全公司

    # 预算金额
    total_amount = db.Column(DECIMAL(14, 2), nullable=False, default=0)     # 预算总额
    used_amount = db.Column(DECIMAL(14, 2), nullable=False, default=0)       # 已使用金额
    reserved_amount = db.Column(DECIMAL(14, 2), nullable=False, default=0)   # 预留金额（待审批PR）
    currency = db.Column(VARCHAR(10), nullable=False, default='CNY')

    # 预警阈值
    warning_threshold = db.Column(db.Integer, nullable=False, default=80)     # 预警阈值（百分比）
    critical_threshold = db.Column(db.Integer, nullable=False, default=95)    # 严重阈值（百分比）

    # 状态
    status = db.Column(VARCHAR(30), nullable=False, default='draft')

    # 审批信息
    submitted_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    submitted_at = db.Column(DATETIME, nullable=True)
    approved_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(DATETIME, nullable=True)
    approval_note = db.Column(TEXT, nullable=True)

    # 创建/更新信息
    created_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 备注
    remarks = db.Column(TEXT, nullable=True)

    # 关系
    created_by_user = relationship("User", foreign_keys=[created_by])
    submitted_by_user = relationship("User", foreign_keys=[submitted_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    categories = relationship("BudgetCategory", back_populates="budget", cascade="all, delete-orphan")
    usage_records = relationship("BudgetUsage", back_populates="budget", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Budget {self.budget_code}>'

    @staticmethod
    def generate_budget_code(year, period_type, period_value=None, department=None):
        """生成预算编码"""
        prefix = 'BG'
        period_str = f"{year}"
        if period_type == 'monthly' and period_value:
            period_str += f"M{str(period_value).zfill(2)}"
        elif period_type == 'quarterly' and period_value:
            period_str += f"Q{period_value}"
        else:
            period_str += "Y"

        dept_str = department[:3].upper() if department else "ALL"

        # 获取序号
        count = Budget.query.filter(
            Budget.budget_code.like(f'{prefix}-{period_str}-{dept_str}%')
        ).count()
        seq = str(count + 1).zfill(3)

        return f'{prefix}-{period_str}-{dept_str}-{seq}'

    @property
    def available_amount(self):
        """可用金额"""
        return float(self.total_amount) - float(self.used_amount) - float(self.reserved_amount)

    @property
    def usage_rate(self):
        """使用率（百分比）"""
        if self.total_amount <= 0:
            return 0
        return round(float(self.used_amount) / float(self.total_amount) * 100, 2)

    @property
    def is_warning(self):
        """是否预警"""
        return self.usage_rate >= self.warning_threshold

    @property
    def is_critical(self):
        """是否严重"""
        return self.usage_rate >= self.critical_threshold

    def to_dict(self, include_categories=False, include_usage=False):
        """序列化为字典"""
        result = {
            'id': self.id,
            'budget_code': self.budget_code,
            'name': self.name,
            'description': self.description,
            'period_type': self.period_type,
            'period_type_label': BUDGET_PERIOD_LABELS.get(self.period_type, self.period_type),
            'year': self.year,
            'period_value': self.period_value,
            'department': self.department,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'used_amount': float(self.used_amount) if self.used_amount else 0,
            'reserved_amount': float(self.reserved_amount) if self.reserved_amount else 0,
            'available_amount': self.available_amount,
            'currency': self.currency,
            'usage_rate': self.usage_rate,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'is_warning': self.is_warning,
            'is_critical': self.is_critical,
            'status': self.status,
            'status_label': BUDGET_STATUS_LABELS.get(self.status, self.status),
            'submitted_by': self.submitted_by,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approval_note': self.approval_note,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'remarks': self.remarks,
        }

        if include_categories and self.categories:
            result['categories'] = [c.to_dict() for c in self.categories]

        if include_usage and self.usage_records:
            result['usage_records'] = [u.to_dict() for u in sorted(
                self.usage_records, key=lambda x: x.created_at, reverse=True
            )[:20]]

        return result


class BudgetCategory(db.Model):
    """预算分类（按物料类别分配）"""
    __tablename__ = "budget_categories"
    __table_args__ = (
        db.Index('idx_budget_category_budget_id', 'budget_id'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    budget_id = db.Column(BIGINT(unsigned=True), ForeignKey('budgets.id'), nullable=False)

    # 分类信息
    category_name = db.Column(VARCHAR(100), nullable=False)
    category_code = db.Column(VARCHAR(50), nullable=True)

    # 金额
    allocated_amount = db.Column(DECIMAL(14, 2), nullable=False, default=0)  # 分配金额
    used_amount = db.Column(DECIMAL(14, 2), nullable=False, default=0)        # 已使用

    # 备注
    remarks = db.Column(TEXT, nullable=True)

    # 时间戳
    created_at = db.Column(DATETIME, default=datetime.utcnow)
    updated_at = db.Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    budget = relationship("Budget", back_populates="categories")

    def __repr__(self):
        return f'<BudgetCategory {self.category_name}>'

    @property
    def available_amount(self):
        """可用金额"""
        return float(self.allocated_amount) - float(self.used_amount)

    @property
    def usage_rate(self):
        """使用率"""
        if self.allocated_amount <= 0:
            return 0
        return round(float(self.used_amount) / float(self.allocated_amount) * 100, 2)

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'budget_id': self.budget_id,
            'category_name': self.category_name,
            'category_code': self.category_code,
            'allocated_amount': float(self.allocated_amount) if self.allocated_amount else 0,
            'used_amount': float(self.used_amount) if self.used_amount else 0,
            'available_amount': self.available_amount,
            'usage_rate': self.usage_rate,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class BudgetUsage(db.Model):
    """预算使用记录"""
    __tablename__ = "budget_usage"
    __table_args__ = (
        db.Index('idx_budget_usage_budget_id', 'budget_id'),
        db.Index('idx_budget_usage_pr_id', 'pr_id'),
        db.Index('idx_budget_usage_created_at', 'created_at'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    budget_id = db.Column(BIGINT(unsigned=True), ForeignKey('budgets.id'), nullable=False)

    # 关联采购申请
    pr_id = db.Column(BIGINT(unsigned=True), ForeignKey('prs.id'), nullable=True)
    pr_number = db.Column(VARCHAR(50), nullable=True)

    # 使用类型
    usage_type = db.Column(VARCHAR(20), nullable=False)  # reserve(预留)/consume(消费)/release(释放)/adjust(调整)

    # 金额
    amount = db.Column(DECIMAL(14, 2), nullable=False)
    balance_after = db.Column(DECIMAL(14, 2), nullable=False)  # 操作后余额

    # 备注
    remarks = db.Column(TEXT, nullable=True)

    # 操作人
    operated_by = db.Column(BIGINT(unsigned=True), ForeignKey('users.id'), nullable=True)
    operated_by_name = db.Column(VARCHAR(100), nullable=True)

    # 时间戳
    created_at = db.Column(DATETIME, default=datetime.utcnow)

    # 关系
    budget = relationship("Budget", back_populates="usage_records")

    def __repr__(self):
        return f'<BudgetUsage {self.usage_type} {self.amount}>'

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'budget_id': self.budget_id,
            'pr_id': self.pr_id,
            'pr_number': self.pr_number,
            'usage_type': self.usage_type,
            'amount': float(self.amount) if self.amount else 0,
            'balance_after': float(self.balance_after) if self.balance_after else 0,
            'remarks': self.remarks,
            'operated_by': self.operated_by,
            'operated_by_name': self.operated_by_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


BUDGET_USAGE_TYPE_LABELS = {
    'reserve': '预留',
    'consume': '消费',
    'release': '释放',
    'adjust': '调整',
}
