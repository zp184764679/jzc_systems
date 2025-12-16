from flask import Blueprint, jsonify, request
from app import db
from app.models.base_data import Department, Position, Team, Factory
from sqlalchemy import or_
from app.routes.auth import require_auth

bp = Blueprint('base_data', __name__, url_prefix='/api')


# ========== 部门管理 ==========

@bp.route('/departments', methods=['GET'])
@require_auth
def get_departments(user):
    """获取部门列表"""
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'

    query = Department.query
    if active_only:
        query = query.filter(Department.is_active == True)
    if search:
        query = query.filter(or_(
            Department.code.ilike(f'%{search}%'),
            Department.name.ilike(f'%{search}%')
        ))

    departments = query.order_by(Department.sort_order, Department.code).all()
    return jsonify({
        'success': True,
        'data': [d.to_dict() for d in departments],
        'total': len(departments)
    })


@bp.route('/departments/<int:dept_id>', methods=['GET'])
@require_auth
def get_department(dept_id, user):
    """获取部门详情"""
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({'success': False, 'error': '部门不存在'}), 404
    return jsonify({'success': True, 'data': dept.to_dict()})


@bp.route('/departments', methods=['POST'])
@require_auth
def create_department(user):
    """创建部门"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    code = data.get('code', '').strip()
    name = data.get('name', '').strip()

    if not code or not name:
        return jsonify({'success': False, 'error': '部门编码和名称不能为空'}), 400

    # 检查编码是否重复
    existing = Department.query.filter_by(code=code).first()
    if existing:
        return jsonify({'success': False, 'error': f'部门编码 {code} 已存在'}), 400

    dept = Department(
        code=code,
        name=name,
        parent_id=data.get('parent_id'),
        manager_id=data.get('manager_id'),
        description=data.get('description', ''),
        is_active=data.get('is_active', True),
        sort_order=data.get('sort_order', 0)
    )

    db.session.add(dept)
    db.session.commit()

    return jsonify({'success': True, 'data': dept.to_dict(), 'message': '部门创建成功'}), 201


@bp.route('/departments/<int:dept_id>', methods=['PUT'])
@require_auth
def update_department(dept_id, user):
    """更新部门"""
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({'success': False, 'error': '部门不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    # 检查编码是否重复
    if 'code' in data and data['code'] != dept.code:
        existing = Department.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'success': False, 'error': f'部门编码 {data["code"]} 已存在'}), 400
        dept.code = data['code']

    if 'name' in data:
        dept.name = data['name']
    if 'parent_id' in data:
        dept.parent_id = data['parent_id']
    if 'manager_id' in data:
        dept.manager_id = data['manager_id']
    if 'description' in data:
        dept.description = data['description']
    if 'is_active' in data:
        dept.is_active = data['is_active']
    if 'sort_order' in data:
        dept.sort_order = data['sort_order']

    db.session.commit()
    return jsonify({'success': True, 'data': dept.to_dict(), 'message': '部门更新成功'})


@bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@require_auth
def delete_department(dept_id, user):
    """删除部门（软删除）"""
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({'success': False, 'error': '部门不存在'}), 404

    # 检查是否有员工使用此部门
    if hasattr(dept, 'employees') and dept.employees:
        return jsonify({'success': False, 'error': '该部门下有员工，无法删除'}), 400

    dept.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': '部门已禁用'})


# ========== 职位管理 ==========

@bp.route('/positions', methods=['GET'])
@require_auth
def get_positions(user):
    """获取职位列表"""
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    category = request.args.get('category', '')

    query = Position.query
    if active_only:
        query = query.filter(Position.is_active == True)
    if search:
        query = query.filter(or_(
            Position.code.ilike(f'%{search}%'),
            Position.name.ilike(f'%{search}%')
        ))
    if category:
        query = query.filter(Position.category == category)

    positions = query.order_by(Position.sort_order, Position.code).all()
    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in positions],
        'total': len(positions)
    })


# ========== 职位类别选项 ==========
# 注意：此路由必须在 /positions/<int:pos_id> 之前定义，否则 Flask 会将 "categories" 尝试匹配为 int 导致 404

@bp.route('/positions/categories', methods=['GET'])
@require_auth
def get_position_categories(user):
    """获取职位类别列表"""
    categories = [
        {'value': 'management', 'label': '管理'},
        {'value': 'technical', 'label': '技术'},
        {'value': 'sales', 'label': '销售'},
        {'value': 'admin', 'label': '行政'},
        {'value': 'finance', 'label': '财务'},
        {'value': 'production', 'label': '生产'},
        {'value': 'logistics', 'label': '物流'},
        {'value': 'quality', 'label': '质量'},
        {'value': 'other', 'label': '其他'}
    ]
    return jsonify({'success': True, 'data': categories})


@bp.route('/positions/<int:pos_id>', methods=['GET'])
@require_auth
def get_position(pos_id, user):
    """获取职位详情"""
    pos = Position.query.get(pos_id)
    if not pos:
        return jsonify({'success': False, 'error': '职位不存在'}), 404
    return jsonify({'success': True, 'data': pos.to_dict()})


@bp.route('/positions', methods=['POST'])
@require_auth
def create_position(user):
    """创建职位"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    code = data.get('code', '').strip()
    name = data.get('name', '').strip()

    if not code or not name:
        return jsonify({'success': False, 'error': '职位编码和名称不能为空'}), 400

    existing = Position.query.filter_by(code=code).first()
    if existing:
        return jsonify({'success': False, 'error': f'职位编码 {code} 已存在'}), 400

    pos = Position(
        code=code,
        name=name,
        level=data.get('level'),
        category=data.get('category', ''),
        description=data.get('description', ''),
        is_active=data.get('is_active', True),
        sort_order=data.get('sort_order', 0)
    )

    db.session.add(pos)
    db.session.commit()

    return jsonify({'success': True, 'data': pos.to_dict(), 'message': '职位创建成功'}), 201


