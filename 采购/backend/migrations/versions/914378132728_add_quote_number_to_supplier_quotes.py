"""add_quote_number_to_supplier_quotes

Revision ID: 914378132728
Revises: 4eecc7d8d320
Create Date: 2025-11-03 12:12:03.204989

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = '914378132728'
down_revision = '4eecc7d8d320'
branch_labels = None
depends_on = None


def upgrade():
    # Add quote_number column to supplier_quotes table
    with op.batch_alter_table('supplier_quotes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('quote_number', mysql.VARCHAR(length=50), nullable=True))
        batch_op.create_index('idx_sq_quote_number', ['quote_number'], unique=True)


def downgrade():
    # Remove quote_number column and index
    with op.batch_alter_table('supplier_quotes', schema=None) as batch_op:
        batch_op.drop_index('idx_sq_quote_number')
        batch_op.drop_column('quote_number')
