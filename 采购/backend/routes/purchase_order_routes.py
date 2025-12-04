# -*- coding: utf-8 -*-
import json
"""
采购订单管理路由
Purchase Order Management Routes
"""
from flask import Blueprint, jsonify, request
from models.purchase_order import PurchaseOrder
from models.supplier import Supplier
from models.rfq import RFQ
from extensions import db
from sqlalchemy import desc
import sys
import os

# Add shared module to path for JWT verification
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '..'))
from shared.auth import verify_token

URL_PREFIX = '/api/v1/purchase-orders'
bp = Blueprint('purchase_order', __name__)


@bp.before_request
def check_auth():
    """JWT认证检查"""
    # OPTIONS 请求跳过认证（CORS预检）
    if request.method == 'OPTIONS':
        return None

    # 检查 Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if payload:
            request.current_user_id = payload.get('user_id')
            request.current_user_role = payload.get('role')
            return None

    # 回退检查 User-ID header（兼容旧方式）
    user_id = request.headers.get('User-ID')
    if user_id:
        request.current_user_id = user_id
        request.current_user_role = request.headers.get('User-Role')
        return None

    return jsonify({"error": "未授权：请先登录"}), 401

@bp.route('', methods=['GET', 'OPTIONS'])
def list_purchase_orders():
    """
    获取采购订单列表

    GET /api/v1/purchase-orders?page=1&per_page=20&status=created&supplier_id=5

    Query Parameters:
        - page: 页码 (default: 1)
        - per_page: 每页数量 (default: 20)
        - status: 状态筛选 (created/confirmed/received/completed/cancelled)
        - supplier_id: 供应商ID筛选
        - search: 搜索PO号或供应商名称

    Returns:
        {
            "items": [
                {
                    "id": 1,
                    "po_number": "PO-20251103-00001",
                    "supplier_id": 5,
                    "supplier_name": "XX供应商",
                    "rfq_id": 10,
                    "quote_id": 25,
                    "total_price": 15000.00,
                    "lead_time": 7,
                    "status": "created",
                    "invoice_due_date": "2025-11-10T00:00:00",
                    "invoice_uploaded": false,
                    "created_at": "2025-11-03T10:00:00",
                    "confirmed_at": null
                }
            ],
            "total": 100,
            "page": 1,
            "per_page": 20,
            "pages": 5
        }
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '').strip()
        supplier_id = request.args.get('supplier_id', type=int)
        search = request.args.get('search', '').strip()

        # 获取用户角色
        user_role = request.headers.get('User-Role', '')
        user_supplier_id = request.args.get('user_supplier_id', type=int)
        
        # 构建查询
        query = PurchaseOrder.query

        # 供应商只能看到已确认的订单
        is_supplier = (user_role == 'supplier')
        if is_supplier:
            query = query.filter(PurchaseOrder.status == 'confirmed')
            # 供应商只能看到自己的订单
            if user_supplier_id:
                query = query.filter(PurchaseOrder.supplier_id == user_supplier_id)

        # 状态筛选
        if status and not is_supplier:  # 供应商不能自定义状态筛选
            query = query.filter(PurchaseOrder.status == status)

        # 供应商筛选（非供应商用户）
        if supplier_id and not is_supplier:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)

        # 搜索
        if search:
            query = query.filter(
                db.or_(
                    PurchaseOrder.po_number.like(f'%{search}%'),
                    PurchaseOrder.supplier_name.like(f'%{search}%')
                )
            )

        # 按创建时间倒序
        query = query.order_by(desc(PurchaseOrder.created_at))

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        items = []
        for po in pagination.items:
            items.append({
                'id': po.id,
                'po_number': po.po_number,
                'supplier_id': po.supplier_id,
                'supplier_name': po.supplier_name,
                'rfq_id': po.rfq_id,
                'quote_id': po.quote_id,
                'total_price': float(po.total_price) if po.total_price else 0,
                'lead_time': po.lead_time,
                'status': po.status,
                'invoice_due_date': po.invoice_due_date.isoformat() if po.invoice_due_date else None,
                'invoice_uploaded': po.invoice_uploaded,
                'created_at': po.created_at.isoformat() if po.created_at else None,
                'confirmed_at': po.confirmed_at.isoformat() if po.confirmed_at else None
            })

        return jsonify({
            'items': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:po_id>', methods=['GET', 'OPTIONS'])
def get_purchase_order_detail(po_id):
    """
    获取采购订单详情

    GET /api/v1/purchase-orders/<po_id>

    Returns:
        {
            "id": 1,
            "po_number": "PO-20251103-00001",
            "supplier_id": 5,
            "supplier_name": "XX供应商",
            "supplier": {
                "id": 5,
                "company_name": "XX供应商",
                "contact_name": "张三",
                "contact_phone": "13800138000"
            },
            "rfq_id": 10,
            "rfq": {
                "id": 10,
                "pr_id": 100,
                "status": "po_created"
            },
            "quote_id": 25,
            "quote_data": {
                "item_name": "螺丝刀",
                "quantity": 100,
                "unit_price": 150.00
            },
            "total_price": 15000.00,
            "lead_time": 7,
            "status": "created",
            "invoice_due_date": "2025-11-10T00:00:00",
            "invoice_uploaded": false,
            "created_at": "2025-11-03T10:00:00",
            "confirmed_at": null,
            "invoices": [],
            "receipts": []
        }
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        po = PurchaseOrder.query.get(po_id)
        if not po:
            return jsonify({'error': f'采购订单 #{po_id} 不存在'}), 404

        # 获取供应商信息
        supplier = None
        if po.supplier_id:
            s = Supplier.query.get(po.supplier_id)
            if s:
                supplier = {
                    'id': s.id,
                    'company_name': s.company_name,
                    'contact_name': s.contact_name,
                    'contact_phone': s.contact_phone,
                    'contact_email': s.contact_email
                }

        # 获取RFQ信息
        rfq = None
        if po.rfq_id:
            r = RFQ.query.get(po.rfq_id)
            if r:
                rfq = {
                    'id': r.id,
                    'pr_id': r.pr_id,
                    'status': r.status
                }

        # 获取发票
        invoices = []
        if hasattr(po, 'invoices'):
            for inv in po.invoices:
                invoices.append({
                    'id': inv.id,
                    'invoice_number': inv.invoice_number,
                    'amount': float(inv.amount) if inv.amount else 0,
                    'status': inv.status,
                    'created_at': inv.created_at.isoformat() if inv.created_at else None
                })

        # 获取收货回执
        receipts = []
        if hasattr(po, 'receipts'):
            for rec in po.receipts:
                receipts.append({
                    'id': rec.id,
                    'receipt_number': rec.receipt_number,
                    'quality_status': rec.quality_status,
                    'status': rec.status,
                    'received_date': rec.received_date.isoformat() if rec.received_date else None
                })

        import json
        quote_data = None
        if po.quote_data:
            try:
                quote_data = json.loads(po.quote_data) if isinstance(po.quote_data, str) else po.quote_data
            except:
                quote_data = str(po.quote_data)

        return jsonify({
            'id': po.id,
            'po_number': po.po_number,
            'supplier_id': po.supplier_id,
            'supplier_name': po.supplier_name,
            'supplier': supplier,
            'rfq_id': po.rfq_id,
            'rfq': rfq,
            'quote_id': po.quote_id,
            'quote_data': quote_data,
            'total_price': float(po.total_price) if po.total_price else 0,
            'lead_time': po.lead_time,
            'status': po.status,
            'invoice_due_date': po.invoice_due_date.isoformat() if po.invoice_due_date else None,
            'invoice_uploaded': po.invoice_uploaded,
            'created_at': po.created_at.isoformat() if po.created_at else None,
            'confirmed_at': po.confirmed_at.isoformat() if po.confirmed_at else None,
            'admin_confirmed_by': po.admin_confirmed_by,
            'admin_confirmed_at': po.admin_confirmed_at.isoformat() if po.admin_confirmed_at else None,
            'super_admin_confirmed_by': po.super_admin_confirmed_by,
            'super_admin_confirmed_at': po.super_admin_confirmed_at.isoformat() if po.super_admin_confirmed_at else None,
            'confirmation_note': po.confirmation_note,
            'invoices': invoices,
            'receipts': receipts
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/stats', methods=['GET', 'OPTIONS'])
def get_purchase_order_stats():
    """
    获取采购订单统计数据

    GET /api/v1/purchase-orders/stats

    Returns:
        {
            "total": 100,
            "by_status": {
                "created": 30,
                "confirmed": 20,
                "received": 40,
                "completed": 10,
                "cancelled": 0
            },
            "invoice_pending": 15,
            "invoice_overdue": 5
        }
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        from datetime import datetime

        total = PurchaseOrder.query.count()

        # 按状态统计
        by_status = {}
        for status in ['created', 'confirmed', 'received', 'completed', 'cancelled']:
            count = PurchaseOrder.query.filter_by(status=status).count()
            by_status[status] = count

        # 待上传发票数量
        invoice_pending = PurchaseOrder.query.filter_by(invoice_uploaded=False).filter(
            PurchaseOrder.invoice_due_date.isnot(None)
        ).count()

        # 发票逾期数量
        now = datetime.utcnow()
        invoice_overdue = PurchaseOrder.query.filter_by(invoice_uploaded=False).filter(
            PurchaseOrder.invoice_due_date < now
        ).count()

        return jsonify({
            'total': total,
            'by_status': by_status,
            'invoice_pending': invoice_pending,
            'invoice_overdue': invoice_overdue
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/pending-confirmation', methods=['GET', 'OPTIONS'])
def get_pending_confirmation():
    """获取待确认的采购订单列表"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        user_role = request.headers.get('User-Role')
        
        if user_role not in ['admin', 'super_admin']:
            return jsonify({'error': '权限不足'}), 403
        
        query = PurchaseOrder.query
        
        if user_role == 'admin':
            query = query.filter(PurchaseOrder.status == 'pending_admin_confirmation')
        elif user_role == 'super_admin':
            query = query.filter(
                db.or_(
                    PurchaseOrder.status == 'pending_admin_confirmation',
                    PurchaseOrder.status == 'pending_super_admin_confirmation'
                )
            )
        
        query = query.order_by(desc(PurchaseOrder.created_at))
        pos = query.all()
        
        items = []
        for po in pos:
            # Parse quote_data to get items
            quote_items = []
            if po.quote_data:
                try:
                    quote_data_parsed = json.loads(po.quote_data) if isinstance(po.quote_data, str) else po.quote_data
                    quote_items = quote_data_parsed.get('items', [])
                except:
                    pass

            # Get all participants who quoted on this RFQ
            participants = []
            if po.rfq_id:
                from models.supplier_quote import SupplierQuote
                all_quotes = SupplierQuote.query.filter_by(rfq_id=po.rfq_id, status='awarded').all()

                # Group by supplier
                supplier_totals = {}
                for q in all_quotes:
                    sid = q.supplier_id
                    if sid not in supplier_totals:
                        supplier_totals[sid] = {
                            'supplier_id': sid,
                            'name': q.supplier.company_name if q.supplier else f'Supplier #{sid}',
                            'total_price': 0.0,
                            'is_winner': (sid == po.supplier_id)
                        }
                    supplier_totals[sid]['total_price'] += float(q.total_price or 0)

                participants = sorted(supplier_totals.values(), key=lambda x: x['total_price'])

            items.append({
                'id': po.id,
                'po_number': po.po_number,
                'supplier_id': po.supplier_id,
                'supplier_name': po.supplier_name,
                'total_price': float(po.total_price),
                'lead_time': po.lead_time,
                'status': po.status,
                'admin_confirmed_by': po.admin_confirmed_by,
                'admin_confirmed_at': po.admin_confirmed_at.isoformat() if po.admin_confirmed_at else None,
                'super_admin_confirmed_by': po.super_admin_confirmed_by,
                'super_admin_confirmed_at': po.super_admin_confirmed_at.isoformat() if po.super_admin_confirmed_at else None,
                'created_at': po.created_at.isoformat(),
                'items': quote_items,
                'participants': participants,
            })
        
        return jsonify({'items': items, 'total': len(items)}), 200
    
    except Exception as e:
        print(f'获取待确认订单列表失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'获取失败: {str(e)}'}), 500


@bp.route('/<int:po_id>/admin-confirm', methods=['POST', 'OPTIONS'])
def admin_confirm_po(po_id):
    """管理员确认采购订单"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        from datetime import datetime
        
        user_id = request.headers.get('User-ID')
        user_role = request.headers.get('User-Role')
        
        if user_role not in ['admin', 'super_admin']:
            return jsonify({'error': '权限不足'}), 403
        
        po = PurchaseOrder.query.get(po_id)
        if not po:
            return jsonify({'error': '采购订单不存在'}), 404
        
        if po.status != 'pending_admin_confirmation':
            return jsonify({'error': f'订单状态不正确：{po.status}'}), 400
        
        data = request.get_json() or {}
        note = data.get('note', '')
        
        po.status = 'pending_super_admin_confirmation'
        po.admin_confirmed_by = int(user_id) if user_id else None
        po.admin_confirmed_at = datetime.utcnow()
        if note:
            po.confirmation_note = note
        
        db.session.commit()
        
        return jsonify({
            'message': '管理员确认成功',
            'po_id': po.id,
            'po_number': po.po_number,
            'status': po.status
        }), 200
    
    except Exception as e:
        db.session.rollback()
        print(f'管理员确认失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'确认失败: {str(e)}'}), 500


@bp.route('/<int:po_id>/super-admin-confirm', methods=['POST', 'OPTIONS'])
def super_admin_confirm_po(po_id):
    """超级管理员最终确认采购订单"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        from datetime import datetime, timedelta
        
        user_id = request.headers.get('User-ID')
        user_role = request.headers.get('User-Role')
        
        if user_role != 'super_admin':
            return jsonify({'error': '权限不足'}), 403
        
        po = PurchaseOrder.query.get(po_id)
        if not po:
            return jsonify({'error': '采购订单不存在'}), 404
        
        if po.status != 'pending_super_admin_confirmation':
            return jsonify({'error': f'订单状态不正确：{po.status}'}), 400
        
        data = request.get_json() or {}
        note = data.get('note', '')
        
        po.status = 'confirmed'
        po.super_admin_confirmed_by = int(user_id) if user_id else None
        po.super_admin_confirmed_at = datetime.utcnow()
        po.confirmed_at = datetime.utcnow()
        po.invoice_due_date = datetime.utcnow() + timedelta(days=7)
        po.invoice_due_date = datetime.utcnow() + timedelta(days=7)
        if note:
            if po.confirmation_note:
                po.confirmation_note += '\n超管：' + note
            else:
                po.confirmation_note = '超管：' + note
        
        db.session.commit()
        
        return jsonify({
            'message': '超管最终确认成功',
            'po_id': po.id,
            'po_number': po.po_number,
            'status': po.status,
            'invoice_due_date': po.invoice_due_date.isoformat() if po.invoice_due_date else None
        }), 200
    
    except Exception as e:
        db.session.rollback()
        print(f'超管确认失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'确认失败: {str(e)}'}), 500


@bp.route('/<int:po_id>/detail-with-quotes', methods=['GET', 'OPTIONS'])
def get_po_detail_with_quotes(po_id):
    """
    获取PO详细信息，包含该RFQ的所有供应商报价对比
    用于管理审批中心查看
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        from models.rfq import RFQ
        from models.supplier_quote import SupplierQuote
        
        # 获取PO
        po = PurchaseOrder.query.get(po_id)
        if not po:
            return jsonify({'error': 'PO不存在'}), 404
        
        # 获取关联的RFQ
        rfq = RFQ.query.get(po.rfq_id) if po.rfq_id else None
        if not rfq:
            return jsonify({'error': 'RFQ不存在'}), 404
        
        # 获取该RFQ的所有报价
        all_quotes = SupplierQuote.query.filter_by(rfq_id=po.rfq_id).all()
        
        # 格式化报价列表
        quotes_list = []
        for quote in all_quotes:
            quotes_list.append({
                'id': quote.id,
                'supplier_id': quote.supplier_id,
                'supplier_name': quote.supplier.company_name if quote.supplier else quote.supplier_name,
                'total_price': float(quote.total_price) if quote.total_price else 0,
                'lead_time': quote.lead_time,
                'status': quote.status,
                'is_selected': quote.id == po.quote_id,  # 是否为选中的报价
                'submitted_at': quote.updated_at.isoformat() if quote.updated_at else None,
                'quote_items': []  # 可以添加报价明细
            })
        
        # 按价格排序
        quotes_list.sort(key=lambda x: x['total_price'])
        
        # PO基本信息
        po_info = {
            'id': po.id,
            'po_number': po.po_number,
            'supplier_id': po.supplier_id,
            'supplier_name': po.supplier_name,
            'total_price': float(po.total_price),
            'lead_time': po.lead_time,
            'status': po.status,
            'created_at': po.created_at.isoformat(),
            'admin_confirmed_by': po.admin_confirmed_by,
            'admin_confirmed_at': po.admin_confirmed_at.isoformat() if po.admin_confirmed_at else None,
            'super_admin_confirmed_by': po.super_admin_confirmed_by,
            'super_admin_confirmed_at': po.super_admin_confirmed_at.isoformat() if po.super_admin_confirmed_at else None,
            'confirmation_note': po.confirmation_note,
        }
        
        # RFQ信息
        rfq_info = {
            'id': rfq.id,
            'rfq_number': getattr(rfq, 'rfq_number', f'RFQ-{rfq.id}'),
            'pr_number': rfq.pr.pr_number if rfq.pr else None,
            'created_at': rfq.created_at.isoformat() if rfq.created_at else None,
        }
        
        return jsonify({
            'po': po_info,
            'rfq': rfq_info,
            'all_quotes': quotes_list,
            'total_quotes': len(quotes_list),
        }), 200
    
    except Exception as e:
        print(f'获取PO详情失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'获取失败: {str(e)}'}), 500

