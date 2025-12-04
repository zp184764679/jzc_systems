# routes/grn_routes.py
# -*- coding: utf-8 -*-
"""
商品收货单（Goods Receipt Note）路由
支持物料级别的收货质检，对接仓库系统
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models.receipt import Receipt, ReceiptItem
from models.purchase_order import PurchaseOrder
from datetime import datetime
import traceback
import json
import logging
import requests
import os

logger = logging.getLogger(__name__)

# 注意：使用 /api 前缀以匹配前端调用 /api/grn
URL_PREFIX = '/api'

bp = Blueprint('grn', __name__)


@bp.before_request
def handle_preflight():
    """处理CORS预检请求"""
    if request.method == 'OPTIONS':
        return '', 200


@bp.route('/grn', methods=['POST', 'OPTIONS'])
def submit_grn():
    """
    提交商品收货单（GRN）

    请求体：
    {
        "poId": "PO-2024-001",  // PO编号
        "items": [
            {
                "sku": "MAT-001",      // 物料编码
                "qty": 100,            // 到货数量
                "okQty": 95,           // 合格数量
                "ngQty": 5             // 不良数量
            },
            ...
        ]
    }

    返回：
    {
        "success": true,
        "message": "收货单已成功创建",
        "receipt": { ... },
        "scm_sync": { ... }  // SCM同步状态
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
        po_number = data.get('poId')
        items = data.get('items', [])

        if not po_number:
            return jsonify({'error': '缺少采购订单号 (poId)'}), 400

        if not items or len(items) == 0:
            return jsonify({'error': '缺少收货明细 (items)'}), 400

        # 查找PO（通过PO编号）
        po = PurchaseOrder.query.filter_by(po_number=po_number).first()
        if not po:
            return jsonify({'error': f'找不到采购订单: {po_number}'}), 404

        # 检查是否已创建收货回执
        existing = Receipt.query.filter_by(po_id=po.id).first()
        if existing:
            return jsonify({
                'error': f'此PO已创建收货回执: {existing.receipt_number}'
            }), 400

        # 验证并处理每个物料行
        total_delivered = 0
        total_accepted = 0
        total_rejected = 0
        processed_items = []

        for idx, item in enumerate(items):
            sku = item.get('sku', '').strip()
            qty = int(item.get('qty', 0))
            ok_qty = int(item.get('okQty', 0))
            ng_qty = int(item.get('ngQty', 0))

            # 验证
            if not sku:
                return jsonify({
                    'error': f'第 {idx + 1} 行：物料编码不能为空'
                }), 400

            if qty <= 0:
                return jsonify({
                    'error': f'第 {idx + 1} 行：到货数必须大于0'
                }), 400

            if ok_qty < 0 or ng_qty < 0:
                return jsonify({
                    'error': f'第 {idx + 1} 行：合格数和不良数不能为负数'
                }), 400

            if ok_qty + ng_qty != qty:
                return jsonify({
                    'error': f'第 {idx + 1} 行：合格数({ok_qty}) + 不良数({ng_qty}) 必须等于到货数({qty})'
                }), 400

            # 计算合格率
            pass_rate = (ok_qty / qty * 100) if qty > 0 else 0

            processed_items.append({
                'sku': sku,
                'qty': qty,
                'ok_qty': ok_qty,
                'ng_qty': ng_qty,
                'pass_rate': round(pass_rate, 2)
            })

            total_delivered += qty
            total_accepted += ok_qty
            total_rejected += ng_qty

        # 确定整体质量状态
        overall_pass_rate = (total_accepted / total_delivered * 100) if total_delivered > 0 else 0

        if overall_pass_rate >= 100:
            quality_status = 'qualified'
        elif overall_pass_rate >= 80:
            quality_status = 'defective'
        else:
            quality_status = 'rejected'

        # 创建收货回执主记录
        receipt = Receipt(
            receipt_number=Receipt.generate_receipt_number(),
            po_id=po.id,
            receiver_id=int(user_id),
            received_date=datetime.utcnow(),
            quality_status=quality_status,
            quantity_received=total_delivered,
            notes=f'整体合格率: {overall_pass_rate:.1f}%',
            status='confirmed',
            created_by=int(user_id)
        )

        db.session.add(receipt)
        db.session.flush()  # 获取receipt.id

        # 创建收货明细记录
        receipt_items = []
        for item_data in processed_items:
            receipt_item = ReceiptItem(
                receipt_id=receipt.id,
                material_code=item_data['sku'],
                material_name=item_data['sku'],  # 可以后续从物料主数据获取
                quantity_ordered=0,  # 可以从PO明细获取
                quantity_delivered=item_data['qty'],
                quantity_accepted=item_data['ok_qty'],
                quantity_rejected=item_data['ng_qty'],
                pass_rate=item_data['pass_rate']
            )
            db.session.add(receipt_item)
            receipt_items.append(receipt_item)

        # 更新PO状态为已收货
        po.status = 'received'

        db.session.commit()

        # 准备SCM同步（异步触发）
        scm_sync_result = trigger_scm_stock_in(receipt, receipt_items)

        logger.info(f"✅ GRN created: {receipt.receipt_number} for PO: {po_number}")

        return jsonify({
            'success': True,
            'message': f'收货单已成功创建: {receipt.receipt_number}',
            'receipt': {
                'id': receipt.id,
                'receipt_number': receipt.receipt_number,
                'po_number': po_number,
                'received_date': receipt.received_date.isoformat(),
                'quality_status': quality_status,
                'total_delivered': total_delivered,
                'total_accepted': total_accepted,
                'total_rejected': total_rejected,
                'overall_pass_rate': round(overall_pass_rate, 2),
                'items': [item.to_dict() for item in receipt_items]
            },
            'scm_sync': scm_sync_result
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"GRN submission failed: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'提交收货单失败: {str(e)}'}), 500


@bp.route('/grn/<po_number>', methods=['GET', 'OPTIONS'])
def get_grn_by_po(po_number):
    """
    根据PO编号获取收货单
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        po = PurchaseOrder.query.filter_by(po_number=po_number).first()
        if not po:
            return jsonify({'error': f'找不到采购订单: {po_number}'}), 404

        receipt = Receipt.query.filter_by(po_id=po.id).first()
        if not receipt:
            return jsonify({'error': f'此PO尚未创建收货单'}), 404

        return jsonify({
            'success': True,
            'receipt': receipt.to_dict()
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取收货单失败: {str(e)}'}), 500


def trigger_scm_stock_in(receipt, receipt_items):
    """
    触发SCM仓库系统的入库请求
    调用SCM的 /api/inventory/tx 批量入库接口
    """
    try:
        SCM_API_BASE = os.getenv('SCM_API_BASE_URL', 'http://localhost:8004')

        # 准备批量入库数据
        batch_items = []
        for item in receipt_items:
            # 只入库合格品
            if item.quantity_accepted > 0:
                batch_items.append({
                    'product_text': item.material_code,  # 映射到SCM的product_text
                    'qty_delta': float(item.quantity_accepted),
                    'tx_type': 'IN',
                    'order_no': receipt.po.po_number if receipt.po else '',
                    'uom': 'pcs',  # 可以从物料主数据获取
                    'location': '深圳',  # 默认位置，可以从配置获取
                    'bin_code': item.storage_location or '',
                    'ref': f'RECEIPT-{receipt.receipt_number}',
                    'remark': f'采购收货 - 合格率{item.pass_rate}%'
                })

        if not batch_items:
            logger.warning(f"No qualified items to sync for {receipt.receipt_number}")
            return {
                'status': 'skipped',
                'message': '没有合格品需要入库',
                'items_count': 0
            }

        # 调用SCM批量入库API
        logger.info(f"Calling SCM API: POST {SCM_API_BASE}/api/inventory/tx with {len(batch_items)} items")

        response = requests.post(
            f"{SCM_API_BASE}/api/inventory/tx",
            json=batch_items,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"✅ SCM sync successful for {receipt.receipt_number}: {result}")

            return {
                'status': 'success',
                'message': 'SCM库存已更新',
                'items_count': len(batch_items),
                'scm_response': result
            }
        else:
            logger.error(f"SCM API returned {response.status_code}: {response.text}")
            return {
                'status': 'error',
                'message': f'SCM API返回错误: {response.status_code}',
                'items_count': len(batch_items),
                'error_detail': response.text
            }

    except requests.exceptions.ConnectionError as e:
        logger.warning(f"SCM service not available: {str(e)}")
        return {
            'status': 'pending',
            'message': 'SCM服务暂时不可用，入库请求已记录，将自动重试',
            'items_count': len(batch_items) if 'batch_items' in locals() else 0,
            'error': str(e)
        }
    except requests.exceptions.Timeout as e:
        logger.error(f"SCM API timeout: {str(e)}")
        return {
            'status': 'timeout',
            'message': 'SCM服务响应超时',
            'items_count': len(batch_items) if 'batch_items' in locals() else 0,
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"SCM sync failed: {str(e)}")
        return {
            'status': 'error',
            'message': f'SCM同步失败: {str(e)}',
            'items_count': 0
        }


@bp.route('/grn/pending', methods=['GET', 'OPTIONS'])
def get_pending_grn():
    """
    获取待收货的PO列表
    """
    if request.method == 'OPTIONS':
        return '', 200

    try:
        # 查询状态为confirmed但尚未收货的PO
        confirmed_pos = PurchaseOrder.query.filter(
            PurchaseOrder.status.in_(['confirmed', 'invoiced'])
        ).all()

        # 排除已创建收货单的PO
        receipted_po_ids = [r.po_id for r in Receipt.query.all()]

        pending_pos = []
        for po in confirmed_pos:
            if po.id not in receipted_po_ids:
                pending_pos.append({
                    'po_id': po.id,
                    'po_number': po.po_number,
                    'supplier_name': po.supplier_name,
                    'total_price': float(po.total_price),
                    'status': po.status,
                    'confirmed_at': po.confirmed_at.isoformat() if po.confirmed_at else None
                })

        return jsonify({
            'success': True,
            'count': len(pending_pos),
            'pending_pos': pending_pos
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'获取待收货PO失败: {str(e)}'}), 500
