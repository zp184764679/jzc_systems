# -*- coding: utf-8 -*-
"""
更新数据库表结构 - 添加发票和收货回执相关字段
"""
from app import app
from extensions import db
from sqlalchemy import text

def update_schema():
    with app.app_context():
        try:
            # 添加invoices表的po_id字段
            try:
                db.session.execute(text("""
                    ALTER TABLE invoices
                    ADD COLUMN po_id BIGINT UNSIGNED NOT NULL AFTER supplier_id
                """))
                db.session.execute(text("""
                    ALTER TABLE invoices
                    ADD CONSTRAINT fk_invoices_po
                    FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE
                """))
                db.session.execute(text("""
                    CREATE INDEX idx_invoices_po_id ON invoices(po_id)
                """))
                db.session.commit()
                print("✅ invoices表po_id字段添加成功")
            except Exception as e:
                db.session.rollback()
                if "Duplicate column name" in str(e) or "Column already exists" in str(e):
                    print("ℹ️  invoices.po_id字段已存在")
                else:
                    print(f"⚠️  invoices.po_id: {str(e)}")

            # 添加purchase_orders表的发票相关字段
            try:
                db.session.execute(text("""
                    ALTER TABLE purchase_orders
                    ADD COLUMN invoice_due_date DATETIME NULL AFTER status
                """))
                db.session.commit()
                print("✅ purchase_orders表invoice_due_date字段添加成功")
            except Exception as e:
                db.session.rollback()
                if "Duplicate column name" in str(e):
                    print("ℹ️  purchase_orders.invoice_due_date字段已存在")
                else:
                    print(f"⚠️  purchase_orders.invoice_due_date: {str(e)}")

            try:
                db.session.execute(text("""
                    ALTER TABLE purchase_orders
                    ADD COLUMN invoice_uploaded TINYINT(1) NOT NULL DEFAULT 0 AFTER invoice_due_date
                """))
                db.session.commit()
                print("✅ purchase_orders表invoice_uploaded字段添加成功")
            except Exception as e:
                db.session.rollback()
                if "Duplicate column name" in str(e):
                    print("ℹ️  purchase_orders.invoice_uploaded字段已存在")
                else:
                    print(f"⚠️  purchase_orders.invoice_uploaded: {str(e)}")

            # 创建receipts表
            try:
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS receipts (
                        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                        po_id BIGINT UNSIGNED NOT NULL,
                        receiver_id BIGINT UNSIGNED NULL,
                        receipt_number VARCHAR(100) NOT NULL UNIQUE,
                        received_date DATETIME NOT NULL,
                        quality_status VARCHAR(20) NOT NULL DEFAULT 'qualified',
                        quantity_received INT NULL,
                        notes TEXT NULL,
                        photos TEXT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_by BIGINT UNSIGNED NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
                        FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE SET NULL,
                        FOREIGN KEY (created_by) REFERENCES users(id),
                        INDEX idx_receipts_po_id (po_id),
                        INDEX idx_receipts_receiver_id (receiver_id),
                        INDEX idx_receipts_status (status),
                        INDEX idx_receipts_received_date (received_date)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                db.session.commit()
                print("✅ receipts表创建成功")
            except Exception as e:
                db.session.rollback()
                if "Table 'receipts' already exists" in str(e):
                    print("ℹ️  receipts表已存在")
                else:
                    print(f"⚠️  receipts表: {str(e)}")

            print("\n" + "=" * 60)
            print("🎉 数据库表结构更新完成！")
            print("=" * 60)

        except Exception as e:
            print(f"❌ 更新失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("开始更新数据库表结构...")
    print("=" * 60)
    update_schema()
