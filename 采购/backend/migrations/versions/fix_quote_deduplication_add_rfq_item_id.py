"""fix_quote_deduplication_add_rfq_item_id

Revision ID: fix_dedup_2025
Revises: 85f668c04a07
Create Date: 2025-11-08 (Manual)

修复报价去重问题：
- 添加 rfq_item_id 字段，关联到具体物料项
- 删除旧的 supplier_id+rfq_id+category 唯一索引
- 添加新的 supplier_id+rfq_id+rfq_item_id 唯一索引
- 确保每个供应商可以对每个物料项单独报价

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'fix_dedup_2025'
down_revision = '85f668c04a07'
branch_labels = None
depends_on = None


def upgrade():
    # 修改 supplier_quotes 表
    with op.batch_alter_table('supplier_quotes', schema=None) as batch_op:
        # 1. 添加 rfq_item_id 字段
        batch_op.add_column(
            sa.Column(
                'rfq_item_id',
                mysql.BIGINT(unsigned=True),
                nullable=True,
                comment='关联的RFQ物料项ID，每个物料单独报价'
            )
        )

        # 2. 添加外键约束
        batch_op.create_foreign_key(
            'fk_supplier_quotes_rfq_item_id',
            'rfq_items',
            ['rfq_item_id'],
            ['id']
        )

        # 3. 添加 rfq_item_id 索引
        batch_op.create_index(
            'idx_sq_rfq_item_id',
            ['rfq_item_id'],
            unique=False
        )

        # 4. 删除旧的 category 唯一索引（supplier_id + rfq_id + category）
        batch_op.drop_index('ix_supplier_quotes_supplier_rfq_category')

        # 5. 创建新的唯一索引（supplier_id + rfq_id + rfq_item_id）
        batch_op.create_index(
            'ix_supplier_quotes_supplier_rfq_item_id',
            ['supplier_id', 'rfq_id', 'rfq_item_id'],
            unique=True
        )


def downgrade():
    # 回滚操作
    with op.batch_alter_table('supplier_quotes', schema=None) as batch_op:
        # 1. 删除新索引
        batch_op.drop_index('ix_supplier_quotes_supplier_rfq_item_id')

        # 2. 恢复旧的 category 唯一索引
        batch_op.create_index(
            'ix_supplier_quotes_supplier_rfq_category',
            ['supplier_id', 'rfq_id', 'category'],
            unique=True
        )

        # 3. 删除 rfq_item_id 索引
        batch_op.drop_index('idx_sq_rfq_item_id')

        # 4. 删除外键约束
        batch_op.drop_constraint(
            'fk_supplier_quotes_rfq_item_id',
            type_='foreignkey'
        )

        # 5. 删除 rfq_item_id 字段
        batch_op.drop_column('rfq_item_id')
