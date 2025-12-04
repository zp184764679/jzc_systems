# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.user import User, DEPARTMENT_ENUM, ROLE_LEVELS
from sqlalchemy import text, inspect
import traceback
import sys
import os

# Add shared module to path for JWT verification
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '..'))
from shared.auth import verify_token, verify_password, create_token_from_user, init_auth_db, AuthSessionLocal
from shared.auth import User as AuthUser  # 统一账户系统用户

bp = Blueprint('user', __name__, url_prefix="/api/v1")

# 公开路由列表（不需要认证）
PUBLIC_ENDPOINTS = ['/register', '/login']


@bp.before_request
def check_auth():
    """JWT认证检查（排除公开路由）"""
    if request.method == 'OPTIONS':
        return None

    # 检查是否为公开路由
    for endpoint in PUBLIC_ENDPOINTS:
        if request.path.endswith(endpoint):
            return None

    # 检查 Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if payload:
            request.current_user_id = payload.get('user_id')
            request.current_user_role = payload.get('role')
            return None

    # 回退检查 User-ID header
    user_id = request.headers.get('User-ID')
    if user_id:
        request.current_user_id = user_id
        request.current_user_role = request.headers.get('User-Role')
        return None

    return jsonify({"error": "未授权：请先登录"}), 401

def check_super_admin_permission():
    """检查是否为超级管理员"""
    user_id = request.headers.get('User-ID')
    user_role = request.headers.get('User-Role')
    
    if user_role == 'super_admin':
        return True, None, None
    
    if user_id:
        try:
            user = User.query.get(int(user_id))
            if user and user.role == 'super_admin':
                return True, None, None
        except:
            pass
    
    return False, jsonify({"error": "权限不足：只有超级管理员可以访问"}), 403


def check_admin_permission():
    """检查是否为管理员（admin 或 super_admin）"""
    user_id = request.headers.get('User-ID')
    user_role = request.headers.get('User-Role')
    
    # 方式1：前端直接传入角色（快速）
    if user_role in ['admin', 'super_admin']:
        return True, None, None
    
    # 方式2：从用户ID查询角色（更安全）
    if user_id:
        try:
            user = User.query.get(int(user_id))
            if user and user.role in ['admin', 'super_admin']:
                return True, None, None
        except:
            pass
    
    return False, jsonify({"error": "权限不足：只有管理员可以访问"}), 403


def get_current_user():
    """从请求头获取当前用户"""
    user_id = request.headers.get('User-ID')
    user_role = request.headers.get('User-Role')
    
    if not user_id:
        return None, jsonify({"error": "未提供用户认证信息"}), 401
    
    user = User.query.get(int(user_id))
    if not user:
        return None, jsonify({"error": "用户不存在"}), 404
    
    return user, None, None

@bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    """用户注册 - 部门为必填项"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误，请使用 JSON"}), 400
            
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        department = data.get('department', '').strip()
        employee_no = data.get('employee_no', '').strip()
        phone = data.get('phone', '').strip()

        if not username or not username.strip():
            return jsonify({"error": "用户名不能为空"}), 400
        if not email or not email.strip():
            return jsonify({"error": "邮箱不能为空"}), 400
        if not password or not password.strip():
            return jsonify({"error": "密码不能为空"}), 400
        
        if not department:
            return jsonify({"error": "部门为必填项，请选择部门"}), 400
        
        if department not in DEPARTMENT_ENUM:
            return jsonify({
                "error": f"部门不在可选范围。可选部门: {', '.join(DEPARTMENT_ENUM)}"
            }), 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "该邮箱已被注册"}), 400
        
        if employee_no:
            existing_employee = User.query.filter_by(employee_no=employee_no).first()
            if existing_employee:
                return jsonify({"error": "该工号已被注册"}), 400

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username.strip(), 
            email=email.strip(), 
            password_hash=hashed_password, 
            status='pending',
            department=department,
            employee_no=employee_no if employee_no else None,
            phone=phone if phone else None
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "注册成功，待管理员审批"}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"注册错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "服务器内部错误"}), 500

@bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """用户登录 - 使用统一账户系统"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200

    try:
        data = request.get_json()
        print(f"[LOGIN DEBUG] request.get_json() = {data}")

        if not data:
            return jsonify({"error": "请求数据格式错误，请使用 JSON"}), 400

        email = data.get('email')
        password = data.get('password')
        print(f"[LOGIN DEBUG] email = {email}, password = {'*' * len(password) if password else 'None'}")

        if not email or not password:
            return jsonify({"error": "请提供完整的登录信息"}), 400

        # 使用统一账户系统进行认证
        from sqlalchemy.orm import sessionmaker
        engine = init_auth_db()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        try:
            # 查询统一账户表
            auth_user = session.query(AuthUser).filter_by(email=email).first()
            print(f"[LOGIN DEBUG] auth_user found = {auth_user is not None}")

            if not auth_user:
                return jsonify({"error": "账户或密码错误"}), 400

            # 验证密码
            if not verify_password(password, auth_user.hashed_password):
                print("[LOGIN DEBUG] password mismatch")
                return jsonify({"error": "账户或密码错误"}), 400

            # 检查用户是否激活
            if not auth_user.is_active:
                return jsonify({"error": "用户账户已被禁用"}), 403

            # 生成JWT token（需要传入字典）
            token = create_token_from_user(auth_user.to_dict())

            user_data = {
                "message": "登录成功",
                "token": token,
                "user_id": auth_user.id,
                "username": auth_user.username,
                "full_name": auth_user.full_name,
                "email": auth_user.email,
                "role": auth_user.role,
                "status": "approved",  # 统一账户系统中的用户都是已批准的
                "department": auth_user.department_name or "",
                "employee_no": auth_user.emp_no or "",
                "type": "employee",
            }
            return jsonify(user_data), 200
        finally:
            session.close()

    except Exception as e:
        print(f"登录错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "服务器内部错误"}), 500

@bp.route('/approve/<int:user_id>', methods=['POST', 'OPTIONS'])
def approve_user(user_id):
    """管理员审批用户"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200
    
    try:
        current_user, err_response, err_code = get_current_user()
        if err_response:
            return err_response, err_code
        
        if current_user.role not in ['admin', 'super_admin']:
            return jsonify({"error": "权限不足"}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "用户未找到"}), 404

        if current_user.role == 'admin' and user.role != 'user':
            return jsonify({"error": "管理员只能审批普通用户"}), 403

        user.status = 'approved'
        db.session.commit()
        return jsonify({"message": "用户已批准"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"审批用户错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "服务器内部错误"}), 500

@bp.route('/admin/users', methods=['GET', 'OPTIONS'])
def get_users():
    """获取用户列表（支持搜索）- 管理员权限（admin 或 super_admin）"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200
    
    try:
        is_admin, err_response, err_code = check_admin_permission()
        if not is_admin:
            return err_response, err_code
        
        keyword = request.args.get('keyword', '').strip()
        query = User.query
        
        if keyword:
            try:
                user_id = int(keyword)
                query = query.filter(
                    (User.id == user_id) |
                    (User.username.ilike(f'%{keyword}%')) |
                    (User.email.ilike(f'%{keyword}%'))
                )
            except ValueError:
                query = query.filter(
                    (User.username.ilike(f'%{keyword}%')) |
                    (User.email.ilike(f'%{keyword}%'))
                )
        
        users = query.all()
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'status': user.status,
                'department': user.department or "",
                'employee_no': user.employee_no or "",
                'phone': user.phone or "",
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        return jsonify(users_data), 200
    except Exception as e:
        print(f"获取用户列表错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "服务器内部错误"}), 500

@bp.route('/reject/<int:user_id>', methods=['POST', 'OPTIONS'])
def reject_user(user_id):
    """管理员拒绝用户"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200
    
    try:
        current_user, err_response, err_code = get_current_user()
        if err_response:
            return err_response, err_code
        
        if current_user.role not in ['admin', 'super_admin']:
            return jsonify({"error": "权限不足"}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "用户未找到"}), 404

        user.status = 'rejected'
        db.session.commit()
        return jsonify({"message": "用户已拒绝"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"拒绝用户错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "服务器内部错误"}), 500

@bp.route('/delete/<int:user_id>', methods=['DELETE', 'OPTIONS'])
def delete_user(user_id):
    """管理员删除用户 - 超级管理员权限"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200
    
    try:
        is_super_admin, err_response, err_code = check_super_admin_permission()
        if not is_super_admin:
            return err_response, err_code

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "用户未找到"}), 404

        pr_ids = [pr.id for pr in user.prs]
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            "message": "用户已删除",
            "user_id": user_id,
            "deleted_prs_count": len(pr_ids),
            "deleted_pr_ids": pr_ids
        }), 200
        
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        print(f"删除用户错误: {error_msg}")
        print(traceback.format_exc())
        return jsonify({
            "error": "删除用户失败",
            "detail": error_msg
        }), 500

@bp.route('/update-role/<int:user_id>', methods=['POST', 'OPTIONS'])
def update_user_role(user_id):
    """管理员更新用户角色 - 超级管理员权限"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200
    
    try:
        is_super_admin, err_response, err_code = check_super_admin_permission()
        if not is_super_admin:
            return err_response, err_code
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误，请使用 JSON"}), 400
            
        new_role = data.get('role')
        if not new_role or new_role not in ROLE_LEVELS:
            return jsonify({"error": "无效的角色"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "用户未找到"}), 404

        user.role = new_role
        db.session.commit()
        
        return jsonify({"message": "用户角色已更新", "role": new_role}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"更新用户角色错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "服务器内部错误"}), 500

@bp.route('/admin/users/<int:user_id>', methods=['PUT', 'OPTIONS'])
def update_user(user_id):
    """管理员更新用户信息 - 超级管理员权限"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200
    
    try:
        is_super_admin, err_response, err_code = check_super_admin_permission()
        if not is_super_admin:
            return err_response, err_code
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据格式错误，请使用 JSON"}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "用户未找到"}), 404
        
        if 'username' in data and data['username']:
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.id != user_id:
                return jsonify({"error": "用户名已存在"}), 400
            user.username = data['username']
        
        if 'email' in data and data['email']:
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                return jsonify({"error": "邮箱已存在"}), 400
            user.email = data['email']
        
        if 'status' in data:
            user.status = data['status']
        
        if 'department' in data and data['department']:
            if data['department'] not in DEPARTMENT_ENUM:
                return jsonify({
                    "error": f"部门不在可选范围。可选部门: {', '.join(DEPARTMENT_ENUM)}"
                }), 400
            user.department = data['department']
        
        if 'employee_no' in data:
            user.employee_no = data['employee_no'] if data['employee_no'] else None
        
        if 'phone' in data:
            user.phone = data['phone'] if data['phone'] else None
        
        if 'role' in data:
            user.role = data['role']
        
        db.session.commit()
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"更新用户信息错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "服务器内部错误"}), 500

@bp.route('/me', methods=['GET', 'OPTIONS'])
def get_current_user_info():
    """获取当前登录用户信息"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200
    
    try:
        current_user, err_response, err_code = get_current_user()
        if err_response:
            return err_response, err_code

        return jsonify(current_user.to_dict()), 200
        
    except Exception as e:
        print(f"获取用户信息错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "服务器内部错误"}), 500