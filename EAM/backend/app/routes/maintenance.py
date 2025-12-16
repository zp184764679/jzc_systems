# -*- coding: utf-8 -*-
"""
EAM 维护保养 API
包含：保养标准、保养计划、保养工单、故障报修、点检记录
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from datetime import date, datetime, timedelta
import re

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from sqlalchemy import or_, desc, asc, and_, func

from .. import db
from ..models.maintenance import (
    MaintenanceStandard, MaintenancePlan, MaintenanceOrder,
    FaultReport, InspectionRecord,
    generate_order_no, generate_report_no, generate_inspection_no,
    CYCLE_DAYS_MAP, ORDER_STATUS_TRANSITIONS, FAULT_STATUS_TRANSITIONS
)
from ..models.machine import Machine

bp = Blueprint("maintenance", __name__, url_prefix="/api/maintenance")


# ==========================
# 工具函数
# ==========================
def _json() -> Dict[str, Any]:
    try:
        return request.get_json(force=True, silent=True) or {}
    except Exception:
        return {}

def _trim(s: Optional[str]) -> Optional[str]:
    return s.strip() if isinstance(s, str) else s

def _as_int(v: Any) -> Optional[int]:
    try:
        return int(v) if v not in (None, "") else None
    except Exception:
        return None

def _as_float(v: Any) -> Optional[float]:
    try:
        return float(v) if v not in (None, "") else None
    except Exception:
        return None

def _as_date(s: Any) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None

def _as_datetime(s: Any) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except Exception:
        return None


# ==========================
# 保养标准 API
# ==========================
@bp.route("/standards", methods=["GET"])
@cross_origin()
def list_standards():
    """获取保养标准列表"""
    args = request.args or {}
    page = _as_int(args.get("page")) or 1
    page_size = _as_int(args.get("page_size")) or 20

    query = MaintenanceStandard.query

    # 筛选
    if args.get("keyword"):
        like = f"%{args.get('keyword')}%"
        query = query.filter(or_(
            MaintenanceStandard.code.ilike(like),
            MaintenanceStandard.name.ilike(like),
        ))
    if args.get("maintenance_type"):
        query = query.filter(MaintenanceStandard.maintenance_type == args.get("maintenance_type"))
    if args.get("machine_id"):
        query = query.filter(MaintenanceStandard.machine_id == int(args.get("machine_id")))
    if args.get("is_active") is not None:
        is_active = args.get("is_active") in ("true", "1", True)
        query = query.filter(MaintenanceStandard.is_active == is_active)

    # 排序
    query = query.order_by(asc(MaintenanceStandard.sort_order), desc(MaintenanceStandard.created_at))

    # 分页
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [s.to_dict() for s in items],
    })


@bp.route("/standards/<int:sid>", methods=["GET"])
@cross_origin()
def get_standard(sid: int):
    """获取保养标准详情"""
    s = MaintenanceStandard.query.get_or_404(sid)
    return jsonify(s.to_dict())


@bp.route("/standards", methods=["POST"])
@cross_origin()
def create_standard():
    """创建保养标准"""
    data = _json()

    name = _trim(data.get("name"))
    if not name:
        return jsonify({"error": "name is required"}), 400

    code = _trim(data.get("code")) or f"MS{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 检查编码唯一性
    if MaintenanceStandard.query.filter(MaintenanceStandard.code == code).first():
        return jsonify({"error": "code already exists"}), 409

    s = MaintenanceStandard(
        code=code,
        name=name,
        description=_trim(data.get("description")),
        machine_id=_as_int(data.get("machine_id")),
        machine_model=_trim(data.get("machine_model")),
        equipment_group=_trim(data.get("equipment_group")),
        maintenance_type=_trim(data.get("maintenance_type")) or "preventive",
        cycle=_trim(data.get("cycle")) or "monthly",
        cycle_days=_as_int(data.get("cycle_days")),
        estimated_hours=_as_float(data.get("estimated_hours")) or 1.0,
        check_items=data.get("check_items") or [],
        tools_required=data.get("tools_required") or [],
        spare_parts=data.get("spare_parts") or [],
        safety_notes=_trim(data.get("safety_notes")),
        is_active=data.get("is_active", True),
        sort_order=_as_int(data.get("sort_order")) or 0,
        created_by=_as_int(data.get("created_by")),
        created_by_name=_trim(data.get("created_by_name")),
    )

    try:
        db.session.add(s)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(s.to_dict()), 201


@bp.route("/standards/<int:sid>", methods=["PUT"])
@cross_origin()
def update_standard(sid: int):
    """更新保养标准"""
    s = MaintenanceStandard.query.get_or_404(sid)
    data = _json()

    # 更新字段
    if "name" in data:
        s.name = _trim(data["name"])
    if "description" in data:
        s.description = _trim(data["description"])
    if "machine_id" in data:
        s.machine_id = _as_int(data["machine_id"])
    if "machine_model" in data:
        s.machine_model = _trim(data["machine_model"])
    if "equipment_group" in data:
        s.equipment_group = _trim(data["equipment_group"])
    if "maintenance_type" in data:
        s.maintenance_type = _trim(data["maintenance_type"])
    if "cycle" in data:
        s.cycle = _trim(data["cycle"])
    if "cycle_days" in data:
        s.cycle_days = _as_int(data["cycle_days"])
    if "estimated_hours" in data:
        s.estimated_hours = _as_float(data["estimated_hours"])
    if "check_items" in data:
        s.check_items = data["check_items"]
    if "tools_required" in data:
        s.tools_required = data["tools_required"]
    if "spare_parts" in data:
        s.spare_parts = data["spare_parts"]
    if "safety_notes" in data:
        s.safety_notes = _trim(data["safety_notes"])
    if "is_active" in data:
        s.is_active = data["is_active"]
    if "sort_order" in data:
        s.sort_order = _as_int(data["sort_order"])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(s.to_dict())


@bp.route("/standards/<int:sid>", methods=["DELETE"])
@cross_origin()
def delete_standard(sid: int):
    """删除保养标准"""
    s = MaintenanceStandard.query.get_or_404(sid)

    try:
        db.session.delete(s)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"ok": True, "id": sid})


# ==========================
# 保养计划 API
# ==========================
@bp.route("/plans", methods=["GET"])
@cross_origin()
def list_plans():
    """获取保养计划列表"""
    args = request.args or {}
    page = _as_int(args.get("page")) or 1
    page_size = _as_int(args.get("page_size")) or 20

    query = MaintenancePlan.query

    # 筛选
    if args.get("keyword"):
        like = f"%{args.get('keyword')}%"
        query = query.filter(or_(
            MaintenancePlan.code.ilike(like),
            MaintenancePlan.name.ilike(like),
        ))
    if args.get("machine_id"):
        query = query.filter(MaintenancePlan.machine_id == int(args.get("machine_id")))
    if args.get("is_active") is not None:
        is_active = args.get("is_active") in ("true", "1", True)
        query = query.filter(MaintenancePlan.is_active == is_active)

    # 排序
    query = query.order_by(desc(MaintenancePlan.created_at))

    # 分页
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [p.to_dict() for p in items],
    })


@bp.route("/plans/<int:pid>", methods=["GET"])
@cross_origin()
def get_plan(pid: int):
    """获取保养计划详情"""
    p = MaintenancePlan.query.get_or_404(pid)
    return jsonify(p.to_dict())


@bp.route("/plans", methods=["POST"])
@cross_origin()
def create_plan():
    """创建保养计划"""
    data = _json()

    name = _trim(data.get("name"))
    machine_id = _as_int(data.get("machine_id"))

    if not name:
        return jsonify({"error": "name is required"}), 400
    if not machine_id:
        return jsonify({"error": "machine_id is required"}), 400

    # 验证设备存在
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({"error": "machine not found"}), 404

    code = _trim(data.get("code")) or f"MP{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 检查编码唯一性
    if MaintenancePlan.query.filter(MaintenancePlan.code == code).first():
        return jsonify({"error": "code already exists"}), 409

    start_date = _as_date(data.get("start_date")) or date.today()
    cycle = _trim(data.get("cycle")) or "monthly"
    cycle_days = _as_int(data.get("cycle_days")) if cycle == "custom" else CYCLE_DAYS_MAP.get(cycle, 30)

    p = MaintenancePlan(
        code=code,
        name=name,
        description=_trim(data.get("description")),
        machine_id=machine_id,
        standard_id=_as_int(data.get("standard_id")),
        cycle=cycle,
        cycle_days=cycle_days,
        start_date=start_date,
        end_date=_as_date(data.get("end_date")),
        next_due_date=start_date,
        advance_days=_as_int(data.get("advance_days")) or 3,
        responsible_id=_as_int(data.get("responsible_id")),
        responsible_name=_trim(data.get("responsible_name")),
        is_active=data.get("is_active", True),
        created_by=_as_int(data.get("created_by")),
        created_by_name=_trim(data.get("created_by_name")),
    )

    try:
        db.session.add(p)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(p.to_dict()), 201


@bp.route("/plans/<int:pid>", methods=["PUT"])
@cross_origin()
def update_plan(pid: int):
    """更新保养计划"""
    p = MaintenancePlan.query.get_or_404(pid)
    data = _json()

    # 更新字段
    if "name" in data:
        p.name = _trim(data["name"])
    if "description" in data:
        p.description = _trim(data["description"])
    if "standard_id" in data:
        p.standard_id = _as_int(data["standard_id"])
    if "cycle" in data:
        p.cycle = _trim(data["cycle"])
    if "cycle_days" in data:
        p.cycle_days = _as_int(data["cycle_days"])
    if "start_date" in data:
        p.start_date = _as_date(data["start_date"])
    if "end_date" in data:
        p.end_date = _as_date(data["end_date"])
    if "next_due_date" in data:
        p.next_due_date = _as_date(data["next_due_date"])
    if "advance_days" in data:
        p.advance_days = _as_int(data["advance_days"])
    if "responsible_id" in data:
        p.responsible_id = _as_int(data["responsible_id"])
    if "responsible_name" in data:
        p.responsible_name = _trim(data["responsible_name"])
    if "is_active" in data:
        p.is_active = data["is_active"]

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(p.to_dict())


@bp.route("/plans/<int:pid>", methods=["DELETE"])
@cross_origin()
def delete_plan(pid: int):
    """删除保养计划"""
    p = MaintenancePlan.query.get_or_404(pid)

    try:
        db.session.delete(p)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"ok": True, "id": pid})


@bp.route("/plans/<int:pid>/generate-order", methods=["POST"])
@cross_origin()
def generate_order_from_plan(pid: int):
    """从保养计划生成工单"""
    p = MaintenancePlan.query.get_or_404(pid)
    data = _json()

    planned_date = _as_date(data.get("planned_date")) or p.next_due_date or date.today()

    order = MaintenanceOrder(
        order_no=generate_order_no(),
        title=f"{p.machine.name} - {p.name}",
        description=p.description,
        machine_id=p.machine_id,
        plan_id=p.id,
        standard_id=p.standard_id,
        maintenance_type=p.standard.maintenance_type if p.standard else "preventive",
        source="plan",
        planned_date=planned_date,
        due_date=planned_date + timedelta(days=p.advance_days or 3),
        estimated_hours=p.standard.estimated_hours if p.standard else None,
        assigned_to_id=p.responsible_id,
        assigned_to_name=p.responsible_name,
        check_results=p.standard.check_items if p.standard else [],
        created_by=_as_int(data.get("created_by")),
        created_by_name=_trim(data.get("created_by_name")),
    )

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(order.to_dict()), 201


# ==========================
# 保养工单 API
# ==========================
@bp.route("/orders", methods=["GET"])
@cross_origin()
def list_orders():
    """获取保养工单列表"""
    args = request.args or {}
    page = _as_int(args.get("page")) or 1
    page_size = _as_int(args.get("page_size")) or 20

    query = MaintenanceOrder.query

    # 筛选
    if args.get("keyword"):
        like = f"%{args.get('keyword')}%"
        query = query.filter(or_(
            MaintenanceOrder.order_no.ilike(like),
            MaintenanceOrder.title.ilike(like),
        ))
    if args.get("machine_id"):
        query = query.filter(MaintenanceOrder.machine_id == int(args.get("machine_id")))
    if args.get("status"):
        query = query.filter(MaintenanceOrder.status == args.get("status"))
    if args.get("maintenance_type"):
        query = query.filter(MaintenanceOrder.maintenance_type == args.get("maintenance_type"))
    if args.get("priority"):
        query = query.filter(MaintenanceOrder.priority == args.get("priority"))

    # 日期范围
    if args.get("start_date"):
        query = query.filter(MaintenanceOrder.planned_date >= _as_date(args.get("start_date")))
    if args.get("end_date"):
        query = query.filter(MaintenanceOrder.planned_date <= _as_date(args.get("end_date")))

    # 排序
    sort_by = args.get("sort_by", "planned_date")
    order = args.get("order", "asc")
    if sort_by == "planned_date":
        query = query.order_by(asc(MaintenanceOrder.planned_date) if order == "asc" else desc(MaintenanceOrder.planned_date))
    else:
        query = query.order_by(desc(MaintenanceOrder.created_at))

    # 分页
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [o.to_dict() for o in items],
    })


@bp.route("/orders/<int:oid>", methods=["GET"])
@cross_origin()
def get_order(oid: int):
    """获取保养工单详情"""
    o = MaintenanceOrder.query.get_or_404(oid)
    return jsonify(o.to_dict())


@bp.route("/orders", methods=["POST"])
@cross_origin()
def create_order():
    """创建保养工单"""
    data = _json()

    title = _trim(data.get("title"))
    machine_id = _as_int(data.get("machine_id"))

    if not title:
        return jsonify({"error": "title is required"}), 400
    if not machine_id:
        return jsonify({"error": "machine_id is required"}), 400

    # 验证设备存在
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({"error": "machine not found"}), 404

    o = MaintenanceOrder(
        order_no=generate_order_no(),
        title=title,
        description=_trim(data.get("description")),
        machine_id=machine_id,
        plan_id=_as_int(data.get("plan_id")),
        standard_id=_as_int(data.get("standard_id")),
        maintenance_type=_trim(data.get("maintenance_type")) or "preventive",
        source=_trim(data.get("source")) or "manual",
        planned_date=_as_date(data.get("planned_date")) or date.today(),
        due_date=_as_date(data.get("due_date")),
        estimated_hours=_as_float(data.get("estimated_hours")),
        assigned_to_id=_as_int(data.get("assigned_to_id")),
        assigned_to_name=_trim(data.get("assigned_to_name")),
        priority=_trim(data.get("priority")) or "normal",
        check_results=data.get("check_results") or [],
        remark=_trim(data.get("remark")),
        created_by=_as_int(data.get("created_by")),
        created_by_name=_trim(data.get("created_by_name")),
    )

    try:
        db.session.add(o)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(o.to_dict()), 201


@bp.route("/orders/<int:oid>", methods=["PUT"])
@cross_origin()
def update_order(oid: int):
    """更新保养工单"""
    o = MaintenanceOrder.query.get_or_404(oid)
    data = _json()

    # 更新字段
    if "title" in data:
        o.title = _trim(data["title"])
    if "description" in data:
        o.description = _trim(data["description"])
    if "maintenance_type" in data:
        o.maintenance_type = _trim(data["maintenance_type"])
    if "planned_date" in data:
        o.planned_date = _as_date(data["planned_date"])
    if "due_date" in data:
        o.due_date = _as_date(data["due_date"])
    if "estimated_hours" in data:
        o.estimated_hours = _as_float(data["estimated_hours"])
    if "assigned_to_id" in data:
        o.assigned_to_id = _as_int(data["assigned_to_id"])
    if "assigned_to_name" in data:
        o.assigned_to_name = _trim(data["assigned_to_name"])
    if "priority" in data:
        o.priority = _trim(data["priority"])
    if "check_results" in data:
        o.check_results = data["check_results"]
    if "remark" in data:
        o.remark = _trim(data["remark"])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(o.to_dict())


@bp.route("/orders/<int:oid>", methods=["DELETE"])
@cross_origin()
def delete_order(oid: int):
    """删除保养工单"""
    o = MaintenanceOrder.query.get_or_404(oid)

    # 只能删除待执行的工单
    if o.status not in ("pending", "cancelled"):
        return jsonify({"error": "只能删除待执行或已取消的工单"}), 400

    try:
        db.session.delete(o)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"ok": True, "id": oid})


@bp.route("/orders/<int:oid>/start", methods=["POST"])
@cross_origin()
def start_order(oid: int):
    """开始执行工单"""
    o = MaintenanceOrder.query.get_or_404(oid)
    data = _json()

    if o.status not in ("pending", "overdue"):
        return jsonify({"error": f"当前状态 {o.status} 不能开始执行"}), 400

    o.status = "in_progress"
    o.started_at = datetime.now()
    o.executor_id = _as_int(data.get("executor_id"))
    o.executor_name = _trim(data.get("executor_name"))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(o.to_dict())


@bp.route("/orders/<int:oid>/complete", methods=["POST"])
@cross_origin()
def complete_order(oid: int):
    """完成工单"""
    o = MaintenanceOrder.query.get_or_404(oid)
    data = _json()

    if o.status != "in_progress":
        return jsonify({"error": "只有执行中的工单才能完成"}), 400

    o.status = "completed"
    o.completed_at = datetime.now()
    o.actual_hours = _as_float(data.get("actual_hours"))
    o.check_results = data.get("check_results") or o.check_results
    o.spare_parts_used = data.get("spare_parts_used")
    o.cost = _as_float(data.get("cost")) or 0
    o.remark = _trim(data.get("remark")) or o.remark

    # 更新保养计划的执行日期
    if o.plan_id:
        plan = MaintenancePlan.query.get(o.plan_id)
        if plan:
            plan.last_executed_date = date.today()
            plan.next_due_date = plan.calculate_next_due_date()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(o.to_dict())


@bp.route("/orders/<int:oid>/cancel", methods=["POST"])
@cross_origin()
def cancel_order(oid: int):
    """取消工单"""
    o = MaintenanceOrder.query.get_or_404(oid)
    data = _json()

    if o.status in ("completed",):
        return jsonify({"error": "已完成的工单不能取消"}), 400

    o.status = "cancelled"
    o.remark = _trim(data.get("reason")) or o.remark

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(o.to_dict())


# ==========================
# 故障报修 API
# ==========================
@bp.route("/faults", methods=["GET"])
@cross_origin()
def list_faults():
    """获取故障报修列表"""
    args = request.args or {}
    page = _as_int(args.get("page")) or 1
    page_size = _as_int(args.get("page_size")) or 20

    query = FaultReport.query

    # 筛选
    if args.get("keyword"):
        like = f"%{args.get('keyword')}%"
        query = query.filter(or_(
            FaultReport.report_no.ilike(like),
            FaultReport.title.ilike(like),
            FaultReport.description.ilike(like),
        ))
    if args.get("machine_id"):
        query = query.filter(FaultReport.machine_id == int(args.get("machine_id")))
    if args.get("status"):
        query = query.filter(FaultReport.status == args.get("status"))
    if args.get("severity"):
        query = query.filter(FaultReport.severity == args.get("severity"))
    if args.get("fault_type"):
        query = query.filter(FaultReport.fault_type == args.get("fault_type"))

    # 排序
    query = query.order_by(desc(FaultReport.created_at))

    # 分页
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [f.to_dict() for f in items],
    })


@bp.route("/faults/<int:fid>", methods=["GET"])
@cross_origin()
def get_fault(fid: int):
    """获取故障报修详情"""
    f = FaultReport.query.get_or_404(fid)
    return jsonify(f.to_dict())


@bp.route("/faults", methods=["POST"])
@cross_origin()
def create_fault():
    """创建故障报修"""
    data = _json()

    title = _trim(data.get("title"))
    machine_id = _as_int(data.get("machine_id"))
    description = _trim(data.get("description"))

    if not title:
        return jsonify({"error": "title is required"}), 400
    if not machine_id:
        return jsonify({"error": "machine_id is required"}), 400
    if not description:
        return jsonify({"error": "description is required"}), 400

    # 验证设备存在
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({"error": "machine not found"}), 404

    f = FaultReport(
        report_no=generate_report_no(),
        title=title,
        description=description,
        machine_id=machine_id,
        fault_type=_trim(data.get("fault_type")),
        severity=_trim(data.get("severity")) or "normal",
        fault_time=_as_datetime(data.get("fault_time")) or datetime.now(),
        reporter_id=_as_int(data.get("reporter_id")),
        reporter_name=_trim(data.get("reporter_name")),
        reporter_phone=_trim(data.get("reporter_phone")),
        images=data.get("images") or [],
    )

    # 更新设备状态为维修中
    machine.status = "维修中"

    try:
        db.session.add(f)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(f.to_dict()), 201


@bp.route("/faults/<int:fid>", methods=["PUT"])
@cross_origin()
def update_fault(fid: int):
    """更新故障报修"""
    f = FaultReport.query.get_or_404(fid)
    data = _json()

    if "title" in data:
        f.title = _trim(data["title"])
    if "description" in data:
        f.description = _trim(data["description"])
    if "fault_type" in data:
        f.fault_type = _trim(data["fault_type"])
    if "severity" in data:
        f.severity = _trim(data["severity"])
    if "diagnosis" in data:
        f.diagnosis = _trim(data["diagnosis"])
    if "solution" in data:
        f.solution = _trim(data["solution"])
    if "images" in data:
        f.images = data["images"]

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(f.to_dict())


@bp.route("/faults/<int:fid>/assign", methods=["POST"])
@cross_origin()
def assign_fault(fid: int):
    """指派故障处理人"""
    f = FaultReport.query.get_or_404(fid)
    data = _json()

    if f.status not in ("reported",):
        return jsonify({"error": "只有已报修的故障可以指派"}), 400

    f.status = "assigned"
    f.handler_id = _as_int(data.get("handler_id"))
    f.handler_name = _trim(data.get("handler_name"))
    f.assigned_at = datetime.now()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(f.to_dict())


@bp.route("/faults/<int:fid>/start", methods=["POST"])
@cross_origin()
def start_fault(fid: int):
    """开始处理故障"""
    f = FaultReport.query.get_or_404(fid)
    data = _json()

    if f.status not in ("assigned",):
        return jsonify({"error": "只有已指派的故障可以开始处理"}), 400

    f.status = "in_progress"
    f.started_at = datetime.now()

    # 可以更新处理人
    if data.get("handler_id"):
        f.handler_id = _as_int(data.get("handler_id"))
        f.handler_name = _trim(data.get("handler_name"))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(f.to_dict())


@bp.route("/faults/<int:fid>/complete", methods=["POST"])
@cross_origin()
def complete_fault(fid: int):
    """完成故障处理"""
    f = FaultReport.query.get_or_404(fid)
    data = _json()

    if f.status not in ("in_progress",):
        return jsonify({"error": "只有处理中的故障可以完成"}), 400

    f.status = "completed"
    f.completed_at = datetime.now()
    f.diagnosis = _trim(data.get("diagnosis")) or f.diagnosis
    f.solution = _trim(data.get("solution")) or f.solution
    f.spare_parts_used = data.get("spare_parts_used")
    f.cost = _as_float(data.get("cost")) or 0

    # 计算停机时长
    if f.fault_time and f.completed_at:
        delta = f.completed_at - f.fault_time
        f.downtime_hours = round(delta.total_seconds() / 3600, 2)

    # 更新设备状态为正常
    if f.machine:
        f.machine.status = "正常"

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(f.to_dict())


@bp.route("/faults/<int:fid>/close", methods=["POST"])
@cross_origin()
def close_fault(fid: int):
    """关闭故障报修"""
    f = FaultReport.query.get_or_404(fid)

    if f.status not in ("completed", "reported"):
        return jsonify({"error": "只有已完成或已报修的故障可以关闭"}), 400

    f.status = "closed"
    f.closed_at = datetime.now()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(f.to_dict())


# ==========================
# 点检记录 API
# ==========================
@bp.route("/inspections", methods=["GET"])
@cross_origin()
def list_inspections():
    """获取点检记录列表"""
    args = request.args or {}
    page = _as_int(args.get("page")) or 1
    page_size = _as_int(args.get("page_size")) or 20

    query = InspectionRecord.query

    # 筛选
    if args.get("machine_id"):
        query = query.filter(InspectionRecord.machine_id == int(args.get("machine_id")))
    if args.get("result"):
        query = query.filter(InspectionRecord.result == args.get("result"))
    if args.get("inspector_name"):
        query = query.filter(InspectionRecord.inspector_name.ilike(f"%{args.get('inspector_name')}%"))

    # 日期范围
    if args.get("start_date"):
        query = query.filter(InspectionRecord.inspection_date >= _as_date(args.get("start_date")))
    if args.get("end_date"):
        query = query.filter(InspectionRecord.inspection_date <= _as_date(args.get("end_date")))

    # 排序
    query = query.order_by(desc(InspectionRecord.inspection_date), desc(InspectionRecord.created_at))

    # 分页
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [r.to_dict() for r in items],
    })


@bp.route("/inspections/<int:iid>", methods=["GET"])
@cross_origin()
def get_inspection(iid: int):
    """获取点检记录详情"""
    r = InspectionRecord.query.get_or_404(iid)
    return jsonify(r.to_dict())


@bp.route("/inspections", methods=["POST"])
@cross_origin()
def create_inspection():
    """创建点检记录"""
    data = _json()

    machine_id = _as_int(data.get("machine_id"))
    if not machine_id:
        return jsonify({"error": "machine_id is required"}), 400

    # 验证设备存在
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({"error": "machine not found"}), 404

    r = InspectionRecord(
        record_no=generate_inspection_no(),
        machine_id=machine_id,
        standard_id=_as_int(data.get("standard_id")),
        inspection_date=_as_date(data.get("inspection_date")) or date.today(),
        shift=_trim(data.get("shift")),
        inspector_id=_as_int(data.get("inspector_id")),
        inspector_name=_trim(data.get("inspector_name")),
        result=_trim(data.get("result")) or "normal",
        check_items=data.get("check_items") or [],
        abnormal_items=data.get("abnormal_items") or [],
        remark=_trim(data.get("remark")),
    )

    try:
        db.session.add(r)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(r.to_dict()), 201


@bp.route("/inspections/<int:iid>", methods=["PUT"])
@cross_origin()
def update_inspection(iid: int):
    """更新点检记录"""
    r = InspectionRecord.query.get_or_404(iid)
    data = _json()

    if "inspection_date" in data:
        r.inspection_date = _as_date(data["inspection_date"])
    if "shift" in data:
        r.shift = _trim(data["shift"])
    if "result" in data:
        r.result = _trim(data["result"])
    if "check_items" in data:
        r.check_items = data["check_items"]
    if "abnormal_items" in data:
        r.abnormal_items = data["abnormal_items"]
    if "remark" in data:
        r.remark = _trim(data["remark"])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(r.to_dict())


@bp.route("/inspections/<int:iid>", methods=["DELETE"])
@cross_origin()
def delete_inspection(iid: int):
    """删除点检记录"""
    r = InspectionRecord.query.get_or_404(iid)

    try:
        db.session.delete(r)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"ok": True, "id": iid})


# ==========================
# 统计和日历 API
# ==========================
@bp.route("/calendar", methods=["GET"])
@cross_origin()
def get_calendar():
    """获取维护日历数据"""
    args = request.args or {}

    start_date = _as_date(args.get("start_date")) or date.today().replace(day=1)
    end_date = _as_date(args.get("end_date")) or (start_date + timedelta(days=31))

    # 获取工单
    orders = MaintenanceOrder.query.filter(
        MaintenanceOrder.planned_date.between(start_date, end_date)
    ).all()

    # 获取即将到期的保养计划
    plans = MaintenancePlan.query.filter(
        MaintenancePlan.is_active == True,
        MaintenancePlan.next_due_date.between(start_date, end_date)
    ).all()

    events = []

    for o in orders:
        events.append({
            "id": f"order_{o.id}",
            "type": "order",
            "title": o.title,
            "date": o.planned_date.isoformat(),
            "status": o.status,
            "priority": o.priority,
            "machine_name": o.machine.name if o.machine else None,
        })

    for p in plans:
        # 检查是否已有对应工单
        has_order = any(o.plan_id == p.id and o.planned_date == p.next_due_date for o in orders)
        if not has_order:
            events.append({
                "id": f"plan_{p.id}",
                "type": "plan",
                "title": f"[计划] {p.name}",
                "date": p.next_due_date.isoformat() if p.next_due_date else None,
                "machine_name": p.machine.name if p.machine else None,
            })

    return jsonify({
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "events": events,
    })


@bp.route("/statistics", methods=["GET"])
@cross_origin()
def get_statistics():
    """获取维护统计数据"""
    # 工单统计
    order_stats = db.session.query(
        MaintenanceOrder.status,
        func.count(MaintenanceOrder.id)
    ).group_by(MaintenanceOrder.status).all()

    # 故障统计
    fault_stats = db.session.query(
        FaultReport.status,
        func.count(FaultReport.id)
    ).group_by(FaultReport.status).all()

    # 本月完成工单数
    today = date.today()
    first_day = today.replace(day=1)
    completed_this_month = MaintenanceOrder.query.filter(
        MaintenanceOrder.status == "completed",
        MaintenanceOrder.completed_at >= first_day
    ).count()

    # 逾期工单
    overdue_orders = MaintenanceOrder.query.filter(
        MaintenanceOrder.status.in_(["pending", "in_progress"]),
        MaintenanceOrder.due_date < today
    ).count()

    # 即将到期的计划（7天内）
    upcoming_plans = MaintenancePlan.query.filter(
        MaintenancePlan.is_active == True,
        MaintenancePlan.next_due_date.between(today, today + timedelta(days=7))
    ).count()

    return jsonify({
        "order_stats": {s: c for s, c in order_stats},
        "fault_stats": {s: c for s, c in fault_stats},
        "completed_this_month": completed_this_month,
        "overdue_orders": overdue_orders,
        "upcoming_plans": upcoming_plans,
    })


@bp.route("/overdue", methods=["GET"])
@cross_origin()
def get_overdue():
    """获取逾期保养列表"""
    today = date.today()

    # 逾期工单
    overdue_orders = MaintenanceOrder.query.filter(
        MaintenanceOrder.status.in_(["pending"]),
        MaintenanceOrder.due_date < today
    ).all()

    # 逾期计划
    overdue_plans = MaintenancePlan.query.filter(
        MaintenancePlan.is_active == True,
        MaintenancePlan.next_due_date < today
    ).all()

    return jsonify({
        "orders": [o.to_dict() for o in overdue_orders],
        "plans": [p.to_dict() for p in overdue_plans],
    })
