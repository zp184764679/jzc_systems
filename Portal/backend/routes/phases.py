"""
Phases API Routes - 项目阶段管理API
"""
from flask import Blueprint, request, jsonify
from models import SessionLocal
from models.project import Project
from models.project_phase import ProjectPhase, PhaseType, PhaseStatus
from datetime import datetime
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

phases_bp = Blueprint('phases', __name__)


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


@phases_bp.route('/api/projects/<int:project_id>/phases', methods=['GET'])
def get_project_phases(project_id):
    """获取项目的所有阶段"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # 检查项目是否存在
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 获取项目阶段，按顺序排序
        phases = session.query(ProjectPhase).filter_by(
            project_id=project_id
        ).order_by(ProjectPhase.phase_order).all()

        return jsonify({
            'phases': [p.to_dict() for p in phases],
            'total': len(phases)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@phases_bp.route('/api/projects/<int:project_id>/phases', methods=['POST'])
def create_phase(project_id):
    """创建项目阶段"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少数据'}), 400

    session = SessionLocal()
    try:
        # 检查项目是否存在
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 获取当前最大阶段顺序
        max_order = session.query(ProjectPhase).filter_by(
            project_id=project_id
        ).count()

        # 解析阶段类型
        phase_type = data.get('phase_type', 'customer_order')
        if phase_type in PhaseType.__members__:
            phase_type = PhaseType[phase_type]
        else:
            # 尝试从值匹配
            for pt in PhaseType:
                if pt.value == phase_type:
                    phase_type = pt
                    break

        phase = ProjectPhase(
            project_id=project_id,
            phase_type=phase_type,
            phase_order=data.get('phase_order', max_order + 1),
            name=data.get('name', '新阶段'),
            description=data.get('description'),
            planned_start_date=datetime.strptime(data['planned_start_date'], '%Y-%m-%d').date() if data.get('planned_start_date') else None,
            planned_end_date=datetime.strptime(data['planned_end_date'], '%Y-%m-%d').date() if data.get('planned_end_date') else None,
            responsible_user_id=data.get('responsible_user_id'),
            department=data.get('department'),
        )

        session.add(phase)
        session.commit()
        session.refresh(phase)

        return jsonify(phase.to_dict()), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@phases_bp.route('/api/projects/<int:project_id>/phases/init', methods=['POST'])
def init_default_phases(project_id):
    """为项目初始化默认的7个阶段"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # 检查项目是否存在
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 检查是否已有阶段
        existing_count = session.query(ProjectPhase).filter_by(project_id=project_id).count()
        if existing_count > 0:
            return jsonify({'error': '项目已有阶段，无法初始化'}), 400

        # 创建默认阶段
        default_phases = ProjectPhase.get_default_phases()
        phases = []
        for phase_config in default_phases:
            phase = ProjectPhase(
                project_id=project_id,
                phase_type=phase_config['phase_type'],
                phase_order=phase_config['phase_order'],
                name=phase_config['name'],
                description=phase_config['description'],
            )
            session.add(phase)
            phases.append(phase)

        session.commit()

        # Refresh all phases
        for phase in phases:
            session.refresh(phase)

        return jsonify({
            'message': '阶段初始化成功',
            'phases': [p.to_dict() for p in phases]
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@phases_bp.route('/api/phases/<int:phase_id>', methods=['GET'])
def get_phase(phase_id):
    """获取单个阶段详情"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        phase = session.query(ProjectPhase).filter_by(id=phase_id).first()
        if not phase:
            return jsonify({'error': '阶段不存在'}), 404

        return jsonify(phase.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@phases_bp.route('/api/phases/<int:phase_id>', methods=['PUT'])
def update_phase(phase_id):
    """更新阶段"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    session = SessionLocal()
    try:
        phase = session.query(ProjectPhase).filter_by(id=phase_id).first()
        if not phase:
            return jsonify({'error': '阶段不存在'}), 404

        # 更新字段
        if 'name' in data:
            phase.name = data['name']
        if 'description' in data:
            phase.description = data['description']
        if 'planned_start_date' in data:
            phase.planned_start_date = datetime.strptime(data['planned_start_date'], '%Y-%m-%d').date() if data['planned_start_date'] else None
        if 'planned_end_date' in data:
            phase.planned_end_date = datetime.strptime(data['planned_end_date'], '%Y-%m-%d').date() if data['planned_end_date'] else None
        if 'actual_start_date' in data:
            phase.actual_start_date = datetime.strptime(data['actual_start_date'], '%Y-%m-%d').date() if data['actual_start_date'] else None
        if 'actual_end_date' in data:
            phase.actual_end_date = datetime.strptime(data['actual_end_date'], '%Y-%m-%d').date() if data['actual_end_date'] else None
        if 'status' in data:
            status_value = data['status']
            for ps in PhaseStatus:
                if ps.value == status_value:
                    phase.status = ps
                    break
        if 'completion_percentage' in data:
            phase.completion_percentage = max(0, min(100, int(data['completion_percentage'])))
        if 'responsible_user_id' in data:
            phase.responsible_user_id = data['responsible_user_id']
        if 'department' in data:
            phase.department = data['department']

        session.commit()
        session.refresh(phase)

        return jsonify(phase.to_dict()), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@phases_bp.route('/api/phases/<int:phase_id>/complete', methods=['POST'])
def complete_phase(phase_id):
    """完成阶段"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        phase = session.query(ProjectPhase).filter_by(id=phase_id).first()
        if not phase:
            return jsonify({'error': '阶段不存在'}), 404

        phase.status = PhaseStatus.COMPLETED
        phase.completion_percentage = 100
        phase.actual_end_date = datetime.now().date()

        session.commit()
        session.refresh(phase)

        return jsonify({
            'message': '阶段已完成',
            'phase': phase.to_dict()
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@phases_bp.route('/api/phases/<int:phase_id>/start', methods=['POST'])
def start_phase(phase_id):
    """开始阶段"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        phase = session.query(ProjectPhase).filter_by(id=phase_id).first()
        if not phase:
            return jsonify({'error': '阶段不存在'}), 404

        phase.status = PhaseStatus.IN_PROGRESS
        phase.actual_start_date = datetime.now().date()

        session.commit()
        session.refresh(phase)

        return jsonify({
            'message': '阶段已开始',
            'phase': phase.to_dict()
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@phases_bp.route('/api/phases/<int:phase_id>', methods=['DELETE'])
def delete_phase(phase_id):
    """删除阶段"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        phase = session.query(ProjectPhase).filter_by(id=phase_id).first()
        if not phase:
            return jsonify({'error': '阶段不存在'}), 404

        session.delete(phase)
        session.commit()

        return jsonify({'message': '阶段已删除'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
