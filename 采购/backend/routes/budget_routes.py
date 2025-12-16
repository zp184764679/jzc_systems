# -*- coding: utf-8 -*-
"""
采购预算管理路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from sqlalchemy import func, extract

from extensions import db
from models.budget import (
    Budget, BudgetCategory, BudgetUsage,
    BUDGET_PERIOD_LABELS, BUDGET_STATUS_LABELS, BUDGET_USAGE_TYPE_LABELS
)

logger = logging.getLogger(__name__)

budget_bp = Blueprint('budgets', __name__)
URL_PREFIX = '/api/v1'


# ==================== 预算 CRUD ====================

@budget_bp.route('/budgets', methods=['GET'])
def get_budgets():
    """获取预算列表"""
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # 筛选参数
        status = request.args.get('status')
        period_type = request.args.get('period_type')
        year = request.args.get('year', type=int)
        department = request.args.get('department')
        search = request.args.get('search', '').strip()
        warning_only = request.args.get('warning_only', 'false').lower() == 'true'

        query = Budget.query

        if status:
            query = query.filter(Budget.status == status)
        if period_type:
            query = query.filter(Budget.period_type == period_type)
        if year:
            query = query.filter(Budget.year == year)
        if department:
            query = query.filter(Budget.department == department)
        if search:
            query = query.filter(
                db.or_(
                    Budget.budget_code.ilike(f'%{search}%'),
                    Budget.name.ilike(f'%{search}%'),
                    Budget.department.ilike(f'%{search}%')
                )
            )

        # 只显示预警的预算
        if warning_only:
            # 使用子查询过滤预警预算
            budgets_all = query.all()
            warning_budgets = [b for b in budgets_all if b.is_warning]
            total = len(warning_budgets)
            start = (page - 1) * per_page
            end = start + per_page
            items = warning_budgets[start:end]
            pages = (total + per_page - 1) // per_page

            return jsonify({
                'items': [b.to_dict() for b in items],
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': pages
            })

        # 排序
        query = query.order_by(Budget.year.desc(), Budget.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [b.to_dict() for b in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })

    except Exception as e:
        logger.error(f"获取预算列表失败: {e}")
        return jsonify({'error': '获取预算列表失败'}), 500


@budget_bp.route('/budgets/<int:budget_id>', methods=['GET'])
def get_budget(budget_id):
    """获取预算详情"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        include_categories = request.args.get('include_categories', 'true').lower() == 'true'
        include_usage = request.args.get('include_usage', 'true').lower() == 'true'

        return jsonify(budget.to_dict(
            include_categories=include_categories,
            include_usage=include_usage
        ))

    except Exception as e:
        logger.error(f"获取预算详情失败: {e}")
        return jsonify({'error': '获取预算详情失败'}), 500


