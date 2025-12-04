# 生产报工路由
from flask import Blueprint, request, jsonify
from database import db
from models.work_order import WorkOrder
from models.production_record import ProductionRecord
from datetime import datetime

production_bp = Blueprint('production', __name__)


@production_bp.route('/report', methods=['POST'])
def report_production():
    """生产报工"""
    data = request.get_json()
    work_order_id = data.get('work_order_id')

    order = WorkOrder.query.get_or_404(work_order_id)
    if order.status != 'in_progress':
        return jsonify({'success': False, 'error': '工单未在生产中'}), 400

    record = ProductionRecord(
        work_order_id=work_order_id,
        process_step=data.get('process_step'),
        process_name=data.get('process_name'),
        quantity=data.get('quantity', 0),
        good_quantity=data.get('good_quantity', 0),
        defect_quantity=data.get('defect_quantity', 0),
        equipment_id=data.get('equipment_id'),
        equipment_code=data.get('equipment_code'),
        equipment_name=data.get('equipment_name'),
        material_batch=data.get('material_batch'),
        operator_id=data.get('operator_id'),
        operator_name=data.get('operator_name'),
        start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
        end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
        work_hours=data.get('work_hours'),
        notes=data.get('notes'),
        defect_reason=data.get('defect_reason')
    )

    # 更新工单完成数量
    order.completed_quantity += record.good_quantity
    order.defect_quantity += record.defect_quantity

    db.session.add(record)
    db.session.commit()

    return jsonify({'success': True, 'data': record.to_dict()}), 201


@production_bp.route('/records', methods=['GET'])
def get_production_records():
    """获取生产记录"""
    work_order_id = request.args.get('work_order_id')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    query = ProductionRecord.query
    if work_order_id:
        query = query.filter_by(work_order_id=work_order_id)

    total = query.count()
    records = query.order_by(ProductionRecord.created_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'success': True,
        'data': {
            'items': [r.to_dict() for r in records],
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })


@production_bp.route('/today', methods=['GET'])
def get_today_production():
    """获取今日生产数据"""
    today = datetime.utcnow().date()
    records = ProductionRecord.query.filter(
        db.func.date(ProductionRecord.created_at) == today
    ).all()

    total_quantity = sum(r.quantity for r in records)
    total_good = sum(r.good_quantity for r in records)
    total_defect = sum(r.defect_quantity for r in records)

    return jsonify({
        'success': True,
        'data': {
            'total_quantity': total_quantity,
            'good_quantity': total_good,
            'defect_quantity': total_defect,
            'defect_rate': round(total_defect / total_quantity * 100, 2) if total_quantity > 0 else 0,
            'record_count': len(records)
        }
    })
