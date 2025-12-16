# -*- coding: utf-8 -*-
"""
订单工作流 API
提供订单状态流转、审批操作、审批历史查询等功能
"""
from __future__ import annotations

from datetime import datetime
from flask import jsonify, request

from . import orders  # 复用 orders.py 中的 bp 和工具函数
from ..models.core import (
    Order, OrderApproval,
    OrderStatus, ApprovalAction,
    can_transition, get_next_status
)
from .. import db

bp = orders.bp  # 使用同一个 Blueprint


# === 状态中文映射 ===
ORDER_STATUS_MAP = {
    OrderStatus.DRAFT.value: "草稿",
    OrderStatus.PENDING.value: "待审批",
    OrderStatus.CONFIRMED.value: "已确认",
    OrderStatus.IN_PRODUCTION.value: "生产中",
    OrderStatus.IN_DELIVERY.value: "交货中",
    OrderStatus.COMPLETED.value: "已完成",
    OrderStatus.CANCELLED.value: "已取消",
}

# === 动作中文映射 ===
ACTION_NAME_MAP = {
    ApprovalAction.SUBMIT.value: "提交审批",
    ApprovalAction.APPROVE.value: "审批通过",
    ApprovalAction.REJECT.value: "审批拒绝",
    ApprovalAction.RETURN.value: "退回修改",
    ApprovalAction.CANCEL.value: "取消订单",
    ApprovalAction.START_PRODUCTION.value: "开始生产",
    ApprovalAction.START_DELIVERY.value: "开始交货",
    ApprovalAction.COMPLETE.value: "完成订单",
}


def _get_current_user():
    """获取当前用户信息（从请求头或 JWT 中解析）"""
    # 尝试从请求头获取用户信息
    user_id = request.headers.get('X-User-Id')
    user_name = request.headers.get('X-User-Name', '系统')

    if user_id:
        try:
            user_id = int(user_id)
        except:
            user_id = None

    return user_id, user_name


def _create_approval_record(order: Order, action: str, from_status: str, to_status: str, comment: str = None):
    """创建审批记录"""
    user_id, user_name = _get_current_user()

    approval = OrderApproval(
        order_id=order.id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        operator_id=user_id,
        operator_name=user_name,
        comment=comment
    )
    db.session.add(approval)
    return approval


def _perform_action(order_id: int, action: str, comment: str = None, extra_update: dict = None):
    """执行工作流动作的通用方法"""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"success": False, "error": "订单不存在"}), 404

    current_status = order.status or OrderStatus.DRAFT.value

    # 检查状态流转是否合法
    if not can_transition(current_status, action):
        allowed = list(orders.ORDER_STATUS_TRANSITIONS.get(current_status, {}).keys()) if hasattr(orders, 'ORDER_STATUS_TRANSITIONS') else []
        return jsonify({
            "success": False,
            "error": f"当前状态 [{ORDER_STATUS_MAP.get(current_status, current_status)}] 不允许执行 [{ACTION_NAME_MAP.get(action, action)}]",
            "current_status": current_status,
            "allowed_actions": allowed
        }), 400

    # 获取目标状态
    new_status = get_next_status(current_status, action)
    if not new_status:
        return jsonify({"success": False, "error": "无法确定目标状态"}), 500

    try:
        # 更新订单状态
        old_status = order.status
        order.status = new_status

        # 根据动作更新特定字段
        user_id, user_name = _get_current_user()
        now = datetime.now()

        if action == ApprovalAction.SUBMIT.value:
            order.submitted_at = now
            order.submitted_by = user_id
            order.submitted_by_name = user_name
        elif action == ApprovalAction.APPROVE.value:
            order.confirmed_at = now
            order.confirmed_by = user_id
            order.confirmed_by_name = user_name
        elif action == ApprovalAction.COMPLETE.value:
            order.completed_at = now
        elif action == ApprovalAction.CANCEL.value:
            order.cancelled_at = now
            if comment:
                order.cancel_reason = comment

        # 应用额外更新
        if extra_update:
            for key, value in extra_update.items():
                if hasattr(order, key):
                    setattr(order, key, value)

        # 创建审批记录
        _create_approval_record(order, action, old_status, new_status, comment)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"{ACTION_NAME_MAP.get(action, action)}成功",
            "order_id": order.id,
            "order_no": order.order_no,
            "from_status": old_status,
            "to_status": new_status,
            "status_name": ORDER_STATUS_MAP.get(new_status, new_status)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# === 工作流动作 API ===

