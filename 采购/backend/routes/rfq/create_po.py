# routes/rfq/create_po.py
# 从RFQ选中标并创建采购订单
from flask import Blueprint, request, jsonify
from extensions import db
from models.rfq import RFQ
from models.supplier_quote import SupplierQuote
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('rfq_create_po', __name__)

@bp.route('/<int:rfq_id>/create-po', methods=['POST', 'OPTIONS'])
def create_po_from_rfq(rfq_id):
    """
    从RFQ创建采购订单（选中标）

    POST /api/v1/rfqs/<rfq_id>/create-po
    Body: {
        "selected_quotes": [1, 2, 3]  # 选中的报价ID列表
    }

    Returns:
        {
            "success": true,
            "po_id": 123,
            "message": "采购订单创建成功"
        }
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        # 获取请求数据
        data = request.get_json() or {}
        selected_quote_ids = data.get('selected_quotes', [])

        if not selected_quote_ids:
            return jsonify({"error": "请选择至少一个报价"}), 400

        # 验证RFQ存在
        rfq = RFQ.query.get(rfq_id)
        if not rfq:
            return jsonify({"error": f"RFQ#{rfq_id} 不存在"}), 404

        # 验证所有报价都属于这个RFQ
        quotes = SupplierQuote.query.filter(
            SupplierQuote.id.in_(selected_quote_ids),
            SupplierQuote.rfq_id == rfq_id
        ).all()

        if len(quotes) != len(selected_quote_ids):
            return jsonify({"error": "部分报价不属于该RFQ"}), 400

        # 验证所有报价都已提交
        pending_quotes = [q for q in quotes if q.status == 'pending']
        if pending_quotes:
            return jsonify({
                "error": f"有 {len(pending_quotes)} 个报价尚未提交"
            }), 400

        # TODO: 创建采购订单（PO）
        # 这里需要实现PO模型和创建逻辑
        # 目前先标记报价为"已中标"

        for quote in quotes:
            quote.status = 'awarded'  # 中标状态

        # 更新RFQ状态
        rfq.status = 'po_created'

        db.session.commit()

        logger.info(f"✅ RFQ#{rfq_id} 创建采购订单成功，选中 {len(quotes)} 个报价")

        return jsonify({
            "success": True,
            "rfq_id": rfq_id,
            "selected_quotes": len(quotes),
            "message": f"成功选中 {len(quotes)} 个报价并标记为中标",
            "note": "采购订单(PO)功能待完善"
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 创建PO失败: {str(e)}", exc_info=True)
        return jsonify({"error": f"创建采购订单失败: {str(e)}"}), 500
