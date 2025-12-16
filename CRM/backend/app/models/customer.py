# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy import Index, or_, case
from sqlalchemy.orm import validates
from sqlalchemy.ext.mutable import MutableList

from .. import db


class Customer(db.Model):
    __tablename__ = "crm_customers"

    # ========== 主键 ==========
    id = db.Column(db.Integer, primary_key=True)

    # ========== 序号 ==========
    seq_no = db.Column(db.Integer, index=True, nullable=True)                   # Excel导入序号

    # ========== 基本信息 ==========
    code = db.Column(db.String(64), index=True, nullable=True)                  # 客户代码
    short_name = db.Column(db.String(128), index=True, nullable=True)           # 客户简称
    name = db.Column(db.String(255), index=True, nullable=True)                 # 客户全称

    # ========== 客户分级 ==========
    grade = db.Column(db.String(32), default='regular', index=True)             # 客户等级: vip/gold/silver/regular
    grade_score = db.Column(db.Integer, default=0)                              # 评分（用于自动分级）
    grade_updated_at = db.Column(db.DateTime, nullable=True)                    # 等级更新时间
    is_key_account = db.Column(db.Boolean, default=False)                       # 是否重点客户

    currency_default = db.Column(db.String(16), nullable=True)                  # 默认币种
    tax_points = db.Column(db.Integer, nullable=True)                           # 含税点数（>=0）
    settlement_cycle_days = db.Column(db.Integer, nullable=True)               # 结算周期（天，>=0）
    settlement_method = db.Column(db.String(64), nullable=True)                 # 结算方式
    statement_day = db.Column(db.Integer, nullable=True)                        # 对账日（1-31 或 0 表示不固定）

    address = db.Column(db.String(512), nullable=True)                          # 公司地址
    remark = db.Column(db.String(1024), nullable=True)                          # 备注

    # 详情区联系人（职位/姓名/电话），JSON 数组：
    # [ {"role":"仓管","name":"王强","phone":"138..."}, ... ]
    # 使用 MutableList 以便局部修改能被追踪
    contacts = db.Column(MutableList.as_mutable(db.JSON), default=list, nullable=False)

    # ========== 扩展字段 ==========
    shipping_method = db.Column(db.String(64), nullable=True)                   # 出货方式
    need_customs = db.Column(db.Boolean, default=False, nullable=False)         # 是否报关
    order_method = db.Column(db.String(64), nullable=True)                      # 接单方式
    delivery_requirements = db.Column(db.String(512), nullable=True)            # 送货要求
    delivery_address = db.Column(db.String(512), nullable=True)                 # 送货地址
    order_status_desc = db.Column(db.String(512), nullable=True)                # 目前订单情况
    sample_dev_desc = db.Column(db.String(512), nullable=True)                  # 样品和开发情况
    has_price_drop_contact = db.Column(db.Boolean, default=False, nullable=False)  # 是否有降价联系

    # ========== 数据权限控制 ==========
    owner_id = db.Column(db.Integer, index=True, nullable=True)                    # 负责人ID（业务员）
    owner_name = db.Column(db.String(64), nullable=True)                           # 负责人姓名
    department_id = db.Column(db.Integer, index=True, nullable=True)               # 所属部门ID
    department_name = db.Column(db.String(128), nullable=True)                     # 所属部门名称
    created_by = db.Column(db.Integer, nullable=True)                              # 创建人ID

    # ========== 审计 ==========
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True, nullable=False
    )

    # ========== 索引（联合索引等）==========
    __table_args__ = (
        # 常用检索组合
        Index("idx_customers_code_name", "code", "name"),
        Index("idx_customers_short_name_name", "short_name", "name"),
    )

    # ---------------- 工具 / 业务方法 ----------------

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "seq_no": self.seq_no,
            "code": self.code or "",
            "short_name": self.short_name or "",
            "name": self.name or "",
            "grade": self.grade or "regular",
            "grade_score": self.grade_score or 0,
            "grade_updated_at": (self.grade_updated_at.isoformat() if self.grade_updated_at else None),
            "is_key_account": bool(self.is_key_account),
            "currency_default": self.currency_default or "",
            "tax_points": self.tax_points,
            "settlement_cycle_days": self.settlement_cycle_days,
            "settlement_method": self.settlement_method or "",
            "statement_day": self.statement_day,
            "address": self.address or "",
            "remark": self.remark or "",
            "contacts": self.contacts or [],

            "shipping_method": self.shipping_method or "",
            "need_customs": bool(self.need_customs),
            "order_method": self.order_method or "",
            "delivery_requirements": self.delivery_requirements or "",
            "delivery_address": self.delivery_address or "",
            "order_status_desc": self.order_status_desc or "",
            "sample_dev_desc": self.sample_dev_desc or "",
            "has_price_drop_contact": bool(self.has_price_drop_contact),

            "owner_id": self.owner_id,
            "owner_name": self.owner_name or "",
            "department_id": self.department_id,
            "department_name": self.department_name or "",
            "created_by": self.created_by,

            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None),
        }

    @staticmethod
    def _normalize_contacts(value: Optional[Iterable[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        规范化联系人列表，确保返回 list[dict] 且键存在。
        只保留常见键：role/name/phone，其他键原样透传。
        """
        if not value:
            return []
        out: List[Dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                # 忽略不合法项
                continue
            norm = dict(item)  # 浅拷贝，保留未知键
            norm.setdefault("role", "")
            norm.setdefault("name", "")
            norm.setdefault("phone", "")
            out.append(norm)
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Customer":
        """
        根据 dict 创建实例（未提交）。
        """
        obj = cls(
            code=data.get("code"),
            short_name=data.get("short_name"),
            name=data.get("name"),
            grade=data.get("grade", "regular"),
            grade_score=data.get("grade_score", 0),
            is_key_account=bool(data.get("is_key_account", False)),
            currency_default=data.get("currency_default"),
            tax_points=data.get("tax_points"),
            settlement_cycle_days=data.get("settlement_cycle_days"),
            settlement_method=data.get("settlement_method"),
            statement_day=data.get("statement_day"),
            address=data.get("address"),
            remark=data.get("remark"),
            contacts=cls._normalize_contacts(data.get("contacts")),
            shipping_method=data.get("shipping_method"),
            need_customs=bool(data.get("need_customs", False)),
            order_method=data.get("order_method"),
            delivery_requirements=data.get("delivery_requirements"),
            delivery_address=data.get("delivery_address"),
            order_status_desc=data.get("order_status_desc"),
            sample_dev_desc=data.get("sample_dev_desc"),
            has_price_drop_contact=bool(data.get("has_price_drop_contact", False)),
        )
        return obj

    def update_from_dict(self, data: Dict[str, Any]) -> "Customer":
        """
        基于 dict 局部更新（未提交）。
        """
        for key in [
            "code", "short_name", "name", "grade", "grade_score",
            "currency_default", "tax_points",
            "settlement_cycle_days", "settlement_method", "statement_day",
            "address", "remark", "shipping_method", "order_method",
            "delivery_requirements", "delivery_address", "order_status_desc",
            "sample_dev_desc",
        ]:
            if key in data:
                setattr(self, key, data.get(key))

        if "need_customs" in data:
            self.need_customs = bool(data.get("need_customs"))

        if "has_price_drop_contact" in data:
            self.has_price_drop_contact = bool(data.get("has_price_drop_contact"))

        if "is_key_account" in data:
            self.is_key_account = bool(data.get("is_key_account"))

        # Update grade timestamp if grade changed
        if "grade" in data and data.get("grade") != self.grade:
            self.grade_updated_at = datetime.utcnow()

        if "contacts" in data:
            self.contacts = self._normalize_contacts(data.get("contacts"))

        return self

    @classmethod
    def paginate_query(
        cls, query, page: int = 1, page_size: int = 20
    ) -> Tuple[List["Customer"], int]:
        """
        通用分页：返回 (rows, total)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20

        total = query.count()
        # 优先按seq_no排序，没有seq_no的按id排序（MySQL兼容）
        rows = query.order_by(case((cls.seq_no.is_(None), 1), else_=0), cls.seq_no.asc(), cls.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
        return rows, total

    @classmethod
    def search(
        cls,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        order_by: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        关键字搜索 + 分页。
        - keyword 会在 code/short_name/name/address/remark 做 ilike 模糊。
        - order_by 可传入模型字段，如 Customer.name.asc()。
        返回：{ items, total, page, page_size, pages }
        """
        query = cls.query

        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    cls.code.ilike(like),
                    cls.short_name.ilike(like),
                    cls.name.ilike(like),
                    cls.address.ilike(like),
                    cls.remark.ilike(like),
                )
            )

        if order_by is not None:
            query = query.order_by(order_by)
        else:
            # 默认按seq_no排序（MySQL兼容）
            query = query.order_by(case((cls.seq_no.is_(None), 1), else_=0), cls.seq_no.asc(), cls.id.asc())

        rows, total = cls.paginate_query(query, page=page, page_size=page_size)
        pages = (total + page_size - 1) // page_size if page_size else 1
        return {
            "items": [r.to_dict() for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    # ---------------- 数据校验 ----------------

    @validates("statement_day")
    def validate_statement_day(self, key: str, value: Optional[int]) -> Optional[int]:
        """
        对账天数（如60表示60天后对账），必须 >= 0。
        """
        if value is None:
            return None
        iv = int(value)
        if iv < 0:
            raise ValueError("statement_day must be >= 0")
        return iv

    @validates("tax_points")
    def validate_tax_points(self, key: str, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        iv = int(value)
        if iv < 0:
            raise ValueError("tax_points must be >= 0")
        return iv

    @validates("settlement_cycle_days")
    def validate_settlement_cycle_days(self, key: str, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        iv = int(value)
        if iv < 0:
            raise ValueError("settlement_cycle_days must be >= 0")
        return iv

    def __repr__(self) -> str:
        return f"<Customer id={self.id} code={self.code!r} short_name={self.short_name!r} name={self.name!r}>"
