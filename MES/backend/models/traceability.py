# MES 物料追溯模型
# Material Traceability Models

from database import db
from datetime import datetime
import enum


class MaterialLotStatus(enum.Enum):
    """物料批次状态"""
    AVAILABLE = "available"          # 可用
    IN_USE = "in_use"                # 使用中
    DEPLETED = "depleted"            # 已耗尽
    QUARANTINE = "quarantine"        # 隔离
    EXPIRED = "expired"              # 已过期


class ProductLotStatus(enum.Enum):
    """产品批次状态"""
    IN_PRODUCTION = "in_production"  # 生产中
    COMPLETED = "completed"          # 已完成
    QUARANTINE = "quarantine"        # 隔离
    SHIPPED = "shipped"              # 已出货
    SCRAPPED = "scrapped"            # 已报废


MATERIAL_LOT_STATUS_LABELS = {
    MaterialLotStatus.AVAILABLE: "可用",
    MaterialLotStatus.IN_USE: "使用中",
    MaterialLotStatus.DEPLETED: "已耗尽",
    MaterialLotStatus.QUARANTINE: "隔离",
    MaterialLotStatus.EXPIRED: "已过期",
}

PRODUCT_LOT_STATUS_LABELS = {
    ProductLotStatus.IN_PRODUCTION: "生产中",
    ProductLotStatus.COMPLETED: "已完成",
    ProductLotStatus.QUARANTINE: "隔离",
    ProductLotStatus.SHIPPED: "已出货",
    ProductLotStatus.SCRAPPED: "已报废",
}


def generate_material_lot_no():
    """生成物料批次号 ML-YYYYMMDD-XXX"""
    from sqlalchemy import func
    today = datetime.now().strftime('%Y%m%d')
    prefix = f'ML-{today}-'
    last = db.session.query(MaterialLot).filter(
        MaterialLot.lot_no.like(f'{prefix}%')
    ).order_by(MaterialLot.lot_no.desc()).first()
    if last:
        seq = int(last.lot_no.split('-')[-1]) + 1
    else:
        seq = 1
    return f'{prefix}{seq:03d}'


def generate_product_lot_no():
    """生成产品批次号 PL-YYYYMMDD-XXX"""
    from sqlalchemy import func
    today = datetime.now().strftime('%Y%m%d')
    prefix = f'PL-{today}-'
    last = db.session.query(ProductLot).filter(
        ProductLot.lot_no.like(f'{prefix}%')
    ).order_by(ProductLot.lot_no.desc()).first()
    if last:
        seq = int(last.lot_no.split('-')[-1]) + 1
    else:
        seq = 1
    return f'{prefix}{seq:03d}'


class MaterialLot(db.Model):
    """物料批次 - 入库物料的批次记录"""
    __tablename__ = 'mes_material_lots'

    id = db.Column(db.Integer, primary_key=True)
    lot_no = db.Column(db.String(50), unique=True, nullable=False, comment='批次号')

    # 物料信息
    material_id = db.Column(db.Integer, comment='物料ID')
    material_code = db.Column(db.String(64), nullable=False, comment='物料编码')
    material_name = db.Column(db.String(200), comment='物料名称')
    specification = db.Column(db.String(200), comment='规格')

    # 数量
    initial_quantity = db.Column(db.Numeric(14, 4), nullable=False, comment='初始数量')
    current_quantity = db.Column(db.Numeric(14, 4), nullable=False, comment='当前数量')
    consumed_quantity = db.Column(db.Numeric(14, 4), default=0, comment='已消耗数量')
    uom = db.Column(db.String(20), default='个', comment='单位')

    # 来源
    source_type = db.Column(db.String(50), comment='来源类型: purchase/transfer/return')
    source_no = db.Column(db.String(64), comment='来源单号（采购单/入库单）')
    supplier_id = db.Column(db.Integer, comment='供应商ID')
    supplier_name = db.Column(db.String(200), comment='供应商名称')

    # 存储
    warehouse_id = db.Column(db.Integer, comment='仓库ID')
    warehouse_name = db.Column(db.String(100), comment='仓库名称')
    bin_code = db.Column(db.String(50), comment='库位编码')

    # 日期
    production_date = db.Column(db.Date, comment='生产日期')
    expiry_date = db.Column(db.Date, comment='有效期')
    receive_date = db.Column(db.Date, default=datetime.now, comment='入库日期')

    # 质量
    inspection_no = db.Column(db.String(50), comment='质检单号')
    inspection_result = db.Column(db.String(20), comment='质检结果')
    certificate_no = db.Column(db.String(100), comment='合格证号')

    # 状态
    status = db.Column(db.String(20), default=MaterialLotStatus.AVAILABLE.value, comment='状态')

    # 备注
    remark = db.Column(db.Text, comment='备注')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer, comment='创建人ID')
    created_by_name = db.Column(db.String(100), comment='创建人姓名')

    def to_dict(self):
        return {
            'id': self.id,
            'lot_no': self.lot_no,
            'material_id': self.material_id,
            'material_code': self.material_code,
            'material_name': self.material_name,
            'specification': self.specification,
            'initial_quantity': float(self.initial_quantity) if self.initial_quantity else 0,
            'current_quantity': float(self.current_quantity) if self.current_quantity else 0,
            'consumed_quantity': float(self.consumed_quantity) if self.consumed_quantity else 0,
            'uom': self.uom,
            'source_type': self.source_type,
            'source_no': self.source_no,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse_name,
            'bin_code': self.bin_code,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'receive_date': self.receive_date.isoformat() if self.receive_date else None,
            'inspection_no': self.inspection_no,
            'inspection_result': self.inspection_result,
            'certificate_no': self.certificate_no,
            'status': self.status,
            'status_label': MATERIAL_LOT_STATUS_LABELS.get(MaterialLotStatus(self.status), self.status) if self.status else None,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
        }


