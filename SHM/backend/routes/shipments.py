from flask import Blueprint, request, jsonify
from datetime import datetime
from extensions import db
from models.shipment import Shipment, ShipmentItem
from services.scm_service import deduct_inventory
import traceback
import logging
import sys
import os

# 添加shared模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

try:
    from auth_middleware import requires_auth, success_response, error_response, paginated_response
    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False
    # 如果没有auth模块，提供空装饰器
    def requires_auth(f):
        return f
    def success_response(data=None, message='操作成功', **kwargs):
        response = {'success': True, 'message': message}
        if data is not None:
            response['data'] = data
        response.update(kwargs)
        return response
    def error_response(error, code='ERROR', status_code=400):
        return jsonify({'success': False, 'error': error, 'code': code}), status_code
    def paginated_response(items, total, page, per_page):
        return {
            'success': True,
            'data': items,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        }

logger = logging.getLogger(__name__)

shipments_bp = Blueprint('shipments', __name__)


def generate_shipment_no():
    """生成出货单号"""
    today = datetime.now().strftime('%Y%m%d')
    prefix = f'SHM{today}'

    # 查询今天最大的单号
    last_shipment = Shipment.query.filter(
        Shipment.shipment_no.like(f'{prefix}%')
    ).order_by(Shipment.shipment_no.desc()).first()

    if last_shipment:
        last_seq = int(last_shipment.shipment_no[-4:])
        new_seq = last_seq + 1
    else:
        new_seq = 1

    return f'{prefix}{new_seq:04d}'


