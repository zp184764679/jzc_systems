#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入基础数据：部门、职位、团队
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.base_data import Department, Position, Team
from app.models.employee import Employee

def import_base_data():
    """导入基础数据"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("导入基础数据")
        print("=" * 80)

        # 1. 导入部门数据
        print("\n【导入部门数据】")
        print("-" * 80)

        departments_data = [
            {'code': 'XC', 'name': '铣床', 'sort_order': 1},
            {'code': 'MC', 'name': '磨床', 'sort_order': 2},
            {'code': 'SK', 'name': '数控', 'sort_order': 3},
            {'code': 'ZXJ', 'name': '走心机', 'sort_order': 4},
            {'code': 'JGZX', 'name': '加工中心', 'sort_order': 5},
            {'code': 'PZB', 'name': '品质部', 'sort_order': 6},
            {'code': 'XZB', 'name': '行政部', 'sort_order': 7},
            {'code': 'CCB', 'name': '仓储部', 'sort_order': 8},
            {'code': 'PMC', 'name': 'PMC部', 'sort_order': 9},
            {'code': 'BZB', 'name': '包装部', 'sort_order': 10},
            {'code': 'HQB', 'name': '后勤部', 'sort_order': 11},
            {'code': 'GCB', 'name': '工程部', 'sort_order': 12},
            {'code': 'DD', 'name': '待定', 'sort_order': 99},
        ]

        dept_count = 0
        for dept_data in departments_data:
            # 检查是否已存在
            existing = Department.query.filter_by(code=dept_data['code']).first()
            if not existing:
                dept = Department(
                    code=dept_data['code'],
                    name=dept_data['name'],
                    sort_order=dept_data['sort_order'],
                    is_active=True
                )
                db.session.add(dept)
                dept_count += 1
                print(f"  ✓ 添加部门: {dept_data['code']} - {dept_data['name']}")
            else:
                print(f"  - 部门已存在: {dept_data['code']} - {dept_data['name']}")

        print(f"\n新增部门数量: {dept_count}")

        # 2. 导入职位数据
        print("\n【导入职位数据】")
        print("-" * 80)

        positions_data = [
            {'code': 'CZY', 'name': '操作员', 'category': '生产', 'level': 3, 'sort_order': 1},
            {'code': 'JSY', 'name': '技术员', 'category': '技术', 'level': 4, 'sort_order': 2},
            {'code': 'ZZ', 'name': '组长', 'category': '管理', 'level': 5, 'sort_order': 3},
            {'code': 'XT', 'name': '学徒', 'category': '生产', 'level': 1, 'sort_order': 4},
            {'code': 'BZRY', 'name': '包装人员', 'category': '生产', 'level': 3, 'sort_order': 5},
            {'code': 'QJRY', 'name': '全检人员', 'category': '品质', 'level': 3, 'sort_order': 6},
            {'code': 'KGY', 'name': '库管员', 'category': '仓储', 'level': 3, 'sort_order': 7},
            {'code': 'SJ', 'name': '司机', 'category': '后勤', 'level': 3, 'sort_order': 8},
            {'code': 'WXG', 'name': '维修工', 'category': '技术', 'level': 4, 'sort_order': 9},
            {'code': 'BSRY', 'name': '保安人员', 'category': '后勤', 'level': 2, 'sort_order': 10},
            {'code': 'QJY', 'name': '清洁员', 'category': '后勤', 'level': 2, 'sort_order': 11},
        ]

        pos_count = 0
        for pos_data in positions_data:
            existing = Position.query.filter_by(code=pos_data['code']).first()
            if not existing:
                pos = Position(
                    code=pos_data['code'],
                    name=pos_data['name'],
                    category=pos_data['category'],
                    level=pos_data['level'],
                    sort_order=pos_data['sort_order'],
                    is_active=True
                )
                db.session.add(pos)
                pos_count += 1
                print(f"  ✓ 添加职位: {pos_data['code']} - {pos_data['name']} ({pos_data['category']})")
            else:
                print(f"  - 职位已存在: {pos_data['code']} - {pos_data['name']}")

        print(f"\n新增职位数量: {pos_count}")

        # 3. 导入团队数据
        print("\n【导入团队数据】")
        print("-" * 80)

        teams_data = [
            {'code': 'BB', 'name': '白班', 'sort_order': 1},
            {'code': 'YB', 'name': '夜班', 'sort_order': 2},
            {'code': 'ZXJZ', 'name': '走心机组', 'sort_order': 3},
            {'code': 'QJZ', 'name': '全检组', 'sort_order': 4},
        ]

        team_count = 0
        for team_data in teams_data:
            existing = Team.query.filter_by(code=team_data['code']).first()
            if not existing:
                team = Team(
                    code=team_data['code'],
                    name=team_data['name'],
                    sort_order=team_data['sort_order'],
                    is_active=True
                )
                db.session.add(team)
                team_count += 1
                print(f"  ✓ 添加团队: {team_data['code']} - {team_data['name']}")
            else:
                print(f"  - 团队已存在: {team_data['code']} - {team_data['name']}")

        print(f"\n新增团队数量: {team_count}")

        # 提交所有更改
        try:
            db.session.commit()
            print("\n" + "=" * 80)
            print("✓ 基础数据导入完成！")
            print(f"  部门: {dept_count} 个")
            print(f"  职位: {pos_count} 个")
            print(f"  团队: {team_count} 个")
            print("=" * 80)

            # 显示统计信息
            print("\n【数据库统计】")
            print("-" * 80)
            print(f"  总部门数: {Department.query.count()}")
            print(f"  总职位数: {Position.query.count()}")
            print(f"  总团队数: {Team.query.count()}")

        except Exception as e:
            print(f"\n✗ 提交失败: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

        return True


if __name__ == '__main__':
    import_base_data()
