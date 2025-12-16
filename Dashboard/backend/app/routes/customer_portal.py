from flask import Blueprint, request, jsonify
from app import db
from app.models import CustomerAccessToken, ProductionPlan, ProductionStep
from datetime import datetime, timedelta
from functools import wraps

customer_portal_bp = Blueprint('customer_portal', __name__)


def require_customer_token(f):
    """验证客户访问令牌的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token') or request.headers.get('X-Customer-Token')
        if not token:
            return jsonify({'error': '缺少访问令牌'}), 401

        access_token = CustomerAccessToken.query.filter_by(
            token=token,
            is_active=True
        ).first()

        if not access_token:
            return jsonify({'error': '无效的访问令牌'}), 403

        if access_token.is_expired:
            return jsonify({'error': '访问令牌已过期'}), 403

        # 记录访问
        access_token.record_access()
        db.session.commit()

        # 将token对象传递给视图函数
        request.customer_token = access_token
        return f(*args, **kwargs)

    return decorated_function


@customer_portal_bp.route('/generate-link', methods=['POST'])
def generate_access_link():
    """生成客户访问链接"""
    data = request.get_json()

    customer_id = data.get('customer_id')
    customer_name = data.get('customer_name')
    order_ids = data.get('order_ids')  # 可访问的订单ID列表
    valid_days = data.get('valid_days', 30)
    contact_name = data.get('contact_name')
    contact_phone = data.get('contact_phone')
    contact_email = data.get('contact_email')

    if not customer_id:
        return jsonify({'error': 'customer_id is required'}), 400

    # 生成令牌
    token = CustomerAccessToken.generate_token()
    expires_at = datetime.now() + timedelta(days=valid_days)

    access_token = CustomerAccessToken(
        customer_id=customer_id,
        customer_name=customer_name,
        contact_name=contact_name,
        contact_phone=contact_phone,
        contact_email=contact_email,
        token=token,
        order_ids=order_ids,
        expires_at=expires_at,
        permissions={
            'view_order': True,
            'view_timeline': True,
            'download_report': True
        }
    )

    db.session.add(access_token)
    db.session.commit()

    # 构建访问URL
    base_url = request.host_url.rstrip('/')
    access_url = f'{base_url}/customer-portal?token={token}'

    return jsonify({
        'token_id': access_token.id,
        'token': token,
        'access_url': access_url,
        'expires_at': expires_at.isoformat(),
        'valid_days': valid_days
    }), 201


@customer_portal_bp.route('/tokens', methods=['GET'])
def list_tokens():
    """列出所有客户访问令牌（管理接口）"""
    customer_id = request.args.get('customer_id', type=int)
    is_active = request.args.get('is_active')

    query = CustomerAccessToken.query

    if customer_id:
        query = query.filter(CustomerAccessToken.customer_id == customer_id)

    if is_active is not None:
        query = query.filter(CustomerAccessToken.is_active == (is_active.lower() == 'true'))

    tokens = query.order_by(CustomerAccessToken.created_at.desc()).all()

    return jsonify({
        'tokens': [t.to_dict() for t in tokens]
    })


@customer_portal_bp.route('/tokens/<int:token_id>/revoke', methods=['POST'])
def revoke_token(token_id):
    """撤销访问令牌"""
    token = CustomerAccessToken.query.get_or_404(token_id)
    reason = request.get_json().get('reason') if request.get_json() else None

    token.revoke(reason)
    db.session.commit()

    return jsonify({
        'message': '令牌已撤销',
        'token_id': token_id
    })


@customer_portal_bp.route('/verify', methods=['GET'])
@require_customer_token
def verify_token():
    """验证令牌有效性"""
    token = request.customer_token
    return jsonify({
        'valid': True,
        'customer_id': token.customer_id,
        'customer_name': token.customer_name,
        'expires_at': token.expires_at.isoformat(),
        'days_remaining': token.days_until_expiry,
        'order_ids': token.order_ids
    })


@customer_portal_bp.route('/orders', methods=['GET'])
@require_customer_token
def get_customer_orders():
    """获取客户可访问的订单列表"""
    token = request.customer_token

    query = ProductionPlan.query.filter(
        ProductionPlan.customer_id == token.customer_id
    )

    # 如果指定了订单ID列表，则过滤
    if token.order_ids:
        query = query.filter(ProductionPlan.order_id.in_(token.order_ids))

    orders = query.order_by(ProductionPlan.plan_end_date.desc()).all()

    # 返回简化的订单数据（隐藏内部信息）
    result = []
    for order in orders:
        result.append({
            'order_id': order.order_id,
            'order_no': order.order_no,
            'product_name': order.product_name,
            'quantity': order.plan_quantity,
            'status': order.status,
            'progress': order.progress_percentage,
            'plan_start_date': order.plan_start_date.isoformat() if order.plan_start_date else None,
            'plan_end_date': order.plan_end_date.isoformat() if order.plan_end_date else None,
            'is_delayed': order.is_delayed,
            'days_remaining': order.days_remaining
        })

    return jsonify({'orders': result})


@customer_portal_bp.route('/orders/<int:order_id>', methods=['GET'])
@require_customer_token
def get_order_detail(order_id):
    """获取订单详情"""
    token = request.customer_token

    # 验证访问权限
    if token.order_ids and order_id not in token.order_ids:
        return jsonify({'error': '无权访问此订单'}), 403

    plan = ProductionPlan.query.filter_by(
        order_id=order_id,
        customer_id=token.customer_id
    ).first()

    if not plan:
        return jsonify({'error': '订单不存在'}), 404

    # 获取工序步骤
    steps = ProductionStep.query.filter_by(plan_id=plan.id).order_by(ProductionStep.step_sequence).all()

    # 返回简化的数据
    return jsonify({
        'order': {
            'order_no': plan.order_no,
            'product_name': plan.product_name,
            'quantity': plan.plan_quantity,
            'status': plan.status,
            'progress': plan.progress_percentage,
            'plan_start_date': plan.plan_start_date.isoformat() if plan.plan_start_date else None,
            'plan_end_date': plan.plan_end_date.isoformat() if plan.plan_end_date else None,
            'is_delayed': plan.is_delayed,
            'days_remaining': plan.days_remaining
        },
        'timeline': [
            {
                'step': step.step_name,
                'sequence': step.step_sequence,
                'status': step.status,
                'progress': float(step.completion_rate) if step.completion_rate else 0,
                'plan_start': step.plan_start.isoformat() if step.plan_start else None,
                'plan_end': step.plan_end.isoformat() if step.plan_end else None
            }
            for step in steps
        ],
        'milestones': _get_order_milestones(plan)
    })


def _get_order_milestones(plan):
    """获取订单里程碑"""
    milestones = []

    # 订单创建
    if plan.created_at:
        milestones.append({
            'name': '订单创建',
            'date': plan.created_at.isoformat(),
            'completed': True
        })

    # 生产开始
    if plan.actual_start_date:
        milestones.append({
            'name': '生产开始',
            'date': plan.actual_start_date.isoformat(),
            'completed': True
        })
    elif plan.plan_start_date:
        milestones.append({
            'name': '计划开始',
            'date': plan.plan_start_date.isoformat(),
            'completed': False
        })

    # 预计完成
    if plan.plan_end_date:
        milestones.append({
            'name': '预计完成',
            'date': plan.plan_end_date.isoformat(),
            'completed': plan.status == 'completed'
        })

    # 实际完成
    if plan.actual_end_date:
        milestones.append({
            'name': '实际完成',
            'date': plan.actual_end_date.isoformat(),
            'completed': True
        })

    return milestones


@customer_portal_bp.route('/orders/<int:order_id>/timeline', methods=['GET'])
@require_customer_token
def get_order_timeline(order_id):
    """获取订单时间轴数据（用于可视化）"""
    token = request.customer_token

    # 验证访问权限
    if token.order_ids and order_id not in token.order_ids:
        return jsonify({'error': '无权访问此订单'}), 403

    plan = ProductionPlan.query.filter_by(
        order_id=order_id,
        customer_id=token.customer_id
    ).first()

    if not plan:
        return jsonify({'error': '订单不存在'}), 404

    # 获取工序步骤
    steps = ProductionStep.query.filter_by(plan_id=plan.id).order_by(ProductionStep.step_sequence).all()

    # 构建时间轴数据
    groups = [{
        'id': f'order-{order_id}',
        'title': plan.product_name or plan.order_no
    }]

    items = []
    for step in steps:
        items.append({
            'id': f'step-{step.id}',
            'group': f'order-{order_id}',
            'title': step.step_name,
            'start_time': int(step.plan_start.timestamp() * 1000) if step.plan_start else None,
            'end_time': int(step.plan_end.timestamp() * 1000) if step.plan_end else None,
            'status': step.status,
            'progress': float(step.completion_rate) if step.completion_rate else 0
        })

    return jsonify({
        'groups': groups,
        'items': items
    })
