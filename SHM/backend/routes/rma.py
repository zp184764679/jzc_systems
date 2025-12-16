# -*- coding: utf-8 -*-
"""
RMA退货管理 API
"""
from datetime import datetime, date
from flask import Blueprint, request, jsonify
from sqlalchemy import or_, desc
from extensions import db
from models.shipment import (
    RMAOrder, RMAItem, Shipment, ShipmentItem,
    RMAStatus, RMAType, RMAHandleMethod,
    RMA_STATUS_LABELS, RMA_TYPE_LABELS, RMA_HANDLE_LABELS
)

rma_bp = Blueprint('rma', __name__)


def generate_rma_no():
    """生成RMA单号 RMA-YYYYMMDD-XXXX"""
    today = date.today().strftime('%Y%m%d')
    prefix = f'RMA-{today}-'

    # 查找当天最大序号
    last_rma = RMAOrder.query.filter(
        RMAOrder.rma_no.like(f'{prefix}%')
    ).order_by(desc(RMAOrder.rma_no)).first()

    if last_rma:
        try:
            last_seq = int(last_rma.rma_no.split('-')[-1])
            new_seq = last_seq + 1
        except (ValueError, IndexError):
            new_seq = 1
    else:
        new_seq = 1

    return f'{prefix}{new_seq:04d}'


