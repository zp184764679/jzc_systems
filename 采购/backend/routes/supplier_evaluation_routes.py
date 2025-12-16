# routes/supplier_evaluation_routes.py
# -*- coding: utf-8 -*-
"""
供应商评估 API 路由
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import or_, and_, func
from datetime import datetime
import json
import logging

from extensions import db
from models.supplier_evaluation import (
    EvaluationTemplate,
    EvaluationCriteria,
    SupplierEvaluation,
    EvaluationScore,
    EVALUATION_STATUS_LABELS,
    PERIOD_TYPE_LABELS,
    GRADE_LABELS,
    generate_evaluation_no,
    init_default_template,
)
from models.supplier import Supplier

logger = logging.getLogger(__name__)

# URL 前缀
URL_PREFIX = '/api/v1'

# 创建蓝图
evaluation_template_bp = Blueprint('evaluation_template', __name__)
supplier_evaluation_bp = Blueprint('supplier_evaluation', __name__)

BLUEPRINTS = [evaluation_template_bp, supplier_evaluation_bp]


# ==================== 评估模板 API ====================

@evaluation_template_bp.route('/evaluation-templates', methods=['GET'])
def get_templates():
    """获取评估模板列表"""
    try:
        # 查询参数
        is_active = request.args.get('is_active')
        supplier_category = request.args.get('supplier_category')

        query = EvaluationTemplate.query

        if is_active is not None:
            query = query.filter(EvaluationTemplate.is_active == (is_active.lower() == 'true'))

        if supplier_category:
            query = query.filter(
                or_(
                    EvaluationTemplate.supplier_category == supplier_category,
                    EvaluationTemplate.supplier_category.is_(None)
                )
            )

        templates = query.order_by(EvaluationTemplate.is_default.desc(), EvaluationTemplate.created_at.desc()).all()

        return jsonify({
            'success': True,
            'data': [t.to_dict(include_criteria=False) for t in templates]
        })
    except Exception as e:
        logger.error(f"获取评估模板列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@evaluation_template_bp.route('/evaluation-templates/<int:template_id>', methods=['GET'])
def get_template_detail(template_id):
    """获取评估模板详情（含指标）"""
    try:
        template = EvaluationTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': '模板不存在'}), 404

        return jsonify({
            'success': True,
            'data': template.to_dict(include_criteria=True)
        })
    except Exception as e:
        logger.error(f"获取评估模板详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@evaluation_template_bp.route('/evaluation-templates', methods=['POST'])
def create_template():
    """创建评估模板"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('code') or not data.get('name'):
            return jsonify({'success': False, 'error': '模板编码和名称为必填项'}), 400

        # 检查编码唯一性
        existing = EvaluationTemplate.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'success': False, 'error': f'模板编码 {data["code"]} 已存在'}), 400

        # 创建模板
        template = EvaluationTemplate(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            supplier_category=data.get('supplier_category'),
            period_type=data.get('period_type', 'quarterly'),
            version=data.get('version', '1.0'),
            is_active=data.get('is_active', True),
            is_default=data.get('is_default', False),
        )
        db.session.add(template)
        db.session.flush()

        # 添加评估指标
        criteria_list = data.get('criteria', [])
        for i, c in enumerate(criteria_list):
            criteria = EvaluationCriteria(
                template_id=template.id,
                code=c.get('code', f'C{i+1}'),
                name=c['name'],
                description=c.get('description'),
                category=c.get('category', 'general'),
                weight=c.get('weight', 10),
                max_score=c.get('max_score', 100),
                min_score=c.get('min_score', 0),
                score_type=c.get('score_type', 'numeric'),
                score_options=c.get('score_options'),
                sort_order=c.get('sort_order', i),
                is_required=c.get('is_required', True),
            )
            db.session.add(criteria)

        # 如果设为默认，取消其他默认模板
        if template.is_default:
            EvaluationTemplate.query.filter(
                EvaluationTemplate.id != template.id,
                EvaluationTemplate.is_default == True
            ).update({'is_default': False})

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '模板创建成功',
            'data': template.to_dict(include_criteria=True)
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建评估模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@evaluation_template_bp.route('/evaluation-templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    """更新评估模板"""
    try:
        template = EvaluationTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': '模板不存在'}), 404

        data = request.get_json()

        # 更新基本信息
        if 'name' in data:
            template.name = data['name']
        if 'description' in data:
            template.description = data['description']
        if 'supplier_category' in data:
            template.supplier_category = data['supplier_category']
        if 'period_type' in data:
            template.period_type = data['period_type']
        if 'version' in data:
            template.version = data['version']
        if 'is_active' in data:
            template.is_active = data['is_active']
        if 'is_default' in data:
            template.is_default = data['is_default']
            if data['is_default']:
                # 取消其他默认模板
                EvaluationTemplate.query.filter(
                    EvaluationTemplate.id != template.id,
                    EvaluationTemplate.is_default == True
                ).update({'is_default': False})

        # 更新评估指标（如果提供）
        if 'criteria' in data:
            # 删除旧指标
            EvaluationCriteria.query.filter_by(template_id=template.id).delete()

            # 添加新指标
            for i, c in enumerate(data['criteria']):
                criteria = EvaluationCriteria(
                    template_id=template.id,
                    code=c.get('code', f'C{i+1}'),
                    name=c['name'],
                    description=c.get('description'),
                    category=c.get('category', 'general'),
                    weight=c.get('weight', 10),
                    max_score=c.get('max_score', 100),
                    min_score=c.get('min_score', 0),
                    score_type=c.get('score_type', 'numeric'),
                    score_options=c.get('score_options'),
                    sort_order=c.get('sort_order', i),
                    is_required=c.get('is_required', True),
                )
                db.session.add(criteria)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '模板更新成功',
            'data': template.to_dict(include_criteria=True)
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新评估模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@evaluation_template_bp.route('/evaluation-templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """删除评估模板"""
    try:
        template = EvaluationTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': '模板不存在'}), 404

        # 检查是否有关联的评估记录
        eval_count = SupplierEvaluation.query.filter_by(template_id=template_id).count()
        if eval_count > 0:
            return jsonify({'success': False, 'error': f'该模板已被 {eval_count} 条评估记录使用，无法删除'}), 400

        db.session.delete(template)
        db.session.commit()

        return jsonify({'success': True, 'message': '模板删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除评估模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@evaluation_template_bp.route('/evaluation-templates/options', methods=['GET'])
def get_template_options():
    """获取模板选项（用于下拉框）"""
    try:
        templates = EvaluationTemplate.query.filter_by(is_active=True).order_by(
            EvaluationTemplate.is_default.desc(),
            EvaluationTemplate.name
        ).all()

        return jsonify({
            'success': True,
            'data': [{
                'id': t.id,
                'code': t.code,
                'name': t.name,
                'is_default': t.is_default,
                'criteria_count': len(t.criteria),
            } for t in templates]
        })
    except Exception as e:
        logger.error(f"获取模板选项失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@evaluation_template_bp.route('/evaluation-templates/init-default', methods=['POST'])
def initialize_default_template():
    """初始化默认评估模板"""
    try:
        template = init_default_template()
        return jsonify({
            'success': True,
            'message': '默认模板已初始化',
            'data': template.to_dict(include_criteria=True)
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"初始化默认模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 供应商评估 API ====================

@supplier_evaluation_bp.route('/supplier-evaluations', methods=['GET'])
def get_evaluations():
    """获取供应商评估列表"""
    try:
        # 查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        supplier_id = request.args.get('supplier_id', type=int)
        template_id = request.args.get('template_id', type=int)
        status = request.args.get('status')
        grade = request.args.get('grade')
        evaluation_period = request.args.get('evaluation_period')
        keyword = request.args.get('keyword')

        query = SupplierEvaluation.query

        # 过滤条件
        if supplier_id:
            query = query.filter(SupplierEvaluation.supplier_id == supplier_id)
        if template_id:
            query = query.filter(SupplierEvaluation.template_id == template_id)
        if status:
            query = query.filter(SupplierEvaluation.status == status)
        if grade:
            query = query.filter(SupplierEvaluation.grade == grade)
        if evaluation_period:
            query = query.filter(SupplierEvaluation.evaluation_period == evaluation_period)
        if keyword:
            query = query.join(Supplier).filter(
                or_(
                    SupplierEvaluation.evaluation_no.ilike(f'%{keyword}%'),
                    Supplier.company_name.ilike(f'%{keyword}%')
                )
            )

        # 排序
        query = query.order_by(SupplierEvaluation.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [e.to_dict() for e in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
            }
        })
    except Exception as e:
        logger.error(f"获取评估列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@supplier_evaluation_bp.route('/supplier-evaluations/<int:evaluation_id>', methods=['GET'])
def get_evaluation_detail(evaluation_id):
    """获取评估详情（含评分）"""
    try:
        evaluation = SupplierEvaluation.query.get(evaluation_id)
        if not evaluation:
            return jsonify({'success': False, 'error': '评估记录不存在'}), 404

        return jsonify({
            'success': True,
            'data': evaluation.to_dict(include_scores=True)
        })
    except Exception as e:
        logger.error(f"获取评估详情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@supplier_evaluation_bp.route('/supplier-evaluations', methods=['POST'])
def create_evaluation():
    """创建供应商评估"""
    try:
        data = request.get_json()

        # 验证必填字段
        supplier_id = data.get('supplier_id')
        template_id = data.get('template_id')
        evaluation_period = data.get('evaluation_period')

        if not supplier_id or not template_id or not evaluation_period:
            return jsonify({'success': False, 'error': '供应商、评估模板和评估周期为必填项'}), 400

        # 验证供应商
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({'success': False, 'error': '供应商不存在'}), 404

        # 验证模板
        template = EvaluationTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': '评估模板不存在'}), 404

        # 检查是否已存在相同周期的评估
        existing = SupplierEvaluation.query.filter_by(
            supplier_id=supplier_id,
            evaluation_period=evaluation_period,
        ).first()
        if existing:
            return jsonify({'success': False, 'error': f'该供应商在 {evaluation_period} 周期已存在评估记录'}), 400

        # 创建评估记录
        evaluation = SupplierEvaluation(
            evaluation_no=generate_evaluation_no(),
            supplier_id=supplier_id,
            template_id=template_id,
            evaluation_period=evaluation_period,
            period_type=data.get('period_type', template.period_type),
            period_start=datetime.fromisoformat(data['period_start']) if data.get('period_start') else None,
            period_end=datetime.fromisoformat(data['period_end']) if data.get('period_end') else None,
            status='draft',
            evaluator_id=data.get('evaluator_id'),
            evaluator_name=data.get('evaluator_name'),
        )
        db.session.add(evaluation)
        db.session.flush()

        # 根据模板指标创建评分记录
        for criteria in template.criteria:
            score = EvaluationScore(
                evaluation_id=evaluation.id,
                criteria_id=criteria.id,
            )
            db.session.add(score)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '评估记录创建成功',
            'data': evaluation.to_dict(include_scores=True)
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建评估记录失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@supplier_evaluation_bp.route('/supplier-evaluations/<int:evaluation_id>', methods=['PUT'])
def update_evaluation(evaluation_id):
    """更新供应商评估"""
    try:
        evaluation = SupplierEvaluation.query.get(evaluation_id)
        if not evaluation:
            return jsonify({'success': False, 'error': '评估记录不存在'}), 404

        if evaluation.status == 'completed':
            return jsonify({'success': False, 'error': '已完成的评估不能修改'}), 400

        data = request.get_json()

        # 更新基本信息
        if 'summary' in data:
            evaluation.summary = data['summary']
        if 'strengths' in data:
            evaluation.strengths = data['strengths']
        if 'weaknesses' in data:
            evaluation.weaknesses = data['weaknesses']
        if 'improvement_plan' in data:
            evaluation.improvement_plan = data['improvement_plan']
        if 'evaluator_id' in data:
            evaluation.evaluator_id = data['evaluator_id']
        if 'evaluator_name' in data:
            evaluation.evaluator_name = data['evaluator_name']

        # 更新评分（如果提供）
        if 'scores' in data:
            for score_data in data['scores']:
                score = EvaluationScore.query.filter_by(
                    evaluation_id=evaluation.id,
                    criteria_id=score_data['criteria_id']
                ).first()
                if score:
                    if 'score' in score_data:
                        score.score = score_data['score']
                        score.calculate_weighted_score()
                    if 'comment' in score_data:
                        score.comment = score_data['comment']
                    if 'evidence' in score_data:
                        score.evidence = score_data['evidence']

            # 重新计算总分
            evaluation.calculate_total_score()

            # 计算各维度得分
            dimension_scores = {}
            for score in evaluation.scores:
                if score.criteria and score.score is not None:
                    category = score.criteria.category
                    if category not in dimension_scores:
                        dimension_scores[category] = {'total': 0, 'weight': 0}
                    dimension_scores[category]['total'] += score.score * score.criteria.weight
                    dimension_scores[category]['weight'] += score.criteria.weight

            # 计算平均
            for cat, val in dimension_scores.items():
                if val['weight'] > 0:
                    dimension_scores[cat] = round(val['total'] / val['weight'], 2)
                else:
                    dimension_scores[cat] = 0
            evaluation.dimension_scores = json.dumps(dimension_scores)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '评估记录更新成功',
            'data': evaluation.to_dict(include_scores=True)
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新评估记录失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@supplier_evaluation_bp.route('/supplier-evaluations/<int:evaluation_id>', methods=['DELETE'])
def delete_evaluation(evaluation_id):
    """删除供应商评估"""
    try:
        evaluation = SupplierEvaluation.query.get(evaluation_id)
        if not evaluation:
            return jsonify({'success': False, 'error': '评估记录不存在'}), 404

        if evaluation.status not in ['draft', 'cancelled']:
            return jsonify({'success': False, 'error': '只能删除草稿或已取消的评估'}), 400

        db.session.delete(evaluation)
        db.session.commit()

        return jsonify({'success': True, 'message': '评估记录已删除'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除评估记录失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@supplier_evaluation_bp.route('/supplier-evaluations/<int:evaluation_id>/start', methods=['POST'])
def start_evaluation(evaluation_id):
    """开始评估"""
    try:
        evaluation = SupplierEvaluation.query.get(evaluation_id)
        if not evaluation:
            return jsonify({'success': False, 'error': '评估记录不存在'}), 404

        if evaluation.status != 'draft':
            return jsonify({'success': False, 'error': '只有草稿状态的评估可以开始'}), 400

        evaluation.status = 'in_progress'
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '评估已开始',
            'data': evaluation.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"开始评估失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@supplier_evaluation_bp.route('/supplier-evaluations/<int:evaluation_id>/complete', methods=['POST'])
def complete_evaluation(evaluation_id):
    """完成评估"""
    try:
        evaluation = SupplierEvaluation.query.get(evaluation_id)
        if not evaluation:
            return jsonify({'success': False, 'error': '评估记录不存在'}), 404

        if evaluation.status not in ['draft', 'in_progress']:
            return jsonify({'success': False, 'error': '当前状态不能完成'}), 400

        # 检查是否所有必填指标都已评分
        for score in evaluation.scores:
            if score.criteria.is_required and score.score is None:
                return jsonify({'success': False, 'error': f'必填指标 {score.criteria.name} 尚未评分'}), 400

        data = request.get_json() or {}

        # 计算总分
        evaluation.calculate_total_score()

        # 更新状态
        evaluation.status = 'completed'
        evaluation.completed_at = datetime.utcnow()

        # 可选：更新评估备注
        if 'summary' in data:
            evaluation.summary = data['summary']
        if 'strengths' in data:
            evaluation.strengths = data['strengths']
        if 'weaknesses' in data:
            evaluation.weaknesses = data['weaknesses']
        if 'improvement_plan' in data:
            evaluation.improvement_plan = data['improvement_plan']

        # 更新供应商评分
        supplier = evaluation.supplier
        if supplier:
            supplier.rating = evaluation.total_score
            supplier.rating_updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '评估已完成',
            'data': evaluation.to_dict(include_scores=True)
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"完成评估失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@supplier_evaluation_bp.route('/supplier-evaluations/<int:evaluation_id>/cancel', methods=['POST'])
def cancel_evaluation(evaluation_id):
    """取消评估"""
    try:
        evaluation = SupplierEvaluation.query.get(evaluation_id)
        if not evaluation:
            return jsonify({'success': False, 'error': '评估记录不存在'}), 404

        if evaluation.status == 'completed':
            return jsonify({'success': False, 'error': '已完成的评估不能取消'}), 400

        evaluation.status = 'cancelled'
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '评估已取消',
            'data': evaluation.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"取消评估失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 统计 API ====================

@supplier_evaluation_bp.route('/supplier-evaluations/statistics/summary', methods=['GET'])
def get_evaluation_statistics():
    """获取评估统计概览"""
    try:
        # 总体统计
        total = SupplierEvaluation.query.count()
        draft = SupplierEvaluation.query.filter_by(status='draft').count()
        in_progress = SupplierEvaluation.query.filter_by(status='in_progress').count()
        completed = SupplierEvaluation.query.filter_by(status='completed').count()

        # 等级分布
        grade_distribution = db.session.query(
            SupplierEvaluation.grade,
            func.count(SupplierEvaluation.id)
        ).filter(
            SupplierEvaluation.status == 'completed',
            SupplierEvaluation.grade.isnot(None)
        ).group_by(SupplierEvaluation.grade).all()

        grade_stats = {grade: count for grade, count in grade_distribution}

        # 平均分
        avg_score = db.session.query(func.avg(SupplierEvaluation.total_score)).filter(
            SupplierEvaluation.status == 'completed',
            SupplierEvaluation.total_score.isnot(None)
        ).scalar()

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'by_status': {
                    'draft': draft,
                    'in_progress': in_progress,
                    'completed': completed,
                },
                'by_grade': grade_stats,
                'average_score': round(avg_score, 2) if avg_score else 0,
            }
        })
    except Exception as e:
        logger.error(f"获取评估统计失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@supplier_evaluation_bp.route('/supplier-evaluations/statistics/supplier-ranking', methods=['GET'])
def get_supplier_ranking():
    """获取供应商排名"""
    try:
        limit = request.args.get('limit', 10, type=int)
        period = request.args.get('period')  # 可选过滤周期

        query = db.session.query(
            SupplierEvaluation.supplier_id,
            Supplier.company_name,
            func.avg(SupplierEvaluation.total_score).label('avg_score'),
            func.count(SupplierEvaluation.id).label('eval_count'),
            func.max(SupplierEvaluation.grade).label('latest_grade'),
        ).join(Supplier).filter(
            SupplierEvaluation.status == 'completed',
            SupplierEvaluation.total_score.isnot(None)
        )

        if period:
            query = query.filter(SupplierEvaluation.evaluation_period == period)

        query = query.group_by(
            SupplierEvaluation.supplier_id,
            Supplier.company_name
        ).order_by(func.avg(SupplierEvaluation.total_score).desc()).limit(limit)

        results = query.all()

        return jsonify({
            'success': True,
            'data': [{
                'rank': i + 1,
                'supplier_id': r[0],
                'supplier_name': r[1],
                'avg_score': round(r[2], 2),
                'eval_count': r[3],
                'latest_grade': r[4],
            } for i, r in enumerate(results)]
        })
    except Exception as e:
        logger.error(f"获取供应商排名失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 枚举 API ====================

@supplier_evaluation_bp.route('/supplier-evaluations/enums', methods=['GET'])
def get_evaluation_enums():
    """获取评估相关枚举值"""
    return jsonify({
        'success': True,
        'data': {
            'status': EVALUATION_STATUS_LABELS,
            'period_type': PERIOD_TYPE_LABELS,
            'grade': GRADE_LABELS,
            'criteria_category': {
                'quality': '质量',
                'delivery': '交期',
                'service': '服务',
                'price': '价格',
                'technology': '技术',
                'general': '综合',
            }
        }
    })
