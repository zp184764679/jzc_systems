"""
File Hub API Routes - 文件中心API
提供跨系统文件的统一查询、上传、下载功能
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from models import SessionLocal
from models.file_index import FileIndex, FileStatus, FILE_CATEGORIES, SOURCE_SYSTEMS
from services.file_index_service import FileIndexService
from datetime import datetime
import sys
import os
import hashlib
import logging
import zipfile
import io
import tempfile

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token
from shared.auth.models import User, AuthSessionLocal, init_auth_db
from shared.file_storage_v2 import EnterpriseFileStorage

# Initialize auth database for user queries
init_auth_db()

logger = logging.getLogger(__name__)

file_hub_bp = Blueprint('file_hub', __name__, url_prefix='/api/file-hub')

# Initialize enterprise file storage
storage = EnterpriseFileStorage()

# 文件大小限制 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes


def get_current_user():
    """从请求头获取当前用户"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    parts = auth_header.split(' ')
    if len(parts) != 2:
        return None
    token = parts[1]
    payload = verify_token(token)
    return payload if payload else None


def calculate_md5(file_bytes):
    """计算文件MD5"""
    return hashlib.md5(file_bytes).hexdigest()


# ==================== 文件列表与搜索 ====================

@file_hub_bp.route('/files', methods=['GET'])
def get_files():
    """获取文件列表（支持多维筛选）"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)

        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        query = request.args.get('query', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # 构建筛选条件
        filters = {}

        source_system = request.args.get('source_system')
        if source_system:
            filters['source_system'] = source_system.split(',')

        file_category = request.args.get('file_category')
        if file_category:
            filters['file_category'] = file_category.split(',')

        if request.args.get('order_no'):
            filters['order_no'] = request.args.get('order_no')
        if request.args.get('project_id'):
            filters['project_id'] = request.args.get('project_id', type=int)
        if request.args.get('project_no'):
            filters['project_no'] = request.args.get('project_no')
        if request.args.get('supplier_id'):
            filters['supplier_id'] = request.args.get('supplier_id', type=int)
        if request.args.get('customer_id'):
            filters['customer_id'] = request.args.get('customer_id', type=int)
        if request.args.get('part_number'):
            filters['part_number'] = request.args.get('part_number')
        if request.args.get('po_number'):
            filters['po_number'] = request.args.get('po_number')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')

        # 执行搜索
        result = service.search(
            query=query,
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/search', methods=['GET'])
def search_files():
    """全局搜索文件"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)

        query = request.args.get('q', '')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        if not query:
            return jsonify({'success': False, 'error': '请输入搜索关键词'}), 400

        result = service.search(query=query, page=page, page_size=page_size)

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"搜索文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==================== 按维度查询 ====================

