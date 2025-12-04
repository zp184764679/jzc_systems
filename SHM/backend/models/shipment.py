from datetime import datetime
from extensions import db


class Shipment(db.Model):
    """出货单主表"""
    __tablename__ = 'shm_shipments'

    id = db.Column(db.Integer, primary_key=True)
    shipment_no = db.Column(db.String(50), unique=True, nullable=False, comment='出货单号')
    order_no = db.Column(db.String(50), comment='订单号')
    customer_id = db.Column(db.String(50), comment='客户ID')
    customer_name = db.Column(db.String(200), comment='客户名称')
    delivery_date = db.Column(db.Date, comment='出货日期')
    expected_arrival = db.Column(db.Date, comment='预计到达日期')
    shipping_method = db.Column(db.String(50), comment='运输方式：快递/物流/自提')
    carrier = db.Column(db.String(100), comment='承运商')
    tracking_no = db.Column(db.String(100), comment='物流单号')
    status = db.Column(db.String(20), default='待出货', comment='状态：待出货/已发货/已签收/已取消')
    warehouse_id = db.Column(db.String(50), comment='发货仓库')
    warehouse_contact = db.Column(db.String(100), comment='仓库联系人')
    warehouse_phone = db.Column(db.String(50), comment='仓库联系电话')

    # 收货地址信息
    receiver_contact = db.Column(db.String(100), comment='收货联系人')
    receiver_phone = db.Column(db.String(50), comment='收货联系电话')
    receiver_address = db.Column(db.String(500), comment='收货地址')

    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联出货明细
    items = db.relationship('ShipmentItem', backref='shipment', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'shipment_no': self.shipment_no,
            'order_no': self.order_no,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'expected_arrival': self.expected_arrival.isoformat() if self.expected_arrival else None,
            'shipping_method': self.shipping_method,
            'carrier': self.carrier,
            'tracking_no': self.tracking_no,
            'status': self.status,
            'warehouse_id': self.warehouse_id,
            'warehouse_contact': self.warehouse_contact,
            'warehouse_phone': self.warehouse_phone,
            'receiver_contact': self.receiver_contact,
            'receiver_phone': self.receiver_phone,
            'receiver_address': self.receiver_address,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items]
        }


class ShipmentItem(db.Model):
    """出货明细"""
    __tablename__ = 'shm_shipment_items'

    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shm_shipments.id'), nullable=False)
    product_code = db.Column(db.String(100), comment='产品编码/内部图号')
    product_name = db.Column(db.String(200), comment='产品名称')
    qty = db.Column(db.Numeric(10, 2), comment='数量')
    unit = db.Column(db.String(20), default='个', comment='单位')
    bin_code = db.Column(db.String(50), comment='仓位')
    batch_no = db.Column(db.String(50), comment='批次号')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'qty': float(self.qty) if self.qty else 0,
            'unit': self.unit,
            'bin_code': self.bin_code,
            'batch_no': self.batch_no,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CustomerAddress(db.Model):
    """客户收货地址"""
    __tablename__ = 'shm_customer_addresses'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(50), comment='客户ID')
    customer_name = db.Column(db.String(200), comment='客户名称')
    contact_person = db.Column(db.String(100), comment='联系人')
    contact_phone = db.Column(db.String(50), comment='联系电话')
    province = db.Column(db.String(50), comment='省份')
    city = db.Column(db.String(50), comment='城市')
    district = db.Column(db.String(50), comment='区县')
    address = db.Column(db.String(500), comment='详细地址')
    postal_code = db.Column(db.String(20), comment='邮编')
    is_default = db.Column(db.Boolean, default=False, comment='是否默认')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'province': self.province,
            'city': self.city,
            'district': self.district,
            'address': self.address,
            'postal_code': self.postal_code,
            'is_default': self.is_default,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def full_address(self):
        """完整地址"""
        parts = [self.province, self.city, self.district, self.address]
        return ''.join([p for p in parts if p])


class DeliveryRequirement(db.Model):
    """交货要求/提示"""
    __tablename__ = 'shm_delivery_requirements'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(50), comment='客户ID')
    customer_name = db.Column(db.String(200), comment='客户名称')
    packaging_type = db.Column(db.String(50), comment='包装类型：标准/防潮/防震/真空')
    packaging_material = db.Column(db.String(50), comment='包装材料：纸箱/木箱/泡沫/托盘')
    labeling_requirement = db.Column(db.String(200), comment='标签要求：产品标签/条码/二维码')
    delivery_time_window = db.Column(db.String(100), comment='送货时间窗口')
    special_instructions = db.Column(db.Text, comment='特殊说明')
    quality_cert_required = db.Column(db.Boolean, default=False, comment='是否需要质检报告')
    packing_list_format = db.Column(db.String(100), comment='装箱单格式')
    invoice_requirement = db.Column(db.String(200), comment='发票要求')
    remark = db.Column(db.Text, comment='其他备注')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'packaging_type': self.packaging_type,
            'packaging_material': self.packaging_material,
            'labeling_requirement': self.labeling_requirement,
            'delivery_time_window': self.delivery_time_window,
            'special_instructions': self.special_instructions,
            'quality_cert_required': self.quality_cert_required,
            'packing_list_format': self.packing_list_format,
            'invoice_requirement': self.invoice_requirement,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
