# backend/app/routes/customers.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import json, traceback

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import or_, case
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError, ProgrammingError

from .. import db
from ..models.customer import Customer

bp = Blueprint("customers", __name__, url_prefix="/api/customers")

# ---------- helpers ----------
def _s(v) -> str:
    return (str(v).strip() if v is not None else "")

def _i(v, default=None):
    try:
        if v is None or v == "":
            return default
        return int(v)
    except Exception:
        return default

def _b(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y", "on"}

def _parse_contacts(v):
    """contacts 可为 list / JSON 字符串 / 逗号分割字符串，统一转成 list[dict]."""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        # 尝试 JSON
        try:
            j = json.loads(s)
            if isinstance(j, list):
                return j
        except Exception:
            pass
        # 尝试用逗号分割成简单 name 列表
        parts = [p.strip() for p in s.split(",") if p.strip()]
        return [{"name": p} for p in parts]
    return []

# 允许的字段（避免 set 任意属性）
_ALLOWED_FIELDS = {
    "code","short_name","name",
    "currency_default","tax_points","settlement_cycle_days","settlement_method","statement_day",
    "address","remark","contacts",
    "shipping_method","need_customs","order_method","delivery_requirements","delivery_address",
    "order_status_desc","sample_dev_desc","has_price_drop_contact",
}

def _coerce_row(d: Dict[str, Any]) -> Dict[str, Any]:
    """把一行导入数据做容错与字段映射 + 兜底。"""
    code = _s(d.get("code") or d.get("客户代码") or d.get("CODE"))
    short_name = _s(d.get("short_name") or d.get("简称") or d.get("客户简称") or d.get("SHORT_NAME"))
    name = _s(d.get("name") or d.get("客户全称") or d.get("NAME") or short_name or code)

    if not short_name and name:
        short_name = name
    if not code and (short_name or name):
        code = short_name or name

    out = {
        "code": code or None,
        "short_name": short_name or None,
        "name": name or None,

        "currency_default": _s(d.get("currency_default") or d.get("默认币种") or d.get("currency") or d.get("币种")) or None,
        "tax_points": _i(d.get("tax_points") or d.get("含税点数")),
        "settlement_cycle_days": _i(d.get("settlement_cycle_days") or d.get("结算周期（天）") or d.get("结算周期")),
        "settlement_method": _s(d.get("settlement_method") or d.get("结算方式")) or None,
        "statement_day": _i(d.get("statement_day") or d.get("对账日期")),

        "address": _s(d.get("address") or d.get("公司地址")) or None,
        "remark": _s(d.get("remark") or d.get("备注")) or None,
        "contacts": _parse_contacts(d.get("contacts") or d.get("联系人")),

        "shipping_method": _s(d.get("shipping_method") or d.get("出货方式")) or None,
        "need_customs": _b(d.get("need_customs") or d.get("是否报关")),
        "order_method": _s(d.get("order_method") or d.get("接单方式")) or None,
        "delivery_requirements": _s(d.get("delivery_requirements") or d.get("送货要求")) or None,
        "delivery_address": _s(d.get("delivery_address") or d.get("送货地址")) or None,
        "order_status_desc": _s(d.get("order_status_desc") or d.get("目前订单情况")) or None,
        "sample_dev_desc": _s(d.get("sample_dev_desc") or d.get("样品和开发情况")) or None,
        "has_price_drop_contact": _b(d.get("has_price_drop_contact") or d.get("是否有降价联系")),
    }
    return {k: v for k, v in out.items() if k in _ALLOWED_FIELDS}

def _apply_to_model(obj: Customer, data: Dict[str, Any]) -> None:
    for k, v in data.items():
        if k not in _ALLOWED_FIELDS:  # 双保险
            continue
        if k == "contacts":
            obj.contacts = _parse_contacts(v)
        elif k in {"tax_points","settlement_cycle_days","statement_day"}:
            setattr(obj, k, _i(v))
        elif k in {"need_customs","has_price_drop_contact"}:
            setattr(obj, k, _b(v))
        else:
            setattr(obj, k, (v or None) if isinstance(v, str) else v)

def _find_existing(code: str | None, name: str | None, short_name: str | None = None) -> Customer | None:
    """允许按 code/name/short_name 任一命中视为存在。"""
    q = Customer.query
    conds = []
    if code:
        conds.append(Customer.code == code)
    if name:
        conds.append(Customer.name == name)
    if short_name:
        conds.append(Customer.short_name == short_name)
    if not conds:
        return None
    return q.filter(or_(*conds)).first()

def _merge_non_empty(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    """
    把 src 中"有值"的字段合并到 dst：
    - 若 dst[k] 为空(None/''/[])且 src[k] 有值，则写入
    - 如需"后者覆盖前者"，改为：dst[k] = src[k]（当 src[k] is not None）
    """
    for k in _ALLOWED_FIELDS:
        if k not in src:
            continue
        sv = src[k]
        dv = dst.get(k)
        empty = (dv is None) or (isinstance(dv, str) and dv.strip() == "") or (isinstance(dv, list) and len(dv) == 0)
        if empty and sv not in (None, ""):
            dst[k] = sv
    return dst

def _norm_key(d: Dict[str, Any]) -> Tuple[str, str, str]:
    """用于批内去重的 key（三元组）：(code, name, short_name)"""
    return (_s(d.get("code")), _s(d.get("name")), _s(d.get("short_name")))

def _clip_to_column_lengths(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据 SQLAlchemy 模型列长度，自动截断字符串，避免 DataError/ProgrammingError（字符串过长）。
    未声明长度的 String/JSON 列不截断。
    """
    cols = Customer.__table__.columns
    out = dict(data)
    for c in cols:
        name = c.name
        if name not in out:
            continue
        val = out[name]
        # String 列有 length 的情况
        try:
            from sqlalchemy import String
            if hasattr(c.type, "length") and isinstance(c.type, String) and c.type.length and isinstance(val, str):
                if len(val) > c.type.length:
                    out[name] = val[: c.type.length]
        except Exception:
            pass
        # JSON 列如果传来的是字符串，尝试解析；如果解析失败，给默认 []
        if c.type.__class__.__name__.lower() == "json" and isinstance(val, str):
            try:
                parsed = json.loads(val)
                out[name] = parsed
            except Exception:
                out[name] = []
    # 数值型兜底：空字符串 -> None
    for k in ("tax_points", "settlement_cycle_days", "statement_day"):
        if k in out and out[k] == "":
            out[k] = None
    # 布尔型兜底：字符串 -> 布尔
    for k in ("need_customs", "has_price_drop_contact"):
        if k in out and not isinstance(out[k], bool):
            out[k] = _b(out[k])
    # contacts 兜底
    if "contacts" in out:
        out["contacts"] = _parse_contacts(out["contacts"])
    return out

def _sanitize_for_model(data: Dict[str, Any]) -> Dict[str, Any]:
    """按模型预期再做一次兜底，避免触发 @validates 的 ValueError。"""
    out = dict(data)

    def _nzint_nonneg(v):
        if v in (None, ""):
            return None
        try:
            iv = int(v)
            return iv if iv >= 0 else None
        except Exception:
            return None

    out["tax_points"] = _nzint_nonneg(out.get("tax_points"))
    out["settlement_cycle_days"] = _nzint_nonneg(out.get("settlement_cycle_days"))

    # 对账日通常 1~31（也可能 None）
    sd = _nzint_nonneg(out.get("statement_day"))
    if sd is not None:
        if not (1 <= sd <= 31):
            sd = None
    out["statement_day"] = sd

    # 布尔
    for k in ("need_customs", "has_price_drop_contact"):
        if k in out:
            out[k] = _b(out.get(k))

    # contacts 规范为 list[dict]
    if "contacts" in out:
        out["contacts"] = _parse_contacts(out.get("contacts"))

    return out

# ---------- list (GET) ----------
@bp.get("")
def list_customers():
    page = _i(request.args.get("page"), 1) or 1
    page_size = max(1, min(_i(request.args.get("page_size"), 20) or 20, 200))
    keyword = _s(request.args.get("keyword"))

    q = Customer.query
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(
            Customer.code.like(like),
            Customer.short_name.like(like),
            Customer.name.like(like),
        ))

    total = q.count()
    # 按seq_no升序排列（Excel导入顺序），没有seq_no的排在最后（MySQL兼容）
    items = q.order_by(case((Customer.seq_no.is_(None), 1), else_=0), Customer.seq_no.asc(), Customer.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({"success": True, "data": {
        "items": [c.to_dict() for c in items],
        "total": total, "page": page, "page_size": page_size
    }})

# ---------- 兼容的 POST list/search/query ----------
def _post_list_like():
    data = request.get_json(silent=True) or {}
    page = _i(data.get("page"), 1) or 1
    page_size = max(1, min(_i(data.get("page_size"), 20) or 20, 200))
    keyword = _s(data.get("keyword"))

    q = Customer.query
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(
            Customer.code.like(like),
            Customer.short_name.like(like),
            Customer.name.like(like),
        ))

    total = q.count()
    # 按seq_no升序排列（Excel导入顺序），没有seq_no的排在最后（MySQL兼容）
    items = q.order_by(case((Customer.seq_no.is_(None), 1), else_=0), Customer.seq_no.asc(), Customer.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({"success": True, "data": {
        "items": [c.to_dict() for c in items],
        "total": total, "page": page, "page_size": page_size
    }})

@bp.post("/list")
def list_customers_post():
    return _post_list_like()

@bp.post("/search")
def search_customers_post():
    return _post_list_like()

@bp.post("/query")
def query_customers_post():
    return _post_list_like()

# ---------- detail ----------
@bp.get("/<int:cid>")
def get_customer(cid: int):
    c = Customer.query.get(cid)
    if not c:
        return jsonify({"success": False, "error": "Not Found"}), 404
    return jsonify({"success": True, "data": c.to_dict()})

# ---------- create / bulk upsert（安全导入：逐条 savepoint + flush） ----------
@bp.post("")
def create_or_import_customers():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"success": False, "error": "Invalid JSON body"}), 400

    # 兼容外层 data 包裹
    if isinstance(payload, dict) and "data" in payload and not isinstance(payload.get("items"), list):
        payload = payload.get("data")

    # 兼容三种：list / {items:list} / 单条 dict
    if isinstance(payload, list):
        raw_rows = payload
    elif isinstance(payload, dict):
        raw_rows = payload.get("items") if isinstance(payload.get("items"), list) else [payload]
    else:
        return jsonify({"success": False, "error": "Unsupported payload type"}), 400

    # 1) 预清洗 + 批内聚合（去重合并）
    merged_by_key: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    codes, names, shorts = set(), set(), set()

    for r in raw_rows:
        if not isinstance(r, dict):
            continue
        d = _coerce_row(r)

        code = d.get("code")
        name = d.get("name")
        short_name = d.get("short_name")
        if not (code or name or short_name):
            # 没有主字段，跳过
            continue

        if not code:
            d["code"] = code = short_name or name
        if not short_name:
            d["short_name"] = short_name = name or code
        if not name:
            d["name"] = name = short_name or code

        # 按模型列长度裁剪 + 类型/范围兜底
        d = _clip_to_column_lengths(d)
        d = _sanitize_for_model(d)

        k = _norm_key(d)
        if k in merged_by_key:
            _merge_non_empty(merged_by_key[k], d)   # 只填补空字段；如需后者覆盖，请改策略
        else:
            merged_by_key[k] = {kk: vv for kk, vv in d.items() if kk in _ALLOWED_FIELDS}

        if code: codes.add(code)
        if name: names.add(name)
        if short_name: shorts.add(short_name)

    rows = list(merged_by_key.values())
    if not rows:
        return jsonify({"success": True, "data": {
            "created_count": 0, "updated_count": 0, "skipped_count": 0,
            "items": [], "errors": []
        }})

    # 2) 一次预取数据库中已存在的（按 code/name/short_name 其一）
    existing = []
    if codes or names or shorts:
        q = Customer.query
        conds = []
        if codes:
            conds.append(Customer.code.in_(list(codes)))
        if names:
            conds.append(Customer.name.in_(list(names)))
        if shorts:
            conds.append(Customer.short_name.in_(list(shorts)))
        existing = q.filter(or_(*conds)).all()

    # 3) 建映射（已存在 + 本批将创建），保证同批次重复 upsert 到同一对象
    by_code: Dict[str, Customer] = {}
    by_name: Dict[str, Customer] = {}
    by_short: Dict[str, Customer] = {}
    for c in existing:
        if c.code: by_code[c.code] = c
        if c.name: by_name[c.name] = c
        if c.short_name: by_short[c.short_name] = c

    created: List[Customer] = []
    updated: List[Customer] = []
    errors: List[Dict[str, Any]] = []

    # 4) 安全导入：逐条 savepoint + flush（单条失败不影响其它）
    for idx, d in enumerate(rows):
        # 再保险：按列长度裁剪 + 类型/范围兜底，避免触发 @validates
        d = _clip_to_column_lengths(d)
        d = _sanitize_for_model(d)

        code = d.get("code")
        name = d.get("name")
        short_name = d.get("short_name")

        # 命中目标
        target = None
        if code and code in by_code:
            target = by_code[code]
        elif name and name in by_name:
            target = by_name[name]
        elif short_name and short_name in by_short:
            target = by_short[short_name]

        try:
            with db.session.begin_nested():  # SAVEPOINT
                if target:
                    _apply_to_model(target, d)
                    db.session.flush()  # 当场发现类型/长度/唯一键/validators 问题
                    if target not in updated and target not in created:
                        updated.append(target)
                else:
                    obj = Customer()
                    _apply_to_model(obj, d)
                    db.session.add(obj)
                    db.session.flush()
                    created.append(obj)
                    # 放入映射，供本批后续命中
                    if obj.code: by_code[obj.code] = obj
                    if obj.name: by_name[obj.name] = obj
                    if obj.short_name: by_short[obj.short_name] = obj

        except (IntegrityError, DataError, ProgrammingError) as e:
            errors.append({
                "index": idx,
                "error": e.__class__.__name__,
                "detail": str(getattr(e, "orig", e)),
                "sample": {k: d.get(k) for k in sorted(d.keys())[:12]}
            })
        except SQLAlchemyError as e:
            errors.append({
                "index": idx,
                "error": e.__class__.__name__,
                "detail": str(e),
                "sample": {k: d.get(k) for k in sorted(d.keys())[:12]}
            })
        except Exception as e:
            # 非 SQLA 异常（多半来自 @validates 的 ValueError）
            errors.append({
                "index": idx,
                "error": e.__class__.__name__,
                "detail": str(e),
                "sample": {k: d.get(k) for k in sorted(d.keys())[:12]}
            })

    # 5) 成功的统一提交
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        # 理论上不该到这（单条已 flush 校验过），防一手
        return jsonify({
            "success": False,
            "error": e.__class__.__name__,
            "detail": str(e),
        }), 500

    res_items = [c.to_dict() for c in created + updated]
    return jsonify({"success": True, "data": {
        "created_count": len(created),
        "updated_count": len(updated),
        "skipped_count": len(errors),
        "errors": errors,                      # 前端可直接显示
        "created_ids": [c.id for c in created[:50]],
        "updated_ids": [c.id for c in updated[:50]],
        "items": res_items
    }})

# ---------- update ----------
@bp.put("/<int:cid>")
@bp.patch("/<int:cid>")
def update_customer(cid: int):
    c = Customer.query.get(cid)
    if not c:
        return jsonify({"success": False, "error": "Not Found"}), 404

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Invalid JSON body"}), 400

    try:
        _apply_to_model(c, _clip_to_column_lengths(_sanitize_for_model(_coerce_row(data))))
        db.session.flush()
        db.session.commit()
        return jsonify({"success": True, "data": c.to_dict()})
    except (IntegrityError, DataError, ProgrammingError) as e:
        db.session.rollback()
        return jsonify({"success": False, "error": e.__class__.__name__, "detail": str(getattr(e, "orig", e))}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"success": False, "error": e.__class__.__name__, "detail": str(e)}), 500
    except Exception as e:
        db.session.rollback()
        # 多半是 validators 的 ValueError
        return jsonify({"success": False, "error": e.__class__.__name__, "detail": str(e)}), 400

# ---------- delete ----------
@bp.delete("/<int:cid>")
def delete_customer(cid: int):
    c = Customer.query.get(cid)
    if not c:
        return jsonify({"success": False, "error": "Not Found"}), 404
    try:
        db.session.delete(c)
        db.session.commit()
        return jsonify({"success": True})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ---------- count ----------
@bp.get("/_count")
def customers_count():
    cnt = Customer.query.count()
    return jsonify({"success": True, "data": {"count": cnt}})


# ---------- OCR fuzzy match (for quotation system) ----------
def _fuzzy_score(text: str, target: str) -> float:
    """
    Simple fuzzy matching score (0.0 - 1.0).
    Higher score = better match.
    """
    if not text or not target:
        return 0.0

    text = text.lower().strip()
    target = target.lower().strip()

    # Exact match
    if text == target:
        return 1.0

    # Contains match
    if text in target:
        return 0.9 * len(text) / len(target)
    if target in text:
        return 0.8 * len(target) / len(text)

    # Substring match (character overlap)
    common = sum(1 for c in text if c in target)
    return 0.5 * common / max(len(text), len(target))


@bp.post("/match")
def match_customers_ocr():
    """
    OCR fuzzy match endpoint for quotation system.

    Request body:
    {
        "texts": ["text1", "text2", ...],  // OCR extracted texts
        "limit": 5  // max results per text (default 5)
    }

    Response:
    {
        "success": true,
        "data": {
            "matches": [
                {
                    "text": "original text",
                    "customers": [
                        {"customer": {...}, "score": 0.95, "matched_field": "short_name"},
                        ...
                    ]
                },
                ...
            ],
            "best_match": {...}  // overall best match if any
        }
    }
    """
    data = request.get_json(silent=True) or {}
    texts = data.get("texts", [])
    limit = _i(data.get("limit"), 5) or 5

    if not texts:
        # If single text provided directly
        if data.get("text"):
            texts = [data.get("text")]
        else:
            return jsonify({"success": True, "data": {"matches": [], "best_match": None}})

    if isinstance(texts, str):
        texts = [texts]

    # Get all customers for matching (cached approach for small datasets)
    all_customers = Customer.query.all()

    results = []
    best_overall = None
    best_overall_score = 0.0

    for text in texts:
        if not text or not isinstance(text, str):
            continue

        text = text.strip()
        if not text:
            continue

        matches = []

        for cust in all_customers:
            best_score = 0.0
            matched_field = None

            # Check against various fields
            for field, value in [
                ("code", cust.code),
                ("short_name", cust.short_name),
                ("name", cust.name),
                ("address", cust.address),
            ]:
                if value:
                    score = _fuzzy_score(text, value)
                    if score > best_score:
                        best_score = score
                        matched_field = field

            if best_score > 0.3:  # threshold
                matches.append({
                    "customer": cust.to_dict(),
                    "score": round(best_score, 3),
                    "matched_field": matched_field
                })

        # Sort by score and limit
        matches.sort(key=lambda x: x["score"], reverse=True)
        matches = matches[:limit]

        if matches:
            results.append({
                "text": text,
                "customers": matches
            })

            # Track overall best
            if matches[0]["score"] > best_overall_score:
                best_overall_score = matches[0]["score"]
                best_overall = {
                    "text": text,
                    "customer": matches[0]["customer"],
                    "score": matches[0]["score"],
                    "matched_field": matches[0]["matched_field"]
                }

    return jsonify({
        "success": True,
        "data": {
            "matches": results,
            "best_match": best_overall
        }
    })
