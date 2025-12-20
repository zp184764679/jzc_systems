"""
工艺库管理 API - 与报价系统共享数据
"""
from flask import Blueprint, request, jsonify
from models import db
from models.shared_process import Process

processes_bp = Blueprint('processes', __name__)


@processes_bp.route('/processes', methods=['GET'])
def list_processes():
    """获取工艺列表"""
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # 筛选参数
    category = request.args.get('category', '')
    search = request.args.get('search', '')

    # 构建查询
    query = Process.query.filter(Process.is_active == True)

    if category:
        query = query.filter(Process.category == category)

    if search:
        query = query.filter(
            db.or_(
                Process.process_code.contains(search),
                Process.process_name.contains(search)
            )
        )

    # 排序
    query = query.order_by(Process.process_code)

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    })


@processes_bp.route('/processes/categories', methods=['GET'])
def list_categories():
    """获取工艺类别列表"""
    categories = db.session.query(Process.category).filter(
        Process.is_active == True,
        Process.category.isnot(None)
    ).distinct().all()

    return jsonify({
        'success': True,
        'data': [cat[0] for cat in categories if cat[0]]
    })


@processes_bp.route('/processes/<int:process_id>', methods=['GET'])
def get_process(process_id):
    """获取工艺详情"""
    process = Process.query.filter(
        Process.id == process_id,
        Process.is_active == True
    ).first()

    if not process:
        return jsonify({'success': False, 'error': '工艺不存在'}), 404

    return jsonify({
        'success': True,
        'data': process.to_dict()
    })


@processes_bp.route('/processes/code/<process_code>', methods=['GET'])
def get_process_by_code(process_code):
    """通过工艺代码获取工艺"""
    process = Process.query.filter(
        Process.process_code == process_code,
        Process.is_active == True
    ).first()

    if not process:
        return jsonify({'success': False, 'error': f'工艺代码 {process_code} 不存在'}), 404

    return jsonify({
        'success': True,
        'data': process.to_dict()
    })


@processes_bp.route('/processes', methods=['POST'])
def create_process():
    """创建工艺"""
    data = request.get_json()

    # 检查必填字段
    if not data.get('process_code'):
        return jsonify({'success': False, 'error': '工艺代码不能为空'}), 400
    if not data.get('process_name'):
        return jsonify({'success': False, 'error': '工艺名称不能为空'}), 400

    # 检查工艺代码是否已存在
    existing = Process.query.filter(Process.process_code == data['process_code']).first()
    if existing:
        return jsonify({'success': False, 'error': f'工艺代码 {data["process_code"]} 已存在'}), 400

    # 创建工艺
    process = Process(
        process_code=data['process_code'],
        process_name=data['process_name'],
        category=data.get('category'),
        machine_type=data.get('machine_type'),
        machine_model=data.get('machine_model'),
        hourly_rate=data.get('hourly_rate'),
        setup_time=data.get('setup_time', 0),
        daily_fee=data.get('daily_fee', 0),
        daily_output=data.get('daily_output', 1000),
        defect_rate=data.get('defect_rate', 0),
        icon=data.get('icon'),
        description=data.get('description'),
        is_active=True
    )

    db.session.add(process)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': process.to_dict()
    }), 201


@processes_bp.route('/processes/<int:process_id>', methods=['PUT'])
def update_process(process_id):
    """更新工艺"""
    process = Process.query.get(process_id)

    if not process:
        return jsonify({'success': False, 'error': '工艺不存在'}), 404

    data = request.get_json()

    # 检查工艺代码是否与其他工艺冲突
    if data.get('process_code') and data['process_code'] != process.process_code:
        existing = Process.query.filter(
            Process.process_code == data['process_code'],
            Process.id != process_id
        ).first()
        if existing:
            return jsonify({'success': False, 'error': f'工艺代码 {data["process_code"]} 已被使用'}), 400

    # 更新字段
    for field in ['process_code', 'process_name', 'category', 'machine_type', 'machine_model',
                  'hourly_rate', 'setup_time', 'daily_fee', 'daily_output', 'defect_rate',
                  'icon', 'description', 'is_active']:
        if field in data:
            setattr(process, field, data[field])

    db.session.commit()

    return jsonify({
        'success': True,
        'data': process.to_dict()
    })


@processes_bp.route('/processes/<int:process_id>', methods=['DELETE'])
def delete_process(process_id):
    """删除工艺（软删除）"""
    process = Process.query.get(process_id)

    if not process:
        return jsonify({'success': False, 'error': '工艺不存在'}), 404

    # 软删除
    process.is_active = False
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'工艺 {process.process_name} 已删除'
    })


@processes_bp.route('/processes/search', methods=['GET'])
def search_processes():
    """搜索工艺"""
    keyword = request.args.get('keyword', '')
    limit = request.args.get('limit', 20, type=int)

    if not keyword:
        return jsonify({'success': True, 'data': []})

    processes = Process.query.filter(
        Process.is_active == True,
        db.or_(
            Process.process_code.contains(keyword),
            Process.process_name.contains(keyword)
        )
    ).limit(limit).all()

    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in processes]
    })
