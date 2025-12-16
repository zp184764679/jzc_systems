from datetime import datetime
from extensions import db
import enum


class LogisticsEventType(enum.Enum):
    """物流事件类型"""
    CREATED = "created"              # 已创建
    PICKED_UP = "picked_up"          # 已揽收
    IN_TRANSIT = "in_transit"        # 运输中
    ARRIVED = "arrived"              # 已到达
    OUT_FOR_DELIVERY = "out_for_delivery"  # 派送中
    DELIVERED = "delivered"          # 已签收
    EXCEPTION = "exception"          # 异常
    RETURNED = "returned"            # 已退回


class RMAStatus(enum.Enum):
    """RMA退货状态"""
    PENDING = "pending"              # 待审核
    APPROVED = "approved"            # 已批准
    REJECTED = "rejected"            # 已拒绝
    RECEIVING = "receiving"          # 待收货
    RECEIVED = "received"            # 已收货
    INSPECTING = "inspecting"        # 质检中
    COMPLETED = "completed"          # 已完成
    CANCELLED = "cancelled"          # 已取消


class RMAType(enum.Enum):
    """RMA退货类型"""
    QUALITY = "quality"              # 质量问题
    WRONG_ITEM = "wrong_item"        # 发错货
    DAMAGED = "damaged"              # 运输损坏
    EXCESS = "excess"                # 多发货
    OTHER = "other"                  # 其他原因


class RMAHandleMethod(enum.Enum):
    """RMA处理方式"""
    REFUND = "refund"                # 退款
    EXCHANGE = "exchange"            # 换货
    REPAIR = "repair"                # 维修
    CREDIT = "credit"                # 抵扣


RMA_STATUS_LABELS = {
    RMAStatus.PENDING: "待审核",
    RMAStatus.APPROVED: "已批准",
    RMAStatus.REJECTED: "已拒绝",
    RMAStatus.RECEIVING: "待收货",
    RMAStatus.RECEIVED: "已收货",
    RMAStatus.INSPECTING: "质检中",
    RMAStatus.COMPLETED: "已完成",
    RMAStatus.CANCELLED: "已取消",
}


RMA_TYPE_LABELS = {
    RMAType.QUALITY: "质量问题",
    RMAType.WRONG_ITEM: "发错货",
    RMAType.DAMAGED: "运输损坏",
    RMAType.EXCESS: "多发货",
    RMAType.OTHER: "其他原因",
}


RMA_HANDLE_LABELS = {
    RMAHandleMethod.REFUND: "退款",
    RMAHandleMethod.EXCHANGE: "换货",
    RMAHandleMethod.REPAIR: "维修",
    RMAHandleMethod.CREDIT: "抵扣",
}


LOGISTICS_EVENT_LABELS = {
    LogisticsEventType.CREATED: "已创建",
    LogisticsEventType.PICKED_UP: "已揽收",
    LogisticsEventType.IN_TRANSIT: "运输中",
    LogisticsEventType.ARRIVED: "已到达",
    LogisticsEventType.OUT_FOR_DELIVERY: "派送中",
    LogisticsEventType.DELIVERED: "已签收",
    LogisticsEventType.EXCEPTION: "异常",
    LogisticsEventType.RETURNED: "已退回",
}


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


