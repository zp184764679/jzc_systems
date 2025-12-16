# -*- coding: utf-8 -*-
"""
订单报表统计 API
提供订单汇总、客户分析、状态分布、趋势图表、交付绩效等报表功能
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import jsonify, request
from sqlalchemy import func, and_, or_, extract, case

from . import orders  # 复用 orders.py 中的 bp 和工具函数
from ..models.core import Order, OrderLine, OrderStatus
from ..models.customer import Customer
from .. import db

bp = orders.bp  # 使用同一个 Blueprint


# === 状态中文映射（复用） ===
ORDER_STATUS_MAP = {
    OrderStatus.DRAFT.value: "草稿",
    OrderStatus.PENDING.value: "待审批",
    OrderStatus.CONFIRMED.value: "已确认",
    OrderStatus.IN_PRODUCTION.value: "生产中",
    OrderStatus.IN_DELIVERY.value: "交货中",
    OrderStatus.COMPLETED.value: "已完成",
    OrderStatus.CANCELLED.value: "已取消",
}


def _parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        if isinstance(date_str, (date, datetime)):
            return date_str if isinstance(date_str, date) else date_str.date()
        return datetime.strptime(str(date_str), '%Y-%m-%d').date()
    except:
        return None


def _safe_float(v):
    """安全转换为浮点数"""
    try:
        if v is None:
            return 0.0
        if isinstance(v, Decimal):
            return float(v)
        return float(v)
    except:
        return 0.0


# === 报表汇总 API ===

@bp.route('/reports/summary', methods=['GET'])
def get_order_summary_report():
    """
    订单汇总统计
    参数:
      - date_from: 开始日期 (YYYY-MM-DD)
      - date_to: 结束日期 (YYYY-MM-DD)
    """
    date_from = _parse_date(request.args.get('date_from'))
    date_to = _parse_date(request.args.get('date_to'))

    # 基础查询
    query = db.session.query(Order)
    if date_from:
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        query = query.filter(Order.order_date <= date_to)

    # 总体统计
    total_stats = db.session.query(
        func.count(Order.id).label('total_count'),
        func.sum(Order.order_qty).label('total_qty'),
        func.sum(Order.delivered_qty).label('delivered_qty'),
        func.sum(Order.deficit_qty).label('deficit_qty'),
        func.sum(Order.unit_price * Order.order_qty).label('total_amount')
    ).filter(
        Order.order_date >= date_from if date_from else True,
        Order.order_date <= date_to if date_to else True
    ).first()

    # 按状态分组统计
    status_stats = db.session.query(
        Order.status,
        func.count(Order.id).label('count'),
        func.sum(Order.order_qty).label('qty'),
        func.sum(Order.unit_price * Order.order_qty).label('amount')
    ).filter(
        Order.order_date >= date_from if date_from else True,
        Order.order_date <= date_to if date_to else True
    ).group_by(Order.status).all()

    by_status = []
    for stat in status_stats:
        status = stat[0] or OrderStatus.DRAFT.value
        by_status.append({
            "status": status,
            "status_name": ORDER_STATUS_MAP.get(status, status),
            "count": stat[1] or 0,
            "qty": _safe_float(stat[2]),
            "amount": _safe_float(stat[3])
        })

    # 本月 vs 上月对比
    today = date.today()
    first_day_this_month = today.replace(day=1)
    first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)

    this_month_stats = db.session.query(
        func.count(Order.id).label('count'),
        func.sum(Order.order_qty).label('qty'),
        func.sum(Order.unit_price * Order.order_qty).label('amount')
    ).filter(Order.order_date >= first_day_this_month).first()

    last_month_stats = db.session.query(
        func.count(Order.id).label('count'),
        func.sum(Order.order_qty).label('qty'),
        func.sum(Order.unit_price * Order.order_qty).label('amount')
    ).filter(
        Order.order_date >= first_day_last_month,
        Order.order_date <= last_day_last_month
    ).first()

    # 计算环比增长率
    this_month_count = this_month_stats[0] or 0
    last_month_count = last_month_stats[0] or 0
    growth_rate = 0.0
    if last_month_count > 0:
        growth_rate = round((this_month_count - last_month_count) / last_month_count * 100, 2)

    return jsonify({
        "success": True,
        "date_range": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None
        },
        "total": {
            "count": total_stats[0] or 0,
            "qty": _safe_float(total_stats[1]),
            "delivered_qty": _safe_float(total_stats[2]),
            "deficit_qty": _safe_float(total_stats[3]),
            "amount": _safe_float(total_stats[4])
        },
        "by_status": by_status,
        "this_month": {
            "count": this_month_count,
            "qty": _safe_float(this_month_stats[1]),
            "amount": _safe_float(this_month_stats[2])
        },
        "last_month": {
            "count": last_month_count,
            "qty": _safe_float(last_month_stats[1]),
            "amount": _safe_float(last_month_stats[2])
        },
        "growth_rate": growth_rate
    })


# === 按客户统计 API ===

@bp.route('/reports/by-customer', methods=['GET'])
def get_order_by_customer_report():
    """
    按客户统计订单
    参数:
      - date_from: 开始日期
      - date_to: 结束日期
      - limit: 返回数量限制（默认10）
    """
    date_from = _parse_date(request.args.get('date_from'))
    date_to = _parse_date(request.args.get('date_to'))
    limit = request.args.get('limit', 10, type=int)

    # 按客户分组统计
    query = db.session.query(
        Order.customer_id,
        Order.customer_code,
        func.count(Order.id).label('order_count'),
        func.sum(Order.order_qty).label('total_qty'),
        func.sum(Order.delivered_qty).label('delivered_qty'),
        func.sum(Order.unit_price * Order.order_qty).label('total_amount')
    )

    if date_from:
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        query = query.filter(Order.order_date <= date_to)

    customer_stats = query.group_by(
        Order.customer_id,
        Order.customer_code
    ).order_by(func.count(Order.id).desc()).limit(limit).all()

    # 获取客户名称
    customer_ids = [s[0] for s in customer_stats if s[0]]
    customer_names = {}
    if customer_ids:
        customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()
        customer_names = {c.id: c.short_name or c.name for c in customers}

    top_customers = []
    for stat in customer_stats:
        customer_id = stat[0]
        customer_code = stat[1]
        customer_name = customer_names.get(customer_id, customer_code or '未知客户')

        top_customers.append({
            "customer_id": customer_id,
            "customer_code": customer_code,
            "customer_name": customer_name,
            "order_count": stat[2] or 0,
            "total_qty": _safe_float(stat[3]),
            "delivered_qty": _safe_float(stat[4]),
            "total_amount": _safe_float(stat[5])
        })

    return jsonify({
        "success": True,
        "date_range": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None
        },
        "top_customers": top_customers
    })


# === 按状态分布 API ===

@bp.route('/reports/by-status', methods=['GET'])
def get_order_by_status_report():
    """获取订单状态分布"""
    date_from = _parse_date(request.args.get('date_from'))
    date_to = _parse_date(request.args.get('date_to'))

    query = db.session.query(
        Order.status,
        func.count(Order.id).label('count'),
        func.sum(Order.order_qty).label('qty'),
        func.sum(Order.unit_price * Order.order_qty).label('amount')
    )

    if date_from:
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        query = query.filter(Order.order_date <= date_to)

    status_stats = query.group_by(Order.status).all()

    distribution = []
    total_count = 0
    for stat in status_stats:
        count = stat[1] or 0
        total_count += count
        status = stat[0] or OrderStatus.DRAFT.value
        distribution.append({
            "status": status,
            "status_name": ORDER_STATUS_MAP.get(status, status),
            "count": count,
            "qty": _safe_float(stat[2]),
            "amount": _safe_float(stat[3])
        })

    # 计算百分比
    for item in distribution:
        item['percentage'] = round(item['count'] / total_count * 100, 2) if total_count > 0 else 0

    return jsonify({
        "success": True,
        "total_count": total_count,
        "distribution": distribution
    })


# === 订单趋势 API ===

@bp.route('/reports/trend', methods=['GET'])
def get_order_trend_report():
    """
    订单趋势统计（按日/周/月）
    参数:
      - date_from: 开始日期
      - date_to: 结束日期
      - group_by: 分组方式 (day/week/month，默认 day)
    """
    date_from = _parse_date(request.args.get('date_from'))
    date_to = _parse_date(request.args.get('date_to'))
    group_by = request.args.get('group_by', 'day')

    # 默认最近30天
    if not date_to:
        date_to = date.today()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    # 根据分组方式构建查询
    if group_by == 'month':
        date_expr = func.date_format(Order.order_date, '%Y-%m')
    elif group_by == 'week':
        date_expr = func.date_format(Order.order_date, '%Y-%u')
    else:  # day
        date_expr = func.date(Order.order_date)

    trend_stats = db.session.query(
        date_expr.label('period'),
        func.count(Order.id).label('count'),
        func.sum(Order.order_qty).label('qty'),
        func.sum(Order.unit_price * Order.order_qty).label('amount')
    ).filter(
        Order.order_date >= date_from,
        Order.order_date <= date_to
    ).group_by(date_expr).order_by(date_expr).all()

    trend_data = []
    for stat in trend_stats:
        period = str(stat[0]) if stat[0] else ''
        trend_data.append({
            "period": period,
            "count": stat[1] or 0,
            "qty": _safe_float(stat[2]),
            "amount": _safe_float(stat[3])
        })

    return jsonify({
        "success": True,
        "date_range": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        },
        "group_by": group_by,
        "trend": trend_data
    })


# === 交付绩效 API ===

@bp.route('/reports/delivery-performance', methods=['GET'])
def get_delivery_performance_report():
    """
    交付绩效统计
    参数:
      - date_from: 开始日期
      - date_to: 结束日期
    """
    date_from = _parse_date(request.args.get('date_from'))
    date_to = _parse_date(request.args.get('date_to'))

    # 已完成订单
    completed_query = Order.query.filter(Order.status == OrderStatus.COMPLETED.value)
    if date_from:
        completed_query = completed_query.filter(Order.order_date >= date_from)
    if date_to:
        completed_query = completed_query.filter(Order.order_date <= date_to)

    total_completed = completed_query.count()

    # 按时交付（completed_at <= due_date）
    on_time_count = completed_query.filter(
        Order.completed_at.isnot(None),
        Order.due_date.isnot(None),
        func.date(Order.completed_at) <= Order.due_date
    ).count()

    # 逾期交付
    overdue_count = completed_query.filter(
        Order.completed_at.isnot(None),
        Order.due_date.isnot(None),
        func.date(Order.completed_at) > Order.due_date
    ).count()

    # 计算按时交付率
    on_time_rate = round(on_time_count / total_completed * 100, 2) if total_completed > 0 else 0

    # 平均订单周期（从下单到完成）
    avg_cycle_query = db.session.query(
        func.avg(func.datediff(Order.completed_at, Order.order_date))
    ).filter(
        Order.status == OrderStatus.COMPLETED.value,
        Order.completed_at.isnot(None),
        Order.order_date.isnot(None)
    )
    if date_from:
        avg_cycle_query = avg_cycle_query.filter(Order.order_date >= date_from)
    if date_to:
        avg_cycle_query = avg_cycle_query.filter(Order.order_date <= date_to)

    avg_cycle_days = avg_cycle_query.scalar()
    avg_cycle_days = round(float(avg_cycle_days or 0), 1)

    # 当前逾期订单（未完成且已过due_date）
    today = date.today()
    current_overdue = Order.query.filter(
        Order.status.in_([
            OrderStatus.CONFIRMED.value,
            OrderStatus.IN_PRODUCTION.value,
            OrderStatus.IN_DELIVERY.value
        ]),
        Order.due_date < today
    ).count()

    return jsonify({
        "success": True,
        "total_completed": total_completed,
        "on_time_count": on_time_count,
        "overdue_count": overdue_count,
        "on_time_rate": on_time_rate,
        "avg_cycle_days": avg_cycle_days,
        "current_overdue": current_overdue
    })


# === 产品销量排行 API ===

@bp.route('/reports/product-ranking', methods=['GET'])
def get_product_ranking_report():
    """
    产品销量排行
    参数:
      - date_from: 开始日期
      - date_to: 结束日期
      - limit: 返回数量限制（默认10）
    """
    date_from = _parse_date(request.args.get('date_from'))
    date_to = _parse_date(request.args.get('date_to'))
    limit = request.args.get('limit', 10, type=int)

    # 按产品分组统计
    query = db.session.query(
        Order.product,
        Order.cn_name,
        func.count(Order.id).label('order_count'),
        func.sum(Order.order_qty).label('total_qty'),
        func.sum(Order.delivered_qty).label('delivered_qty'),
        func.sum(Order.unit_price * Order.order_qty).label('total_amount')
    )

    if date_from:
        query = query.filter(Order.order_date >= date_from)
    if date_to:
        query = query.filter(Order.order_date <= date_to)

    product_stats = query.filter(
        Order.product.isnot(None),
        Order.product != ''
    ).group_by(
        Order.product,
        Order.cn_name
    ).order_by(func.sum(Order.order_qty).desc()).limit(limit).all()

    ranking = []
    for i, stat in enumerate(product_stats, 1):
        ranking.append({
            "rank": i,
            "product": stat[0],
            "cn_name": stat[1],
            "order_count": stat[2] or 0,
            "total_qty": _safe_float(stat[3]),
            "delivered_qty": _safe_float(stat[4]),
            "total_amount": _safe_float(stat[5])
        })

    return jsonify({
        "success": True,
        "date_range": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None
        },
        "ranking": ranking
    })
