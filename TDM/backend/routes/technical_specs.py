"""
技术规格 API 路由
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from flask import Blueprint, request, jsonify
from models import db, ProductMaster, TechnicalSpec

technical_specs_bp = Blueprint('technical_specs', __name__)


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


@technical_specs_bp.route('/products/<int:product_id>/tech-specs', methods=['GET'])
def get_product_tech_specs(product_id):
    """获取产品的技术规格列表"""
    try:
        product = ProductMaster.query.get_or_404(product_id)

        # 是否只返回当前版本
        current_only = request.args.get('current_only', 'true').lower() == 'true'

        if current_only:
            specs = product.technical_specs.filter_by(is_current=True).all()
        else:
            specs = product.technical_specs.order_by(TechnicalSpec.version.desc()).all()

        return jsonify({
            'success': True,
            'data': [s.to_dict() for s in specs]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@technical_specs_bp.route('/tech-specs/<int:spec_id>', methods=['GET'])
def get_tech_spec(spec_id):
    """获取技术规格详情"""
    try:
        spec = TechnicalSpec.query.get_or_404(spec_id)
        return jsonify({
            'success': True,
            'data': spec.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@technical_specs_bp.route('/products/<int:product_id>/tech-specs', methods=['POST'])
def create_tech_spec(product_id):
    """创建技术规格"""
    try:
        product = ProductMaster.query.get_or_404(product_id)
        data = request.get_json()
        user = get_current_user()

        # 将现有的当前版本标记为非当前
        TechnicalSpec.query.filter_by(
            product_id=product_id,
            is_current=True
        ).update({'is_current': False})

        # 创建新技术规格
        spec = TechnicalSpec(
            product_id=product_id,
            part_number=product.part_number,
            # 材料信息
            material_code=data.get('material_code'),
            material_name=data.get('material_name'),
            material_spec=data.get('material_spec'),
            density=data.get('density'),
            hardness=data.get('hardness'),
            tensile_strength=data.get('tensile_strength'),
            # 尺寸信息
            outer_diameter=data.get('outer_diameter'),
            inner_diameter=data.get('inner_diameter'),
            length=data.get('length'),
            width=data.get('width'),
            height=data.get('height'),
            weight=data.get('weight'),
            volume=data.get('volume'),
            # 精度要求
            tolerance_class=data.get('tolerance_class'),
            surface_roughness=data.get('surface_roughness'),
            geometric_tolerance=data.get('geometric_tolerance'),
            position_tolerance=data.get('position_tolerance'),
            form_tolerance=data.get('form_tolerance'),
            # 热处理
            heat_treatment=data.get('heat_treatment'),
            hardness_spec=data.get('hardness_spec'),
            heat_treatment_temp=data.get('heat_treatment_temp'),
            # 表面处理
            surface_treatment=data.get('surface_treatment'),
            coating_spec=data.get('coating_spec'),
            coating_thickness=data.get('coating_thickness'),
            color=data.get('color'),
            # 特殊要求
            special_requirements=data.get('special_requirements'),
            quality_requirements=data.get('quality_requirements'),
            packaging_requirements=data.get('packaging_requirements'),
            # 版本信息
            version='1.0',
            is_current=True,
            version_note=data.get('version_note', '初始版本'),
            # 审计
            created_by=user['user_id'] if user else None,
            created_by_name=user['full_name'] if user else None
        )

        db.session.add(spec)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': spec.to_dict(),
            'message': '技术规格创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@technical_specs_bp.route('/tech-specs/<int:spec_id>', methods=['PUT'])
def update_tech_spec(spec_id):
    """更新技术规格（直接修改当前版本）"""
    try:
        spec = TechnicalSpec.query.get_or_404(spec_id)
        data = request.get_json()

        # 更新字段
        updatable_fields = [
            'material_code', 'material_name', 'material_spec', 'density',
            'hardness', 'tensile_strength', 'outer_diameter', 'inner_diameter',
            'length', 'width', 'height', 'weight', 'volume',
            'tolerance_class', 'surface_roughness', 'geometric_tolerance',
            'position_tolerance', 'form_tolerance', 'heat_treatment',
            'hardness_spec', 'heat_treatment_temp', 'surface_treatment',
            'coating_spec', 'coating_thickness', 'color',
            'special_requirements', 'quality_requirements', 'packaging_requirements'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(spec, field, data[field])

        db.session.commit()

        return jsonify({
            'success': True,
            'data': spec.to_dict(),
            'message': '技术规格更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@technical_specs_bp.route('/tech-specs/<int:spec_id>/new-version', methods=['POST'])
def create_new_version(spec_id):
    """创建新版本（保留历史）"""
    try:
        old_spec = TechnicalSpec.query.get_or_404(spec_id)
        data = request.get_json()
        user = get_current_user()

        # 计算新版本号
        new_version = increment_version(old_spec.version)

        # 将旧版本标记为非当前
        old_spec.is_current = False

        # 创建新版本
        new_spec = TechnicalSpec(
            product_id=old_spec.product_id,
            part_number=old_spec.part_number,
            # 复制所有字段
            material_code=data.get('material_code', old_spec.material_code),
            material_name=data.get('material_name', old_spec.material_name),
            material_spec=data.get('material_spec', old_spec.material_spec),
            density=data.get('density', old_spec.density),
            hardness=data.get('hardness', old_spec.hardness),
            tensile_strength=data.get('tensile_strength', old_spec.tensile_strength),
            outer_diameter=data.get('outer_diameter', old_spec.outer_diameter),
            inner_diameter=data.get('inner_diameter', old_spec.inner_diameter),
            length=data.get('length', old_spec.length),
            width=data.get('width', old_spec.width),
            height=data.get('height', old_spec.height),
            weight=data.get('weight', old_spec.weight),
            volume=data.get('volume', old_spec.volume),
            tolerance_class=data.get('tolerance_class', old_spec.tolerance_class),
            surface_roughness=data.get('surface_roughness', old_spec.surface_roughness),
            geometric_tolerance=data.get('geometric_tolerance', old_spec.geometric_tolerance),
            position_tolerance=data.get('position_tolerance', old_spec.position_tolerance),
            form_tolerance=data.get('form_tolerance', old_spec.form_tolerance),
            heat_treatment=data.get('heat_treatment', old_spec.heat_treatment),
            hardness_spec=data.get('hardness_spec', old_spec.hardness_spec),
            heat_treatment_temp=data.get('heat_treatment_temp', old_spec.heat_treatment_temp),
            surface_treatment=data.get('surface_treatment', old_spec.surface_treatment),
            coating_spec=data.get('coating_spec', old_spec.coating_spec),
            coating_thickness=data.get('coating_thickness', old_spec.coating_thickness),
            color=data.get('color', old_spec.color),
            special_requirements=data.get('special_requirements', old_spec.special_requirements),
            quality_requirements=data.get('quality_requirements', old_spec.quality_requirements),
            packaging_requirements=data.get('packaging_requirements', old_spec.packaging_requirements),
            # 新版本信息
            version=new_version,
            is_current=True,
            parent_version_id=old_spec.id,
            version_note=data.get('version_note', ''),
            created_by=user['user_id'] if user else None,
            created_by_name=user['full_name'] if user else None
        )

        db.session.add(new_spec)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': new_spec.to_dict(),
            'message': f'新版本 v{new_version} 创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@technical_specs_bp.route('/tech-specs/<int:spec_id>/versions', methods=['GET'])
def get_spec_versions(spec_id):
    """获取版本历史"""
    try:
        spec = TechnicalSpec.query.get_or_404(spec_id)

        # 查找同一产品的所有版本
        versions = TechnicalSpec.query.filter_by(
            product_id=spec.product_id
        ).order_by(TechnicalSpec.version.desc()).all()

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