class LogisticsTrace(db.Model):
    """物流追踪记录"""
    __tablename__ = 'shm_logistics_traces'

    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shm_shipments.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False, comment='事件类型')
    event_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='事件时间')
    location = db.Column(db.String(200), comment='地点')
    description = db.Column(db.String(500), comment='描述')
    operator = db.Column(db.String(100), comment='操作人')
    operator_phone = db.Column(db.String(50), comment='操作人电话')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联出货单
    shipment = db.relationship('Shipment', backref=db.backref('traces', lazy=True, order_by='LogisticsTrace.event_time.desc()'))

    def to_dict(self):
        event_label = LOGISTICS_EVENT_LABELS.get(
            LogisticsEventType(self.event_type) if self.event_type in [e.value for e in LogisticsEventType] else None,
            self.event_type
        )
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'event_type': self.event_type,
            'event_type_label': event_label,
            'event_time': self.event_time.strftime('%Y-%m-%d %H:%M:%S') if self.event_time else None,
            'location': self.location,
            'description': self.description,
            'operator': self.operator,
            'operator_phone': self.operator_phone,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DeliveryReceipt(db.Model):
    """签收回执"""
    __tablename__ = 'shm_delivery_receipts'

    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shm_shipments.id'), nullable=False, unique=True)
    receiver_name = db.Column(db.String(100), nullable=False, comment='签收人姓名')
    receiver_phone = db.Column(db.String(50), comment='签收人电话')
    receiver_id_card = db.Column(db.String(50), comment='签收人身份证')
    sign_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='签收时间')
    sign_location = db.Column(db.String(200), comment='签收地点')
    sign_photo = db.Column(db.String(500), comment='签收照片路径')
    signature_image = db.Column(db.String(500), comment='签名图片路径')
    receipt_condition = db.Column(db.String(50), default='完好', comment='收货状况：完好/部分损坏/严重损坏')
    damage_description = db.Column(db.Text, comment='损坏描述')
    damage_photos = db.Column(db.Text, comment='损坏照片路径（JSON数组）')
    actual_qty = db.Column(db.Numeric(10, 2), comment='实际收货数量')
    qty_difference = db.Column(db.Numeric(10, 2), comment='数量差异')
    difference_reason = db.Column(db.Text, comment='差异原因')
    feedback = db.Column(db.Text, comment='客户反馈')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联出货单
    shipment = db.relationship('Shipment', backref=db.backref('receipt', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'receiver_name': self.receiver_name,
            'receiver_phone': self.receiver_phone,
            'receiver_id_card': self.receiver_id_card,
            'sign_time': self.sign_time.strftime('%Y-%m-%d %H:%M:%S') if self.sign_time else None,
            'sign_location': self.sign_location,
            'sign_photo': self.sign_photo,
            'signature_image': self.signature_image,
            'receipt_condition': self.receipt_condition,
            'damage_description': self.damage_description,
            'damage_photos': self.damage_photos,
            'actual_qty': float(self.actual_qty) if self.actual_qty else None,
            'qty_difference': float(self.qty_difference) if self.qty_difference else None,
            'difference_reason': self.difference_reason,
            'feedback': self.feedback,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class RMAOrder(db.Model):
    """RMA退货申请单"""
    __tablename__ = 'shm_rma_orders'

    id = db.Column(db.Integer, primary_key=True)
    rma_no = db.Column(db.String(50), unique=True, nullable=False, comment='RMA单号')
    shipment_id = db.Column(db.Integer, db.ForeignKey('shm_shipments.id'), comment='原出货单ID')
    shipment_no = db.Column(db.String(50), comment='原出货单号')
    customer_id = db.Column(db.String(50), comment='客户ID')
    customer_name = db.Column(db.String(200), comment='客户名称')

    # 退货类型和原因
    rma_type = db.Column(db.String(50), nullable=False, comment='退货类型')
    reason = db.Column(db.Text, comment='退货原因详述')

    # 状态
    status = db.Column(db.String(50), default='pending', comment='状态')

    # 处理方式
    handle_method = db.Column(db.String(50), comment='处理方式')

    # 日期
    apply_date = db.Column(db.Date, default=datetime.now, comment='申请日期')
    approved_date = db.Column(db.Date, comment='审批日期')
    received_date = db.Column(db.Date, comment='收货日期')
    completed_date = db.Column(db.Date, comment='完成日期')

    # 退货地址
    return_address = db.Column(db.String(500), comment='退货地址')
    return_contact = db.Column(db.String(100), comment='退货联系人')
    return_phone = db.Column(db.String(50), comment='退货联系电话')

    # 物流信息
    return_carrier = db.Column(db.String(100), comment='退货承运商')
    return_tracking_no = db.Column(db.String(100), comment='退货物流单号')

    # 质检结果
    inspection_result = db.Column(db.String(50), comment='质检结果：合格/不合格/部分合格')
    inspection_note = db.Column(db.Text, comment='质检备注')
    inspected_by = db.Column(db.Integer, comment='质检人ID')
    inspected_by_name = db.Column(db.String(100), comment='质检人姓名')
    inspected_at = db.Column(db.DateTime, comment='质检时间')

    # 处理结果
    refund_amount = db.Column(db.Numeric(14, 2), comment='退款金额')
    exchange_shipment_no = db.Column(db.String(50), comment='换货出货单号')
    credit_amount = db.Column(db.Numeric(14, 2), comment='抵扣金额')

    # 附件
    photos = db.Column(db.Text, comment='问题照片（JSON数组）')
    attachments = db.Column(db.Text, comment='附件（JSON数组）')

    # 操作人
    created_by = db.Column(db.Integer, comment='创建人ID')
    created_by_name = db.Column(db.String(100), comment='创建人姓名')
    approved_by = db.Column(db.Integer, comment='审批人ID')
    approved_by_name = db.Column(db.String(100), comment='审批人姓名')
    reject_reason = db.Column(db.Text, comment='拒绝原因')

    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    items = db.relationship('RMAItem', backref='rma_order', lazy=True, cascade='all, delete-orphan')
    shipment = db.relationship('Shipment', backref=db.backref('rma_orders', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'rma_no': self.rma_no,
            'shipment_id': self.shipment_id,
            'shipment_no': self.shipment_no,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'rma_type': self.rma_type,
            'rma_type_label': RMA_TYPE_LABELS.get(RMAType(self.rma_type), self.rma_type) if self.rma_type else None,
            'reason': self.reason,
            'status': self.status,
            'status_label': RMA_STATUS_LABELS.get(RMAStatus(self.status), self.status) if self.status else None,
            'handle_method': self.handle_method,
            'handle_method_label': RMA_HANDLE_LABELS.get(RMAHandleMethod(self.handle_method), self.handle_method) if self.handle_method else None,
            'apply_date': self.apply_date.isoformat() if self.apply_date else None,
            'approved_date': self.approved_date.isoformat() if self.approved_date else None,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'return_address': self.return_address,
            'return_contact': self.return_contact,
            'return_phone': self.return_phone,
            'return_carrier': self.return_carrier,
            'return_tracking_no': self.return_tracking_no,
            'inspection_result': self.inspection_result,
            'inspection_note': self.inspection_note,
            'inspected_by': self.inspected_by,
            'inspected_by_name': self.inspected_by_name,
            'inspected_at': self.inspected_at.isoformat() if self.inspected_at else None,
            'refund_amount': float(self.refund_amount) if self.refund_amount else None,
            'exchange_shipment_no': self.exchange_shipment_no,
            'credit_amount': float(self.credit_amount) if self.credit_amount else None,
            'photos': self.photos,
            'attachments': self.attachments,
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
            'approved_by': self.approved_by,
            'approved_by_name': self.approved_by_name,
            'reject_reason': self.reject_reason,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items],
            'total_return_qty': sum(float(item.return_qty or 0) for item in self.items),
        }


class RMAItem(db.Model):
    """RMA退货明细"""
    __tablename__ = 'shm_rma_items'

    id = db.Column(db.Integer, primary_key=True)
    rma_id = db.Column(db.Integer, db.ForeignKey('shm_rma_orders.id'), nullable=False)
    shipment_item_id = db.Column(db.Integer, comment='原出货明细ID')
    product_code = db.Column(db.String(100), comment='产品编码')
    product_name = db.Column(db.String(200), comment='产品名称')
    original_qty = db.Column(db.Numeric(10, 2), comment='原出货数量')
    return_qty = db.Column(db.Numeric(10, 2), nullable=False, comment='退货数量')
    unit = db.Column(db.String(20), default='个', comment='单位')
    batch_no = db.Column(db.String(50), comment='批次号')

    # 质检
    inspected_qty = db.Column(db.Numeric(10, 2), comment='检验数量')
    qualified_qty = db.Column(db.Numeric(10, 2), comment='合格数量')
    unqualified_qty = db.Column(db.Numeric(10, 2), comment='不合格数量')

    # 处理
    restocked_qty = db.Column(db.Numeric(10, 2), comment='重新入库数量')
    scrapped_qty = db.Column(db.Numeric(10, 2), comment='报废数量')

    unit_price = db.Column(db.Numeric(14, 4), comment='单价')
    amount = db.Column(db.Numeric(14, 2), comment='金额')

    defect_description = db.Column(db.Text, comment='缺陷描述')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'rma_id': self.rma_id,
            'shipment_item_id': self.shipment_item_id,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'original_qty': float(self.original_qty) if self.original_qty else None,
            'return_qty': float(self.return_qty) if self.return_qty else 0,
            'unit': self.unit,
            'batch_no': self.batch_no,
            'inspected_qty': float(self.inspected_qty) if self.inspected_qty else None,
            'qualified_qty': float(self.qualified_qty) if self.qualified_qty else None,
            'unqualified_qty': float(self.unqualified_qty) if self.unqualified_qty else None,
            'restocked_qty': float(self.restocked_qty) if self.restocked_qty else None,
            'scrapped_qty': float(self.scrapped_qty) if self.scrapped_qty else None,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'amount': float(self.amount) if self.amount else None,
            'defect_description': self.defect_description,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
