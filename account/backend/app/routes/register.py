from flask import Blueprint, request, jsonify, g
import sys
import os
import requests

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.auth import User, hash_password, init_auth_db, create_access_token
from shared.auth.permissions import is_admin
from shared.auth.audit_service import AuditService
from shared.auth_middleware import requires_auth
import shared.auth.models as auth_models
from app.models.registration import RegistrationRequest, get_db, init_db
import json

# HR Backend URL for syncing employee data
HR_BACKEND_URL = os.getenv('HR_BACKEND_URL', 'http://localhost:8003')

# Initialize databases
init_db()  # Initialize registration database
init_auth_db()  # Initialize shared auth database

register_bp = Blueprint('register', __name__, url_prefix='/register')


@register_bp.route('/submit', methods=['POST'])
def submit_registration():
    data = request.get_json()

    if not data or 'emp_no' not in data or 'full_name' not in data:
        return jsonify({'error': '请提供工号和姓名'}), 400

    if 'username' not in data or 'password' not in data:
        return jsonify({'error': '请提供用户名和密码'}), 400

    emp_no = data['emp_no']
    full_name = data['full_name']
    username = data['username']
    password = data['password']
    email = data.get('email')
    factory_name = data.get('factory_name')
    factory_id = data.get('factory_id')
    department = data.get('department')
    department_id = data.get('department_id')
    title = data.get('title')
    position_id = data.get('position_id')
    team = data.get('team')
    team_id = data.get('team_id')

    # Check if user already exists
    auth_session = auth_models.AuthSessionLocal()
    try:
        existing_user = auth_session.query(User).filter(User.emp_no == emp_no).first()
        if existing_user:
            return jsonify({'error': '该工号已注册，请直接登录'}), 400

        # Check if username already exists
        existing_username = auth_session.query(User).filter(User.username == username).first()
        if existing_username:
            return jsonify({'error': '用户名已被使用，请更换'}), 400
    finally:
        auth_session.close()

    # Check if there is already a pending request
    db = get_db()
    try:
        existing_request = db.query(RegistrationRequest).filter(
            RegistrationRequest.emp_no == emp_no,
            RegistrationRequest.status == 'pending'
        ).first()

        if existing_request:
            return jsonify({'error': '您的申请正在审核中，请耐心等待'}), 400

        # Create registration request with hashed password
        new_request = RegistrationRequest(
            emp_no=emp_no,
            full_name=full_name,
            username=username,
            hashed_password=hash_password(password),
            email=email,
            factory_name=factory_name,
            factory_id=factory_id,
            department=department,
            department_id=department_id,
            title=title,
            position_id=position_id,
            team=team,
            team_id=team_id,
            status='pending'
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        return jsonify({
            'message': '注册申请已提交，请等待管理员审批',
            'request': new_request.to_dict()
        }), 201
    
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'提交失败: {str(e)}'}), 500
    finally:
        db.close()


@register_bp.route('/requests', methods=['GET'])
@requires_auth
def get_requests():
    # 检查是否为管理员
    current_user = g.current_user
    if not is_admin(current_user.get('role')):
        return jsonify({'error': '需要管理员权限'}), 403

    status = request.args.get('status', 'pending')

    db = get_db()
    try:
        if status == 'all':
            requests_list = db.query(RegistrationRequest).order_by(
                RegistrationRequest.created_at.desc()
            ).all()
        else:
            requests_list = db.query(RegistrationRequest).filter(
                RegistrationRequest.status == status
            ).order_by(RegistrationRequest.created_at.desc()).all()

        return jsonify([req.to_dict() for req in requests_list])
    finally:
        db.close()


@register_bp.route('/approve/<int:request_id>', methods=['POST'])
@requires_auth
def approve_registration(request_id):
    # 检查是否为管理员
    current_user = g.current_user
    if not is_admin(current_user.get('role')):
        return jsonify({'error': '需要管理员权限'}), 403

    data = request.get_json()
    permissions = data.get('permissions', []) if data else []
    role = data.get('role', 'user') if data else 'user'

    # 验证权限不能为空
    if not permissions or len(permissions) == 0:
        return jsonify({'error': '请至少为用户分配一个系统权限'}), 400

    db = get_db()
    auth_session = auth_models.AuthSessionLocal()

    try:
        # Find registration request
        reg_request = db.query(RegistrationRequest).filter(
            RegistrationRequest.id == request_id
        ).first()

        if not reg_request:
            return jsonify({'error': '申请不存在'}), 404

        if reg_request.status != 'pending':
            return jsonify({'error': '该申请已处理'}), 400

        # Validate that username and password exist in request
        if not reg_request.username or not reg_request.hashed_password:
            return jsonify({'error': '注册申请缺少用户名或密码信息'}), 400

        # Check if username already exists
        existing_user = auth_session.query(User).filter(User.username == reg_request.username).first()
        if existing_user:
            return jsonify({'error': '用户名已存在'}), 400

        # Determine is_admin_flag based on role
        is_admin_flag = role in ['admin', 'super_admin']

        # Create new user using saved username and hashed password
        new_user = User(
            username=reg_request.username,
            hashed_password=reg_request.hashed_password,
            email=reg_request.email,
            full_name=reg_request.full_name,
            emp_no=reg_request.emp_no,
            department_id=reg_request.department_id,
            department_name=reg_request.department,
            position_id=reg_request.position_id,
            position_name=reg_request.title,
            team_id=reg_request.team_id,
            team_name=reg_request.team,
            is_active=True,
            is_admin=is_admin_flag,
            role=role,
            permissions=json.dumps(permissions)
        )
        auth_session.add(new_user)
        auth_session.commit()

        # Update registration request status
        reg_request.status = 'approved'
        db.commit()

        # 记录审计日志
        try:
            AuditService.log(
                action_type='user_approve',
                user_id=current_user.get('user_id'),
                username=current_user.get('username'),
                resource_type='registration',
                resource_id=str(request_id),
                description=f'审批通过用户注册: {reg_request.username} (角色: {role}, 权限: {permissions})',
                status='success',
                module='account'
            )
        except Exception as audit_error:
            print(f"审计日志记录失败: {audit_error}")

        # Sync data back to HR system - update employee info if emp_no matches
        hr_sync_result = None
        try:
            hr_sync_result = sync_to_hr_system(reg_request)
        except Exception as e:
            print(f"HR同步警告: {e}")  # Log but don't fail the approval

        return jsonify({
            'message': '申请已批准，用户创建成功',
            'user': new_user.to_dict(),
            'hr_sync': hr_sync_result
        })

    except Exception as e:
        auth_session.rollback()
        db.rollback()
        # 记录失败的审计日志
        try:
            AuditService.log(
                action_type='user_approve',
                user_id=current_user.get('user_id'),
                username=current_user.get('username'),
                resource_type='registration',
                resource_id=str(request_id),
                description=f'审批用户注册失败: {str(e)}',
                status='failed',
                error_message=str(e),
                module='account'
            )
        except Exception:
            pass
        return jsonify({'error': f'创建用户失败: {str(e)}'}), 500
    finally:
        auth_session.close()
        db.close()