@bp.route('/<int:order_id>/submit', methods=['POST'])
def submit_order(order_id):
    """提交订单审批"""
    data = request.get_json(silent=True) or {}
    return _perform_action(order_id, ApprovalAction.SUBMIT.value, data.get('comment'))


@bp.route('/<int:order_id>/approve', methods=['POST'])
def approve_order(order_id):
    """审批通过"""
    data = request.get_json(silent=True) or {}
    return _perform_action(order_id, ApprovalAction.APPROVE.value, data.get('comment'))


@bp.route('/<int:order_id>/reject', methods=['POST'])
def reject_order(order_id):
    """审批拒绝（退回草稿）"""
    data = request.get_json(silent=True) or {}
    comment = data.get('comment') or data.get('reason')
    if not comment:
        return jsonify({"success": False, "error": "拒绝时必须填写原因"}), 400
    return _perform_action(order_id, ApprovalAction.REJECT.value, comment)


@bp.route('/<int:order_id>/return', methods=['POST'])
def return_order(order_id):
    """退回修改"""
    data = request.get_json(silent=True) or {}
    comment = data.get('comment') or data.get('reason')
    return _perform_action(order_id, ApprovalAction.RETURN.value, comment)


@bp.route('/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """取消订单"""
    data = request.get_json(silent=True) or {}
    comment = data.get('comment') or data.get('reason')
    return _perform_action(order_id, ApprovalAction.CANCEL.value, comment)


@bp.route('/<int:order_id>/start-production', methods=['POST'])
def start_production(order_id):
    """开始生产"""
    data = request.get_json(silent=True) or {}
    return _perform_action(order_id, ApprovalAction.START_PRODUCTION.value, data.get('comment'))


@bp.route('/<int:order_id>/start-delivery', methods=['POST'])
def start_delivery(order_id):
    """开始交货"""
    data = request.get_json(silent=True) or {}
    return _perform_action(order_id, ApprovalAction.START_DELIVERY.value, data.get('comment'))


@bp.route('/<int:order_id>/complete', methods=['POST'])
def complete_order(order_id):
    """完成订单"""
    data = request.get_json(silent=True) or {}
    return _perform_action(order_id, ApprovalAction.COMPLETE.value, data.get('comment'))


# === 审批历史 API ===

@bp.route('/<int:order_id>/approvals', methods=['GET'])
def get_order_approvals(order_id):
    """获取订单审批历史"""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"success": False, "error": "订单不存在"}), 404

    approvals = OrderApproval.query.filter_by(order_id=order_id).order_by(OrderApproval.created_at.desc()).all()

    return jsonify({
        "success": True,
        "order_id": order_id,
        "order_no": order.order_no,
        "current_status": order.status,
        "current_status_name": ORDER_STATUS_MAP.get(order.status, order.status),
        "approvals": [
            {
                **a.to_dict(),
                "action_name": ACTION_NAME_MAP.get(a.action, a.action),
                "from_status_name": ORDER_STATUS_MAP.get(a.from_status, a.from_status),
                "to_status_name": ORDER_STATUS_MAP.get(a.to_status, a.to_status),
            }
            for a in approvals
        ]
    })


# === 待审批列表 API ===

