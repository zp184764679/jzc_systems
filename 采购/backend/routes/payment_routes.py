# -*- coding: utf-8 -*-
"""
采购付款管理路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from sqlalchemy import func, extract

from extensions import db
from models.payment import (
    Payment, PaymentPlan,
    PAYMENT_STATUS_LABELS, PAYMENT_TYPE_LABELS, PAYMENT_METHOD_LABELS
)
from models.supplier import Supplier

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payments', __name__)
URL_PREFIX = '/api/v1'


# ==================== 付款 CRUD ====================

@payment_bp.route('/payments', methods=['GET'])
def get_payments():
    """获取付款列表"""
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # 筛选参数
        status = request.args.get('status')
        payment_type = request.args.get('payment_type')
        supplier_id = request.args.get('supplier_id', type=int)
        search = request.args.get('search', '').strip()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        overdue_only = request.args.get('overdue_only', 'false').lower() == 'true'

        query = Payment.query

        if status:
            query = query.filter(Payment.status == status)
        if payment_type:
            query = query.filter(Payment.payment_type == payment_type)
        if supplier_id:
            query = query.filter(Payment.supplier_id == supplier_id)
        if search:
            query = query.filter(
                db.or_(
                    Payment.payment_number.ilike(f'%{search}%'),
                    Payment.supplier_name.ilike(f'%{search}%'),
                    Payment.po_number.ilike(f'%{search}%'),
                    Payment.invoice_number.ilike(f'%{search}%')
                )
            )
        if start_date:
            query = query.filter(Payment.due_date >= start_date)
        if end_date:
            query = query.filter(Payment.due_date <= end_date)

        # 只显示逾期的付款
        if overdue_only:
            today = datetime.utcnow().date()
            query = query.filter(
                Payment.due_date < today,
                Payment.status.notin_(['paid', 'cancelled'])
            )

        # 排序
        query = query.order_by(Payment.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })

    except Exception as e:
        logger.error(f"获取付款列表失败: {e}")
        return jsonify({'error': '获取付款列表失败'}), 500


@payment_bp.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    """获取付款详情"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': '付款记录不存在'}), 404

        return jsonify(payment.to_dict())

    except Exception as e:
        logger.error(f"获取付款详情失败: {e}")
        return jsonify({'error': '获取付款详情失败'}), 500


