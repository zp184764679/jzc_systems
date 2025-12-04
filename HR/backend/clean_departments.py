#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清洗和归类部门数据
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.employee import Employee

# 部门归类映射规则
DEPARTMENT_MAPPING = {
    # 数控
    '数控': [
        '数控', '数控学徒', '数控技术员', '数控临时工', '数控操作员', '数控操作工',
        '数控学徒工', '数控小师傅', '数控操作员实习生', '三楼数控', 'NC操作工', 'NC 杂工',
        'CNC', 'CNC技术员', 'CNC临时工', 'CNC操作员', 'CNC学徒',
    ],

    # 铣床
    '铣床': [
        '铣床', '铣床操作员', '铣床临时工', '铣床技术员', '铣床？', '暑期铣床操作员',
    ],

    # 磨床
    '磨床': [
        '磨床', '磨床操作员', '磨床临时工', '磨床技术员', '磨床普工', '磨床操作工',
        '磨床通磨技术员', '磨床学徒', '通磨技术员', '无心磨技术员', '无芯磨技术员',
        '台阶磨技术员', '定位磨技术员',
    ],

    # 走心机
    '走心机': [
        '走芯机', '走芯机技术员', '走芯机学徒', '走芯机操作员', '走芯机普工',
        '走芯机临时工', '走芯机学徒工', '走心机操作员', '走心机技术员', '走心机技术',
    ],

    # 加工中心
    '加工中心': [
        '加工中心', '加工中心技术员', '加工中心操作员', '加工中心学徒',
        '加工中心临时工', '加工中心调机员', '加工中心师傅',
    ],

    # 生产普工
    '生产普工': [
        '操作员', '操作工', '普工', '临时工', '零时工', '作业员',
        '技术员', '小师傅', '杂工', '生产主管', '7.18离职生产主管', '生产文员',
    ],

    # 二次加工部
    '二次加工部': [
        '二次加工操作员', '二次加工普工', '二次加工临时工', '二次加工技术员',
        '二次加工主管', '二次加工磨床操作员', '二次加工磨床普工', '二次加工磨床学徒',
        '二次加工铣床操作员', '二次加工震动磨', '二次加工振动磨',
    ],

    # 品质部
    '品质部': [
        '品质部', 'QC', 'IPQC', 'OQC', 'QC径跳',
        '品质临时工', '品质操作员', '品质部包装', '品质部包装员', '品质包装', '品质包装员',
        '品质部全检', '品质部巡检', '品质部仓管', '品质仓管', '品质仓管员',
        '品质部QC', '品质部临时工', '品质部径跳员', '品质径跳员', '品质径跳测试员',
        '品质组长', '品检组长', '品质经理', '品质主管', '品质工程师', '品质IPQC',
        '巡检', '全检组', '全检外观', '外观全检', '径跳测试员', '计量员', '计量临时工',
        '计量员临时工', 'IPQC组长', '选别区', '制程', '制程检验',
    ],

    # PMC部
    'PMC部': [
        'PMC', '生管', '生管组', '生管临时工', '生产计划员', '计划员',
    ],

    # 包装部
    '包装部': [
        '包装', '包装员', '包装临时工', '包装部临时工', '包装部物料员',
    ],

    # 仓储部
    '仓储部': [
        '仓库', '仓管', '仓管员', '原材料仓管', '原材料仓管员', '成品仓仓管',
    ],

    # 工程部
    '工程部': [
        '工程部', '工程师助理', '绘图员',
    ],

    # 行政部
    '行政部': [
        '行政部', '行政部综合文员', '综合文员', '文员', '人事', '总务', '总务文员',
        '副总', '肖忠虎', '营业', '业务跟单',
    ],

    # 后勤部
    '后勤部': [
        '厨师', '后勤厨师', '帮厨', '保洁',
    ],
}

def clean_departments():
    """清洗部门数据"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("部门数据清洗")
        print("=" * 80)

        # 创建反向映射
        reverse_mapping = {}
        for dept, keywords in DEPARTMENT_MAPPING.items():
            for keyword in keywords:
                reverse_mapping[keyword] = dept

        # 统计清洗前的数据
        before_count = db.session.query(Employee.department).distinct().count()
        print(f"\n清洗前: {before_count} 个不同的部门名称")

        # 清洗数据
        updated_count = 0
        unmapped_depts = set()

        for employee in Employee.query.all():
            if employee.department:
                old_dept = employee.department
                new_dept = reverse_mapping.get(old_dept)

                if new_dept:
                    if old_dept != new_dept:
                        employee.department = new_dept
                        updated_count += 1
                else:
                    unmapped_depts.add(old_dept)

        # 提交更改
        db.session.commit()

        # 统计清洗后的数据
        after_count = db.session.query(Employee.department).distinct().count()
        print(f"清洗后: {after_count} 个不同的部门名称")
        print(f"更新了: {updated_count} 条员工记录")

        if unmapped_depts:
            print(f"\n未映射的部门名称 ({len(unmapped_depts)} 个):")
            for dept in sorted(unmapped_depts):
                count = Employee.query.filter_by(department=dept).count()
                print(f"  - {dept}: {count} 人")

        # 显示清洗后的部门统计
        print("\n清洗后的部门统计:")
        print("-" * 80)
        dept_counts = db.session.query(
            Employee.department,
            db.func.count(Employee.id)
        ).filter(
            Employee.department.isnot(None)
        ).group_by(
            Employee.department
        ).order_by(
            db.func.count(Employee.id).desc()
        ).all()

        for dept, count in dept_counts:
            print(f"{dept:<40s} {count:>8d}")

        print("\n✓ 部门数据清洗完成！")

if __name__ == '__main__':
    clean_departments()