@rma_bp.route('/rma', methods=['GET'])
def get_rma_list():
    """获取RMA列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status')
        rma_type = request.args.get('rma_type')
        customer_id = request.args.get('customer_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = RMAOrder.query

        # 搜索条件
        if search:
            query = query.filter(or_(
                RMAOrder.rma_no.ilike(f'%{search}%'),
                RMAOrder.shipment_no.ilike(f'%{search}%'),
                RMAOrder.customer_name.ilike(f'%{search}%'),
            ))

        # 筛选条件
        if status:
            query = query.filter(RMAOrder.status == status)
        if rma_type:
            query = query.filter(RMAOrder.rma_type == rma_type)
        if customer_id:
            query = query.filter(RMAOrder.customer_id == customer_id)
        if start_date:
            query = query.filter(RMAOrder.apply_date >= start_date)
        if end_date:
            query = query.filter(RMAOrder.apply_date <= end_date)

        # 排序和分页
        query = query.order_by(desc(RMAOrder.created_at))
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return jsonify({
            'items': [item.to_dict() for item in items],
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size if page_size else 1
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/<int:id>', methods=['GET'])
def get_rma_detail(id):
    """获取RMA详情"""
    try:
        rma = RMAOrder.query.get(id)
        if not rma:
            return jsonify({'error': 'RMA不存在'}), 404
        return jsonify(rma.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma', methods=['POST'])
def create_rma():
    """创建RMA退货申请"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('rma_type'):
            return jsonify({'error': '请选择退货类型'}), 400
        if not data.get('items') or len(data.get('items', [])) == 0:
            return jsonify({'error': '请添加退货明细'}), 400

        # 生成RMA单号
        rma_no = generate_rma_no()

        # 创建RMA主记录
        rma = RMAOrder(
            rma_no=rma_no,
            shipment_id=data.get('shipment_id'),
            shipment_no=data.get('shipment_no'),
            customer_id=data.get('customer_id'),
            customer_name=data.get('customer_name'),
            rma_type=data.get('rma_type'),
            reason=data.get('reason'),
            status='pending',
            handle_method=data.get('handle_method'),
            apply_date=date.today(),
            return_address=data.get('return_address'),
            return_contact=data.get('return_contact'),
            return_phone=data.get('return_phone'),
            photos=data.get('photos'),
            attachments=data.get('attachments'),
            created_by=data.get('created_by'),
            created_by_name=data.get('created_by_name'),
            remark=data.get('remark'),
        )
        db.session.add(rma)
        db.session.flush()  # 获取ID

        # 创建退货明细
        for item_data in data.get('items', []):
            item = RMAItem(
                rma_id=rma.id,
                shipment_item_id=item_data.get('shipment_item_id'),
                product_code=item_data.get('product_code'),
                product_name=item_data.get('product_name'),
                original_qty=item_data.get('original_qty'),
                return_qty=item_data.get('return_qty'),
                unit=item_data.get('unit', '个'),
                batch_no=item_data.get('batch_no'),
                unit_price=item_data.get('unit_price'),
                amount=item_data.get('amount'),
                defect_description=item_data.get('defect_description'),
                remark=item_data.get('remark'),
            )
            db.session.add(item)

        db.session.commit()
        return jsonify({'message': '创建成功', 'data': rma.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/<int:id>', methods=['PUT'])
def update_rma(id):
    """更新RMA"""
    try:
        rma = RMAOrder.query.get(id)
        if not rma:
            return jsonify({'error': 'RMA不存在'}), 404

        # 只允许待审核状态的RMA修改
        if rma.status not in ['pending']:
            return jsonify({'error': '当前状态不允许修改'}), 400

        data = request.get_json()

        # 更新字段
        for field in ['rma_type', 'reason', 'handle_method', 'return_address',
                      'return_contact', 'return_phone', 'photos', 'attachments', 'remark']:
            if field in data:
                setattr(rma, field, data[field])

        # 更新明细
        if 'items' in data:
            # 删除旧明细
            RMAItem.query.filter_by(rma_id=id).delete()
            # 添加新明细
            for item_data in data.get('items', []):
                item = RMAItem(
                    rma_id=id,
                    shipment_item_id=item_data.get('shipment_item_id'),
                    product_code=item_data.get('product_code'),
                    product_name=item_data.get('product_name'),
                    original_qty=item_data.get('original_qty'),
                    return_qty=item_data.get('return_qty'),
                    unit=item_data.get('unit', '个'),
                    batch_no=item_data.get('batch_no'),
                    unit_price=item_data.get('unit_price'),
                    amount=item_data.get('amount'),
                    defect_description=item_data.get('defect_description'),
                    remark=item_data.get('remark'),
                )
                db.session.add(item)

        db.session.commit()
        return jsonify({'message': '更新成功', 'data': rma.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/<int:id>', methods=['DELETE'])
def delete_rma(id):
    """删除RMA"""
    try:
        rma = RMAOrder.query.get(id)
        if not rma:
            return jsonify({'error': 'RMA不存在'}), 404

        # 只允许待审核状态的RMA删除
        if rma.status not in ['pending']:
            return jsonify({'error': '当前状态不允许删除'}), 400

        db.session.delete(rma)
        db.session.commit()
        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/<int:id>/approve', methods=['POST'])
def approve_rma(id):
    """审批通过RMA"""
    try:
        rma = RMAOrder.query.get(id)
        if not rma:
            return jsonify({'error': 'RMA不存在'}), 404

        if rma.status != 'pending':
            return jsonify({'error': '当前状态不允许审批'}), 400

        data = request.get_json() or {}

        rma.status = 'approved'
        rma.approved_date = date.today()
        rma.approved_by = data.get('approved_by')
        rma.approved_by_name = data.get('approved_by_name')
        rma.handle_method = data.get('handle_method') or rma.handle_method

        db.session.commit()
        return jsonify({'message': '审批通过', 'data': rma.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/<int:id>/reject', methods=['POST'])
def reject_rma(id):
    """拒绝RMA"""
    try:
        rma = RMAOrder.query.get(id)
        if not rma:
            return jsonify({'error': 'RMA不存在'}), 404

        if rma.status != 'pending':
            return jsonify({'error': '当前状态不允许拒绝'}), 400

        data = request.get_json() or {}

        rma.status = 'rejected'
        rma.approved_date = date.today()
        rma.approved_by = data.get('approved_by')
        rma.approved_by_name = data.get('approved_by_name')
        rma.reject_reason = data.get('reject_reason')

        db.session.commit()
        return jsonify({'message': '已拒绝', 'data': rma.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/<int:id>/receive', methods=['POST'])
def receive_rma(id):
    """确认收货"""
    try:
        rma = RMAOrder.query.get(id)
        if not rma:
            return jsonify({'error': 'RMA不存在'}), 404

        if rma.status not in ['approved', 'receiving']:
            return jsonify({'error': '当前状态不允许收货'}), 400

        data = request.get_json() or {}

        rma.status = 'received'
        rma.received_date = date.today()
        rma.return_carrier = data.get('return_carrier') or rma.return_carrier
        rma.return_tracking_no = data.get('return_tracking_no') or rma.return_tracking_no

        db.session.commit()
        return jsonify({'message': '收货确认', 'data': rma.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/<int:id>/inspect', methods=['POST'])
def inspect_rma(id):
    """质检"""
    try:
        rma = RMAOrder.query.get(id)
        if not rma:
            return jsonify({'error': 'RMA不存在'}), 404

        if rma.status not in ['received', 'inspecting']:
            return jsonify({'error': '当前状态不允许质检'}), 400

        data = request.get_json() or {}

        rma.status = 'inspecting'
        rma.inspection_result = data.get('inspection_result')
        rma.inspection_note = data.get('inspection_note')
        rma.inspected_by = data.get('inspected_by')
        rma.inspected_by_name = data.get('inspected_by_name')
        rma.inspected_at = datetime.now()

        # 更新明细的质检结果
        for item_data in data.get('items', []):
            item = RMAItem.query.get(item_data.get('id'))
            if item and item.rma_id == id:
                item.inspected_qty = item_data.get('inspected_qty')
                item.qualified_qty = item_data.get('qualified_qty')
                item.unqualified_qty = item_data.get('unqualified_qty')

        db.session.commit()
        return jsonify({'message': '质检完成', 'data': rma.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/<int:id>/complete', methods=['POST'])
def complete_rma(id):
    """完成RMA"""
    try:
        rma = RMAOrder.query.get(id)
        if not rma:
            return jsonify({'error': 'RMA不存在'}), 404

        if rma.status not in ['received', 'inspecting']:
            return jsonify({'error': '当前状态不允许完成'}), 400

        data = request.get_json() or {}

        rma.status = 'completed'
        rma.completed_date = date.today()
        rma.handle_method = data.get('handle_method') or rma.handle_method
        rma.refund_amount = data.get('refund_amount')
        rma.exchange_shipment_no = data.get('exchange_shipment_no')
        rma.credit_amount = data.get('credit_amount')

        # 更新明细的处理结果
        for item_data in data.get('items', []):
            item = RMAItem.query.get(item_data.get('id'))
            if item and item.rma_id == id:
                item.restocked_qty = item_data.get('restocked_qty')
                item.scrapped_qty = item_data.get('scrapped_qty')

        db.session.commit()
        return jsonify({'message': 'RMA完成', 'data': rma.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/<int:id>/cancel', methods=['POST'])
def cancel_rma(id):
    """取消RMA"""
    try:
        rma = RMAOrder.query.get(id)
        if not rma:
            return jsonify({'error': 'RMA不存在'}), 404

        if rma.status in ['completed', 'cancelled']:
            return jsonify({'error': '当前状态不允许取消'}), 400

        rma.status = 'cancelled'
        db.session.commit()
        return jsonify({'message': 'RMA已取消', 'data': rma.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/statistics', methods=['GET'])
def get_rma_statistics():
    """获取RMA统计"""
    try:
        from sqlalchemy import func

        # 总数统计
        total = RMAOrder.query.count()

        # 按状态统计
        status_stats = db.session.query(
            RMAOrder.status,
            func.count(RMAOrder.id).label('count')
        ).group_by(RMAOrder.status).all()

        status_data = {s.status: s.count for s in status_stats}

        # 按类型统计
        type_stats = db.session.query(
            RMAOrder.rma_type,
            func.count(RMAOrder.id).label('count')
        ).group_by(RMAOrder.rma_type).all()

        type_data = {t.rma_type: t.count for t in type_stats}

        # 本月统计
        today = date.today()
        month_start = today.replace(day=1)
        month_total = RMAOrder.query.filter(
            RMAOrder.apply_date >= month_start
        ).count()

        return jsonify({
            'total': total,
            'by_status': {
                'pending': status_data.get('pending', 0),
                'approved': status_data.get('approved', 0),
                'rejected': status_data.get('rejected', 0),
                'receiving': status_data.get('receiving', 0),
                'received': status_data.get('received', 0),
                'inspecting': status_data.get('inspecting', 0),
                'completed': status_data.get('completed', 0),
                'cancelled': status_data.get('cancelled', 0),
            },
            'by_type': type_data,
            'this_month': month_total,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rma_bp.route('/rma/enums', methods=['GET'])
def get_rma_enums():
    """获取RMA枚举值"""
    return jsonify({
        'statuses': [
            {'value': e.value, 'label': RMA_STATUS_LABELS.get(e, e.value)}
            for e in RMAStatus
        ],
        'types': [
            {'value': e.value, 'label': RMA_TYPE_LABELS.get(e, e.value)}
            for e in RMAType
        ],
        'handle_methods': [
            {'value': e.value, 'label': RMA_HANDLE_LABELS.get(e, e.value)}
            for e in RMAHandleMethod
        ],
    })


@rma_bp.route('/rma/from-shipment/<int:shipment_id>', methods=['GET'])
def get_rma_from_shipment(shipment_id):
    """从出货单获取可退货明细"""
    try:
        shipment = Shipment.query.get(shipment_id)
        if not shipment:
            return jsonify({'error': '出货单不存在'}), 404

        # 获取已退货数量
        existing_returns = db.session.query(
            RMAItem.shipment_item_id,
            db.func.sum(RMAItem.return_qty).label('returned_qty')
        ).join(RMAOrder).filter(
            RMAOrder.shipment_id == shipment_id,
            RMAOrder.status.notin_(['cancelled', 'rejected'])
        ).group_by(RMAItem.shipment_item_id).all()

        returned_map = {r.shipment_item_id: float(r.returned_qty or 0) for r in existing_returns}

        items = []
        for item in shipment.items:
            returned = returned_map.get(item.id, 0)
            available = float(item.qty or 0) - returned
            if available > 0:
                items.append({
                    'shipment_item_id': item.id,
                    'product_code': item.product_code,
                    'product_name': item.product_name,
                    'original_qty': float(item.qty or 0),
                    'returned_qty': returned,
                    'available_qty': available,
                    'unit': item.unit,
                    'batch_no': item.batch_no,
                })

        return jsonify({
            'shipment': shipment.to_dict(),
            'items': items,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
