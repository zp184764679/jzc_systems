"""
产品主数据 API 路由
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from models import db, ProductMaster

products_bp = Blueprint('products', __name__)


def get_current_user():
    """从请求头获取当前用户信息"""
    from shared.auth.jwt_utils import verify_token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        try:
            payload = verify_token(token)
            return {
                'user_id': payload.get('user_id') or payload.get('id'),
                'username': payload.get('username'),
                'full_name': payload.get('full_name', payload.get('username'))
            }
        except:
            pass
    return None


@products_bp.route('/products', methods=['GET'])
def get_products():
    """获取产品列表"""
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # 搜索和筛选参数
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        status = request.args.get('status', '').strip()
        customer_id = request.args.get('customer_id', type=int)

        # 构建查询
        query = ProductMaster.query.filter_by(is_active=True)

        # 搜索（品番号、产品名、客户名）
        if search:
            search_term = f'%{search}%'
            query = query.filter(or_(
                ProductMaster.part_number.like(search_term),
                ProductMaster.product_name.like(search_term),
                ProductMaster.customer_name.like(search_term),
                ProductMaster.customer_part_number.like(search_term)
            ))

        # 分类筛选
        if category:
            query = query.filter_by(category=category)

        # 状态筛选
        if status:
            query = query.filter_by(status=status)

        # 客户筛选
        if customer_id:
            query = query.filter_by(customer_id=customer_id)

        # 排序
        sort_by = request.args.get('sort_by', 'updated_at')
        sort_order = request.args.get('sort_order', 'desc')
        if hasattr(ProductMaster, sort_by):
            order_col = getattr(ProductMaster, sort_by)
            if sort_order == 'desc':
                order_col = order_col.desc()
            query = query.order_by(order_col)

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """获取单个产品详情"""
    try:
        include_relations = request.args.get('include_relations', 'true').lower() == 'true'
        product = ProductMaster.query.get_or_404(product_id)
        return jsonify({
            'success': True,
            'data': product.to_dict(include_relations=include_relations)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/products/by-part/<part_number>', methods=['GET'])
def get_product_by_part_number(part_number):
    """按品番号获取产品"""
    try:
        include_relations = request.args.get('include_relations', 'true').lower() == 'true'
        product = ProductMaster.query.filter_by(part_number=part_number).first_or_404()
        return jsonify({
            'success': True,
            'data': product.to_dict(include_relations=include_relations)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/products', methods=['POST'])
def create_product():
    """创建产品"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('part_number'):
            return jsonify({'success': False, 'error': '品番号不能为空'}), 400
        if not data.get('product_name'):
            return jsonify({'success': False, 'error': '产品名称不能为空'}), 400

        # 检查品番号是否已存在
        existing = ProductMaster.query.filter_by(part_number=data['part_number']).first()
        if existing:
            return jsonify({'success': False, 'error': f"品番号 {data['part_number']} 已存在"}), 400

        # 获取当前用户
        user = get_current_user()

        # 创建产品
        product = ProductMaster(
            part_number=data['part_number'],
            product_name=data['product_name'],
            product_name_en=data.get('product_name_en'),
            product_name_ja=data.get('product_name_ja'),
            customer_id=data.get('customer_id'),
            customer_name=data.get('customer_name'),
            customer_part_number=data.get('customer_part_number'),
            category=data.get('category'),
            sub_category=data.get('sub_category'),
            status=data.get('status', 'draft'),
            description=data.get('description'),
            remarks=data.get('remarks'),
            quotation_product_id=data.get('quotation_product_id'),
            created_by=user['user_id'] if user else None,
            created_by_name=user['full_name'] if user else None
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': '产品创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """更新产品"""
    try:
        product = ProductMaster.query.get_or_404(product_id)
        data = request.get_json()

        # 获取当前用户
        user = get_current_user()

        # 更新字段
        updatable_fields = [
            'product_name', 'product_name_en', 'product_name_ja',
            'customer_id', 'customer_name', 'customer_part_number',
            'category', 'sub_category', 'status', 'description', 'remarks',
            'quotation_product_id'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(product, field, data[field])

        # 更新审计字段
        if user:
            product.updated_by = user['user_id']
            product.updated_by_name = user['full_name']

        db.session.commit()

        return jsonify({
            'success': True,
            'data': product.to_dict(),
            'message': '产品更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """删除产品（软删除）"""
    try:
        product = ProductMaster.query.get_or_404(product_id)
        product.is_active = False
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '产品已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/products/search', methods=['GET'])
def search_products():
    """搜索产品（简化版，用于下拉选择等）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        limit = request.args.get('limit', 20, type=int)

        if not keyword:
            return jsonify({'success': True, 'data': []})

        search_term = f'%{keyword}%'
        products = ProductMaster.query.filter(
            ProductMaster.is_active == True,
            or_(
                ProductMaster.part_number.like(search_term),
                ProductMaster.product_name.like(search_term)
            )
        ).limit(limit).all()

        return jsonify({
            'success': True,
            'data': [{
                'id': p.id,
                'part_number': p.part_number,
                'product_name': p.product_name,
                'customer_name': p.customer_name
            } for p in products]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/products/categories', methods=['GET'])
def get_categories():
    """获取产品分类列表"""
    try:
        categories = db.session.query(ProductMaster.category).filter(
            ProductMaster.is_active == True,
            ProductMaster.category.isnot(None)
        ).distinct().all()

        return jsonify({
            'success': True,
            'data': [c[0] for c in categories if c[0]]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@products_bp.route('/products/statistics', methods=['GET'])
def get_statistics():
    """获取产品统计数据"""
    try:
        total = ProductMaster.query.filter_by(is_active=True).count()

        # 按状态统计
        status_stats = db.session.query(
            ProductMaster.status,
            db.func.count(ProductMaster.id)
        ).filter_by(is_active=True).group_by(ProductMaster.status).all()

        # 按分类统计
        category_stats = db.session.query(
            ProductMaster.category,
            db.func.count(ProductMaster.id)
        ).filter(
            ProductMaster.is_active == True,
            ProductMaster.category.isnot(None)
        ).group_by(ProductMaster.category).all()

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'by_status': {s[0]: s[1] for s in status_stats},
                'by_category': {c[0]: c[1] for c in category_stats if c[0]}
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
