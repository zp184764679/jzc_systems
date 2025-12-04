# -*- coding: utf-8 -*-
"""
修复RFQ报价去重问题 - 每个物料单独创建报价

问题描述：
- 当前系统按品类分组，导致3个不同的镗刀被合并成1个报价
- 需要改为每个物料项单独创建报价

解决方案：
- 添加 rfq_item_id 字段关联到具体物料项
- 删除旧的 supplier_id+rfq_id+category 唯一索引
- 添加新的 supplier_id+rfq_id+rfq_item_id 唯一索引
"""
import os
import sys

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app import app
from extensions import db
from sqlalchemy import text

def fix_quote_deduplication():
    with app.app_context():
        try:
            print("=" * 60)
            print("开始修复RFQ报价去重问题...")
            print("=" * 60)

            # 1. 添加 rfq_item_id 字段
            try:
                db.session.execute(text("""
                    ALTER TABLE supplier_quotes
                    ADD COLUMN rfq_item_id BIGINT UNSIGNED NULL
                    COMMENT '关联的RFQ物料项ID，每个物料单独报价'
                    AFTER rfq_id
                """))
                db.session.commit()
                print("✅ 添加 rfq_item_id 字段成功")
            except Exception as e:
                db.session.rollback()
                if "Duplicate column name" in str(e):
                    print("ℹ️  rfq_item_id 字段已存在")
                else:
                    print(f"⚠️  添加 rfq_item_id 字段失败: {str(e)}")
                    raise

            # 2. 添加外键约束
            try:
                db.session.execute(text("""
                    ALTER TABLE supplier_quotes
                    ADD CONSTRAINT fk_supplier_quotes_rfq_item
                    FOREIGN KEY (rfq_item_id) REFERENCES rfq_items(id)
                    ON DELETE CASCADE
                """))
                db.session.commit()
                print("✅ 添加外键约束成功")
            except Exception as e:
                db.session.rollback()
                if "Duplicate foreign key" in str(e) or "already exists" in str(e):
                    print("ℹ️  外键约束已存在")
                else:
                    print(f"⚠️  添加外键约束失败: {str(e)}")

            # 3. 添加 rfq_item_id 索引
            try:
                db.session.execute(text("""
                    CREATE INDEX idx_sq_rfq_item_id
                    ON supplier_quotes(rfq_item_id)
                """))
                db.session.commit()
                print("✅ 添加 rfq_item_id 索引成功")
            except Exception as e:
                db.session.rollback()
                if "Duplicate key name" in str(e):
                    print("ℹ️  rfq_item_id 索引已存在")
                else:
                    print(f"⚠️  添加索引失败: {str(e)}")

            # 4. 删除旧的唯一索引 (supplier_id + rfq_id + category)
            try:
                db.session.execute(text("""
                    DROP INDEX ix_supplier_quotes_supplier_rfq_category
                    ON supplier_quotes
                """))
                db.session.commit()
                print("✅ 删除旧的 category 唯一索引成功")
            except Exception as e:
                db.session.rollback()
                if "doesn't exist" in str(e) or "Can't DROP" in str(e):
                    print("ℹ️  旧索引不存在，跳过删除")
                else:
                    print(f"⚠️  删除旧索引失败: {str(e)}")

            # 5. 创建新的唯一索引 (supplier_id + rfq_id + rfq_item_id)
            try:
                db.session.execute(text("""
                    CREATE UNIQUE INDEX ix_supplier_quotes_supplier_rfq_item_id
                    ON supplier_quotes(supplier_id, rfq_id, rfq_item_id)
                """))
                db.session.commit()
                print("✅ 添加新的物料项唯一索引成功")
            except Exception as e:
                db.session.rollback()
                if "Duplicate key name" in str(e):
                    print("ℹ️  新唯一索引已存在")
                else:
                    print(f"⚠️  添加新索引失败: {str(e)}")

            print("\n" + "=" * 60)
            print("🎉 RFQ报价去重问题修复完成！")
            print("=" * 60)
            print("\n现在每个供应商可以对每个物料项单独报价，不再合并！")
            print("示例：3个不同的镗刀 → 3个独立的报价\n")

        except Exception as e:
            print(f"\n❌ 修复失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    fix_quote_deduplication()