@shipments_bp.route('/shipments', methods=['GET'])
@requires_auth
def get_shipments():
    """获取出货单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)
        status = request.args.get('status')
        customer_name = request.args.get('customer_name')
        shipment_no = request.args.get('shipment_no')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = Shipment.query

        if status:
            query = query.filter(Shipment.status == status)
        if customer_name:
            query = query.filter(Shipment.customer_name.like(f'%{customer_name}%'))
        if shipment_no:
            query = query.filter(Shipment.shipment_no.like(f'%{shipment_no}%'))
        if start_date:
            query = query.filter(Shipment.delivery_date >= start_date)
        if end_date:
            query = query.filter(Shipment.delivery_date <= end_date)

        query = query.order_by(Shipment.created_at.desc())

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return jsonify(paginated_response(
            items=[s.to_dict() for s in pagination.items],
            total=pagination.total,
            page=page,
            per_page=page_size
        ))

    except Exception as e:
        logger.error(f"获取出货单列表失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'获取出货单列表失败: {str(e)}', 'LIST_ERROR', 500)


@shipments_bp.route('/shipments', methods=['POST'])
@requires_auth
def create_shipment():
    """创建出货单"""
    try:
        data = request.get_json()

        if not data:
            return error_response('请求数据不能为空', 'INVALID_JSON', 400)

        # 验证必填字段
        required_fields = ['customer_name']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'缺少必填字段: {field}', 'MISSING_FIELD', 400)

        # 解析日期字段，增加错误处理
        delivery_date = None
        expected_arrival = None

        if data.get('delivery_date'):
            try:
                delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
            except ValueError as e:
                return error_response(f'发货日期格式错误，应为YYYY-MM-DD: {str(e)}', 'INVALID_DATE', 400)

        if data.get('expected_arrival'):
            try:
                expected_arrival = datetime.strptime(data['expected_arrival'], '%Y-%m-%d').date()
            except ValueError as e:
                return error_response(f'预计到达日期格式错误，应为YYYY-MM-DD: {str(e)}', 'INVALID_DATE', 400)

        shipment = Shipment(
            shipment_no=generate_shipment_no(),
            order_no=data.get('order_no'),
            customer_id=data.get('customer_id'),
            customer_name=data.get('customer_name'),
            delivery_date=delivery_date,
            expected_arrival=expected_arrival,
            shipping_method=data.get('shipping_method'),
            carrier=data.get('carrier'),
            tracking_no=data.get('tracking_no'),
            status='待出货',
            warehouse_id=data.get('warehouse_id'),
            warehouse_contact=data.get('warehouse_contact'),
            warehouse_phone=data.get('warehouse_phone'),
            receiver_contact=data.get('receiver_contact'),
            receiver_phone=data.get('receiver_phone'),
            receiver_address=data.get('receiver_address'),
            remark=data.get('remark')
        )

        # 添加出货明细
        items = data.get('items', [])
        for idx, item_data in enumerate(items):
            if not item_data.get('product_code'):
                return error_response(f'第{idx+1}行明细缺少产品编码', 'MISSING_PRODUCT_CODE', 400)
            if not item_data.get('qty') or item_data.get('qty') <= 0:
                return error_response(f'第{idx+1}行明细数量必须大于0', 'INVALID_QTY', 400)

            item = ShipmentItem(
                product_code=item_data.get('product_code'),
                product_name=item_data.get('product_name'),
                qty=item_data.get('qty'),
                unit=item_data.get('unit', '个'),
                bin_code=item_data.get('bin_code'),
                batch_no=item_data.get('batch_no'),
                remark=item_data.get('remark')
            )
            shipment.items.append(item)

        db.session.add(shipment)
        db.session.commit()

        logger.info(f"出货单创建成功: {shipment.shipment_no}")

        return jsonify(success_response(
            data=shipment.to_dict(),
            message='出货单创建成功'
        )), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建出货单失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'创建出货单失败: {str(e)}', 'CREATE_ERROR', 500)


@shipments_bp.route('/shipments/<int:id>', methods=['GET'])
@requires_auth
def get_shipment(id):
    """获取出货单详情"""
    try:
        shipment = Shipment.query.get(id)
        if not shipment:
            return error_response(f'出货单不存在: {id}', 'NOT_FOUND', 404)

        return jsonify(success_response(data=shipment.to_dict()))

    except Exception as e:
        logger.error(f"获取出货单详情失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'获取出货单详情失败: {str(e)}', 'GET_ERROR', 500)


@shipments_bp.route('/shipments/<int:id>', methods=['PUT'])
@requires_auth
def update_shipment(id):
    """更新出货单"""
    try:
        shipment = Shipment.query.get(id)
        if not shipment:
            return error_response(f'出货单不存在: {id}', 'NOT_FOUND', 404)

        data = request.get_json()
        if not data:
            return error_response('请求数据不能为空', 'INVALID_JSON', 400)

        # 只有待出货状态才能修改
        if shipment.status != '待出货':
            return error_response('只有待出货状态的出货单才能修改', 'INVALID_STATUS', 400)

        # 更新基本信息
        if 'order_no' in data:
            shipment.order_no = data['order_no']
        if 'customer_id' in data:
            shipment.customer_id = data['customer_id']
        if 'customer_name' in data:
            shipment.customer_name = data['customer_name']
        if 'delivery_date' in data and data['delivery_date']:
            try:
                shipment.delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
            except ValueError as e:
                return error_response(f'发货日期格式错误: {str(e)}', 'INVALID_DATE', 400)
        if 'expected_arrival' in data and data['expected_arrival']:
            try:
                shipment.expected_arrival = datetime.strptime(data['expected_arrival'], '%Y-%m-%d').date()
            except ValueError as e:
                return error_response(f'预计到达日期格式错误: {str(e)}', 'INVALID_DATE', 400)
        if 'shipping_method' in data:
            shipment.shipping_method = data['shipping_method']
        if 'carrier' in data:
            shipment.carrier = data['carrier']
        if 'tracking_no' in data:
            shipment.tracking_no = data['tracking_no']
        if 'warehouse_id' in data:
            shipment.warehouse_id = data['warehouse_id']
        if 'warehouse_contact' in data:
            shipment.warehouse_contact = data['warehouse_contact']
        if 'warehouse_phone' in data:
            shipment.warehouse_phone = data['warehouse_phone']
        if 'receiver_contact' in data:
            shipment.receiver_contact = data['receiver_contact']
        if 'receiver_phone' in data:
            shipment.receiver_phone = data['receiver_phone']
        if 'receiver_address' in data:
            shipment.receiver_address = data['receiver_address']
        if 'remark' in data:
            shipment.remark = data['remark']

        # 更新出货明细
        if 'items' in data:
            # 删除原有明细
            ShipmentItem.query.filter_by(shipment_id=id).delete()

            # 添加新明细
            for idx, item_data in enumerate(data['items']):
                if not item_data.get('product_code'):
                    db.session.rollback()
                    return error_response(f'第{idx+1}行明细缺少产品编码', 'MISSING_PRODUCT_CODE', 400)

                item = ShipmentItem(
                    shipment_id=id,
                    product_code=item_data.get('product_code'),
                    product_name=item_data.get('product_name'),
                    qty=item_data.get('qty'),
                    unit=item_data.get('unit', '个'),
                    bin_code=item_data.get('bin_code'),
                    batch_no=item_data.get('batch_no'),
                    remark=item_data.get('remark')
                )
                db.session.add(item)

        db.session.commit()

        logger.info(f"出货单更新成功: {shipment.shipment_no}")

        return jsonify(success_response(
            data=shipment.to_dict(),
            message='出货单更新成功'
        ))

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新出货单失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'更新出货单失败: {str(e)}', 'UPDATE_ERROR', 500)


@shipments_bp.route('/shipments/<int:id>', methods=['DELETE'])
@requires_auth
def delete_shipment(id):
    """删除出货单"""
    try:
        shipment = Shipment.query.get(id)
        if not shipment:
            return error_response(f'出货单不存在: {id}', 'NOT_FOUND', 404)

        # 只有待出货状态才能删除
        if shipment.status != '待出货':
            return error_response('只有待出货状态的出货单才能删除', 'INVALID_STATUS', 400)

        shipment_no = shipment.shipment_no
        db.session.delete(shipment)
        db.session.commit()

        logger.info(f"出货单删除成功: {shipment_no}")

        return jsonify(success_response(message='出货单删除成功'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除出货单失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'删除出货单失败: {str(e)}', 'DELETE_ERROR', 500)


@shipments_bp.route('/shipments/<int:id>/ship', methods=['POST'])
@requires_auth
def ship_shipment(id):
    """发货操作 - 扣减SCM库存"""
    try:
        shipment = Shipment.query.get(id)
        if not shipment:
            return error_response(f'出货单不存在: {id}', 'NOT_FOUND', 404)

        if shipment.status != '待出货':
            return error_response('只有待出货状态的出货单才能发货', 'INVALID_STATUS', 400)

        data = request.get_json() or {}

        # 更新物流信息
        if 'tracking_no' in data:
            shipment.tracking_no = data['tracking_no']
        if 'carrier' in data:
            shipment.carrier = data['carrier']

        # 扣减库存
        failed_items = []
        for item in shipment.items:
            try:
                result = deduct_inventory(item.product_code, item.qty, shipment.shipment_no)
                if not result.get('success', True):  # 如果SCM返回失败
                    failed_items.append({
                        'product_code': item.product_code,
                        'error': result.get('error', '库存扣减失败')
                    })
            except Exception as e:
                logger.warning(f"库存扣减异常: {item.product_code} - {str(e)}")
                failed_items.append({
                    'product_code': item.product_code,
                    'error': f'库存服务调用失败: {str(e)}'
                })

        if failed_items:
            return jsonify({
                'success': False,
                'error': '部分产品库存扣减失败',
                'code': 'INVENTORY_ERROR',
                'failed_items': failed_items
            }), 400

        # 更新状态为已发货
        shipment.status = '已发货'
        if not shipment.delivery_date:
            shipment.delivery_date = datetime.now().date()

        db.session.commit()

        logger.info(f"发货成功: {shipment.shipment_no}")

        return jsonify(success_response(
            data=shipment.to_dict(),
            message='发货成功，库存已扣减'
        ))

    except Exception as e:
        db.session.rollback()
        logger.error(f"发货操作失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'发货操作失败: {str(e)}', 'SHIP_ERROR', 500)


@shipments_bp.route('/shipments/<int:id>/status', methods=['PATCH'])
@requires_auth
def update_shipment_status(id):
    """更新出货单状态"""
    try:
        shipment = Shipment.query.get(id)
        if not shipment:
            return error_response(f'出货单不存在: {id}', 'NOT_FOUND', 404)

        data = request.get_json()
        if not data:
            return error_response('请求数据不能为空', 'INVALID_JSON', 400)

        new_status = data.get('status')
        if not new_status:
            return error_response('缺少状态字段', 'MISSING_STATUS', 400)

        # 状态流转验证
        valid_transitions = {
            '待出货': ['已发货', '已取消'],
            '已发货': ['已签收'],
            '已签收': [],
            '已取消': []
        }

        if new_status not in valid_transitions.get(shipment.status, []):
            return error_response(
                f'不能从 {shipment.status} 状态变更为 {new_status}',
                'INVALID_TRANSITION',
                400
            )

        # 如果是发货操作，需要扣减库存
        if shipment.status == '待出货' and new_status == '已发货':
            return error_response('请使用发货接口进行发货操作', 'USE_SHIP_API', 400)

        shipment.status = new_status
        db.session.commit()

        logger.info(f"出货单状态更新: {shipment.shipment_no} -> {new_status}")

        return jsonify(success_response(
            data=shipment.to_dict(),
            message=f'状态已更新为 {new_status}'
        ))

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新出货单状态失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'更新状态失败: {str(e)}', 'STATUS_ERROR', 500)


@shipments_bp.route('/shipments/stats', methods=['GET'])
@requires_auth
def get_shipment_stats():
    """获取出货统计"""
    try:
        total = Shipment.query.count()
        pending = Shipment.query.filter_by(status='待出货').count()
        shipped = Shipment.query.filter_by(status='已发货').count()
        delivered = Shipment.query.filter_by(status='已签收').count()
        cancelled = Shipment.query.filter_by(status='已取消').count()

        return jsonify(success_response(data={
            'total': total,
            'pending': pending,
            'shipped': shipped,
            'delivered': delivered,
            'cancelled': cancelled
        }))

    except Exception as e:
        logger.error(f"获取出货统计失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'获取统计失败: {str(e)}', 'STATS_ERROR', 500)