@file_hub_bp.route('/by-order/<order_no>', methods=['GET'])
def get_files_by_order(order_no):
    """按订单号获取文件"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)
        files = service.get_by_order(order_no)

        return jsonify({'success': True, 'data': files})

    except Exception as e:
        logger.error(f"按订单获取文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/by-project/<project_no>', methods=['GET'])
def get_files_by_project(project_no):
    """按项目号获取文件"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)
        files = service.get_by_project(project_no=project_no)

        return jsonify({'success': True, 'data': files})

    except Exception as e:
        logger.error(f"按项目获取文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/by-supplier/<int:supplier_id>', methods=['GET'])
def get_files_by_supplier(supplier_id):
    """按供应商获取文件"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)
        files = service.get_by_supplier(supplier_id)

        return jsonify({'success': True, 'data': files})

    except Exception as e:
        logger.error(f"按供应商获取文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/by-customer/<int:customer_id>', methods=['GET'])
def get_files_by_customer(customer_id):
    """按客户获取文件"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)
        files = service.get_by_customer(customer_id)

        return jsonify({'success': True, 'data': files})

    except Exception as e:
        logger.error(f"按客户获取文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==================== 文件详情与下载 ====================

@file_hub_bp.route('/files/<int:file_id>', methods=['GET'])
def get_file_detail(file_id):
    """获取文件详情"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)
        file_index = service.get_by_id(file_id)

        if not file_index:
            return jsonify({'success': False, 'error': '文件不存在'}), 404

        return jsonify({'success': True, 'data': file_index.to_dict()})

    except Exception as e:
        logger.error(f"获取文件详情失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/files/<int:file_id>/download', methods=['GET'])
def download_file(file_id):
    """下载文件"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)
        file_index = service.get_by_id(file_id)

        if not file_index:
            return jsonify({'success': False, 'error': '文件不存在'}), 404

        file_path = file_index.file_path

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在于磁盘'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_index.file_name
        )

    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/files/<int:file_id>/preview', methods=['GET'])
def preview_file(file_id):
    """预览文件"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)
        file_index = service.get_by_id(file_id)

        if not file_index:
            return jsonify({'success': False, 'error': '文件不存在'}), 404

        file_path = file_index.file_path

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在于磁盘'}), 404

        # 获取 MIME 类型
        mime_type = file_index.file_type or 'application/octet-stream'

        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=False,
            download_name=file_index.file_name
        )

    except Exception as e:
        logger.error(f"预览文件失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/batch-download', methods=['POST'])
def batch_download():
    """批量下载文件（打包为ZIP）"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    data = request.get_json()
    file_ids = data.get('file_ids', [])

    if not file_ids:
        return jsonify({'success': False, 'error': '请选择要下载的文件'}), 400

    db = SessionLocal()
    try:
        service = FileIndexService(db)

        # 创建临时ZIP文件
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_id in file_ids:
                file_index = service.get_by_id(file_id)
                if file_index and os.path.exists(file_index.file_path):
                    # 使用文件名作为ZIP内的文件名
                    zip_file.write(file_index.file_path, file_index.file_name)

        zip_buffer.seek(0)

        # 生成下载文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'files_{timestamp}.zip'

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        logger.error(f"批量下载失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==================== 文件上传 ====================

@file_hub_bp.route('/upload', methods=['POST'])
def upload_file():
    """上传文件到文件中心"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '未找到文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '未选择文件'}), 400

    # 获取元数据
    file_category = request.form.get('file_category', 'other')
    order_no = request.form.get('order_no')
    project_id = request.form.get('project_id', type=int)
    project_no = request.form.get('project_no')
    supplier_id = request.form.get('supplier_id', type=int)
    supplier_name = request.form.get('supplier_name')
    customer_id = request.form.get('customer_id', type=int)
    customer_name = request.form.get('customer_name')
    part_number = request.form.get('part_number')
    po_number = request.form.get('po_number')

    db = SessionLocal()
    try:
        # 读取文件内容
        file_bytes = file.read()
        file_size = len(file_bytes)

        # 检查文件大小
        if file_size > MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': f'文件大小超过限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)'}), 400

        # 安全的文件名
        original_filename = file.filename
        safe_filename = secure_filename(original_filename)
        if not safe_filename:
            safe_filename = f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 计算MD5
        md5_hash = calculate_md5(file_bytes)

        # 获取文件类型
        file_type = file.content_type or 'application/octet-stream'
        file_extension = os.path.splitext(original_filename)[1].lower().lstrip('.')

        # 使用企业级存储保存文件
        file_stream = io.BytesIO(file_bytes)
        result = storage.store_file(
            file_stream=file_stream,
            filename=original_filename,
            system='portal',
            entity_type='file_hub',
            entity_id=0,  # 通用文件中心上传
            category=file_category,
            user_id=user.get('user_id'),
            metadata={
                'order_no': order_no,
                'project_no': project_no,
                'supplier_name': supplier_name,
                'customer_name': customer_name,
                'part_number': part_number,
                'po_number': po_number,
            }
        )

        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error', '文件存储失败')}), 500

        file_path = result.get('file_path')
        file_url = result.get('url')

        # 创建索引
        service = FileIndexService(db)
        file_index = service.index_file(
            source_system='portal',
            source_table='file_hub',
            source_id=result.get('file_id', 0),
            file_name=original_filename,
            file_path=file_path,
            file_category=file_category,
            file_url=file_url,
            file_size=file_size,
            file_type=file_type,
            file_extension=file_extension,
            md5_hash=md5_hash,
            order_no=order_no,
            project_id=project_id,
            project_no=project_no,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            customer_id=customer_id,
            customer_name=customer_name,
            part_number=part_number,
            po_number=po_number,
            uploaded_by=user.get('user_id'),
            uploaded_by_name=user.get('full_name') or user.get('username'),
        )

        return jsonify({
            'success': True,
            'data': file_index.to_dict(),
            'message': '文件上传成功'
        })

    except Exception as e:
        logger.error(f"上传文件失败: {str(e)}")
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==================== 索引管理（内部API，供其他系统调用） ====================

@file_hub_bp.route('/index', methods=['POST'])
def add_to_index():
    """添加文件到索引（供其他系统调用）"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    data = request.get_json()

    # 验证必填字段
    required_fields = ['source_system', 'source_table', 'source_id', 'file_name', 'file_path', 'file_category']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400

    db = SessionLocal()
    try:
        service = FileIndexService(db)
        file_index = service.index_file(
            source_system=data['source_system'],
            source_table=data['source_table'],
            source_id=data['source_id'],
            file_name=data['file_name'],
            file_path=data['file_path'],
            file_category=data['file_category'],
            file_url=data.get('file_url'),
            file_size=data.get('file_size', 0),
            file_type=data.get('file_type'),
            file_extension=data.get('file_extension'),
            md5_hash=data.get('md5_hash'),
            order_no=data.get('order_no'),
            project_id=data.get('project_id'),
            project_no=data.get('project_no'),
            part_number=data.get('part_number'),
            supplier_id=data.get('supplier_id'),
            supplier_name=data.get('supplier_name'),
            customer_id=data.get('customer_id'),
            customer_name=data.get('customer_name'),
            po_number=data.get('po_number'),
            uploaded_by=data.get('uploaded_by') or user.get('user_id'),
            uploaded_by_name=data.get('uploaded_by_name') or user.get('full_name') or user.get('username'),
        )

        return jsonify({
            'success': True,
            'data': file_index.to_dict(),
            'message': '文件已添加到索引'
        })

    except Exception as e:
        logger.error(f"添加索引失败: {str(e)}")
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/index/<int:file_id>', methods=['PUT'])
def update_index(file_id):
    """更新文件索引"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    data = request.get_json()

    db = SessionLocal()
    try:
        file_index = db.query(FileIndex).filter(FileIndex.id == file_id).first()
        if not file_index:
            return jsonify({'success': False, 'error': '文件不存在'}), 404

        service = FileIndexService(db)
        updated = service.update_index(
            file_index.source_system,
            file_index.source_table,
            file_index.source_id,
            **data
        )

        if updated:
            return jsonify({
                'success': True,
                'data': updated.to_dict(),
                'message': '索引已更新'
            })
        else:
            return jsonify({'success': False, 'error': '更新失败'}), 500

    except Exception as e:
        logger.error(f"更新索引失败: {str(e)}")
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/index/<int:file_id>', methods=['DELETE'])
def remove_from_index(file_id):
    """从索引中移除文件"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        file_index = db.query(FileIndex).filter(FileIndex.id == file_id).first()
        if not file_index:
            return jsonify({'success': False, 'error': '文件不存在'}), 404

        service = FileIndexService(db)
        success = service.remove_from_index(
            file_index.source_system,
            file_index.source_table,
            file_index.source_id
        )

        if success:
            return jsonify({'success': True, 'message': '文件已从索引中移除'})
        else:
            return jsonify({'success': False, 'error': '移除失败'}), 500

    except Exception as e:
        logger.error(f"移除索引失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==================== 统计与元数据 ====================

@file_hub_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取文件统计信息"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)

        # 构建筛选条件
        filters = {}
        if request.args.get('source_system'):
            filters['source_system'] = request.args.get('source_system')
        if request.args.get('project_id'):
            filters['project_id'] = request.args.get('project_id', type=int)
        if request.args.get('supplier_id'):
            filters['supplier_id'] = request.args.get('supplier_id', type=int)

        stats = service.get_statistics(filters)

        return jsonify({'success': True, 'data': stats})

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取文件分类列表"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)
        categories = service.get_categories()

        return jsonify({'success': True, 'data': categories})

    except Exception as e:
        logger.error(f"获取分类列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@file_hub_bp.route('/source-systems', methods=['GET'])
def get_source_systems():
    """获取来源系统列表"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': '未授权'}), 401

    db = SessionLocal()
    try:
        service = FileIndexService(db)
        systems = service.get_source_systems()

        return jsonify({'success': True, 'data': systems})

    except Exception as e:
        logger.error(f"获取来源系统列表失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()
