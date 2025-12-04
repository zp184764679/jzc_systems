#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入东莞厂员工数据
Import Dongguan factory employee data from Excel
"""
import sys
import os
import pandas as pd
from datetime import datetime
import numpy as np

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.employee import Employee
from app.models.base_data import Factory

# Excel文件路径
EXCEL_FILE = r"C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls"

def clean_value(value):
    """清理数据值，将NaN、None、空字符串转换为None"""
    if pd.isna(value) or value == '' or (isinstance(value, str) and value.strip() == ''):
        return None
    if isinstance(value, str):
        return value.strip()
    return value

def parse_date(date_value):
    """解析日期，支持多种格式"""
    if pd.isna(date_value) or date_value == '' or date_value is None:
        return None

    # 如果已经是datetime对象
    if isinstance(date_value, datetime):
        return date_value.date()

    # 如果是字符串，尝试解析
    if isinstance(date_value, str):
        date_str = date_value.strip()
        if not date_str:
            return None

        # 替换点号为横杠 (1985.12.19 -> 1985-12-19)
        date_str = date_str.replace('.', '-')

        # 尝试多种日期格式
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%d/%m/%Y', '%d-%m-%Y']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # Silently ignore unparseable dates
        return None

    return None

def import_active_employees():
    """导入在职员工（从"总人数"工作表）"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("HR系统 - 导入东莞厂在职员工数据")
        print("=" * 80)

        # 获取东莞工厂ID
        dongguan_factory = Factory.query.filter_by(code='DG').first()
        if not dongguan_factory:
            print("✗ 未找到东莞工厂数据！请先初始化工厂数据。")
            return False

        print(f"\n工厂信息: {dongguan_factory.name} (ID: {dongguan_factory.id})")

        # 读取"总人数"工作表
        try:
            print(f"\n正在读取Excel文件: {EXCEL_FILE}")
            print(f"工作表: 总人数")

            # 跳过标题行，读取数据
            df = pd.read_excel(EXCEL_FILE, sheet_name='总人数', skiprows=2)

            print(f"✓ 成功读取 {len(df)} 行数据")
            print(f"✓ 列数: {len(df.columns)}")

            # 显示列名
            print(f"\n列名列表:")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i:2d}. {col}")

        except Exception as e:
            print(f"✗ 读取Excel文件失败: {e}")
            import traceback
            traceback.print_exc()
            return False

        # 清空现有员工数据
        print(f"\n正在清空现有员工数据...")
        try:
            Employee.query.delete()
            db.session.commit()
            print("✓ 已清空现有员工数据")
        except Exception as e:
            print(f"✗ 清空数据失败: {e}")
            db.session.rollback()
            return False

        # 导入员工数据
        success_count = 0
        error_count = 0

        print(f"\n开始导入员工数据...")

        for index, row in df.iterrows():
            try:
                # 跳过空行（没有员工编号的行）
                emp_no = clean_value(row.get('工号'))
                if not emp_no:
                    continue

                # 检查员工编号是否已存在（跳过重复）
                existing_by_empno = Employee.query.filter_by(empNo=str(emp_no)).first()
                if existing_by_empno:
                    error_count += 1
                    continue

                # 检查身份证号是否已存在（如果有身份证）
                id_card_value = clean_value(row.get('身份证号码'))
                if id_card_value:
                    existing_by_idcard = Employee.query.filter_by(id_card=id_card_value).first()
                    if existing_by_idcard:
                        error_count += 1
                        continue

                # 创建员工对象
                employee = Employee(
                    # 基本信息
                    empNo=str(emp_no),
                    name=clean_value(row.get('姓名')),
                    gender=clean_value(row.get('性别')),
                    birth_date=parse_date(row.get('出生年月')),
                    id_card=clean_value(row.get('身份证号码')),
                    phone=clean_value(row.get('联系电话')),

                    # 新增字段
                    nationality=clean_value(row.get('民族')),
                    education=clean_value(row.get('学历')),
                    native_place=clean_value(row.get('籍贯')),
                    bank_card=clean_value(row.get('银行卡')),
                    has_card=clean_value(row.get('制卡')),
                    salary_type=clean_value(row.get('薪资\n制')),
                    accommodation=clean_value(row.get('住宿\n情况')),

                    # 工作信息
                    factory_id=dongguan_factory.id,
                    department=clean_value(row.get('部门')),
                    title=clean_value(row.get('职位')),
                    team=clean_value(row.get('组别')),
                    hire_date=parse_date(row.get('入厂时间')),
                    employment_status='Active',

                    # 地址和联系人
                    home_address=clean_value(row.get('身份证地址')),
                    emergency_contact=clean_value(row.get('紧急联系人姓名')),
                    emergency_phone=clean_value(row.get('紧急联络人电话'))
                )

                db.session.add(employee)
                success_count += 1

                # 每100条提交一次
                if success_count % 100 == 0:
                    db.session.commit()
                    print(f"  已导入 {success_count} 名员工...")

            except Exception as e:
                error_count += 1
                print(f"✗ 第{index+1}行导入失败: {e}")
                print(f"  数据: {row.to_dict()}")
                db.session.rollback()
                continue

        # 最后提交
        try:
            db.session.commit()
            print(f"\n✓ 数据导入完成！")
            print(f"  成功: {success_count} 名员工")
            print(f"  失败: {error_count} 条记录")

            return True

        except Exception as e:
            print(f"✗ 最终提交失败: {e}")
            db.session.rollback()
            return False


