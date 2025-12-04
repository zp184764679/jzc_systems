# 生产看板路由
from flask import Blueprint, jsonify
from database import db
from models.work_order import WorkOrder
from models.production_record import ProductionRecord
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/overview', methods=['GET'])
def get_overview():
    """生产总览"""
    # 工单统计
    pending_count = WorkOrder.query.filter_by(status='pending').count()
    in_progress_count = WorkOrder.query.filter_by(status='in_progress').count()
    completed_today = WorkOrder.query.filter(
        WorkOrder.status == 'completed',
        db.func.date(WorkOrder.actual_end) == datetime.utcnow().date()
    ).count()

    # 今日生产
    today = datetime.utcnow().date()
    today_records = ProductionRecord.query.filter(
        db.func.date(ProductionRecord.created_at) == today
    ).all()

    total_output = sum(r.good_quantity for r in today_records)
    total_defect = sum(r.defect_quantity for r in today_records)

    return jsonify({
        'success': True,
        'data': {
            'work_orders': {
                'pending': pending_count,
                'in_progress': in_progress_count,
                'completed_today': completed_today
            },
            'today_production': {
                'output': total_output,
                'defect': total_defect,
                'defect_rate': round(total_defect / (total_output + total_defect) * 100, 2) if (total_output + total_defect) > 0 else 0
            }
        }
    })


@dashboard_bp.route('/production-trend', methods=['GET'])
def get_production_trend():
    """7天生产趋势"""
    trend_data = []
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        records = ProductionRecord.query.filter(
            db.func.date(ProductionRecord.created_at) == date
        ).all()

        trend_data.append({
            'date': date.isoformat(),
            'output': sum(r.good_quantity for r in records),
            'defect': sum(r.defect_quantity for r in records)
        })

    return jsonify({'success': True, 'data': trend_data})


@dashboard_bp.route('/active-orders', methods=['GET'])
def get_active_orders():
    """获取进行中的工单"""
    orders = WorkOrder.query.filter_by(status='in_progress') \
        .order_by(WorkOrder.priority.asc()).limit(10).all()

    return jsonify({
        'success': True,
        'data': [o.to_dict() for o in orders]
    })
