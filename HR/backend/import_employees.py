#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
员工数据导入脚本
从 list.xlsx 导入员工数据到HR系统
"""
import sys
import os
import pandas as pd
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.employee import Employee
from app.models.base_data import Factory, Department, Position, Team


def clean_employment_status(status):
    """
    清洗雇佣状态数据
    - 临时工：合并"本厂临时工"和"中介临时工"
    - 实习生：合并所有实习生类型
    """
    if not status or pd.isna(status):
        return 'Active'

    status_str = str(status).strip()

    # 临时工合并
    if '临时工' in status_str:
        return '临时工'

    # 实习生合并
    if '实习生' in status_str:
        return '实习生'

    return status_str


def initialize_factories(app):
    """初始化工厂基础数据：深圳和东莞"""
    with app.app_context():
        print("初始化工厂数据...")

        # 检查是否已存在
        existing = Factory.query.all()
        if existing:
            print(f"工厂数据已存在 ({len(existing)} 个)，跳过初始化")
            return

        # 创建深圳工厂
        shenzhen = Factory(
            code='SZ',
            name='深圳工厂',
            city='深圳',
            address='广东省深圳市',
            is_active=True,
            sort_order=1
        )

        # 创建东莞工厂
        dongguan = Factory(
            code='DG',
            name='东莞工厂',
            city='东莞',
            address='广东省东莞市',
            is_active=True,
            sort_order=2
        )

        db.session.add(shenzhen)
        db.session.add(dongguan)
        db.session.commit()

        print(f"✓ 创建工厂数据: 深圳 (ID: {shenzhen.id}), 东莞 (ID: {dongguan.id})")
        return dongguan.id  # 返回东莞工厂ID


def clear_test_data(app):
    """清除测试数据"""
    with app.app_context():
        print("\n清除现有测试数据...")

        # 删除所有员工
        count = Employee.query.delete()
        db.session.commit()

        print(f"✓ 已删除 {count} 条员工记录")


def import_employees(app, excel_file):
    """从Excel导入员工数据"""
    with app.app_context():
        print(f"\n从 {excel_file} 导入员工数据...")

        # 读取Excel文件
        try:
            df = pd.read_excel(excel_file)
            print(f"✓ 读取到 {len(df)} 行数据")
            print(f"✓ 列名: {list(df.columns)}")
        except Exception as e:
            print(f"✗ 读取Excel文件失败: {e}")
            return

        # 获取东莞工厂ID
        dongguan = Factory.query.filter_by(code='DG').first()
        if not dongguan:
            print("✗ 找不到东莞工厂数据！")
            return

        print(f"✓ 使用工厂: {dongguan.name} (ID: {dongguan.id})")

        # 导入数据
        success_count = 0
        error_count = 0

        for index, row in df.iterrows():
            try:
                # 提取数据（根据实际Excel列名调整）
                emp_data = {
                    'empNo': str(row.get('工号', f'EMP{index+1:04d}')).strip(),
                    'name': str(row.get('姓名', '')).strip(),
                    'gender': str(row.get('性别', '')).strip() if pd.notna(row.get('性别')) else None,
                    'department': str(row.get('部门', '')).strip() if pd.notna(row.get('部门')) else None,
                    'title': str(row.get('职位', '')).strip() if pd.notna(row.get('职位')) else None,
                    'team': str(row.get('班组', '')).strip() if pd.notna(row.get('班组')) else None,
                    'employment_status': clean_employment_status(row.get('雇佣状态', 'Active')),
                    'factory_id': dongguan.id,  # 所有员工都属于东莞工厂
                }

                # 处理入职日期
                hire_date = row.get('入职日期')
                if pd.notna(hire_date):
                    if isinstance(hire_date, str):
                        try:
                            emp_data['hire_date'] = datetime.strptime(hire_date, '%Y-%m-%d').date()
                        except:
                            pass
                    elif hasattr(hire_date, 'date'):
                        emp_data['hire_date'] = hire_date.date()

                # 跳过空姓名的记录
                if not emp_data['name']:
                    continue

                # 创建员工记录
                employee = Employee(**emp_data)
                db.session.add(employee)
                success_count += 1

                if success_count % 10 == 0:
                    print(f"  已处理 {success_count} 条记录...")

            except Exception as e:
                error_count += 1
                print(f"✗ 第 {index+1} 行导入失败: {e}")
                continue

        # 提交到数据库
        try:
            db.session.commit()
            print(f"\n✓ 导入完成!")
            print(f"  成功: {success_count} 条")
            print(f"  失败: {error_count} 条")
            print(f"  工厂: {dongguan.name}")
        except Exception as e:
            db.session.rollback()
            print(f"✗ 提交数据库失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("HR系统 - 员工数据导入工具")
    print("=" * 60)

    # 创建Flask应用
    app = create_app()

    # Excel文件路径
    excel_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'list.xlsx')

    if not os.path.exists(excel_file):
        print(f"✗ 找不到Excel文件: {excel_file}")
        return

    print(f"\n使用Excel文件: {excel_file}")

    # 执行导入流程
    try:
        # 1. 初始化工厂数据
        initialize_factories(app)

        # 2. 清除测试数据
        clear_test_data(app)

        # 3. 导入新数据
        import_employees(app, excel_file)

        print("\n" + "=" * 60)
        print("导入完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 导入过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
