"""
工艺文件 API 路由
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from flask import Blueprint, request, jsonify
from models import db, ProductMaster, ProcessDocument

process_docs_bp = Blueprint('process_docs', __name__)


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


def increment_version(current_version):
    """增加版本号"""
    try:
        parts = current_version.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return f"{major}.{minor + 1}"
    except:
        return "1.1"


@process_docs_bp.route('/products/<int:product_id>/processes', methods=['GET'])
def get_product_processes(product_id):
    """获取产品的工艺文件列表"""
    try:
        product = ProductMaster.query.get_or_404(product_id)

        current_only = request.args.get('current_only', 'true').lower() == 'true'

        query = product.process_documents

        if current_only:
            query = query.filter_by(is_current=True)

        processes = query.order_by(ProcessDocument.process_sequence).all()

        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in processes]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@process_docs_bp.route('/processes/<int:process_id>', methods=['GET'])
def get_process(process_id):
    """获取工艺文件详情"""
    try:
        process = ProcessDocument.query.get_or_404(process_id)
        return jsonify({
            'success': True,
            'data': process.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@process_docs_bp.route('/products/<int:product_id>/processes', methods=['POST'])
def create_process(product_id):
    """创建工艺文件"""
    try:
        product = ProductMaster.query.get_or_404(product_id)
        data = request.get_json()
        user = get_current_user()

        # 获取下一个工序顺序号
        max_seq = db.session.query(db.func.max(ProcessDocument.process_sequence)).filter_by(
            product_id=product_id,
            is_current=True
        ).scalar() or 0

        process = ProcessDocument(
            product_id=product_id,
            part_number=product.part_number,
            process_code=data.get('process_code'),
            process_name=data.get('process_name'),
            process_category=data.get('process_category'),
            process_sequence=data.get('process_sequence', max_seq + 10),
            quotation_process_id=data.get('quotation_process_id'),
            setup_time=data.get('setup_time'),
            cycle_time=data.get('cycle_time'),
            daily_output=data.get('daily_output'),
            defect_rate=data.get('defect_rate'),
            machine_type=data.get('machine_type'),
            machine_model=data.get('machine_model'),
            machine_specs=data.get('machine_specs'),
            parameters=data.get('parameters', {}),
            work_instruction=data.get('work_instruction'),
            safety_notes=data.get('safety_notes'),
            quality_points=data.get('quality_points'),
            file_index_ids=data.get('file_index_ids', []),
            version='1.0',
            is_current=True,
            version_note=data.get('version_note', '初始版本'),
            created_by=user['user_id'] if user else None,
            created_by_name=user['full_name'] if user else None
        )

        db.session.add(process)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': process.to_dict(),
            'message': '工艺文件创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@process_docs_bp.route('/processes/<int:process_id>', methods=['PUT'])
def update_process(process_id):
    """更新工艺文件"""
    try:
        process = ProcessDocument.query.get_or_404(process_id)
        data = request.get_json()

        # 更新字段
        updatable_fields = [
            'process_code', 'process_name', 'process_category', 'process_sequence',
            'setup_time', 'cycle_time', 'daily_output', 'defect_rate',
            'machine_type', 'machine_model', 'machine_specs', 'parameters',
            'work_instruction', 'safety_notes', 'quality_points', 'file_index_ids'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(process, field, data[field])

        db.session.commit()

        return jsonify({
            'success': True,
            'data': process.to_dict(),
            'message': '工艺文件更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@process_docs_bp.route('/processes/<int:process_id>/new-version', methods=['POST'])
def create_process_new_version(process_id):
    """创建工艺文件新版本"""
    try:
        old_process = ProcessDocument.query.get_or_404(process_id)
        data = request.get_json()
        user = get_current_user()

        new_version = increment_version(old_process.version)

        # 将旧版本标记为非当前
        old_process.is_current = False

        # 创建新版本
        new_process = ProcessDocument(
            product_id=old_process.product_id,
            part_number=old_process.part_number,
            process_code=old_process.process_code,
            process_name=data.get('process_name', old_process.process_name),
            process_category=data.get('process_category', old_process.process_category),
            process_sequence=data.get('process_sequence', old_process.process_sequence),
            quotation_process_id=old_process.quotation_process_id,
            setup_time=data.get('setup_time', old_process.setup_time),
            cycle_time=data.get('cycle_time', old_process.cycle_time),
            daily_output=data.get('daily_output', old_process.daily_output),
            defect_rate=data.get('defect_rate', old_process.defect_rate),
            machine_type=data.get('machine_type', old_process.machine_type),
            machine_model=data.get('machine_model', old_process.machine_model),
            machine_specs=data.get('machine_specs', old_process.machine_specs),
            parameters=data.get('parameters', old_process.parameters),
            work_instruction=data.get('work_instruction', old_process.work_instruction),
            safety_notes=data.get('safety_notes', old_process.safety_notes),
            quality_points=data.get('quality_points', old_process.quality_points),
            file_index_ids=data.get('file_index_ids', old_process.file_index_ids),
            version=new_version,
            is_current=True,
            parent_version_id=old_process.id,
            version_note=data.get('version_note', ''),
            created_by=user['user_id'] if user else None,
            created_by_name=user['full_name'] if user else None
        )

        db.session.add(new_process)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': new_process.to_dict(),
            'message': f'新版本 v{new_version} 创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@process_docs_bp.route('/processes/<int:process_id>/versions', methods=['GET'])
def get_process_versions(process_id):
    """获取工艺文件版本历史"""
    try:
        process = ProcessDocument.query.get_or_404(process_id)

        # 查找同一工艺代码的所有版本
        versions = ProcessDocument.query.filter_by(
            product_id=process.product_id,
            process_code=process.process_code
        ).order_by(ProcessDocument.version.desc()).all()

        return jsonify({
            'success': True,
            'data': [{
                'id': v.id,
                'version': v.version,
                'is_current': v.is_current,
                'version_note': v.version_note,
                'created_by_name': v.created_by_name,
                'created_at': v.created_at.isoformat() if v.created_at else None
            } for v in versions]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@process_docs_bp.route('/products/<int:product_id>/processes/reorder', methods=['POST'])
def reorder_processes(product_id):
    """重新排序工艺文件"""
    try:
        data = request.get_json()
        process_ids = data.get('process_ids', [])

        for i, process_id in enumerate(process_ids):
            process = ProcessDocument.query.get(process_id)
            if process and process.product_id == product_id:
                process.process_sequence = (i + 1) * 10

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '工序顺序已更新'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@process_docs_bp.route('/processes/<int:process_id>', methods=['DELETE'])
def delete_process(process_id):
    """删除工艺文件"""
    try:
        process = ProcessDocument.query.get_or_404(process_id)
        db.session.delete(process)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '工艺文件已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
