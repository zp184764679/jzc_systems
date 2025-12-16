# -*- coding: utf-8 -*-
"""
物料主数据模型
包含: 物料分类、物料档案
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import enum

from sqlalchemy import Index, func
from sqlalchemy.dialects.mysql import JSON

from app import db


class MaterialStatus(enum.Enum):
    """物料状态枚举"""
    ACTIVE = "active"           # 启用
    INACTIVE = "inactive"       # 停用
    OBSOLETE = "obsolete"       # 淘汰


class MaterialType(enum.Enum):
    """物料类型枚举"""
    RAW = "raw"                 # 原材料
    SEMI = "semi"               # 半成品
    FINISHED = "finished"       # 成品
    CONSUMABLE = "consumable"   # 耗材
    SPARE = "spare"             # 备件
    PACKAGING = "packaging"     # 包装材料
    OTHER = "other"             # 其他


class MaterialCategory(db.Model):
    """物料分类（支持多层级）"""
    __tablename__ = "scm_material_categories"

    id = db.Column(db.Integer, primary_key=True)

    # 分类编码和名称
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)

    # 层级关系
    parent_id = db.Column(db.Integer, db.ForeignKey('scm_material_categories.id'), index=True)
    level = db.Column(db.Integer, default=1)                    # 层级深度 (1, 2, 3...)
    path = db.Column(db.String(255))                            # 层级路径 (如 "1/3/5")

    # 分类属性
    description = db.Column(db.String(500))
    default_uom = db.Column(db.String(32))                      # 默认计量单位

    # 状态
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer)

    # 关系
    parent = db.relationship('MaterialCategory', remote_side=[id], backref='children')
    materials = db.relationship('Material', backref='category', lazy='dynamic')

    __table_args__ = (
        Index("idx_category_parent", "parent_id"),
        Index("idx_category_path", "path"),
    )

    def to_dict(self, include_children=False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "parent_id": self.parent_id,
            "level": self.level,
            "path": self.path,
            "description": self.description,
            "default_uom": self.default_uom,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_children:
            data["children"] = [c.to_dict(include_children=True) for c in self.children if c.is_active]

        return data

    def update_path(self):
        """更新层级路径"""
        if self.parent:
            self.path = f"{self.parent.path}/{self.id}" if self.parent.path else str(self.id)
            self.level = self.parent.level + 1
        else:
            self.path = str(self.id)
            self.level = 1


class Material(db.Model):
    """物料主数据"""
    __tablename__ = "scm_materials"

    id = db.Column(db.Integer, primary_key=True)

    # 物料编码（支持多种编码）
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)   # 内部物料编码
    barcode = db.Column(db.String(64), index=True)                              # 条形码
    customer_code = db.Column(db.String(64))                                    # 客户物料号
    supplier_code = db.Column(db.String(64))                                    # 供应商物料号

    # 基本信息
    name = db.Column(db.String(200), nullable=False)            # 物料名称
    short_name = db.Column(db.String(100))                      # 简称
    english_name = db.Column(db.String(200))                    # 英文名称
    description = db.Column(db.Text)                            # 详细描述

    # 分类
    category_id = db.Column(db.Integer, db.ForeignKey('scm_material_categories.id'), index=True)
    material_type = db.Column(db.String(32), default=MaterialType.RAW.value)    # 物料类型

    # 规格参数
    specification = db.Column(db.String(500))                   # 规格型号
    model = db.Column(db.String(100))                           # 型号
    brand = db.Column(db.String(100))                           # 品牌
    color = db.Column(db.String(50))                            # 颜色
    material = db.Column(db.String(100))                        # 材质

    # 计量单位
    base_uom = db.Column(db.String(32), default='pcs')          # 基本计量单位
    purchase_uom = db.Column(db.String(32))                     # 采购单位
    sales_uom = db.Column(db.String(32))                        # 销售单位
    purchase_conversion = db.Column(db.Numeric(10, 4), default=1)  # 采购单位转换比
    sales_conversion = db.Column(db.Numeric(10, 4), default=1)     # 销售单位转换比

    # 库存参数
    min_stock = db.Column(db.Numeric(12, 2), default=0)         # 最低库存
    max_stock = db.Column(db.Numeric(12, 2))                    # 最高库存
    safety_stock = db.Column(db.Numeric(12, 2), default=0)      # 安全库存
    reorder_point = db.Column(db.Numeric(12, 2))                # 再订货点
    reorder_qty = db.Column(db.Numeric(12, 2))                  # 再订货量

    # 仓储属性
    default_warehouse_id = db.Column(db.Integer)                # 默认仓库ID
    default_bin = db.Column(db.String(64))                      # 默认仓位
    shelf_life_days = db.Column(db.Integer)                     # 保质期（天）
    is_batch_managed = db.Column(db.Boolean, default=False)     # 是否批次管理
    is_serial_managed = db.Column(db.Boolean, default=False)    # 是否序列号管理

    # 采购参数
    default_supplier_id = db.Column(db.Integer)                 # 默认供应商ID
    lead_time_days = db.Column(db.Integer)                      # 采购提前期（天）
    min_order_qty = db.Column(db.Numeric(12, 2))                # 最小订购量

    # 价格信息（参考价）
    reference_cost = db.Column(db.Numeric(14, 4))               # 参考成本
    reference_price = db.Column(db.Numeric(14, 4))              # 参考售价
    currency = db.Column(db.String(8), default='CNY')           # 币种

    # 物理属性
    gross_weight = db.Column(db.Numeric(10, 4))                 # 毛重 (kg)
    net_weight = db.Column(db.Numeric(10, 4))                   # 净重 (kg)
    length = db.Column(db.Numeric(10, 4))                       # 长 (mm)
    width = db.Column(db.Numeric(10, 4))                        # 宽 (mm)
    height = db.Column(db.Numeric(10, 4))                       # 高 (mm)
    volume = db.Column(db.Numeric(12, 6))                       # 体积 (m³)

    # 附件
    image_url = db.Column(db.String(500))                       # 图片URL
    drawing_url = db.Column(db.String(500))                     # 图纸URL
    attachments = db.Column(JSON, default=list)                 # 附件列表

    # 状态
    status = db.Column(db.String(32), default=MaterialStatus.ACTIVE.value, index=True)

    # 备注
    remark = db.Column(db.Text)

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer)

    # 索引
    __table_args__ = (
        Index("idx_material_category", "category_id"),
        Index("idx_material_type_status", "material_type", "status"),
        Index("idx_material_barcode", "barcode"),
    )

    def to_dict(self, include_category=False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "code": self.code,
            "barcode": self.barcode,
            "customer_code": self.customer_code,
            "supplier_code": self.supplier_code,
            "name": self.name,
            "short_name": self.short_name,
            "english_name": self.english_name,
            "description": self.description,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "material_type": self.material_type,
            "specification": self.specification,
            "model": self.model,
            "brand": self.brand,
            "color": self.color,
            "material": self.material,
            "base_uom": self.base_uom,
            "purchase_uom": self.purchase_uom,
            "sales_uom": self.sales_uom,
            "purchase_conversion": float(self.purchase_conversion or 1),
            "sales_conversion": float(self.sales_conversion or 1),
            "min_stock": float(self.min_stock or 0),
            "max_stock": float(self.max_stock) if self.max_stock else None,
            "safety_stock": float(self.safety_stock or 0),
            "reorder_point": float(self.reorder_point) if self.reorder_point else None,
            "reorder_qty": float(self.reorder_qty) if self.reorder_qty else None,
            "default_warehouse_id": self.default_warehouse_id,
            "default_bin": self.default_bin,
            "shelf_life_days": self.shelf_life_days,
            "is_batch_managed": self.is_batch_managed,
            "is_serial_managed": self.is_serial_managed,
            "default_supplier_id": self.default_supplier_id,
            "lead_time_days": self.lead_time_days,
            "min_order_qty": float(self.min_order_qty) if self.min_order_qty else None,
            "reference_cost": float(self.reference_cost) if self.reference_cost else None,
            "reference_price": float(self.reference_price) if self.reference_price else None,
            "currency": self.currency,
            "gross_weight": float(self.gross_weight) if self.gross_weight else None,
            "net_weight": float(self.net_weight) if self.net_weight else None,
            "length": float(self.length) if self.length else None,
            "width": float(self.width) if self.width else None,
            "height": float(self.height) if self.height else None,
            "volume": float(self.volume) if self.volume else None,
            "image_url": self.image_url,
            "drawing_url": self.drawing_url,
            "attachments": self.attachments or [],
            "status": self.status,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }

        if include_category and self.category:
            data["category"] = self.category.to_dict()

        return data

    @staticmethod
    def generate_code(category_code: str = None) -> str:
        """生成物料编码: MAT-YYYYMMDD-XXXX 或 {分类编码}-XXXX"""
        from datetime import datetime

        if category_code:
            prefix = f"{category_code}-"
        else:
            today = datetime.now().strftime("%Y%m%d")
            prefix = f"MAT-{today}-"

        # 获取最大编号
        last = Material.query.filter(
            Material.code.like(f"{prefix}%")
        ).order_by(Material.code.desc()).first()

        if last:
            try:
                last_num = int(last.code.split("-")[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"


class Warehouse(db.Model):
    """仓库主数据"""
    __tablename__ = "scm_warehouses"

    id = db.Column(db.Integer, primary_key=True)

    # 仓库编码和名称
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    short_name = db.Column(db.String(50))

    # 位置信息
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))    # 关联地点
    address = db.Column(db.String(255))

    # 仓库属性
    warehouse_type = db.Column(db.String(32), default='normal')           # 仓库类型: normal/virtual/consignment
    is_allow_negative = db.Column(db.Boolean, default=False)              # 是否允许负库存

    # 负责人
    manager_id = db.Column(db.Integer)
    manager_name = db.Column(db.String(64))
    contact_phone = db.Column(db.String(32))

    # 状态
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    # 备注
    description = db.Column(db.Text)

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer)

    # 关系
    location = db.relationship('Location', backref='warehouses')
    storage_bins = db.relationship('StorageBin', backref='warehouse', lazy='dynamic')

    def to_dict(self, include_bins=False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "short_name": self.short_name,
            "location_id": self.location_id,
            "location_name": self.location.name if self.location else None,
            "address": self.address,
            "warehouse_type": self.warehouse_type,
            "is_allow_negative": self.is_allow_negative,
            "manager_id": self.manager_id,
            "manager_name": self.manager_name,
            "contact_phone": self.contact_phone,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_bins:
            data["bins"] = [b.to_dict() for b in self.storage_bins.filter_by(is_active=True).all()]

        return data


class StorageBin(db.Model):
    """库位（货架/货位）"""
    __tablename__ = "scm_storage_bins"

    id = db.Column(db.Integer, primary_key=True)

    # 库位编码
    code = db.Column(db.String(64), nullable=False, index=True)   # 库位编码
    name = db.Column(db.String(100))                               # 库位名称

    # 所属仓库
    warehouse_id = db.Column(db.Integer, db.ForeignKey('scm_warehouses.id'), nullable=False, index=True)

    # 库位属性
    zone = db.Column(db.String(32))                                # 区域 (A区/B区...)
    aisle = db.Column(db.String(16))                               # 通道
    rack = db.Column(db.String(16))                                # 货架
    level = db.Column(db.String(16))                               # 层
    position = db.Column(db.String(16))                            # 位置

    # 容量
    max_weight = db.Column(db.Numeric(10, 2))                      # 最大承重 (kg)
    max_volume = db.Column(db.Numeric(10, 4))                      # 最大容积 (m³)

    # 用途限制
    bin_type = db.Column(db.String(32), default='storage')         # 类型: storage/picking/receiving/shipping
    allowed_material_types = db.Column(JSON, default=list)         # 允许的物料类型

    # 状态
    is_active = db.Column(db.Boolean, default=True)
    is_occupied = db.Column(db.Boolean, default=False)             # 是否已占用
    sort_order = db.Column(db.Integer, default=0)

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('warehouse_id', 'code', name='uq_warehouse_bin_code'),
        Index("idx_bin_warehouse", "warehouse_id"),
        Index("idx_bin_zone", "zone"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse.name if self.warehouse else None,
            "zone": self.zone,
            "aisle": self.aisle,
            "rack": self.rack,
            "level": self.level,
            "position": self.position,
            "max_weight": float(self.max_weight) if self.max_weight else None,
            "max_volume": float(self.max_volume) if self.max_volume else None,
            "bin_type": self.bin_type,
            "allowed_material_types": self.allowed_material_types or [],
            "is_active": self.is_active,
            "is_occupied": self.is_occupied,
            "sort_order": self.sort_order,
        }

    @property
    def full_code(self) -> str:
        """完整库位编码: 仓库-区域-通道-货架-层-位"""
        parts = [self.warehouse.code if self.warehouse else '']
        if self.zone:
            parts.append(self.zone)
        if self.aisle:
            parts.append(self.aisle)
        if self.rack:
            parts.append(self.rack)
        if self.level:
            parts.append(self.level)
        if self.position:
            parts.append(self.position)
        return '-'.join(filter(None, parts))


class Inventory(db.Model):
    """库存汇总表（实时库存）"""
    __tablename__ = "scm_inventory"

    id = db.Column(db.Integer, primary_key=True)

    # 物料
    material_id = db.Column(db.Integer, db.ForeignKey('scm_materials.id'), nullable=False, index=True)
    material_code = db.Column(db.String(64), index=True)           # 冗余物料编码

    # 仓库和库位
    warehouse_id = db.Column(db.Integer, db.ForeignKey('scm_warehouses.id'), nullable=False, index=True)
    bin_id = db.Column(db.Integer, db.ForeignKey('scm_storage_bins.id'), index=True)

    # 批次/序列号（可选）
    batch_no = db.Column(db.String(64), index=True)                # 批次号
    serial_no = db.Column(db.String(64), index=True)               # 序列号

    # 库存数量
    quantity = db.Column(db.Numeric(14, 4), default=0)             # 库存数量
    reserved_qty = db.Column(db.Numeric(14, 4), default=0)         # 预留数量
    available_qty = db.Column(db.Numeric(14, 4), default=0)        # 可用数量 = quantity - reserved_qty

    # 计量单位
    uom = db.Column(db.String(32), default='pcs')

    # 批次属性
    production_date = db.Column(db.Date)                           # 生产日期
    expiry_date = db.Column(db.Date)                               # 有效期

    # 审计字段
    last_in_date = db.Column(db.DateTime)                          # 最后入库时间
    last_out_date = db.Column(db.DateTime)                         # 最后出库时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    material = db.relationship('Material', backref='inventory_records')
    warehouse = db.relationship('Warehouse', backref='inventory_records')
    bin = db.relationship('StorageBin', backref='inventory_records')

    __table_args__ = (
        db.UniqueConstraint('material_id', 'warehouse_id', 'bin_id', 'batch_no', name='uq_inventory_location'),
        Index("idx_inventory_material", "material_id"),
        Index("idx_inventory_warehouse", "warehouse_id"),
        Index("idx_inventory_batch", "batch_no"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "material_id": self.material_id,
            "material_code": self.material_code,
            "material_name": self.material.name if self.material else None,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse.name if self.warehouse else None,
            "bin_id": self.bin_id,
            "bin_code": self.bin.code if self.bin else None,
            "batch_no": self.batch_no,
            "serial_no": self.serial_no,
            "quantity": float(self.quantity or 0),
            "reserved_qty": float(self.reserved_qty or 0),
            "available_qty": float(self.available_qty or 0),
            "uom": self.uom,
            "production_date": self.production_date.isoformat() if self.production_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "last_in_date": self.last_in_date.isoformat() if self.last_in_date else None,
            "last_out_date": self.last_out_date.isoformat() if self.last_out_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_available_qty(self):
        """更新可用数量"""
        self.available_qty = (self.quantity or 0) - (self.reserved_qty or 0)


# 物料类型名称映射
MATERIAL_TYPE_MAP = {
    MaterialType.RAW.value: "原材料",
    MaterialType.SEMI.value: "半成品",
    MaterialType.FINISHED.value: "成品",
    MaterialType.CONSUMABLE.value: "耗材",
    MaterialType.SPARE.value: "备件",
    MaterialType.PACKAGING.value: "包装材料",
    MaterialType.OTHER.value: "其他",
}

# 物料状态名称映射
MATERIAL_STATUS_MAP = {
    MaterialStatus.ACTIVE.value: "启用",
    MaterialStatus.INACTIVE.value: "停用",
    MaterialStatus.OBSOLETE.value: "淘汰",
}

# 仓库类型名称映射
WAREHOUSE_TYPE_MAP = {
    "normal": "普通仓库",
    "virtual": "虚拟仓库",
    "consignment": "寄售仓库",
}

# 库位类型名称映射
BIN_TYPE_MAP = {
    "storage": "存储位",
    "picking": "拣货位",
    "receiving": "收货位",
    "shipping": "发货位",
}
