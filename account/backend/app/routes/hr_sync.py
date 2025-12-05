"""
HR Sync API - 从HR系统同步员工数据到账户系统
"""
from flask import Blueprint, request, jsonify
import requests
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.auth import User, verify_token
import shared.auth.models as auth_models
from functools import wraps

hr_sync_bp = Blueprint('hr_sync', __name__, url_prefix='/hr-sync')

# HR Backend URL
HR_BACKEND_URL = os.getenv('HR_BACKEND_URL', 'http://localhost:8003')

# HR数据库配置（直接连接HR数据库获取组织数据）
HR_DB_USER = os.getenv('HR_DB_USER', 'app')
HR_DB_PASSWORD = os.getenv('HR_DB_PASSWORD', 'app')
HR_DB_HOST = os.getenv('HR_DB_HOST', 'localhost')
HR_DB_NAME = os.getenv('HR_DB_NAME', 'hr_system')


@hr_sync_bp.route('/org-options', methods=['GET'])
def get_org_options():
    """获取组织选项（工厂、部门、岗位）- 公开接口供注册使用"""
    try:
        from sqlalchemy import create_engine, text

        # 连接HR数据库
        hr_db_url = f'mysql+pymysql://{HR_DB_USER}:{HR_DB_PASSWORD}@{HR_DB_HOST}/{HR_DB_NAME}?charset=utf8mb4'
        hr_engine = create_engine(hr_db_url, echo=False)

        with hr_engine.connect() as conn:
            # 获取工厂（地点）
            factories = []
            result = conn.execute(text("SELECT id, name FROM factories WHERE is_active = 1 ORDER BY sort_order, name"))
            for row in result:
                factories.append({'id': row[0], 'name': row[1]})

            # 获取部门
            departments = []
            result = conn.execute(text("SELECT id, name FROM departments WHERE is_active = 1 ORDER BY sort_order, name"))
            for row in result:
                departments.append({'id': row[0], 'name': row[1]})

            # 获取岗位
            positions = []
            result = conn.execute(text("SELECT id, name FROM positions WHERE is_active = 1 ORDER BY sort_order, name"))
            for row in result:
                positions.append({'id': row[0], 'name': row[1]})

            # 获取团队
            teams = []
            result = conn.execute(text("SELECT id, name FROM teams WHERE is_active = 1 ORDER BY sort_order, name"))
            for row in result:
                teams.append({'id': row[0], 'name': row[1]})

        return jsonify({
            'factories': factories,
            'departments': departments,
            'positions': positions,
            'teams': teams
        })

    except Exception as e:
        return jsonify({'error': f'获取组织数据失败: {str(e)}'}), 500


def require_admin(f):
    '''Decorator to require admin authentication'''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '未授权访问'}), 401

        token = auth_header.split(' ')[1]
        try:
            payload = verify_token(token)
            if not payload:
                return jsonify({'error': '无效的令牌'}), 401
            request.current_user = payload

            # Check if user is admin
            is_admin = payload.get('is_admin', False)
            role = payload.get('role', '')
            if not is_admin and role not in ['admin', 'super_admin']:
                return jsonify({'error': '需要管理员权限'}), 403

        except Exception as e:
            return jsonify({'error': '无效的令牌'}), 401

        return f(*args, **kwargs)
    return decorated_function