class ProductLot(db.Model):
    """产品批次 - 生产产出的批次记录"""
    __tablename__ = 'mes_product_lots'

    id = db.Column(db.Integer, primary_key=True)
    lot_no = db.Column(db.String(50), unique=True, nullable=False, comment='批次号')

    # 产品信息
    product_id = db.Column(db.Integer, comment='产品ID')
    product_code = db.Column(db.String(64), nullable=False, comment='产品编码')
    product_name = db.Column(db.String(200), comment='产品名称')
    specification = db.Column(db.String(200), comment='规格')

    # 生产信息
    work_order_id = db.Column(db.Integer, comment='工单ID')
    work_order_no = db.Column(db.String(64), comment='工单编号')
    process_id = db.Column(db.Integer, comment='最后工序ID')
    process_name = db.Column(db.String(100), comment='最后工序名称')

    # 数量
    quantity = db.Column(db.Numeric(14, 4), nullable=False, comment='数量')
    uom = db.Column(db.String(20), default='个', comment='单位')

    # 质量
    inspection_no = db.Column(db.String(50), comment='质检单号')
    inspection_result = db.Column(db.String(20), comment='质检结果')
    quality_grade = db.Column(db.String(20), comment='质量等级')

    # 出货
    shipment_id = db.Column(db.Integer, comment='出货单ID')
    shipment_no = db.Column(db.String(64), comment='出货单号')
    customer_id = db.Column(db.Integer, comment='客户ID')
    customer_name = db.Column(db.String(200), comment='客户名称')

    # 日期
    production_date = db.Column(db.Date, default=datetime.now, comment='生产日期')
    completion_date = db.Column(db.Date, comment='完成日期')
    shipment_date = db.Column(db.Date, comment='出货日期')

    # 状态
    status = db.Column(db.String(20), default=ProductLotStatus.IN_PRODUCTION.value, comment='状态')

    # 备注
    remark = db.Column(db.Text, comment='备注')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer, comment='创建人ID')
    created_by_name = db.Column(db.String(100), comment='创建人姓名')

    def to_dict(self):
        return {
            'id': self.id,
            'lot_no': self.lot_no,
            'product_id': self.product_id,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'specification': self.specification,
            'work_order_id': self.work_order_id,
            'work_order_no': self.work_order_no,
            'process_id': self.process_id,
            'process_name': self.process_name,
            'quantity': float(self.quantity) if self.quantity else 0,
            'uom': self.uom,
            'inspection_no': self.inspection_no,
            'inspection_result': self.inspection_result,
            'quality_grade': self.quality_grade,
            'shipment_id': self.shipment_id,
            'shipment_no': self.shipment_no,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'shipment_date': self.shipment_date.isoformat() if self.shipment_date else None,
            'status': self.status,
            'status_label': PRODUCT_LOT_STATUS_LABELS.get(ProductLotStatus(self.status), self.status) if self.status else None,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
        }