def sync_to_hr_system(reg_request):
    """
    同步注册信息到HR系统
    如果工号+姓名匹配HR系统的员工记录，则用注册信息更新HR系统
    """
    try:
        # 创建内部服务调用的 token（系统管理员权限）
        service_token = create_access_token({
            'user_id': 0,
            'username': 'system_service',
            'role': 'super_admin',
            'is_admin': True,
            'service': 'account_hr_sync'
        })
        headers = {'Authorization': f'Bearer {service_token}'}

        # 先查询HR系统中是否有匹配的员工
        response = requests.get(
            f'{HR_BACKEND_URL}/api/employees',
            params={'search': reg_request.emp_no},
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            return {'success': False, 'error': f'HR系统查询失败: {response.status_code}'}

        data = response.json()
        employees = data.get('data', [])

        # 查找匹配的员工（工号匹配）
        matched_employee = None
        for emp in employees:
            if emp.get('empNo') == reg_request.emp_no:
                matched_employee = emp
                break

        if not matched_employee:
            return {'success': False, 'error': '未找到匹配的HR员工记录', 'emp_no': reg_request.emp_no}

        # 验证姓名是否匹配
        hr_name = matched_employee.get('name', '')
        if hr_name != reg_request.full_name:
            return {
                'success': False,
                'error': f'姓名不匹配 (HR: {hr_name}, 注册: {reg_request.full_name})',
                'emp_no': reg_request.emp_no
            }

        # 构建更新数据 - 用注册信息覆盖HR系统
        update_data = {}

        if reg_request.department_id:
            update_data['department_id'] = reg_request.department_id
        if reg_request.position_id:
            update_data['position_id'] = reg_request.position_id
        if reg_request.team_id:
            update_data['team_id'] = reg_request.team_id
        if reg_request.factory_id:
            update_data['factory_id'] = reg_request.factory_id

        if not update_data:
            return {'success': True, 'message': '无需更新', 'emp_no': reg_request.emp_no}

        # 调用HR系统API更新员工信息
        employee_id = matched_employee.get('id')
        update_response = requests.put(
            f'{HR_BACKEND_URL}/api/employees/{employee_id}',
            json=update_data,
            headers=headers,
            timeout=10
        )

        if update_response.status_code == 200:
            return {
                'success': True,
                'message': 'HR系统员工信息已更新',
                'emp_no': reg_request.emp_no,
                'updated_fields': list(update_data.keys())
            }
        else:
            return {
                'success': False,
                'error': f'HR系统更新失败: {update_response.status_code}',
                'emp_no': reg_request.emp_no
            }

    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'无法连接HR系统: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'同步失败: {str(e)}'}


@register_bp.route('/reject/<int:request_id>', methods=['POST'])
@requires_auth
def reject_registration(request_id):
    # 检查是否为管理员
    current_user = g.current_user
    if not is_admin(current_user.get('role')):
        return jsonify({'error': '需要管理员权限'}), 403

    data = request.get_json()

    if not data or 'reason' not in data:
        return jsonify({'error': '请提供拒绝原因'}), 400

    reason = data['reason']

    db = get_db()
    try:
        # Find registration request
        reg_request = db.query(RegistrationRequest).filter(
            RegistrationRequest.id == request_id
        ).first()

        if not reg_request:
            return jsonify({'error': '申请不存在'}), 404

        if reg_request.status != 'pending':
            return jsonify({'error': '该申请已处理'}), 400

        # Update registration request status
        reg_request.status = 'rejected'
        reg_request.reason = reason
        db.commit()

        # 记录审计日志
        try:
            AuditService.log(
                action_type='user_reject',
                user_id=current_user.get('user_id'),
                username=current_user.get('username'),
                resource_type='registration',
                resource_id=str(request_id),
                description=f'拒绝用户注册: {reg_request.username} (原因: {reason})',
                status='success',
                module='account'
            )
        except Exception as audit_error:
            print(f"审计日志记录失败: {audit_error}")

        return jsonify({'message': '申请已拒绝'})

    except Exception as e:
        db.rollback()
        return jsonify({'error': f'更新状态失败: {str(e)}'}), 500
    finally:
        db.close()