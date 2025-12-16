# -*- coding: utf-8 -*-
"""
Customer Grade Management API - 客户分级管理
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc

from .. import db
from ..models.customer import Customer

customer_grades_bp = Blueprint('customer_grades', __name__, url_prefix='/api/customer-grades')

# 客户等级配置
CUSTOMER_GRADES = {
    'vip': {'label': 'VIP客户', 'color': '#f5222d', 'min_score': 90, 'order': 1},
    'gold': {'label': '金牌客户', 'color': '#faad14', 'min_score': 70, 'order': 2},
    'silver': {'label': '银牌客户', 'color': '#1890ff', 'min_score': 50, 'order': 3},
    'regular': {'label': '普通客户', 'color': '#8c8c8c', 'min_score': 0, 'order': 4},
}


@customer_grades_bp.route('/config', methods=['GET'])
def get_grade_config():
    """获取客户等级配置"""
    return jsonify({
        'grades': CUSTOMER_GRADES,
        'grade_options': [
            {'value': k, 'label': v['label'], 'color': v['color']}
            for k, v in sorted(CUSTOMER_GRADES.items(), key=lambda x: x[1]['order'])
        ]
    })


@customer_grades_bp.route('/statistics', methods=['GET'])
def get_grade_statistics():
    """获取客户分级统计"""
    try:
        # 按等级统计客户数量
        grade_stats = db.session.query(
            Customer.grade,
            func.count(Customer.id).label('count')
        ).group_by(Customer.grade).all()

        # 转换为字典
        stats_dict = {g: 0 for g in CUSTOMER_GRADES.keys()}
        for grade, count in grade_stats:
            if grade in stats_dict:
                stats_dict[grade] = count
            else:
                stats_dict['regular'] = stats_dict.get('regular', 0) + count

        # 计算总数和占比
        total = sum(stats_dict.values())
        distribution = []
        for grade_key in ['vip', 'gold', 'silver', 'regular']:
            grade_info = CUSTOMER_GRADES[grade_key]
            count = stats_dict.get(grade_key, 0)
            distribution.append({
                'grade': grade_key,
                'label': grade_info['label'],
                'color': grade_info['color'],
                'count': count,
                'percentage': round(count / total * 100, 1) if total > 0 else 0
            })

        # 重点客户统计
        key_account_count = Customer.query.filter_by(is_key_account=True).count()

        return jsonify({
            'total': total,
            'distribution': distribution,
            'key_account_count': key_account_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@customer_grades_bp.route('/batch-update', methods=['POST'])
def batch_update_grades():
    """批量更新客户等级"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供数据'}), 400

    customer_ids = data.get('customer_ids', [])
    new_grade = data.get('grade')
    is_key_account = data.get('is_key_account')

    if not customer_ids:
        return jsonify({'error': '请选择客户'}), 400

    if not new_grade and is_key_account is None:
        return jsonify({'error': '请提供等级或重点客户标记'}), 400

    try:
        updated = 0
        for customer_id in customer_ids:
            customer = Customer.query.get(customer_id)
            if customer:
                if new_grade and new_grade in CUSTOMER_GRADES:
                    customer.grade = new_grade
                    customer.grade_updated_at = datetime.utcnow()
                if is_key_account is not None:
                    customer.is_key_account = bool(is_key_account)
                updated += 1

        db.session.commit()

        return jsonify({
            'message': f'成功更新 {updated} 个客户',
            'updated_count': updated
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@customer_grades_bp.route('/customer/<int:customer_id>', methods=['PUT'])
def update_customer_grade(customer_id):
    """更新单个客户等级"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供数据'}), 400

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'error': '客户不存在'}), 404

    try:
        if 'grade' in data:
            new_grade = data['grade']
            if new_grade not in CUSTOMER_GRADES:
                return jsonify({'error': f'无效的等级: {new_grade}'}), 400
            if customer.grade != new_grade:
                customer.grade = new_grade
                customer.grade_updated_at = datetime.utcnow()

        if 'grade_score' in data:
            customer.grade_score = int(data['grade_score'])

        if 'is_key_account' in data:
            customer.is_key_account = bool(data['is_key_account'])

        db.session.commit()

        return jsonify({
            'message': '更新成功',
            'customer': customer.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@customer_grades_bp.route('/by-grade/<grade>', methods=['GET'])
def get_customers_by_grade(grade):
    """按等级获取客户列表"""
    if grade not in CUSTOMER_GRADES:
        return jsonify({'error': f'无效的等级: {grade}'}), 400

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    query = Customer.query.filter_by(grade=grade)

    # 支持关键字搜索
    keyword = request.args.get('keyword', '')
    if keyword:
        like = f'%{keyword}%'
        query = query.filter(
            db.or_(
                Customer.code.ilike(like),
                Customer.short_name.ilike(like),
                Customer.name.ilike(like)
            )
        )

    total = query.count()
    customers = query.order_by(desc(Customer.grade_score), Customer.id).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return jsonify({
        'items': [c.to_dict() for c in customers],
        'total': total,
        'page': page,
        'page_size': page_size,
        'pages': (total + page_size - 1) // page_size if page_size else 1,
        'grade': grade,
        'grade_info': CUSTOMER_GRADES[grade]
    })


@customer_grades_bp.route('/key-accounts', methods=['GET'])
def get_key_accounts():
    """获取重点客户列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    query = Customer.query.filter_by(is_key_account=True)

    # 支持关键字搜索
    keyword = request.args.get('keyword', '')
    if keyword:
        like = f'%{keyword}%'
        query = query.filter(
            db.or_(
                Customer.code.ilike(like),
                Customer.short_name.ilike(like),
                Customer.name.ilike(like)
            )
        )

    total = query.count()
    customers = query.order_by(desc(Customer.grade_score), Customer.id).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return jsonify({
        'items': [c.to_dict() for c in customers],
        'total': total,
        'page': page,
        'page_size': page_size,
        'pages': (total + page_size - 1) // page_size if page_size else 1
    })


@customer_grades_bp.route('/auto-grade', methods=['POST'])
def auto_grade_customers():
    """
    根据评分自动分级客户
    评分规则可基于订单金额、订单数量、付款及时率等
    """
    data = request.get_json() or {}
    customer_ids = data.get('customer_ids')  # 可选，不传则处理所有客户

    try:
        query = Customer.query
        if customer_ids:
            query = query.filter(Customer.id.in_(customer_ids))

        customers = query.all()
        updated = 0

        for customer in customers:
            score = customer.grade_score or 0

            # 根据评分确定等级
            new_grade = 'regular'
            for grade_key, grade_info in sorted(
                CUSTOMER_GRADES.items(),
                key=lambda x: x[1]['min_score'],
                reverse=True
            ):
                if score >= grade_info['min_score']:
                    new_grade = grade_key
                    break

            if customer.grade != new_grade:
                customer.grade = new_grade
                customer.grade_updated_at = datetime.utcnow()
                updated += 1

        db.session.commit()

        return jsonify({
            'message': f'自动分级完成，更新了 {updated} 个客户',
            'total_processed': len(customers),
            'updated_count': updated
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@customer_grades_bp.route('/update-score/<int:customer_id>', methods=['POST'])
def update_customer_score(customer_id):
    """更新客户评分"""
    data = request.get_json()
    if not data or 'score' not in data:
        return jsonify({'error': '请提供评分'}), 400

    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'error': '客户不存在'}), 404

    try:
        score = int(data['score'])
        if score < 0 or score > 100:
            return jsonify({'error': '评分必须在 0-100 之间'}), 400

        customer.grade_score = score

        # 可选：自动根据评分更新等级
        auto_update_grade = data.get('auto_update_grade', False)
        if auto_update_grade:
            for grade_key, grade_info in sorted(
                CUSTOMER_GRADES.items(),
                key=lambda x: x[1]['min_score'],
                reverse=True
            ):
                if score >= grade_info['min_score']:
                    if customer.grade != grade_key:
                        customer.grade = grade_key
                        customer.grade_updated_at = datetime.utcnow()
                    break

        db.session.commit()

        return jsonify({
            'message': '评分更新成功',
            'customer': customer.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