@budget_bp.route('/budgets', methods=['POST'])
def create_budget():
    """创建预算"""
    try:
        data = request.get_json() or {}

        # 验证必填字段
        required_fields = ['name', 'period_type', 'year', 'total_amount']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        period_type = data['period_type']
        year = data['year']
        period_value = data.get('period_value')
        department = data.get('department')

        # 验证周期值
        if period_type == 'monthly' and (not period_value or period_value < 1 or period_value > 12):
            return jsonify({'error': '月度预算需要指定有效的月份(1-12)'}), 400
        if period_type == 'quarterly' and (not period_value or period_value < 1 or period_value > 4):
            return jsonify({'error': '季度预算需要指定有效的季度(1-4)'}), 400

        # 检查是否已存在相同周期的预算
        existing_query = Budget.query.filter(
            Budget.period_type == period_type,
            Budget.year == year
        )
        if period_value:
            existing_query = existing_query.filter(Budget.period_value == period_value)
        if department:
            existing_query = existing_query.filter(Budget.department == department)
        else:
            existing_query = existing_query.filter(Budget.department.is_(None))

        if existing_query.first():
            return jsonify({'error': '该周期的预算已存在'}), 400

        # 生成预算编码
        budget_code = Budget.generate_budget_code(year, period_type, period_value, department)

        # 创建预算
        budget = Budget(
            budget_code=budget_code,
            name=data['name'],
            description=data.get('description'),
            period_type=period_type,
            year=year,
            period_value=period_value,
            department=department,
            total_amount=data['total_amount'],
            currency=data.get('currency', 'CNY'),
            warning_threshold=data.get('warning_threshold', 80),
            critical_threshold=data.get('critical_threshold', 95),
            status='draft',
            created_by=data.get('created_by'),
            remarks=data.get('remarks'),
        )

        db.session.add(budget)

        # 添加预算分类
        categories = data.get('categories', [])
        for cat_data in categories:
            category = BudgetCategory(
                budget=budget,
                category_name=cat_data.get('category_name', ''),
                category_code=cat_data.get('category_code'),
                allocated_amount=cat_data.get('allocated_amount', 0),
                remarks=cat_data.get('remarks'),
            )
            db.session.add(category)

        db.session.commit()

        return jsonify({
            'message': '预算创建成功',
            'budget': budget.to_dict(include_categories=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建预算失败: {e}")
        return jsonify({'error': f'创建预算失败: {str(e)}'}), 500


@budget_bp.route('/budgets/<int:budget_id>', methods=['PUT'])
def update_budget(budget_id):
    """更新预算"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        if budget.status not in ['draft', 'pending_approval']:
            return jsonify({'error': '只能修改草稿或待审批状态的预算'}), 400

        data = request.get_json() or {}

        # 更新基本信息
        if 'name' in data:
            budget.name = data['name']
        if 'description' in data:
            budget.description = data['description']
        if 'total_amount' in data:
            budget.total_amount = data['total_amount']
        if 'currency' in data:
            budget.currency = data['currency']
        if 'warning_threshold' in data:
            budget.warning_threshold = data['warning_threshold']
        if 'critical_threshold' in data:
            budget.critical_threshold = data['critical_threshold']
        if 'remarks' in data:
            budget.remarks = data['remarks']

        # 更新预算分类
        if 'categories' in data:
            # 删除现有分类
            BudgetCategory.query.filter_by(budget_id=budget.id).delete()

            # 添加新分类
            for cat_data in data['categories']:
                category = BudgetCategory(
                    budget_id=budget.id,
                    category_name=cat_data.get('category_name', ''),
                    category_code=cat_data.get('category_code'),
                    allocated_amount=cat_data.get('allocated_amount', 0),
                    remarks=cat_data.get('remarks'),
                )
                db.session.add(category)

        db.session.commit()

        return jsonify({
            'message': '预算更新成功',
            'budget': budget.to_dict(include_categories=True)
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新预算失败: {e}")
        return jsonify({'error': f'更新预算失败: {str(e)}'}), 500


@budget_bp.route('/budgets/<int:budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    """删除预算"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        if budget.status not in ['draft', 'closed']:
            return jsonify({'error': '只能删除草稿或已关闭的预算'}), 400

        # 检查是否有使用记录
        if budget.usage_records:
            return jsonify({'error': '该预算已有使用记录，无法删除'}), 400

        db.session.delete(budget)
        db.session.commit()

        return jsonify({'message': '预算删除成功'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除预算失败: {e}")
        return jsonify({'error': '删除预算失败'}), 500


# ==================== 预算审批 ====================

@budget_bp.route('/budgets/<int:budget_id>/submit', methods=['POST'])
def submit_budget(budget_id):
    """提交预算审批"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        if budget.status != 'draft':
            return jsonify({'error': '只能提交草稿状态的预算'}), 400

        data = request.get_json() or {}

        budget.status = 'pending_approval'
        budget.submitted_by = data.get('submitted_by')
        budget.submitted_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '预算已提交审批',
            'budget': budget.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"提交预算审批失败: {e}")
        return jsonify({'error': '提交预算审批失败'}), 500


@budget_bp.route('/budgets/<int:budget_id>/approve', methods=['POST'])
def approve_budget(budget_id):
    """审批通过预算"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        if budget.status != 'pending_approval':
            return jsonify({'error': '只能审批待审批状态的预算'}), 400

        data = request.get_json() or {}

        budget.status = 'approved'
        budget.approved_by = data.get('approved_by')
        budget.approved_at = datetime.utcnow()
        budget.approval_note = data.get('approval_note')

        db.session.commit()

        return jsonify({
            'message': '预算审批通过',
            'budget': budget.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"审批预算失败: {e}")
        return jsonify({'error': '审批预算失败'}), 500


@budget_bp.route('/budgets/<int:budget_id>/reject', methods=['POST'])
def reject_budget(budget_id):
    """拒绝预算"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        if budget.status != 'pending_approval':
            return jsonify({'error': '只能拒绝待审批状态的预算'}), 400

        data = request.get_json() or {}

        budget.status = 'draft'  # 退回草稿状态
        budget.approval_note = data.get('rejection_reason', '审批未通过')

        db.session.commit()

        return jsonify({
            'message': '预算已退回',
            'budget': budget.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"拒绝预算失败: {e}")
        return jsonify({'error': '拒绝预算失败'}), 500


@budget_bp.route('/budgets/<int:budget_id>/activate', methods=['POST'])
def activate_budget(budget_id):
    """激活预算（开始执行）"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        if budget.status != 'approved':
            return jsonify({'error': '只能激活已批准的预算'}), 400

        budget.status = 'active'
        db.session.commit()

        return jsonify({
            'message': '预算已激活',
            'budget': budget.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"激活预算失败: {e}")
        return jsonify({'error': '激活预算失败'}), 500


@budget_bp.route('/budgets/<int:budget_id>/close', methods=['POST'])
def close_budget(budget_id):
    """关闭预算"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        if budget.status not in ['active', 'exceeded']:
            return jsonify({'error': '只能关闭执行中或已超支的预算'}), 400

        budget.status = 'closed'
        db.session.commit()

        return jsonify({
            'message': '预算已关闭',
            'budget': budget.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"关闭预算失败: {e}")
        return jsonify({'error': '关闭预算失败'}), 500


# ==================== 预算使用 ====================

@budget_bp.route('/budgets/<int:budget_id>/reserve', methods=['POST'])
def reserve_budget(budget_id):
    """预留预算（PR提交时）"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        if budget.status not in ['active', 'exceeded']:
            return jsonify({'error': '只能使用执行中的预算'}), 400

        data = request.get_json() or {}
        amount = float(data.get('amount', 0))

        if amount <= 0:
            return jsonify({'error': '预留金额必须大于0'}), 400

        # 检查可用金额
        if amount > budget.available_amount:
            return jsonify({
                'error': '预留金额超出可用预算',
                'available_amount': budget.available_amount,
                'requested_amount': amount
            }), 400

        # 更新预留金额
        budget.reserved_amount = float(budget.reserved_amount) + amount

        # 记录使用
        usage = BudgetUsage(
            budget_id=budget.id,
            pr_id=data.get('pr_id'),
            pr_number=data.get('pr_number'),
            usage_type='reserve',
            amount=amount,
            balance_after=budget.available_amount,
            remarks=data.get('remarks', '采购申请预留'),
            operated_by=data.get('operated_by'),
            operated_by_name=data.get('operated_by_name'),
        )
        db.session.add(usage)

        # 检查是否超出预警
        if budget.usage_rate >= 100:
            budget.status = 'exceeded'

        db.session.commit()

        return jsonify({
            'message': '预算预留成功',
            'budget': budget.to_dict(),
            'usage': usage.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"预留预算失败: {e}")
        return jsonify({'error': f'预留预算失败: {str(e)}'}), 500


@budget_bp.route('/budgets/<int:budget_id>/consume', methods=['POST'])
def consume_budget(budget_id):
    """消耗预算（PO确认时）"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        if budget.status not in ['active', 'exceeded']:
            return jsonify({'error': '只能使用执行中的预算'}), 400

        data = request.get_json() or {}
        amount = float(data.get('amount', 0))
        from_reserved = data.get('from_reserved', True)  # 是否从预留转消耗

        if amount <= 0:
            return jsonify({'error': '消耗金额必须大于0'}), 400

        # 更新金额
        if from_reserved:
            # 从预留转为实际使用
            if amount > float(budget.reserved_amount):
                return jsonify({'error': '消耗金额超出预留金额'}), 400
            budget.reserved_amount = float(budget.reserved_amount) - amount
        else:
            # 直接消耗（跳过预留）
            if amount > budget.available_amount:
                return jsonify({'error': '消耗金额超出可用预算'}), 400

        budget.used_amount = float(budget.used_amount) + amount

        # 记录使用
        usage = BudgetUsage(
            budget_id=budget.id,
            pr_id=data.get('pr_id'),
            pr_number=data.get('pr_number'),
            usage_type='consume',
            amount=amount,
            balance_after=budget.available_amount,
            remarks=data.get('remarks', '采购订单消耗'),
            operated_by=data.get('operated_by'),
            operated_by_name=data.get('operated_by_name'),
        )
        db.session.add(usage)

        # 检查是否超出
        if budget.usage_rate >= 100:
            budget.status = 'exceeded'

        db.session.commit()

        return jsonify({
            'message': '预算消耗成功',
            'budget': budget.to_dict(),
            'usage': usage.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"消耗预算失败: {e}")
        return jsonify({'error': f'消耗预算失败: {str(e)}'}), 500


@budget_bp.route('/budgets/<int:budget_id>/release', methods=['POST'])
def release_budget(budget_id):
    """释放预算（PR取消时）"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        data = request.get_json() or {}
        amount = float(data.get('amount', 0))
        release_type = data.get('release_type', 'reserved')  # reserved/used

        if amount <= 0:
            return jsonify({'error': '释放金额必须大于0'}), 400

        if release_type == 'reserved':
            if amount > float(budget.reserved_amount):
                return jsonify({'error': '释放金额超出预留金额'}), 400
            budget.reserved_amount = float(budget.reserved_amount) - amount
        else:
            if amount > float(budget.used_amount):
                return jsonify({'error': '释放金额超出已使用金额'}), 400
            budget.used_amount = float(budget.used_amount) - amount

        # 记录使用
        usage = BudgetUsage(
            budget_id=budget.id,
            pr_id=data.get('pr_id'),
            pr_number=data.get('pr_number'),
            usage_type='release',
            amount=-amount,  # 负数表示释放
            balance_after=budget.available_amount,
            remarks=data.get('remarks', '采购申请取消释放'),
            operated_by=data.get('operated_by'),
            operated_by_name=data.get('operated_by_name'),
        )
        db.session.add(usage)

        # 恢复状态
        if budget.status == 'exceeded' and budget.usage_rate < 100:
            budget.status = 'active'

        db.session.commit()

        return jsonify({
            'message': '预算释放成功',
            'budget': budget.to_dict(),
            'usage': usage.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"释放预算失败: {e}")
        return jsonify({'error': f'释放预算失败: {str(e)}'}), 500


@budget_bp.route('/budgets/<int:budget_id>/adjust', methods=['POST'])
def adjust_budget(budget_id):
    """调整预算（追加或减少）"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        if budget.status not in ['active', 'exceeded', 'approved']:
            return jsonify({'error': '只能调整已批准或执行中的预算'}), 400

        data = request.get_json() or {}
        adjustment = float(data.get('adjustment', 0))  # 正数追加，负数减少

        if adjustment == 0:
            return jsonify({'error': '调整金额不能为0'}), 400

        # 检查减少时不能低于已使用金额
        new_total = float(budget.total_amount) + adjustment
        if new_total < float(budget.used_amount):
            return jsonify({'error': '调整后预算总额不能低于已使用金额'}), 400

        old_total = float(budget.total_amount)
        budget.total_amount = new_total

        # 记录调整
        usage = BudgetUsage(
            budget_id=budget.id,
            usage_type='adjust',
            amount=adjustment,
            balance_after=budget.available_amount,
            remarks=data.get('remarks', f'预算调整: {old_total} -> {new_total}'),
            operated_by=data.get('operated_by'),
            operated_by_name=data.get('operated_by_name'),
        )
        db.session.add(usage)

        # 更新状态
        if budget.usage_rate >= 100:
            budget.status = 'exceeded'
        elif budget.status == 'exceeded':
            budget.status = 'active'

        db.session.commit()

        return jsonify({
            'message': '预算调整成功',
            'budget': budget.to_dict(),
            'usage': usage.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"调整预算失败: {e}")
        return jsonify({'error': f'调整预算失败: {str(e)}'}), 500


@budget_bp.route('/budgets/<int:budget_id>/usage', methods=['GET'])
def get_budget_usage(budget_id):
    """获取预算使用记录"""
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            return jsonify({'error': '预算不存在'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        usage_type = request.args.get('usage_type')

        query = BudgetUsage.query.filter_by(budget_id=budget_id)

        if usage_type:
            query = query.filter(BudgetUsage.usage_type == usage_type)

        query = query.order_by(BudgetUsage.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [u.to_dict() for u in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })

    except Exception as e:
        logger.error(f"获取预算使用记录失败: {e}")
        return jsonify({'error': '获取预算使用记录失败'}), 500


# ==================== 统计和查询 ====================

@budget_bp.route('/budgets/statistics', methods=['GET'])
def get_budget_statistics():
    """获取预算统计"""
    try:
        year = request.args.get('year', datetime.utcnow().year, type=int)

        # 各状态数量
        status_counts = {}
        for status in BUDGET_STATUS_LABELS.keys():
            count = Budget.query.filter(
                Budget.year == year,
                Budget.status == status
            ).count()
            status_counts[status] = count

        # 预警预算数量
        all_active = Budget.query.filter(
            Budget.year == year,
            Budget.status.in_(['active', 'exceeded'])
        ).all()
        warning_count = sum(1 for b in all_active if b.is_warning and not b.is_critical)
        critical_count = sum(1 for b in all_active if b.is_critical)

        # 总额统计
        total_budget = db.session.query(
            func.sum(Budget.total_amount)
        ).filter(
            Budget.year == year,
            Budget.status.in_(['active', 'exceeded', 'closed'])
        ).scalar() or 0

        total_used = db.session.query(
            func.sum(Budget.used_amount)
        ).filter(
            Budget.year == year,
            Budget.status.in_(['active', 'exceeded', 'closed'])
        ).scalar() or 0

        total_reserved = db.session.query(
            func.sum(Budget.reserved_amount)
        ).filter(
            Budget.year == year,
            Budget.status.in_(['active', 'exceeded'])
        ).scalar() or 0

        # 按周期类型统计
        period_stats = []
        for period_type in BUDGET_PERIOD_LABELS.keys():
            period_total = db.session.query(
                func.sum(Budget.total_amount)
            ).filter(
                Budget.year == year,
                Budget.period_type == period_type,
                Budget.status.in_(['active', 'exceeded', 'closed'])
            ).scalar() or 0

            period_used = db.session.query(
                func.sum(Budget.used_amount)
            ).filter(
                Budget.year == year,
                Budget.period_type == period_type,
                Budget.status.in_(['active', 'exceeded', 'closed'])
            ).scalar() or 0

            period_stats.append({
                'period_type': period_type,
                'period_type_label': BUDGET_PERIOD_LABELS[period_type],
                'total_amount': float(period_total),
                'used_amount': float(period_used),
                'usage_rate': round(float(period_used) / float(period_total) * 100, 2) if period_total > 0 else 0
            })

        return jsonify({
            'year': year,
            'status_counts': status_counts,
            'warning_count': warning_count,
            'critical_count': critical_count,
            'total_budget': float(total_budget),
            'total_used': float(total_used),
            'total_reserved': float(total_reserved),
            'total_available': float(total_budget) - float(total_used) - float(total_reserved),
            'overall_usage_rate': round(float(total_used) / float(total_budget) * 100, 2) if total_budget > 0 else 0,
            'period_stats': period_stats
        })

    except Exception as e:
        logger.error(f"获取预算统计失败: {e}")
        return jsonify({'error': '获取预算统计失败'}), 500


@budget_bp.route('/budgets/warnings', methods=['GET'])
def get_budget_warnings():
    """获取预警预算列表"""
    try:
        year = request.args.get('year', datetime.utcnow().year, type=int)

        budgets = Budget.query.filter(
            Budget.year == year,
            Budget.status.in_(['active', 'exceeded'])
        ).all()

        warning_budgets = [b for b in budgets if b.is_warning]
        warning_budgets.sort(key=lambda x: x.usage_rate, reverse=True)

        return jsonify({
            'items': [b.to_dict() for b in warning_budgets],
            'total': len(warning_budgets)
        })

    except Exception as e:
        logger.error(f"获取预警预算失败: {e}")
        return jsonify({'error': '获取预警预算失败'}), 500


@budget_bp.route('/budgets/by-department', methods=['GET'])
def get_budgets_by_department():
    """按部门获取预算"""
    try:
        year = request.args.get('year', datetime.utcnow().year, type=int)
        department = request.args.get('department')

        query = Budget.query.filter(Budget.year == year)

        if department:
            query = query.filter(Budget.department == department)
        else:
            query = query.filter(Budget.department.is_(None))

        budgets = query.order_by(Budget.period_type, Budget.period_value).all()

        return jsonify({
            'items': [b.to_dict() for b in budgets],
            'total': len(budgets)
        })

    except Exception as e:
        logger.error(f"获取部门预算失败: {e}")
        return jsonify({'error': '获取部门预算失败'}), 500


@budget_bp.route('/budgets/check-availability', methods=['POST'])
def check_budget_availability():
    """检查预算可用性（PR提交前检查）"""
    try:
        data = request.get_json() or {}
        amount = float(data.get('amount', 0))
        department = data.get('department')
        year = data.get('year', datetime.utcnow().year)
        period_type = data.get('period_type', 'annual')
        period_value = data.get('period_value')

        # 查找匹配的预算
        query = Budget.query.filter(
            Budget.year == year,
            Budget.period_type == period_type,
            Budget.status == 'active'
        )

        if period_value:
            query = query.filter(Budget.period_value == period_value)

        if department:
            query = query.filter(Budget.department == department)
        else:
            query = query.filter(Budget.department.is_(None))

        budget = query.first()

        if not budget:
            return jsonify({
                'available': False,
                'message': '未找到匹配的可用预算',
                'budget': None
            })

        available = budget.available_amount >= amount

        return jsonify({
            'available': available,
            'message': '预算充足' if available else '预算不足',
            'budget': budget.to_dict(),
            'requested_amount': amount,
            'available_amount': budget.available_amount
        })

    except Exception as e:
        logger.error(f"检查预算可用性失败: {e}")
        return jsonify({'error': '检查预算可用性失败'}), 500


@budget_bp.route('/budgets/years', methods=['GET'])
def get_budget_years():
    """获取有预算的年份列表"""
    try:
        years = db.session.query(Budget.year).distinct().order_by(Budget.year.desc()).all()
        return jsonify({
            'years': [y[0] for y in years]
        })

    except Exception as e:
        logger.error(f"获取预算年份失败: {e}")
        return jsonify({'error': '获取预算年份失败'}), 500


@budget_bp.route('/budgets/departments', methods=['GET'])
def get_budget_departments():
    """获取有预算的部门列表"""
    try:
        year = request.args.get('year', datetime.utcnow().year, type=int)

        departments = db.session.query(Budget.department).filter(
            Budget.year == year,
            Budget.department.isnot(None)
        ).distinct().all()

        return jsonify({
            'departments': [d[0] for d in departments if d[0]]
        })

    except Exception as e:
        logger.error(f"获取预算部门失败: {e}")
        return jsonify({'error': '获取预算部门失败'}), 500


@budget_bp.route('/budgets/enums', methods=['GET'])
def get_budget_enums():
    """获取预算枚举值"""
    return jsonify({
        'period_types': BUDGET_PERIOD_LABELS,
        'statuses': BUDGET_STATUS_LABELS,
        'usage_types': BUDGET_USAGE_TYPE_LABELS
    })


# 蓝图列表（用于自动注册）
BLUEPRINTS = [budget_bp]
