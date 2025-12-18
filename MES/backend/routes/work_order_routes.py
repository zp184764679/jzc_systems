# 工单管理路由
from flask import Blueprint, request, jsonify
from database import db
from models.work_order import WorkOrder
from datetime import datetime

work_order_bp = Blueprint('work_orders', __name__)


@work_order_bp.route('', methods=['GET'])
def get_work_orders():
    """获取工单列表"""
    status = request.args.get('status', '')
    keyword = request.args.get('keyword', '')
    # P1-10: 分页参数验证
    page = max(1, int(request.args.get('page', 1)))
    page_size = max(1, min(int(request.args.get('page_size', 20)), 1000))

    query = WorkOrder.query
    if status:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(
            (WorkOrder.order_no.contains(keyword)) |
            (WorkOrder.product_name.contains(keyword))
        )

    total = query.count()
    orders = query.order_by(WorkOrder.priority.asc(), WorkOrder.created_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'success': True,
        'data': {
            'items': [o.to_dict() for o in orders],
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })


@work_order_bp.route('', methods=['POST'])
def create_work_order():
    """创建工单"""
    data = request.get_json()

    # 生成工单编号
    today = datetime.now().strftime('%Y%m%d')
    count = WorkOrder.query.filter(WorkOrder.order_no.like(f'WO{today}%')).count()
    order_no = f'WO{today}{count + 1:04d}'

    order = WorkOrder(
        order_no=order_no,
        product_id=data.get('product_id'),
        product_code=data.get('product_code'),
        product_name=data.get('product_name'),
        planned_quantity=data.get('planned_quantity', 0),
        planned_start=datetime.fromisoformat(data['planned_start']) if data.get('planned_start') else None,
        planned_end=datetime.fromisoformat(data['planned_end']) if data.get('planned_end') else None,
        priority=data.get('priority', 3),
        source_type=data.get('source_type', 'manual'),
        source_id=data.get('source_id'),
        notes=data.get('notes'),
        created_by=data.get('created_by', 'system')
    )

    db.session.add(order)
    db.session.commit()

    return jsonify({'success': True, 'data': order.to_dict()}), 201


@work_order_bp.route('/<int:id>', methods=['GET'])
def get_work_order(id):
    """获取工单详情"""
    order = WorkOrder.query.get_or_404(id)
    return jsonify({'success': True, 'data': order.to_dict()})


@work_order_bp.route('/<int:id>/start', methods=['POST'])
def start_work_order(id):
    """开始生产"""
    order = WorkOrder.query.get_or_404(id)
    if order.status != 'pending':
        return jsonify({'success': False, 'error': '工单状态不允许开始'}), 400

    order.status = 'in_progress'
    order.actual_start = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'data': order.to_dict()})


@work_order_bp.route('/<int:id>/complete', methods=['POST'])
def complete_work_order(id):
    """完成工单"""
    order = WorkOrder.query.get_or_404(id)
    if order.status != 'in_progress':
        return jsonify({'success': False, 'error': '工单状态不允许完成'}), 400

    order.status = 'completed'
    order.actual_end = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'data': order.to_dict()})


@work_order_bp.route('/<int:id>', methods=['PUT'])
def update_work_order(id):
    """更新工单"""
    order = WorkOrder.query.get_or_404(id)
    data = request.get_json()

    for key in ['priority', 'notes', 'planned_quantity']:
        if key in data:
            setattr(order, key, data[key])

    db.session.commit()
    return jsonify({'success': True, 'data': order.to_dict()})
