# -*- coding: utf-8 -*-
"""
供应商自动评分服务
Supplier Rating Service - 基于实际订单数据自动计算供应商综合评分

评分维度：
1. 订单完成率 (40%) - 已完成订单数 / 总订单数
2. 响应速度 (20%) - RFQ报价响应时间（越快越好）
3. 交付及时性 (20%) - 实际交付时间 vs 承诺交货期
4. 发票合规性 (10%) - 是否按时上传发票
5. 价格竞争力 (10%) - 报价在同RFQ中的价格排名

最终评分：0-5分（保留1位小数）
"""

from datetime import datetime, timedelta
from sqlalchemy import func, desc, case
from extensions import db
from models.supplier import Supplier
from models.purchase_order import PurchaseOrder
from models.supplier_quote import SupplierQuote
import logging

logger = logging.getLogger(__name__)


def calculate_supplier_rating(supplier_id):
    """
    计算单个供应商的综合评分

    Args:
        supplier_id: 供应商ID

    Returns:
        dict: {
            'rating': float (0-5),
            'metrics': {各项指标详情},
            'total_orders': int,
            'completed_orders': int
        }
    """
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        logger.warning(f"供应商 ID={supplier_id} 不存在")
        return None

    try:
        # 获取该供应商所有订单
        all_orders = PurchaseOrder.query.filter_by(supplier_id=supplier_id).all()

        if not all_orders:
            # 新供应商，没有订单历史，默认3.0分（中性评分）
            return {
                'rating': 3.0,
                'metrics': {
                    'completion_rate': 0,
                    'response_speed': 0,
                    'delivery_timeliness': 0,
                    'invoice_compliance': 0,
                    'price_competitiveness': 0
                },
                'total_orders': 0,
                'completed_orders': 0,
                'message': '新供应商，暂无订单数据'
            }

        # 1. 订单完成率 (40%)
        total_orders = len(all_orders)
        completed_orders = len([o for o in all_orders if o.status == 'completed'])
        cancelled_orders = len([o for o in all_orders if o.status == 'cancelled'])

        # 完成率 = 已完成 / (总数 - 已取消)
        valid_orders = total_orders - cancelled_orders
        completion_rate = (completed_orders / valid_orders * 100) if valid_orders > 0 else 0
        completion_score = min(completion_rate / 100 * 5, 5.0) * 0.4  # 最高2分

        # 2. 响应速度 (20%)
        supplier_quotes = SupplierQuote.query.filter_by(
            supplier_id=supplier_id,
            status='received'  # 只统计已提交的报价
        ).all()

        response_times = []
        for quote in supplier_quotes:
            if quote.responded_at and quote.created_at:
                delta = (quote.responded_at - quote.created_at).total_seconds() / 3600  # 小时
                response_times.append(delta)

        if response_times:
            avg_response_hours = sum(response_times) / len(response_times)
            # 响应速度评分：24小时内5分，48小时内4分，72小时内3分，96小时内2分，更长1分
            if avg_response_hours <= 24:
                response_score = 5.0
            elif avg_response_hours <= 48:
                response_score = 4.0
            elif avg_response_hours <= 72:
                response_score = 3.0
            elif avg_response_hours <= 96:
                response_score = 2.0
            else:
                response_score = 1.0
            response_score = response_score * 0.2  # 最高1分
        else:
            response_score = 0

        # 3. 交付及时性 (20%)
        # 对比 confirmed_at + lead_time 与实际完成时间（此处简化为status=completed的updated_at）
        delivery_performance = []
        for order in all_orders:
            if order.status == 'completed' and order.confirmed_at and order.lead_time:
                expected_delivery = order.confirmed_at + timedelta(days=order.lead_time)
                # 使用 updated_at 作为实际交付时间（更准确需要单独字段）
                actual_delivery = order.updated_at

                if actual_delivery <= expected_delivery:
                    delivery_performance.append(1)  # 准时
                elif actual_delivery <= expected_delivery + timedelta(days=3):
                    delivery_performance.append(0.8)  # 轻微延迟（3天内）
                elif actual_delivery <= expected_delivery + timedelta(days=7):
                    delivery_performance.append(0.5)  # 中度延迟（7天内）
                else:
                    delivery_performance.append(0.2)  # 严重延迟

        if delivery_performance:
            delivery_rate = (sum(delivery_performance) / len(delivery_performance)) * 100
            delivery_score = (delivery_rate / 100 * 5) * 0.2  # 最高1分
        else:
            delivery_score = 0

        # 4. 发票合规性 (10%)
        orders_with_invoice_due = [o for o in all_orders if o.invoice_due_date]
        if orders_with_invoice_due:
            on_time_invoices = 0
            for order in orders_with_invoice_due:
                # 如果已上传发票，检查是否在截止日期前上传（简化处理，假设uploaded=True即合规）
                if order.invoice_uploaded:
                    on_time_invoices += 1

            invoice_compliance = (on_time_invoices / len(orders_with_invoice_due)) * 100
            invoice_score = (invoice_compliance / 100 * 5) * 0.1  # 最高0.5分
        else:
            invoice_score = 0

        # 5. 价格竞争力 (10%)
        # 统计该供应商在同RFQ中的价格排名（需要与同RFQ其他报价对比）
        price_rankings = []
        for order in all_orders:
            if order.quote_id:
                # 获取同一RFQ的所有报价
                same_rfq_quotes = SupplierQuote.query.filter_by(
                    rfq_id=order.rfq_id,
                    status='received'
                ).order_by(SupplierQuote.total_price.asc()).all()

                if len(same_rfq_quotes) > 1:
                    # 找到该供应商的排名（1-based）
                    for idx, quote in enumerate(same_rfq_quotes, 1):
                        if quote.supplier_id == supplier_id:
                            total_competitors = len(same_rfq_quotes)
                            # 排名越靠前得分越高：第1名得5分，最后一名得1分
                            rank_score = 5 - ((idx - 1) / (total_competitors - 1) * 4)
                            price_rankings.append(rank_score)
                            break

        if price_rankings:
            avg_price_score = sum(price_rankings) / len(price_rankings)
            price_score = avg_price_score * 0.1  # 最高0.5分
        else:
            price_score = 0

        # 综合评分
        total_score = completion_score + response_score + delivery_score + invoice_score + price_score

        # 确保评分在0-5之间
        final_rating = max(0.0, min(5.0, round(total_score, 1)))

        metrics = {
            'completion_rate': round(completion_rate, 1),
            'completion_score': round(completion_score, 2),
            'response_speed_hours': round(sum(response_times) / len(response_times), 1) if response_times else 0,
            'response_score': round(response_score, 2),
            'delivery_timeliness': round(sum(delivery_performance) / len(delivery_performance) * 100, 1) if delivery_performance else 0,
            'delivery_score': round(delivery_score, 2),
            'invoice_compliance': round(invoice_compliance if 'invoice_compliance' in locals() else 0, 1),
            'invoice_score': round(invoice_score, 2),
            'avg_price_rank_score': round(sum(price_rankings) / len(price_rankings), 2) if price_rankings else 0,
            'price_score': round(price_score, 2)
        }

        logger.info(f"✅ 供应商 {supplier.company_name} 评分计算完成: {final_rating}/5.0")

        return {
            'rating': final_rating,
            'metrics': metrics,
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'message': '评分计算成功'
        }

    except Exception as e:
        logger.error(f"❌ 计算供应商 {supplier_id} 评分时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def update_supplier_rating(supplier_id):
    """
    更新供应商评分到数据库

    Args:
        supplier_id: 供应商ID

    Returns:
        dict: 评分结果
    """
    result = calculate_supplier_rating(supplier_id)

    if not result:
        return {'success': False, 'error': '评分计算失败'}

    try:
        supplier = Supplier.query.get(supplier_id)
        if supplier:
            supplier.rating = result['rating']
            supplier.rating_updated_at = datetime.now()
            db.session.commit()

            logger.info(f"✅ 供应商 {supplier.company_name} 评分已更新: {result['rating']}/5.0")

            return {
                'success': True,
                'supplier_id': supplier_id,
                'supplier_name': supplier.company_name,
                'rating': result['rating'],
                'metrics': result['metrics'],
                'total_orders': result['total_orders'],
                'completed_orders': result['completed_orders']
            }
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 更新供应商 {supplier_id} 评分到数据库时出错: {str(e)}")
        return {'success': False, 'error': str(e)}


def batch_update_all_ratings():
    """
    批量更新所有已批准供应商的评分

    Returns:
        dict: {
            'total': int,
            'success': int,
            'failed': int,
            'results': [...]
        }
    """
    suppliers = Supplier.query.filter_by(status='approved').all()

    results = {
        'total': len(suppliers),
        'success': 0,
        'failed': 0,
        'results': []
    }

    logger.info(f"开始批量更新 {len(suppliers)} 个供应商的评分...")

    for supplier in suppliers:
        result = update_supplier_rating(supplier.id)
        if result.get('success'):
            results['success'] += 1
        else:
            results['failed'] += 1
        results['results'].append(result)

    logger.info(f"✅ 批量评分更新完成: 成功 {results['success']}/{results['total']}")

    return results


def get_top_suppliers(limit=10):
    """
    获取评分最高的供应商列表

    Args:
        limit: 返回数量限制

    Returns:
        list: 供应商列表（按评分降序）
    """
    suppliers = Supplier.query.filter(
        Supplier.status == 'approved',
        Supplier.rating.isnot(None)
    ).order_by(desc(Supplier.rating)).limit(limit).all()

    return [{
        'id': s.id,
        'code': s.code,
        'company_name': s.company_name,
        'rating': s.rating,
        'rating_updated_at': s.rating_updated_at.isoformat() if s.rating_updated_at else None
    } for s in suppliers]
