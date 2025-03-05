"""Add is_rush to ProductionOrder

Revision ID: c01c43766079
Revises: ec50f120cf4b
Create Date: [timestamp]

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c01c43766079'
down_revision = 'ec50f120cf4b'
branch_labels = None
depends_on = None

def upgrade():
    # Add the column as nullable first
    op.add_column('production_order', sa.Column('is_rush', sa.Boolean(), nullable=True))
    
    # Update existing rows with a default value (False)
    op.execute("UPDATE production_order SET is_rush = FALSE WHERE is_rush IS NULL")
    
    # Alter the column to NOT NULL
    op.alter_column('production_order', 'is_rush', nullable=False)

def downgrade():
    # Remove the is_rush column
    op.drop_column('production_order', 'is_rush')