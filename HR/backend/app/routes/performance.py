"""
绩效管理 API 路由
包含: 考核周期、KPI模板、绩效目标、绩效评估、等级配置、绩效反馈
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Employee
from app.models.performance import (
    PerformancePeriod, KPITemplate, PerformanceGoal, PerformanceEvaluation,
    PerformanceGradeConfig, PerformanceFeedback,
    PerformancePeriodType, PerformanceStatus, GoalStatus,
    init_default_grade_configs, init_default_kpi_templates
)
from datetime import datetime, date
from functools import wraps
from sqlalchemy import func

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')


# ============ 认证装饰器 ============
def require_auth(f):
    """验证 JWT Token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': '未提供认证信息'}), 401

        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            if not token:
                return jsonify({'error': 'Token 无效'}), 401
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': f'认证失败: {str(e)}'}), 401

    return decorated


# ============ 辅助函数 ============
def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


def get_grade_by_score(score):
    """根据分数获取等级"""
    if score is None:
        return None, None

    grade_config = PerformanceGradeConfig.query.filter(
        PerformanceGradeConfig.is_active == True,
        PerformanceGradeConfig.min_score <= score,
        PerformanceGradeConfig.max_score >= score
    ).first()

    if grade_config:
        return grade_config.grade, grade_config.name
    return None, None


