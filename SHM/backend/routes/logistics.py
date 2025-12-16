"""
物流追踪路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from extensions import db
from models.shipment import (
    Shipment, LogisticsTrace, DeliveryReceipt,
    LogisticsEventType, LOGISTICS_EVENT_LABELS
)

logistics_bp = Blueprint('logistics', __name__)


@logistics_bp.route('/shipments/<int:shipment_id>/traces', methods=['GET'])
def get_traces(shipment_id):
    """获取出货单的物流轨迹"""
    shipment = Shipment.query.get_or_404(shipment_id)
    traces = LogisticsTrace.query.filter_by(shipment_id=shipment_id)\
        .order_by(LogisticsTrace.event_time.desc()).all()

    return jsonify({
        'code': 0,
        'data': {
            'shipment_no': shipment.shipment_no,
            'tracking_no': shipment.tracking_no,
            'carrier': shipment.carrier,
            'status': shipment.status,
            'traces': [t.to_dict() for t in traces]
        }
    })


@logistics_bp.route('/shipments/<int:shipment_id>/traces', methods=['POST'])
def add_trace(shipment_id):
    """添加物流轨迹"""
    shipment = Shipment.query.get_or_404(shipment_id)
    data = request.get_json()

    # 验证事件类型
    event_type = data.get('event_type')
    valid_types = [e.value for e in LogisticsEventType]
    if event_type not in valid_types:
        return jsonify({
            'code': 1,
            'message': f'无效的事件类型，有效类型: {valid_types}'
        }), 400

    # 创建轨迹记录
    trace = LogisticsTrace(
        shipment_id=shipment_id,
        event_type=event_type,
        event_time=datetime.strptime(data['event_time'], '%Y-%m-%d %H:%M:%S') if data.get('event_time') else datetime.now(),
        location=data.get('location'),
        description=data.get('description'),
        operator=data.get('operator'),
        operator_phone=data.get('operator_phone'),
        remark=data.get('remark')
    )

    db.session.add(trace)

    # 根据事件类型更新出货单状态
    if event_type == LogisticsEventType.PICKED_UP.value:
        shipment.status = '已发货'
    elif event_type == LogisticsEventType.DELIVERED.value:
        shipment.status = '已签收'
    elif event_type == LogisticsEventType.RETURNED.value:
        shipment.status = '已退回'

    db.session.commit()

    return jsonify({
        'code': 0,
        'message': '添加成功',
        'data': trace.to_dict()
    })


@logistics_bp.route('/traces/<int:trace_id>', methods=['PUT'])
def update_trace(trace_id):
    """更新物流轨迹"""
    trace = LogisticsTrace.query.get_or_404(trace_id)
    data = request.get_json()

    if 'event_type' in data:
        valid_types = [e.value for e in LogisticsEventType]
        if data['event_type'] not in valid_types:
            return jsonify({
                'code': 1,
                'message': f'无效的事件类型，有效类型: {valid_types}'
            }), 400
        trace.event_type = data['event_type']

    if 'event_time' in data:
        trace.event_time = datetime.strptime(data['event_time'], '%Y-%m-%d %H:%M:%S')
    if 'location' in data:
        trace.location = data['location']
    if 'description' in data:
        trace.description = data['description']
    if 'operator' in data:
        trace.operator = data['operator']
    if 'operator_phone' in data:
        trace.operator_phone = data['operator_phone']
    if 'remark' in data:
        trace.remark = data['remark']

    db.session.commit()

    return jsonify({
        'code': 0,
        'message': '更新成功',
        'data': trace.to_dict()
    })


@logistics_bp.route('/traces/<int:trace_id>', methods=['DELETE'])
def delete_trace(trace_id):
    """删除物流轨迹"""
    trace = LogisticsTrace.query.get_or_404(trace_id)
    db.session.delete(trace)
    db.session.commit()

    return jsonify({
        'code': 0,
        'message': '删除成功'
    })


# ==================== 签收回执 ====================

@logistics_bp.route('/shipments/<int:shipment_id>/receipt', methods=['GET'])
def get_receipt(shipment_id):
    """获取签收回执"""
    shipment = Shipment.query.get_or_404(shipment_id)
    receipt = DeliveryReceipt.query.filter_by(shipment_id=shipment_id).first()

    return jsonify({
        'code': 0,
        'data': {
            'shipment_no': shipment.shipment_no,
            'receipt': receipt.to_dict() if receipt else None
        }
    })


@logistics_bp.route('/shipments/<int:shipment_id>/receipt', methods=['POST'])
def create_receipt(shipment_id):
    """创建签收回执"""
    shipment = Shipment.query.get_or_404(shipment_id)

    # 检查是否已有签收回执
    existing = DeliveryReceipt.query.filter_by(shipment_id=shipment_id).first()
    if existing:
        return jsonify({
            'code': 1,
            'message': '该出货单已有签收回执'
        }), 400

    data = request.get_json()

    # 创建签收回执
    receipt = DeliveryReceipt(
        shipment_id=shipment_id,
        receiver_name=data.get('receiver_name'),
        receiver_phone=data.get('receiver_phone'),
        receiver_id_card=data.get('receiver_id_card'),
        sign_time=datetime.strptime(data['sign_time'], '%Y-%m-%d %H:%M:%S') if data.get('sign_time') else datetime.now(),
        sign_location=data.get('sign_location'),
        sign_photo=data.get('sign_photo'),
        signature_image=data.get('signature_image'),
        receipt_condition=data.get('receipt_condition', '完好'),
        damage_description=data.get('damage_description'),
        damage_photos=data.get('damage_photos'),
        actual_qty=data.get('actual_qty'),
        qty_difference=data.get('qty_difference'),
        difference_reason=data.get('difference_reason'),
        feedback=data.get('feedback'),
        remark=data.get('remark')
    )

    db.session.add(receipt)

    # 更新出货单状态为已签收
    shipment.status = '已签收'

    # 自动添加签收轨迹
    trace = LogisticsTrace(
        shipment_id=shipment_id,
        event_type=LogisticsEventType.DELIVERED.value,
        event_time=receipt.sign_time,
        location=receipt.sign_location,
        description=f'已签收，签收人：{receipt.receiver_name}',
        operator=receipt.receiver_name,
        operator_phone=receipt.receiver_phone
    )
    db.session.add(trace)

    db.session.commit()

    return jsonify({
        'code': 0,
        'message': '签收成功',
        'data': receipt.to_dict()
    })


@logistics_bp.route('/shipments/<int:shipment_id>/receipt', methods=['PUT'])
def update_receipt(shipment_id):
    """更新签收回执"""
    receipt = DeliveryReceipt.query.filter_by(shipment_id=shipment_id).first()
    if not receipt:
        return jsonify({
            'code': 1,
            'message': '签收回执不存在'
        }), 404

    data = request.get_json()

    if 'receiver_name' in data:
        receipt.receiver_name = data['receiver_name']
    if 'receiver_phone' in data:
        receipt.receiver_phone = data['receiver_phone']
    if 'receiver_id_card' in data:
        receipt.receiver_id_card = data['receiver_id_card']
    if 'sign_time' in data:
        receipt.sign_time = datetime.strptime(data['sign_time'], '%Y-%m-%d %H:%M:%S')
    if 'sign_location' in data:
        receipt.sign_location = data['sign_location']
    if 'sign_photo' in data:
        receipt.sign_photo = data['sign_photo']
    if 'signature_image' in data:
        receipt.signature_image = data['signature_image']
    if 'receipt_condition' in data:
        receipt.receipt_condition = data['receipt_condition']
    if 'damage_description' in data:
        receipt.damage_description = data['damage_description']
    if 'damage_photos' in data:
        receipt.damage_photos = data['damage_photos']
    if 'actual_qty' in data:
        receipt.actual_qty = data['actual_qty']
    if 'qty_difference' in data:
        receipt.qty_difference = data['qty_difference']
    if 'difference_reason' in data:
        receipt.difference_reason = data['difference_reason']
    if 'feedback' in data:
        receipt.feedback = data['feedback']
    if 'remark' in data:
        receipt.remark = data['remark']

    db.session.commit()

    return jsonify({
        'code': 0,
        'message': '更新成功',
        'data': receipt.to_dict()
    })


# ==================== 快速操作 ====================

@logistics_bp.route('/shipments/<int:shipment_id>/ship', methods=['POST'])
def ship_out(shipment_id):
    """发货操作 - 快速更新发货信息并添加轨迹"""
    shipment = Shipment.query.get_or_404(shipment_id)
    data = request.get_json()

    # 更新发货信息
    if 'carrier' in data:
        shipment.carrier = data['carrier']
    if 'tracking_no' in data:
        shipment.tracking_no = data['tracking_no']
    if 'delivery_date' in data:
        shipment.delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
    if 'expected_arrival' in data:
        shipment.expected_arrival = datetime.strptime(data['expected_arrival'], '%Y-%m-%d').date()

    shipment.status = '已发货'

    # 添加发货轨迹
    trace = LogisticsTrace(
        shipment_id=shipment_id,
        event_type=LogisticsEventType.PICKED_UP.value,
        event_time=datetime.now(),
        location=data.get('location', shipment.warehouse_id),
        description=f'已发货，承运商：{shipment.carrier}，运单号：{shipment.tracking_no}',
        operator=data.get('operator'),
        remark=data.get('remark')
    )
    db.session.add(trace)

    db.session.commit()

    return jsonify({
        'code': 0,
        'message': '发货成功',
        'data': shipment.to_dict()
    })


@logistics_bp.route('/shipments/<int:shipment_id>/sign', methods=['POST'])
def sign_delivery(shipment_id):
    """快速签收 - 简化的签收操作"""
    shipment = Shipment.query.get_or_404(shipment_id)
    data = request.get_json()

    # 检查是否已签收
    if shipment.status == '已签收':
        return jsonify({
            'code': 1,
            'message': '该出货单已签收'
        }), 400

    # 创建签收回执
    receipt = DeliveryReceipt(
        shipment_id=shipment_id,
        receiver_name=data.get('receiver_name', shipment.receiver_contact),
        receiver_phone=data.get('receiver_phone', shipment.receiver_phone),
        sign_time=datetime.now(),
        sign_location=data.get('sign_location', shipment.receiver_address),
        receipt_condition=data.get('receipt_condition', '完好'),
        feedback=data.get('feedback'),
        remark=data.get('remark')
    )
    db.session.add(receipt)

    # 更新状态
    shipment.status = '已签收'

    # 添加签收轨迹
    trace = LogisticsTrace(
        shipment_id=shipment_id,
        event_type=LogisticsEventType.DELIVERED.value,
        event_time=datetime.now(),
        location=receipt.sign_location,
        description=f'已签收，签收人：{receipt.receiver_name}',
        operator=receipt.receiver_name,
        operator_phone=receipt.receiver_phone
    )
    db.session.add(trace)

    db.session.commit()

    return jsonify({
        'code': 0,
        'message': '签收成功',
        'data': {
            'shipment': shipment.to_dict(),
            'receipt': receipt.to_dict()
        }
    })


# ==================== 枚举接口 ====================

@logistics_bp.route('/logistics/event-types', methods=['GET'])
def get_event_types():
    """获取物流事件类型枚举"""
    return jsonify({
        'code': 0,
        'data': [
            {'value': e.value, 'label': LOGISTICS_EVENT_LABELS[e]}
            for e in LogisticsEventType
        ]
    })


@logistics_bp.route('/logistics/receipt-conditions', methods=['GET'])
def get_receipt_conditions():
    """获取收货状况枚举"""
    conditions = ['完好', '部分损坏', '严重损坏']
    return jsonify({
        'code': 0,
        'data': [{'value': c, 'label': c} for c in conditions]
    })
