"""
System Management API - PM2服务管理
提供PM2服务的启动、停止、重启、状态查询等功能
安全修复: 添加JWT认证、角色检查、服务名白名单、移除命令注入风险
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import subprocess
import json
import re
import os
import sys

# 添加共享模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.auth import verify_token

system_bp = Blueprint('system', __name__, url_prefix='/api/system')

# 允许的服务名白名单（只允许操作这些服务）
ALLOWED_SERVICES = {
    'portal-backend',
    'hr-backend',
    'account-backend',
    'quotation-backend',
    'caigou-backend',
    'shm-backend',
    'crm-backend',
    'scm-backend',
    'eam-backend',
    'mes-backend',
    'all'  # 允许 restart all / stop all
}

# 日志行数限制
MAX_LOG_LINES = 500


def require_super_admin(f):
    """装饰器：要求 super_admin 角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从 Authorization Header 获取 Token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': '未授权：缺少认证Token'}), 401

        token = auth_header[7:]
        if not token:
            return jsonify({'success': False, 'error': '未授权：Token为空'}), 401

        # 验证 Token
        payload = verify_token(token)
        if not payload:
            return jsonify({'success': False, 'error': '未授权：Token无效或已过期'}), 401

        # 检查角色是否为 super_admin
        role = payload.get('role', '')
        if role != 'super_admin':
            return jsonify({'success': False, 'error': '权限不足：仅超级管理员可执行此操作'}), 403

        # 将用户信息添加到 request
        request.current_user = payload
        return f(*args, **kwargs)

    return decorated_function


def validate_service_name(service_name):
    """验证服务名是否在白名单中"""
    if not service_name:
        return False
    # 转换为小写进行比较
    return service_name.lower() in ALLOWED_SERVICES


def sanitize_service_name(service_name):
    """清理服务名，只允许字母、数字、连字符"""
    if not service_name:
        return None
    # 只允许字母、数字、连字符
    if not re.match(r'^[a-zA-Z0-9\-]+$', service_name):
        return None
    return service_name


def run_pm2_command_safe(args_list):
    """安全执行PM2命令（使用列表参数，避免shell=True）"""
    try:
        # 构建命令列表
        cmd = ['powershell', '-Command', f'pm2 {" ".join(args_list)} --silent']
        result = subprocess.run(
            cmd,
            shell=False,  # 安全：不使用shell
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else ''
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': '命令执行超时'
        }
    except Exception:
        return {
            'success': False,
            'output': '',
            'error': '命令执行失败'
        }


@system_bp.route('/services', methods=['GET'])
@require_super_admin
def get_services():
    """获取所有PM2服务状态"""
    try:
        # 执行pm2 jlist命令获取JSON格式的服务列表
        result = subprocess.run(
            ['powershell', '-Command', 'pm2 jlist'],
            shell=False,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            services_data = json.loads(result.stdout)

            # 格式化服务数据
            services = []
            for service in services_data:
                services.append({
                    'name': service.get('name'),
                    'pm_id': service.get('pm_id'),
                    'status': service.get('pm2_env', {}).get('status'),
                    'cpu': service.get('monit', {}).get('cpu', 0),
                    'memory': service.get('monit', {}).get('memory', 0),
                    'uptime': service.get('pm2_env', {}).get('pm_uptime'),
                    'restarts': service.get('pm2_env', {}).get('restart_time', 0),
                    'pid': service.get('pid')
                })

            return jsonify({
                'success': True,
                'services': services
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': '获取服务列表失败'
            }), 500

    except json.JSONDecodeError:
        return jsonify({
            'success': False,
            'error': '解析服务列表失败'
        }), 500
    except Exception:
        return jsonify({
            'success': False,
            'error': '获取服务状态时发生错误'
        }), 500


@system_bp.route('/service/<service_name>/start', methods=['POST'])
@require_super_admin
def start_service(service_name):
    """启动指定服务"""
    # 验证服务名
    clean_name = sanitize_service_name(service_name)
    if not clean_name or not validate_service_name(clean_name):
        return jsonify({
            'success': False,
            'error': '无效的服务名或服务不在允许列表中'
        }), 400

    result = run_pm2_command_safe(['start', clean_name])

    if result['success']:
        return jsonify({
            'success': True,
            'message': f'服务 {clean_name} 启动成功'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': '服务启动失败'
        }), 500


@system_bp.route('/service/<service_name>/stop', methods=['POST'])
@require_super_admin
def stop_service(service_name):
    """停止指定服务"""
    # 验证服务名
    clean_name = sanitize_service_name(service_name)
    if not clean_name or not validate_service_name(clean_name):
        return jsonify({
            'success': False,
            'error': '无效的服务名或服务不在允许列表中'
        }), 400

    result = run_pm2_command_safe(['stop', clean_name])

    if result['success']:
        return jsonify({
            'success': True,
            'message': f'服务 {clean_name} 停止成功'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': '服务停止失败'
        }), 500


@system_bp.route('/service/<service_name>/restart', methods=['POST'])
@require_super_admin
def restart_service(service_name):
    """重启指定服务"""
    # 验证服务名
    clean_name = sanitize_service_name(service_name)
    if not clean_name or not validate_service_name(clean_name):
        return jsonify({
            'success': False,
            'error': '无效的服务名或服务不在允许列表中'
        }), 400

    result = run_pm2_command_safe(['restart', clean_name])

    if result['success']:
        return jsonify({
            'success': True,
            'message': f'服务 {clean_name} 重启成功'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': '服务重启失败'
        }), 500


@system_bp.route('/service/<service_name>/logs', methods=['GET'])
@require_super_admin
def get_service_logs(service_name):
    """获取服务日志"""
    # 验证服务名
    clean_name = sanitize_service_name(service_name)
    if not clean_name or not validate_service_name(clean_name):
        return jsonify({
            'success': False,
            'error': '无效的服务名或服务不在允许列表中'
        }), 400

    # 限制日志行数
    lines = request.args.get('lines', 50, type=int)
    lines = min(max(1, lines), MAX_LOG_LINES)  # 限制在 1-500 之间

    try:
        result = subprocess.run(
            ['powershell', '-Command', f'pm2 logs {clean_name} --lines {lines} --nostream'],
            shell=False,
            capture_output=True,
            text=True,
            timeout=10
        )

        return jsonify({
            'success': True,
            'logs': result.stdout
        }), 200

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': '获取日志超时'
        }), 500
    except Exception:
        return jsonify({
            'success': False,
            'error': '获取日志失败'
        }), 500


@system_bp.route('/restart-all', methods=['POST'])
@require_super_admin
def restart_all():
    """重启所有服务"""
    result = run_pm2_command_safe(['restart', 'all'])

    if result['success']:
        return jsonify({
            'success': True,
            'message': '所有服务重启成功'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': '重启所有服务失败'
        }), 500


@system_bp.route('/stop-all', methods=['POST'])
@require_super_admin
def stop_all():
    """停止所有服务"""
    result = run_pm2_command_safe(['stop', 'all'])

    if result['success']:
        return jsonify({
            'success': True,
            'message': '所有服务停止成功'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': '停止所有服务失败'
        }), 500