@payment_bp.route('/payments', methods=['POST'])
def create_payment():
    """创建付款"""
    try:
        data = request.get_json() or {}

        # 验证必填字段
        required_fields = ['supplier_id', 'amount']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        # 获取供应商信息
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        # 生成付款编号
        payment_number = Payment.generate_payment_number()

        # 计算金额
        amount = float(data.get('amount', 0))
        tax_amount = float(data.get('tax_amount', 0))
        total_amount = amount + tax_amount

        # 创建付款
        payment = Payment(
            payment_number=payment_number,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            po_id=data.get('po_id'),
            po_number=data.get('po_number'),
            invoice_id=data.get('invoice_id'),
            invoice_number=data.get('invoice_number'),
            contract_id=data.get('contract_id'),
            contract_number=data.get('contract_number'),
            payment_type=data.get('payment_type', 'full'),
            payment_method=data.get('payment_method', 'bank_transfer'),
            currency=data.get('currency', 'CNY'),
            amount=amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None,
            bank_name=data.get('bank_name') or (supplier.bank_name if hasattr(supplier, 'bank_name') else None),
            bank_account=data.get('bank_account') or (supplier.bank_account if hasattr(supplier, 'bank_account') else None),
            bank_account_name=data.get('bank_account_name') or (supplier.bank_account_name if hasattr(supplier, 'bank_account_name') else None),
            status='draft',
            created_by=data.get('created_by'),
            remarks=data.get('remarks'),
        )

        db.session.add(payment)
        db.session.commit()

        return jsonify({
            'message': '付款创建成功',
            'payment': payment.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建付款失败: {e}")
        return jsonify({'error': f'创建付款失败: {str(e)}'}), 500


@payment_bp.route('/payments/<int:payment_id>', methods=['PUT'])
def update_payment(payment_id):
    """更新付款"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': '付款记录不存在'}), 404

        if payment.status not in ['draft', 'pending_approval']:
            return jsonify({'error': '只能修改草稿或待审批状态的付款'}), 400

        data = request.get_json() or {}

        # 更新基本信息
        if 'payment_type' in data:
            payment.payment_type = data['payment_type']
        if 'payment_method' in data:
            payment.payment_method = data['payment_method']
        if 'amount' in data:
            payment.amount = float(data['amount'])
        if 'tax_amount' in data:
            payment.tax_amount = float(data['tax_amount'])
        if 'amount' in data or 'tax_amount' in data:
            payment.total_amount = float(payment.amount) + float(payment.tax_amount)
        if 'due_date' in data:
            payment.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data['due_date'] else None
        if 'bank_name' in data:
            payment.bank_name = data['bank_name']
        if 'bank_account' in data:
            payment.bank_account = data['bank_account']
        if 'bank_account_name' in data:
            payment.bank_account_name = data['bank_account_name']
        if 'remarks' in data:
            payment.remarks = data['remarks']

        db.session.commit()

        return jsonify({
            'message': '付款更新成功',
            'payment': payment.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新付款失败: {e}")
        return jsonify({'error': f'更新付款失败: {str(e)}'}), 500


@payment_bp.route('/payments/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    """删除付款"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': '付款记录不存在'}), 404

        if payment.status not in ['draft', 'cancelled']:
            return jsonify({'error': '只能删除草稿或已取消的付款'}), 400

        db.session.delete(payment)
        db.session.commit()

        return jsonify({'message': '付款删除成功'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除付款失败: {e}")
        return jsonify({'error': '删除付款失败'}), 500


# ==================== 付款审批 ====================

@payment_bp.route('/payments/<int:payment_id>/submit', methods=['POST'])
def submit_payment(payment_id):
    """提交付款审批"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': '付款记录不存在'}), 404

        if payment.status != 'draft':
            return jsonify({'error': '只能提交草稿状态的付款'}), 400

        data = request.get_json() or {}

        payment.status = 'pending_approval'
        payment.submitted_by = data.get('submitted_by')
        payment.submitted_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '付款已提交审批',
            'payment': payment.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"提交付款审批失败: {e}")
        return jsonify({'error': '提交付款审批失败'}), 500


@payment_bp.route('/payments/<int:payment_id>/approve', methods=['POST'])
def approve_payment(payment_id):
    """审批通过付款"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': '付款记录不存在'}), 404

        if payment.status != 'pending_approval':
            return jsonify({'error': '只能审批待审批状态的付款'}), 400

        data = request.get_json() or {}

        payment.status = 'approved'
        payment.approved_by = data.get('approved_by')
        payment.approved_at = datetime.utcnow()
        payment.approval_note = data.get('approval_note')

        db.session.commit()

        return jsonify({
            'message': '付款审批通过',
            'payment': payment.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"审批付款失败: {e}")
        return jsonify({'error': '审批付款失败'}), 500


@payment_bp.route('/payments/<int:payment_id>/reject', methods=['POST'])
def reject_payment(payment_id):
    """拒绝付款"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': '付款记录不存在'}), 404

        if payment.status != 'pending_approval':
            return jsonify({'error': '只能拒绝待审批状态的付款'}), 400

        data = request.get_json() or {}

        payment.status = 'draft'  # 退回草稿状态
        payment.approval_note = data.get('rejection_reason', '审批未通过')

        db.session.commit()

        return jsonify({
            'message': '付款已退回',
            'payment': payment.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"拒绝付款失败: {e}")
        return jsonify({'error': '拒绝付款失败'}), 500


@payment_bp.route('/payments/<int:payment_id>/process', methods=['POST'])
def process_payment(payment_id):
    """开始处理付款"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': '付款记录不存在'}), 404

        if payment.status != 'approved':
            return jsonify({'error': '只能处理已批准的付款'}), 400

        payment.status = 'processing'
        db.session.commit()

        return jsonify({
            'message': '付款处理中',
            'payment': payment.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"处理付款失败: {e}")
        return jsonify({'error': '处理付款失败'}), 500


@payment_bp.route('/payments/<int:payment_id>/confirm', methods=['POST'])
def confirm_payment(payment_id):
    """确认付款完成"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': '付款记录不存在'}), 404

        if payment.status not in ['approved', 'processing']:
            return jsonify({'error': '只能确认已批准或处理中的付款'}), 400

        data = request.get_json() or {}

        payment.status = 'paid'
        payment.payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d').date() if data.get('payment_date') else datetime.utcnow().date()
        payment.voucher_number = data.get('voucher_number')
        payment.voucher_path = data.get('voucher_path')

        # 更新关联的付款计划
        if data.get('plan_id'):
            plan = PaymentPlan.query.get(data['plan_id'])
            if plan:
                plan.payment_id = payment.id
                plan.actual_amount = float(payment.total_amount)
                plan.actual_date = payment.payment_date
                plan.is_completed = True

        db.session.commit()

        return jsonify({
            'message': '付款已确认完成',
            'payment': payment.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"确认付款失败: {e}")
        return jsonify({'error': f'确认付款失败: {str(e)}'}), 500


@payment_bp.route('/payments/<int:payment_id>/cancel', methods=['POST'])
def cancel_payment(payment_id):
    """取消付款"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'error': '付款记录不存在'}), 404

        if payment.status == 'paid':
            return jsonify({'error': '已付款的记录不能取消'}), 400

        data = request.get_json() or {}

        payment.status = 'cancelled'
        payment.remarks = data.get('cancel_reason', payment.remarks)

        db.session.commit()

        return jsonify({
            'message': '付款已取消',
            'payment': payment.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"取消付款失败: {e}")
        return jsonify({'error': '取消付款失败'}), 500


# ==================== 付款计划 ====================

@payment_bp.route('/payment-plans', methods=['GET'])
def get_payment_plans():
    """获取付款计划列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        supplier_id = request.args.get('supplier_id', type=int)
        po_id = request.args.get('po_id', type=int)
        contract_id = request.args.get('contract_id', type=int)
        completed = request.args.get('completed')
        overdue_only = request.args.get('overdue_only', 'false').lower() == 'true'

        query = PaymentPlan.query

        if supplier_id:
            query = query.filter(PaymentPlan.supplier_id == supplier_id)
        if po_id:
            query = query.filter(PaymentPlan.po_id == po_id)
        if contract_id:
            query = query.filter(PaymentPlan.contract_id == contract_id)
        if completed is not None:
            query = query.filter(PaymentPlan.is_completed == (completed.lower() == 'true'))
        if overdue_only:
            today = datetime.utcnow().date()
            query = query.filter(
                PaymentPlan.due_date < today,
                PaymentPlan.is_completed == False
            )

        query = query.order_by(PaymentPlan.due_date)
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })

    except Exception as e:
        logger.error(f"获取付款计划失败: {e}")
        return jsonify({'error': '获取付款计划失败'}), 500


@payment_bp.route('/payment-plans', methods=['POST'])
def create_payment_plan():
    """创建付款计划"""
    try:
        data = request.get_json() or {}

        required_fields = ['supplier_id', 'plan_name', 'amount', 'due_date']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        plan = PaymentPlan(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            po_id=data.get('po_id'),
            po_number=data.get('po_number'),
            contract_id=data.get('contract_id'),
            contract_number=data.get('contract_number'),
            plan_name=data['plan_name'],
            payment_type=data.get('payment_type', 'progress'),
            percentage=data.get('percentage'),
            amount=float(data['amount']),
            currency=data.get('currency', 'CNY'),
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
            condition=data.get('condition'),
            remarks=data.get('remarks'),
        )

        db.session.add(plan)
        db.session.commit()

        return jsonify({
            'message': '付款计划创建成功',
            'plan': plan.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建付款计划失败: {e}")
        return jsonify({'error': f'创建付款计划失败: {str(e)}'}), 500


@payment_bp.route('/payment-plans/<int:plan_id>', methods=['PUT'])
def update_payment_plan(plan_id):
    """更新付款计划"""
    try:
        plan = PaymentPlan.query.get(plan_id)
        if not plan:
            return jsonify({'error': '付款计划不存在'}), 404

        if plan.is_completed:
            return jsonify({'error': '已完成的计划不能修改'}), 400

        data = request.get_json() or {}

        if 'plan_name' in data:
            plan.plan_name = data['plan_name']
        if 'payment_type' in data:
            plan.payment_type = data['payment_type']
        if 'percentage' in data:
            plan.percentage = data['percentage']
        if 'amount' in data:
            plan.amount = float(data['amount'])
        if 'due_date' in data:
            plan.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        if 'condition' in data:
            plan.condition = data['condition']
        if 'remarks' in data:
            plan.remarks = data['remarks']

        db.session.commit()

        return jsonify({
            'message': '付款计划更新成功',
            'plan': plan.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新付款计划失败: {e}")
        return jsonify({'error': f'更新付款计划失败: {str(e)}'}), 500


@payment_bp.route('/payment-plans/<int:plan_id>', methods=['DELETE'])
def delete_payment_plan(plan_id):
    """删除付款计划"""
    try:
        plan = PaymentPlan.query.get(plan_id)
        if not plan:
            return jsonify({'error': '付款计划不存在'}), 404

        if plan.is_completed:
            return jsonify({'error': '已完成的计划不能删除'}), 400

        db.session.delete(plan)
        db.session.commit()

        return jsonify({'message': '付款计划删除成功'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除付款计划失败: {e}")
        return jsonify({'error': '删除付款计划失败'}), 500


# ==================== 统计和查询 ====================

@payment_bp.route('/payments/statistics', methods=['GET'])
def get_payment_statistics():
    """获取付款统计"""
    try:
        # 各状态数量
        status_counts = {}
        for status in PAYMENT_STATUS_LABELS.keys():
            count = Payment.query.filter(Payment.status == status).count()
            status_counts[status] = count

        today = datetime.utcnow().date()

        # 逾期付款
        overdue_count = Payment.query.filter(
            Payment.due_date < today,
            Payment.status.notin_(['paid', 'cancelled'])
        ).count()

        overdue_amount = db.session.query(
            func.sum(Payment.total_amount)
        ).filter(
            Payment.due_date < today,
            Payment.status.notin_(['paid', 'cancelled'])
        ).scalar() or 0

        # 本周到期
        week_end = today + timedelta(days=7)
        due_this_week = Payment.query.filter(
            Payment.due_date >= today,
            Payment.due_date <= week_end,
            Payment.status.notin_(['paid', 'cancelled'])
        ).count()

        # 本月付款统计
        current_month = today.month
        current_year = today.year
        monthly_paid = db.session.query(
            func.sum(Payment.total_amount)
        ).filter(
            extract('month', Payment.payment_date) == current_month,
            extract('year', Payment.payment_date) == current_year,
            Payment.status == 'paid'
        ).scalar() or 0

        # 待付款总额
        pending_amount = db.session.query(
            func.sum(Payment.total_amount)
        ).filter(
            Payment.status.in_(['draft', 'pending_approval', 'approved', 'processing'])
        ).scalar() or 0

        return jsonify({
            'status_counts': status_counts,
            'overdue_count': overdue_count,
            'overdue_amount': float(overdue_amount),
            'due_this_week': due_this_week,
            'monthly_paid': float(monthly_paid),
            'pending_amount': float(pending_amount)
        })

    except Exception as e:
        logger.error(f"获取付款统计失败: {e}")
        return jsonify({'error': '获取付款统计失败'}), 500


@payment_bp.route('/payments/overdue', methods=['GET'])
def get_overdue_payments():
    """获取逾期付款列表"""
    try:
        today = datetime.utcnow().date()

        payments = Payment.query.filter(
            Payment.due_date < today,
            Payment.status.notin_(['paid', 'cancelled'])
        ).order_by(Payment.due_date).all()

        return jsonify({
            'items': [p.to_dict() for p in payments],
            'total': len(payments)
        })

    except Exception as e:
        logger.error(f"获取逾期付款失败: {e}")
        return jsonify({'error': '获取逾期付款失败'}), 500


@payment_bp.route('/payments/due-soon', methods=['GET'])
def get_due_soon_payments():
    """获取即将到期的付款"""
    try:
        days = request.args.get('days', 7, type=int)
        today = datetime.utcnow().date()
        end_date = today + timedelta(days=days)

        payments = Payment.query.filter(
            Payment.due_date >= today,
            Payment.due_date <= end_date,
            Payment.status.notin_(['paid', 'cancelled'])
        ).order_by(Payment.due_date).all()

        return jsonify({
            'items': [p.to_dict() for p in payments],
            'total': len(payments)
        })

    except Exception as e:
        logger.error(f"获取即将到期付款失败: {e}")
        return jsonify({'error': '获取即将到期付款失败'}), 500


@payment_bp.route('/payments/by-supplier/<int:supplier_id>', methods=['GET'])
def get_supplier_payments(supplier_id):
    """获取供应商的所有付款"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = Payment.query.filter(Payment.supplier_id == supplier_id)
        query = query.order_by(Payment.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # 统计
        total_paid = db.session.query(
            func.sum(Payment.total_amount)
        ).filter(
            Payment.supplier_id == supplier_id,
            Payment.status == 'paid'
        ).scalar() or 0

        total_pending = db.session.query(
            func.sum(Payment.total_amount)
        ).filter(
            Payment.supplier_id == supplier_id,
            Payment.status.in_(['draft', 'pending_approval', 'approved', 'processing'])
        ).scalar() or 0

        return jsonify({
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'statistics': {
                'total_paid': float(total_paid),
                'total_pending': float(total_pending)
            }
        })

    except Exception as e:
        logger.error(f"获取供应商付款失败: {e}")
        return jsonify({'error': '获取供应商付款失败'}), 500


@payment_bp.route('/payments/enums', methods=['GET'])
def get_payment_enums():
    """获取付款枚举值"""
    return jsonify({
        'statuses': PAYMENT_STATUS_LABELS,
        'types': PAYMENT_TYPE_LABELS,
        'methods': PAYMENT_METHOD_LABELS
    })


# 蓝图列表（用于自动注册）
BLUEPRINTS = [payment_bp]