class MaterialConsumption(db.Model):
    """物料消耗记录 - 记录生产过程中的物料消耗"""
    __tablename__ = 'mes_material_consumptions'

    id = db.Column(db.Integer, primary_key=True)

    # 消耗对象
    work_order_id = db.Column(db.Integer, nullable=False, comment='工单ID')
    work_order_no = db.Column(db.String(64), comment='工单编号')
    process_id = db.Column(db.Integer, comment='工序ID')
    process_name = db.Column(db.String(100), comment='工序名称')

    # 物料批次
    material_lot_id = db.Column(db.Integer, db.ForeignKey('mes_material_lots.id'), nullable=False, comment='物料批次ID')
    material_code = db.Column(db.String(64), comment='物料编码')
    material_name = db.Column(db.String(200), comment='物料名称')
    lot_no = db.Column(db.String(50), comment='批次号')

    # 产品批次（产出）
    product_lot_id = db.Column(db.Integer, db.ForeignKey('mes_product_lots.id'), comment='产品批次ID')
    product_lot_no = db.Column(db.String(50), comment='产品批次号')

    # 消耗数量
    quantity = db.Column(db.Numeric(14, 4), nullable=False, comment='消耗数量')
    uom = db.Column(db.String(20), default='个', comment='单位')

    # 消耗时间
    consumed_at = db.Column(db.DateTime, default=datetime.now, comment='消耗时间')

    # 操作人
    operator_id = db.Column(db.Integer, comment='操作员ID')
    operator_name = db.Column(db.String(100), comment='操作员姓名')

    # 备注
    remark = db.Column(db.Text, comment='备注')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联
    material_lot = db.relationship('MaterialLot', backref=db.backref('consumptions', lazy='dynamic'))
    product_lot = db.relationship('ProductLot', backref=db.backref('consumptions', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'work_order_id': self.work_order_id,
            'work_order_no': self.work_order_no,
            'process_id': self.process_id,
            'process_name': self.process_name,
            'material_lot_id': self.material_lot_id,
            'material_code': self.material_code,
            'material_name': self.material_name,
            'lot_no': self.lot_no,
            'product_lot_id': self.product_lot_id,
            'product_lot_no': self.product_lot_no,
            'quantity': float(self.quantity) if self.quantity else 0,
            'uom': self.uom,
            'consumed_at': self.consumed_at.isoformat() if self.consumed_at else None,
            'operator_id': self.operator_id,
            'operator_name': self.operator_name,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class TraceRecord(db.Model):
    """追溯记录 - 建立物料批次和产品批次的关联关系"""
    __tablename__ = 'mes_trace_records'

    id = db.Column(db.Integer, primary_key=True)

    # 物料批次
    material_lot_id = db.Column(db.Integer, db.ForeignKey('mes_material_lots.id'), nullable=False, comment='物料批次ID')
    material_lot_no = db.Column(db.String(50), comment='物料批次号')
    material_code = db.Column(db.String(64), comment='物料编码')
    material_name = db.Column(db.String(200), comment='物料名称')

    # 产品批次
    product_lot_id = db.Column(db.Integer, db.ForeignKey('mes_product_lots.id'), nullable=False, comment='产品批次ID')
    product_lot_no = db.Column(db.String(50), comment='产品批次号')
    product_code = db.Column(db.String(64), comment='产品编码')
    product_name = db.Column(db.String(200), comment='产品名称')

    # 工单
    work_order_id = db.Column(db.Integer, comment='工单ID')
    work_order_no = db.Column(db.String(64), comment='工单编号')

    # 消耗数量
    consumed_quantity = db.Column(db.Numeric(14, 4), comment='消耗数量')
    uom = db.Column(db.String(20), comment='单位')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联
    material_lot = db.relationship('MaterialLot', backref=db.backref('trace_records', lazy='dynamic'))
    product_lot = db.relationship('ProductLot', backref=db.backref('trace_records', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'material_lot_id': self.material_lot_id,
            'material_lot_no': self.material_lot_no,
            'material_code': self.material_code,
            'material_name': self.material_name,
            'product_lot_id': self.product_lot_id,
            'product_lot_no': self.product_lot_no,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'work_order_id': self.work_order_id,
            'work_order_no': self.work_order_no,
            'consumed_quantity': float(self.consumed_quantity) if self.consumed_quantity else 0,
            'uom': self.uom,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
