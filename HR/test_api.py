"""测试API返回数据"""
import requests

# 先登录获取token
login_resp = requests.post('http://localhost:8003/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
print("登录响应:", login_resp.status_code)
if login_resp.status_code == 200:
    token = login_resp.json().get('token')
    print("Token:", token[:50] + "..." if token else "无")

    # 获取员工列表
    headers = {'Authorization': f'Bearer {token}'}
    emp_resp = requests.get('http://localhost:8003/api/employees', headers=headers)
    print("\n员工API响应:", emp_resp.status_code)

    if emp_resp.status_code == 200:
        data = emp_resp.json()
        employees = data.get('data', [])
        pagination = data.get('pagination', {})

        print(f"返回员工数: {len(employees)}")
        print(f"分页信息: {pagination}")

        # 统计各状态
        active = [e for e in employees if e.get('employment_status') == 'Active' and not e.get('is_blacklisted')]
        resigned = [e for e in employees if e.get('employment_status') == 'Resigned']

        print(f"\nActive员工数: {len(active)}")
        print(f"Resigned员工数: {len(resigned)}")
    else:
        print("错误:", emp_resp.text)
else:
    print("登录失败:", login_resp.text)