@bp.route('/positions/<int:pos_id>', methods=['PUT'])
@require_auth
def update_position(pos_id, user):
    """更新职位"""
    pos = Position.query.get(pos_id)
    if not pos:
        return jsonify({'success': False, 'error': '职位不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    if 'code' in data and data['code'] != pos.code:
        existing = Position.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'success': False, 'error': f'职位编码 {data["code"]} 已存在'}), 400
        pos.code = data['code']

    if 'name' in data:
        pos.name = data['name']
    if 'level' in data:
        pos.level = data['level']
    if 'category' in data:
        pos.category = data['category']
    if 'description' in data:
        pos.description = data['description']
    if 'is_active' in data:
        pos.is_active = data['is_active']
    if 'sort_order' in data:
        pos.sort_order = data['sort_order']

    db.session.commit()
    return jsonify({'success': True, 'data': pos.to_dict(), 'message': '职位更新成功'})


@bp.route('/positions/<int:pos_id>', methods=['DELETE'])
@require_auth
def delete_position(pos_id, user):
    """删除职位（软删除）"""
    pos = Position.query.get(pos_id)
    if not pos:
        return jsonify({'success': False, 'error': '职位不存在'}), 404

    if hasattr(pos, 'employees') and pos.employees:
        return jsonify({'success': False, 'error': '该职位下有员工，无法删除'}), 400

    pos.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': '职位已禁用'})


# ========== 团队管理 ==========

@bp.route('/teams', methods=['GET'])
@require_auth
def get_teams(user):
    """获取团队列表"""
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    department_id = request.args.get('department_id', type=int)

    query = Team.query
    if active_only:
        query = query.filter(Team.is_active == True)
    if search:
        query = query.filter(or_(
            Team.code.ilike(f'%{search}%'),
            Team.name.ilike(f'%{search}%')
        ))
    if department_id:
        query = query.filter(Team.department_id == department_id)

    teams = query.order_by(Team.sort_order, Team.code).all()
    return jsonify({
        'success': True,
        'data': [t.to_dict() for t in teams],
        'total': len(teams)
    })


@bp.route('/teams/<int:team_id>', methods=['GET'])
@require_auth
def get_team(team_id, user):
    """获取团队详情"""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'success': False, 'error': '团队不存在'}), 404
    return jsonify({'success': True, 'data': team.to_dict()})


