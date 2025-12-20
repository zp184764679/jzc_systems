"""
检验标准 API 路由
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, ProductMaster, InspectionCriteria

inspection_bp = Blueprint('inspection', __name__)


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


@inspection_bp.route('/products/<int:product_id>/inspection', methods=['GET'])
def get_product_inspections(product_id):
    """获取产品的检验标准列表"""
    try:
        product = ProductMaster.query.get_or_404(product_id)

        # 筛选参数
        stage = request.args.get('stage', '').strip()
        current_only = request.args.get('current_only', 'true').lower() == 'true'

        query = product.inspection_criteria

        if current_only:
            query = query.filter_by(is_current=True)

        if stage:
            query = query.filter_by(inspection_stage=stage)

        inspections = query.order_by(InspectionCriteria.inspection_stage).all()

        return jsonify({
            'success': True,
            'data': [i.to_dict() for i in inspections]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@inspection_bp.route('/inspection/<int:inspection_id>', methods=['GET'])
def get_inspection(inspection_id):
    """获取检验标准详情"""
    try:
        inspection = InspectionCriteria.query.get_or_404(inspection_id)
        return jsonify({
            'success': True,
            'data': inspection.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@inspection_bp.route('/products/<int:product_id>/inspection', methods=['POST'])
def create_inspection(product_id):
    """创建检验标准"""
    try:
        product = ProductMaster.query.get_or_404(product_id)
        data = request.get_json()
        user = get_current_user()

        # 验证必填字段
        if not data.get('criteria_code'):
            return jsonify({'success': False, 'error': '标准编码不能为空'}), 400
        if not data.get('criteria_name'):
            return jsonify({'success': False, 'error': '标准名称不能为空'}), 400

        # 创建检验标准
        inspection = InspectionCriteria(
            product_id=product_id,
            part_number=product.part_number,
            criteria_code=data['criteria_code'],
            criteria_name=data['criteria_name'],
            inspection_stage=data.get('inspection_stage'),
            inspection_method=data.get('inspection_method', 'sampling'),
            sampling_plan=data.get('sampling_plan'),
            sample_size_formula=data.get('sample_size_formula'),
            inspection_items=data.get('inspection_items', []),
            aql_critical=data.get('aql_critical'),
            aql_major=data.get('aql_major'),
            aql_minor=data.get('aql_minor'),
            effective_date=datetime.strptime(data['effective_date'], '%Y-%m-%d').date() if data.get('effective_date') else None,
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
            status=data.get('status', 'draft'),
            version='1.0',
            is_current=True,
            version_note=data.get('version_note', '初始版本'),
            created_by=user['user_id'] if user else None,
            created_by_name=user['full_name'] if user else None
        )

        db.session.add(inspection)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': inspection.to_dict(),
            'message': '检验标准创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@inspection_bp.route('/inspection/<int:inspection_id>', methods=['PUT'])
def update_inspection(inspection_id):
    """更新检验标准"""
    try:
        inspection = InspectionCriteria.query.get_or_404(inspection_id)
        data = request.get_json()

        # 更新字段
        updatable_fields = [
            'criteria_name', 'inspection_stage', 'inspection_method',
            'sampling_plan', 'sample_size_formula', 'inspection_items',
            'aql_critical', 'aql_major', 'aql_minor', 'status'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(inspection, field, data[field])

        # 处理日期字段
        if 'effective_date' in data:
            inspection.effective_date = datetime.strptime(data['effective_date'], '%Y-%m-%d').date() if data['effective_date'] else None
        if 'expiry_date' in data:
            inspection.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data['expiry_date'] else None

        db.session.commit()

        return jsonify({
            'success': True,
            'data': inspection.to_dict(),
            'message': '检验标准更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@inspection_bp.route('/inspection/<int:inspection_id>/new-version', methods=['POST'])
def create_inspection_new_version(inspection_id):
    """创建检验标准新版本"""
    try:
        old_inspection = InspectionCriteria.query.get_or_404(inspection_id)
        data = request.get_json()
        user = get_current_user()

        new_version = increment_version(old_inspection.version)

        # 将旧版本标记为非当前
        old_inspection.is_current = False

        # 创建新版本
        new_inspection = InspectionCriteria(
            product_id=old_inspection.product_id,
            part_number=old_inspection.part_number,
            criteria_code=old_inspection.criteria_code,
            criteria_name=data.get('criteria_name', old_inspection.criteria_name),
            inspection_stage=data.get('inspection_stage', old_inspection.inspection_stage),
            inspection_method=data.get('inspection_method', old_inspection.inspection_method),
            sampling_plan=data.get('sampling_plan', old_inspection.sampling_plan),
            sample_size_formula=data.get('sample_size_formula', old_inspection.sample_size_formula),
            inspection_items=data.get('inspection_items', old_inspection.inspection_items),
            aql_critical=data.get('aql_critical', old_inspection.aql_critical),
            aql_major=data.get('aql_major', old_inspection.aql_major),
            aql_minor=data.get('aql_minor', old_inspection.aql_minor),
            effective_date=datetime.strptime(data['effective_date'], '%Y-%m-%d').date() if data.get('effective_date') else old_inspection.effective_date,
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else old_inspection.expiry_date,
            status='draft',  # 新版本默认为草稿
            version=new_version,
            is_current=True,
            parent_version_id=old_inspection.id,
            version_note=data.get('version_note', ''),
            created_by=user['user_id'] if user else None,
            created_by_name=user['full_name'] if user else None
        )

        db.session.add(new_inspection)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': new_inspection.to_dict(),
            'message': f'新版本 v{new_version} 创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@inspection_bp.route('/inspection/<int:inspection_id>/approve', methods=['POST'])
def approve_inspection(inspection_id):
    """审批检验标准"""
    try:
        inspection = InspectionCriteria.query.get_or_404(inspection_id)
        user = get_current_user()

        if inspection.status != 'draft':
            return jsonify({'success': False, 'error': '只有草稿状态的标准可以审批'}), 400

        inspection.status = 'active'
        inspection.approved_by = user['user_id'] if user else None
        inspection.approved_by_name = user['full_name'] if user else None
        inspection.approved_at = datetime.now()

        db.session.commit()

        return jsonify({
            'success': True,
            'data': inspection.to_dict(),
            'message': '检验标准已审批生效'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@inspection_bp.route('/inspection/<int:inspection_id>/versions', methods=['GET'])
def get_inspection_versions(inspection_id):
    """获取检验标准版本历史"""
    try:
        inspection = InspectionCriteria.query.get_or_404(inspection_id)

        # 查找同一标准编码的所有版本
        versions = InspectionCriteria.query.filter_by(
            product_id=inspection.product_id,
            criteria_code=inspection.criteria_code
        ).order_by(InspectionCriteria.version.desc()).all()

        return jsonify({
            'success': True,
            'data': [{
                'id': v.id,
                'version': v.version,
                'is_current': v.is_current,
                'status': v.status,
                'version_note': v.version_note,
                'approved_by_name': v.approved_by_name,
                'approved_at': v.approved_at.isoformat() if v.approved_at else None,
                'created_by_name': v.created_by_name,
                'created_at': v.created_at.isoformat() if v.created_at else None
            } for v in versions]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@inspection_bp.route('/inspection/stages', methods=['GET'])
def get_inspection_stages():
    """获取检验阶段列表"""
    return jsonify({
        'success': True,
        'data': [
            {'value': 'incoming', 'label': '来料检验 (IQC)', 'label_en': 'Incoming Quality Control'},
            {'value': 'process', 'label': '过程检验 (IPQC)', 'label_en': 'In-Process Quality Control'},
            {'value': 'final', 'label': '最终检验 (FQC)', 'label_en': 'Final Quality Control'},
            {'value': 'outgoing', 'label': '出货检验 (OQC)', 'label_en': 'Outgoing Quality Control'},
        ]
    })
