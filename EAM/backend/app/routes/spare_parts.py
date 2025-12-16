# EAM 备件管理 API
from flask import Blueprint, request, jsonify
from datetime import datetime, date
from .. import db
from ..models import (
    SparePartCategory, SparePart, SparePartTransaction,
    Machine, MaintenanceOrder, FaultReport,
    TRANSACTION_TYPE_LABELS,
    generate_spare_part_code, generate_transaction_no, generate_category_code
)

bp = Blueprint("spare_parts", __name__, url_prefix="/api/spare-parts")


# ==================== 备件分类 API ====================

@bp.route("/categories", methods=["GET"])
def get_categories():
    """获取备件分类列表"""
    try:
        # 获取树形结构
        tree = request.args.get("tree", "false").lower() == "true"

        if tree:
            # 返回树形结构
            roots = SparePartCategory.query.filter(
                SparePartCategory.parent_id.is_(None)
            ).order_by(SparePartCategory.sort_order, SparePartCategory.code).all()
            return jsonify([c.to_dict(include_children=True) for c in roots])
        else:
            # 返回平铺列表
            query = SparePartCategory.query.order_by(
                SparePartCategory.level, SparePartCategory.sort_order, SparePartCategory.code
            )

            # 筛选条件
            is_active = request.args.get("is_active")
            if is_active is not None:
                query = query.filter(SparePartCategory.is_active == (is_active.lower() == "true"))

            categories = query.all()
            return jsonify([c.to_dict() for c in categories])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/categories/<int:id>", methods=["GET"])
def get_category(id):
    """获取分类详情"""
    category = SparePartCategory.query.get_or_404(id)
    return jsonify(category.to_dict(include_children=True))


