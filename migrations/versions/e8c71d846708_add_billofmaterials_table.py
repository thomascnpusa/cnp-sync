"""Add BillOfMaterials table

Revision ID: e8c71d846708
Revises: 84bc16949c28
Create Date: <timestamp>
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e8c71d846708'
down_revision = '84bc16949c28'
branch_labels = None
depends_on = None

def upgrade():
    # Only add the BillOfMaterials table
    op.create_table(
        'bill_of_materials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('finished_product_id', sa.String(length=50), nullable=False),
        sa.Column('component_product_id', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['finished_product_id'], ['product.product_id'], ),
        sa.ForeignKeyConstraint(['component_product_id'], ['product.product_id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Only drop the BillOfMaterials table
    op.drop_table('bill_of_materials')
