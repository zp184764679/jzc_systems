# revision identifiers, used by Alembic.
revision = "rename_rfqitem_cols"
down_revision = "d7743944a83e"

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    # rfq_items.name -> item_name
    op.alter_column(
        "rfq_items",
        "name",
        new_column_name="item_name",
        existing_type=mysql.VARCHAR(length=200),
        existing_nullable=False,
    )
    # rfq_items.spec -> item_spec
    op.alter_column(
        "rfq_items",
        "spec",
        new_column_name="item_spec",
        existing_type=mysql.VARCHAR(length=200),
        existing_nullable=True,
    )
    # rfq_items.qty -> quantity
    op.alter_column(
        "rfq_items",
        "qty",
        new_column_name="quantity",
        existing_type=mysql.INTEGER(),
        existing_nullable=False,
    )

def downgrade():
    op.alter_column(
        "rfq_items",
        "item_name",
        new_column_name="name",
        existing_type=mysql.VARCHAR(length=200),
        existing_nullable=False,
    )
    op.alter_column(
        "rfq_items",
        "item_spec",
        new_column_name="spec",
        existing_type=mysql.VARCHAR(length=200),
        existing_nullable=True,
    )
    op.alter_column(
        "rfq_items",
        "quantity",
        new_column_name="qty",
        existing_type=mysql.INTEGER(),
        existing_nullable=False,
    )