@bp.route("/categories", methods=["POST"])
def create_category():
    """创建备件分类"""
    try:
        data = request.json

        # 确定层级和父分类
        parent_id = data.get("parent_id")
        parent = None
        level = 1
        parent_code = None

        if parent_id:
            parent = SparePartCategory.query.get(parent_id)
            if parent:
                level = parent.level + 1
                parent_code = parent.code

        # 生成编码
        code = data.get("code") or generate_category_code(parent_code)

        # 检查编码唯一性
        if SparePartCategory.query.filter_by(code=code).first():
            return jsonify({"error": f"分类编码 {code} 已存在"}), 400

        category = SparePartCategory(
            code=code,
            name=data.get("name"),
            parent_id=parent_id,
            level=level,
            sort_order=data.get("sort_order", 0),
            description=data.get("description"),
            is_active=data.get("is_active", True)
        )

        db.session.add(category)
        db.session.commit()

        return jsonify(category.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/categories/<int:id>", methods=["PUT"])
def update_category(id):
    """更新备件分类"""
    try:
        category = SparePartCategory.query.get_or_404(id)
        data = request.json

        category.name = data.get("name", category.name)
        category.sort_order = data.get("sort_order", category.sort_order)
        category.description = data.get("description", category.description)
        category.is_active = data.get("is_active", category.is_active)

        db.session.commit()
        return jsonify(category.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/categories/<int:id>", methods=["DELETE"])
def delete_category(id):
    """删除备件分类"""
    try:
        category = SparePartCategory.query.get_or_404(id)

        # 检查是否有子分类
        if category.children:
            return jsonify({"error": "该分类下有子分类，无法删除"}), 400

        # 检查是否有关联备件
        if category.spare_parts.count() > 0:
            return jsonify({"error": "该分类下有备件，无法删除"}), 400

        db.session.delete(category)
        db.session.commit()

        return jsonify({"message": "删除成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==================== 备件 API ====================

@bp.route("", methods=["GET"])
def get_spare_parts():
    """获取备件列表"""
    try:
        query = SparePart.query

        # 筛选条件
        keyword = request.args.get("keyword")
        if keyword:
            query = query.filter(
                db.or_(
                    SparePart.code.ilike(f"%{keyword}%"),
                    SparePart.name.ilike(f"%{keyword}%"),
                    SparePart.specification.ilike(f"%{keyword}%")
                )
            )

        category_id = request.args.get("category_id")
        if category_id:
            query = query.filter(SparePart.category_id == int(category_id))

        is_active = request.args.get("is_active")
        if is_active is not None:
            query = query.filter(SparePart.is_active == (is_active.lower() == "true"))

        stock_status = request.args.get("stock_status")
        if stock_status:
            if stock_status == "low_stock":
                query = query.filter(
                    SparePart.current_stock > 0,
                    SparePart.current_stock <= SparePart.safety_stock
                )
            elif stock_status == "out_of_stock":
                query = query.filter(SparePart.current_stock <= 0)
            elif stock_status == "over_stock":
                query = query.filter(
                    SparePart.max_stock > 0,
                    SparePart.current_stock >= SparePart.max_stock
                )

        # 排序
        sort_by = request.args.get("sort_by", "code")
        sort_order = request.args.get("sort_order", "asc")
        if hasattr(SparePart, sort_by):
            order_col = getattr(SparePart, sort_by)
            query = query.order_by(order_col.desc() if sort_order == "desc" else order_col.asc())

        # 分页
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return jsonify({
            "items": [sp.to_dict() for sp in pagination.items],
            "total": pagination.total,
            "page": page,
            "page_size": page_size,
            "pages": pagination.pages
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/options", methods=["GET"])
def get_spare_part_options():
    """获取备件选项（用于下拉选择）"""
    try:
        query = SparePart.query.filter(SparePart.is_active == True)

        keyword = request.args.get("keyword")
        if keyword:
            query = query.filter(
                db.or_(
                    SparePart.code.ilike(f"%{keyword}%"),
                    SparePart.name.ilike(f"%{keyword}%")
                )
            )

        spare_parts = query.order_by(SparePart.code).limit(50).all()
        return jsonify([sp.to_option() for sp in spare_parts])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:id>", methods=["GET"])
def get_spare_part(id):
    """获取备件详情"""
    spare_part = SparePart.query.get_or_404(id)
    return jsonify(spare_part.to_dict())


@bp.route("", methods=["POST"])
def create_spare_part():
    """创建备件"""
    try:
        data = request.json

        # 生成编码
        code = data.get("code") or generate_spare_part_code()

        # 检查编码唯一性
        if SparePart.query.filter_by(code=code).first():
            return jsonify({"error": f"备件编码 {code} 已存在"}), 400

        spare_part = SparePart(
            code=code,
            name=data.get("name"),
            category_id=data.get("category_id"),
            specification=data.get("specification"),
            brand=data.get("brand"),
            manufacturer=data.get("manufacturer"),
            unit=data.get("unit", "个"),
            current_stock=data.get("current_stock", 0),
            min_stock=data.get("min_stock", 0),
            max_stock=data.get("max_stock", 0),
            safety_stock=data.get("safety_stock", 0),
            unit_price=data.get("unit_price", 0),
            currency=data.get("currency", "CNY"),
            warehouse=data.get("warehouse"),
            location=data.get("location"),
            applicable_machines=data.get("applicable_machines"),
            description=data.get("description"),
            image_url=data.get("image_url"),
            supplier=data.get("supplier"),
            lead_time_days=data.get("lead_time_days", 7),
            is_active=data.get("is_active", True),
            created_by=request.headers.get("User-ID")
        )

        db.session.add(spare_part)
        db.session.commit()

        return jsonify(spare_part.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:id>", methods=["PUT"])
def update_spare_part(id):
    """更新备件"""
    try:
        spare_part = SparePart.query.get_or_404(id)
        data = request.json

        # 更新字段
        for field in ["name", "category_id", "specification", "brand", "manufacturer",
                      "unit", "min_stock", "max_stock", "safety_stock", "unit_price",
                      "currency", "warehouse", "location", "applicable_machines",
                      "description", "image_url", "supplier", "lead_time_days", "is_active"]:
            if field in data:
                setattr(spare_part, field, data[field])

        db.session.commit()
        return jsonify(spare_part.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:id>", methods=["DELETE"])
def delete_spare_part(id):
    """删除备件"""
    try:
        spare_part = SparePart.query.get_or_404(id)

        # 检查是否有出入库记录
        if spare_part.transactions.count() > 0:
            return jsonify({"error": "该备件有出入库记录，无法删除"}), 400

        db.session.delete(spare_part)
        db.session.commit()

        return jsonify({"message": "删除成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==================== 出入库 API ====================

@bp.route("/transactions", methods=["GET"])
def get_transactions():
    """获取出入库记录列表"""
    try:
        query = SparePartTransaction.query

        # 筛选条件
        spare_part_id = request.args.get("spare_part_id")
        if spare_part_id:
            query = query.filter(SparePartTransaction.spare_part_id == int(spare_part_id))

        transaction_type = request.args.get("transaction_type")
        if transaction_type:
            query = query.filter(SparePartTransaction.transaction_type == transaction_type)

        direction = request.args.get("direction")
        if direction == "in":
            query = query.filter(SparePartTransaction.transaction_type.in_([
                "purchase_in", "return_in", "adjust_in", "transfer_in"
            ]))
        elif direction == "out":
            query = query.filter(SparePartTransaction.transaction_type.in_([
                "issue_out", "scrap_out", "adjust_out", "transfer_out"
            ]))

        # 日期范围
        start_date = request.args.get("start_date")
        if start_date:
            query = query.filter(SparePartTransaction.transaction_date >= start_date)

        end_date = request.args.get("end_date")
        if end_date:
            query = query.filter(SparePartTransaction.transaction_date <= end_date)

        # 关联单据
        reference_type = request.args.get("reference_type")
        if reference_type:
            query = query.filter(SparePartTransaction.reference_type == reference_type)

        reference_id = request.args.get("reference_id")
        if reference_id:
            query = query.filter(SparePartTransaction.reference_id == int(reference_id))

        # 排序
        query = query.order_by(SparePartTransaction.created_at.desc())

        # 分页
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return jsonify({
            "items": [t.to_dict() for t in pagination.items],
            "total": pagination.total,
            "page": page,
            "page_size": page_size,
            "pages": pagination.pages
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/transactions/<int:id>", methods=["GET"])
def get_transaction(id):
    """获取出入库记录详情"""
    transaction = SparePartTransaction.query.get_or_404(id)
    return jsonify(transaction.to_dict())


@bp.route("/transactions", methods=["POST"])
def create_transaction():
    """创建出入库记录"""
    try:
        data = request.json

        spare_part_id = data.get("spare_part_id")
        spare_part = SparePart.query.get_or_404(spare_part_id)

        transaction_type = data.get("transaction_type")
        quantity = data.get("quantity", 0)

        # 入库类型数量为正，出库类型数量为负
        if transaction_type in ["purchase_in", "return_in", "adjust_in", "transfer_in"]:
            quantity = abs(quantity)
        else:
            quantity = -abs(quantity)

        # 检查库存是否足够（出库时）
        if quantity < 0 and spare_part.current_stock + quantity < 0:
            return jsonify({"error": f"库存不足，当前库存: {spare_part.current_stock}"}), 400

        # 记录变动前库存
        before_stock = spare_part.current_stock

        # 更新库存
        spare_part.current_stock += quantity
        after_stock = spare_part.current_stock

        # 获取关联设备信息
        machine_id = data.get("machine_id")
        machine_code = None
        machine_name = None
        if machine_id:
            machine = Machine.query.get(machine_id)
            if machine:
                machine_code = machine.machine_code
                machine_name = machine.name

        # 创建出入库记录
        transaction = SparePartTransaction(
            transaction_no=generate_transaction_no(),
            spare_part_id=spare_part_id,
            transaction_type=transaction_type,
            quantity=quantity,
            unit_price=data.get("unit_price", spare_part.unit_price),
            total_amount=abs(quantity) * data.get("unit_price", spare_part.unit_price),
            before_stock=before_stock,
            after_stock=after_stock,
            reference_type=data.get("reference_type"),
            reference_id=data.get("reference_id"),
            reference_no=data.get("reference_no"),
            machine_id=machine_id,
            machine_code=machine_code,
            machine_name=machine_name,
            transaction_date=datetime.strptime(data.get("transaction_date"), "%Y-%m-%d").date()
                if data.get("transaction_date") else date.today(),
            operator_id=data.get("operator_id") or request.headers.get("User-ID"),
            operator_name=data.get("operator_name"),
            remark=data.get("remark")
        )

        db.session.add(transaction)
        db.session.commit()

        return jsonify(transaction.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/issue", methods=["POST"])
def issue_spare_parts():
    """批量领用备件（用于维护工单或故障报修）"""
    try:
        data = request.json

        reference_type = data.get("reference_type")  # maintenance_order / fault_report
        reference_id = data.get("reference_id")
        reference_no = data.get("reference_no")
        items = data.get("items", [])  # [{spare_part_id, quantity}]

        # 获取关联设备信息
        machine_id = None
        machine_code = None
        machine_name = None

        if reference_type == "maintenance_order" and reference_id:
            order = MaintenanceOrder.query.get(reference_id)
            if order and order.machine_id:
                machine = Machine.query.get(order.machine_id)
                if machine:
                    machine_id = machine.id
                    machine_code = machine.machine_code
                    machine_name = machine.name
        elif reference_type == "fault_report" and reference_id:
            report = FaultReport.query.get(reference_id)
            if report and report.machine_id:
                machine = Machine.query.get(report.machine_id)
                if machine:
                    machine_id = machine.id
                    machine_code = machine.machine_code
                    machine_name = machine.name

        transactions = []
        for item in items:
            spare_part_id = item.get("spare_part_id")
            quantity = item.get("quantity", 1)

            spare_part = SparePart.query.get(spare_part_id)
            if not spare_part:
                continue

            # 检查库存
            if spare_part.current_stock < quantity:
                return jsonify({
                    "error": f"备件 {spare_part.name} 库存不足，当前库存: {spare_part.current_stock}"
                }), 400

            before_stock = spare_part.current_stock
            spare_part.current_stock -= quantity
            after_stock = spare_part.current_stock

            transaction = SparePartTransaction(
                transaction_no=generate_transaction_no(),
                spare_part_id=spare_part_id,
                transaction_type="issue_out",
                quantity=-quantity,
                unit_price=spare_part.unit_price,
                total_amount=quantity * spare_part.unit_price,
                before_stock=before_stock,
                after_stock=after_stock,
                reference_type=reference_type,
                reference_id=reference_id,
                reference_no=reference_no,
                machine_id=machine_id,
                machine_code=machine_code,
                machine_name=machine_name,
                transaction_date=date.today(),
                operator_id=request.headers.get("User-ID"),
                operator_name=data.get("operator_name"),
                remark=item.get("remark")
            )

            db.session.add(transaction)
            transactions.append(transaction)

        db.session.commit()

        return jsonify({
            "message": f"成功领用 {len(transactions)} 项备件",
            "transactions": [t.to_dict() for t in transactions]
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==================== 统计 API ====================

@bp.route("/statistics/summary", methods=["GET"])
def get_statistics_summary():
    """备件统计概览"""
    try:
        total_count = SparePart.query.filter(SparePart.is_active == True).count()

        # 库存状态统计
        out_of_stock = SparePart.query.filter(
            SparePart.is_active == True,
            SparePart.current_stock <= 0
        ).count()

        low_stock = SparePart.query.filter(
            SparePart.is_active == True,
            SparePart.current_stock > 0,
            SparePart.current_stock <= SparePart.safety_stock
        ).count()

        # 库存总值
        spare_parts = SparePart.query.filter(SparePart.is_active == True).all()
        total_value = sum(sp.current_stock * sp.unit_price for sp in spare_parts)

        # 本月出入库统计
        today = date.today()
        month_start = date(today.year, today.month, 1)

        month_in = db.session.query(db.func.sum(SparePartTransaction.quantity)).filter(
            SparePartTransaction.transaction_date >= month_start,
            SparePartTransaction.quantity > 0
        ).scalar() or 0

        month_out = db.session.query(db.func.sum(SparePartTransaction.quantity)).filter(
            SparePartTransaction.transaction_date >= month_start,
            SparePartTransaction.quantity < 0
        ).scalar() or 0

        return jsonify({
            "total_count": total_count,
            "out_of_stock": out_of_stock,
            "low_stock": low_stock,
            "total_value": round(total_value, 2),
            "month_in": abs(month_in),
            "month_out": abs(month_out)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/statistics/low-stock", methods=["GET"])
def get_low_stock_list():
    """获取库存预警列表"""
    try:
        spare_parts = SparePart.query.filter(
            SparePart.is_active == True,
            SparePart.current_stock <= SparePart.safety_stock
        ).order_by(SparePart.current_stock.asc()).all()

        return jsonify([{
            "id": sp.id,
            "code": sp.code,
            "name": sp.name,
            "specification": sp.specification,
            "current_stock": sp.current_stock,
            "safety_stock": sp.safety_stock,
            "stock_status": sp.stock_status,
            "stock_status_label": sp.stock_status_label,
            "supplier": sp.supplier,
            "lead_time_days": sp.lead_time_days
        } for sp in spare_parts])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/statistics/by-category", methods=["GET"])
def get_statistics_by_category():
    """按分类统计备件"""
    try:
        # 按分类统计数量和库存值
        results = db.session.query(
            SparePartCategory.id,
            SparePartCategory.name,
            db.func.count(SparePart.id).label("count"),
            db.func.sum(SparePart.current_stock).label("total_stock"),
            db.func.sum(SparePart.current_stock * SparePart.unit_price).label("total_value")
        ).outerjoin(
            SparePart, SparePart.category_id == SparePartCategory.id
        ).filter(
            SparePartCategory.is_active == True
        ).group_by(
            SparePartCategory.id, SparePartCategory.name
        ).all()

        return jsonify([{
            "category_id": r.id,
            "category_name": r.name,
            "count": r.count or 0,
            "total_stock": r.total_stock or 0,
            "total_value": round(r.total_value or 0, 2)
        } for r in results])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 枚举 API ====================

@bp.route("/enums", methods=["GET"])
def get_enums():
    """获取备件管理枚举值"""
    return jsonify({
        "transaction_types": [
            {"value": k, "label": v}
            for k, v in TRANSACTION_TYPE_LABELS.items()
        ],
        "stock_status": [
            {"value": "normal", "label": "正常"},
            {"value": "low_stock", "label": "库存不足"},
            {"value": "out_of_stock", "label": "缺货"},
            {"value": "over_stock", "label": "库存过高"},
        ],
        "units": ["个", "件", "套", "台", "米", "千克", "升", "箱", "盒", "卷"]
    })
