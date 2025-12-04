# routes/supplier_quote_routes.py
# 供应商报价相关API路由
# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from datetime import datetime
from extensions import db
from models.supplier_quote import SupplierQuote
from models.supplier import Supplier
import logging
import json
import sys
import os

# Add shared module to path for JWT verification
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '..'))
from shared.auth import verify_token

logger = logging.getLogger(__name__)

bp_supplier_quote = Blueprint(
    "supplier_quote",
    __name__
)

# 设置URL前缀，让app.py自动注册时使用
URL_PREFIX = "/api/v1/suppliers"


@bp_supplier_quote.before_request
def check_auth():
    """JWT认证检查"""
    if request.method == 'OPTIONS':
        return None

    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if payload:
            request.current_user_id = payload.get('user_id')
            request.current_user_role = payload.get('role')
            request.current_supplier_id = payload.get('supplier_id')
            return None

    # 回退检查 Supplier-ID header（供应商端）
    supplier_id = request.headers.get('Supplier-ID')
    user_id = request.headers.get('User-ID')
    if supplier_id or user_id:
        request.current_supplier_id = supplier_id
        request.current_user_id = user_id
        request.current_user_role = request.headers.get('User-Role')
        return None

    return jsonify({"error": "未授权：请先登录"}), 401


def _to_int(v, default=None):
    try:
        if v is None:
            return default
        return int(str(v).strip())
    except Exception:
        return default


# 供应商：提交报价
@bp_supplier_quote.route("/me/supplier-quotes/<int:quote_id>/participate", methods=["POST", "OPTIONS"])
def participate_in_quote(quote_id):
    """
    POST /api/v1/suppliers/me/supplier-quotes/:id/participate
    供应商对报价请求进行报价（支持多物料品类分组）

    请求体：
    {
        "total_price": 5000.00,        // 总价（必填）
        "lead_time": 7,                 // 交货期（天）
        "payment_terms": 90,            // 付款周期（天），默认90
        "quote_json": {                 // 详细报价（改进版，支持多个items）
            "items": [
                {
                    "item_name": "铣刀",
                    "item_description": "直径10mm硬质合金",
                    "quantity_requested": 100,
                    "unit": "个",
                    "unit_price": 45.00,      // 供应商填写的单价
                    "subtotal": 4500.00       // 小计
                },
                {
                    "item_name": "车刀",
                    "item_description": "YT15材质",
                    "quantity_requested": 10,
                    "unit": "个",
                    "unit_price": 50.00,
                    "subtotal": 500.00
                }
            ],
            "notes": "质保一年，包含运费"  // 备注
        }
    }
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    # 1) 读取 Supplier-ID
    supplier_id = request.headers.get("Supplier-ID") or request.headers.get("Supplier-Id") or request.headers.get("supplier-id")
    supplier_id = _to_int(supplier_id)
    if not supplier_id:
        return jsonify({"error": "缺少 Supplier-ID 请求头"}), 400

    # 2) 获取报价记录
    quote = SupplierQuote.query.filter_by(id=quote_id, supplier_id=supplier_id).first()
    if not quote:
        return jsonify({"error": "报价记录不存在"}), 404

    # 3) 检查状态 - 只有 pending 状态可以报价
    if quote.status != 'pending':
        return jsonify({"error": f"该报价状态为 {quote.status}，不允许报价"}), 400

    # 4) 获取报价数据
    try:
        data = request.get_json() or {}
    except Exception:
        return jsonify({"error": "无效的 JSON 数据"}), 400

    total_price = data.get('total_price')
    lead_time = data.get('lead_time')
    payment_terms = data.get('payment_terms')
    quote_json = data.get('quote_json')

    if total_price is None:
        return jsonify({"error": "缺少 total_price 字段"}), 400

    try:
        # 5) 更新报价
        quote.total_price = float(total_price)
        quote.lead_time = _to_int(lead_time) if lead_time else None
        quote.payment_terms = _to_int(payment_terms, 90)  # 默认90天
        quote.status = 'received'  # 改为已报价状态
        quote.responded_at = datetime.utcnow()

        # 如果有详细报价JSON，保存
        if quote_json:
            quote.quote_json = json.dumps(quote_json) if isinstance(quote_json, dict) else quote_json

        # 6) 生成并保存报价号（如果还没有）
        if not quote.quote_number:
            from models.supplier_quote import generate_quote_display_no
            # 确保supplier关联已加载
            if not quote.supplier:
                from models.supplier import Supplier
                quote.supplier = Supplier.query.get(quote.supplier_id)
            quote.quote_number = generate_quote_display_no(quote)

        db.session.commit()

        logger.info(f"✅ 供应商 {supplier_id} 已对报价 {quote_id} 完成报价，报价号：{quote.quote_number}")

        return jsonify({
            "message": "报价成功",
            "data": quote.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 提交报价失败: {str(e)}")
        return jsonify({"error": "提交报价失败"}), 500


BLUEPRINTS = [bp_supplier_quote]
