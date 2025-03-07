"""empty message

Revision ID: 186d14ef8538
Revises: 
Create Date: 2025-03-04 11:27:07.638360

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '186d14ef8538'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('product',
    sa.Column('product_id', sa.String(length=50), nullable=False),
    sa.Column('product_name', sa.String(length=255), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('product_id')
    )
    op.create_table('inventory',
    sa.Column('inventory_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.String(length=50), nullable=False),
    sa.Column('stock_level', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['product.product_id'], ),
    sa.PrimaryKeyConstraint('inventory_id')
    )
    op.create_table('sale',
    sa.Column('sale_id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.String(length=50), nullable=False),
    sa.Column('product_id', sa.String(length=50), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['product.product_id'], ),
    sa.PrimaryKeyConstraint('sale_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sale')
    op.drop_table('inventory')
    op.drop_table('product')
    # ### end Alembic commands ###
