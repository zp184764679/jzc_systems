# models/supplier.py
# -*- coding: utf-8 -*-
# ✅ 在原模型基础上新增了企业微信Kf点对点所需字段：
#    - preferred_channel：首选消息通道（默认 wecom_kf）
#    - wecom_external_userid：企微外部联系人ID（点对点所需，唯一）
#    - wecom_bind_status：与Kf是否已建链（bound/pending/unknown）
#    - 相关索引：preferred_channel / wecom_bind_status / wecom_external_userid
#
# 其余字段保持与你现有实现一致；保留原有唯一约束与索引。

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.mysql import BIGINT
from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

# 供应商状态枚举（供业务参考）
SUPPLIER_STATUS = {
    'PENDING': 'pending',
    'APPROVED': 'approved',
    'DENIED': 'denied',
    'FROZEN': 'frozen',
    'BLACKLISTED': 'blacklisted'
}

# Kf建链状态
WECOM_BIND_STATUS = ['bound', 'pending', 'unknown']

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    __table_args__ = (
        # company_name、email、code 已各自 unique
        db.Index('idx_suppliers_status', 'status'),
        db.Index('idx_suppliers_code', 'code'),
        # 新增索引：按通道与绑定状态过滤更高效
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # ✅ code 字段允许 nullable，插入后由路由生成（保持你现有逻辑）
    code = db.Column(String(50), unique=True, nullable=True)

    # 登录凭据
    email = db.Column(String(120), unique=True, nullable=False)
    password_hash = db.Column(String(255), nullable=False)

    # 主体信息
    company_name = db.Column(String(200), unique=True, nullable=False)
    tax_id = db.Column(String(50), nullable=False)  # 统一社会信用代码/税号
    business_scope = db.Column(String(500), nullable=True)  # 经营范围/主营品类

    # 🏢 基本信息扩展字段
    credit_code = db.Column(String(50), nullable=True)  # 信用代码（与tax_id可能重复，保留兼容）
    tax_number = db.Column(String(50), nullable=True)  # 税号（独立字段）
    legal_representative = db.Column(String(100), nullable=True)  # 法定代表人
    registered_capital = db.Column(String(50), nullable=True)  # 注册资本（万元）
    registered_address = db.Column(String(300), nullable=True)  # 注册地址
    established_date = db.Column(String(50), nullable=True)  # 成立日期
    company_type = db.Column(String(100), nullable=True)  # 企业类型
    business_status = db.Column(String(50), nullable=True)  # 经营状态

    province = db.Column(String(50), nullable=True)
    city = db.Column(String(50), nullable=True)
    district = db.Column(String(50), nullable=True)
    address = db.Column(String(200), nullable=True)

    # 📞 联系方式
    contact_name = db.Column(String(50), nullable=True)
    contact_phone = db.Column(String(30), nullable=False)
    contact_email = db.Column(String(120), nullable=False)
    company_phone = db.Column(String(30), nullable=True)  # 公司电话
    fax = db.Column(String(30), nullable=True)  # 传真
    website = db.Column(String(200), nullable=True)  # 公司网站
    office_address = db.Column(String(300), nullable=True)  # 办公地址
    postal_code = db.Column(String(20), nullable=True)  # 邮政编码

    # 资质文件
    business_license_url = db.Column(db.Text, nullable=True)  # 用 Text 支持 Base64/URL
    license_file_type = db.Column(String(20), nullable=True)
    license_file_size = db.Column(String(20), nullable=True)  # 存字符串以兼容"MB/字节"表示

    # 💼 业务信息
    company_description = db.Column(db.Text, nullable=True)  # 公司简介
    description = db.Column(db.Text, nullable=True)  # 描述（兼容字段）
    main_products = db.Column(String(500), nullable=True)  # 主营产品
    annual_revenue = db.Column(String(50), nullable=True)  # 年营业额（万元）
    employee_count = db.Column(String(50), nullable=True)  # 员工人数
    factory_area = db.Column(String(50), nullable=True)  # 工厂面积（平方米）
    production_capacity = db.Column(String(300), nullable=True)  # 生产能力
    quality_certifications = db.Column(String(500), nullable=True)  # 质量认证

    # 💰 财务信息
    bank_name = db.Column(String(200), nullable=True)  # 开户银行
    bank_account = db.Column(String(100), nullable=True)  # 银行账号
    bank_branch = db.Column(String(200), nullable=True)  # 开户行地址
    swift_code = db.Column(String(50), nullable=True)  # SWIFT代码
    payment_terms = db.Column(String(200), nullable=True)  # 付款条件
    credit_rating = db.Column(String(50), nullable=True)  # 信用等级
    tax_registration_number = db.Column(String(50), nullable=True)  # 税务登记号
    invoice_type = db.Column(String(50), nullable=True)  # 开票类型

    # 📋 结算方式
    # per_order: 单次结算（每个PO一张发票）
    # monthly: 月结（一个月所有PO汇总一张发票）
    settlement_type = db.Column(String(20), default='per_order', nullable=False, comment='结算方式')
    settlement_day = db.Column(db.Integer, nullable=True, comment='月结结算日（1-28，如每月25日结算）')
    payment_days = db.Column(db.Integer, nullable=True, default=30, comment='账期天数（月结后多少天付款）')

    # 评分字段（自动计算）
    rating = db.Column(db.Float, nullable=True, default=0.0)  # 综合评分
    rating_updated_at = db.Column(DateTime, nullable=True)  # 评分更新时间

    # 审批/状态
    status = db.Column(String(20), default='pending')
    reason = db.Column(String(300), nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(DateTime, nullable=True)

    # 微信服务号集成（外部供应商普通微信通知）
    wechat_openid = db.Column(String(100), nullable=True, unique=True, comment='微信服务号OpenID')
    is_subscribed = db.Column(db.Boolean, default=False, comment='是否关注公众号')

    # 供应品类映射（多对多），如已有中间表保持不动
    categories = db.relationship(
        'SupplierCategory',
        back_populates='supplier',
        cascade='all, delete-orphan',
        lazy=True
    )

    # ===== 方法 =====
    def __repr__(self):
        return f'<Supplier {self.company_name}>'

    def set_password(self, password):
        """设置密码（自动hash处理）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """校验密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'company_name': self.company_name,
            'email': self.email,
            'status': self.status,
            'reason': self.reason,

            # 基本信息
            'tax_id': self.tax_id,
            'credit_code': self.credit_code,
            'tax_number': self.tax_number,
            'legal_representative': self.legal_representative,
            'registered_capital': self.registered_capital,
            'registered_address': self.registered_address,
            'established_date': self.established_date,
            'company_type': self.company_type,
            'business_status': self.business_status,
            'province': self.province,
            'city': self.city,
            'district': self.district,
            'address': self.address,

            # 联系方式
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'company_phone': self.company_phone,
            'fax': self.fax,
            'website': self.website,
            'office_address': self.office_address,
            'postal_code': self.postal_code,

            # 资质文件
            'business_license_url': self.business_license_url,
            'license_file_type': self.license_file_type,
            'license_file_size': self.license_file_size,

            # 业务信息
            'business_scope': self.business_scope,
            'company_description': self.company_description,
            'description': self.description,
            'main_products': self.main_products,
            'annual_revenue': self.annual_revenue,
            'employee_count': self.employee_count,
            'factory_area': self.factory_area,
            'production_capacity': self.production_capacity,
            'quality_certifications': self.quality_certifications,

            # 财务信息
            'bank_name': self.bank_name,
            'bank_account': self.bank_account,
            'bank_branch': self.bank_branch,
            'swift_code': self.swift_code,
            'payment_terms': self.payment_terms,
            'credit_rating': self.credit_rating,
            'tax_registration_number': self.tax_registration_number,
            'invoice_type': self.invoice_type,

            # 结算方式
            'settlement_type': self.settlement_type,
            'settlement_day': self.settlement_day,
            'payment_days': self.payment_days,

            # 评分
            'rating': self.rating,
            'rating_updated_at': self.rating_updated_at.isoformat() if self.rating_updated_at else None,

            # 分类
            'categories': [c.category_code for c in self.categories] if self.categories else [],

            # 微信集成
            'wechat_openid': self.wechat_openid,
            'is_subscribed': self.is_subscribed,

            # 时间戳
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
        }
