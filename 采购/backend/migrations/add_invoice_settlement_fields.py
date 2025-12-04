# migrations/add_invoice_settlement_fields.py
# -*- coding: utf-8 -*-
r"""
迁移脚本：为发票系统添加月结支持

变更内容：
1. invoices表新增字段：
   - settlement_type: 结算方式 (per_order/monthly)
   - settlement_period: 结算周期 (YYYY-MM格式)
2. invoices.po_id 改为 nullable (月结发票不需要)
3. 创建 invoice_po_links 表（发票-PO多对多关联）
4. suppliers表新增字段：
   - settlement_type: 供应商默认结算方式
   - settlement_day: 月结结算日
   - payment_days: 账期天数

运行方式：
cd C:\Users\Admin\Desktop\采购\backend
venv\Scripts\python.exe migrations\add_invoice_settlement_fields.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from sqlalchemy import text


def column_exists(table, column):
    """检查列是否存在"""
    sql = text("""
        SELECT COUNT(*) as cnt FROM information_schema.columns
        WHERE table_schema = DATABASE()
        AND table_name = :table
        AND column_name = :column
    """)
    result = db.session.execute(sql, {'table': table, 'column': column})
    return result.fetchone()[0] > 0


def table_exists(table_name):
    """检查表是否存在"""
    sql = text("""
        SELECT COUNT(*) as cnt FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = :table
    """)
    result = db.session.execute(sql, {'table': table_name})
    return result.fetchone()[0] > 0


def index_exists(table, index_name):
    """检查索引是否存在"""
    sql = text("""
        SELECT COUNT(*) as cnt FROM information_schema.statistics
        WHERE table_schema = DATABASE()
        AND table_name = :table
        AND index_name = :index_name
    """)
    result = db.session.execute(sql, {'table': table, 'index_name': index_name})
    return result.fetchone()[0] > 0


def run_migration():
    """执行迁移"""
    from app import app

    with app.app_context():
        print("=" * 60)
        print("发票月结支持迁移脚本")
        print("=" * 60)

        # 1. 检查并添加 suppliers 表的结算字段
        print("\n[1/5] 检查 suppliers 表结算字段...")

        if not column_exists('suppliers', 'settlement_type'):
            print("  添加 settlement_type 字段...")
            db.session.execute(text("""
                ALTER TABLE suppliers
                ADD COLUMN settlement_type VARCHAR(20) NOT NULL DEFAULT 'per_order'
                COMMENT '结算方式: per_order=单次结算, monthly=月结'
            """))
        else:
            print("  settlement_type 已存在，跳过")

        if not column_exists('suppliers', 'settlement_day'):
            print("  添加 settlement_day 字段...")
            db.session.execute(text("""
                ALTER TABLE suppliers
                ADD COLUMN settlement_day INT NULL
                COMMENT '月结结算日（1-28）'
            """))
        else:
            print("  settlement_day 已存在，跳过")

        if not column_exists('suppliers', 'payment_days'):
            print("  添加 payment_days 字段...")
            db.session.execute(text("""
                ALTER TABLE suppliers
                ADD COLUMN payment_days INT NULL DEFAULT 30
                COMMENT '账期天数'
            """))
        else:
            print("  payment_days 已存在，跳过")

        db.session.commit()
        print("  ✅ suppliers 表更新完成")

        # 2. 检查并添加 invoices 表的结算字段
        print("\n[2/5] 检查 invoices 表结算字段...")

        if not column_exists('invoices', 'settlement_type'):
            print("  添加 settlement_type 字段...")
            db.session.execute(text("""
                ALTER TABLE invoices
                ADD COLUMN settlement_type VARCHAR(20) NOT NULL DEFAULT 'per_order'
                COMMENT '结算方式'
            """))
        else:
            print("  settlement_type 已存在，跳过")

        if not column_exists('invoices', 'settlement_period'):
            print("  添加 settlement_period 字段...")
            db.session.execute(text("""
                ALTER TABLE invoices
                ADD COLUMN settlement_period VARCHAR(10) NULL
                COMMENT '结算周期（YYYY-MM格式）'
            """))
        else:
            print("  settlement_period 已存在，跳过")

        db.session.commit()
        print("  ✅ invoices 表字段更新完成")

        # 3. 修改 po_id 为 nullable
        print("\n[3/5] 修改 invoices.po_id 为 nullable...")
        try:
            db.session.execute(text("""
                ALTER TABLE invoices
                MODIFY COLUMN po_id BIGINT UNSIGNED NULL
                COMMENT '单次结算时的PO ID'
            """))
            db.session.commit()
            print("  ✅ po_id 已改为 nullable")
        except Exception as e:
            if "Duplicate" in str(e):
                print("  po_id 已经是 nullable，跳过")
            else:
                print(f"  ⚠️ 修改失败: {e}")

        # 4. 创建 invoice_po_links 表
        print("\n[4/5] 创建 invoice_po_links 表...")

        if not table_exists('invoice_po_links'):
            db.session.execute(text("""
                CREATE TABLE invoice_po_links (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    invoice_id BIGINT UNSIGNED NOT NULL,
                    po_id BIGINT UNSIGNED NOT NULL,
                    po_amount DECIMAL(12, 2) NULL COMMENT '该PO对应的发票金额',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_invoice_po_links_invoice
                        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                    CONSTRAINT fk_invoice_po_links_po
                        FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
                    CONSTRAINT uq_invoice_po UNIQUE (invoice_id, po_id),

                    INDEX idx_invoice_po_links_invoice (invoice_id),
                    INDEX idx_invoice_po_links_po (po_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='发票与PO的多对多关联表（用于月结发票）'
            """))
            db.session.commit()
            print("  ✅ invoice_po_links 表创建成功")
        else:
            print("  invoice_po_links 表已存在，跳过")

        # 5. 添加索引
        print("\n[5/5] 添加索引...")

        if not index_exists('invoices', 'idx_invoices_settlement_type'):
            db.session.execute(text("""
                CREATE INDEX idx_invoices_settlement_type ON invoices(settlement_type)
            """))
            print("  添加 idx_invoices_settlement_type 索引")
        else:
            print("  idx_invoices_settlement_type 已存在")

        if not index_exists('invoices', 'idx_invoices_settlement_period'):
            db.session.execute(text("""
                CREATE INDEX idx_invoices_settlement_period ON invoices(settlement_period)
            """))
            print("  添加 idx_invoices_settlement_period 索引")
        else:
            print("  idx_invoices_settlement_period 已存在")

        db.session.commit()
        print("  ✅ 索引添加完成")

        print("\n" + "=" * 60)
        print("✅ 迁移完成！")
        print("=" * 60)
        print("\n变更摘要:")
        print("  - suppliers 表: 添加 settlement_type, settlement_day, payment_days")
        print("  - invoices 表: 添加 settlement_type, settlement_period; po_id 改为 nullable")
        print("  - 新建 invoice_po_links 表（多对多关联）")


if __name__ == '__main__':
    run_migration()
