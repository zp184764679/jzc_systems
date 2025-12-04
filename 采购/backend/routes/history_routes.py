# routes/history_routes.py
# -*- coding: utf-8 -*-
"""
操作历史记录API路由
"""

from flask import Blueprint, request, jsonify
from models.operation_history import OperationHistory
from extensions import db
from datetime import datetime
import traceback

bp = Blueprint('history', __name__, url_prefix='/api/v1/history')


@bp.route('/', methods=['GET'])
def list_history():
    """
    查询操作历史列表

    Query参数:
    - system: 系统标识
    - module: 模块名称
    - action: 操作类型
    - target_type: 目标类型
    - target_id: 目标ID
    - operator_id: 操作人ID
    - start_date: 开始日期 (YYYY-MM-DD)
    - end_date: 结束日期 (YYYY-MM-DD)
    - keyword: 关键词搜索
    - page: 页码 (默认1)
    - page_size: 每页数量 (默认20)
    """
    try:
        # 获取查询参数
        system = request.args.get('system')
        module = request.args.get('module')
        action = request.args.get('action')
        target_type = request.args.get('target_type')
        target_id = request.args.get('target_id')
        operator_id = request.args.get('operator_id', type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        keyword = request.args.get('keyword')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # 限制每页数量
        if page_size > 100:
            page_size = 100

        # 构建查询
        query = OperationHistory.query

        if system:
            query = query.filter(OperationHistory.system == system)
        if module:
            query = query.filter(OperationHistory.module == module)
        if action:
            query = query.filter(OperationHistory.action == action)
        if target_type:
            query = query.filter(OperationHistory.target_type == target_type)
        if target_id:
            query = query.filter(OperationHistory.target_id == str(target_id))
        if operator_id:
            query = query.filter(OperationHistory.operator_id == operator_id)

        # 日期过滤
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                query = query.filter(OperationHistory.created_at >= start_date)
            except ValueError:
                pass

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                # 加一天以包含当天
                from datetime import timedelta
                end_date = end_date + timedelta(days=1)
                query = query.filter(OperationHistory.created_at < end_date)
            except ValueError:
                pass

        # 关键词搜索
        if keyword:
            query = query.filter(
                db.or_(
                    OperationHistory.description.like(f'%{keyword}%'),
                    OperationHistory.target_name.like(f'%{keyword}%')
                )
            )

        # 统计总数
        total = query.count()

        # 分页查询
        records = query.order_by(OperationHistory.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        # 转换为字典
        data = [record.to_dict() for record in records]

        return jsonify({
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }), 200

    except Exception as e:
        print(f"查询操作历史错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500


@bp.route('/target/<target_type>/<target_id>', methods=['GET'])
def get_target_history(target_type, target_id):
    """
    获取特定目标的操作历史

    URL参数:
    - target_type: 目标类型 (PR, RFQ, Supplier等)
    - target_id: 目标ID

    Query参数:
    - limit: 返回数量限制 (默认100)
    """
    try:
        limit = request.args.get('limit', 100, type=int)

        records = OperationHistory.get_target_history(target_type, target_id, limit)
        data = [record.to_dict() for record in records]

        return jsonify({
            "data": data,
            "target_type": target_type,
            "target_id": target_id,
            "total": len(data)
        }), 200

    except Exception as e:
        print(f"查询目标历史错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500


@bp.route('/stats', methods=['GET'])
def get_history_stats():
    """
    获取操作历史统计

    Query参数:
    - system: 系统标识
    - days: 统计天数 (默认7)
    """
    try:
        from sqlalchemy import func
        from datetime import timedelta

        system = request.args.get('system')
        days = request.args.get('days', 7, type=int)

        # 计算开始日期
        start_date = datetime.utcnow() - timedelta(days=days)

        # 基础查询
        query = db.session.query(
            OperationHistory.action,
            func.count(OperationHistory.id).label('count')
        ).filter(OperationHistory.created_at >= start_date)

        if system:
            query = query.filter(OperationHistory.system == system)

        # 按操作类型统计
        action_stats = query.group_by(OperationHistory.action).all()

        # 按操作人统计
        operator_query = db.session.query(
            OperationHistory.operator_name,
            func.count(OperationHistory.id).label('count')
        ).filter(
            OperationHistory.created_at >= start_date,
            OperationHistory.operator_name.isnot(None)
        )

        if system:
            operator_query = operator_query.filter(OperationHistory.system == system)

        operator_stats = operator_query.group_by(OperationHistory.operator_name) \
            .order_by(func.count(OperationHistory.id).desc()) \
            .limit(10) \
            .all()

        # 按模块统计
        module_query = db.session.query(
            OperationHistory.module,
            func.count(OperationHistory.id).label('count')
        ).filter(OperationHistory.created_at >= start_date)

        if system:
            module_query = module_query.filter(OperationHistory.system == system)

        module_stats = module_query.group_by(OperationHistory.module).all()

        # 操作类型中文标签
        action_labels = {
            "create": "创建",
            "update": "修改",
            "delete": "删除",
            "approve": "审批通过",
            "reject": "驳回",
            "forward": "转交",
            "submit": "提交",
            "upload": "上传",
            "download": "下载",
        }

        return jsonify({
            "period_days": days,
            "system": system or "all",
            "by_action": [
                {"action": a[0], "label": action_labels.get(a[0], a[0]), "count": a[1]}
                for a in action_stats
            ],
            "by_operator": [
                {"operator_name": o[0], "count": o[1]}
                for o in operator_stats
            ],
            "by_module": [
                {"module": m[0], "count": m[1]}
                for m in module_stats
            ]
        }), 200

    except Exception as e:
        print(f"查询操作历史统计错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500
