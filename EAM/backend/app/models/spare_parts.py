# EAM 备件管理模型
from datetime import datetime, date
from .. import db
import enum


# ==================== 枚举定义 ====================

class TransactionType(enum.Enum):
    """出入库类型"""
    PURCHASE_IN = "purchase_in"      # 采购入库
    RETURN_IN = "return_in"          # 退还入库
    ADJUST_IN = "adjust_in"          # 盘盈入库
    TRANSFER_IN = "transfer_in"      # 调拨入库
    ISSUE_OUT = "issue_out"          # 领用出库
    SCRAP_OUT = "scrap_out"          # 报废出库
    ADJUST_OUT = "adjust_out"        # 盘亏出库
    TRANSFER_OUT = "transfer_out"    # 调拨出库


TRANSACTION_TYPE_LABELS = {
    "purchase_in": "采购入库",
    "return_in": "退还入库",
    "adjust_in": "盘盈入库",
    "transfer_in": "调拨入库",
    "issue_out": "领用出库",
    "scrap_out": "报废出库",
    "adjust_out": "盘亏出库",
    "transfer_out": "调拨出库",
}


# ==================== 备件分类模型 ====================

class SparePartCategory(db.Model):
    """备件分类"""
    __tablename__ = "eam_spare_part_categories"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, comment="分类编码")
    name = db.Column(db.String(100), nullable=False, comment="分类名称")
    parent_id = db.Column(db.Integer, db.ForeignKey("eam_spare_part_categories.id"), nullable=True, comment="父分类ID")
    level = db.Column(db.Integer, default=1, comment="层级")
    sort_order = db.Column(db.Integer, default=0, comment="排序序号")
    description = db.Column(db.Text, nullable=True, comment="描述")
    is_active = db.Column(db.Boolean, default=True, comment="是否启用")
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    parent = db.relationship("SparePartCategory", remote_side=[id], backref="children")
    spare_parts = db.relationship("SparePart", back_populates="category", lazy="dynamic")

    def to_dict(self, include_children=False):
        data = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "parent_id": self.parent_id,
            "level": self.level,
            "sort_order": self.sort_order,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
        if include_children:
            data["children"] = [c.to_dict(include_children=True) for c in self.children]
        return data


# ==================== 备件模型 ====================