# ============ 考核周期 API ============
@performance_bp.route('/periods', methods=['GET'])
@require_auth
def get_periods():
    """获取考核周期列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        year = request.args.get('year', type=int)
        period_type = request.args.get('period_type')
        status = request.args.get('status')
        is_active = request.args.get('is_active')

        query = PerformancePeriod.query

        if year:
            query = query.filter(PerformancePeriod.year == year)
        if period_type:
            query = query.filter(PerformancePeriod.period_type == period_type)
        if status:
            query = query.filter(PerformancePeriod.status == status)
        if is_active is not None:
            query = query.filter(PerformancePeriod.is_active == (is_active.lower() == 'true'))

        query = query.order_by(PerformancePeriod.year.desc(), PerformancePeriod.start_date.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/periods/<int:id>', methods=['GET'])
@require_auth
def get_period(id):
    """获取考核周期详情"""
    try:
        period = PerformancePeriod.query.get_or_404(id)
        return jsonify({'data': period.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/periods', methods=['POST'])
@require_auth
def create_period():
    """创建考核周期"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('name') or not data.get('period_type'):
            return jsonify({'error': '周期编码、名称和类型为必填项'}), 400

        if not data.get('start_date') or not data.get('end_date'):
            return jsonify({'error': '开始日期和结束日期为必填项'}), 400

        existing = PerformancePeriod.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'error': f'周期编码 {data["code"]} 已存在'}), 400

        period = PerformancePeriod(
            code=data['code'],
            name=data['name'],
            period_type=data['period_type'],
            year=data.get('year', datetime.now().year),
            start_date=parse_date(data['start_date']),
            end_date=parse_date(data['end_date']),
            goal_setting_start=parse_date(data.get('goal_setting_start')),
            goal_setting_end=parse_date(data.get('goal_setting_end')),
            self_evaluation_start=parse_date(data.get('self_evaluation_start')),
            self_evaluation_end=parse_date(data.get('self_evaluation_end')),
            manager_evaluation_start=parse_date(data.get('manager_evaluation_start')),
            manager_evaluation_end=parse_date(data.get('manager_evaluation_end')),
            calibration_start=parse_date(data.get('calibration_start')),
            calibration_end=parse_date(data.get('calibration_end')),
            status=data.get('status', 'not_started'),
            is_active=data.get('is_active', True),
            department_ids=data.get('department_ids'),
            factory_id=data.get('factory_id'),
            description=data.get('description'),
            created_by=data.get('created_by')
        )

        db.session.add(period)
        db.session.commit()

        return jsonify({'message': '创建成功', 'data': period.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/periods/<int:id>', methods=['PUT'])
@require_auth
def update_period(id):
    """更新考核周期"""
    try:
        period = PerformancePeriod.query.get_or_404(id)
        data = request.get_json()

        for field in ['name', 'period_type', 'year', 'status', 'is_active',
                      'department_ids', 'factory_id', 'description']:
            if field in data:
                setattr(period, field, data[field])

        date_fields = ['start_date', 'end_date', 'goal_setting_start', 'goal_setting_end',
                       'self_evaluation_start', 'self_evaluation_end',
                       'manager_evaluation_start', 'manager_evaluation_end',
                       'calibration_start', 'calibration_end']

        for field in date_fields:
            if field in data:
                setattr(period, field, parse_date(data[field]))

        db.session.commit()
        return jsonify({'message': '更新成功', 'data': period.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/periods/<int:id>/activate', methods=['PUT'])
@require_auth
def activate_period(id):
    """激活考核周期"""
    try:
        period = PerformancePeriod.query.get_or_404(id)

        if period.status != 'not_started':
            return jsonify({'error': f'当前状态 {period.status} 无法激活'}), 400

        period.status = 'in_progress'
        db.session.commit()

        return jsonify({'message': '激活成功', 'data': period.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/periods/<int:id>/status', methods=['PUT'])
@require_auth
def update_period_status(id):
    """更新考核周期状态"""
    try:
        period = PerformancePeriod.query.get_or_404(id)
        data = request.get_json()
        new_status = data.get('status')

        valid_statuses = ['not_started', 'in_progress', 'self_evaluation',
                          'manager_evaluation', 'calibration', 'completed', 'archived']

        if new_status not in valid_statuses:
            return jsonify({'error': '无效的状态值'}), 400

        period.status = new_status
        db.session.commit()

        return jsonify({'message': '状态更新成功', 'data': period.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============ KPI 模板 API ============
@performance_bp.route('/kpi-templates', methods=['GET'])
@require_auth
def get_kpi_templates():
    """获取 KPI 模板列表"""
    try:
        category = request.args.get('category')
        is_active = request.args.get('is_active', 'true')

        query = KPITemplate.query

        if category:
            query = query.filter(KPITemplate.category == category)
        if is_active.lower() == 'true':
            query = query.filter(KPITemplate.is_active == True)

        templates = query.order_by(KPITemplate.sort_order, KPITemplate.id).all()

        return jsonify({
            'items': [t.to_dict() for t in templates],
            'total': len(templates)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/kpi-templates', methods=['POST'])
@require_auth
def create_kpi_template():
    """创建 KPI 模板"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('name'):
            return jsonify({'error': 'KPI编码和名称为必填项'}), 400

        existing = KPITemplate.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'error': f'KPI编码 {data["code"]} 已存在'}), 400

        template = KPITemplate(
            code=data['code'],
            name=data['name'],
            category=data.get('category', 'work'),
            default_weight=data.get('default_weight', 0),
            max_score=data.get('max_score', 100),
            min_score=data.get('min_score', 0),
            scoring_criteria=data.get('scoring_criteria'),
            applicable_positions=data.get('applicable_positions'),
            applicable_departments=data.get('applicable_departments'),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0),
            description=data.get('description')
        )

        db.session.add(template)
        db.session.commit()

        return jsonify({'message': '创建成功', 'data': template.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/kpi-templates/<int:id>', methods=['PUT'])
@require_auth
def update_kpi_template(id):
    """更新 KPI 模板"""
    try:
        template = KPITemplate.query.get_or_404(id)
        data = request.get_json()

        for field in ['name', 'category', 'default_weight', 'max_score', 'min_score',
                      'scoring_criteria', 'applicable_positions', 'applicable_departments',
                      'is_active', 'sort_order', 'description']:
            if field in data:
                setattr(template, field, data[field])

        db.session.commit()
        return jsonify({'message': '更新成功', 'data': template.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/kpi-templates/init', methods=['POST'])
@require_auth
def init_kpi_templates():
    """初始化默认 KPI 模板"""
    try:
        init_default_kpi_templates()
        return jsonify({'message': '初始化成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ 绩效目标 API ============
@performance_bp.route('/goals', methods=['GET'])
@require_auth
def get_goals():
    """获取绩效目标列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        period_id = request.args.get('period_id', type=int)
        status = request.args.get('status')
        category = request.args.get('category')

        query = PerformanceGoal.query

        if employee_id:
            query = query.filter(PerformanceGoal.employee_id == employee_id)
        if period_id:
            query = query.filter(PerformanceGoal.period_id == period_id)
        if status:
            query = query.filter(PerformanceGoal.status == status)
        if category:
            query = query.filter(PerformanceGoal.category == category)

        query = query.order_by(PerformanceGoal.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [g.to_dict() for g in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/goals', methods=['POST'])
@require_auth
def create_goal():
    """创建绩效目标"""
    try:
        data = request.get_json()

        if not data.get('employee_id') or not data.get('period_id') or not data.get('goal_name'):
            return jsonify({'error': '员工ID、考核周期ID和目标名称为必填项'}), 400

        # 验证员工存在
        employee = Employee.query.get(data['employee_id'])
        if not employee:
            return jsonify({'error': '员工不存在'}), 404

        # 验证考核周期存在
        period = PerformancePeriod.query.get(data['period_id'])
        if not period:
            return jsonify({'error': '考核周期不存在'}), 404

        goal = PerformanceGoal(
            employee_id=data['employee_id'],
            period_id=data['period_id'],
            kpi_template_id=data.get('kpi_template_id'),
            goal_name=data['goal_name'],
            goal_description=data.get('goal_description'),
            category=data.get('category', 'work'),
            target_value=data.get('target_value'),
            target_unit=data.get('target_unit'),
            weight=data.get('weight', 0),
            max_score=data.get('max_score', 100),
            status='pending'
        )

        db.session.add(goal)
        db.session.commit()

        return jsonify({'message': '创建成功', 'data': goal.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/goals/<int:id>', methods=['PUT'])
@require_auth
def update_goal(id):
    """更新绩效目标"""
    try:
        goal = PerformanceGoal.query.get_or_404(id)
        data = request.get_json()

        for field in ['goal_name', 'goal_description', 'category', 'target_value',
                      'target_unit', 'actual_value', 'weight', 'max_score', 'status']:
            if field in data:
                setattr(goal, field, data[field])

        db.session.commit()
        return jsonify({'message': '更新成功', 'data': goal.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/goals/<int:id>/confirm', methods=['PUT'])
@require_auth
def confirm_goal(id):
    """确认绩效目标"""
    try:
        goal = PerformanceGoal.query.get_or_404(id)

        if goal.status != 'pending':
            return jsonify({'error': '目标已确认'}), 400

        goal.status = 'confirmed'
        db.session.commit()

        return jsonify({'message': '目标已确认', 'data': goal.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/goals/<int:id>/self-evaluate', methods=['PUT'])
@require_auth
def self_evaluate_goal(id):
    """员工自评"""
    try:
        goal = PerformanceGoal.query.get_or_404(id)
        data = request.get_json()

        if goal.status not in ['confirmed', 'in_progress']:
            return jsonify({'error': f'当前状态 {goal.status} 无法自评'}), 400

        goal.self_score = data.get('self_score')
        goal.self_comment = data.get('self_comment')
        goal.actual_value = data.get('actual_value')
        goal.self_evaluated_at = datetime.now()
        goal.status = 'in_progress'

        db.session.commit()
        return jsonify({'message': '自评成功', 'data': goal.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/goals/<int:id>/manager-evaluate', methods=['PUT'])
@require_auth
def manager_evaluate_goal(id):
    """主管评估"""
    try:
        goal = PerformanceGoal.query.get_or_404(id)
        data = request.get_json()

        goal.manager_score = data.get('manager_score')
        goal.manager_comment = data.get('manager_comment')
        goal.manager_id = data.get('manager_id')
        goal.manager_evaluated_at = datetime.now()

        # 计算最终得分（可自定义比例）
        if goal.self_score is not None and goal.manager_score is not None:
            goal.final_score = goal.manager_score  # 以主管评分为准
            goal.weighted_score = goal.final_score * (goal.weight / 100)

        goal.status = 'completed'
        db.session.commit()

        return jsonify({'message': '评估成功', 'data': goal.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/goals/batch-create', methods=['POST'])
@require_auth
def batch_create_goals():
    """批量创建绩效目标（从模板）"""
    try:
        data = request.get_json()
        employee_ids = data.get('employee_ids', [])
        period_id = data.get('period_id')
        template_ids = data.get('template_ids', [])

        if not employee_ids or not period_id:
            return jsonify({'error': '员工IDs和考核周期ID为必填项'}), 400

        # 获取模板
        templates = KPITemplate.query.filter(
            KPITemplate.id.in_(template_ids) if template_ids else KPITemplate.is_active == True
        ).all()

        if not templates:
            return jsonify({'error': '未找到可用的KPI模板'}), 404

        created_count = 0
        errors = []

        for emp_id in employee_ids:
            employee = Employee.query.get(emp_id)
            if not employee:
                errors.append(f'员工ID {emp_id} 不存在')
                continue

            for template in templates:
                # 检查是否已存在
                existing = PerformanceGoal.query.filter_by(
                    employee_id=emp_id,
                    period_id=period_id,
                    kpi_template_id=template.id
                ).first()

                if existing:
                    continue

                goal = PerformanceGoal(
                    employee_id=emp_id,
                    period_id=period_id,
                    kpi_template_id=template.id,
                    goal_name=template.name,
                    goal_description=template.description,
                    category=template.category,
                    weight=template.default_weight,
                    max_score=template.max_score,
                    status='pending'
                )
                db.session.add(goal)
                created_count += 1

        db.session.commit()

        return jsonify({
            'message': f'成功创建 {created_count} 个绩效目标',
            'created_count': created_count,
            'errors': errors
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============ 绩效评估 API ============
@performance_bp.route('/evaluations', methods=['GET'])
@require_auth
def get_evaluations():
    """获取绩效评估列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        period_id = request.args.get('period_id', type=int)
        department_id = request.args.get('department_id', type=int)
        status = request.args.get('status')
        grade = request.args.get('grade')

        query = PerformanceEvaluation.query

        if employee_id:
            query = query.filter(PerformanceEvaluation.employee_id == employee_id)
        if period_id:
            query = query.filter(PerformanceEvaluation.period_id == period_id)
        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)
        if status:
            query = query.filter(PerformanceEvaluation.status == status)
        if grade:
            query = query.filter(PerformanceEvaluation.grade == grade)

        query = query.order_by(PerformanceEvaluation.final_total_score.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [e.to_dict() for e in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/evaluations/<int:id>', methods=['GET'])
@require_auth
def get_evaluation(id):
    """获取绩效评估详情"""
    try:
        evaluation = PerformanceEvaluation.query.get_or_404(id)

        # 获取关联的目标
        goals = PerformanceGoal.query.filter_by(
            employee_id=evaluation.employee_id,
            period_id=evaluation.period_id
        ).all()

        result = evaluation.to_dict()
        result['goals'] = [g.to_dict() for g in goals]

        return jsonify({'data': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/evaluations', methods=['POST'])
@require_auth
def create_evaluation():
    """创建绩效评估"""
    try:
        data = request.get_json()

        if not data.get('employee_id') or not data.get('period_id'):
            return jsonify({'error': '员工ID和考核周期ID为必填项'}), 400

        # 检查是否已存在
        existing = PerformanceEvaluation.query.filter_by(
            employee_id=data['employee_id'],
            period_id=data['period_id']
        ).first()

        if existing:
            return jsonify({'error': '该员工本周期的评估已存在'}), 400

        evaluation = PerformanceEvaluation(
            employee_id=data['employee_id'],
            period_id=data['period_id'],
            status='not_started'
        )

        db.session.add(evaluation)
        db.session.commit()

        return jsonify({'message': '创建成功', 'data': evaluation.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/evaluations/<int:id>/calculate', methods=['PUT'])
@require_auth
def calculate_evaluation(id):
    """计算绩效评估总分"""
    try:
        evaluation = PerformanceEvaluation.query.get_or_404(id)

        # 获取所有目标
        goals = PerformanceGoal.query.filter_by(
            employee_id=evaluation.employee_id,
            period_id=evaluation.period_id
        ).all()

        if not goals:
            return jsonify({'error': '该员工没有设置绩效目标'}), 400

        # 计算总权重和总分
        total_weight = sum(g.weight for g in goals)
        self_total = sum((g.self_score or 0) * (g.weight / 100) for g in goals if g.self_score)
        manager_total = sum((g.manager_score or 0) * (g.weight / 100) for g in goals if g.manager_score)
        final_total = sum((g.final_score or 0) * (g.weight / 100) for g in goals if g.final_score)

        evaluation.total_weight = total_weight
        evaluation.self_total_score = self_total
        evaluation.manager_total_score = manager_total
        evaluation.final_total_score = final_total

        # 确定等级
        grade, grade_desc = get_grade_by_score(final_total)
        evaluation.grade = grade
        evaluation.grade_description = grade_desc

        evaluation.status = 'completed'
        evaluation.evaluated_at = datetime.now()

        db.session.commit()
        return jsonify({'message': '计算完成', 'data': evaluation.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/evaluations/<int:id>/submit', methods=['PUT'])
@require_auth
def submit_evaluation(id):
    """提交绩效评估"""
    try:
        evaluation = PerformanceEvaluation.query.get_or_404(id)
        data = request.get_json()

        evaluation.self_summary = data.get('self_summary')
        evaluation.status = 'self_evaluation'

        db.session.commit()
        return jsonify({'message': '提交成功', 'data': evaluation.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/evaluations/<int:id>/approve', methods=['PUT'])
@require_auth
def approve_evaluation(id):
    """审批绩效评估"""
    try:
        evaluation = PerformanceEvaluation.query.get_or_404(id)
        data = request.get_json()

        evaluation.manager_summary = data.get('manager_summary')
        evaluation.improvement_suggestions = data.get('improvement_suggestions')
        evaluation.development_plan = data.get('development_plan')
        evaluation.evaluator_id = data.get('evaluator_id')
        evaluation.evaluated_at = datetime.now()
        evaluation.status = 'completed'

        db.session.commit()
        return jsonify({'message': '审批成功', 'data': evaluation.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/evaluations/<int:id>/calibrate', methods=['PUT'])
@require_auth
def calibrate_evaluation(id):
    """校准绩效评估"""
    try:
        evaluation = PerformanceEvaluation.query.get_or_404(id)
        data = request.get_json()

        new_score = data.get('final_total_score')
        if new_score is None:
            return jsonify({'error': '请提供校准后的分数'}), 400

        # 记录校准前分数
        evaluation.score_before_calibration = evaluation.final_total_score
        evaluation.final_total_score = new_score

        # 重新确定等级
        grade, grade_desc = get_grade_by_score(new_score)
        evaluation.grade = grade
        evaluation.grade_description = grade_desc

        evaluation.is_calibrated = True
        evaluation.calibrated_by = data.get('calibrated_by')
        evaluation.calibrated_at = datetime.now()
        evaluation.calibration_reason = data.get('calibration_reason')

        db.session.commit()
        return jsonify({'message': '校准成功', 'data': evaluation.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/evaluations/batch-create', methods=['POST'])
@require_auth
def batch_create_evaluations():
    """批量创建绩效评估"""
    try:
        data = request.get_json()
        employee_ids = data.get('employee_ids', [])
        period_id = data.get('period_id')
        department_id = data.get('department_id')
        factory_id = data.get('factory_id')

        if not period_id:
            return jsonify({'error': '考核周期ID为必填项'}), 400

        # 获取员工列表
        if employee_ids:
            employees = Employee.query.filter(
                Employee.id.in_(employee_ids),
                Employee.employment_status == 'Active'
            ).all()
        else:
            query = Employee.query.filter(Employee.employment_status == 'Active')
            if department_id:
                query = query.filter(Employee.department_id == department_id)
            if factory_id:
                query = query.filter(Employee.factory_id == factory_id)
            employees = query.all()

        created_count = 0
        skipped_count = 0

        for emp in employees:
            existing = PerformanceEvaluation.query.filter_by(
                employee_id=emp.id,
                period_id=period_id
            ).first()

            if existing:
                skipped_count += 1
                continue

            evaluation = PerformanceEvaluation(
                employee_id=emp.id,
                period_id=period_id,
                status='not_started'
            )
            db.session.add(evaluation)
            created_count += 1

        db.session.commit()

        return jsonify({
            'message': f'成功创建 {created_count} 个评估，跳过 {skipped_count} 个已存在的',
            'created_count': created_count,
            'skipped_count': skipped_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============ 等级配置 API ============
@performance_bp.route('/grade-configs', methods=['GET'])
@require_auth
def get_grade_configs():
    """获取绩效等级配置列表"""
    try:
        is_active = request.args.get('is_active', 'true')

        query = PerformanceGradeConfig.query

        if is_active.lower() == 'true':
            query = query.filter(PerformanceGradeConfig.is_active == True)

        configs = query.order_by(PerformanceGradeConfig.sort_order).all()

        return jsonify({
            'items': [c.to_dict() for c in configs],
            'total': len(configs)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/grade-configs', methods=['POST'])
@require_auth
def create_grade_config():
    """创建绩效等级配置"""
    try:
        data = request.get_json()

        if not data.get('grade') or not data.get('name'):
            return jsonify({'error': '等级和名称为必填项'}), 400

        existing = PerformanceGradeConfig.query.filter_by(grade=data['grade']).first()
        if existing:
            return jsonify({'error': f'等级 {data["grade"]} 已存在'}), 400

        config = PerformanceGradeConfig(
            grade=data['grade'],
            name=data['name'],
            min_score=data.get('min_score', 0),
            max_score=data.get('max_score', 100),
            target_percentage=data.get('target_percentage'),
            max_percentage=data.get('max_percentage'),
            bonus_coefficient=data.get('bonus_coefficient', 1.0),
            sort_order=data.get('sort_order', 0),
            color=data.get('color'),
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )

        db.session.add(config)
        db.session.commit()

        return jsonify({'message': '创建成功', 'data': config.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/grade-configs/<int:id>', methods=['PUT'])
@require_auth
def update_grade_config(id):
    """更新绩效等级配置"""
    try:
        config = PerformanceGradeConfig.query.get_or_404(id)
        data = request.get_json()

        for field in ['name', 'min_score', 'max_score', 'target_percentage', 'max_percentage',
                      'bonus_coefficient', 'sort_order', 'color', 'description', 'is_active']:
            if field in data:
                setattr(config, field, data[field])

        db.session.commit()
        return jsonify({'message': '更新成功', 'data': config.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/grade-configs/init', methods=['POST'])
@require_auth
def init_grade_configs():
    """初始化默认等级配置"""
    try:
        init_default_grade_configs()
        return jsonify({'message': '初始化成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ 绩效反馈 API ============
@performance_bp.route('/feedbacks', methods=['GET'])
@require_auth
def get_feedbacks():
    """获取绩效反馈列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        period_id = request.args.get('period_id', type=int)
        feedback_type = request.args.get('feedback_type')

        query = PerformanceFeedback.query

        if employee_id:
            query = query.filter(PerformanceFeedback.employee_id == employee_id)
        if period_id:
            query = query.filter(PerformanceFeedback.period_id == period_id)
        if feedback_type:
            query = query.filter(PerformanceFeedback.feedback_type == feedback_type)

        query = query.order_by(PerformanceFeedback.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [f.to_dict() for f in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/feedbacks', methods=['POST'])
@require_auth
def create_feedback():
    """创建绩效反馈"""
    try:
        data = request.get_json()

        if not data.get('employee_id') or not data.get('content') or not data.get('feedback_by'):
            return jsonify({'error': '员工ID、反馈内容和反馈人为必填项'}), 400

        feedback = PerformanceFeedback(
            employee_id=data['employee_id'],
            period_id=data.get('period_id'),
            goal_id=data.get('goal_id'),
            feedback_type=data.get('feedback_type', 'general'),
            content=data['content'],
            feedback_by=data['feedback_by'],
            feedback_by_name=data.get('feedback_by_name'),
            is_visible_to_employee=data.get('is_visible_to_employee', True)
        )

        db.session.add(feedback)
        db.session.commit()

        return jsonify({'message': '反馈成功', 'data': feedback.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============ 统计报表 API ============
@performance_bp.route('/reports/ranking', methods=['GET'])
@require_auth
def get_ranking():
    """获取绩效排名"""
    try:
        period_id = request.args.get('period_id', type=int)
        department_id = request.args.get('department_id', type=int)
        factory_id = request.args.get('factory_id', type=int)
        limit = request.args.get('limit', 20, type=int)

        if not period_id:
            return jsonify({'error': '考核周期ID为必填项'}), 400

        query = PerformanceEvaluation.query.filter(
            PerformanceEvaluation.period_id == period_id,
            PerformanceEvaluation.status == 'completed'
        )

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)
        if factory_id:
            query = query.join(Employee).filter(Employee.factory_id == factory_id)

        evaluations = query.order_by(PerformanceEvaluation.final_total_score.desc()).limit(limit).all()

        ranking = []
        for i, evaluation in enumerate(evaluations, 1):
            item = evaluation.to_dict()
            item['rank'] = i
            ranking.append(item)

        return jsonify({
            'items': ranking,
            'total': len(ranking)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/reports/grade-distribution', methods=['GET'])
@require_auth
def get_grade_distribution():
    """获取绩效等级分布"""
    try:
        period_id = request.args.get('period_id', type=int)
        department_id = request.args.get('department_id', type=int)

        if not period_id:
            return jsonify({'error': '考核周期ID为必填项'}), 400

        query = PerformanceEvaluation.query.filter(
            PerformanceEvaluation.period_id == period_id,
            PerformanceEvaluation.status == 'completed'
        )

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        # 按等级分组统计
        distribution = db.session.query(
            PerformanceEvaluation.grade,
            func.count(PerformanceEvaluation.id).label('count')
        ).filter(
            PerformanceEvaluation.period_id == period_id,
            PerformanceEvaluation.status == 'completed'
        ).group_by(PerformanceEvaluation.grade).all()

        total = sum(d.count for d in distribution)

        result = []
        for d in distribution:
            result.append({
                'grade': d.grade,
                'count': d.count,
                'percentage': round((d.count / total * 100), 2) if total > 0 else 0
            })

        return jsonify({
            'items': result,
            'total': total
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@performance_bp.route('/reports/summary', methods=['GET'])
@require_auth
def get_performance_summary():
    """获取绩效统计汇总"""
    try:
        period_id = request.args.get('period_id', type=int)
        department_id = request.args.get('department_id', type=int)

        if not period_id:
            return jsonify({'error': '考核周期ID为必填项'}), 400

        query = PerformanceEvaluation.query.filter(PerformanceEvaluation.period_id == period_id)

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        evaluations = query.all()

        if not evaluations:
            return jsonify({
                'period_id': period_id,
                'total_employees': 0,
                'completed_count': 0,
                'avg_score': 0,
                'max_score': 0,
                'min_score': 0
            })

        completed = [e for e in evaluations if e.status == 'completed']
        scores = [e.final_total_score for e in completed if e.final_total_score]

        return jsonify({
            'period_id': period_id,
            'total_employees': len(evaluations),
            'completed_count': len(completed),
            'pending_count': len([e for e in evaluations if e.status != 'completed']),
            'avg_score': round(sum(scores) / len(scores), 2) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'by_status': {
                'not_started': len([e for e in evaluations if e.status == 'not_started']),
                'in_progress': len([e for e in evaluations if e.status == 'in_progress']),
                'self_evaluation': len([e for e in evaluations if e.status == 'self_evaluation']),
                'manager_evaluation': len([e for e in evaluations if e.status == 'manager_evaluation']),
                'completed': len(completed)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
