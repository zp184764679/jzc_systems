# routes/invoice_routes.py
# -*- coding: utf-8 -*-
"""
发票管理路由 - 员工端

员工手动上传发票并关联采购单，支持两种结算方式：
1. 单次结算 (per_order): 每个PO对应一张发票
2. 月结 (monthly): 一张发票对应多个PO（同一供应商同一月份）
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models.invoice import Invoice, InvoicePOLink
from models.purchase_order import PurchaseOrder
from models.supplier import Supplier
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func, extract
import traceback
import subprocess
import base64
import json
import re
import os
import tempfile

URL_PREFIX = '/api/v1/invoices'

bp = Blueprint('invoice', __name__)


@bp.before_request
def handle_preflight():
    """处理CORS预检请求"""
    if request.method == 'OPTIONS':
        return '', 200


def iso(dt):
    """日期序列化"""
    return dt.isoformat(timespec='seconds') if dt else None


# ============ 员工端API ============

@bp.route('', methods=['GET', 'OPTIONS'])
def get_invoices():
    """
    获取发票列表（员工端）

    查询参数：
    - page: 页码
    - per_page: 每页数量
    - status: 状态筛选 (pending/approved/rejected)
    - supplier_id: 供应商筛选
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        status = request.args.get('status')
        supplier_id = request.args.get('supplier_id', type=int)
        settlement_type = request.args.get('settlement_type')  # per_order / monthly

        query = Invoice.query

        # 筛选条件
        if status:
            query = query.filter_by(status=status)
        if supplier_id:
            query = query.filter_by(supplier_id=supplier_id)
        if settlement_type:
            query = query.filter_by(settlement_type=settlement_type)

        # 分页
        query = query.order_by(Invoice.created_at.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        invoices = []
        for inv in paginated.items:
            invoice_dict = {
                'id': inv.id,
                'settlement_type': inv.settlement_type,
                'settlement_period': inv.settlement_period,
                'invoice_number': inv.invoice_number,
                'invoice_code': inv.invoice_code,
                'po_id': inv.po_id,
                'supplier_id': inv.supplier_id,
                'supplier_name': inv.supplier.company_name if inv.supplier else None,
                'po_number': inv.po.po_number if inv.po else None,
                'amount': float(inv.amount) if inv.amount else 0,
                'total_amount': float(inv.total_amount) if inv.total_amount else 0,
                'currency': inv.currency,
                'invoice_date': iso(inv.invoice_date),
                'file_url': inv.file_url,
                'file_name': inv.file_name,
                'status': inv.status,
                'approval_notes': inv.approval_notes,
                'created_at': iso(inv.created_at),
                'uploaded_at': iso(inv.uploaded_at),
                'approved_at': iso(inv.approved_at),
                'description': inv.description,
                'remark': inv.remark,
            }
            # 月结发票显示PO数量
            if inv.settlement_type == 'monthly':
                invoice_dict['po_count'] = len(inv.po_links) if inv.po_links else 0
            invoices.append(invoice_dict)

        return jsonify({
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page,
            'per_page': per_page,
            'invoices': invoices
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取发票列表失败: {str(e)}'}), 500


@bp.route('/overdue', methods=['GET', 'OPTIONS'])
def get_overdue_invoices():
    """
    获取超期发票列表（未在7天内上传的PO）

    返回所有超过invoice_due_date但未上传发票的PO
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        now = datetime.utcnow()

        # 查询超期的PO（invoice_due_date < now 且 invoice_uploaded = False）
        overdue_pos = PurchaseOrder.query.filter(
            and_(
                PurchaseOrder.invoice_due_date < now,
                PurchaseOrder.invoice_uploaded == False,
                PurchaseOrder.status != 'cancelled'
            )
        ).order_by(PurchaseOrder.invoice_due_date.asc()).all()

        result = []
        for po in overdue_pos:
            days_overdue = (now - po.invoice_due_date).days
            result.append({
                'po_id': po.id,
                'po_number': po.po_number,
                'supplier_id': po.supplier_id,
                'supplier_name': po.supplier_name,
                'total_price': float(po.total_price),
                'status': po.status,
                'confirmed_at': iso(po.confirmed_at),
                'invoice_due_date': iso(po.invoice_due_date),
                'days_overdue': days_overdue,
            })

        return jsonify({
            'count': len(result),
            'overdue_pos': result
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取超期发票失败: {str(e)}'}), 500


@bp.route('/stats', methods=['GET', 'OPTIONS'])
def get_invoice_stats():
    """
    获取发票统计信息（员工端）

    返回：
    - total: 总数
    - pending: 待审核
    - approved: 已批准
    - rejected: 已拒绝
    - overdue_count: 未提交超期数量
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        now = datetime.utcnow()

        # 发票统计
        total = Invoice.query.count()
        pending = Invoice.query.filter_by(status='pending').count()
        approved = Invoice.query.filter_by(status='approved').count()
        rejected = Invoice.query.filter_by(status='rejected').count()

        # 超期未提交统计
        overdue_count = PurchaseOrder.query.filter(
            and_(
                PurchaseOrder.invoice_due_date < now,
                PurchaseOrder.invoice_uploaded == False,
                PurchaseOrder.status != 'cancelled'
            )
        ).count()

        return jsonify({
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'overdue_count': overdue_count
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取统计失败: {str(e)}'}), 500


@bp.route('/<int:invoice_id>', methods=['GET', 'OPTIONS'])
def get_invoice_detail(invoice_id):
    """获取发票详情"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return jsonify({'error': '发票不存在'}), 404

        return jsonify(invoice.to_dict()), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取发票详情失败: {str(e)}'}), 500


@bp.route('/<int:invoice_id>/approve', methods=['POST', 'OPTIONS'])
def approve_invoice(invoice_id):
    """
    批准发票

    请求体：
    {
        "approval_notes": "审批意见（可选）"
    }
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json() or {}
        invoice = Invoice.query.get(invoice_id)

        if not invoice:
            return jsonify({'error': '发票不存在'}), 404

        if invoice.status != 'pending':
            return jsonify({'error': '只能审批待审核的发票'}), 400

        # 更新发票状态
        invoice.status = 'approved'
        invoice.approval_notes = data.get('approval_notes', '')
        invoice.approved_at = datetime.utcnow()
        invoice.approved_by = int(request.headers.get('User-ID', 0))

        db.session.commit()

        # 🔔 发送发票审批通过通知给供应商
        from services.notification_service import NotificationService
        if invoice.supplier:
            NotificationService.notify_invoice_approved(invoice, invoice.supplier)

        return jsonify({
            'success': True,
            'message': '发票已批准，已通知供应商',
            'invoice': invoice.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'批准发票失败: {str(e)}'}), 500


@bp.route('/<int:invoice_id>/reject', methods=['POST', 'OPTIONS'])
def reject_invoice(invoice_id):
    """
    拒绝发票

    请求体：
    {
        "approval_notes": "拒绝原因（必填）"
    }
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json() or {}
        approval_notes = data.get('approval_notes', '').strip()

        if not approval_notes:
            return jsonify({'error': '请填写拒绝原因'}), 400

        invoice = Invoice.query.get(invoice_id)

        if not invoice:
            return jsonify({'error': '发票不存在'}), 404

        if invoice.status != 'pending':
            return jsonify({'error': '只能审批待审核的发票'}), 400

        # 更新发票状态
        invoice.status = 'rejected'
        invoice.approval_notes = approval_notes
        invoice.approved_at = datetime.utcnow()
        invoice.approved_by = int(request.headers.get('User-ID', 0))

        db.session.commit()

        # 🔔 发送发票驳回通知给供应商
        from services.notification_service import NotificationService
        if invoice.supplier:
            NotificationService.notify_invoice_rejected(invoice, invoice.supplier, approval_notes)

        return jsonify({
            'success': True,
            'message': '发票已拒绝',
            'invoice': invoice.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'拒绝发票失败: {str(e)}'}), 500


# ============ 员工上传发票API ============

@bp.route('/pending-pos', methods=['GET', 'OPTIONS'])
def get_pending_invoice_pos():
    """
    获取待上传发票的PO列表（员工端）

    查询参数：
    - supplier_id: 供应商ID（可选，筛选特定供应商）
    - period: 期间（可选，YYYY-MM格式，筛选特定月份）

    返回未上传发票的PO，按供应商分组
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        supplier_id = request.args.get('supplier_id', type=int)
        period = request.args.get('period')

        # 基础查询：已确认/已收货/已完成且未上传发票
        query = PurchaseOrder.query.filter(
            PurchaseOrder.invoice_uploaded == False,
            PurchaseOrder.status.in_(['confirmed', 'received', 'completed'])
        )

        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)

        if period:
            try:
                year, month = map(int, period.split('-'))
                query = query.filter(
                    extract('year', PurchaseOrder.confirmed_at) == year,
                    extract('month', PurchaseOrder.confirmed_at) == month
                )
            except:
                pass

        pos = query.order_by(
            PurchaseOrder.supplier_id,
            PurchaseOrder.confirmed_at.desc()
        ).all()

        # 按供应商分组
        grouped = {}
        for po in pos:
            sid = po.supplier_id
            if sid not in grouped:
                supplier = Supplier.query.get(sid)
                grouped[sid] = {
                    'supplier_id': sid,
                    'supplier_name': supplier.company_name if supplier else None,
                    'supplier_code': supplier.code if supplier else None,
                    'settlement_type': supplier.settlement_type if supplier else 'per_order',
                    'pos': [],
                    'total_amount': 0
                }

            grouped[sid]['pos'].append({
                'po_id': po.id,
                'po_number': po.po_number,
                'total_price': float(po.total_price) if po.total_price else 0,
                'status': po.status,
                'confirmed_at': iso(po.confirmed_at),
            })
            grouped[sid]['total_amount'] += float(po.total_price) if po.total_price else 0

        result = list(grouped.values())

        return jsonify({
            'count': len(pos),
            'supplier_count': len(result),
            'suppliers': result
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取待上传发票PO失败: {str(e)}'}), 500


@bp.route('/upload', methods=['POST', 'OPTIONS'])
def upload_invoice_by_employee():
    """
    员工上传发票（单次结算，关联单个PO）

    请求体：
    {
        "po_id": 123,
        "invoice_number": "INV-20250101-001",
        "invoice_code": "012345678901",
        "invoice_date": "2025-01-01",
        "amount_before_tax": 10000.00,
        "tax_amount": 1300.00,
        "total_amount": 11300.00,
        "file_url": "/storage/2025-11/caigou/invoices/xxx.pdf",
        "file_name": "发票.pdf",
        "file_type": "application/pdf",
        "file_size": "1.5MB",
        "remark": "备注"
    }
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json() or {}
        user_id = int(request.headers.get('User-ID', 0))

        # 验证必填字段
        required_fields = ['po_id', 'invoice_number', 'total_amount', 'file_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        # 验证PO
        po = PurchaseOrder.query.get(data['po_id'])
        if not po:
            return jsonify({'error': 'PO不存在'}), 404

        if po.invoice_uploaded:
            return jsonify({'error': '此PO已上传发票'}), 400

        # 获取供应商
        supplier = Supplier.query.get(po.supplier_id)

        # 检查发票号是否重复
        if Invoice.query.filter_by(invoice_number=data['invoice_number']).first():
            return jsonify({'error': '发票号已存在'}), 400

        # 创建发票
        invoice = Invoice(
            settlement_type='per_order',
            supplier_id=po.supplier_id,
            po_id=po.id,
            quote_id=po.quote_id,
            invoice_number=data['invoice_number'],
            invoice_code=data.get('invoice_code'),
            invoice_date=datetime.fromisoformat(data['invoice_date']) if data.get('invoice_date') else None,
            buyer_name=data.get('buyer_name'),
            buyer_tax_id=data.get('buyer_tax_id'),
            seller_name=supplier.company_name if supplier else None,
            seller_tax_id=supplier.tax_id if supplier else None,
            amount_before_tax=data.get('amount_before_tax'),
            tax_amount=data.get('tax_amount'),
            total_amount=data['total_amount'],
            amount=data['total_amount'],
            currency=data.get('currency', 'CNY'),
            file_url=data['file_url'],
            file_name=data.get('file_name'),
            file_type=data.get('file_type'),
            file_size=data.get('file_size'),
            remark=data.get('remark'),
            description=data.get('description'),
            status='pending',
            uploaded_at=datetime.utcnow()
        )

        # 标记PO已上传发票
        po.invoice_uploaded = True

        db.session.add(invoice)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '发票上传成功',
            'invoice': invoice.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'上传发票失败: {str(e)}'}), 500


@bp.route('/upload/monthly', methods=['POST', 'OPTIONS'])
def upload_monthly_invoice_by_employee():
    """
    员工上传月结发票（关联多个PO）

    请求体：
    {
        "supplier_id": 1,
        "period": "2025-11",
        "po_ids": [1, 2, 3],
        "invoice_number": "INV-202511-001",
        "invoice_code": "012345678901",
        "invoice_date": "2025-11-25",
        "amount_before_tax": 50000.00,
        "tax_amount": 6500.00,
        "total_amount": 56500.00,
        "file_url": "/storage/2025-11/caigou/invoices/xxx.pdf",
        "file_name": "11月月结发票.pdf",
        "file_type": "application/pdf",
        "file_size": "2.5MB",
        "remark": "2025年11月月结发票"
    }
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json() or {}
        user_id = int(request.headers.get('User-ID', 0))

        # 验证必填字段
        required_fields = ['supplier_id', 'period', 'po_ids', 'invoice_number', 'total_amount', 'file_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        supplier_id = data['supplier_id']
        period = data['period']
        po_ids = data['po_ids']

        if not isinstance(po_ids, list) or len(po_ids) == 0:
            return jsonify({'error': 'po_ids必须是非空数组'}), 400

        # 验证期间格式
        try:
            year, month = map(int, period.split('-'))
        except:
            return jsonify({'error': '期间格式错误，应为YYYY-MM'}), 400

        # 获取供应商
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        # 检查该期间是否已有月结发票
        existing = Invoice.query.filter_by(
            supplier_id=supplier_id,
            settlement_type='monthly',
            settlement_period=period
        ).first()
        if existing:
            return jsonify({
                'error': f'该供应商在{period}期间已存在月结发票',
                'invoice_id': existing.id
            }), 400

        # 检查发票号是否重复
        if Invoice.query.filter_by(invoice_number=data['invoice_number']).first():
            return jsonify({'error': '发票号已存在'}), 400

        # 验证所有PO属于该供应商且可开票
        pos = PurchaseOrder.query.filter(
            PurchaseOrder.id.in_(po_ids),
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.invoice_uploaded == False,
            PurchaseOrder.status.in_(['confirmed', 'received', 'completed'])
        ).all()

        if len(pos) != len(po_ids):
            found_ids = {po.id for po in pos}
            missing_ids = [pid for pid in po_ids if pid not in found_ids]
            return jsonify({
                'error': '部分PO不存在、不属于该供应商或已开票',
                'missing_ids': missing_ids
            }), 400

        # 计算PO总金额
        po_total = sum(float(po.total_price) if po.total_price else 0 for po in pos)

        # 创建月结发票
        invoice = Invoice(
            settlement_type='monthly',
            settlement_period=period,
            supplier_id=supplier_id,
            po_id=None,
            invoice_number=data['invoice_number'],
            invoice_code=data.get('invoice_code'),
            invoice_date=datetime.fromisoformat(data['invoice_date']) if data.get('invoice_date') else None,
            buyer_name=data.get('buyer_name'),
            buyer_tax_id=data.get('buyer_tax_id'),
            seller_name=supplier.company_name,
            seller_tax_id=supplier.tax_id,
            amount_before_tax=data.get('amount_before_tax'),
            tax_amount=data.get('tax_amount'),
            total_amount=data['total_amount'],
            amount=data['total_amount'],
            currency=data.get('currency', 'CNY'),
            file_url=data['file_url'],
            file_name=data.get('file_name'),
            file_type=data.get('file_type'),
            file_size=data.get('file_size'),
            remark=data.get('remark'),
            description=f'{period}月结发票，包含{len(pos)}个PO',
            status='pending',
            uploaded_at=datetime.utcnow()
        )

        db.session.add(invoice)
        db.session.flush()

        # 创建发票-PO关联
        for po in pos:
            link = InvoicePOLink(
                invoice_id=invoice.id,
                po_id=po.id,
                po_amount=po.total_price
            )
            db.session.add(link)
            po.invoice_uploaded = True

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'月结发票上传成功，包含{len(pos)}个PO',
            'invoice': invoice.to_dict(),
            'po_total': po_total
        }), 201

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'上传月结发票失败: {str(e)}'}), 500


@bp.route('/<int:invoice_id>', methods=['DELETE', 'OPTIONS'])
def delete_invoice(invoice_id):
    """
    删除发票（仅限待审批状态）
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return jsonify({'error': '发票不存在'}), 404

        if invoice.status != 'pending':
            return jsonify({'error': '只能删除待审批的发票'}), 400

        # 恢复PO的发票状态
        if invoice.settlement_type == 'monthly':
            # 月结发票：恢复所有关联PO
            for link in invoice.po_links:
                if link.po:
                    link.po.invoice_uploaded = False
        elif invoice.po:
            # 单次结算：恢复单个PO
            invoice.po.invoice_uploaded = False

        db.session.delete(invoice)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '发票已删除'
        }), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'删除发票失败: {str(e)}'}), 500


# ============ 供应商端API（保留兼容） ============

@bp.route('/supplier/pending-pos', methods=['GET', 'OPTIONS'])
def get_supplier_pending_pos():
    """
    获取供应商待上传发票的PO列表

    需要请求头：Supplier-ID (供应商ID)
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        supplier_id = request.headers.get('Supplier-ID')
        if not supplier_id:
            return jsonify({'error': '未授权'}), 401

        # 获取供应商信息
        supplier = Supplier.query.get(int(supplier_id))
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        now = datetime.utcnow()

        # 查询该供应商的待上传发票的PO
        # 只包括已确认(confirmed)和已收货(received)的订单
        pending_pos = PurchaseOrder.query.filter(
            and_(
                PurchaseOrder.supplier_id == supplier.id,
                PurchaseOrder.invoice_uploaded == False,
                PurchaseOrder.status.in_(['confirmed', 'received'])
            )
        ).order_by(PurchaseOrder.confirmed_at.desc()).all()

        result = []
        for po in pending_pos:
            days_remaining = (po.invoice_due_date - now).days if po.invoice_due_date else None
            is_overdue = days_remaining is not None and days_remaining < 0

            result.append({
                'po_id': po.id,
                'po_number': po.po_number,
                'total_price': float(po.total_price),
                'status': po.status,
                'confirmed_at': iso(po.confirmed_at),
                'invoice_due_date': iso(po.invoice_due_date),
                'days_remaining': days_remaining,
                'is_overdue': is_overdue,
                'urgency_level': 'overdue' if is_overdue else (
                    'critical' if days_remaining <= 2 else (
                        'warning' if days_remaining <= 5 else 'normal'
                    )
                ) if days_remaining is not None else 'normal'
            })

        return jsonify({
            'count': len(result),
            'pending_pos': result
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取待上传PO失败: {str(e)}'}), 500


@bp.route('/supplier/upload', methods=['POST', 'OPTIONS'])
def upload_invoice():
    """
    供应商上传发票

    请求体：
    {
        "po_id": 123,
        "invoice_number": "INV-20250101-001",
        "invoice_date": "2025-01-01",
        "amount": 5000.00,
        "currency": "CNY",
        "file_url": "/uploads/invoice_xxx.pdf",
        "file_name": "发票.pdf",
        "file_type": "application/pdf",
        "file_size": "1.5MB",
        "description": "备注"
    }
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        supplier_id = request.headers.get('Supplier-ID')
        if not supplier_id:
            return jsonify({'error': '未授权'}), 401

        # 获取供应商信息
        supplier = Supplier.query.get(int(supplier_id))
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        data = request.get_json() or {}

        # 验证必填字段
        required_fields = ['po_id', 'invoice_number', 'amount', 'file_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        # 验证PO
        po = PurchaseOrder.query.get(data['po_id'])
        if not po:
            return jsonify({'error': 'PO不存在'}), 404

        if po.supplier_id != supplier.id:
            return jsonify({'error': '无权为此PO上传发票'}), 403

        if po.invoice_uploaded:
            return jsonify({'error': '此PO已上传发票'}), 400

        # 检查发票号是否重复
        existing = Invoice.query.filter_by(invoice_number=data['invoice_number']).first()
        if existing:
            return jsonify({'error': '发票号已存在'}), 400

        # 创建发票记录
        invoice = Invoice(
            supplier_id=supplier.id,
            po_id=po.id,
            quote_id=po.quote_id,
            invoice_number=data['invoice_number'],
            invoice_date=datetime.fromisoformat(data['invoice_date']) if data.get('invoice_date') else None,
            amount=data['amount'],
            currency=data.get('currency', 'CNY'),
            file_url=data['file_url'],
            file_name=data.get('file_name'),
            file_type=data.get('file_type'),
            file_size=data.get('file_size'),
            description=data.get('description'),
            status='pending',
            uploaded_at=datetime.utcnow()
        )

        # 更新PO状态
        po.invoice_uploaded = True

        db.session.add(invoice)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '发票上传成功',
            'invoice': invoice.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'上传发票失败: {str(e)}'}), 500


@bp.route('/supplier/my-invoices', methods=['GET', 'OPTIONS'])
def get_supplier_invoices():
    """
    获取供应商自己的发票列表

    需要请求头：Supplier-ID (供应商ID)
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        supplier_id = request.headers.get('Supplier-ID')
        if not supplier_id:
            return jsonify({'error': '未授权'}), 401

        # 获取供应商信息
        supplier = Supplier.query.get(int(supplier_id))
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        status = request.args.get('status')

        query = Invoice.query.filter_by(supplier_id=supplier.id)

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(Invoice.created_at.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        invoices = []
        for inv in paginated.items:
            invoices.append({
                'id': inv.id,
                'invoice_number': inv.invoice_number,
                'po_id': inv.po_id,
                'po_number': inv.po.po_number if inv.po else None,
                'amount': float(inv.amount) if inv.amount else 0,
                'currency': inv.currency,
                'invoice_date': iso(inv.invoice_date),
                'file_url': inv.file_url,
                'file_name': inv.file_name,
                'status': inv.status,
                'approval_notes': inv.approval_notes,
                'created_at': iso(inv.created_at),
                'uploaded_at': iso(inv.uploaded_at),
                'approved_at': iso(inv.approved_at),
            })

        return jsonify({
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page,
            'per_page': per_page,
            'invoices': invoices
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取发票列表失败: {str(e)}'}), 500


@bp.route('/supplier/stats', methods=['GET', 'OPTIONS'])
def get_supplier_invoice_stats():
    """
    获取供应商发票统计

    需要请求头：Supplier-ID (供应商ID)
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        supplier_id = request.headers.get('Supplier-ID')
        if not supplier_id:
            return jsonify({'error': '未授权'}), 401

        # 获取供应商信息
        supplier = Supplier.query.get(int(supplier_id))
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        now = datetime.utcnow()

        # 发票统计
        total = Invoice.query.filter_by(supplier_id=supplier.id).count()
        pending = Invoice.query.filter_by(supplier_id=supplier.id, status='pending').count()
        approved = Invoice.query.filter_by(supplier_id=supplier.id, status='approved').count()
        rejected = Invoice.query.filter_by(supplier_id=supplier.id, status='rejected').count()

        # 超期未提交统计
        overdue_count = PurchaseOrder.query.filter(
            and_(
                PurchaseOrder.supplier_id == supplier.id,
                PurchaseOrder.invoice_due_date < now,
                PurchaseOrder.invoice_uploaded == False,
                PurchaseOrder.status != 'cancelled'
            )
        ).count()

        return jsonify({
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'overdue_count': overdue_count
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取统计失败: {str(e)}'}), 500


# ============ 月结相关API ============

@bp.route('/monthly/summary', methods=['GET', 'OPTIONS'])
def get_monthly_settlement_summary():
    """
    获取月结汇总信息（员工端）

    查询参数：
    - period: 结算周期（YYYY-MM），默认当月
    - supplier_id: 供应商ID（可选）

    返回按供应商分组的月结汇总
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        now = datetime.utcnow()
        period = request.args.get('period', now.strftime('%Y-%m'))
        supplier_id = request.args.get('supplier_id', type=int)

        # 解析期间
        try:
            year, month = map(int, period.split('-'))
        except:
            return jsonify({'error': '期间格式错误，应为YYYY-MM'}), 400

        # 查询月结供应商的PO
        query = db.session.query(
            Supplier.id.label('supplier_id'),
            Supplier.company_name,
            Supplier.code.label('supplier_code'),
            Supplier.settlement_type,
            Supplier.settlement_day,
            Supplier.payment_days,
            func.count(PurchaseOrder.id).label('po_count'),
            func.sum(PurchaseOrder.total_price).label('total_amount')
        ).join(
            PurchaseOrder, PurchaseOrder.supplier_id == Supplier.id
        ).filter(
            Supplier.settlement_type == 'monthly',
            extract('year', PurchaseOrder.confirmed_at) == year,
            extract('month', PurchaseOrder.confirmed_at) == month,
            PurchaseOrder.status.in_(['confirmed', 'received', 'completed']),
            PurchaseOrder.invoice_uploaded == False
        ).group_by(
            Supplier.id
        )

        if supplier_id:
            query = query.filter(Supplier.id == supplier_id)

        results = query.all()

        summaries = []
        for row in results:
            # 检查该供应商该期间是否已有月结发票
            existing_invoice = Invoice.query.filter_by(
                supplier_id=row.supplier_id,
                settlement_type='monthly',
                settlement_period=period
            ).first()

            summaries.append({
                'supplier_id': row.supplier_id,
                'supplier_name': row.company_name,
                'supplier_code': row.supplier_code,
                'settlement_day': row.settlement_day,
                'payment_days': row.payment_days,
                'period': period,
                'po_count': row.po_count,
                'total_amount': float(row.total_amount) if row.total_amount else 0,
                'has_invoice': existing_invoice is not None,
                'invoice_id': existing_invoice.id if existing_invoice else None,
                'invoice_status': existing_invoice.status if existing_invoice else None,
            })

        return jsonify({
            'period': period,
            'count': len(summaries),
            'summaries': summaries
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取月结汇总失败: {str(e)}'}), 500


@bp.route('/supplier/monthly/pending', methods=['GET', 'OPTIONS'])
def get_supplier_monthly_pending():
    """
    获取供应商待月结的PO列表

    需要请求头：Supplier-ID (供应商ID)

    查询参数：
    - period: 结算周期（YYYY-MM），默认当月

    仅对月结供应商返回数据
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        supplier_id = request.headers.get('Supplier-ID')
        if not supplier_id:
            return jsonify({'error': '未授权'}), 401

        supplier = Supplier.query.get(int(supplier_id))
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        # 检查是否为月结供应商
        if supplier.settlement_type != 'monthly':
            return jsonify({
                'error': '非月结供应商',
                'settlement_type': supplier.settlement_type
            }), 400

        now = datetime.utcnow()
        period = request.args.get('period', now.strftime('%Y-%m'))

        # 解析期间
        try:
            year, month = map(int, period.split('-'))
        except:
            return jsonify({'error': '期间格式错误，应为YYYY-MM'}), 400

        # 查询该期间内的待开票PO
        pending_pos = PurchaseOrder.query.filter(
            PurchaseOrder.supplier_id == supplier.id,
            extract('year', PurchaseOrder.confirmed_at) == year,
            extract('month', PurchaseOrder.confirmed_at) == month,
            PurchaseOrder.status.in_(['confirmed', 'received', 'completed']),
            PurchaseOrder.invoice_uploaded == False
        ).order_by(PurchaseOrder.confirmed_at.asc()).all()

        # 计算汇总
        total_amount = sum(float(po.total_price) if po.total_price else 0 for po in pending_pos)

        # 检查该期间是否已有月结发票
        existing_invoice = Invoice.query.filter_by(
            supplier_id=supplier.id,
            settlement_type='monthly',
            settlement_period=period
        ).first()

        result = []
        for po in pending_pos:
            result.append({
                'po_id': po.id,
                'po_number': po.po_number,
                'total_price': float(po.total_price) if po.total_price else 0,
                'status': po.status,
                'confirmed_at': iso(po.confirmed_at),
            })

        return jsonify({
            'period': period,
            'settlement_day': supplier.settlement_day,
            'payment_days': supplier.payment_days,
            'po_count': len(result),
            'total_amount': total_amount,
            'pending_pos': result,
            'has_invoice': existing_invoice is not None,
            'invoice_id': existing_invoice.id if existing_invoice else None,
            'invoice_status': existing_invoice.status if existing_invoice else None,
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取月结待开票PO失败: {str(e)}'}), 500


@bp.route('/supplier/monthly/upload', methods=['POST', 'OPTIONS'])
def upload_monthly_invoice():
    """
    供应商上传月结发票

    需要请求头：Supplier-ID (供应商ID)

    请求体：
    {
        "period": "2025-01",
        "po_ids": [1, 2, 3],  // 要包含在此发票中的PO ID列表
        "invoice_number": "INV-202501-001",
        "invoice_code": "012345678901",
        "invoice_date": "2025-01-25",
        "amount_before_tax": 10000.00,
        "tax_amount": 1300.00,
        "total_amount": 11300.00,
        "file_url": "/storage/2025-01/caigou/invoices/xxx.pdf",
        "file_name": "月结发票.pdf",
        "file_type": "application/pdf",
        "file_size": "2.5MB",
        "remark": "2025年1月月结发票"
    }
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        supplier_id = request.headers.get('Supplier-ID')
        if not supplier_id:
            return jsonify({'error': '未授权'}), 401

        supplier = Supplier.query.get(int(supplier_id))
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        # 检查是否为月结供应商
        if supplier.settlement_type != 'monthly':
            return jsonify({
                'error': '非月结供应商，请使用单次结算上传接口',
                'settlement_type': supplier.settlement_type
            }), 400

        data = request.get_json() or {}

        # 验证必填字段
        required_fields = ['period', 'po_ids', 'invoice_number', 'total_amount', 'file_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        period = data['period']
        po_ids = data['po_ids']

        if not isinstance(po_ids, list) or len(po_ids) == 0:
            return jsonify({'error': 'po_ids必须是非空数组'}), 400

        # 验证期间格式
        try:
            year, month = map(int, period.split('-'))
        except:
            return jsonify({'error': '期间格式错误，应为YYYY-MM'}), 400

        # 检查该期间是否已有月结发票
        existing = Invoice.query.filter_by(
            supplier_id=supplier.id,
            settlement_type='monthly',
            settlement_period=period
        ).first()
        if existing:
            return jsonify({
                'error': f'该期间({period})已存在月结发票',
                'invoice_id': existing.id
            }), 400

        # 检查发票号是否重复
        if Invoice.query.filter_by(invoice_number=data['invoice_number']).first():
            return jsonify({'error': '发票号已存在'}), 400

        # 验证所有PO属于该供应商且可开票
        pos = PurchaseOrder.query.filter(
            PurchaseOrder.id.in_(po_ids),
            PurchaseOrder.supplier_id == supplier.id,
            PurchaseOrder.invoice_uploaded == False,
            PurchaseOrder.status.in_(['confirmed', 'received', 'completed'])
        ).all()

        if len(pos) != len(po_ids):
            found_ids = {po.id for po in pos}
            missing_ids = [pid for pid in po_ids if pid not in found_ids]
            return jsonify({
                'error': '部分PO不存在、不属于您或已开票',
                'missing_ids': missing_ids
            }), 400

        # 计算PO总金额
        po_total = sum(float(po.total_price) if po.total_price else 0 for po in pos)

        # 创建月结发票
        invoice = Invoice(
            settlement_type='monthly',
            settlement_period=period,
            supplier_id=supplier.id,
            po_id=None,  # 月结发票不关联单个PO
            invoice_number=data['invoice_number'],
            invoice_code=data.get('invoice_code'),
            invoice_date=datetime.fromisoformat(data['invoice_date']) if data.get('invoice_date') else None,
            buyer_name=data.get('buyer_name'),
            buyer_tax_id=data.get('buyer_tax_id'),
            seller_name=supplier.company_name,
            seller_tax_id=supplier.tax_id,
            amount_before_tax=data.get('amount_before_tax'),
            tax_amount=data.get('tax_amount'),
            total_amount=data['total_amount'],
            amount=data['total_amount'],  # 兼容字段
            currency=data.get('currency', 'CNY'),
            file_url=data['file_url'],
            file_name=data.get('file_name'),
            file_type=data.get('file_type'),
            file_size=data.get('file_size'),
            remark=data.get('remark'),
            description=f'{period}月结发票，包含{len(pos)}个PO',
            status='pending',
            uploaded_at=datetime.utcnow()
        )

        db.session.add(invoice)
        db.session.flush()  # 获取invoice.id

        # 创建发票-PO关联
        for po in pos:
            link = InvoicePOLink(
                invoice_id=invoice.id,
                po_id=po.id,
                po_amount=po.total_price
            )
            db.session.add(link)

            # 标记PO已开票
            po.invoice_uploaded = True

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'月结发票上传成功，包含{len(pos)}个PO',
            'invoice': invoice.to_dict(),
            'po_total': po_total
        }), 201

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'上传月结发票失败: {str(e)}'}), 500


@bp.route('/monthly/<int:invoice_id>/pos', methods=['GET', 'OPTIONS'])
def get_monthly_invoice_pos(invoice_id):
    """
    获取月结发票关联的所有PO

    返回该发票包含的所有PO详情
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return jsonify({'error': '发票不存在'}), 404

        if invoice.settlement_type != 'monthly':
            return jsonify({'error': '非月结发票'}), 400

        links = InvoicePOLink.query.filter_by(invoice_id=invoice_id).all()

        pos = []
        for link in links:
            if link.po:
                pos.append({
                    'link_id': link.id,
                    'po_id': link.po_id,
                    'po_number': link.po.po_number,
                    'po_amount': float(link.po_amount) if link.po_amount else None,
                    'total_price': float(link.po.total_price) if link.po.total_price else 0,
                    'status': link.po.status,
                    'confirmed_at': iso(link.po.confirmed_at),
                })

        return jsonify({
            'invoice_id': invoice_id,
            'invoice_number': invoice.invoice_number,
            'settlement_period': invoice.settlement_period,
            'po_count': len(pos),
            'total_po_amount': sum(p['total_price'] for p in pos),
            'invoice_amount': float(invoice.total_amount) if invoice.total_amount else 0,
            'pos': pos
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取月结发票PO失败: {str(e)}'}), 500


@bp.route('/supplier/settlement-info', methods=['GET', 'OPTIONS'])
def get_supplier_settlement_info():
    """
    获取供应商结算信息

    需要请求头：Supplier-ID (供应商ID)

    返回供应商的结算方式配置和当前待处理情况
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        supplier_id = request.headers.get('Supplier-ID')
        if not supplier_id:
            return jsonify({'error': '未授权'}), 401

        supplier = Supplier.query.get(int(supplier_id))
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        now = datetime.utcnow()
        current_period = now.strftime('%Y-%m')

        result = {
            'supplier_id': supplier.id,
            'company_name': supplier.company_name,
            'settlement_type': supplier.settlement_type,
            'settlement_day': supplier.settlement_day,
            'payment_days': supplier.payment_days,
        }

        if supplier.settlement_type == 'monthly':
            # 月结供应商：查询当月待开票PO
            pending_count = PurchaseOrder.query.filter(
                PurchaseOrder.supplier_id == supplier.id,
                extract('year', PurchaseOrder.confirmed_at) == now.year,
                extract('month', PurchaseOrder.confirmed_at) == now.month,
                PurchaseOrder.status.in_(['confirmed', 'received', 'completed']),
                PurchaseOrder.invoice_uploaded == False
            ).count()

            pending_amount = db.session.query(
                func.sum(PurchaseOrder.total_price)
            ).filter(
                PurchaseOrder.supplier_id == supplier.id,
                extract('year', PurchaseOrder.confirmed_at) == now.year,
                extract('month', PurchaseOrder.confirmed_at) == now.month,
                PurchaseOrder.status.in_(['confirmed', 'received', 'completed']),
                PurchaseOrder.invoice_uploaded == False
            ).scalar() or 0

            # 检查是否已有当月发票
            current_invoice = Invoice.query.filter_by(
                supplier_id=supplier.id,
                settlement_type='monthly',
                settlement_period=current_period
            ).first()

            result.update({
                'current_period': current_period,
                'pending_po_count': pending_count,
                'pending_amount': float(pending_amount),
                'has_current_invoice': current_invoice is not None,
                'current_invoice_status': current_invoice.status if current_invoice else None,
            })
        else:
            # 单次结算供应商：查询待开票PO数量
            pending_count = PurchaseOrder.query.filter(
                PurchaseOrder.supplier_id == supplier.id,
                PurchaseOrder.invoice_uploaded == False,
                PurchaseOrder.status.in_(['confirmed', 'received'])
            ).count()

            result.update({
                'pending_po_count': pending_count,
            })

        return jsonify(result), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取结算信息失败: {str(e)}'}), 500


# ============ OCR 发票识别 ============

# PaddleOCR 脚本路径
PADDLE_OCR_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ocr_paddle.py')


def ocr_with_paddle(image_path):
    """
    通过调用外部脚本使用 PaddleOCR 识别图片中的文字
    返回识别出的所有文字（按位置排序）
    """
    try:
        # 使用全局 Python 运行 OCR 脚本
        result = subprocess.run(
            ['python', PADDLE_OCR_SCRIPT, image_path],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8'
        )

        if result.returncode != 0:
            print(f"PaddleOCR 脚本错误: {result.stderr}")
            return None

        # 解析 JSON 输出
        output = result.stdout.strip()
        if not output:
            return None

        data = json.loads(output)
        if data.get('success'):
            return data.get('text')
        else:
            print(f"PaddleOCR 识别失败: {data.get('error')}")
            return None

    except subprocess.TimeoutExpired:
        print("PaddleOCR 识别超时")
        return None
    except Exception as e:
        print(f"PaddleOCR 调用错误: {e}")
        traceback.print_exc()
        return None


@bp.route('/ocr', methods=['POST', 'OPTIONS'])
def ocr_invoice():
    """
    使用 PaddleOCR + Ollama 识别发票信息

    流程：
    1. PaddleOCR 精确识别图片中的文字
    2. Ollama 从识别的文字中提取结构化信息

    请求：multipart/form-data
    - file: 发票图片文件 (jpg/png)

    返回识别出的发票信息
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': '请上传发票图片'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '请选择文件'}), 400

        # 检查文件类型
        allowed_extensions = {'jpg', 'jpeg', 'png'}
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            return jsonify({'error': f'不支持的文件格式，仅支持: {", ".join(allowed_extensions)}'}), 400

        # 保存临时文件
        with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
            file.save(tmp)
            temp_image_path = tmp.name

        try:
            # 第一步：使用 PaddleOCR 识别文字
            print(f"[OCR] 开始 PaddleOCR 识别: {temp_image_path}")
            ocr_text = ocr_with_paddle(temp_image_path)

            if not ocr_text:
                return jsonify({
                    'success': False,
                    'error': 'PaddleOCR 识别失败，请确保图片清晰'
                }), 200

            print(f"[OCR] PaddleOCR 识别结果:\n{ocr_text[:500]}...")

            # 第二步：使用 Ollama 提取结构化信息
            prompt = f"""请从以下发票OCR识别文本中提取结构化信息，以JSON格式返回。

OCR识别文本：
---
{ocr_text}
---

请提取以下字段（如果找不到则设为null）：
- invoice_number: 发票号码（通常是8位数字）
- invoice_code: 发票代码（通常是10-12位数字）
- invoice_date: 开票日期（格式：YYYY-MM-DD）
- buyer_name: 购买方名称
- buyer_tax_id: 购买方纳税人识别号/统一社会信用代码
- seller_name: 销售方名称
- seller_tax_id: 销售方纳税人识别号/统一社会信用代码
- amount_before_tax: 不含税金额（数字）
- tax_amount: 税额（数字）
- total_amount: 价税合计/小写金额（数字，注意识别¥符号后的数字）
- tax_rate: 税率（如"13"表示13%）
- drawer: 开票人
- remark: 备注

注意：
1. 金额字段只返回数字，不要包含¥符号或逗号
2. 价税合计优先取"小写"后面的金额
3. 日期格式统一为 YYYY-MM-DD

只返回JSON，不要有其他文字。示例：
{{"invoice_number": "12345678", "invoice_code": "1234567890", "invoice_date": "2025-01-15", "buyer_name": "某公司", "buyer_tax_id": "91440300XXXXXXXX", "seller_name": "销售方", "seller_tax_id": "91441900XXXXXXXX", "amount_before_tax": 14867.26, "tax_amount": 1932.74, "total_amount": 16800.00, "tax_rate": "13", "drawer": "张三", "remark": ""}}"""

            # 调用 Ollama
            ollama_request = {
                "model": "qwen3:8b",  # 使用文本模型，不需要视觉模型
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }

            # 将请求写入临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(ollama_request, f, ensure_ascii=False)
                ollama_temp_file = f.name

            try:
                # 转换 Windows 路径为 WSL 路径
                wsl_path = ollama_temp_file.replace('C:', '/mnt/c').replace('\\', '/')

                # 调用 WSL 中的 Ollama
                cmd = f'wsl curl -s -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" -d @"{wsl_path}"'

                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60  # 1分钟超时
                )

                if result.returncode != 0:
                    print(f"Ollama调用失败: {result.stderr}")
                    return jsonify({
                        'success': False,
                        'error': 'AI提取失败',
                        'ocr_text': ocr_text
                    }), 200

                # 解析 Ollama 响应
                response_text = result.stdout.strip()
                if not response_text:
                    return jsonify({
                        'success': False,
                        'error': 'AI无响应',
                        'ocr_text': ocr_text
                    }), 200

                ollama_response = json.loads(response_text)
                generated_text = ollama_response.get('response', '')

                print(f"[OCR] Ollama 响应:\n{generated_text[:500]}...")

                # 从生成的文本中提取 JSON
                invoice_data = extract_json_from_text(generated_text)

                if not invoice_data:
                    return jsonify({
                        'success': False,
                        'error': '无法解析发票信息',
                        'ocr_text': ocr_text,
                        'raw_response': generated_text
                    }), 200

                return jsonify({
                    'success': True,
                    'data': invoice_data,
                    'ocr_text': ocr_text  # 也返回原始OCR文本供参考
                }), 200

            finally:
                try:
                    os.unlink(ollama_temp_file)
                except:
                    pass

        finally:
            # 清理图片临时文件
            try:
                os.unlink(temp_image_path)
            except:
                pass

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'OCR识别超时，请重试'}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'OCR识别失败: {str(e)}'}), 500


def extract_json_from_text(text):
    """
    从文本中提取 JSON 对象
    """
    if not text:
        return None

    # 移除可能的 markdown 代码块标记
    text = re.sub(r'^```json\s*', '', text.strip())
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    # 移除 <think> 标签内容
    text = re.sub(r'<think>[\s\S]*?</think>', '', text)
    text = text.strip()

    # 尝试直接解析
    try:
        return json.loads(text)
    except:
        pass

    # 尝试找到 JSON 对象
    json_match = re.search(r'\{[^{}]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass

    # 尝试找到更复杂的 JSON（可能包含嵌套）
    json_match = re.search(r'\{[\s\S]*?\}(?=\s*$|\s*\n)', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass

    return None
