from flask import Blueprint, request, jsonify
from app import db
from app.models import ProductionPlan, ProductionStep, Task
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/kpi/summary', methods=['GET'])
def get_kpi_summary():
    """获取仪表盘KPI汇总"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    # 1. 进行中订单数
    active_orders = ProductionPlan.query.filter(
        ProductionPlan.status.in_(['pending', 'in_progress'])
    ).count()

    # 上周同期对比
    active_orders_last_week = ProductionPlan.query.filter(
        ProductionPlan.status.in_(['pending', 'in_progress']),
        ProductionPlan.created_at <= week_ago
    ).count()

    # 2. 今日到期任务
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    today_tasks = Task.query.filter(
        Task.due_date.between(today_start, today_end),
        Task.status.notin_(['completed', 'cancelled'])
    ).count()

    urgent_tasks = Task.query.filter(
        Task.due_date.between(today_start, today_end),
        Task.status.notin_(['completed', 'cancelled']),
        Task.priority == 'urgent'
    ).count()

    # 3. 生产完工率
    total_plans = ProductionPlan.query.filter(
        ProductionPlan.status.in_(['in_progress', 'completed']),
        ProductionPlan.created_at >= week_ago
    ).count()

    completed_plans = ProductionPlan.query.filter(
        ProductionPlan.status == 'completed',
        ProductionPlan.created_at >= week_ago
    ).count()

    completion_rate = (completed_plans / total_plans * 100) if total_plans > 0 else 0

    # 4. 平均交货周期（最近完成的订单）
    avg_delivery_query = db.session.query(
        func.avg(
            func.datediff(ProductionPlan.actual_end_date, ProductionPlan.plan_start_date)
        )
    ).filter(
        ProductionPlan.status == 'completed',
        ProductionPlan.actual_end_date.isnot(None)
    ).scalar()

    avg_delivery_days = float(avg_delivery_query) if avg_delivery_query else 0

    # 5. 延期订单数
    delayed_orders = ProductionPlan.query.filter(
        ProductionPlan.status.notin_(['completed', 'cancelled']),
        ProductionPlan.plan_end_date < today
    ).count()

    return jsonify({
        'active_orders': {
            'value': active_orders,
            'trend': active_orders - active_orders_last_week,
            'trend_type': 'up' if active_orders > active_orders_last_week else 'down'
        },
        'today_tasks': {
            'value': today_tasks,
            'urgent': urgent_tasks
        },
        'completion_rate': {
            'value': round(completion_rate, 1),
            'target': 90
        },
        'avg_delivery_days': {
            'value': round(avg_delivery_days, 1)
        },
        'delayed_orders': {
            'value': delayed_orders
        }
    })


@dashboard_bp.route('/charts/order-status', methods=['GET'])
def get_order_status_chart():
    """订单状态分布（饼图数据）"""
    status_data = db.session.query(
        ProductionPlan.status,
        func.count(ProductionPlan.id).label('count')
    ).group_by(ProductionPlan.status).all()

    status_labels = {
        'pending': '待开始',
        'in_progress': '生产中',
        'completed': '已完成',
        'delayed': '已延期',
        'cancelled': '已取消'
    }

    data = []
    for status, count in status_data:
        data.append({
            'name': status_labels.get(status, status),
            'value': count,
            'status': status
        })

    return jsonify({'data': data})


@dashboard_bp.route('/charts/delivery-trend', methods=['GET'])
def get_delivery_trend_chart():
    """每日订单交付趋势（折线图数据）"""
    days = request.args.get('days', 30, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # 计划交付
    planned_query = db.session.query(
        ProductionPlan.plan_end_date,
        func.count(ProductionPlan.id)
    ).filter(
        ProductionPlan.plan_end_date.between(start_date, end_date)
    ).group_by(ProductionPlan.plan_end_date).all()

    # 实际交付
    actual_query = db.session.query(
        ProductionPlan.actual_end_date,
        func.count(ProductionPlan.id)
    ).filter(
        ProductionPlan.actual_end_date.between(start_date, end_date),
        ProductionPlan.status == 'completed'
    ).group_by(ProductionPlan.actual_end_date).all()

    # 构建日期序列
    dates = []
    planned_data = {}
    actual_data = {}

    current = start_date
    while current <= end_date:
        dates.append(current.strftime('%m-%d'))
        planned_data[current] = 0
        actual_data[current] = 0
        current += timedelta(days=1)

    for d, count in planned_query:
        if d:
            planned_data[d] = count

    for d, count in actual_query:
        if d:
            actual_data[d] = count

    return jsonify({
        'dates': dates,
        'series': [
            {
                'name': '计划交付',
                'data': [planned_data.get(start_date + timedelta(days=i), 0) for i in range(days + 1)]
            },
            {
                'name': '实际交付',
                'data': [actual_data.get(start_date + timedelta(days=i), 0) for i in range(days + 1)]
            }
        ]
    })


@dashboard_bp.route('/charts/process-capacity', methods=['GET'])
def get_process_capacity_chart():
    """工序产能利用率（柱状图数据）"""
    # 统计各工序的任务数量和完成情况
    process_stats = db.session.query(
        ProductionStep.step_name,
        func.count(ProductionStep.id).label('total'),
        func.sum(
            db.case(
                (ProductionStep.status == 'completed', 1),
                else_=0
            )
        ).label('completed'),
        func.sum(
            db.case(
                (ProductionStep.status == 'in_progress', 1),
                else_=0
            )
        ).label('in_progress')
    ).group_by(ProductionStep.step_name).all()

    data = []
    for name, total, completed, in_progress in process_stats:
        # 利用率 = (进行中 + 已完成) / 总数 * 100
        utilization = ((completed or 0) + (in_progress or 0)) / total * 100 if total > 0 else 0
        data.append({
            'name': name,
            'total': total,
            'completed': completed or 0,
            'in_progress': in_progress or 0,
            'utilization': round(utilization, 1)
        })

    # 按利用率排序
    data.sort(key=lambda x: x['utilization'], reverse=True)

    return jsonify({
        'categories': [d['name'] for d in data],
        'series': [{
            'name': '利用率',
            'data': [d['utilization'] for d in data]
        }],
        'details': data
    })


@dashboard_bp.route('/charts/customer-ranking', methods=['GET'])
def get_customer_ranking_chart():
    """客户订单金额排行（横向柱状图数据）"""
    limit = request.args.get('limit', 10, type=int)

    # 这里假设有订单金额字段，如果没有则用数量代替
    customer_stats = db.session.query(
        ProductionPlan.customer_name,
        ProductionPlan.customer_id,
        func.count(ProductionPlan.id).label('order_count'),
        func.sum(ProductionPlan.plan_quantity).label('total_quantity')
    ).filter(
        ProductionPlan.customer_name.isnot(None)
    ).group_by(
        ProductionPlan.customer_id,
        ProductionPlan.customer_name
    ).order_by(
        func.count(ProductionPlan.id).desc()
    ).limit(limit).all()

    data = []
    for name, cid, count, qty in customer_stats:
        data.append({
            'customer': name or f'客户{cid}',
            'customer_id': cid,
            'order_count': count,
            'total_quantity': qty or 0
        })

    return jsonify({
        'categories': [d['customer'] for d in data],
        'series': [{
            'name': '订单数',
            'data': [d['order_count'] for d in data]
        }],
        'details': data
    })


@dashboard_bp.route('/overview', methods=['GET'])
def get_dashboard_overview():
    """获取仪表盘概览（合并多个接口减少请求）"""
    kpi = get_kpi_summary().get_json()
    order_status = get_order_status_chart().get_json()

    return jsonify({
        'kpi': kpi,
        'order_status': order_status['data']
    })
