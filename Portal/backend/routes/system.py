"""
System Management API - PM2服务管理
提供PM2服务的启动、停止、重启、状态查询等功能
"""
from flask import Blueprint, jsonify, request
import subprocess
import json

system_bp = Blueprint('system', __name__, url_prefix='/api/system')


def run_pm2_command(command):
    """执行PM2命令并返回结果"""
    try:
        # 使用PowerShell执行PM2命令
        full_command = f'powershell -Command "pm2 {command} --silent"'
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': '命令执行超时'
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e)
        }


@system_bp.route('/services', methods=['GET'])
def get_services():
    """获取所有PM2服务状态"""
    try:
        # 执行pm2 jlist命令获取JSON格式的服务列表
        result = subprocess.run(
            'powershell -Command "pm2 jlist"',
            shell=True,
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
                'error': result.stderr
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@system_bp.route('/service/<service_name>/start', methods=['POST'])
def start_service(service_name):
    """启动指定服务"""
    result = run_pm2_command(f'start {service_name}')

    if result['success']:
        return jsonify({
            'success': True,
            'message': f'服务 {service_name} 启动成功'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500


@system_bp.route('/service/<service_name>/stop', methods=['POST'])
def stop_service(service_name):
    """停止指定服务"""
    result = run_pm2_command(f'stop {service_name}')

    if result['success']:
        return jsonify({
            'success': True,
            'message': f'服务 {service_name} 停止成功'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500


@system_bp.route('/service/<service_name>/restart', methods=['POST'])
def restart_service(service_name):
    """重启指定服务"""
    result = run_pm2_command(f'restart {service_name}')

    if result['success']:
        return jsonify({
            'success': True,
            'message': f'服务 {service_name} 重启成功'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500


@system_bp.route('/service/<service_name>/logs', methods=['GET'])
def get_service_logs(service_name):
    """获取服务日志"""
    lines = request.args.get('lines', 50, type=int)

    try:
        result = subprocess.run(
            f'powershell -Command "pm2 logs {service_name} --lines {lines} --nostream"',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        return jsonify({
            'success': True,
            'logs': result.stdout
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@system_bp.route('/restart-all', methods=['POST'])
def restart_all():
    """重启所有服务"""
    result = run_pm2_command('restart all')

    if result['success']:
        return jsonify({
            'success': True,
            'message': '所有服务重启成功'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500


@system_bp.route('/stop-all', methods=['POST'])
def stop_all():
    """停止所有服务"""
    result = run_pm2_command('stop all')

    if result['success']:
        return jsonify({
            'success': True,
            'message': '所有服务停止成功'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500
