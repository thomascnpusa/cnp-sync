"""Add InventoryReceipt table

Revision ID: 84bc16949c28
Revises: 186d14ef8538
Create Date: 2025-03-04 11:39:52.869806

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '84bc16949c28'
down_revision = '186d14ef8538'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('inventory_receipt',
    sa.Column('receipt_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.String(length=50), nullable=False),
    sa.Column('quantity_received', sa.Float(), nullable=False),
    sa.Column('date_received', sa.DateTime(), nullable=True),
    sa.Column('batch_number', sa.String(length=50), nullable=True),
    sa.Column('notes', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['product.product_id'], ),
    sa.PrimaryKeyConstraint('receipt_id')
    )
    with op.batch_alter_table('inventory', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location', sa.String(length=50), nullable=False))
        batch_op.add_column(sa.Column('quantity', sa.Float(), nullable=False))
        batch_op.add_column(sa.Column('minimum_quantity', sa.Float(), nullable=False))
        batch_op.drop_column('stock_level')

    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.String(length=50), nullable=False))
        batch_op.add_column(sa.Column('sellable', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('default_unit_of_measure', sa.String(length=20), nullable=False))
        batch_op.drop_column('price')

    with op.batch_alter_table('sale', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date', sa.DateTime(), nullable=False))
        batch_op.add_column(sa.Column('channel', sa.String(length=50), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sale', schema=None) as batch_op:
        batch_op.drop_column('channel')
        batch_op.drop_column('date')

    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('price', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
        batch_op.drop_column('default_unit_of_measure')
        batch_op.drop_column('sellable')
        batch_op.drop_column('type')

    with op.batch_alter_table('inventory', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stock_level', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.drop_column('minimum_quantity')
        batch_op.drop_column('quantity')
        batch_op.drop_column('location')

    op.drop_table('inventory_receipt')
    # ### end Alembic commands ###
