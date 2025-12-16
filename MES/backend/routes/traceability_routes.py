# MES 物料追溯路由
# Material Traceability Routes

from flask import Blueprint, request, jsonify
from database import db
from models.traceability import (
    MaterialLot, ProductLot, MaterialConsumption, TraceRecord,
    MaterialLotStatus, ProductLotStatus,
    generate_material_lot_no, generate_product_lot_no,
    MATERIAL_LOT_STATUS_LABELS, PRODUCT_LOT_STATUS_LABELS
)
from datetime import datetime, date
from sqlalchemy import func, or_

traceability_bp = Blueprint('traceability', __name__)


# ============ 物料批次 API ============

@traceability_bp.route('/material-lots', methods=['GET'])
def get_material_lots():
    """获取物料批次列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', '')
        material_code = request.args.get('material_code', '')
        supplier_id = request.args.get('supplier_id', type=int)
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        query = MaterialLot.query

        if keyword:
            query = query.filter(or_(
                MaterialLot.lot_no.like(f'%{keyword}%'),
                MaterialLot.material_code.like(f'%{keyword}%'),
                MaterialLot.material_name.like(f'%{keyword}%')
            ))

        if status:
            query = query.filter(MaterialLot.status == status)

        if material_code:
            query = query.filter(MaterialLot.material_code == material_code)

        if supplier_id:
            query = query.filter(MaterialLot.supplier_id == supplier_id)

        if start_date:
            query = query.filter(MaterialLot.receive_date >= start_date)

        if end_date:
            query = query.filter(MaterialLot.receive_date <= end_date)

        query = query.order_by(MaterialLot.created_at.desc())

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return jsonify({
            'success': True,
            'data': [lot.to_dict() for lot in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/material-lots/<int:id>', methods=['GET'])
def get_material_lot(id):
    """获取物料批次详情"""
    try:
        lot = MaterialLot.query.get_or_404(id)
        data = lot.to_dict()

        # 获取消耗记录
        consumptions = MaterialConsumption.query.filter_by(material_lot_id=id).all()
        data['consumptions'] = [c.to_dict() for c in consumptions]

        # 获取追溯的产品批次
        traces = TraceRecord.query.filter_by(material_lot_id=id).all()
        data['product_lots'] = [t.to_dict() for t in traces]

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/material-lots', methods=['POST'])
def create_material_lot():
    """创建物料批次"""
    try:
        data = request.get_json()

        lot = MaterialLot(
            lot_no=generate_material_lot_no(),
            material_id=data.get('material_id'),
            material_code=data['material_code'],
            material_name=data.get('material_name'),
            specification=data.get('specification'),
            initial_quantity=data['initial_quantity'],
            current_quantity=data['initial_quantity'],
            consumed_quantity=0,
            uom=data.get('uom', '个'),
            source_type=data.get('source_type'),
            source_no=data.get('source_no'),
            supplier_id=data.get('supplier_id'),
            supplier_name=data.get('supplier_name'),
            warehouse_id=data.get('warehouse_id'),
            warehouse_name=data.get('warehouse_name'),
            bin_code=data.get('bin_code'),
            production_date=datetime.strptime(data['production_date'], '%Y-%m-%d').date() if data.get('production_date') else None,
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
            receive_date=datetime.strptime(data['receive_date'], '%Y-%m-%d').date() if data.get('receive_date') else date.today(),
            inspection_no=data.get('inspection_no'),
            inspection_result=data.get('inspection_result'),
            certificate_no=data.get('certificate_no'),
            status=MaterialLotStatus.AVAILABLE.value,
            remark=data.get('remark'),
            created_by=data.get('created_by'),
            created_by_name=data.get('created_by_name')
        )

        db.session.add(lot)
        db.session.commit()

        return jsonify({'success': True, 'data': lot.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/material-lots/<int:id>', methods=['PUT'])
def update_material_lot(id):
    """更新物料批次"""
    try:
        lot = MaterialLot.query.get_or_404(id)
        data = request.get_json()

        for field in ['material_code', 'material_name', 'specification', 'uom',
                      'source_type', 'source_no', 'supplier_id', 'supplier_name',
                      'warehouse_id', 'warehouse_name', 'bin_code',
                      'inspection_no', 'inspection_result', 'certificate_no',
                      'status', 'remark']:
            if field in data:
                setattr(lot, field, data[field])

        if 'production_date' in data:
            lot.production_date = datetime.strptime(data['production_date'], '%Y-%m-%d').date() if data['production_date'] else None

        if 'expiry_date' in data:
            lot.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data['expiry_date'] else None

        db.session.commit()

        return jsonify({'success': True, 'data': lot.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/material-lots/<int:id>', methods=['DELETE'])
def delete_material_lot(id):
    """删除物料批次"""
    try:
        lot = MaterialLot.query.get_or_404(id)

        # 检查是否有消耗记录
        if MaterialConsumption.query.filter_by(material_lot_id=id).count() > 0:
            return jsonify({'success': False, 'message': '该批次已有消耗记录，无法删除'}), 400

        db.session.delete(lot)
        db.session.commit()

        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ 产品批次 API ============

@traceability_bp.route('/product-lots', methods=['GET'])
def get_product_lots():
    """获取产品批次列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', '')
        product_code = request.args.get('product_code', '')
        work_order_id = request.args.get('work_order_id', type=int)
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        query = ProductLot.query

        if keyword:
            query = query.filter(or_(
                ProductLot.lot_no.like(f'%{keyword}%'),
                ProductLot.product_code.like(f'%{keyword}%'),
                ProductLot.product_name.like(f'%{keyword}%'),
                ProductLot.work_order_no.like(f'%{keyword}%')
            ))

        if status:
            query = query.filter(ProductLot.status == status)

        if product_code:
            query = query.filter(ProductLot.product_code == product_code)

        if work_order_id:
            query = query.filter(ProductLot.work_order_id == work_order_id)

        if start_date:
            query = query.filter(ProductLot.production_date >= start_date)

        if end_date:
            query = query.filter(ProductLot.production_date <= end_date)

        query = query.order_by(ProductLot.created_at.desc())

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return jsonify({
            'success': True,
            'data': [lot.to_dict() for lot in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/product-lots/<int:id>', methods=['GET'])
def get_product_lot(id):
    """获取产品批次详情"""
    try:
        lot = ProductLot.query.get_or_404(id)
        data = lot.to_dict()

        # 获取消耗记录（使用的物料）
        consumptions = MaterialConsumption.query.filter_by(product_lot_id=id).all()
        data['consumptions'] = [c.to_dict() for c in consumptions]

        # 获取追溯的物料批次
        traces = TraceRecord.query.filter_by(product_lot_id=id).all()
        data['material_lots'] = [t.to_dict() for t in traces]

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/product-lots', methods=['POST'])
def create_product_lot():
    """创建产品批次"""
    try:
        data = request.get_json()

        lot = ProductLot(
            lot_no=generate_product_lot_no(),
            product_id=data.get('product_id'),
            product_code=data['product_code'],
            product_name=data.get('product_name'),
            specification=data.get('specification'),
            work_order_id=data.get('work_order_id'),
            work_order_no=data.get('work_order_no'),
            process_id=data.get('process_id'),
            process_name=data.get('process_name'),
            quantity=data['quantity'],
            uom=data.get('uom', '个'),
            inspection_no=data.get('inspection_no'),
            inspection_result=data.get('inspection_result'),
            quality_grade=data.get('quality_grade'),
            production_date=datetime.strptime(data['production_date'], '%Y-%m-%d').date() if data.get('production_date') else date.today(),
            status=ProductLotStatus.IN_PRODUCTION.value,
            remark=data.get('remark'),
            created_by=data.get('created_by'),
            created_by_name=data.get('created_by_name')
        )

        db.session.add(lot)
        db.session.commit()

        return jsonify({'success': True, 'data': lot.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/product-lots/<int:id>', methods=['PUT'])
def update_product_lot(id):
    """更新产品批次"""
    try:
        lot = ProductLot.query.get_or_404(id)
        data = request.get_json()

        for field in ['product_code', 'product_name', 'specification',
                      'process_id', 'process_name', 'quantity', 'uom',
                      'inspection_no', 'inspection_result', 'quality_grade',
                      'shipment_id', 'shipment_no', 'customer_id', 'customer_name',
                      'status', 'remark']:
            if field in data:
                setattr(lot, field, data[field])

        if 'completion_date' in data:
            lot.completion_date = datetime.strptime(data['completion_date'], '%Y-%m-%d').date() if data['completion_date'] else None

        if 'shipment_date' in data:
            lot.shipment_date = datetime.strptime(data['shipment_date'], '%Y-%m-%d').date() if data['shipment_date'] else None

        db.session.commit()

        return jsonify({'success': True, 'data': lot.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/product-lots/<int:id>/complete', methods=['POST'])
def complete_product_lot(id):
    """完成产品批次"""
    try:
        lot = ProductLot.query.get_or_404(id)

        if lot.status != ProductLotStatus.IN_PRODUCTION.value:
            return jsonify({'success': False, 'message': '只有生产中的批次可以完成'}), 400

        lot.status = ProductLotStatus.COMPLETED.value
        lot.completion_date = date.today()

        db.session.commit()

        return jsonify({'success': True, 'data': lot.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ 物料消耗 API ============

@traceability_bp.route('/consumptions', methods=['GET'])
def get_consumptions():
    """获取物料消耗记录"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        work_order_id = request.args.get('work_order_id', type=int)
        material_lot_id = request.args.get('material_lot_id', type=int)
        product_lot_id = request.args.get('product_lot_id', type=int)
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        query = MaterialConsumption.query

        if work_order_id:
            query = query.filter(MaterialConsumption.work_order_id == work_order_id)

        if material_lot_id:
            query = query.filter(MaterialConsumption.material_lot_id == material_lot_id)

        if product_lot_id:
            query = query.filter(MaterialConsumption.product_lot_id == product_lot_id)

        if start_date:
            query = query.filter(MaterialConsumption.consumed_at >= start_date)

        if end_date:
            query = query.filter(MaterialConsumption.consumed_at <= end_date + ' 23:59:59')

        query = query.order_by(MaterialConsumption.consumed_at.desc())

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return jsonify({
            'success': True,
            'data': [c.to_dict() for c in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/consumptions', methods=['POST'])
def create_consumption():
    """记录物料消耗"""
    try:
        data = request.get_json()

        # 获取物料批次
        material_lot = MaterialLot.query.get_or_404(data['material_lot_id'])

        # 检查数量
        quantity = float(data['quantity'])
        if quantity > float(material_lot.current_quantity):
            return jsonify({'success': False, 'message': f'消耗数量超过可用数量({material_lot.current_quantity})'}), 400

        # 创建消耗记录
        consumption = MaterialConsumption(
            work_order_id=data['work_order_id'],
            work_order_no=data.get('work_order_no'),
            process_id=data.get('process_id'),
            process_name=data.get('process_name'),
            material_lot_id=material_lot.id,
            material_code=material_lot.material_code,
            material_name=material_lot.material_name,
            lot_no=material_lot.lot_no,
            product_lot_id=data.get('product_lot_id'),
            product_lot_no=data.get('product_lot_no'),
            quantity=quantity,
            uom=material_lot.uom,
            consumed_at=datetime.now(),
            operator_id=data.get('operator_id'),
            operator_name=data.get('operator_name'),
            remark=data.get('remark')
        )

        # 更新物料批次数量
        material_lot.current_quantity = float(material_lot.current_quantity) - quantity
        material_lot.consumed_quantity = float(material_lot.consumed_quantity or 0) + quantity

        # 检查是否耗尽
        if material_lot.current_quantity <= 0:
            material_lot.status = MaterialLotStatus.DEPLETED.value
        elif material_lot.status == MaterialLotStatus.AVAILABLE.value:
            material_lot.status = MaterialLotStatus.IN_USE.value

        # 如果指定了产品批次，创建追溯记录
        if data.get('product_lot_id'):
            product_lot = ProductLot.query.get(data['product_lot_id'])
            if product_lot:
                trace = TraceRecord(
                    material_lot_id=material_lot.id,
                    material_lot_no=material_lot.lot_no,
                    material_code=material_lot.material_code,
                    material_name=material_lot.material_name,
                    product_lot_id=product_lot.id,
                    product_lot_no=product_lot.lot_no,
                    product_code=product_lot.product_code,
                    product_name=product_lot.product_name,
                    work_order_id=data['work_order_id'],
                    work_order_no=data.get('work_order_no'),
                    consumed_quantity=quantity,
                    uom=material_lot.uom
                )
                db.session.add(trace)

        db.session.add(consumption)
        db.session.commit()

        return jsonify({'success': True, 'data': consumption.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ 追溯查询 API ============

@traceability_bp.route('/trace/forward/<int:material_lot_id>', methods=['GET'])
def trace_forward(material_lot_id):
    """正向追溯：物料批次 -> 产品批次（物料去了哪些产品）"""
    try:
        material_lot = MaterialLot.query.get_or_404(material_lot_id)

        traces = TraceRecord.query.filter_by(material_lot_id=material_lot_id).all()

        # 获取关联的产品批次详情
        product_lots = []
        for trace in traces:
            product_lot = ProductLot.query.get(trace.product_lot_id)
            if product_lot:
                product_lots.append({
                    **product_lot.to_dict(),
                    'consumed_quantity': float(trace.consumed_quantity) if trace.consumed_quantity else 0
                })

        return jsonify({
            'success': True,
            'data': {
                'material_lot': material_lot.to_dict(),
                'product_lots': product_lots,
                'total': len(product_lots)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/trace/backward/<int:product_lot_id>', methods=['GET'])
def trace_backward(product_lot_id):
    """反向追溯：产品批次 -> 物料批次（产品用了哪些物料）"""
    try:
        product_lot = ProductLot.query.get_or_404(product_lot_id)

        traces = TraceRecord.query.filter_by(product_lot_id=product_lot_id).all()

        # 获取关联的物料批次详情
        material_lots = []
        for trace in traces:
            material_lot = MaterialLot.query.get(trace.material_lot_id)
            if material_lot:
                material_lots.append({
                    **material_lot.to_dict(),
                    'consumed_quantity': float(trace.consumed_quantity) if trace.consumed_quantity else 0
                })

        return jsonify({
            'success': True,
            'data': {
                'product_lot': product_lot.to_dict(),
                'material_lots': material_lots,
                'total': len(material_lots)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/trace/by-work-order/<int:work_order_id>', methods=['GET'])
def trace_by_work_order(work_order_id):
    """按工单追溯：获取工单关联的所有物料和产品批次"""
    try:
        # 获取工单关联的产品批次
        product_lots = ProductLot.query.filter_by(work_order_id=work_order_id).all()

        # 获取工单关联的物料消耗
        consumptions = MaterialConsumption.query.filter_by(work_order_id=work_order_id).all()

        # 获取唯一的物料批次
        material_lot_ids = set([c.material_lot_id for c in consumptions])
        material_lots = MaterialLot.query.filter(MaterialLot.id.in_(material_lot_ids)).all() if material_lot_ids else []

        return jsonify({
            'success': True,
            'data': {
                'work_order_id': work_order_id,
                'product_lots': [lot.to_dict() for lot in product_lots],
                'material_lots': [lot.to_dict() for lot in material_lots],
                'consumptions': [c.to_dict() for c in consumptions]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ 统计 API ============

@traceability_bp.route('/statistics/summary', methods=['GET'])
def get_statistics_summary():
    """获取追溯统计概览"""
    try:
        # 物料批次统计
        material_lot_stats = db.session.query(
            MaterialLot.status,
            func.count(MaterialLot.id).label('count')
        ).group_by(MaterialLot.status).all()

        material_stats = {
            'total': sum([s.count for s in material_lot_stats]),
            'by_status': {s.status: s.count for s in material_lot_stats}
        }

        # 产品批次统计
        product_lot_stats = db.session.query(
            ProductLot.status,
            func.count(ProductLot.id).label('count')
        ).group_by(ProductLot.status).all()

        product_stats = {
            'total': sum([s.count for s in product_lot_stats]),
            'by_status': {s.status: s.count for s in product_lot_stats}
        }

        # 今日消耗
        today = date.today()
        today_consumptions = MaterialConsumption.query.filter(
            func.date(MaterialConsumption.consumed_at) == today
        ).count()

        # 追溯关联数
        trace_count = TraceRecord.query.count()

        return jsonify({
            'success': True,
            'data': {
                'material_lots': material_stats,
                'product_lots': product_stats,
                'today_consumptions': today_consumptions,
                'trace_records': trace_count
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@traceability_bp.route('/statistics/by-material', methods=['GET'])
def get_statistics_by_material():
    """按物料统计消耗"""
    try:
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        limit = request.args.get('limit', 10, type=int)

        query = db.session.query(
            MaterialConsumption.material_code,
            MaterialConsumption.material_name,
            func.sum(MaterialConsumption.quantity).label('total_consumed'),
            func.count(MaterialConsumption.id).label('consumption_count')
        ).group_by(
            MaterialConsumption.material_code,
            MaterialConsumption.material_name
        )

        if start_date:
            query = query.filter(MaterialConsumption.consumed_at >= start_date)

        if end_date:
            query = query.filter(MaterialConsumption.consumed_at <= end_date + ' 23:59:59')

        stats = query.order_by(func.sum(MaterialConsumption.quantity).desc()).limit(limit).all()

        return jsonify({
            'success': True,
            'data': [{
                'material_code': s.material_code,
                'material_name': s.material_name,
                'total_consumed': float(s.total_consumed) if s.total_consumed else 0,
                'consumption_count': s.consumption_count
            } for s in stats]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ 枚举 API ============

@traceability_bp.route('/enums', methods=['GET'])
def get_enums():
    """获取追溯相关枚举"""
    return jsonify({
        'success': True,
        'data': {
            'material_lot_status': [
                {'value': s.value, 'label': MATERIAL_LOT_STATUS_LABELS.get(s, s.value)}
                for s in MaterialLotStatus
            ],
            'product_lot_status': [
                {'value': s.value, 'label': PRODUCT_LOT_STATUS_LABELS.get(s, s.value)}
                for s in ProductLotStatus
            ],
            'source_types': [
                {'value': 'purchase', 'label': '采购入库'},
                {'value': 'transfer', 'label': '调拨入库'},
                {'value': 'return', 'label': '退料入库'},
                {'value': 'other', 'label': '其他'}
            ]
        }
    })
