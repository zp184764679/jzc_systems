from flask import Blueprint, request, jsonify
from app import db
from app.models import ProductionPlan, ProductionStep, Task
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

timeline_bp = Blueprint('timeline', __name__)


@timeline_bp.route('/data', methods=['GET'])
def get_timeline_data():
    """
    获取时间轴数据

    Query参数:
    - view_type: customer | order | process | department
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD
    - customer_id: 可选，筛选特定客户
    - status: 可选，状态筛选 (pending, in_progress, completed, delayed)
    - search: 可选，搜索关键词
    - include_steps: 是否包含工序步骤 (true/false)
    """
    view_type = request.args.get('view_type', 'order')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    customer_id = request.args.get('customer_id', type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    include_steps = request.args.get('include_steps', 'true').lower() == 'true'

    # 默认时间范围：过去30天到未来60天
    if not start_date_str:
        start_date = datetime.now().date() - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

    if not end_date_str:
        end_date = datetime.now().date() + timedelta(days=60)
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # 构建查询
    query = ProductionPlan.query.filter(
        or_(
            and_(ProductionPlan.plan_start_date >= start_date, ProductionPlan.plan_start_date <= end_date),
            and_(ProductionPlan.plan_end_date >= start_date, ProductionPlan.plan_end_date <= end_date),
            and_(ProductionPlan.plan_start_date <= start_date, ProductionPlan.plan_end_date >= end_date)
        )
    )

    if customer_id:
        query = query.filter(ProductionPlan.customer_id == customer_id)

    if status:
        if status == 'delayed':
            query = query.filter(
                ProductionPlan.status != 'completed',
                ProductionPlan.plan_end_date < datetime.now().date()
            )
        else:
            query = query.filter(ProductionPlan.status == status)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                ProductionPlan.plan_no.ilike(search_term),
                ProductionPlan.order_no.ilike(search_term),
                ProductionPlan.product_name.ilike(search_term),
                ProductionPlan.customer_name.ilike(search_term)
            )
        )

    plans = query.order_by(ProductionPlan.plan_start_date).all()

    # 根据视图类型生成分组和项目
    groups = []
    items = []
    group_set = set()

    for plan in plans:
        # 生成项目
        item = plan.to_timeline_item()

        # 根据视图类型调整分组
        if view_type == 'customer':
            group_id = f'customer-{plan.customer_id}'
            group_title = plan.customer_name or f'客户 {plan.customer_id}'
            item['group'] = group_id
        elif view_type == 'order':
            group_id = f'order-{plan.order_id}'
            group_title = plan.order_no or f'订单 {plan.order_id}'
            item['group'] = group_id
        elif view_type == 'department':
            group_id = f'dept-{plan.department}' if plan.department else 'dept-unassigned'
            group_title = plan.department or '未分配部门'
            item['group'] = group_id
        else:  # process - 按工序分组，需要steps数据
            group_id = f'plan-{plan.id}'
            group_title = f'{plan.product_name} ({plan.plan_no})'
            item['group'] = group_id

        items.append(item)

        # 添加分组
        if group_id not in group_set:
            group_set.add(group_id)
            groups.append({
                'id': group_id,
                'title': group_title,
                'type': view_type
            })

        # 如果需要，添加工序步骤
        if include_steps and view_type == 'order':
            steps = ProductionStep.query.filter_by(plan_id=plan.id).order_by(ProductionStep.step_sequence).all()
            for step in steps:
                step_item = step.to_timeline_item(group_prefix='order')
                step_item['group'] = item['group']  # 使用相同的分组
                items.append(step_item)

    # 如果是工序视图，按工序名称重新分组
    if view_type == 'process':
        groups = []
        items = []
        group_set = set()

        steps = ProductionStep.query.join(ProductionPlan).filter(
            or_(
                and_(ProductionStep.plan_start >= start_date, ProductionStep.plan_start <= end_date),
                and_(ProductionStep.plan_end >= start_date, ProductionStep.plan_end <= end_date)
            )
        ).all()

        for step in steps:
            group_id = f'process-{step.step_name}'
            item = step.to_timeline_item()
            item['group'] = group_id

            items.append(item)

            if group_id not in group_set:
                group_set.add(group_id)
                groups.append({
                    'id': group_id,
                    'title': step.step_name,
                    'type': 'process'
                })

    return jsonify({
        'groups': groups,
        'items': items,
        'meta': {
            'total_count': len(items),
            'view_type': view_type,
            'date_range': [start_date.isoformat(), end_date.isoformat()]
        }
    })


@timeline_bp.route('/item/<item_type>/<int:item_id>', methods=['GET'])
def get_timeline_item_detail(item_type, item_id):
    """获取时间轴项目详情"""
    if item_type == 'plan':
        item = ProductionPlan.query.get_or_404(item_id)
        steps = ProductionStep.query.filter_by(plan_id=item_id).order_by(ProductionStep.step_sequence).all()
        return jsonify({
            'plan': item.to_dict(),
            'steps': [s.to_dict() for s in steps]
        })
    elif item_type == 'step':
        item = ProductionStep.query.get_or_404(item_id)
        return jsonify(item.to_dict())
    elif item_type == 'task':
        item = Task.query.get_or_404(item_id)
        return jsonify(item.to_dict())
    else:
        return jsonify({'error': 'Invalid item type'}), 400


@timeline_bp.route('/dependencies', methods=['GET'])
def get_dependencies():
    """获取工序依赖关系（用于绘制连接线）"""
    plan_id = request.args.get('plan_id', type=int)

    query = ProductionStep.query.filter(ProductionStep.depends_on_step_id.isnot(None))
    if plan_id:
        query = query.filter(ProductionStep.plan_id == plan_id)

    steps = query.all()

    dependencies = []
    for step in steps:
        dependencies.append({
            'from': f'step-{step.depends_on_step_id}',
            'to': f'step-{step.id}',
            'type': 'finish-to-start'
        })

    return jsonify({'dependencies': dependencies})


@timeline_bp.route('/stats', methods=['GET'])
def get_timeline_stats():
    """获取时间轴统计数据"""
    today = datetime.now().date()

    # 状态统计
    status_stats = db.session.query(
        ProductionPlan.status,
        db.func.count(ProductionPlan.id)
    ).group_by(ProductionPlan.status).all()

    # 延期数量
    delayed_count = ProductionPlan.query.filter(
        ProductionPlan.status != 'completed',
        ProductionPlan.plan_end_date < today
    ).count()

    # 本周到期
    week_end = today + timedelta(days=7)
    due_this_week = ProductionPlan.query.filter(
        ProductionPlan.status.in_(['pending', 'in_progress']),
        ProductionPlan.plan_end_date.between(today, week_end)
    ).count()

    return jsonify({
        'status_distribution': {s: c for s, c in status_stats},
        'delayed_count': delayed_count,
        'due_this_week': due_this_week,
        'total_active': ProductionPlan.query.filter(
            ProductionPlan.status.in_(['pending', 'in_progress'])
        ).count()
    })
