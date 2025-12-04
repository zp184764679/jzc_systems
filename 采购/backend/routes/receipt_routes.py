# routes/receipt_routes.py
# -*- coding: utf-8 -*-
"""
收货回执管理路由
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models.receipt import Receipt
from models.purchase_order import PurchaseOrder
from models.invoice import Invoice
from datetime import datetime
import traceback
import json

URL_PREFIX = '/api/v1/receipts'

bp = Blueprint('receipt', __name__)


@bp.before_request
def handle_preflight():
    """处理CORS预检请求"""
    if request.method == 'OPTIONS':
        return '', 200


def iso(dt):
    """日期序列化"""
    return dt.isoformat(timespec='seconds') if dt else None


@bp.route('', methods=['POST', 'OPTIONS'])
def create_receipt():
    """
    创建收货回执

    请求体：
    {
        "po_id": 123,
        "received_date": "2025-01-10",
        "quality_status": "qualified",  // qualified/defective/rejected
        "quantity_received": 100,
        "notes": "货物完好",
        "photos": ["url1", "url2"]  // 可选
    }
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        user_id = request.headers.get('User-ID')
        if not user_id:
            return jsonify({'error': '未授权'}), 401

        data = request.get_json() or {}

        # 验证必填字段
        required_fields = ['po_id', 'received_date', 'quality_status']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        # 验证PO
        po = PurchaseOrder.query.get(data['po_id'])
        if not po:
            return jsonify({'error': 'PO不存在'}), 404

        # 检查是否已创建回执
        existing = Receipt.query.filter_by(po_id=po.id).first()
        if existing:
            return jsonify({'error': '此PO已创建收货回执'}), 400

        # 验证质量状态
        valid_statuses = ['qualified', 'defective', 'rejected']
        if data['quality_status'] not in valid_statuses:
            return jsonify({'error': f'quality_status必须是: {", ".join(valid_statuses)}'}), 400

        # 处理照片
        photos = data.get('photos', [])
        photos_json = json.dumps(photos) if photos else None

        # 创建收货回执
        receipt = Receipt(
            receipt_number=Receipt.generate_receipt_number(),
            po_id=po.id,
            receiver_id=int(user_id),
            received_date=datetime.fromisoformat(data['received_date']),
            quality_status=data['quality_status'],
            quantity_received=data.get('quantity_received'),
            notes=data.get('notes'),
            photos=photos_json,
            status='confirmed',
            created_by=int(user_id)
        )

        # 更新PO状态为已收货
        po.status = 'received'

        db.session.add(receipt)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '收货回执创建成功',
            'receipt': receipt.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'创建收货回执失败: {str(e)}'}), 500


@bp.route('', methods=['GET', 'OPTIONS'])
def get_receipts():
    """
    获取收货回执列表

    查询参数：
    - page: 页码
    - per_page: 每页数量
    - status: 状态筛选
    - quality_status: 质量状态筛选
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        status = request.args.get('status')
        quality_status = request.args.get('quality_status')

        query = Receipt.query

        if status:
            query = query.filter_by(status=status)
        if quality_status:
            query = query.filter_by(quality_status=quality_status)

        query = query.order_by(Receipt.received_date.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        receipts = []
        for receipt in paginated.items:
            receipt_dict = {
                'id': receipt.id,
                'receipt_number': receipt.receipt_number,
                'po_id': receipt.po_id,
                'po_number': receipt.po.po_number if receipt.po else None,
                'supplier_name': receipt.po.supplier_name if receipt.po else None,
                'receiver_id': receipt.receiver_id,
                'receiver_name': receipt.receiver.realname if receipt.receiver else None,
                'received_date': iso(receipt.received_date),
                'quality_status': receipt.quality_status,
                'quantity_received': receipt.quantity_received,
                'notes': receipt.notes,
                'photos': json.loads(receipt.photos) if receipt.photos else [],
                'status': receipt.status,
                'created_at': iso(receipt.created_at),
            }
            receipts.append(receipt_dict)

        return jsonify({
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page,
            'per_page': per_page,
            'receipts': receipts
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取收货回执列表失败: {str(e)}'}), 500


@bp.route('/<int:receipt_id>', methods=['GET', 'OPTIONS'])
def get_receipt_detail(receipt_id):
    """获取收货回执详情"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        receipt = Receipt.query.get(receipt_id)
        if not receipt:
            return jsonify({'error': '收货回执不存在'}), 404

        receipt_dict = receipt.to_dict()

        # 添加照片列表
        if receipt.photos:
            receipt_dict['photos'] = json.loads(receipt.photos)
        else:
            receipt_dict['photos'] = []

        return jsonify(receipt_dict), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取收货回执详情失败: {str(e)}'}), 500