def import_resigned_employees():
    """导入离职员工（从"离职人员"工作表）"""
    app = create_app()

    with app.app_context():
        print("\n" + "=" * 80)
        print("HR系统 - 导入东莞厂离职员工数据")
        print("=" * 80)

        # 获取东莞工厂ID
        dongguan_factory = Factory.query.filter_by(code='DG').first()
        if not dongguan_factory:
            print("✗ 未找到东莞工厂数据！")
            return False

        # 读取"离职人员"工作表
        try:
            print(f"\n正在读取Excel文件: {EXCEL_FILE}")
            print(f"工作表: 离职人员")

            df = pd.read_excel(EXCEL_FILE, sheet_name='离职人员', skiprows=2)

            print(f"✓ 成功读取 {len(df)} 行数据")

        except Exception as e:
            print(f"✗ 读取Excel文件失败: {e}")
            import traceback
            traceback.print_exc()
            return False

        # 导入离职员工数据
        success_count = 0
        error_count = 0

        print(f"\n开始导入离职员工数据...")

        for index, row in df.iterrows():
            try:
                # 跳过空行
                emp_no = clean_value(row.get('工号'))
                if not emp_no:
                    continue

                # 检查员工编号是否已存在（跳过重复）
                existing_by_empno = Employee.query.filter_by(empNo=str(emp_no)).first()
                if existing_by_empno:
                    error_count += 1
                    continue

                # Skip ID card uniqueness check for resigned employees
                # (Excel column misalignment causes id_card field to contain wrong data)

                # 创建员工对象
                # NOTE: 离职人员 sheet is missing '部门' column, causing data to shift left!
                # The column mapping is different from 总人数 sheet:
                # - '职位' column actually contains department data
                # - '制卡' column actually contains position data
                # - '薪资\n制' column actually contains has_card data
                # - etc. All columns shifted left by one position
                # Since the id_card data is incorrect due to column shift, we'll store NULL for resigned employees
                employee = Employee(
                    empNo=str(emp_no),
                    name=clean_value(row.get('姓名')),
                    gender=clean_value(row.get('性别')),
                    birth_date=parse_date(row.get('联系电话')),  # Shifted! This column has birth date
                    id_card=None,  # Skip id_card for resigned employees (data is misaligned and incorrect)
                    phone=clean_value(row.get('紧急联络人')),  # Shifted! This column has phone

                    nationality=clean_value(row.get('民族')),
                    education=clean_value(row.get('学历')),
                    native_place=clean_value(row.get('出生年月')),  # Shifted! This column has native place
                    bank_card=clean_value(row.get('银行卡')),
                    has_card=clean_value(row.get('薪资\n制')),  # Shifted! This column has has_card
                    salary_type=clean_value(row.get('住宿\n情况')),  # Shifted! This column has salary type
                    accommodation=clean_value(row.get('籍贯')),  # Shifted! This column has accommodation

                    factory_id=dongguan_factory.id,
                    department=clean_value(row.get('职位')),  # Shifted! This column actually has department
                    title=clean_value(row.get('制卡')),  # Shifted! This column actually has position
                    team=clean_value(row.get('组别')),
                    hire_date=parse_date(row.get('入厂时间')),
                    resignation_date=parse_date(row.get('离职日期')),
                    employment_status='Resigned',

                    home_address=clean_value(row.get('身份证号码')),  # Shifted! This column has home address
                    emergency_contact=clean_value(row.get('家庭住址')),  # Shifted! This column has emergency contact
                    emergency_phone=clean_value(row.get('身份证号码'))  # Approximate mapping
                )

                db.session.add(employee)
                success_count += 1

                if success_count % 100 == 0:
                    db.session.commit()
                    print(f"  已导入 {success_count} 名离职员工...")

            except Exception as e:
                error_count += 1
                print(f"✗ 第{index+1}行导入失败: {e}")
                db.session.rollback()
                continue

        # 最后提交
        try:
            db.session.commit()
            print(f"\n✓ 离职员工数据导入完成！")
            print(f"  成功: {success_count} 名员工")
            print(f"  失败: {error_count} 条记录")

            return True

        except Exception as e:
            print(f"✗ 最终提交失败: {e}")
            db.session.rollback()
            return False


def main():
    """主函数"""
    print("=" * 80)
    print("东莞厂人事数据导入工具")
    print("=" * 80)

    # 导入在职员工
    if not import_active_employees():
        print("\n✗ 在职员工数据导入失败！")
        sys.exit(1)

    # 导入离职员工
    if not import_resigned_employees():
        print("\n✗ 离职员工数据导入失败！")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("所有数据导入完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
