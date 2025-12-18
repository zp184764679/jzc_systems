"""
公共文件模板库 API
提供模板上传、下载、管理功能
"""
from flask import Blueprint, request, jsonify, send_file, current_app, g
from datetime import datetime
import os
import sys
import uuid
import shutil
from functools import wraps
from werkzeug.utils import secure_filename
from sqlalchemy import text

from models import SessionLocal

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token


def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': '未提供认证令牌'}), 401

        user = verify_token(token)
        if not user:
            return jsonify({'error': '无效的认证令牌'}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """获取当前用户"""
    return getattr(g, 'current_user', None)

templates_bp = Blueprint('templates', __name__, url_prefix='/api/templates')

# 允许的文件类型
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'doc', 'docx', 'pdf', 'ppt', 'pptx', 'txt', 'csv', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@templates_bp.route('', methods=['GET'])
@require_auth
def get_templates():
    """获取模板列表"""
    category = request.args.get('category')
    customer = request.args.get('customer')
    search = request.args.get('search', '')

    db = SessionLocal()
    try:
        query = "SELECT * FROM file_templates WHERE is_active = 1"
        params = {}

        if category:
            query += " AND category = :category"
            params['category'] = category

        if customer:
            query += " AND customer_name = :customer"
            params['customer'] = customer

        if search:
            query += " AND (name LIKE :search OR description LIKE :search)"
            params['search'] = f'%{search}%'

        query += " ORDER BY created_at DESC"

        result = db.execute(text(query), params)
        templates = [dict(row._mapping) for row in result]

        # 获取分类和客户选项
        categories_result = db.execute(
            text("SELECT DISTINCT category FROM file_templates WHERE is_active = 1 AND category IS NOT NULL")
        )
        categories = [row[0] for row in categories_result]

        customers_result = db.execute(
            text("SELECT DISTINCT customer_name FROM file_templates WHERE is_active = 1 AND customer_name IS NOT NULL")
        )
        customers = [row[0] for row in customers_result]

        return jsonify({
            'templates': templates,
            'total': len(templates),
            'categories': categories,
            'customers': customers
        })
    finally:
        db.close()


@templates_bp.route('', methods=['POST'])
@require_auth
def upload_template():
    """上传新模板"""
    user = get_current_user()

    if 'file' not in request.files:
        return jsonify({'error': '请选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '请选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'不支持的文件类型，允许: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # 获取表单数据
    name = request.form.get('name', file.filename)
    description = request.form.get('description', '')
    category = request.form.get('category', 'general')
    customer_name = request.form.get('customer_name', '')

    # 保存文件
    original_filename = file.filename
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    # 模板存储目录
    upload_folder = current_app.config.get('UPLOAD_FOLDER', '/www/jzc_systems/uploads')
    template_dir = os.path.join(upload_folder, 'templates')
    os.makedirs(template_dir, exist_ok=True)

    file_path = os.path.join(template_dir, unique_filename)
    file.save(file_path)

    # 获取文件大小
    file_size = os.path.getsize(file_path)

    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO file_templates
                (name, description, category, customer_name, file_name, file_path, file_size, file_type, uploaded_by_id, uploaded_by_name)
                VALUES (:name, :desc, :cat, :cust, :fname, :fpath, :fsize, :ftype, :uid, :uname)
            """),
            {
                'name': name,
                'desc': description,
                'cat': category,
                'cust': customer_name or None,
                'fname': original_filename,
                'fpath': file_path,
                'fsize': file_size,
                'ftype': file.content_type,
                'uid': user['user_id'],
                'uname': user.get('username', '')
            }
        )
        db.commit()

        return jsonify({
            'message': '模板上传成功',
            'template': {
                'name': name,
                'file_name': original_filename,
                'category': category,
                'customer_name': customer_name
            }
        })
    finally:
        db.close()


@templates_bp.route('/<int:template_id>', methods=['GET'])
@require_auth
def get_template(template_id):
    """获取单个模板详情"""
    db = SessionLocal()
    try:
        result = db.execute(
            text("SELECT * FROM file_templates WHERE id = :id AND is_active = 1"),
            {'id': template_id}
        )
        template = result.fetchone()

        if not template:
            return jsonify({'error': '模板不存在'}), 404

        return jsonify(dict(template._mapping))
    finally:
        db.close()


@templates_bp.route('/<int:template_id>/download', methods=['GET'])
@require_auth
def download_template(template_id):
    """下载模板文件"""
    db = SessionLocal()
    try:
        result = db.execute(
            text("SELECT * FROM file_templates WHERE id = :id AND is_active = 1"),
            {'id': template_id}
        )
        template = result.fetchone()

        if not template:
            return jsonify({'error': '模板不存在'}), 404

        template_dict = dict(template._mapping)
        file_path = template_dict['file_path']

        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404

        # 更新下载次数
        db.execute(
            text("UPDATE file_templates SET download_count = download_count + 1 WHERE id = :id"),
            {'id': template_id}
        )
        db.commit()

        return send_file(
            file_path,
            as_attachment=True,
            download_name=template_dict['file_name']
        )
    finally:
        db.close()


@templates_bp.route('/<int:template_id>', methods=['PUT'])
@require_auth
def update_template(template_id):
    """更新模板信息"""
    data = request.get_json()

    updates = []
    params = {'id': template_id}

    if 'name' in data:
        updates.append("name = :name")
        params['name'] = data['name']
    if 'description' in data:
        updates.append("description = :description")
        params['description'] = data['description']
    if 'category' in data:
        updates.append("category = :category")
        params['category'] = data['category']
    if 'customer_name' in data:
        updates.append("customer_name = :customer_name")
        params['customer_name'] = data['customer_name']

    if not updates:
        return jsonify({'error': '没有要更新的内容'}), 400

    query = f"UPDATE file_templates SET {', '.join(updates)} WHERE id = :id"

    db = SessionLocal()
    try:
        db.execute(text(query), params)
        db.commit()
        return jsonify({'message': '更新成功'})
    finally:
        db.close()


@templates_bp.route('/<int:template_id>', methods=['DELETE'])
@require_auth
def delete_template(template_id):
    """删除模板（软删除）"""
    db = SessionLocal()
    try:
        db.execute(
            text("UPDATE file_templates SET is_active = 0 WHERE id = :id"),
            {'id': template_id}
        )
        db.commit()
        return jsonify({'message': '模板已删除'})
    finally:
        db.close()


@templates_bp.route('/<int:template_id>/copy-to-project', methods=['POST'])
@require_auth
def copy_to_project(template_id):
    """复制模板到项目文件"""
    user = get_current_user()
    data = request.get_json()
    project_id = data.get('project_id')

    if not project_id:
        return jsonify({'error': '请指定项目ID'}), 400

    db = SessionLocal()
    try:
        # 获取模板
        result = db.execute(
            text("SELECT * FROM file_templates WHERE id = :id AND is_active = 1"),
            {'id': template_id}
        )
        template = result.fetchone()

        if not template:
            return jsonify({'error': '模板不存在'}), 404

        template_dict = dict(template._mapping)

        if not os.path.exists(template_dict['file_path']):
            return jsonify({'error': '模板文件不存在'}), 404

        # 复制文件到项目目录
        upload_folder = current_app.config.get('UPLOAD_FOLDER', '/www/jzc_systems/uploads')
        project_dir = os.path.join(upload_folder, 'projects', str(project_id))
        os.makedirs(project_dir, exist_ok=True)

        ext = template_dict['file_name'].rsplit('.', 1)[1].lower() if '.' in template_dict['file_name'] else ''
        new_filename = f"{uuid.uuid4().hex}.{ext}"
        new_path = os.path.join(project_dir, new_filename)

        shutil.copy2(template_dict['file_path'], new_path)

        # 插入到项目文件表
        db.execute(
            text("""
                INSERT INTO project_files
                (project_id, file_name, file_path, file_size, file_type, category, uploaded_by_id, remark)
                VALUES (:pid, :fname, :fpath, :fsize, :ftype, :cat, :uid, :remark)
            """),
            {
                'pid': project_id,
                'fname': template_dict['file_name'],
                'fpath': new_path,
                'fsize': template_dict['file_size'],
                'ftype': template_dict['file_type'],
                'cat': 'template',
                'uid': user['user_id'],
                'remark': f"从模板库导入: {template_dict['name']}"
            }
        )
        db.commit()

        return jsonify({
            'message': '模板已添加到项目文件',
            'file_name': template_dict['file_name']
        })
    finally:
        db.close()
