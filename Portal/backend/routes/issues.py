"""
Issues API Routes - 问题/改善跟踪API
"""
from flask import Blueprint, request, jsonify
from models import SessionLocal
from models.issue import Issue, IssueType, IssueSeverity, IssueStatus
from models.project_notification import ProjectNotification, NotificationType
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

issues_bp = Blueprint('issues', __name__, url_prefix='/api/issues')


def get_current_user():
    """获取当前用户"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    parts = auth_header.split(' ')
    if len(parts) != 2:
        return None
    token = parts[1]
    payload = verify_token(token)
    return payload if payload else None


@issues_bp.route('/project/<int:project_id>', methods=['GET'])
def get_project_issues(project_id):
    """获取项目问题列表"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        query = session.query(Issue).filter_by(project_id=project_id)

        # 筛选条件
        status = request.args.get('status')
        severity = request.args.get('severity')
        issue_type = request.args.get('issue_type')

        if status:
            query = query.filter_by(status=status)
        if severity:
            query = query.filter_by(severity=severity)
        if issue_type:
            query = query.filter_by(issue_type=issue_type)

        issues = query.order_by(Issue.created_at.desc()).all()

        return jsonify({
            'issues': [i.to_dict() for i in issues],
            'total': len(issues)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@issues_bp.route('', methods=['POST'])
def create_issue():
    """创建问题"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少请求数据'}), 400

    required_fields = ['project_id', 'title']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400

    session = SessionLocal()
    try:
        # 生成问题编号
        issue_no = Issue.generate_issue_no(session)

        issue = Issue(
            project_id=data['project_id'],
            issue_no=issue_no,
            title=data['title'],
            description=data.get('description'),
            issue_type=data.get('issue_type', 'other'),
            severity=data.get('severity', 'medium'),
            status='open',
            affected_phase_id=data.get('affected_phase_id'),
            affected_task_id=data.get('affected_task_id'),
            reported_by_id=user.get('user_id') or user.get('id'),
            reported_by_name=user.get('full_name') or user.get('username'),
            assigned_to_id=data.get('assigned_to_id'),
            assigned_to_name=data.get('assigned_to_name'),
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
        )

        session.add(issue)
        session.commit()
        session.refresh(issue)

        # 如果有负责人，发送通知
        if issue.assigned_to_id:
            notification = ProjectNotification(
                recipient_id=issue.assigned_to_id,
                recipient_name=issue.assigned_to_name,
                project_id=issue.project_id,
                issue_id=issue.id,
                notification_type=NotificationType.ISSUE_CREATED,
                title=f"新问题分配给你：{issue.title}",
                content=issue.description,
                related_data={'issue_no': issue.issue_no, 'severity': issue.severity.value},
                channels=['in_app']
            )
            session.add(notification)
            session.commit()

        return jsonify(issue.to_dict()), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@issues_bp.route('/<int:issue_id>', methods=['GET'])
def get_issue(issue_id):
    """获取问题详情"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        issue = session.query(Issue).filter_by(id=issue_id).first()
        if not issue:
            return jsonify({'error': '问题不存在'}), 404

        return jsonify(issue.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@issues_bp.route('/<int:issue_id>', methods=['PUT'])
def update_issue(issue_id):
    """更新问题"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少请求数据'}), 400

    session = SessionLocal()
    try:
        issue = session.query(Issue).filter_by(id=issue_id).first()
        if not issue:
            return jsonify({'error': '问题不存在'}), 404

        # 更新字段
        updatable_fields = [
            'title', 'description', 'issue_type', 'severity', 'status',
            'affected_phase_id', 'affected_task_id', 'assigned_to_id',
            'assigned_to_name', 'root_cause', 'corrective_action',
            'preventive_action', 'resolution_notes', 'due_date'
        ]

        for field in updatable_fields:
            if field in data:
                if field == 'due_date' and data[field]:
                    setattr(issue, field, datetime.fromisoformat(data[field]))
                else:
                    setattr(issue, field, data[field])

        session.commit()
        session.refresh(issue)

        return jsonify(issue.to_dict()), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@issues_bp.route('/<int:issue_id>/resolve', methods=['POST'])
def resolve_issue(issue_id):
    """解决问题"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json() or {}

    session = SessionLocal()
    try:
        issue = session.query(Issue).filter_by(id=issue_id).first()
        if not issue:
            return jsonify({'error': '问题不存在'}), 404

        issue.status = IssueStatus.RESOLVED
        issue.resolved_at = datetime.now()
        issue.resolution_notes = data.get('resolution_notes', issue.resolution_notes)
        issue.corrective_action = data.get('corrective_action', issue.corrective_action)
        issue.preventive_action = data.get('preventive_action', issue.preventive_action)

        session.commit()
        session.refresh(issue)

        # 通知报告人
        if issue.reported_by_id:
            notification = ProjectNotification(
                recipient_id=issue.reported_by_id,
                recipient_name=issue.reported_by_name,
                project_id=issue.project_id,
                issue_id=issue.id,
                notification_type=NotificationType.ISSUE_RESOLVED,
                title=f"问题已解决：{issue.title}",
                content=issue.resolution_notes,
                related_data={'issue_no': issue.issue_no},
                channels=['in_app']
            )
            session.add(notification)
            session.commit()

        return jsonify(issue.to_dict()), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@issues_bp.route('/<int:issue_id>/close', methods=['POST'])
def close_issue(issue_id):
    """关闭问题"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        issue = session.query(Issue).filter_by(id=issue_id).first()
        if not issue:
            return jsonify({'error': '问题不存在'}), 404

        issue.status = IssueStatus.CLOSED
        issue.closed_at = datetime.now()

        session.commit()
        session.refresh(issue)

        return jsonify(issue.to_dict()), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@issues_bp.route('/<int:issue_id>/reopen', methods=['POST'])
def reopen_issue(issue_id):
    """重新打开问题"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json() or {}

    session = SessionLocal()
    try:
        issue = session.query(Issue).filter_by(id=issue_id).first()
        if not issue:
            return jsonify({'error': '问题不存在'}), 404

        issue.status = IssueStatus.REOPENED
        issue.resolved_at = None
        issue.closed_at = None

        if data.get('reason'):
            issue.resolution_notes = f"[重新打开原因]: {data['reason']}\n\n{issue.resolution_notes or ''}"

        session.commit()
        session.refresh(issue)

        return jsonify(issue.to_dict()), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@issues_bp.route('/<int:issue_id>', methods=['DELETE'])
def delete_issue(issue_id):
    """删除问题"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        issue = session.query(Issue).filter_by(id=issue_id).first()
        if not issue:
            return jsonify({'error': '问题不存在'}), 404

        session.delete(issue)
        session.commit()

        return jsonify({'message': '问题已删除'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
