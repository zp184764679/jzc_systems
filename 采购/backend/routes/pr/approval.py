# routes/pr/approval.py
# -*- coding: utf-8 -*-
"""
采购审批流程（更新版）：
  submitted → supervisor_approved → price_filled → [pending_general_manager] → approved

  角色说明：
  - user (员工): 只能提交申请
  - supervisor (主管): 审批员工申请 + 填写价格
  - factory_manager (厂长): 审批价格（原admin）
  - general_manager (总经理): 超额审批（金额>2000或价格偏差>5%）
  - super_admin (超级管理员): 最高权限

  流程：
  1. 员工提交 PR (submitted)
  2. 主管审批 → supervisor_approved
  3. 主管填写价格 → price_filled
  4. 厂长审批 → 自动判断：
     - 总金额 ≤ 2000 且 所有物料价格偏差 ≤ 5% → approved（直接通过）
     - 否则 → pending_general_manager → 总经理审批 → approved
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from models.pr import PR
from models.price_history import PriceHistory
from extensions import db
import traceback
from .common import zh_status
from utils.history_logger import log_pr_operation

bp = Blueprint('pr_approval', __name__)

# ============================================
# 主管审批
# ============================================
@bp.route('/<int:id>/supervisor-approve', methods=['POST', 'OPTIONS'])
def supervisor_approve(id):
    """主管审批通过 - 状态从 submitted → supervisor_approved"""
    if request.method == 'OPTIONS':
        return "", 204

    try:
        pr = PR.query.get(id)
        if not pr:
            return jsonify({"error": "申请不存在"}), 404

        if pr.status != "submitted":
            return jsonify({"error": f"当前状态不允许主管审批，当前状态: {zh_status(pr.status)}"}), 400

        user_id = getattr(request, 'current_user_id', None)
        old_status = pr.status

        pr.status = "supervisor_approved"
        pr.supervisor_approved_at = datetime.utcnow()
        pr.supervisor_approved_by = user_id

        # 记录操作历史
        log_pr_operation(
            action="approve",
            pr=pr,
            old_status=old_status,
            new_status=pr.status,
            description=f"主管审批通过 {pr.pr_number}"
        )

        db.session.commit()

        return jsonify({
            "message": "主管审批通过，请填写价格",
            "status": zh_status(pr.status),
            "status_code": pr.status,
            "id": pr.id,
            "prNumber": pr.pr_number
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"主管审批错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


# ============================================
# 填写价格
# ============================================
@bp.route('/<int:id>/fill-price', methods=['POST', 'OPTIONS'])
def fill_price(id):
    """
    填写物料价格 - 状态从 supervisor_approved → price_filled

    请求体:
    {
        "items": [
            {"id": 1, "unit_price": 100.50},
            {"id": 2, "unit_price": 200.00}
        ]
    }
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        pr = PR.query.get(id)
        if not pr:
            return jsonify({"error": "申请不存在"}), 404

        if pr.status != "supervisor_approved":
            return jsonify({"error": f"当前状态不允许填写价格，当前状态: {zh_status(pr.status)}"}), 400

        data = request.json or {}
        items_data = data.get("items", [])

        if not items_data:
            return jsonify({"error": "请提供物料价格"}), 400

        user_id = getattr(request, 'current_user_id', None)
        old_status = pr.status

        # 构建 item_id -> price 映射
        price_map = {item["id"]: item["unit_price"] for item in items_data if "id" in item and "unit_price" in item}

        # 更新每个物料的价格
        total_amount = 0
        price_details = []
        for item in pr.items:
            if item.id in price_map:
                item.unit_price = price_map[item.id]
                item.calculate_total()  # 计算小计
                if item.total_price:
                    total_amount += float(item.total_price)
                price_details.append({
                    "item_id": item.id,
                    "name": item.name,
                    "unit_price": float(item.unit_price) if item.unit_price else 0,
                    "qty": item.qty,
                    "total": float(item.total_price) if item.total_price else 0
                })

        pr.total_amount = total_amount
        pr.status = "price_filled"
        pr.price_filled_at = datetime.utcnow()
        pr.price_filled_by = user_id

        # 记录操作历史
        log_pr_operation(
            action="update",
            pr=pr,
            old_status=old_status,
            new_status=pr.status,
            description=f"填写价格 {pr.pr_number}，总金额 {total_amount:.2f}",
            extra_data={"items": price_details, "total_amount": total_amount}
        )

        db.session.commit()

        return jsonify({
            "message": "价格填写完成，待管理员审批",
            "status": zh_status(pr.status),
            "status_code": pr.status,
            "id": pr.id,
            "prNumber": pr.pr_number,
            "total_amount": float(pr.total_amount) if pr.total_amount else 0
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"填写价格错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


# ============================================
# 厂长审批（含自动判断逻辑）
# ============================================
@bp.route('/<int:id>/admin-approve', methods=['POST', 'OPTIONS'])
@bp.route('/<int:id>/factory-manager-approve', methods=['POST', 'OPTIONS'])
def admin_approve(id):
    """
    厂长审批通过 - 状态从 price_filled → approved 或 pending_general_manager
    自动判断：
    - 总金额 ≤ 2000 且 所有物料价格偏差 ≤ 5% → approved（直接通过）
    - 否则 → pending_general_manager（需要总经理审批）

    兼容旧接口：admin-approve
    新接口：factory-manager-approve
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        pr = PR.query.get(id)
        if not pr:
            return jsonify({"error": "申请不存在"}), 404

        if pr.status != "price_filled":
            return jsonify({"error": f"当前状态不允许管理员审批，当前状态: {zh_status(pr.status)}"}), 400

        user_id = getattr(request, 'current_user_id', None)
        old_status = pr.status

        pr.admin_approved_at = datetime.utcnow()
        pr.admin_approved_by = user_id

        # 自动判断是否需要超管审批
        total_amount = float(pr.total_amount) if pr.total_amount else 0

        # 检查每个物料的价格偏差
        all_within_threshold = True
        deviation_details = []

        for item in pr.items:
            if item.unit_price:
                result = PriceHistory.check_price_deviation(
                    item_name=item.name,
                    item_spec=item.spec,
                    new_price=float(item.unit_price),
                    threshold=0.05  # 5%
                )
                deviation_details.append({
                    "item_name": item.name,
                    "item_spec": item.spec,
                    "unit_price": float(item.unit_price),
                    "has_history": result["has_history"],
                    "avg_price": result["avg_price"],
                    "deviation": result["deviation"],
                    "within_threshold": result["within_threshold"]
                })
                if not result["within_threshold"]:
                    all_within_threshold = False

        # 判断是否自动通过
        if total_amount <= 2000 and all_within_threshold:
            # 自动通过，无需总经理审批
            pr.status = "approved"
            pr.needs_super_admin = False
            pr.auto_approve_reason = f"金额{total_amount}元≤2000且价格偏差≤5%"

            # 记录操作历史
            log_pr_operation(
                action="approve",
                pr=pr,
                old_status=old_status,
                new_status=pr.status,
                description=f"厂长审批通过 {pr.pr_number}（自动通过：{pr.auto_approve_reason}）",
                extra_data={"auto_approved": True, "total_amount": total_amount, "deviation_details": deviation_details}
            )

            # 记录价格到历史表
            _record_prices_to_history(pr)

            db.session.commit()

            return jsonify({
                "message": "厂长审批完成，采购申请已自动通过",
                "status": zh_status(pr.status),
                "status_code": pr.status,
                "id": pr.id,
                "prNumber": pr.pr_number,
                "auto_approved": True,
                "auto_approve_reason": pr.auto_approve_reason,
                "total_amount": total_amount,
                "deviation_details": deviation_details
            }), 200
        else:
            # 需要总经理审批
            pr.status = "pending_super_admin"  # 暂时保留字段名兼容，实际表示待总经理审批
            pr.needs_super_admin = True

            reasons = []
            if total_amount > 2000:
                reasons.append(f"金额{total_amount}元>2000")
            if not all_within_threshold:
                reasons.append("部分物料价格偏差>5%")

            # 记录操作历史
            log_pr_operation(
                action="forward",
                pr=pr,
                old_status=old_status,
                new_status=pr.status,
                description=f"厂长审批转交总经理 {pr.pr_number}（原因：{'；'.join(reasons)}）",
                extra_data={"reasons": reasons, "total_amount": total_amount, "deviation_details": deviation_details}
            )

            db.session.commit()

            return jsonify({
                "message": "需要总经理审批",
                "status": zh_status(pr.status),
                "status_code": pr.status,
                "id": pr.id,
                "prNumber": pr.pr_number,
                "auto_approved": False,
                "need_super_admin_reason": "；".join(reasons),
                "need_general_manager_reason": "；".join(reasons),
                "total_amount": total_amount,
                "deviation_details": deviation_details
            }), 200

    except Exception as e:
        db.session.rollback()
        print(f"管理员审批错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


# ============================================
# 总经理审批（兼容旧接口super-admin-approve）
# ============================================
@bp.route('/<int:id>/super-admin-approve', methods=['POST', 'OPTIONS'])
@bp.route('/<int:id>/general-manager-approve', methods=['POST', 'OPTIONS'])
def super_admin_approve(id):
    """
    总经理审批通过 - 状态从 pending_super_admin → approved

    兼容旧接口：super-admin-approve
    新接口：general-manager-approve
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        pr = PR.query.get(id)
        if not pr:
            return jsonify({"error": "申请不存在"}), 404

        if pr.status != "pending_super_admin":
            return jsonify({"error": f"当前状态不允许总经理审批，当前状态: {zh_status(pr.status)}"}), 400

        user_id = getattr(request, 'current_user_id', None)
        old_status = pr.status

        pr.status = "approved"
        pr.super_admin_approved_at = datetime.utcnow()
        pr.super_admin_approved_by = user_id

        # 记录操作历史
        log_pr_operation(
            action="approve",
            pr=pr,
            old_status=old_status,
            new_status=pr.status,
            description=f"总经理审批通过 {pr.pr_number}",
            extra_data={"total_amount": float(pr.total_amount) if pr.total_amount else 0}
        )

        # 记录价格到历史表
        _record_prices_to_history(pr)

        db.session.commit()

        return jsonify({
            "message": "总经理审批完成",
            "status": zh_status(pr.status),
            "status_code": pr.status,
            "id": pr.id,
            "prNumber": pr.pr_number
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"总经理审批错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


# ============================================
# 驳回（任意阶段可用）
# ============================================
@bp.route('/<int:id>/reject', methods=['POST', 'OPTIONS'])
def reject(id):
    """
    驳回申请 - 任意阶段都可以驳回

    请求体:
    {
        "reason": "驳回原因"
    }
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        pr = PR.query.get(id)
        if not pr:
            return jsonify({"error": "申请不存在"}), 404

        if pr.status in ["completed", "rejected"]:
            return jsonify({"error": f"当前状态不允许驳回，当前状态: {zh_status(pr.status)}"}), 400

        user_id = getattr(request, 'current_user_id', None)
        old_status = pr.status
        data = request.json or {}
        reason = data.get("reason", "")

        pr.status = "rejected"
        pr.rejected_at = datetime.utcnow()
        pr.rejected_by = user_id
        pr.reject_reason = reason

        for item in pr.items:
            item.status = "rejected"

        # 记录操作历史
        log_pr_operation(
            action="reject",
            pr=pr,
            old_status=old_status,
            new_status=pr.status,
            description=f"驳回 {pr.pr_number}" + (f"（原因：{reason}）" if reason else ""),
            extra_data={"reject_reason": reason}
        )

        db.session.commit()

        return jsonify({
            "message": "申请已驳回",
            "status": zh_status(pr.status),
            "status_code": pr.status,
            "id": pr.id,
            "prNumber": pr.pr_number,
            "reject_reason": reason
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"驳回操作错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


# ============================================
# 兼容旧接口
# ============================================
@bp.route('/<int:id>/<string:action>', methods=['POST', 'OPTIONS'])
def approve_or_reject_legacy(id, action):
    """
    兼容旧接口 - 将旧的 approve/reject 映射到新流程
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        pr = PR.query.get(id)
        if not pr:
            return jsonify({"error": "申请不存在"}), 404

        if action == "approve":
            # 根据当前状态决定调用哪个审批
            if pr.status == "submitted":
                return supervisor_approve(id)
            elif pr.status == "price_filled":
                return admin_approve(id)
            elif pr.status == "pending_super_admin":
                return super_admin_approve(id)
            else:
                return jsonify({"error": f"当前状态不允许审批: {zh_status(pr.status)}"}), 400

        elif action == "reject":
            return reject(id)
        else:
            return jsonify({"error": "无效的操作"}), 400

    except Exception as e:
        print(f"审批操作错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


# ============================================
# 辅助函数
# ============================================
def _record_prices_to_history(pr):
    """将PR完成后的价格记录到历史表"""
    for item in pr.items:
        if item.unit_price:
            PriceHistory.record_price(
                item_name=item.name,
                item_spec=item.spec or "",
                unit_price=float(item.unit_price),
                qty=item.qty,
                unit=item.unit,
                pr_id=pr.id,
                pr_number=pr.pr_number,
                pr_item_id=item.id
            )
