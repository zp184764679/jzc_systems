"""测试API响应"""
import sys
sys.path.insert(0, r'C:\Users\Admin\Desktop\HR\backend')

from app import create_app, db
from app.models.employee import Employee
from sqlalchemy import or_

app = create_app()

with app.app_context():
    # 模拟API的查询逻辑
    query = Employee.query

    # 更新后的per_page是10000
    per_page = 10000
    page = 1

    # 按创建时间排序
    query = query.order_by(Employee.created_at.desc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    print(f"API返回总数 (pagination.total): {pagination.total}")
    print(f"当前页数据量 (pagination.items): {len(pagination.items)}")
    print(f"总页数 (pagination.pages): {pagination.pages}")

    # 转换为dict
    data = [emp.to_dict() for emp in pagination.items]
    print(f"\n转换后数据量: {len(data)}")

    # 统计各状态
    active_count = sum(1 for e in data if e['employment_status'] == 'Active' and not e['is_blacklisted'])
    resigned_count = sum(1 for e in data if e['employment_status'] == 'Resigned')

    print(f"\nActive且非黑名单: {active_count}")
    print(f"Resigned: {resigned_count}")

    # 检查前几个Active员工
    print("\n前5个Active员工:")
    active_emps = [e for e in data if e['employment_status'] == 'Active']
    for emp in active_emps[:5]:
        print(f"  {emp['empNo']}: {emp['name']} - {emp['employment_status']} - blacklisted: {emp['is_blacklisted']}")

    print(f"\n总Active员工数: {len(active_emps)}")
