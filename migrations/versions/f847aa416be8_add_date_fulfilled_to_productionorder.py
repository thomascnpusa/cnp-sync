"""Add date_fulfilled to ProductionOrder

Revision ID: f847aa416be8
Revises: bf19b7b52ebd
Create Date: 2025-03-04 22:09:14.030323

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f847aa416be8'
down_revision = 'bf19b7b52ebd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('production_order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date_fulfilled', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('production_order', schema=None) as batch_op:
        batch_op.drop_column('date_fulfilled')

    # ### end Alembic commands ###
