# -*- coding: utf-8 -*-
# app/routes/capacity.py
"""
设备产能配置 API 路由
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from sqlalchemy import or_, desc, asc, func

from .. import db
from ..models.machine import Machine
from ..models.capacity import (
    CapacityConfig, CapacityAdjustment, CapacityLog,
    ShiftType, AdjustmentType, CapacityStatus,
    SHIFT_TYPE_LABELS, ADJUSTMENT_TYPE_LABELS, CAPACITY_STATUS_LABELS,
    generate_config_code, generate_adjustment_code
)

bp = Blueprint("capacity", __name__, url_prefix="/api/capacity")


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


def _as_bool(v: Any) -> Optional[bool]:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).lower()
    if s in ("1", "true", "t", "yes", "y", "on"):
        return True
    if s in ("0", "false", "f", "no", "n", "off"):
        return False
    return None


def _get_user_info() -> tuple:
    """从请求头获取用户信息"""
    user_id = request.headers.get('User-ID')
    user_name = request.headers.get('User-Name', '')
    try:
        user_id = int(user_id) if user_id else None
    except:
        user_id = None
    return user_id, user_name


# ==========================
# 产能配置 API
# ==========================

@bp.route("/configs", methods=["GET"])
@cross_origin()
def list_configs():
    """获取产能配置列表"""
    args = request.args or {}
    page = _as_int(args.get("page")) or 1
    page_size = _as_int(args.get("page_size")) or 10

    # 筛选条件
    machine_id = _as_int(args.get("machine_id"))
    shift_type = _trim(args.get("shift_type"))
    status = _trim(args.get("status"))
    keyword = _trim(args.get("keyword") or args.get("q"))

    query = CapacityConfig.query

    if machine_id:
        query = query.filter(CapacityConfig.machine_id == machine_id)
    if shift_type:
        query = query.filter(CapacityConfig.shift_type == shift_type)
    if status:
        query = query.filter(CapacityConfig.status == status)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(
            CapacityConfig.config_code.ilike(like),
            CapacityConfig.machine_code.ilike(like),
            CapacityConfig.machine_name.ilike(like),
            CapacityConfig.product_type.ilike(like),
        ))

    # 排序
    sort_by = args.get("sort_by", "created_at")
    order = args.get("order", "desc").lower()
    sortable = {
        "created_at": CapacityConfig.created_at,
        "config_code": CapacityConfig.config_code,
        "machine_name": CapacityConfig.machine_name,
        "standard_capacity": CapacityConfig.standard_capacity,
    }
    col = sortable.get(sort_by, CapacityConfig.created_at)
    query = query.order_by(asc(col) if order == "asc" else desc(col))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [c.to_dict() for c in items],
    })


@bp.route("/configs/<int:config_id>", methods=["GET"])
@cross_origin()
def get_config(config_id: int):
    """获取产能配置详情"""
    config = CapacityConfig.query.get_or_404(config_id)
    return jsonify(config.to_dict())


@bp.route("/configs", methods=["POST"])
@cross_origin()
def create_config():
    """创建产能配置"""
    data = _json()
    machine_id = _as_int(data.get("machine_id"))
    if not machine_id:
        return jsonify({"error": "machine_id is required"}), 400

    # 获取设备信息
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({"error": "Machine not found"}), 404

    user_id, user_name = _get_user_info()

    config = CapacityConfig(
        config_code=generate_config_code(),
        machine_id=machine_id,
        machine_code=machine.machine_code,
        machine_name=machine.name,
        shift_type=_trim(data.get("shift_type")) or ShiftType.ALL.value,
        standard_capacity=_as_int(data.get("standard_capacity")) or 0,
        max_capacity=_as_int(data.get("max_capacity")) or 0,
        min_capacity=_as_int(data.get("min_capacity")) or 0,
        working_hours=_as_float(data.get("working_hours")) or 8.0,
        setup_time=_as_float(data.get("setup_time")) or 0,
        cycle_time=_as_float(data.get("cycle_time")) or 0,
        product_type=_trim(data.get("product_type")),
        product_code=_trim(data.get("product_code")),
        effective_from=_as_date(data.get("effective_from")),
        effective_to=_as_date(data.get("effective_to")),
        status=CapacityStatus.DRAFT.value,
        is_default=_as_bool(data.get("is_default")) or False,
        remarks=_trim(data.get("remarks")),
        created_by=user_id,
        created_by_name=user_name,
    )

    try:
        db.session.add(config)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    return jsonify(config.to_dict()), 201


@bp.route("/configs/<int:config_id>", methods=["PUT"])
@cross_origin()
def update_config(config_id: int):
    """更新产能配置"""
    config = CapacityConfig.query.get_or_404(config_id)
    data = _json()

    # 更新字段
    if "shift_type" in data:
        config.shift_type = _trim(data["shift_type"])
    if "standard_capacity" in data:
        config.standard_capacity = _as_int(data["standard_capacity"]) or 0
    if "max_capacity" in data:
        config.max_capacity = _as_int(data["max_capacity"]) or 0
    if "min_capacity" in data:
        config.min_capacity = _as_int(data["min_capacity"]) or 0
    if "working_hours" in data:
        config.working_hours = _as_float(data["working_hours"]) or 8.0
    if "setup_time" in data:
        config.setup_time = _as_float(data["setup_time"]) or 0
    if "cycle_time" in data:
        config.cycle_time = _as_float(data["cycle_time"]) or 0
    if "product_type" in data:
        config.product_type = _trim(data["product_type"])
    if "product_code" in data:
        config.product_code = _trim(data["product_code"])
    if "effective_from" in data:
        config.effective_from = _as_date(data["effective_from"])
    if "effective_to" in data:
        config.effective_to = _as_date(data["effective_to"])
    if "is_default" in data:
        config.is_default = _as_bool(data["is_default"]) or False
    if "remarks" in data:
        config.remarks = _trim(data["remarks"])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    return jsonify(config.to_dict())


@bp.route("/configs/<int:config_id>", methods=["DELETE"])
@cross_origin()
def delete_config(config_id: int):
    """删除产能配置"""
    config = CapacityConfig.query.get_or_404(config_id)

    if config.status == CapacityStatus.ACTIVE.value:
        return jsonify({"error": "Cannot delete active config"}), 400

    try:
        db.session.delete(config)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    return jsonify({"ok": True, "id": config_id})


@bp.route("/configs/<int:config_id>/activate", methods=["POST"])
@cross_origin()
def activate_config(config_id: int):
    """激活产能配置"""
    config = CapacityConfig.query.get_or_404(config_id)

    if config.status == CapacityStatus.ACTIVE.value:
        return jsonify({"error": "Already active"}), 400

    # 如果设为默认，取消同设备其他默认配置
    if config.is_default:
        CapacityConfig.query.filter(
            CapacityConfig.machine_id == config.machine_id,
            CapacityConfig.id != config_id,
            CapacityConfig.is_default == True
        ).update({"is_default": False})

    config.status = CapacityStatus.ACTIVE.value

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    return jsonify(config.to_dict())


@bp.route("/configs/<int:config_id>/deactivate", methods=["POST"])
@cross_origin()
def deactivate_config(config_id: int):
    """停用产能配置"""
    config = CapacityConfig.query.get_or_404(config_id)
    config.status = CapacityStatus.INACTIVE.value

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    return jsonify(config.to_dict())


@bp.route("/configs/by-machine/<int:machine_id>", methods=["GET"])
@cross_origin()
def get_configs_by_machine(machine_id: int):
    """获取设备的产能配置列表"""
    configs = CapacityConfig.query.filter(
        CapacityConfig.machine_id == machine_id
    ).order_by(CapacityConfig.is_default.desc(), CapacityConfig.created_at.desc()).all()
    return jsonify({"list": [c.to_dict() for c in configs]})


@bp.route("/configs/current/<int:machine_id>", methods=["GET"])
@cross_origin()
def get_current_config(machine_id: int):
    """获取设备当前生效的产能配置"""
    today = date.today()

    # 查找有效配置（考虑日期范围和状态）
    config = CapacityConfig.query.filter(
        CapacityConfig.machine_id == machine_id,
        CapacityConfig.status == CapacityStatus.ACTIVE.value,
        or_(
            CapacityConfig.effective_from == None,
            CapacityConfig.effective_from <= today
        ),
        or_(
            CapacityConfig.effective_to == None,
            CapacityConfig.effective_to >= today
        )
    ).order_by(CapacityConfig.is_default.desc()).first()

    if not config:
        return jsonify({"error": "No active config found"}), 404

    # 检查是否有调整
    adjustment = CapacityAdjustment.query.filter(
        CapacityAdjustment.machine_id == machine_id,
        CapacityAdjustment.is_active == True,
        CapacityAdjustment.effective_from <= today,
        or_(
            CapacityAdjustment.effective_to == None,
            CapacityAdjustment.effective_to >= today
        )
    ).first()

    result = config.to_dict()
    if adjustment:
        result["adjusted"] = True
        result["adjustment"] = adjustment.to_dict()
        result["effective_capacity"] = adjustment.adjusted_capacity
    else:
        result["adjusted"] = False
        result["effective_capacity"] = config.standard_capacity

    return jsonify(result)


# ==========================
# 产能调整 API
# ==========================

@bp.route("/adjustments", methods=["GET"])
@cross_origin()
def list_adjustments():
    """获取产能调整列表"""
    args = request.args or {}
    page = _as_int(args.get("page")) or 1
    page_size = _as_int(args.get("page_size")) or 10

    machine_id = _as_int(args.get("machine_id"))
    adjustment_type = _trim(args.get("adjustment_type"))
    is_active = _as_bool(args.get("is_active"))

    query = CapacityAdjustment.query

    if machine_id:
        query = query.filter(CapacityAdjustment.machine_id == machine_id)
    if adjustment_type:
        query = query.filter(CapacityAdjustment.adjustment_type == adjustment_type)
    if is_active is not None:
        query = query.filter(CapacityAdjustment.is_active == is_active)

    query = query.order_by(CapacityAdjustment.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [a.to_dict() for a in items],
    })


@bp.route("/adjustments", methods=["POST"])
@cross_origin()
def create_adjustment():
    """创建产能调整"""
    data = _json()
    machine_id = _as_int(data.get("machine_id"))
    if not machine_id:
        return jsonify({"error": "machine_id is required"}), 400

    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({"error": "Machine not found"}), 404

    user_id, user_name = _get_user_info()

    original_capacity = _as_int(data.get("original_capacity")) or 0
    adjusted_capacity = _as_int(data.get("adjusted_capacity")) or 0

    # 计算调整比例
    adjustment_rate = None
    if original_capacity > 0:
        adjustment_rate = round((adjusted_capacity - original_capacity) / original_capacity * 100, 2)

    adjustment = CapacityAdjustment(
        adjustment_code=generate_adjustment_code(),
        machine_id=machine_id,
        machine_code=machine.machine_code,
        machine_name=machine.name,
        config_id=_as_int(data.get("config_id")),
        adjustment_type=_trim(data.get("adjustment_type")) or AdjustmentType.TEMPORARY.value,
        reason=_trim(data.get("reason")),
        original_capacity=original_capacity,
        adjusted_capacity=adjusted_capacity,
        adjustment_rate=adjustment_rate,
        effective_from=_as_date(data.get("effective_from")) or date.today(),
        effective_to=_as_date(data.get("effective_to")),
        is_active=True,
        created_by=user_id,
        created_by_name=user_name,
    )

    try:
        db.session.add(adjustment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    return jsonify(adjustment.to_dict()), 201


@bp.route("/adjustments/<int:adj_id>", methods=["DELETE"])
@cross_origin()
def delete_adjustment(adj_id: int):
    """删除/取消产能调整"""
    adjustment = CapacityAdjustment.query.get_or_404(adj_id)
    adjustment.is_active = False

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    return jsonify({"ok": True, "id": adj_id})


# ==========================
# 产能日志 API
# ==========================

@bp.route("/logs", methods=["GET"])
@cross_origin()
def list_logs():
    """获取产能日志列表"""
    args = request.args or {}
    page = _as_int(args.get("page")) or 1
    page_size = _as_int(args.get("page_size")) or 10

    machine_id = _as_int(args.get("machine_id"))
    date_from = _as_date(args.get("date_from"))
    date_to = _as_date(args.get("date_to"))
    shift_type = _trim(args.get("shift_type"))

    query = CapacityLog.query

    if machine_id:
        query = query.filter(CapacityLog.machine_id == machine_id)
    if date_from:
        query = query.filter(CapacityLog.log_date >= date_from)
    if date_to:
        query = query.filter(CapacityLog.log_date <= date_to)
    if shift_type:
        query = query.filter(CapacityLog.shift_type == shift_type)

    query = query.order_by(CapacityLog.log_date.desc(), CapacityLog.shift_type)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": [log.to_dict() for log in items],
    })


@bp.route("/logs", methods=["POST"])
@cross_origin()
def create_log():
    """创建/更新产能日志"""
    data = _json()
    machine_id = _as_int(data.get("machine_id"))
    log_date = _as_date(data.get("log_date"))
    shift_type = _trim(data.get("shift_type")) or ShiftType.ALL.value

    if not machine_id:
        return jsonify({"error": "machine_id is required"}), 400
    if not log_date:
        return jsonify({"error": "log_date is required"}), 400

    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({"error": "Machine not found"}), 404

    # 查找是否已存在记录（同设备、同日期、同班次）
    log = CapacityLog.query.filter(
        CapacityLog.machine_id == machine_id,
        CapacityLog.log_date == log_date,
        CapacityLog.shift_type == shift_type
    ).first()

    user_id, user_name = _get_user_info()

    if log:
        # 更新
        log.planned_capacity = _as_int(data.get("planned_capacity")) or log.planned_capacity
        log.actual_output = _as_int(data.get("actual_output")) or log.actual_output
        log.defective_count = _as_int(data.get("defective_count")) or 0
        log.downtime_minutes = _as_int(data.get("downtime_minutes")) or 0
        log.downtime_reason = _trim(data.get("downtime_reason"))
        log.remarks = _trim(data.get("remarks"))
    else:
        # 创建
        log = CapacityLog(
            machine_id=machine_id,
            machine_code=machine.machine_code,
            machine_name=machine.name,
            log_date=log_date,
            shift_type=shift_type,
            planned_capacity=_as_int(data.get("planned_capacity")) or 0,
            actual_output=_as_int(data.get("actual_output")) or 0,
            defective_count=_as_int(data.get("defective_count")) or 0,
            downtime_minutes=_as_int(data.get("downtime_minutes")) or 0,
            downtime_reason=_trim(data.get("downtime_reason")),
            remarks=_trim(data.get("remarks")),
            recorded_by=user_id,
            recorded_by_name=user_name,
        )
        db.session.add(log)

    # 计算效率指标
    log.calculate_rates()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    return jsonify(log.to_dict()), 201 if not log.id else 200


@bp.route("/logs/<int:log_id>", methods=["DELETE"])
@cross_origin()
def delete_log(log_id: int):
    """删除产能日志"""
    log = CapacityLog.query.get_or_404(log_id)

    try:
        db.session.delete(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    return jsonify({"ok": True, "id": log_id})


# ==========================
# 统计 API
# ==========================

@bp.route("/statistics/summary", methods=["GET"])
@cross_origin()
def statistics_summary():
    """产能统计概览"""
    args = request.args or {}
    machine_id = _as_int(args.get("machine_id"))
    date_from = _as_date(args.get("date_from"))
    date_to = _as_date(args.get("date_to"))

    # 默认最近30天
    if not date_to:
        date_to = date.today()
    if not date_from:
        from datetime import timedelta
        date_from = date_to - timedelta(days=30)

    query = CapacityLog.query.filter(
        CapacityLog.log_date >= date_from,
        CapacityLog.log_date <= date_to
    )
    if machine_id:
        query = query.filter(CapacityLog.machine_id == machine_id)

    logs = query.all()

    if not logs:
        return jsonify({
            "total_planned": 0,
            "total_output": 0,
            "total_good": 0,
            "total_defective": 0,
            "avg_utilization": 0,
            "avg_yield": 0,
            "avg_oee": 0,
            "total_downtime": 0,
            "record_count": 0,
        })

    total_planned = sum(l.planned_capacity or 0 for l in logs)
    total_output = sum(l.actual_output or 0 for l in logs)
    total_good = sum(l.good_count or 0 for l in logs)
    total_defective = sum(l.defective_count or 0 for l in logs)
    total_downtime = sum(l.downtime_minutes or 0 for l in logs)

    avg_utilization = round(total_output / total_planned * 100, 2) if total_planned > 0 else 0
    avg_yield = round(total_good / total_output * 100, 2) if total_output > 0 else 0
    avg_oee = round(avg_utilization * avg_yield / 100, 2) if avg_utilization and avg_yield else 0

    return jsonify({
        "total_planned": total_planned,
        "total_output": total_output,
        "total_good": total_good,
        "total_defective": total_defective,
        "avg_utilization": avg_utilization,
        "avg_yield": avg_yield,
        "avg_oee": avg_oee,
        "total_downtime": total_downtime,
        "record_count": len(logs),
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    })


@bp.route("/statistics/by-machine", methods=["GET"])
@cross_origin()
def statistics_by_machine():
    """按设备统计产能"""
    args = request.args or {}
    date_from = _as_date(args.get("date_from"))
    date_to = _as_date(args.get("date_to"))

    if not date_to:
        date_to = date.today()
    if not date_from:
        from datetime import timedelta
        date_from = date_to - timedelta(days=30)

    results = db.session.query(
        CapacityLog.machine_id,
        CapacityLog.machine_code,
        CapacityLog.machine_name,
        func.sum(CapacityLog.planned_capacity).label('total_planned'),
        func.sum(CapacityLog.actual_output).label('total_output'),
        func.sum(CapacityLog.good_count).label('total_good'),
        func.sum(CapacityLog.defective_count).label('total_defective'),
        func.sum(CapacityLog.downtime_minutes).label('total_downtime'),
        func.count(CapacityLog.id).label('record_count'),
    ).filter(
        CapacityLog.log_date >= date_from,
        CapacityLog.log_date <= date_to
    ).group_by(
        CapacityLog.machine_id,
        CapacityLog.machine_code,
        CapacityLog.machine_name
    ).all()

    data = []
    for r in results:
        total_planned = r.total_planned or 0
        total_output = r.total_output or 0
        total_good = r.total_good or 0

        utilization = round(total_output / total_planned * 100, 2) if total_planned > 0 else 0
        yield_rate = round(total_good / total_output * 100, 2) if total_output > 0 else 0
        oee = round(utilization * yield_rate / 100, 2) if utilization and yield_rate else 0

        data.append({
            "machine_id": r.machine_id,
            "machine_code": r.machine_code,
            "machine_name": r.machine_name,
            "total_planned": total_planned,
            "total_output": total_output,
            "total_good": total_good,
            "total_defective": r.total_defective or 0,
            "total_downtime": r.total_downtime or 0,
            "record_count": r.record_count,
            "utilization_rate": utilization,
            "yield_rate": yield_rate,
            "oee": oee,
        })

    # 按 OEE 排序
    data.sort(key=lambda x: x["oee"], reverse=True)

    return jsonify({
        "list": data,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    })


@bp.route("/statistics/trend", methods=["GET"])
@cross_origin()
def statistics_trend():
    """产能趋势（按日期）"""
    args = request.args or {}
    machine_id = _as_int(args.get("machine_id"))
    date_from = _as_date(args.get("date_from"))
    date_to = _as_date(args.get("date_to"))

    if not date_to:
        date_to = date.today()
    if not date_from:
        from datetime import timedelta
        date_from = date_to - timedelta(days=30)

    query = db.session.query(
        CapacityLog.log_date,
        func.sum(CapacityLog.planned_capacity).label('planned'),
        func.sum(CapacityLog.actual_output).label('output'),
        func.sum(CapacityLog.good_count).label('good'),
    ).filter(
        CapacityLog.log_date >= date_from,
        CapacityLog.log_date <= date_to
    )

    if machine_id:
        query = query.filter(CapacityLog.machine_id == machine_id)

    results = query.group_by(CapacityLog.log_date).order_by(CapacityLog.log_date).all()

    data = []
    for r in results:
        planned = r.planned or 0
        output = r.output or 0
        good = r.good or 0
        utilization = round(output / planned * 100, 2) if planned > 0 else 0
        yield_rate = round(good / output * 100, 2) if output > 0 else 0

        data.append({
            "date": r.log_date.isoformat(),
            "planned": planned,
            "output": output,
            "good": good,
            "utilization_rate": utilization,
            "yield_rate": yield_rate,
        })

    return jsonify({
        "list": data,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    })


@bp.route("/enums", methods=["GET"])
@cross_origin()
def get_enums():
    """获取枚举值"""
    return jsonify({
        "shift_types": [{"value": k, "label": v} for k, v in SHIFT_TYPE_LABELS.items()],
        "adjustment_types": [{"value": k, "label": v} for k, v in ADJUSTMENT_TYPE_LABELS.items()],
        "capacity_statuses": [{"value": k, "label": v} for k, v in CAPACITY_STATUS_LABELS.items()],
    })
