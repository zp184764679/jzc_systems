# -*- coding: utf-8 -*-
"""
添加付款周期字段到RFQ和SupplierQuote表
Add payment_terms field to RFQs and SupplierQuotes
"""
from app import app
from extensions import db
from sqlalchemy import text

def migrate_payment_terms():
    """添加付款周期字段"""
    with app.app_context():
        try:
            print("=" * 60)
            print("开始添加付款周期字段...")
            print("=" * 60)

            # RFQ表添加付款周期字段（默认90天）
            rfq_fields = [
                "ALTER TABLE rfqs ADD COLUMN payment_terms INT DEFAULT 90 COMMENT '付款周期(天)'",
            ]

            # SupplierQuote表添加付款周期字段
            quote_fields = [
                "ALTER TABLE supplier_quotes ADD COLUMN payment_terms INT DEFAULT 90 COMMENT '供应商报价付款周期(天)'",
            ]

            all_fields = rfq_fields + quote_fields

            print(f"\n准备添加 {len(all_fields)} 个字段...\n")

            for i, sql in enumerate(all_fields, 1):
                try:
                    db.session.execute(text(sql))
                    table_name = sql.split("ALTER TABLE ")[1].split(" ")[0]
                    print(f"  [{i}/{len(all_fields)}] ✓ 表 {table_name} 添加 payment_terms 字段成功")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        table_name = sql.split("ALTER TABLE ")[1].split(" ")[0]
                        print(f"  [{i}/{len(all_fields)}] ℹ️  表 {table_name} 的 payment_terms 字段已存在，跳过")
                    else:
                        print(f"  [{i}/{len(all_fields)}] ⚠️  添加失败: {str(e)}")

            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ 迁移完成！付款周期字段已添加")
            print("=" * 60)

            # 显示表结构
            print("\n当前 rfqs 表结构（payment_terms 相关）：")
            result = db.session.execute(text("DESCRIBE rfqs"))
            print(f"\n{'字段名':<30} {'类型':<30} {'默认值':<20}")
            print("-" * 80)
            for row in result:
                if 'payment' in row[0].lower():
                    default_val = row[4] if len(row) > 4 else ''
                    print(f"{row[0]:<30} {row[1]:<30} {default_val:<20}")

            print("\n当前 supplier_quotes 表结构（payment_terms 相关）：")
            result = db.session.execute(text("DESCRIBE supplier_quotes"))
            print(f"\n{'字段名':<30} {'类型':<30} {'默认值':<20}")
            print("-" * 80)
            for row in result:
                if 'payment' in row[0].lower():
                    default_val = row[4] if len(row) > 4 else ''
                    print(f"{row[0]:<30} {row[1]:<30} {default_val:<20}")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_payment_terms()
