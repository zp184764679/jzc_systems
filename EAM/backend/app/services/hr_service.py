# HR人力资源系统集成服务 - EAM使用
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_hr_base_url():
    return os.getenv('HR_API_BASE_URL', 'http://localhost:8003')


def get_maintenance_staff(search="", page=1, per_page=100):
    """获取维护人员列表"""
    try:
        response = requests.get(
            f"{get_hr_base_url()}/api/employees",
            params={
                "search": search,
                "employment_status": "Active",
                "page": page,
                "per_page": per_page
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        if result.get('success'):
            staff = []
            for emp in result.get('data', []):
                staff.append({
                    'id': emp.get('id'),
                    'empNo': emp.get('empNo'),
                    'name': emp.get('name'),
                    'department': emp.get('department'),
                    'title': emp.get('title'),
                    'phone': emp.get('phone'),
                    'email': emp.get('email')
                })
            return {
                'success': True,
                'data': staff,
                'total': len(staff)
            }
        return result
    except Exception as e:
        return {
            'success': False,
            'error': f'HR系统连接失败: {str(e)}',
            'data': []
        }


def get_employee(employee_id):
    """获取员工详情"""
    try:
        response = requests.get(
            f"{get_hr_base_url()}/api/employees/{employee_id}",
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