@bp.route('/<int:receipt_id>', methods=['PUT', 'OPTIONS'])
def update_receipt(receipt_id):
    """
    更新收货回执

    请求体：
    {
        "quality_status": "defective",
        "notes": "部分货物有损坏",
        "status": "disputed"
    }
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        user_id = request.headers.get('User-ID')
        if not user_id:
            return jsonify({'error': '未授权'}), 401

        receipt = Receipt.query.get(receipt_id)
        if not receipt:
            return jsonify({'error': '收货回执不存在'}), 404

        data = request.get_json() or {}

        # 更新字段
        if 'quality_status' in data:
            valid_statuses = ['qualified', 'defective', 'rejected']
            if data['quality_status'] not in valid_statuses:
                return jsonify({'error': f'quality_status必须是: {", ".join(valid_statuses)}'}), 400
            receipt.quality_status = data['quality_status']

        if 'quantity_received' in data:
            receipt.quantity_received = data['quantity_received']

        if 'notes' in data:
            receipt.notes = data['notes']

        if 'status' in data:
            valid_statuses = ['confirmed', 'disputed']
            if data['status'] not in valid_statuses:
                return jsonify({'error': f'status必须是: {", ".join(valid_statuses)}'}), 400
            receipt.status = data['status']

        if 'photos' in data:
            photos = data['photos']
            receipt.photos = json.dumps(photos) if photos else None

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '收货回执更新成功',
            'receipt': receipt.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': f'更新收货回执失败: {str(e)}'}), 500


@bp.route('/stats', methods=['GET', 'OPTIONS'])
def get_receipt_stats():
    """
    获取收货回执统计

    返回：
    - total: 总数
    - qualified: 合格数
    - defective: 有缺陷数
    - rejected: 拒收数
    - disputed: 有争议数
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        total = Receipt.query.count()
        qualified = Receipt.query.filter_by(quality_status='qualified').count()
        defective = Receipt.query.filter_by(quality_status='defective').count()
        rejected = Receipt.query.filter_by(quality_status='rejected').count()
        disputed = Receipt.query.filter_by(status='disputed').count()

        return jsonify({
            'total': total,
            'qualified': qualified,
            'defective': defective,
            'rejected': rejected,
            'disputed': disputed
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取统计失败: {str(e)}'}), 500


@bp.route('/pending-pos', methods=['GET', 'OPTIONS'])
def get_pending_pos():
    """
    获取待创建收货回执的PO列表
    （发票已批准但未创建收货回执的PO）
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        # 查询发票已批准的PO
        approved_invoices = Invoice.query.filter_by(status='approved').all()
        approved_po_ids = [inv.po_id for inv in approved_invoices]

        # 查询已创建收货回执的PO
        receipted_po_ids = [r.po_id for r in Receipt.query.all()]

        # 待创建收货回执的PO = 发票已批准 - 已创建收货回执
        pending_po_ids = set(approved_po_ids) - set(receipted_po_ids)

        pending_pos = PurchaseOrder.query.filter(PurchaseOrder.id.in_(pending_po_ids)).all()

        result = []
        for po in pending_pos:
            # 获取对应的发票
            invoice = Invoice.query.filter_by(po_id=po.id, status='approved').first()

            result.append({
                'po_id': po.id,
                'po_number': po.po_number,
                'supplier_id': po.supplier_id,
                'supplier_name': po.supplier_name,
                'total_price': float(po.total_price),
                'status': po.status,
                'confirmed_at': iso(po.confirmed_at),
                'invoice_approved_at': iso(invoice.approved_at) if invoice else None,
            })

        return jsonify({
            'count': len(result),
            'pending_pos': result
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取待收货PO失败: {str(e)}'}), 500
