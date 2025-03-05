"""Add ProductionOrder table

Revision ID: <new_hash>
Revises: e8c71d846708
Create Date: <timestamp>
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '<new_hash>'
down_revision = 'e8c71d846708'
branch_labels = None
depends_on = None

def upgrade():
    # Add the ProductionOrder table
    op.create_table(
        'production_order',
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(length=50), nullable=False),
        sa.Column('quantity_to_produce', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['product.product_id'], ),
        sa.PrimaryKeyConstraint('order_id')
    )

def downgrade():
    # Drop the ProductionOrder table
    op.drop_table('production_order')
