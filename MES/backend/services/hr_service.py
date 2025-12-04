# HR人力资源系统集成服务
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_hr_base_url():
    return os.getenv('HR_API_BASE_URL', '')


def get_employees(search="", department="", status="Active", page=1, per_page=100):
    """获取员工列表"""
    try:
        response = requests.get(
            f"{get_hr_base_url()}/api/employees",
            params={
                "search": search,
                "department": department,
                "employment_status": status,
                "page": page,
                "per_page": per_page
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            'success': False,
            'error': f'HR系统连接失败: {str(e)}',
            'data': []
        }


def get_employee(employee_id):
    """获取单个员工详情"""
    try:
        response = requests.get(
            f"{get_hr_base_url()}/api/employees/{employee_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'success': False, 'error': f'HR系统连接失败: {str(e)}'}


def get_operators(department=""):
    """获取操作员/车间员工列表（用于MES报工选择）"""
    try:
        response = requests.get(
            f"{get_hr_base_url()}/api/employees",
            params={
                "department": department,
                "employment_status": "Active",
                "per_page": 200
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        if result.get('success'):
            # 简化员工数据，只返回MES需要的字段
            operators = []
            for emp in result.get('data', []):
                operators.append({
                    'id': emp.get('id'),
                    'empNo': emp.get('empNo'),
                    'name': emp.get('name'),
                    'department': emp.get('department'),
                    'title': emp.get('title'),
                    'team': emp.get('team')
                })
            return {
                'success': True,
                'data': operators,
                'total': len(operators)
            }
        return result
    except Exception as e:
        return {
            'success': False,
            'error': f'HR系统连接失败: {str(e)}',
            'data': []
        }


def get_employee_stats():
    """获取员工统计数据"""
    try:
        response = requests.get(
            f"{get_hr_base_url()}/api/employees/stats",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'success': False, 'error': f'HR系统连接失败: {str(e)}'}


def check_hr_health():
    """检查HR系统健康状态"""
    try:
        response = requests.get(f"{get_hr_base_url()}/api/employees/stats", timeout=5)
        return response.status_code == 200
    except:
        return False
