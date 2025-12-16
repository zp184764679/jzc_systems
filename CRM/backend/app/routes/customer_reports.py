# -*- coding: utf-8 -*-
"""
客户分析报表 API
提供客户概览、等级分布、增长趋势、活跃度分析、销售额排行等报表功能
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import Blueprint, jsonify, request
from sqlalchemy import func, and_, or_, extract, case, desc, asc, distinct
from collections import defaultdict

from ..models.core import Order, OrderLine, OrderStatus
from ..models.customer import Customer
from ..models.sales import SalesOpportunity, FollowUpRecord
from ..models.contract import Contract
from .. import db

bp = Blueprint("customer_reports", __name__, url_prefix="/api/customers/reports")


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


def _safe_int(v):
    """安全转换为整数"""
    try:
        if v is None:
            return 0
        return int(v)
    except:
        return 0


# === 客户概览统计 ===

@bp.route('/overview', methods=['GET'])
def get_customer_overview():
    """
    客户概览统计
    返回: 客户总数、本月新增、本年新增、重点客户数、各等级客户数
    """
    try:
        today = date.today()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        # 总客户数
        total_customers = Customer.query.count()

        # 本月新增
        month_new = Customer.query.filter(
            Customer.created_at >= month_start
        ).count()

        # 本年新增
        year_new = Customer.query.filter(
            Customer.created_at >= year_start
        ).count()

        # 重点客户数
        key_accounts = Customer.query.filter(
            Customer.is_key_account == True
        ).count()

        # 各等级客户数
        grade_stats = db.session.query(
            Customer.grade,
            func.count(Customer.id).label('count')
        ).group_by(Customer.grade).all()

        grade_distribution = {
            'vip': 0,
            'gold': 0,
            'silver': 0,
            'regular': 0
        }
        for g in grade_stats:
            if g.grade in grade_distribution:
                grade_distribution[g.grade] = g.count

        return jsonify({
            'success': True,
            'data': {
                'total_customers': total_customers,
                'month_new': month_new,
                'year_new': year_new,
                'key_accounts': key_accounts,
                'grade_distribution': grade_distribution
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 客户等级分布 ===

@bp.route('/grade-distribution', methods=['GET'])
def get_grade_distribution():
    """
    客户等级分布详情
    返回: 各等级客户数量和占比
    """
    try:
        total = Customer.query.count() or 1

        grade_stats = db.session.query(
            Customer.grade,
            func.count(Customer.id).label('count')
        ).group_by(Customer.grade).all()

        distribution = []
        grade_names = {
            'vip': 'VIP客户',
            'gold': '金牌客户',
            'silver': '银牌客户',
            'regular': '普通客户'
        }

        for g in grade_stats:
            distribution.append({
                'grade': g.grade or 'regular',
                'grade_name': grade_names.get(g.grade, '普通客户'),
                'count': g.count,
                'percentage': round(g.count / total * 100, 2)
            })

        # 确保所有等级都有数据
        existing_grades = {d['grade'] for d in distribution}
        for grade, name in grade_names.items():
            if grade not in existing_grades:
                distribution.append({
                    'grade': grade,
                    'grade_name': name,
                    'count': 0,
                    'percentage': 0
                })

        # 按等级排序
        grade_order = {'vip': 0, 'gold': 1, 'silver': 2, 'regular': 3}
        distribution.sort(key=lambda x: grade_order.get(x['grade'], 99))

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'distribution': distribution
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 客户增长趋势 ===

@bp.route('/growth-trend', methods=['GET'])
def get_customer_growth_trend():
    """
    客户增长趋势
    参数:
      - period: 周期类型 (day/week/month/year)，默认 month
      - months: 统计月数，默认 12
    """
    try:
        period = request.args.get('period', 'month')
        months = int(request.args.get('months', 12))

        today = date.today()
        start_date = today - timedelta(days=months * 30)

        # 查询各时间段的新增客户数
        if period == 'day':
            # 按天统计（最近30天）
            start_date = today - timedelta(days=30)
            query = db.session.query(
                func.date(Customer.created_at).label('date'),
                func.count(Customer.id).label('count')
            ).filter(
                Customer.created_at >= start_date
            ).group_by(
                func.date(Customer.created_at)
            ).order_by('date').all()

            trend = [{'date': str(r.date), 'count': r.count} for r in query]

        elif period == 'week':
            # 按周统计
            query = db.session.query(
                func.yearweek(Customer.created_at).label('yearweek'),
                func.count(Customer.id).label('count')
            ).filter(
                Customer.created_at >= start_date
            ).group_by('yearweek').order_by('yearweek').all()

            trend = [{'week': str(r.yearweek), 'count': r.count} for r in query]

        elif period == 'year':
            # 按年统计
            query = db.session.query(
                extract('year', Customer.created_at).label('year'),
                func.count(Customer.id).label('count')
            ).group_by('year').order_by('year').all()

            trend = [{'year': int(r.year), 'count': r.count} for r in query]

        else:
            # 默认按月统计
            query = db.session.query(
                extract('year', Customer.created_at).label('year'),
                extract('month', Customer.created_at).label('month'),
                func.count(Customer.id).label('count')
            ).filter(
                Customer.created_at >= start_date
            ).group_by('year', 'month').order_by('year', 'month').all()

            trend = [
                {'month': f"{int(r.year)}-{int(r.month):02d}", 'count': r.count}
                for r in query
            ]

        # 计算累计客户数（用于显示累计曲线）
        cumulative = []
        total = 0
        for item in trend:
            total += item['count']
            cumulative.append({**item, 'cumulative': total})

        return jsonify({
            'success': True,
            'data': {
                'period': period,
                'trend': trend,
                'cumulative': cumulative
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 客户销售额排行 ===

@bp.route('/sales-ranking', methods=['GET'])
def get_customer_sales_ranking():
    """
    客户销售额排行
    参数:
      - date_from: 开始日期
      - date_to: 结束日期
      - top: 返回数量，默认 20
      - order_by: 排序字段 (amount/count)，默认 amount
    """
    try:
        date_from = _parse_date(request.args.get('date_from'))
        date_to = _parse_date(request.args.get('date_to'))
        top = int(request.args.get('top', 20))
        order_by = request.args.get('order_by', 'amount')

        # 基础查询 - 关联订单和客户
        query = db.session.query(
            Customer.id,
            Customer.code,
            Customer.short_name,
            Customer.name,
            Customer.grade,
            func.count(Order.id).label('order_count'),
            func.sum(Order.order_qty).label('total_qty'),
            func.sum(Order.order_amount).label('total_amount')
        ).join(
            Order, Order.customer_id == Customer.id
        ).filter(
            Order.status.in_([
                OrderStatus.CONFIRMED.value,
                OrderStatus.IN_PRODUCTION.value,
                OrderStatus.IN_DELIVERY.value,
                OrderStatus.COMPLETED.value
            ])
        )

        if date_from:
            query = query.filter(Order.order_date >= date_from)
        if date_to:
            query = query.filter(Order.order_date <= date_to)

        query = query.group_by(Customer.id)

        if order_by == 'count':
            query = query.order_by(desc('order_count'))
        else:
            query = query.order_by(desc('total_amount'))

        results = query.limit(top).all()

        ranking = []
        for i, r in enumerate(results, 1):
            ranking.append({
                'rank': i,
                'customer_id': r.id,
                'customer_code': r.code or '',
                'customer_short_name': r.short_name or '',
                'customer_name': r.name or '',
                'grade': r.grade or 'regular',
                'order_count': _safe_int(r.order_count),
                'total_qty': _safe_float(r.total_qty),
                'total_amount': _safe_float(r.total_amount)
            })

        return jsonify({
            'success': True,
            'data': {
                'ranking': ranking,
                'date_from': str(date_from) if date_from else None,
                'date_to': str(date_to) if date_to else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 客户活跃度分析 ===

@bp.route('/activity-analysis', methods=['GET'])
def get_customer_activity_analysis():
    """
    客户活跃度分析
    基于订单频次和跟进记录分析客户活跃度
    参数:
      - months: 统计月数，默认 6
    """
    try:
        months = int(request.args.get('months', 6))
        today = date.today()
        start_date = today - timedelta(days=months * 30)

        # 活跃客户（有订单的客户）
        active_customers = db.session.query(
            distinct(Order.customer_id)
        ).filter(
            Order.order_date >= start_date,
            Order.status != OrderStatus.CANCELLED.value
        ).count()

        # 沉睡客户（超过指定时间没有订单）
        # 首先获取所有客户ID
        all_customer_ids = set([c.id for c in Customer.query.all()])

        # 获取活跃客户ID
        active_ids_query = db.session.query(
            distinct(Order.customer_id)
        ).filter(
            Order.order_date >= start_date,
            Order.status != OrderStatus.CANCELLED.value
        ).all()
        active_ids = set([r[0] for r in active_ids_query if r[0]])

        # 沉睡客户 = 所有客户 - 活跃客户
        dormant_count = len(all_customer_ids - active_ids)

        # 新客户（首次下单在统计期内）
        subquery = db.session.query(
            Order.customer_id,
            func.min(Order.order_date).label('first_order_date')
        ).group_by(Order.customer_id).subquery()

        new_customers = db.session.query(
            func.count(subquery.c.customer_id)
        ).filter(
            subquery.c.first_order_date >= start_date
        ).scalar() or 0

        # 流失客户（之前有订单，但统计期内无订单）
        # 在活跃期之前有订单的客户
        prev_active_ids_query = db.session.query(
            distinct(Order.customer_id)
        ).filter(
            Order.order_date < start_date,
            Order.status != OrderStatus.CANCELLED.value
        ).all()
        prev_active_ids = set([r[0] for r in prev_active_ids_query if r[0]])

        lost_customers = len(prev_active_ids - active_ids)

        # 高频客户（订单数>=5）
        high_freq_subquery = db.session.query(
            Order.customer_id,
            func.count(Order.id).label('order_count')
        ).filter(
            Order.order_date >= start_date,
            Order.status != OrderStatus.CANCELLED.value
        ).group_by(Order.customer_id).subquery()

        high_frequency_customers = db.session.query(
            func.count(high_freq_subquery.c.customer_id)
        ).filter(
            high_freq_subquery.c.order_count >= 5
        ).scalar() or 0

        # 跟进活动统计
        follow_up_count = FollowUpRecord.query.filter(
            FollowUpRecord.follow_up_date >= start_date
        ).count()

        total_customers = len(all_customer_ids)

        return jsonify({
            'success': True,
            'data': {
                'period_months': months,
                'total_customers': total_customers,
                'active_customers': active_customers,
                'dormant_customers': dormant_count,
                'new_customers': new_customers,
                'lost_customers': lost_customers,
                'high_frequency_customers': high_frequency_customers,
                'follow_up_activities': follow_up_count,
                'active_rate': round(active_customers / total_customers * 100, 2) if total_customers > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 客户交易频次分布 ===

@bp.route('/transaction-frequency', methods=['GET'])
def get_transaction_frequency():
    """
    客户交易频次分布
    参数:
      - date_from: 开始日期
      - date_to: 结束日期
    """
    try:
        date_from = _parse_date(request.args.get('date_from'))
        date_to = _parse_date(request.args.get('date_to'))

        if not date_from:
            date_from = date.today() - timedelta(days=365)
        if not date_to:
            date_to = date.today()

        # 统计每个客户的订单数
        subquery = db.session.query(
            Order.customer_id,
            func.count(Order.id).label('order_count')
        ).filter(
            Order.order_date >= date_from,
            Order.order_date <= date_to,
            Order.status != OrderStatus.CANCELLED.value
        ).group_by(Order.customer_id).subquery()

        # 按订单数分组统计客户数
        # 1次、2-5次、6-10次、11-20次、20次以上
        frequency_distribution = []

        # 1次
        count_1 = db.session.query(
            func.count(subquery.c.customer_id)
        ).filter(subquery.c.order_count == 1).scalar() or 0
        frequency_distribution.append({'range': '1次', 'count': count_1})

        # 2-5次
        count_2_5 = db.session.query(
            func.count(subquery.c.customer_id)
        ).filter(
            subquery.c.order_count >= 2,
            subquery.c.order_count <= 5
        ).scalar() or 0
        frequency_distribution.append({'range': '2-5次', 'count': count_2_5})

        # 6-10次
        count_6_10 = db.session.query(
            func.count(subquery.c.customer_id)
        ).filter(
            subquery.c.order_count >= 6,
            subquery.c.order_count <= 10
        ).scalar() or 0
        frequency_distribution.append({'range': '6-10次', 'count': count_6_10})

        # 11-20次
        count_11_20 = db.session.query(
            func.count(subquery.c.customer_id)
        ).filter(
            subquery.c.order_count >= 11,
            subquery.c.order_count <= 20
        ).scalar() or 0
        frequency_distribution.append({'range': '11-20次', 'count': count_11_20})

        # 20次以上
        count_20_plus = db.session.query(
            func.count(subquery.c.customer_id)
        ).filter(subquery.c.order_count > 20).scalar() or 0
        frequency_distribution.append({'range': '20次以上', 'count': count_20_plus})

        return jsonify({
            'success': True,
            'data': {
                'date_from': str(date_from),
                'date_to': str(date_to),
                'distribution': frequency_distribution
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 客户结算方式分布 ===

@bp.route('/settlement-distribution', methods=['GET'])
def get_settlement_distribution():
    """
    客户结算方式分布
    """
    try:
        stats = db.session.query(
            Customer.settlement_method,
            func.count(Customer.id).label('count')
        ).group_by(Customer.settlement_method).all()

        total = Customer.query.count() or 1

        distribution = []
        for s in stats:
            method = s.settlement_method or '未设置'
            distribution.append({
                'settlement_method': method,
                'count': s.count,
                'percentage': round(s.count / total * 100, 2)
            })

        # 按数量排序
        distribution.sort(key=lambda x: x['count'], reverse=True)

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'distribution': distribution
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 客户币种分布 ===

@bp.route('/currency-distribution', methods=['GET'])
def get_currency_distribution():
    """
    客户默认币种分布
    """
    try:
        stats = db.session.query(
            Customer.currency_default,
            func.count(Customer.id).label('count')
        ).group_by(Customer.currency_default).all()

        total = Customer.query.count() or 1

        distribution = []
        for s in stats:
            currency = s.currency_default or '未设置'
            distribution.append({
                'currency': currency,
                'count': s.count,
                'percentage': round(s.count / total * 100, 2)
            })

        distribution.sort(key=lambda x: x['count'], reverse=True)

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'distribution': distribution
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 商机转化分析 ===

@bp.route('/opportunity-conversion', methods=['GET'])
def get_opportunity_conversion():
    """
    商机转化分析
    按客户分析商机赢单率
    """
    try:
        # 按客户统计商机数和赢单数
        stats = db.session.query(
            Customer.id,
            Customer.short_name,
            Customer.name,
            func.count(SalesOpportunity.id).label('total_opportunities'),
            func.sum(
                case((SalesOpportunity.stage == 'closed_won', 1), else_=0)
            ).label('won_count'),
            func.sum(
                case((SalesOpportunity.stage == 'closed_lost', 1), else_=0)
            ).label('lost_count'),
            func.sum(SalesOpportunity.expected_amount).label('total_expected'),
            func.sum(
                case(
                    (SalesOpportunity.stage == 'closed_won', SalesOpportunity.expected_amount),
                    else_=0
                )
            ).label('won_amount')
        ).join(
            SalesOpportunity, SalesOpportunity.customer_id == Customer.id
        ).group_by(Customer.id).all()

        results = []
        for s in stats:
            total = s.total_opportunities or 0
            won = s.won_count or 0
            conversion_rate = round(won / total * 100, 2) if total > 0 else 0

            results.append({
                'customer_id': s.id,
                'customer_name': s.short_name or s.name or '',
                'total_opportunities': total,
                'won_count': won,
                'lost_count': s.lost_count or 0,
                'conversion_rate': conversion_rate,
                'total_expected': _safe_float(s.total_expected),
                'won_amount': _safe_float(s.won_amount)
            })

        # 按赢单数排序
        results.sort(key=lambda x: x['won_count'], reverse=True)

        # 整体转化率
        total_all = sum(r['total_opportunities'] for r in results)
        won_all = sum(r['won_count'] for r in results)
        overall_conversion = round(won_all / total_all * 100, 2) if total_all > 0 else 0

        return jsonify({
            'success': True,
            'data': {
                'customers': results[:20],  # 返回前20
                'summary': {
                    'total_opportunities': total_all,
                    'total_won': won_all,
                    'overall_conversion_rate': overall_conversion
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# === 客户综合报表 ===

@bp.route('/comprehensive', methods=['GET'])
def get_comprehensive_report():
    """
    客户综合报表
    包含概览、等级、活跃度、销售额等综合数据
    参数:
      - months: 统计月数，默认 12
    """
    try:
        months = int(request.args.get('months', 12))
        today = date.today()
        start_date = today - timedelta(days=months * 30)

        # 客户概览
        total_customers = Customer.query.count()
        month_start = today.replace(day=1)
        month_new = Customer.query.filter(Customer.created_at >= month_start).count()
        key_accounts = Customer.query.filter(Customer.is_key_account == True).count()

        # 等级分布
        grade_stats = db.session.query(
            Customer.grade,
            func.count(Customer.id).label('count')
        ).group_by(Customer.grade).all()

        grade_distribution = {}
        for g in grade_stats:
            grade_distribution[g.grade or 'regular'] = g.count

        # 订单统计
        order_stats = db.session.query(
            func.count(Order.id).label('order_count'),
            func.sum(Order.order_amount).label('total_amount'),
            func.count(distinct(Order.customer_id)).label('ordering_customers')
        ).filter(
            Order.order_date >= start_date,
            Order.status != OrderStatus.CANCELLED.value
        ).first()

        # Top 10 客户
        top_customers = db.session.query(
            Customer.id,
            Customer.short_name,
            Customer.name,
            Customer.grade,
            func.sum(Order.order_amount).label('total_amount')
        ).join(
            Order, Order.customer_id == Customer.id
        ).filter(
            Order.order_date >= start_date,
            Order.status != OrderStatus.CANCELLED.value
        ).group_by(Customer.id).order_by(desc('total_amount')).limit(10).all()

        top_list = [
            {
                'customer_id': c.id,
                'customer_name': c.short_name or c.name or '',
                'grade': c.grade or 'regular',
                'total_amount': _safe_float(c.total_amount)
            }
            for c in top_customers
        ]

        return jsonify({
            'success': True,
            'data': {
                'overview': {
                    'total_customers': total_customers,
                    'month_new': month_new,
                    'key_accounts': key_accounts,
                    'ordering_customers': order_stats.ordering_customers or 0 if order_stats else 0,
                    'total_orders': order_stats.order_count or 0 if order_stats else 0,
                    'total_amount': _safe_float(order_stats.total_amount) if order_stats else 0
                },
                'grade_distribution': grade_distribution,
                'top_customers': top_list,
                'period_months': months
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
