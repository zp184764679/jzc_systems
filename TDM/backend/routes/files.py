"""
文件管理 API 路由
与 Portal FileIndex 集成
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from models import db, ProductMaster, ProductFileLink

files_bp = Blueprint('files', __name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif', 'dwg', 'dxf', 'step', 'stp', 'igs'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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


@files_bp.route('/products/<int:product_id>/files', methods=['GET'])
def get_product_files(product_id):
    """获取产品关联的文件列表"""
    try:
        product = ProductMaster.query.get_or_404(product_id)

        # 筛选参数
        file_type = request.args.get('file_type', '').strip()

        query = product.file_links

        if file_type:
            query = query.filter_by(file_type=file_type)

        file_links = query.order_by(
            ProductFileLink.is_primary.desc(),
            ProductFileLink.display_order
        ).all()

        # 获取 FileIndex 详情
        result = []
        for link in file_links:
            link_data = link.to_dict()
            # 可以从 Portal 的 FileIndex 获取更多文件信息
            # 这里先返回基本信息
            result.append(link_data)

        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/products/<int:product_id>/files/link', methods=['POST'])
def link_file_to_product(product_id):
    """关联现有文件到产品"""
    try:
        product = ProductMaster.query.get_or_404(product_id)
        data = request.get_json()
        user = get_current_user()

        # 验证必填字段
        if not data.get('file_index_id'):
            return jsonify({'success': False, 'error': 'file_index_id 不能为空'}), 400
        if not data.get('file_type'):
            return jsonify({'success': False, 'error': 'file_type 不能为空'}), 400

        # 检查是否已关联
        existing = ProductFileLink.query.filter_by(
            product_id=product_id,
            file_index_id=data['file_index_id']
        ).first()

        if existing:
            return jsonify({'success': False, 'error': '该文件已关联到此产品'}), 400

        # 创建关联
        link = ProductFileLink(
            product_id=product_id,
            part_number=product.part_number,
            file_index_id=data['file_index_id'],
            file_uuid=data.get('file_uuid'),
            file_type=data['file_type'],
            file_name=data.get('file_name'),
            file_category=data.get('file_category'),
            is_primary=data.get('is_primary', False),
            display_order=data.get('display_order', 0),
            description=data.get('description'),
            linked_by=user['user_id'] if user else None,
            linked_by_name=user['full_name'] if user else None
        )

        db.session.add(link)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': link.to_dict(),
            'message': '文件关联成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/products/<int:product_id>/files/<int:link_id>', methods=['DELETE'])
def unlink_file_from_product(product_id, link_id):
    """取消文件与产品的关联"""
    try:
        link = ProductFileLink.query.filter_by(
            id=link_id,
            product_id=product_id
        ).first_or_404()

        db.session.delete(link)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '文件关联已取消'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/products/<int:product_id>/files/<int:link_id>', methods=['PUT'])
def update_file_link(product_id, link_id):
    """更新文件关联信息"""
    try:
        link = ProductFileLink.query.filter_by(
            id=link_id,
            product_id=product_id
        ).first_or_404()

        data = request.get_json()

        # 更新字段
        if 'file_type' in data:
            link.file_type = data['file_type']
        if 'is_primary' in data:
            # 如果设置为主文件，取消其他主文件
            if data['is_primary']:
                ProductFileLink.query.filter_by(
                    product_id=product_id,
                    file_type=link.file_type,
                    is_primary=True
                ).update({'is_primary': False})
            link.is_primary = data['is_primary']
        if 'display_order' in data:
            link.display_order = data['display_order']
        if 'description' in data:
            link.description = data['description']

        db.session.commit()

        return jsonify({
            'success': True,
            'data': link.to_dict(),
            'message': '文件关联信息已更新'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/products/<int:product_id>/files/by-type', methods=['GET'])
def get_files_by_type(product_id):
    """按类型分组获取产品文件"""
    try:
        product = ProductMaster.query.get_or_404(product_id)

        file_links = product.file_links.order_by(
            ProductFileLink.file_type,
            ProductFileLink.is_primary.desc(),
            ProductFileLink.display_order
        ).all()

        # 按类型分组
        grouped = {}
        for link in file_links:
            file_type = link.file_type
            if file_type not in grouped:
                grouped[file_type] = {
                    'type': file_type,
                    'type_name': link.FILE_TYPE_NAMES.get(file_type, {}).get('zh', file_type),
                    'files': []
                }
            grouped[file_type]['files'].append(link.to_dict())

        return jsonify({
            'success': True,
            'data': list(grouped.values())
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/file-types', methods=['GET'])
def get_file_types():
    """获取文件类型列表"""
    return jsonify({
        'success': True,
        'data': [
            {'value': 'drawing', 'label': '图纸', 'label_ja': '図面'},
            {'value': 'specification', 'label': '规格书', 'label_ja': '仕様書'},
            {'value': 'inspection_standard', 'label': '检验标准', 'label_ja': '検査基準書'},
            {'value': 'work_instruction', 'label': '作业指导书', 'label_ja': '作業標準書'},
            {'value': 'process_sheet', 'label': '工程表', 'label_ja': '工程表'},
            {'value': 'photo', 'label': '照片', 'label_ja': '写真'},
            {'value': 'certificate', 'label': '证书', 'label_ja': '証明書'},
            {'value': 'report', 'label': '报告', 'label_ja': 'レポート'},
            {'value': 'contract', 'label': '合同', 'label_ja': '契約書'},
            {'value': 'other', 'label': '其他', 'label_ja': 'その他'},
        ]
    })


@files_bp.route('/products/<int:product_id>/files/search-available', methods=['GET'])
def search_available_files(product_id):
    """搜索可关联的文件（从 FileIndex 中搜索）"""
    try:
        product = ProductMaster.query.get_or_404(product_id)

        # 获取已关联的文件 ID
        linked_ids = [link.file_index_id for link in product.file_links.all()]

        # 这里需要查询 Portal 的 FileIndex 表
        # 由于跨数据库，可以通过 API 调用或直接查询
        # 暂时返回空，需要在实际部署时配置

        return jsonify({
            'success': True,
            'data': [],
            'message': '请通过文件中心搜索并关联文件'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
