# routes/supplier_admin/invoice_routes.py
# 供应商管理系统 - 发票路由模块
# -*- coding: utf-8 -*-
from flask import Blueprint, request
from datetime import datetime
from extensions import db
from models.invoice import Invoice
from sqlalchemy import desc
import logging
import traceback

from .utils import (
    error_response, success_response,
    handle_db_operation, validate_json_data, check_admin_permission
)

logger = logging.getLogger(__name__)

bp_invoice = Blueprint(
    "supplier_admin_invoice",
    __name__,
    url_prefix="/api/v1/suppliers/admin"
)


# ==============================
# OPTIONS 预检处理
# ==============================
@bp_invoice.route("/invoices", methods=["OPTIONS"])
@bp_invoice.route("/invoices/<int:invoice_id>", methods=["OPTIONS"])
def handle_options():
    """处理 CORS 预检请求"""
    from .utils import make_response
    resp = make_response()
    return resp, 204


# ==============================
# 发票管理接口
# ==============================

@bp_invoice.route('/invoices', methods=['GET'])
@handle_db_operation("获取所有发票")
def list_all_invoices():
    """
    GET /api/v1/suppliers/admin/invoices
    获取所有供应商的发票（用于审批）
    
    查询参数：
    - page: 页码
    - per_page: 每页数量
    - status: 状态过滤 (pending/approved/rejected)
    - supplier_id: 按供应商过滤
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', None)
        supplier_id = request.args.get('supplier_id', None, type=int)
        
        query = Invoice.query
        
        if status:
            query = query.filter_by(status=status)
        
        if supplier_id:
            query = query.filter_by(supplier_id=supplier_id)
        
        query = query.order_by(desc(Invoice.created_at))
        paginated = query.paginate(page=page, per_page=per_page)
        
        invoices = []
        for inv in paginated.items:
            invoice_dict = {
                "id": inv.id,
                "supplier_id": inv.supplier_id,
                "invoice_number": inv.invoice_number or '',
                "amount": str(inv.amount) if inv.amount else '',
                "currency": inv.currency or '',
                "status": inv.status or '',
                "created_at": inv.created_at.isoformat() if inv.created_at else '',
                "approved_at": inv.approved_at.isoformat() if inv.approved_at else '',
            }
            invoices.append(invoice_dict)
        
        return success_response({
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page,
            "per_page": per_page,
            "invoices": invoices
        })
    
    except Exception as e:
        logger.error(f"❌ 获取发票列表错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("获取发票列表失败", 500)


@bp_invoice.route('/invoices/<int:invoice_id>', methods=['PUT'])
@handle_db_operation("审批发票")
def approve_invoice(invoice_id):
    """
    PUT /api/v1/suppliers/admin/invoices/{invoice_id}
    审批发票（批准或拒绝）
    
    请求体：
    {
        "status": "approved" 或 "rejected",
        "approval_notes": "审批意见（可选）"
    }
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err
    
    data, err = validate_json_data(required_fields=['status'])
    if err:
        return err
    
    try:
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return error_response("发票不存在", 404)
        
        status = data.get('status')
        if status not in ['approved', 'rejected']:
            return error_response("发票状态只能是 approved 或 rejected", 400)
        
        invoice.status = status
        invoice.approval_notes = data.get('approval_notes', '')
        invoice.approved_at = datetime.now()
        invoice.approved_by = int(request.headers.get('User-ID', 0))
        
        db.session.commit()
        
        logger.info(f"✅ 发票 {invoice.invoice_number} 已被 {status}")
        
        return success_response(message=f"发票已被 {'批准' if status == 'approved' else '拒绝'}")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 审批发票错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("审批发票失败", 500)