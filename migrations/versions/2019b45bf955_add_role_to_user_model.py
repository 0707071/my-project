"""Add role to User model
Revision ID: 2019b45bf955
Revises: 0518602c66c1
Create Date: 2024-11-04 14:08:09.354954
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2019b45bf955'
down_revision = '0518602c66c1'
branch_labels = None
depends_on = None

def upgrade():
    # Create the role enum type if it doesn't exist
    role_enum = postgresql.ENUM('client', 'analyst', name='role')
    role_enum.create(op.get_bind(), checkfirst=True)
    
    # Add the role column with a default value
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', role_enum, nullable=False, server_default='client'))  # Ensure default value is set

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('role')
    
    role_enum = postgresql.ENUM('client', 'analyst', name='role')
    role_enum.drop(op.get_bind(), checkfirst=True)