@bp.route('/pending-approval', methods=['GET'])
def get_pending_approval_orders():
    """获取待审批订单列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    query = Order.query.filter(Order.status == OrderStatus.PENDING.value)

    # 支持关键词搜索
    keyword = request.args.get('keyword', '').strip()
    if keyword:
        from sqlalchemy import or_
        query = query.filter(or_(
            Order.order_no.like(f'%{keyword}%'),
            Order.product.like(f'%{keyword}%'),
            Order.customer_code.like(f'%{keyword}%')
        ))

    total = query.count()
    orders_list = query.order_by(Order.submitted_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "success": True,
        "data": [orders._order_to_dict(o) for o in orders_list],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    })


# === 订单统计 API ===

@bp.route('/statistics', methods=['GET'])
def get_order_statistics():
    """获取订单统计数据"""
    from sqlalchemy import func

    # 按状态统计
    status_stats = db.session.query(
        Order.status,
        func.count(Order.id).label('count'),
        func.sum(Order.order_qty).label('total_qty')
    ).group_by(Order.status).all()

    by_status = []
    total_count = 0
    total_qty = 0

    for stat in status_stats:
        status = stat[0] or OrderStatus.DRAFT.value
        count = stat[1] or 0
        qty = float(stat[2] or 0)
        total_count += count
        total_qty += qty
        by_status.append({
            "status": status,
            "status_name": ORDER_STATUS_MAP.get(status, status),
            "count": count,
            "total_qty": qty
        })

    # 本月订单统计
    from datetime import date
    today = date.today()
    first_day_of_month = today.replace(day=1)

    this_month_stats = db.session.query(
        func.count(Order.id).label('count'),
        func.sum(Order.order_qty).label('total_qty')
    ).filter(Order.order_date >= first_day_of_month).first()

    # 待审批数量
    pending_count = Order.query.filter(Order.status == OrderStatus.PENDING.value).count()

    return jsonify({
        "success": True,
        "total_orders": total_count,
        "total_qty": total_qty,
        "pending_approval": pending_count,
        "by_status": by_status,
        "this_month": {
            "count": this_month_stats[0] or 0,
            "total_qty": float(this_month_stats[1] or 0)
        }
    })


# === 枚举值 API ===

@bp.route('/enums', methods=['GET'])
def get_order_enums():
    """获取订单相关枚举值"""
    return jsonify({
        "success": True,
        "statuses": [
            {"value": s.value, "label": ORDER_STATUS_MAP.get(s.value, s.value)}
            for s in OrderStatus
        ],
        "actions": [
            {"value": a.value, "label": ACTION_NAME_MAP.get(a.value, a.value)}
            for a in ApprovalAction
        ],
        "status_transitions": {
            status: {
                action: ORDER_STATUS_MAP.get(target, target)
                for action, target in transitions.items()
            }
            for status, transitions in orders.ORDER_STATUS_TRANSITIONS.items()
        } if hasattr(orders, 'ORDER_STATUS_TRANSITIONS') else {}
    })


# === 可用动作查询 API ===

@bp.route('/<int:order_id>/available-actions', methods=['GET'])
def get_available_actions(order_id):
    """获取订单当前可执行的动作"""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"success": False, "error": "订单不存在"}), 404

    current_status = order.status or OrderStatus.DRAFT.value

    # 从 core.py 导入状态流转规则
    from ..models.core import ORDER_STATUS_TRANSITIONS

    transitions = ORDER_STATUS_TRANSITIONS.get(current_status, {})

    actions = [
        {
            "action": action,
            "action_name": ACTION_NAME_MAP.get(action, action),
            "target_status": target,
            "target_status_name": ORDER_STATUS_MAP.get(target, target)
        }
        for action, target in transitions.items()
    ]

    return jsonify({
        "success": True,
        "order_id": order_id,
        "order_no": order.order_no,
        "current_status": current_status,
        "current_status_name": ORDER_STATUS_MAP.get(current_status, current_status),
        "available_actions": actions
    })
