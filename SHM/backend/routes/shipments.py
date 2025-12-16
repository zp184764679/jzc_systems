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


# ========== 打印功能 ==========

@shipments_bp.route('/shipments/<int:id>/print/delivery-note', methods=['GET'])
@requires_auth
def get_delivery_note(id):
    """获取送货单打印数据"""
    try:
        shipment = Shipment.query.get(id)
        if not shipment:
            return error_response(f'出货单不存在: {id}', 'NOT_FOUND', 404)

        # 计算汇总信息
        total_qty = sum(float(item.qty or 0) for item in shipment.items)
        total_items = len(shipment.items)

        # 格式化打印数据
        print_data = {
            'print_type': 'delivery_note',
            'print_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'company_info': {
                'name': '金正昌五金制品（惠州）有限公司',
                'address': '广东省惠州市惠阳区新圩镇红卫村',
                'phone': '0752-3626888',
                'fax': '0752-3626889'
            },
            'shipment': {
                'shipment_no': shipment.shipment_no,
                'order_no': shipment.order_no,
                'delivery_date': shipment.delivery_date.strftime('%Y-%m-%d') if shipment.delivery_date else '',
                'expected_arrival': shipment.expected_arrival.strftime('%Y-%m-%d') if shipment.expected_arrival else '',
                'shipping_method': shipment.shipping_method,
                'carrier': shipment.carrier,
                'tracking_no': shipment.tracking_no,
                'status': shipment.status,
                'remark': shipment.remark
            },
            'customer': {
                'id': shipment.customer_id,
                'name': shipment.customer_name,
                'contact': shipment.receiver_contact,
                'phone': shipment.receiver_phone,
                'address': shipment.receiver_address
            },
            'warehouse': {
                'id': shipment.warehouse_id,
                'contact': shipment.warehouse_contact,
                'phone': shipment.warehouse_phone
            },
            'items': [{
                'seq': idx + 1,
                'product_code': item.product_code,
                'product_name': item.product_name,
                'qty': float(item.qty or 0),
                'unit': item.unit,
                'batch_no': item.batch_no,
                'bin_code': item.bin_code,
                'remark': item.remark
            } for idx, item in enumerate(shipment.items)],
            'summary': {
                'total_items': total_items,
                'total_qty': total_qty
            }
        }

        return jsonify(success_response(data=print_data))

    except Exception as e:
        logger.error(f"获取送货单打印数据失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'获取送货单打印数据失败: {str(e)}', 'PRINT_ERROR', 500)


@shipments_bp.route('/shipments/<int:id>/print/packing-list', methods=['GET'])
@requires_auth
def get_packing_list(id):
    """获取装箱单打印数据"""
    try:
        shipment = Shipment.query.get(id)
        if not shipment:
            return error_response(f'出货单不存在: {id}', 'NOT_FOUND', 404)

        # 计算汇总信息
        total_qty = sum(float(item.qty or 0) for item in shipment.items)
        total_items = len(shipment.items)

        # 按批次号分组（用于装箱）
        batches = {}
        for item in shipment.items:
            batch_no = item.batch_no or '未指定批次'
            if batch_no not in batches:
                batches[batch_no] = {
                    'batch_no': batch_no,
                    'items': [],
                    'total_qty': 0
                }
            batches[batch_no]['items'].append({
                'product_code': item.product_code,
                'product_name': item.product_name,
                'qty': float(item.qty or 0),
                'unit': item.unit,
                'bin_code': item.bin_code,
                'remark': item.remark
            })
            batches[batch_no]['total_qty'] += float(item.qty or 0)

        # 格式化打印数据
        print_data = {
            'print_type': 'packing_list',
            'print_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'company_info': {
                'name': '金正昌五金制品（惠州）有限公司',
                'address': '广东省惠州市惠阳区新圩镇红卫村',
                'phone': '0752-3626888',
                'fax': '0752-3626889'
            },
            'shipment': {
                'shipment_no': shipment.shipment_no,
                'order_no': shipment.order_no,
                'delivery_date': shipment.delivery_date.strftime('%Y-%m-%d') if shipment.delivery_date else '',
                'shipping_method': shipment.shipping_method,
                'carrier': shipment.carrier,
                'tracking_no': shipment.tracking_no
            },
            'customer': {
                'id': shipment.customer_id,
                'name': shipment.customer_name,
                'contact': shipment.receiver_contact,
                'phone': shipment.receiver_phone,
                'address': shipment.receiver_address
            },
            'items': [{
                'seq': idx + 1,
                'product_code': item.product_code,
                'product_name': item.product_name,
                'qty': float(item.qty or 0),
                'unit': item.unit,
                'batch_no': item.batch_no,
                'bin_code': item.bin_code,
                'remark': item.remark
            } for idx, item in enumerate(shipment.items)],
            'batches': list(batches.values()),
            'summary': {
                'total_items': total_items,
                'total_qty': total_qty,
                'total_batches': len(batches)
            }
        }

        return jsonify(success_response(data=print_data))

    except Exception as e:
        logger.error(f"获取装箱单打印数据失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'获取装箱单打印数据失败: {str(e)}', 'PRINT_ERROR', 500)


@shipments_bp.route('/shipments/batch-ship', methods=['POST'])
@requires_auth
def batch_ship():
    """批量发货操作 - 批量扣减SCM库存"""
    try:
        data = request.get_json()
        if not data:
            return error_response('请求数据不能为空', 'INVALID_JSON', 400)

        shipment_ids = data.get('shipment_ids', [])
        carrier = data.get('carrier')
        tracking_no_prefix = data.get('tracking_no_prefix', '')

        if not shipment_ids:
            return error_response('请选择要发货的出货单', 'EMPTY_SELECTION', 400)

        shipments = Shipment.query.filter(Shipment.id.in_(shipment_ids)).all()

        if not shipments:
            return error_response('未找到指定的出货单', 'NOT_FOUND', 404)

        # 验证所有出货单都是待出货状态
        non_pending = [s.shipment_no for s in shipments if s.status != '待出货']
        if non_pending:
            return error_response(
                f'以下出货单不是待出货状态: {", ".join(non_pending)}',
                'INVALID_STATUS',
                400
            )

        # 批量处理发货
        success_list = []
        failed_list = []

        for idx, shipment in enumerate(shipments):
            try:
                # 更新物流信息
                if carrier:
                    shipment.carrier = carrier
                if tracking_no_prefix:
                    shipment.tracking_no = f"{tracking_no_prefix}-{idx + 1:03d}"

                # 扣减库存
                inventory_errors = []
                for item in shipment.items:
                    try:
                        result = deduct_inventory(item.product_code, item.qty, shipment.shipment_no)
                        if not result.get('success', True):
                            inventory_errors.append({
                                'product_code': item.product_code,
                                'error': result.get('error', '库存扣减失败')
                            })
                    except Exception as e:
                        logger.warning(f"库存扣减异常: {item.product_code} - {str(e)}")
                        inventory_errors.append({
                            'product_code': item.product_code,
                            'error': f'库存服务调用失败: {str(e)}'
                        })

                if inventory_errors:
                    failed_list.append({
                        'shipment_no': shipment.shipment_no,
                        'errors': inventory_errors
                    })
                    continue

                # 更新状态为已发货
                shipment.status = '已发货'
                if not shipment.delivery_date:
                    shipment.delivery_date = datetime.now().date()

                success_list.append(shipment.shipment_no)

            except Exception as e:
                failed_list.append({
                    'shipment_no': shipment.shipment_no,
                    'errors': [{'error': str(e)}]
                })

        db.session.commit()

        logger.info(f"批量发货完成: 成功 {len(success_list)}, 失败 {len(failed_list)}")

        return jsonify({
            'success': len(failed_list) == 0,
            'message': f'批量发货完成: 成功 {len(success_list)} 单, 失败 {len(failed_list)} 单',
            'data': {
                'success_count': len(success_list),
                'failed_count': len(failed_list),
                'success_list': success_list,
                'failed_list': failed_list
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"批量发货失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'批量发货失败: {str(e)}', 'BATCH_SHIP_ERROR', 500)


@shipments_bp.route('/shipments/batch-status', methods=['POST'])
@requires_auth
def batch_update_status():
    """批量更新出货单状态"""
    try:
        data = request.get_json()
        if not data:
            return error_response('请求数据不能为空', 'INVALID_JSON', 400)

        shipment_ids = data.get('shipment_ids', [])
        new_status = data.get('status')

        if not shipment_ids:
            return error_response('请选择要更新的出货单', 'EMPTY_SELECTION', 400)

        if not new_status:
            return error_response('请指定目标状态', 'MISSING_STATUS', 400)

        # 状态验证
        valid_statuses = ['待出货', '已发货', '已签收', '已取消']
        if new_status not in valid_statuses:
            return error_response(f'无效的状态: {new_status}', 'INVALID_STATUS', 400)

        # 不允许通过此接口批量发货（需要走 batch-ship 接口）
        if new_status == '已发货':
            return error_response('批量发货请使用 /batch-ship 接口', 'USE_BATCH_SHIP_API', 400)

        shipments = Shipment.query.filter(Shipment.id.in_(shipment_ids)).all()

        if not shipments:
            return error_response('未找到指定的出货单', 'NOT_FOUND', 404)

        # 状态流转验证
        valid_transitions = {
            '待出货': ['已取消'],
            '已发货': ['已签收'],
            '已签收': [],
            '已取消': []
        }

        success_list = []
        failed_list = []

        for shipment in shipments:
            if new_status in valid_transitions.get(shipment.status, []):
                shipment.status = new_status
                success_list.append(shipment.shipment_no)
            else:
                failed_list.append({
                    'shipment_no': shipment.shipment_no,
                    'error': f'不能从 {shipment.status} 变更为 {new_status}'
                })

        db.session.commit()

        logger.info(f"批量状态更新完成: 成功 {len(success_list)}, 失败 {len(failed_list)}")

        return jsonify({
            'success': len(failed_list) == 0,
            'message': f'批量更新完成: 成功 {len(success_list)} 单, 失败 {len(failed_list)} 单',
            'data': {
                'success_count': len(success_list),
                'failed_count': len(failed_list),
                'success_list': success_list,
                'failed_list': failed_list
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"批量状态更新失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'批量状态更新失败: {str(e)}', 'BATCH_STATUS_ERROR', 500)


@shipments_bp.route('/shipments/batch-delete', methods=['POST'])
@requires_auth
def batch_delete():
    """批量删除出货单"""
    try:
        data = request.get_json()
        if not data:
            return error_response('请求数据不能为空', 'INVALID_JSON', 400)

        shipment_ids = data.get('shipment_ids', [])

        if not shipment_ids:
            return error_response('请选择要删除的出货单', 'EMPTY_SELECTION', 400)

        shipments = Shipment.query.filter(Shipment.id.in_(shipment_ids)).all()

        if not shipments:
            return error_response('未找到指定的出货单', 'NOT_FOUND', 404)

        success_list = []
        failed_list = []

        for shipment in shipments:
            # 只有待出货状态才能删除
            if shipment.status == '待出货':
                db.session.delete(shipment)
                success_list.append(shipment.shipment_no)
            else:
                failed_list.append({
                    'shipment_no': shipment.shipment_no,
                    'error': f'状态为 {shipment.status}，不能删除'
                })

        db.session.commit()

        logger.info(f"批量删除完成: 成功 {len(success_list)}, 失败 {len(failed_list)}")

        return jsonify({
            'success': len(failed_list) == 0,
            'message': f'批量删除完成: 成功 {len(success_list)} 单, 失败 {len(failed_list)} 单',
            'data': {
                'success_count': len(success_list),
                'failed_count': len(failed_list),
                'success_list': success_list,
                'failed_list': failed_list
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"批量删除失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'批量删除失败: {str(e)}', 'BATCH_DELETE_ERROR', 500)


@shipments_bp.route('/shipments/batch-print', methods=['POST'])
@requires_auth
def batch_print():
    """批量打印出货单"""
    try:
        data = request.get_json()
        if not data:
            return error_response('请求数据不能为空', 'INVALID_JSON', 400)

        shipment_ids = data.get('shipment_ids', [])
        print_type = data.get('print_type', 'delivery_note')

        if not shipment_ids:
            return error_response('请选择要打印的出货单', 'EMPTY_SELECTION', 400)

        if print_type not in ['delivery_note', 'packing_list']:
            return error_response('无效的打印类型', 'INVALID_PRINT_TYPE', 400)

        shipments = Shipment.query.filter(Shipment.id.in_(shipment_ids)).all()

        if not shipments:
            return error_response('未找到指定的出货单', 'NOT_FOUND', 404)

        # 构建批量打印数据
        print_data_list = []
        for shipment in shipments:
            total_qty = sum(float(item.qty or 0) for item in shipment.items)
            total_items = len(shipment.items)

            print_item = {
                'shipment': {
                    'shipment_no': shipment.shipment_no,
                    'order_no': shipment.order_no,
                    'delivery_date': shipment.delivery_date.strftime('%Y-%m-%d') if shipment.delivery_date else '',
                    'shipping_method': shipment.shipping_method,
                    'carrier': shipment.carrier,
                    'tracking_no': shipment.tracking_no,
                    'status': shipment.status
                },
                'customer': {
                    'name': shipment.customer_name,
                    'contact': shipment.receiver_contact,
                    'phone': shipment.receiver_phone,
                    'address': shipment.receiver_address
                },
                'items': [{
                    'seq': idx + 1,
                    'product_code': item.product_code,
                    'product_name': item.product_name,
                    'qty': float(item.qty or 0),
                    'unit': item.unit,
                    'batch_no': item.batch_no,
                    'remark': item.remark
                } for idx, item in enumerate(shipment.items)],
                'summary': {
                    'total_items': total_items,
                    'total_qty': total_qty
                }
            }
            print_data_list.append(print_item)

        return jsonify(success_response(data={
            'print_type': print_type,
            'print_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'company_info': {
                'name': '金正昌五金制品（惠州）有限公司',
                'address': '广东省惠州市惠阳区新圩镇红卫村',
                'phone': '0752-3626888',
                'fax': '0752-3626889'
            },
            'shipments': print_data_list,
            'total_count': len(print_data_list)
        }))

    except Exception as e:
        logger.error(f"批量打印失败: {str(e)}")
        traceback.print_exc()
        return error_response(f'批量打印失败: {str(e)}', 'BATCH_PRINT_ERROR', 500)
