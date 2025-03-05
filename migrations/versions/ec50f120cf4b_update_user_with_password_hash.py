"""Update User with password_hash

Revision ID: ec50f120cf4b
Revises: 77b8adb2c1f6
Create Date: [timestamp]

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ec50f120cf4b'
down_revision = '77b8adb2c1f6'
branch_labels = None
depends_on = None

def upgrade():
    # Add the column as nullable first
    op.add_column('user', sa.Column('password_hash', sa.String(length=128), nullable=True))
    
    # Update existing rows with a default password hash (e.g., 'password123')
    op.execute("UPDATE \"user\" SET password_hash = 'pbkdf2:sha256:260000$default$saltedhash' WHERE password_hash IS NULL")
    
    # Alter the column to NOT NULL
    op.alter_column('user', 'password_hash', nullable=False)

def downgrade():
    # Remove the password_hash column
    op.drop_column('user', 'password_hash')