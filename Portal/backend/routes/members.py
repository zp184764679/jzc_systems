"""
Members API Routes - 项目成员管理API
"""
from flask import Blueprint, request, jsonify
from models import SessionLocal
from models.project import Project
from models.project_member import ProjectMember, MemberRole
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

members_bp = Blueprint('members', __name__, url_prefix='/api/members')


def get_current_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    parts = auth_header.split(' ')
    if len(parts) != 2:
        return None
    token = parts[1]
    payload = verify_token(token)
    return payload if payload else None


@members_bp.route('/project/<int:project_id>', methods=['GET'])
def get_project_members(project_id):
    """获取项目成员列表"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        members = session.query(ProjectMember).filter_by(project_id=project_id).all()
        return jsonify({
            'members': [m.to_dict() for m in members],
            'total': len(members)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@members_bp.route('/project/<int:project_id>', methods=['POST'])
def add_member(project_id):
    """添加项目成员"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'error': '缺少用户ID'}), 400

    session = SessionLocal()
    try:
        # Check if member already exists
        existing = session.query(ProjectMember).filter_by(
            project_id=project_id,
            user_id=data['user_id']
        ).first()

        if existing:
            return jsonify({'error': '用户已是项目成员'}), 400

        member = ProjectMember(
            project_id=project_id,
            user_id=data['user_id'],
            department=data.get('department'),
            role=data.get('role', 'member'),
            permissions=ProjectMember.get_default_permissions(
                MemberRole(data.get('role', 'member'))
            )
        )

        session.add(member)
        session.commit()
        session.refresh(member)

        return jsonify(member.to_dict()), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@members_bp.route('/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    """更新成员角色/权限"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    session = SessionLocal()
    try:
        member = session.query(ProjectMember).filter_by(id=member_id).first()
        if not member:
            return jsonify({'error': '成员不存在'}), 404

        if 'role' in data:
            member.role = data['role']
            member.permissions = ProjectMember.get_default_permissions(MemberRole(data['role']))

        session.commit()
        session.refresh(member)

        return jsonify(member.to_dict()), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@members_bp.route('/<int:member_id>', methods=['DELETE'])
def remove_member(member_id):
    """移除成员"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        member = session.query(ProjectMember).filter_by(id=member_id).first()
        if not member:
            return jsonify({'error': '成员不存在'}), 404

        session.delete(member)
        session.commit()

        return jsonify({'message': '成员已移除'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