@hr_sync_bp.route('/employees', methods=['GET'])
@require_admin
def get_hr_employees():
    """获取HR系统的在职员工列表"""
    try:
        # 调用HR后端API获取在职员工
        response = requests.get(
            f'{HR_BACKEND_URL}/api/employees',
            params={'employment_status': 'Active'},
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({'error': f'HR系统请求失败: {response.status_code}'}), 500

        data = response.json()
        employees = data.get('employees', data) if isinstance(data, dict) else data

        # 简化返回数据
        result = []
        for emp in employees:
            result.append({
                'empNo': emp.get('empNo'),
                'name': emp.get('name'),
                'department': emp.get('department'),
                'department_id': emp.get('department_id'),
                'title': emp.get('title'),
                'position_id': emp.get('position_id'),
                'team': emp.get('team'),
                'team_id': emp.get('team_id'),
                'email': emp.get('email'),
                'phone': emp.get('phone'),
                'factory': emp.get('factory'),
                'factory_id': emp.get('factory_id'),
            })

        return jsonify({
            'total': len(result),
            'employees': result
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'无法连接HR系统: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'获取HR员工数据失败: {str(e)}'}), 500


@hr_sync_bp.route('/preview', methods=['GET'])
@require_admin
def preview_sync():
    """预览同步结果 - 显示哪些用户会被更新"""
    try:
        # 获取HR员工数据
        response = requests.get(
            f'{HR_BACKEND_URL}/api/employees',
            params={'employment_status': 'Active'},
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({'error': f'HR系统请求失败: {response.status_code}'}), 500

        data = response.json()
        hr_employees = data.get('employees', data) if isinstance(data, dict) else data

        # 建立工号索引
        hr_by_empno = {emp.get('empNo'): emp for emp in hr_employees if emp.get('empNo')}

        # 获取账户系统用户
        auth_session = auth_models.AuthSessionLocal()
        try:
            users = auth_session.query(User).all()

            matched = []
            unmatched_users = []
            unmatched_employees = list(hr_by_empno.keys())

            for user in users:
                if user.emp_no and user.emp_no in hr_by_empno:
                    emp = hr_by_empno[user.emp_no]
                    unmatched_employees.remove(user.emp_no)

                    # 检查需要更新的字段
                    changes = []
                    if user.full_name != emp.get('name'):
                        changes.append(f"姓名: {user.full_name} -> {emp.get('name')}")
                    if user.department_name != emp.get('department'):
                        changes.append(f"部门: {user.department_name} -> {emp.get('department')}")
                    if user.position_name != emp.get('title'):
                        changes.append(f"岗位: {user.position_name} -> {emp.get('title')}")
                    if user.team_name != emp.get('team'):
                        changes.append(f"团队: {user.team_name} -> {emp.get('team')}")

                    matched.append({
                        'user_id': user.id,
                        'username': user.username,
                        'emp_no': user.emp_no,
                        'current_name': user.full_name,
                        'hr_name': emp.get('name'),
                        'hr_department': emp.get('department'),
                        'hr_position': emp.get('title'),
                        'hr_team': emp.get('team'),
                        'changes': changes,
                        'needs_update': len(changes) > 0
                    })
                else:
                    unmatched_users.append({
                        'user_id': user.id,
                        'username': user.username,
                        'emp_no': user.emp_no,
                        'full_name': user.full_name
                    })

            return jsonify({
                'summary': {
                    'total_hr_employees': len(hr_employees),
                    'total_users': len(users),
                    'matched': len(matched),
                    'needs_update': len([m for m in matched if m['needs_update']]),
                    'unmatched_users': len(unmatched_users),
                    'unmatched_employees': len(unmatched_employees)
                },
                'matched': matched,
                'unmatched_users': unmatched_users,
                'unmatched_employees': unmatched_employees[:50]  # 只返回前50个
            })

        finally:
            auth_session.close()

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'无法连接HR系统: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'预览同步失败: {str(e)}'}), 500


@hr_sync_bp.route('/execute', methods=['POST'])
@require_admin
def execute_sync():
    """执行同步 - 更新匹配用户的信息"""
    try:
        data = request.get_json() or {}
        update_name = data.get('update_name', True)  # 是否更新姓名
        user_ids = data.get('user_ids')  # 指定要更新的用户ID列表，为空则更新全部匹配

        # 获取HR员工数据
        response = requests.get(
            f'{HR_BACKEND_URL}/api/employees',
            params={'employment_status': 'Active'},
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({'error': f'HR系统请求失败: {response.status_code}'}), 500

        resp_data = response.json()
        hr_employees = resp_data.get('employees', resp_data) if isinstance(resp_data, dict) else resp_data

        # 建立工号索引
        hr_by_empno = {emp.get('empNo'): emp for emp in hr_employees if emp.get('empNo')}

        # 执行同步
        auth_session = auth_models.AuthSessionLocal()
        try:
            users = auth_session.query(User).all()

            updated_count = 0
            updated_users = []
            errors = []

            for user in users:
                # 如果指定了用户ID列表，只更新指定的用户
                if user_ids and user.id not in user_ids:
                    continue

                if user.emp_no and user.emp_no in hr_by_empno:
                    emp = hr_by_empno[user.emp_no]
                    changes = []

                    try:
                        # 更新部门信息
                        if emp.get('department') and user.department_name != emp.get('department'):
                            old_val = user.department_name
                            user.department_name = emp.get('department')
                            user.department_id = emp.get('department_id')
                            changes.append(f"部门: {old_val} -> {emp.get('department')}")

                        # 更新岗位信息
                        if emp.get('title') and user.position_name != emp.get('title'):
                            old_val = user.position_name
                            user.position_name = emp.get('title')
                            user.position_id = emp.get('position_id')
                            changes.append(f"岗位: {old_val} -> {emp.get('title')}")

                        # 更新团队信息
                        if emp.get('team') and user.team_name != emp.get('team'):
                            old_val = user.team_name
                            user.team_name = emp.get('team')
                            user.team_id = emp.get('team_id')
                            changes.append(f"团队: {old_val} -> {emp.get('team')}")

                        # 更新姓名（可选）
                        if update_name and emp.get('name') and user.full_name != emp.get('name'):
                            old_val = user.full_name
                            user.full_name = emp.get('name')
                            changes.append(f"姓名: {old_val} -> {emp.get('name')}")

                        if changes:
                            updated_count += 1
                            updated_users.append({
                                'user_id': user.id,
                                'username': user.username,
                                'emp_no': user.emp_no,
                                'changes': changes
                            })

                    except Exception as e:
                        errors.append({
                            'user_id': user.id,
                            'username': user.username,
                            'error': str(e)
                        })

            auth_session.commit()

            return jsonify({
                'success': True,
                'message': f'同步完成，更新了 {updated_count} 个用户',
                'updated_count': updated_count,
                'updated_users': updated_users,
                'errors': errors
            })

        except Exception as e:
            auth_session.rollback()
            raise e
        finally:
            auth_session.close()

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'无法连接HR系统: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'同步执行失败: {str(e)}'}), 500


@hr_sync_bp.route('/batch-create', methods=['POST'])
@require_admin
def batch_create_users():
    """批量创建用户 - 从HR在职员工中创建未注册的用户"""
    try:
        data = request.get_json() or {}
        emp_nos = data.get('emp_nos', [])  # 要创建的工号列表
        default_password = data.get('default_password', 'jzc123456')  # 默认密码
        default_permissions = data.get('default_permissions', [])  # 默认权限

        if not emp_nos:
            return jsonify({'error': '请提供要创建的工号列表'}), 400

        # 获取HR员工数据
        response = requests.get(
            f'{HR_BACKEND_URL}/api/employees',
            params={'employment_status': 'Active'},
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({'error': f'HR系统请求失败: {response.status_code}'}), 500

        resp_data = response.json()
        hr_employees = resp_data.get('employees', resp_data) if isinstance(resp_data, dict) else resp_data

        # 建立工号索引
        hr_by_empno = {emp.get('empNo'): emp for emp in hr_employees if emp.get('empNo')}

        # 执行创建
        from shared.auth import hash_password
        import json

        auth_session = auth_models.AuthSessionLocal()
        try:
            created_count = 0
            created_users = []
            errors = []

            for emp_no in emp_nos:
                if emp_no not in hr_by_empno:
                    errors.append({'emp_no': emp_no, 'error': 'HR系统中未找到此工号'})
                    continue

                # 检查是否已存在
                existing = auth_session.query(User).filter(User.emp_no == emp_no).first()
                if existing:
                    errors.append({'emp_no': emp_no, 'error': f'工号已存在（用户名: {existing.username}）'})
                    continue

                emp = hr_by_empno[emp_no]

                # 生成用户名（使用工号）
                username = emp_no.lower()

                # 检查用户名是否已存在
                existing_username = auth_session.query(User).filter(User.username == username).first()
                if existing_username:
                    username = f"{emp_no.lower()}_{emp.get('name', '')[:1]}"

                try:
                    new_user = User(
                        username=username,
                        email=emp.get('email') or f"{username}@jzchardware.cn",
                        hashed_password=hash_password(default_password),
                        full_name=emp.get('name'),
                        emp_no=emp_no,
                        user_type='employee',
                        role='user',
                        permissions=json.dumps(default_permissions),
                        department_id=emp.get('department_id'),
                        department_name=emp.get('department'),
                        position_id=emp.get('position_id'),
                        position_name=emp.get('title'),
                        team_id=emp.get('team_id'),
                        team_name=emp.get('team'),
                        is_active=True,
                        is_admin=False
                    )
                    auth_session.add(new_user)
                    auth_session.flush()  # 获取ID

                    created_count += 1
                    created_users.append({
                        'user_id': new_user.id,
                        'username': username,
                        'emp_no': emp_no,
                        'full_name': emp.get('name'),
                        'department': emp.get('department')
                    })

                except Exception as e:
                    errors.append({'emp_no': emp_no, 'error': str(e)})

            auth_session.commit()

            return jsonify({
                'success': True,
                'message': f'批量创建完成，成功创建 {created_count} 个用户',
                'created_count': created_count,
                'created_users': created_users,
                'errors': errors,
                'default_password': default_password
            })

        except Exception as e:
            auth_session.rollback()
            raise e
        finally:
            auth_session.close()

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'无法连接HR系统: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'批量创建失败: {str(e)}'}), 500
