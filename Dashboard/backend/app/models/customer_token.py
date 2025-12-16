from app import db
from datetime import datetime
from sqlalchemy import func
import secrets


class CustomerAccessToken(db.Model):
    """客户门户访问令牌"""
    __tablename__ = 'dashboard_customer_tokens'

    id = db.Column(db.Integer, primary_key=True)

    # 客户信息
    customer_id = db.Column(db.Integer, nullable=False, index=True)
    customer_code = db.Column(db.String(64))
    customer_name = db.Column(db.String(200))
    contact_name = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))

    # 令牌
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)

    # 权限范围
    order_ids = db.Column(db.JSON)  # 可访问的订单ID列表, null表示所有
    permissions = db.Column(db.JSON, default=dict)  # 权限配置

    # 有效期
    created_at = db.Column(db.DateTime, default=func.now())
    expires_at = db.Column(db.DateTime, nullable=False)
    last_accessed_at = db.Column(db.DateTime)

    # 状态
    is_active = db.Column(db.Boolean, default=True)
    revoked_at = db.Column(db.DateTime)
    revoked_reason = db.Column(db.String(200))

    # 创建者
    created_by_user_id = db.Column(db.Integer)
    created_by_name = db.Column(db.String(100))

    @staticmethod
    def generate_token():
        """生成安全的随机令牌"""
        return secrets.token_urlsafe(32)

    @property
    def is_expired(self):
        """是否已过期"""
        return datetime.now() > self.expires_at

    @property
    def is_valid(self):
        """是否有效（未过期且未撤销）"""
        return self.is_active and not self.is_expired

    @property
    def days_until_expiry(self):
        """距离过期还有多少天"""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.now()
        return max(0, delta.days)

    def can_access_order(self, order_id):
        """检查是否可以访问指定订单"""
        if not self.is_valid:
            return False
        if self.order_ids is None:
            return True  # 没有限制，可访问所有
        return order_id in self.order_ids

    def record_access(self):
        """记录访问时间"""
        self.last_accessed_at = datetime.now()

    def revoke(self, reason=None):
        """撤销令牌"""
        self.is_active = False
        self.revoked_at = datetime.now()
        self.revoked_reason = reason

    def to_dict(self, include_token=False):
        data = {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_code': self.customer_code,
            'customer_name': self.customer_name,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'order_ids': self.order_ids,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'is_active': self.is_active,
            'is_valid': self.is_valid,
            'days_until_expiry': self.days_until_expiry,
            'created_by_name': self.created_by_name
        }
        if include_token:
            data['token'] = self.token
        return data
