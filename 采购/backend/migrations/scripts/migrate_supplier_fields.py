# -*- coding: utf-8 -*-
"""
供应商表字段迁移脚本
添加基本信息、联系方式、业务信息、财务信息等扩展字段
Migrate supplier fields - add extended fields for basic info, contact, business, financial
"""
from app import app
from extensions import db
from sqlalchemy import text

def migrate_supplier_fields():
    """添加供应商表的扩展字段"""
    with app.app_context():
        try:
            print("=" * 60)
            print("开始迁移 suppliers 表，添加扩展字段...")
            print("=" * 60)

            # 基本信息字段
            basic_info_fields = [
                "ALTER TABLE suppliers ADD COLUMN credit_code VARCHAR(50) NULL COMMENT '信用代码'",
                "ALTER TABLE suppliers ADD COLUMN tax_number VARCHAR(50) NULL COMMENT '税号'",
                "ALTER TABLE suppliers ADD COLUMN legal_representative VARCHAR(100) NULL COMMENT '法定代表人'",
                "ALTER TABLE suppliers ADD COLUMN registered_capital VARCHAR(50) NULL COMMENT '注册资本（万元）'",
                "ALTER TABLE suppliers ADD COLUMN registered_address VARCHAR(300) NULL COMMENT '注册地址'",
                "ALTER TABLE suppliers ADD COLUMN established_date VARCHAR(50) NULL COMMENT '成立日期'",
                "ALTER TABLE suppliers ADD COLUMN company_type VARCHAR(100) NULL COMMENT '企业类型'",
                "ALTER TABLE suppliers ADD COLUMN business_status VARCHAR(50) NULL COMMENT '经营状态'",
            ]

            # 联系方式字段
            contact_fields = [
                "ALTER TABLE suppliers ADD COLUMN company_phone VARCHAR(30) NULL COMMENT '公司电话'",
                "ALTER TABLE suppliers ADD COLUMN fax VARCHAR(30) NULL COMMENT '传真'",
                "ALTER TABLE suppliers ADD COLUMN website VARCHAR(200) NULL COMMENT '公司网站'",
                "ALTER TABLE suppliers ADD COLUMN office_address VARCHAR(300) NULL COMMENT '办公地址'",
                "ALTER TABLE suppliers ADD COLUMN postal_code VARCHAR(20) NULL COMMENT '邮政编码'",
            ]

            # 业务信息字段
            business_fields = [
                "ALTER TABLE suppliers ADD COLUMN company_description TEXT NULL COMMENT '公司简介'",
                "ALTER TABLE suppliers ADD COLUMN description TEXT NULL COMMENT '描述'",
                "ALTER TABLE suppliers ADD COLUMN main_products VARCHAR(500) NULL COMMENT '主营产品'",
                "ALTER TABLE suppliers ADD COLUMN annual_revenue VARCHAR(50) NULL COMMENT '年营业额（万元）'",
                "ALTER TABLE suppliers ADD COLUMN employee_count VARCHAR(50) NULL COMMENT '员工人数'",
                "ALTER TABLE suppliers ADD COLUMN factory_area VARCHAR(50) NULL COMMENT '工厂面积（平方米）'",
                "ALTER TABLE suppliers ADD COLUMN production_capacity VARCHAR(300) NULL COMMENT '生产能力'",
                "ALTER TABLE suppliers ADD COLUMN quality_certifications VARCHAR(500) NULL COMMENT '质量认证'",
            ]

            # 财务信息字段
            financial_fields = [
                "ALTER TABLE suppliers ADD COLUMN bank_name VARCHAR(200) NULL COMMENT '开户银行'",
                "ALTER TABLE suppliers ADD COLUMN bank_account VARCHAR(100) NULL COMMENT '银行账号'",
                "ALTER TABLE suppliers ADD COLUMN bank_branch VARCHAR(200) NULL COMMENT '开户行地址'",
                "ALTER TABLE suppliers ADD COLUMN swift_code VARCHAR(50) NULL COMMENT 'SWIFT代码'",
                "ALTER TABLE suppliers ADD COLUMN payment_terms VARCHAR(200) NULL COMMENT '付款条件'",
                "ALTER TABLE suppliers ADD COLUMN credit_rating VARCHAR(50) NULL COMMENT '信用等级'",
                "ALTER TABLE suppliers ADD COLUMN tax_registration_number VARCHAR(50) NULL COMMENT '税务登记号'",
                "ALTER TABLE suppliers ADD COLUMN invoice_type VARCHAR(50) NULL COMMENT '开票类型'",
            ]

            # 评分字段
            rating_fields = [
                "ALTER TABLE suppliers ADD COLUMN rating FLOAT NULL DEFAULT 0.0 COMMENT '综合评分'",
                "ALTER TABLE suppliers ADD COLUMN rating_updated_at DATETIME NULL COMMENT '评分更新时间'",
            ]

            # 合并所有字段
            all_fields = (
                basic_info_fields +
                contact_fields +
                business_fields +
                financial_fields +
                rating_fields
            )

            # 执行迁移
            print(f"\n准备添加 {len(all_fields)} 个字段...")

            for i, sql in enumerate(all_fields, 1):
                try:
                    db.session.execute(text(sql))
                    field_name = sql.split("ADD COLUMN ")[1].split(" ")[0]
                    print(f"  [{i}/{len(all_fields)}] ✓ 字段 {field_name} 添加成功")
                except Exception as e:
                    field_name = sql.split("ADD COLUMN ")[1].split(" ")[0]
                    if "Duplicate column name" in str(e):
                        print(f"  [{i}/{len(all_fields)}] ℹ️  字段 {field_name} 已存在，跳过")
                    else:
                        print(f"  [{i}/{len(all_fields)}] ⚠️  字段 {field_name} 添加失败: {str(e)}")

            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ 迁移完成！所有扩展字段已添加到 suppliers 表")
            print("=" * 60)

            # 显示表结构
            print("\n当前 suppliers 表结构：")
            result = db.session.execute(text("DESCRIBE suppliers"))
            print(f"\n{'字段名':<30} {'类型':<30} {'允许NULL':<10} {'键':<10}")
            print("-" * 80)
            for row in result:
                print(f"{row[0]:<30} {row[1]:<30} {row[2]:<10} {row[3]:<10}")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_supplier_fields()
