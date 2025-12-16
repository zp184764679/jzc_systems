# SHM 出货报表 API
# 提供出货统计、客户分析、产品分析、交付绩效等报表

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func, case, and_, extract
from extensions import db
from models.shipment import Shipment, ShipmentItem, DeliveryReceipt

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports/summary', methods=['GET'])
def get_summary():
    """获取出货汇总统计"""
    try:
        # 获取日期范围参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 默认本月
        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 基础筛选
        base_query = Shipment.query.filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt
        )

        # 总出货单数
        total_shipments = base_query.count()

        # 按状态统计
        status_stats = db.session.query(
            Shipment.status,
            func.count(Shipment.id).label('count')
        ).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt
        ).group_by(Shipment.status).all()

        status_data = {s.status: s.count for s in status_stats}

        # 已签收数量
        delivered_count = status_data.get('已签收', 0)
        # 已发货数量
        shipped_count = status_data.get('已发货', 0)
        # 待出货数量
        pending_count = status_data.get('待出货', 0)
        # 已取消数量
        cancelled_count = status_data.get('已取消', 0)

        # 计算出货数量
        total_qty_result = db.session.query(
            func.sum(ShipmentItem.qty).label('total_qty')
        ).join(Shipment).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt,
            Shipment.status != '已取消'
        ).first()
        total_qty = float(total_qty_result.total_qty or 0)

        # 计算上月数据用于同比
        last_month_start = (start_dt.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_month_end = start_dt.replace(day=1)

        last_month_count = Shipment.query.filter(
            Shipment.created_at >= last_month_start,
            Shipment.created_at < last_month_end
        ).count()

        # 环比增长率
        growth_rate = 0
        if last_month_count > 0:
            growth_rate = round((total_shipments - last_month_count) / last_month_count * 100, 2)

        # 按客户统计 TOP5
        top_customers = db.session.query(
            Shipment.customer_id,
            Shipment.customer_name,
            func.count(Shipment.id).label('shipment_count')
        ).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt,
            Shipment.status != '已取消'
        ).group_by(
            Shipment.customer_id, Shipment.customer_name
        ).order_by(
            func.count(Shipment.id).desc()
        ).limit(5).all()

        # 按运输方式统计
        shipping_stats = db.session.query(
            Shipment.shipping_method,
            func.count(Shipment.id).label('count')
        ).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt,
            Shipment.status != '已取消'
        ).group_by(Shipment.shipping_method).all()

        return jsonify({
            'success': True,
            'data': {
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'total_shipments': total_shipments,
                'total_qty': total_qty,
                'by_status': {
                    'pending': pending_count,
                    'shipped': shipped_count,
                    'delivered': delivered_count,
                    'cancelled': cancelled_count
                },
                'growth_rate': growth_rate,
                'last_period_count': last_month_count,
                'top_customers': [
                    {
                        'customer_id': c.customer_id,
                        'customer_name': c.customer_name or '未知客户',
                        'shipment_count': c.shipment_count
                    } for c in top_customers
                ],
                'by_shipping_method': [
                    {
                        'method': s.shipping_method or '未指定',
                        'count': s.count
                    } for s in shipping_stats
                ]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@reports_bp.route('/reports/by-customer', methods=['GET'])
def get_by_customer():
    """按客户统计出货数据"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        customer_id = request.args.get('customer_id')

        # 默认本月
        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        query = db.session.query(
            Shipment.customer_id,
            Shipment.customer_name,
            func.count(Shipment.id).label('shipment_count'),
            func.sum(case((Shipment.status == '已签收', 1), else_=0)).label('delivered_count'),
            func.sum(case((Shipment.status == '已发货', 1), else_=0)).label('shipped_count'),
            func.sum(case((Shipment.status == '待出货', 1), else_=0)).label('pending_count'),
        ).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt,
            Shipment.status != '已取消'
        )

        if customer_id:
            query = query.filter(Shipment.customer_id == customer_id)

        stats = query.group_by(
            Shipment.customer_id, Shipment.customer_name
        ).order_by(
            func.count(Shipment.id).desc()
        ).all()

        # 计算每个客户的出货数量
        customer_ids = [s.customer_id for s in stats]
        qty_stats = {}
        if customer_ids:
            qty_result = db.session.query(
                Shipment.customer_id,
                func.sum(ShipmentItem.qty).label('total_qty')
            ).join(ShipmentItem).filter(
                Shipment.created_at >= start_dt,
                Shipment.created_at < end_dt,
                Shipment.status != '已取消',
                Shipment.customer_id.in_(customer_ids)
            ).group_by(Shipment.customer_id).all()
            qty_stats = {q.customer_id: float(q.total_qty or 0) for q in qty_result}

        return jsonify({
            'success': True,
            'data': {
                'date_range': {'start': start_date, 'end': end_date},
                'customers': [
                    {
                        'customer_id': s.customer_id,
                        'customer_name': s.customer_name or '未知客户',
                        'shipment_count': s.shipment_count,
                        'delivered_count': int(s.delivered_count or 0),
                        'shipped_count': int(s.shipped_count or 0),
                        'pending_count': int(s.pending_count or 0),
                        'total_qty': qty_stats.get(s.customer_id, 0),
                        'delivery_rate': round(int(s.delivered_count or 0) / s.shipment_count * 100, 2) if s.shipment_count > 0 else 0
                    } for s in stats
                ]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@reports_bp.route('/reports/by-product', methods=['GET'])
def get_by_product():
    """按产品统计出货数据"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        product_code = request.args.get('product_code')

        # 默认本月
        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        query = db.session.query(
            ShipmentItem.product_code,
            ShipmentItem.product_name,
            ShipmentItem.unit,
            func.count(ShipmentItem.id).label('item_count'),
            func.sum(ShipmentItem.qty).label('total_qty'),
            func.count(func.distinct(Shipment.id)).label('shipment_count'),
            func.count(func.distinct(Shipment.customer_id)).label('customer_count')
        ).join(Shipment).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt,
            Shipment.status != '已取消'
        )

        if product_code:
            query = query.filter(ShipmentItem.product_code.like(f'%{product_code}%'))

        stats = query.group_by(
            ShipmentItem.product_code, ShipmentItem.product_name, ShipmentItem.unit
        ).order_by(
            func.sum(ShipmentItem.qty).desc()
        ).all()

        return jsonify({
            'success': True,
            'data': {
                'date_range': {'start': start_date, 'end': end_date},
                'products': [
                    {
                        'product_code': s.product_code,
                        'product_name': s.product_name or '未知产品',
                        'unit': s.unit or '个',
                        'item_count': s.item_count,
                        'total_qty': float(s.total_qty or 0),
                        'shipment_count': s.shipment_count,
                        'customer_count': s.customer_count
                    } for s in stats
                ]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@reports_bp.route('/reports/trend', methods=['GET'])
def get_trend():
    """获取出货趋势数据（按日/周/月）"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')  # day/week/month

        # 默认最近30天
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 根据分组方式选择提取字段
        if group_by == 'month':
            date_extract = func.date_format(Shipment.created_at, '%Y-%m')
        elif group_by == 'week':
            date_extract = func.date_format(Shipment.created_at, '%Y-%u')
        else:  # day
            date_extract = func.date(Shipment.created_at)

        # 查询趋势数据
        trend_data = db.session.query(
            date_extract.label('period'),
            func.count(Shipment.id).label('shipment_count'),
            func.sum(case((Shipment.status == '已签收', 1), else_=0)).label('delivered_count'),
            func.sum(case((Shipment.status == '已发货', 1), else_=0)).label('shipped_count'),
        ).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt,
            Shipment.status != '已取消'
        ).group_by(date_extract).order_by(date_extract).all()

        # 查询出货数量趋势
        qty_trend = db.session.query(
            date_extract.label('period'),
            func.sum(ShipmentItem.qty).label('total_qty')
        ).join(Shipment).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt,
            Shipment.status != '已取消'
        ).group_by(date_extract).all()

        qty_map = {str(q.period): float(q.total_qty or 0) for q in qty_trend}

        return jsonify({
            'success': True,
            'data': {
                'date_range': {'start': start_date, 'end': end_date},
                'group_by': group_by,
                'trend': [
                    {
                        'period': str(t.period),
                        'shipment_count': t.shipment_count,
                        'delivered_count': int(t.delivered_count or 0),
                        'shipped_count': int(t.shipped_count or 0),
                        'total_qty': qty_map.get(str(t.period), 0)
                    } for t in trend_data
                ]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@reports_bp.route('/reports/delivery-performance', methods=['GET'])
def get_delivery_performance():
    """获取交付绩效数据"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 默认本月
        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 已发货和已签收的出货单
        shipments = Shipment.query.filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt,
            Shipment.status.in_(['已发货', '已签收'])
        ).all()

        total_delivered = len([s for s in shipments if s.status == '已签收'])
        total_shipped = len(shipments)

        # 准时交付统计（预计到达日期 vs 实际签收日期）
        on_time_count = 0
        late_count = 0
        avg_delivery_days = 0
        total_delivery_days = 0
        delivery_count = 0

        for shipment in shipments:
            if shipment.status == '已签收' and shipment.receipt:
                receipt = shipment.receipt
                if receipt.sign_time and shipment.delivery_date:
                    delivery_days = (receipt.sign_time.date() - shipment.delivery_date).days
                    total_delivery_days += delivery_days
                    delivery_count += 1

                    if shipment.expected_arrival:
                        if receipt.sign_time.date() <= shipment.expected_arrival:
                            on_time_count += 1
                        else:
                            late_count += 1

        if delivery_count > 0:
            avg_delivery_days = round(total_delivery_days / delivery_count, 1)

        on_time_rate = round(on_time_count / (on_time_count + late_count) * 100, 2) if (on_time_count + late_count) > 0 else 0

        # 签收回执统计
        receipt_stats = db.session.query(
            DeliveryReceipt.receipt_condition,
            func.count(DeliveryReceipt.id).label('count')
        ).join(Shipment).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt
        ).group_by(DeliveryReceipt.receipt_condition).all()

        condition_data = {r.receipt_condition: r.count for r in receipt_stats}

        # 签收质量
        good_condition = condition_data.get('完好', 0)
        partial_damage = condition_data.get('部分损坏', 0)
        severe_damage = condition_data.get('严重损坏', 0)
        total_receipts = good_condition + partial_damage + severe_damage
        quality_rate = round(good_condition / total_receipts * 100, 2) if total_receipts > 0 else 100

        # 按承运商统计绩效
        carrier_stats = db.session.query(
            Shipment.carrier,
            func.count(Shipment.id).label('total'),
            func.sum(case((Shipment.status == '已签收', 1), else_=0)).label('delivered')
        ).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt,
            Shipment.status.in_(['已发货', '已签收']),
            Shipment.carrier.isnot(None)
        ).group_by(Shipment.carrier).all()

        return jsonify({
            'success': True,
            'data': {
                'date_range': {'start': start_date, 'end': end_date},
                'summary': {
                    'total_shipped': total_shipped,
                    'total_delivered': total_delivered,
                    'delivery_rate': round(total_delivered / total_shipped * 100, 2) if total_shipped > 0 else 0,
                    'on_time_count': on_time_count,
                    'late_count': late_count,
                    'on_time_rate': on_time_rate,
                    'avg_delivery_days': avg_delivery_days
                },
                'quality': {
                    'good_condition': good_condition,
                    'partial_damage': partial_damage,
                    'severe_damage': severe_damage,
                    'quality_rate': quality_rate
                },
                'by_carrier': [
                    {
                        'carrier': c.carrier or '未指定',
                        'total': c.total,
                        'delivered': int(c.delivered or 0),
                        'delivery_rate': round(int(c.delivered or 0) / c.total * 100, 2) if c.total > 0 else 0
                    } for c in carrier_stats
                ]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@reports_bp.route('/reports/by-warehouse', methods=['GET'])
def get_by_warehouse():
    """按仓库统计出货数据"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 默认本月
        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        stats = db.session.query(
            Shipment.warehouse_id,
            func.count(Shipment.id).label('shipment_count'),
            func.sum(case((Shipment.status == '已签收', 1), else_=0)).label('delivered_count'),
            func.sum(case((Shipment.status == '已发货', 1), else_=0)).label('shipped_count'),
            func.sum(case((Shipment.status == '待出货', 1), else_=0)).label('pending_count'),
        ).filter(
            Shipment.created_at >= start_dt,
            Shipment.created_at < end_dt,
            Shipment.status != '已取消'
        ).group_by(Shipment.warehouse_id).all()

        # 计算每个仓库的出货数量
        warehouse_ids = [s.warehouse_id for s in stats if s.warehouse_id]
        qty_stats = {}
        if warehouse_ids:
            qty_result = db.session.query(
                Shipment.warehouse_id,
                func.sum(ShipmentItem.qty).label('total_qty')
            ).join(ShipmentItem).filter(
                Shipment.created_at >= start_dt,
                Shipment.created_at < end_dt,
                Shipment.status != '已取消',
                Shipment.warehouse_id.in_(warehouse_ids)
            ).group_by(Shipment.warehouse_id).all()
            qty_stats = {q.warehouse_id: float(q.total_qty or 0) for q in qty_result}

        return jsonify({
            'success': True,
            'data': {
                'date_range': {'start': start_date, 'end': end_date},
                'warehouses': [
                    {
                        'warehouse_id': s.warehouse_id or '未指定',
                        'shipment_count': s.shipment_count,
                        'delivered_count': int(s.delivered_count or 0),
                        'shipped_count': int(s.shipped_count or 0),
                        'pending_count': int(s.pending_count or 0),
                        'total_qty': qty_stats.get(s.warehouse_id, 0)
                    } for s in stats
                ]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@reports_bp.route('/reports/export', methods=['GET'])
def export_report():
    """导出报表数据"""
    try:
        report_type = request.args.get('type', 'summary')  # summary/customer/product/trend/performance
        format_type = request.args.get('format', 'json')  # json/csv
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 根据报表类型获取数据
        if report_type == 'customer':
            # 调用按客户统计
            with request.app.test_request_context(
                f'/reports/by-customer?start_date={start_date}&end_date={end_date}'
            ):
                response = get_by_customer()
        elif report_type == 'product':
            with request.app.test_request_context(
                f'/reports/by-product?start_date={start_date}&end_date={end_date}'
            ):
                response = get_by_product()
        elif report_type == 'trend':
            with request.app.test_request_context(
                f'/reports/trend?start_date={start_date}&end_date={end_date}'
            ):
                response = get_trend()
        elif report_type == 'performance':
            with request.app.test_request_context(
                f'/reports/delivery-performance?start_date={start_date}&end_date={end_date}'
            ):
                response = get_delivery_performance()
        else:
            with request.app.test_request_context(
                f'/reports/summary?start_date={start_date}&end_date={end_date}'
            ):
                response = get_summary()

        if format_type == 'csv':
            # TODO: 实现 CSV 导出
            return jsonify({'success': False, 'error': 'CSV export not implemented yet'}), 501

        return response

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
