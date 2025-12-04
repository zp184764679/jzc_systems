"""
User registration request routes for HR system
Allows active employees to submit registration requests for approval
"""
from flask import Blueprint, request, jsonify
import sys
import os
from datetime import datetime
import json

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '../..', '..'))

from shared.auth import (
    User,
    RegistrationRequest,
    init_auth_db,
    hash_password
)

# Initialize auth database first
init_auth_db()

# Import AuthSessionLocal after initialization
import shared.auth.models as auth_models

# Import HR models
from app import db
from app.models.employee import Employee
from app.models.base_data import Factory

register_bp = Blueprint('register', __name__, url_prefix='/api/register')


@register_bp.route('/submit', methods=['POST'])
def submit_registration():
    """Submit registration request - requires emp_no, full_name, username, password, email"""
    data = request.get_json()

    # 验证必填字段
    required_fields = ['emp_no', 'full_name', 'username', 'password', 'email']
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return jsonify({'error': f'请提供: {", ".join(missing_fields)}'}), 400

    emp_no = data['emp_no'].strip()
    full_name = data['full_name'].strip()
    username = data['username'].strip()
    password = data['password']
    email = data['email'].strip()

    # 验证邮箱格式
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({'error': '邮箱格式不正确'}), 400

    # 验证用户名格式(字母数字下划线,3-20字符)
    username_pattern = r'^[a-zA-Z0-9_]{3,20}$'
    if not re.match(username_pattern, username):
        return jsonify({'error': '用户名只能包含字母、数字和下划线，长度3-20字符'}), 400

    # 验证密码强度(至少6字符)
    if len(password) < 6:
        return jsonify({'error': '密码长度至少6个字符'}), 400

    # 验证工号和姓名是否匹配HR系统数据库
    employee = Employee.query.filter_by(empNo=emp_no).first()

    if not employee:
        return jsonify({'error': '工号不存在，请联系HR确认您的工号'}), 404

    if employee.name != full_name:
        return jsonify({'error': '工号与姓名不匹配，请确认信息是否正确'}), 403

    if employee.employment_status != 'Active':
        return jsonify({'error': '该员工已离职，无法提交注册申请'}), 403

    # 检查是否已注册
    auth_session = auth_models.AuthSessionLocal()
    try:
        # 检查工号是否已注册
        existing_user = auth_session.query(User).filter_by(emp_no=emp_no).first()
        if existing_user:
            return jsonify({'error': '该工号已注册账户，请直接登录'}), 409

        # 检查用户名是否被占用
        existing_user = auth_session.query(User).filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': '用户名已被占用，请更换'}), 409

        # 检查邮箱是否被占用
        existing_user = auth_session.query(User).filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': '邮箱已被使用，请更换'}), 409

        # 检查是否有待审批的申请
        existing_request = auth_session.query(RegistrationRequest).filter_by(
            emp_no=emp_no,
            status='pending'
        ).first()

        if existing_request:
            return jsonify({'error': '已有待审批的注册申请，请等待处理'}), 409

        # 检查用户名在待审批申请中是否被占用
        existing_request = auth_session.query(RegistrationRequest).filter_by(
            username=username,
            status='pending'
        ).first()

        if existing_request:
            return jsonify({'error': '该用户名已在其他待审批申请中，请更换'}), 409

        # 获取工厂信息
        factory_name = None
        if employee.factory_id:
            factory = Factory.query.get(employee.factory_id)
            if factory:
                factory_name = factory.name

        # 创建注册申请(密码哈希后保存)
        new_request = RegistrationRequest(
            emp_no=emp_no,
            full_name=employee.name,
            username=username,
            email=email,
            hashed_password=hash_password(password),
            department=employee.department,
            title=employee.title,
            factory_name=factory_name,
            status='pending'
        )

        auth_session.add(new_request)
        auth_session.commit()

        return jsonify({
            'message': '注册申请已提交成功！请等待管理员审批，审批结果将通过邮件通知您。',
            'request': new_request.to_dict()
        }), 201

    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'提交失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@register_bp.route('/requests', methods=['GET'])
def get_registration_requests():
    """Get all registration requests (admin only)"""
    status_filter = request.args.get('status', 'pending')

    auth_session = auth_models.AuthSessionLocal()
    try:
        query = auth_session.query(RegistrationRequest)
        
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        requests = query.order_by(RegistrationRequest.created_at.desc()).all()
        
        return jsonify({
            'requests': [req.to_dict() for req in requests]
        })
        
    finally:
        auth_session.close()


@register_bp.route('/approve/<int:request_id>', methods=['POST'])
def approve_registration(request_id):
    """Approve registration request and create user account"""
    data = request.get_json() or {}

    permissions = data.get('permissions', [])

    auth_session = auth_models.AuthSessionLocal()
    try:
        # Get the registration request
        reg_request = auth_session.query(RegistrationRequest).get(request_id)

        if not reg_request:
            return jsonify({'error': '注册申请不存在'}), 404

        if reg_request.status != 'pending':
            return jsonify({'error': f'该申请已被{reg_request.status}'}), 400

        # Check if username already exists (double-check for safety)
        existing_user = auth_session.query(User).filter_by(username=reg_request.username).first()
        if existing_user:
            return jsonify({'error': '用户名已被占用'}), 409

        # Check if emp_no already registered
        existing_user = auth_session.query(User).filter_by(emp_no=reg_request.emp_no).first()
        if existing_user:
            return jsonify({'error': '该工号已注册'}), 409

        # Create user account using stored credentials from registration request
        new_user = User(
            username=reg_request.username,  # Use stored username
            email=reg_request.email,  # Use stored email
            hashed_password=reg_request.hashed_password,  # Use stored hashed password
            full_name=reg_request.full_name,
            emp_no=reg_request.emp_no,
            permissions=json.dumps(permissions),
            is_active=True,
            is_admin=False
        )

        auth_session.add(new_user)

        # Update request status
        reg_request.status = 'approved'
        reg_request.processed_at = datetime.utcnow()

        auth_session.commit()

        return jsonify({
            'message': '申请已批准，账户创建成功',
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'审批失败: {str(e)}'}), 500
    finally:
        auth_session.close()


@register_bp.route('/reject/<int:request_id>', methods=['POST'])
def reject_registration(request_id):
    """Reject registration request"""
    data = request.get_json()
    reason = data.get('reason', '') if data else ''

    auth_session = auth_models.AuthSessionLocal()
    try:
        reg_request = auth_session.query(RegistrationRequest).get(request_id)
        
        if not reg_request:
            return jsonify({'error': '注册申请不存在'}), 404
        
        if reg_request.status != 'pending':
            return jsonify({'error': f'该申请已被{reg_request.status}'}), 400
        
        reg_request.status = 'rejected'
        reg_request.rejection_reason = reason
        reg_request.processed_at = datetime.utcnow()
        
        auth_session.commit()
        
        return jsonify({
            'message': '申请已拒绝',
            'request': reg_request.to_dict()
        })
        
    except Exception as e:
        auth_session.rollback()
        return jsonify({'error': f'拒绝失败: {str(e)}'}), 500
    finally:
        auth_session.close()
