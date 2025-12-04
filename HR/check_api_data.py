"""直接测试API返回数据 - 绕过认证查看员工数"""
import sys
sys.path.insert(0, r'C:\Users\Admin\Desktop\HR\backend')

from app import create_app, db
from app.models.employee import Employee

app = create_app()

with app.app_context():
    # 直接查询数据库
    total = Employee.query.count()
    active = Employee.query.filter_by(employment_status='Active').count()
    active_non_blacklist = Employee.query.filter_by(
        employment_status='Active',
        is_blacklisted=False
    ).count()
    resigned = Employee.query.filter_by(employment_status='Resigned').count()
    blacklisted = Employee.query.filter_by(is_blacklisted=True).count()

    print(f"总员工数: {total}")
    print(f"Active状态员工: {active}")
    print(f"Active且非黑名单: {active_non_blacklist}")
    print(f"Resigned状态: {resigned}")
    print(f"黑名单员工: {blacklisted}")

    # 检查是否有其他状态
    statuses = db.session.query(
        Employee.employment_status,
        db.func.count(Employee.id)
    ).group_by(Employee.employment_status).all()

    print(f"\n各状态分布:")
    for status, count in statuses:
        print(f"  {status or 'NULL'}: {count}")

    # 检查is_blacklisted分布
    print(f"\n黑名单分布:")
    blacklist_dist = db.session.query(
        Employee.is_blacklisted,
        db.func.count(Employee.id)
    ).group_by(Employee.is_blacklisted).all()
    for bl, count in blacklist_dist:
        print(f"  is_blacklisted={bl}: {count}")
