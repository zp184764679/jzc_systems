# routes/auth_routes.py
# 挂载到 /api/v1/auth
from flask import Blueprint, request, jsonify
from extensions import db
from models.user import User, DEPARTMENT_ENUM
import traceback
import sys
import os

# Add shared module to path for SSO
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '..'))
from shared.auth import verify_token

URL_PREFIX = '/api/v1/auth'

bp_auth = Blueprint('auth_router', __name__)

@bp_auth.route('/sso-login', methods=['POST', 'OPTIONS'])
def sso_login():
    """SSO登录 - 接收Portal传来的token"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200

    try:
        # 从请求体或URL参数获取token
        data = request.get_json(silent=True) or {}
        token = data.get('token') or request.args.get('token')

        if not token:
            return jsonify({'error': '缺少token'}), 400

        # 验证token
        payload = verify_token(token)

        if not payload:
            return jsonify({'error': 'Token无效或已过期'}), 401

        # 规范化用户数据，确保前端可以用 user.id 访问
        user_data = {
            **payload,
            'id': payload.get('user_id'),  # 添加 id 字段（前端使用）
            'name': payload.get('full_name'),  # 兼容性别名
            'department': payload.get('department_name'),  # 兼容性别名
        }

        # 返回用户信息，前端存储到localStorage
        return jsonify({
            'message': 'SSO登录成功',
            'user': user_data
        }), 200

    except Exception as e:
        print("sso_login error:", e)
        print(traceback.format_exc())
        return jsonify({'error': f'SSO登录失败: {str(e)}'}), 500


@bp_auth.route('/register-employee', methods=['POST', 'OPTIONS'])
def register_employee():
    """员工注册 - 部门为必填项，并进行严格验证"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200
    
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        department = data.get('department', '').strip()
        employee_no = data.get('employee_no', '').strip()
        phone = data.get('phone', '').strip()

        # 基础字段校验
        if not username:
            return jsonify({"error": "缺少必填字段: username"}), 400
        if not email:
            return jsonify({"error": "缺少必填字段: email"}), 400
        if not password:
            return jsonify({"error": "缺少必填字段: password"}), 400
        
        # ✅ 部门为必填项，不能为空
        if not department:
            return jsonify({
                "error": "缺少必填字段: department。可选部门: " + ", ".join(DEPARTMENT_ENUM)
            }), 400

        # ✅ 部门合法性验证
        if department not in DEPARTMENT_ENUM:
            return jsonify({
                "error": f"部门值无效。可选部门: {', '.join(DEPARTMENT_ENUM)}"
            }), 400
        
        if not phone:
            return jsonify({"error": "缺少必填字段: phone"}), 400

        # 邮箱唯一性检查
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "该邮箱已被注册"}), 400

        # 用户名唯一性检查
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "该用户名已被注册"}), 400

        # 工号唯一性检查（可选字段，但如果提供则必须唯一）
        if employee_no:
            if User.query.filter_by(employee_no=employee_no).first():
                return jsonify({"error": "工号已存在"}), 400

        # 创建用户
        user = User.create_user(
            username=username,
            email=email,
            password=password,
            status='pending',
            department=department,
            employee_no=employee_no if employee_no else None,
            phone=phone,
        )

        # 默认角色 user
        user.role = 'user'

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "message": "注册成功，待管理员审批",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "department": user.department
        }), 201

    except Exception as e:
        db.session.rollback()
        print("register_employee error:", e)
        print(traceback.format_exc())
        return jsonify({"error": "服务器内部错误"}), 500


# ✅ 新增接口：获取当前登录用户的完整信息
@bp_auth.route('/me', methods=['GET', 'OPTIONS'])
def get_current_user():
    """
    GET /api/v1/auth/me
    获取当前登录用户的完整信息

    请求头需要：
    - User-ID: 当前用户ID
    - Authorization: Bearer token (可选，用于从SSO系统获取最新数据)

    返回用户的所有信息，包括 username, department_name, email, phone 等
    优先从共享SSO认证系统获取最新数据
    """
    if request.method == 'OPTIONS':
        return jsonify({"status": "success"}), 200

    try:
        # 获取请求头中的用户ID
        user_id = request.headers.get('User-ID')
        auth_header = request.headers.get('Authorization')

        if not user_id:
            return jsonify({"error": "缺少认证信息（需要 User-ID 请求头）"}), 401

        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({"error": "用户ID格式不正确"}), 400

        # 优先从共享SSO认证数据库获取用户信息
        try:
            from shared.auth import User as SSOUser
            import shared.auth.models as auth_models

            auth_session = auth_models.AuthSessionLocal()
            sso_user = auth_session.query(SSOUser).filter(SSOUser.id == user_id).first()

            if sso_user:
                # 从SSO系统获取到用户，返回最新数据
                user_data = {
                    "id": sso_user.id,
                    "username": sso_user.username,
                    "name": sso_user.full_name or sso_user.username,
                    "full_name": sso_user.full_name,
                    "email": sso_user.email or '',
                    "phone": '',  # SSO系统暂无phone字段
                    "department": sso_user.department_name or '',
                    "department_name": sso_user.department_name or '',
                    "department_id": sso_user.department_id,
                    "position_name": sso_user.position_name or '',
                    "position_id": sso_user.position_id,
                    "team_name": sso_user.team_name or '',
                    "team_id": sso_user.team_id,
                    "role": sso_user.role or 'user',
                    "emp_no": sso_user.emp_no or '',
                    "employee_no": sso_user.emp_no or '',
                }
                auth_session.close()
                return jsonify(user_data), 200

            auth_session.close()
        except Exception as sso_error:
            print(f"从SSO系统获取用户信息失败: {sso_error}")
            # 继续尝试从本地数据库获取

        # 回退：从本地采购系统数据库查询用户
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "用户不存在"}), 404

        # 构建返回数据（本地数据库）
        user_data = {
            "id": user.id,
            "username": user.username,
            "name": getattr(user, 'name', user.username),
            "full_name": getattr(user, 'name', user.username),
            "email": getattr(user, 'email', ''),
            "phone": getattr(user, 'phone', ''),
            "department": getattr(user, 'department', ''),
            "department_name": getattr(user, 'department', ''),
            "role": getattr(user, 'role', 'user'),
            "status": getattr(user, 'status', 'pending'),
            "employee_no": getattr(user, 'employee_no', ''),
            "emp_no": getattr(user, 'employee_no', ''),
        }

        return jsonify(user_data), 200

    except Exception as e:
        print("get_current_user error:", e)
        print(traceback.format_exc())
        return jsonify({"error": "获取用户信息失败"}), 500