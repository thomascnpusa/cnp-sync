"""Add production_batch to ProductionOrder

Revision ID: bf19b7b52ebd
Revises: d4ef1790e37e
Create Date: [your-date-here]
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'bf19b7b52ebd'
down_revision = 'd4ef1790e37e'
branch_labels = None
depends_on = None

def upgrade():
    # Add the column with a temporary default value for existing rows
    op.add_column('production_order', sa.Column('production_batch', sa.String(length=50), nullable=True))
    # Update existing rows with a default batch number
    op.execute("UPDATE production_order SET production_batch = 'PROD-LEGACY-' || order_id WHERE production_batch IS NULL")
    # Now make the column NOT NULL
    op.alter_column('production_order', 'production_batch', nullable=False)
    # Add unique constraint
    op.create_unique_constraint(None, 'production_order', ['production_batch'])

def downgrade():
    # Remove the unique constraint
    op.drop_constraint(None, 'production_order', type_='unique')
    # Drop the column
    op.drop_column('production_order', 'production_batch')