@bp.route('/teams', methods=['POST'])
@require_auth
def create_team(user):
    """创建团队"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    code = data.get('code', '').strip()
    name = data.get('name', '').strip()

    if not code or not name:
        return jsonify({'success': False, 'error': '团队编码和名称不能为空'}), 400

    existing = Team.query.filter_by(code=code).first()
    if existing:
        return jsonify({'success': False, 'error': f'团队编码 {code} 已存在'}), 400

    team = Team(
        code=code,
        name=name,
        department_id=data.get('department_id'),
        leader_id=data.get('leader_id'),
        description=data.get('description', ''),
        is_active=data.get('is_active', True),
        sort_order=data.get('sort_order', 0)
    )

    db.session.add(team)
    db.session.commit()

    return jsonify({'success': True, 'data': team.to_dict(), 'message': '团队创建成功'}), 201


@bp.route('/teams/<int:team_id>', methods=['PUT'])
@require_auth
def update_team(team_id, user):
    """更新团队"""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'success': False, 'error': '团队不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    if 'code' in data and data['code'] != team.code:
        existing = Team.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'success': False, 'error': f'团队编码 {data["code"]} 已存在'}), 400
        team.code = data['code']

    if 'name' in data:
        team.name = data['name']
    if 'department_id' in data:
        team.department_id = data['department_id']
    if 'leader_id' in data:
        team.leader_id = data['leader_id']
    if 'description' in data:
        team.description = data['description']
    if 'is_active' in data:
        team.is_active = data['is_active']
    if 'sort_order' in data:
        team.sort_order = data['sort_order']

    db.session.commit()
    return jsonify({'success': True, 'data': team.to_dict(), 'message': '团队更新成功'})


@bp.route('/teams/<int:team_id>', methods=['DELETE'])
@require_auth
def delete_team(team_id, user):
    """删除团队（软删除）"""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'success': False, 'error': '团队不存在'}), 404

    if hasattr(team, 'members') and team.members:
        return jsonify({'success': False, 'error': '该团队下有成员，无法删除'}), 400

    team.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': '团队已禁用'})


# ========== 工厂管理 ==========

@bp.route('/factories', methods=['GET'])
@require_auth
def get_factories(user):
    """获取工厂列表"""
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'

    query = Factory.query
    if active_only:
        query = query.filter(Factory.is_active == True)
    if search:
        query = query.filter(or_(
            Factory.code.ilike(f'%{search}%'),
            Factory.name.ilike(f'%{search}%'),
            Factory.city.ilike(f'%{search}%')
        ))

    factories = query.order_by(Factory.sort_order, Factory.code).all()
    return jsonify({
        'success': True,
        'data': [f.to_dict() for f in factories],
        'total': len(factories)
    })


@bp.route('/factories/<int:factory_id>', methods=['GET'])
@require_auth
def get_factory(factory_id, user):
    """获取工厂详情"""
    factory = Factory.query.get(factory_id)
    if not factory:
        return jsonify({'success': False, 'error': '工厂不存在'}), 404
    return jsonify({'success': True, 'data': factory.to_dict()})


@bp.route('/factories', methods=['POST'])
@require_auth
def create_factory(user):
    """创建工厂"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    code = data.get('code', '').strip()
    name = data.get('name', '').strip()

    if not code or not name:
        return jsonify({'success': False, 'error': '工厂编码和名称不能为空'}), 400

    existing = Factory.query.filter_by(code=code).first()
    if existing:
        return jsonify({'success': False, 'error': f'工厂编码 {code} 已存在'}), 400

    factory = Factory(
        code=code,
        name=name,
        city=data.get('city', ''),
        address=data.get('address', ''),
        description=data.get('description', ''),
        is_active=data.get('is_active', True),
        sort_order=data.get('sort_order', 0)
    )

    db.session.add(factory)
    db.session.commit()

    return jsonify({'success': True, 'data': factory.to_dict(), 'message': '工厂创建成功'}), 201


@bp.route('/factories/<int:factory_id>', methods=['PUT'])
@require_auth
def update_factory(factory_id, user):
    """更新工厂"""
    factory = Factory.query.get(factory_id)
    if not factory:
        return jsonify({'success': False, 'error': '工厂不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    if 'code' in data and data['code'] != factory.code:
        existing = Factory.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'success': False, 'error': f'工厂编码 {data["code"]} 已存在'}), 400
        factory.code = data['code']

    if 'name' in data:
        factory.name = data['name']
    if 'city' in data:
        factory.city = data['city']
    if 'address' in data:
        factory.address = data['address']
    if 'description' in data:
        factory.description = data['description']
    if 'is_active' in data:
        factory.is_active = data['is_active']
    if 'sort_order' in data:
        factory.sort_order = data['sort_order']

    db.session.commit()
    return jsonify({'success': True, 'data': factory.to_dict(), 'message': '工厂更新成功'})


@bp.route('/factories/<int:factory_id>', methods=['DELETE'])
@require_auth
def delete_factory(factory_id, user):
    """删除工厂（软删除）"""
    factory = Factory.query.get(factory_id)
    if not factory:
        return jsonify({'success': False, 'error': '工厂不存在'}), 404

    factory.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': '工厂已禁用'})