class SparePart(db.Model):
    """备件"""
    __tablename__ = "eam_spare_parts"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, comment="备件编码")
    name = db.Column(db.String(200), nullable=False, comment="备件名称")
    category_id = db.Column(db.Integer, db.ForeignKey("eam_spare_part_categories.id"), nullable=True, comment="分类ID")

    # 规格参数
    specification = db.Column(db.String(200), nullable=True, comment="规格型号")
    brand = db.Column(db.String(100), nullable=True, comment="品牌")
    manufacturer = db.Column(db.String(200), nullable=True, comment="制造商")
    unit = db.Column(db.String(20), default="个", comment="计量单位")

    # 库存信息
    current_stock = db.Column(db.Integer, default=0, comment="当前库存")
    min_stock = db.Column(db.Integer, default=0, comment="最低库存")
    max_stock = db.Column(db.Integer, default=0, comment="最高库存")
    safety_stock = db.Column(db.Integer, default=0, comment="安全库存")

    # 价格信息
    unit_price = db.Column(db.Float, default=0, comment="单价")
    currency = db.Column(db.String(10), default="CNY", comment="币种")

    # 存储位置
    warehouse = db.Column(db.String(100), nullable=True, comment="仓库")
    location = db.Column(db.String(100), nullable=True, comment="库位")

    # 关联设备
    applicable_machines = db.Column(db.JSON, nullable=True, comment="适用设备列表 [{machine_id, machine_code, machine_name}]")

    # 其他信息
    description = db.Column(db.Text, nullable=True, comment="描述")
    image_url = db.Column(db.String(500), nullable=True, comment="图片URL")
    supplier = db.Column(db.String(200), nullable=True, comment="供应商")
    lead_time_days = db.Column(db.Integer, default=7, comment="采购周期（天）")

    is_active = db.Column(db.Boolean, default=True, comment="是否启用")
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.String(50), nullable=True, comment="创建人")

    # 关系
    category = db.relationship("SparePartCategory", back_populates="spare_parts")
    transactions = db.relationship("SparePartTransaction", back_populates="spare_part", lazy="dynamic")

    @property
    def stock_status(self):
        """库存状态"""
        if self.current_stock <= 0:
            return "out_of_stock"
        elif self.current_stock <= self.safety_stock:
            return "low_stock"
        elif self.max_stock > 0 and self.current_stock >= self.max_stock:
            return "over_stock"
        return "normal"

    @property
    def stock_status_label(self):
        status_labels = {
            "out_of_stock": "缺货",
            "low_stock": "库存不足",
            "over_stock": "库存过高",
            "normal": "正常"
        }
        return status_labels.get(self.stock_status, "正常")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "specification": self.specification,
            "brand": self.brand,
            "manufacturer": self.manufacturer,
            "unit": self.unit,
            "current_stock": self.current_stock,
            "min_stock": self.min_stock,
            "max_stock": self.max_stock,
            "safety_stock": self.safety_stock,
            "stock_status": self.stock_status,
            "stock_status_label": self.stock_status_label,
            "unit_price": self.unit_price,
            "currency": self.currency,
            "warehouse": self.warehouse,
            "location": self.location,
            "applicable_machines": self.applicable_machines or [],
            "description": self.description,
            "image_url": self.image_url,
            "supplier": self.supplier,
            "lead_time_days": self.lead_time_days,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
            "created_by": self.created_by,
        }

    def to_option(self):
        """用于下拉选项"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "specification": self.specification,
            "unit": self.unit,
            "current_stock": self.current_stock,
            "unit_price": self.unit_price,
        }


# ==================== 备件出入库记录 ====================

class SparePartTransaction(db.Model):
    """备件出入库记录"""
    __tablename__ = "eam_spare_part_transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_no = db.Column(db.String(50), unique=True, nullable=False, comment="单据编号")
    spare_part_id = db.Column(db.Integer, db.ForeignKey("eam_spare_parts.id"), nullable=False, comment="备件ID")

    transaction_type = db.Column(db.String(20), nullable=False, comment="出入库类型")
    quantity = db.Column(db.Integer, nullable=False, comment="数量（正数入库，负数出库）")
    unit_price = db.Column(db.Float, default=0, comment="单价")
    total_amount = db.Column(db.Float, default=0, comment="总金额")

    # 库存变化
    before_stock = db.Column(db.Integer, default=0, comment="变动前库存")
    after_stock = db.Column(db.Integer, default=0, comment="变动后库存")

    # 关联单据
    reference_type = db.Column(db.String(50), nullable=True, comment="关联单据类型")
    reference_id = db.Column(db.Integer, nullable=True, comment="关联单据ID")
    reference_no = db.Column(db.String(50), nullable=True, comment="关联单据号")

    # 关联设备
    machine_id = db.Column(db.Integer, nullable=True, comment="关联设备ID")
    machine_code = db.Column(db.String(50), nullable=True, comment="关联设备编码")
    machine_name = db.Column(db.String(200), nullable=True, comment="关联设备名称")

    # 操作信息
    transaction_date = db.Column(db.Date, default=date.today, comment="出入库日期")
    operator_id = db.Column(db.Integer, nullable=True, comment="操作人ID")
    operator_name = db.Column(db.String(50), nullable=True, comment="操作人姓名")

    remark = db.Column(db.Text, nullable=True, comment="备注")
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关系
    spare_part = db.relationship("SparePart", back_populates="transactions")

    @property
    def transaction_type_label(self):
        return TRANSACTION_TYPE_LABELS.get(self.transaction_type, self.transaction_type)

    @property
    def direction(self):
        """出入库方向"""
        if self.transaction_type in ["purchase_in", "return_in", "adjust_in", "transfer_in"]:
            return "in"
        return "out"

    @property
    def direction_label(self):
        return "入库" if self.direction == "in" else "出库"

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_no": self.transaction_no,
            "spare_part_id": self.spare_part_id,
            "spare_part_code": self.spare_part.code if self.spare_part else None,
            "spare_part_name": self.spare_part.name if self.spare_part else None,
            "transaction_type": self.transaction_type,
            "transaction_type_label": self.transaction_type_label,
            "direction": self.direction,
            "direction_label": self.direction_label,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_amount": self.total_amount,
            "before_stock": self.before_stock,
            "after_stock": self.after_stock,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "reference_no": self.reference_no,
            "machine_id": self.machine_id,
            "machine_code": self.machine_code,
            "machine_name": self.machine_name,
            "transaction_date": self.transaction_date.strftime("%Y-%m-%d") if self.transaction_date else None,
            "operator_id": self.operator_id,
            "operator_name": self.operator_name,
            "remark": self.remark,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }


# ==================== 辅助函数 ====================

def generate_spare_part_code():
    """生成备件编码"""
    today = date.today()
    prefix = f"SP{today.strftime('%y%m')}"

    # 查询当月最大编号
    last = SparePart.query.filter(
        SparePart.code.like(f"{prefix}%")
    ).order_by(SparePart.code.desc()).first()

    if last and last.code:
        try:
            seq = int(last.code[-4:]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"


def generate_transaction_no():
    """生成出入库单号"""
    today = date.today()
    prefix = f"TXN{today.strftime('%Y%m%d')}"

    # 查询当日最大编号
    last = SparePartTransaction.query.filter(
        SparePartTransaction.transaction_no.like(f"{prefix}%")
    ).order_by(SparePartTransaction.transaction_no.desc()).first()

    if last and last.transaction_no:
        try:
            seq = int(last.transaction_no[-4:]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"


def generate_category_code(parent_code=None):
    """生成分类编码"""
    if parent_code:
        # 子分类编码
        prefix = parent_code
        last = SparePartCategory.query.filter(
            SparePartCategory.code.like(f"{prefix}%"),
            SparePartCategory.code != parent_code
        ).order_by(SparePartCategory.code.desc()).first()

        if last and last.code:
            try:
                seq = int(last.code[-2:]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:02d}"
    else:
        # 顶级分类编码
        prefix = "C"
        last = SparePartCategory.query.filter(
            SparePartCategory.code.like(f"{prefix}%"),
            SparePartCategory.parent_id.is_(None)
        ).order_by(SparePartCategory.code.desc()).first()

        if last and last.code:
            try:
                seq = int(last.code[1:3]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:02d}"
