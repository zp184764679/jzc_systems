# -*- coding: utf-8 -*-
"""
CRM 供应商主数据模型

供应商基础信息的统一数据源，其他系统（如采购）通过 API 查询。
采购系统可以保留业务特定字段（评分、资质、结算等），只需引用 CRM 供应商 ID。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import Index, or_, case
from sqlalchemy.ext.mutable import MutableList

from .. import db


# 供应商状态枚举
SUPPLIER_STATUS = {
    'active': '正常',
    'inactive': '停用',
    'pending': '待审核',
    'blacklisted': '黑名单'
}


class Supplier(db.Model):
    """CRM 供应商主数据"""
    __tablename__ = "crm_suppliers"

    # ========== 主键 ==========
    id = db.Column(db.Integer, primary_key=True)

    # ========== 序号 ==========
    seq_no = db.Column(db.Integer, index=True, nullable=True)

    # ========== 基本信息 ==========
    code = db.Column(db.String(64), unique=True, index=True, nullable=True)      # 供应商代码
    short_name = db.Column(db.String(128), index=True, nullable=True)            # 供应商简称
    name = db.Column(db.String(255), index=True, nullable=False)                 # 供应商全称

    # ========== 分类 ==========
    category = db.Column(db.String(64), nullable=True)                           # 供应商分类
    tags = db.Column(MutableList.as_mutable(db.JSON), default=list)             # 标签列表

    # ========== 状态 ==========
    status = db.Column(db.String(32), default='active', index=True)              # 状态

    # ========== 企业信息 ==========
    tax_id = db.Column(db.String(50), nullable=True)                             # 税号/统一社会信用代码
    legal_representative = db.Column(db.String(100), nullable=True)              # 法定代表人
    registered_capital = db.Column(db.String(50), nullable=True)                 # 注册资本
    established_date = db.Column(db.String(50), nullable=True)                   # 成立日期
    business_scope = db.Column(db.String(500), nullable=True)                    # 经营范围

    # ========== 地址信息 ==========
    province = db.Column(db.String(50), nullable=True)                           # 省份
    city = db.Column(db.String(50), nullable=True)                               # 城市
    district = db.Column(db.String(50), nullable=True)                           # 区县
    address = db.Column(db.String(300), nullable=True)                           # 详细地址
    postal_code = db.Column(db.String(20), nullable=True)                        # 邮编

    # ========== 联系方式 ==========
    # 主联系人（JSON 数组以支持多个联系人）
    contacts = db.Column(MutableList.as_mutable(db.JSON), default=list)
    # [ {"name": "张三", "phone": "138xxx", "email": "xxx@xxx.com", "role": "采购经理"} ]

    # 公司联系方式
    phone = db.Column(db.String(30), nullable=True)                              # 公司电话
    fax = db.Column(db.String(30), nullable=True)                                # 传真
    email = db.Column(db.String(120), nullable=True)                             # 公司邮箱
    website = db.Column(db.String(200), nullable=True)                           # 网站

    # ========== 银行信息 ==========
    bank_name = db.Column(db.String(200), nullable=True)                         # 开户银行
    bank_account = db.Column(db.String(100), nullable=True)                      # 银行账号
    bank_branch = db.Column(db.String(200), nullable=True)                       # 开户行支行

    # ========== 业务信息 ==========
    main_products = db.Column(db.String(500), nullable=True)                     # 主营产品
    currency_default = db.Column(db.String(16), default='CNY')                   # 默认币种
    payment_terms = db.Column(db.String(200), nullable=True)                     # 付款条款

    # ========== 关联 ==========
    # 如果供应商同时也是客户，可以关联
    customer_id = db.Column(db.Integer, nullable=True)                           # 关联客户ID

    # ========== 备注 ==========
    remark = db.Column(db.String(1024), nullable=True)

    # ========== 数据权限控制 ==========
    owner_id = db.Column(db.Integer, index=True, nullable=True)                  # 负责人ID
    owner_name = db.Column(db.String(64), nullable=True)                         # 负责人姓名
    department_id = db.Column(db.Integer, index=True, nullable=True)             # 所属部门ID
    department_name = db.Column(db.String(128), nullable=True)                   # 所属部门名称
    created_by = db.Column(db.Integer, nullable=True)                            # 创建人ID

    # ========== 审计 ==========
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
                          index=True, nullable=False)

    # ========== 索引 ==========
    __table_args__ = (
        Index("idx_suppliers_code_name", "code", "name"),
        Index("idx_suppliers_status_category", "status", "category"),
    )

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "id": self.id,
            "seq_no": self.seq_no,
            "code": self.code or "",
            "short_name": self.short_name or "",
            "name": self.name or "",
            "category": self.category or "",
            "tags": self.tags or [],
            "status": self.status or "active",

            # 企业信息
            "tax_id": self.tax_id or "",
            "legal_representative": self.legal_representative or "",
            "registered_capital": self.registered_capital or "",
            "established_date": self.established_date or "",
            "business_scope": self.business_scope or "",

            # 地址
            "province": self.province or "",
            "city": self.city or "",
            "district": self.district or "",
            "address": self.address or "",
            "postal_code": self.postal_code or "",

            # 联系方式
            "contacts": self.contacts or [],
            "phone": self.phone or "",
            "fax": self.fax or "",
            "email": self.email or "",
            "website": self.website or "",

            # 银行信息
            "bank_name": self.bank_name or "",
            "bank_account": self.bank_account or "",
            "bank_branch": self.bank_branch or "",

            # 业务信息
            "main_products": self.main_products or "",
            "currency_default": self.currency_default or "CNY",
            "payment_terms": self.payment_terms or "",

            # 关联
            "customer_id": self.customer_id,

            # 备注
            "remark": self.remark or "",

            # 数据权限
            "owner_id": self.owner_id,
            "owner_name": self.owner_name or "",
            "department_id": self.department_id,
            "department_name": self.department_name or "",
            "created_by": self.created_by,

            # 时间戳
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Supplier":
        """从字典创建实例"""
        return cls(
            code=data.get("code"),
            short_name=data.get("short_name"),
            name=data.get("name"),
            category=data.get("category"),
            tags=data.get("tags", []),
            status=data.get("status", "active"),
            tax_id=data.get("tax_id"),
            legal_representative=data.get("legal_representative"),
            registered_capital=data.get("registered_capital"),
            established_date=data.get("established_date"),
            business_scope=data.get("business_scope"),
            province=data.get("province"),
            city=data.get("city"),
            district=data.get("district"),
            address=data.get("address"),
            postal_code=data.get("postal_code"),
            contacts=data.get("contacts", []),
            phone=data.get("phone"),
            fax=data.get("fax"),
            email=data.get("email"),
            website=data.get("website"),
            bank_name=data.get("bank_name"),
            bank_account=data.get("bank_account"),
            bank_branch=data.get("bank_branch"),
            main_products=data.get("main_products"),
            currency_default=data.get("currency_default", "CNY"),
            payment_terms=data.get("payment_terms"),
            customer_id=data.get("customer_id"),
            remark=data.get("remark"),
        )

    def update_from_dict(self, data: Dict[str, Any]) -> "Supplier":
        """更新实例"""
        for key in [
            "code", "short_name", "name", "category", "status",
            "tax_id", "legal_representative", "registered_capital",
            "established_date", "business_scope",
            "province", "city", "district", "address", "postal_code",
            "phone", "fax", "email", "website",
            "bank_name", "bank_account", "bank_branch",
            "main_products", "currency_default", "payment_terms",
            "customer_id", "remark",
        ]:
            if key in data:
                setattr(self, key, data.get(key))

        if "contacts" in data:
            self.contacts = data.get("contacts", [])

        if "tags" in data:
            self.tags = data.get("tags", [])

        return self

    @classmethod
    def search(
        cls,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """搜索供应商"""
        query = cls.query

        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    cls.code.ilike(like),
                    cls.short_name.ilike(like),
                    cls.name.ilike(like),
                    cls.main_products.ilike(like),
                )
            )

        if status:
            query = query.filter(cls.status == status)

        if category:
            query = query.filter(cls.category == category)

        # 分页
        total = query.count()
        query = query.order_by(
            case((cls.seq_no.is_(None), 1), else_=0),
            cls.seq_no.asc(),
            cls.id.asc()
        )
        rows = query.offset((page - 1) * page_size).limit(page_size).all()
        pages = (total + page_size - 1) // page_size if page_size else 1

        return {
            "items": [r.to_dict() for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} code={self.code!r} name={self.name!r}>"
