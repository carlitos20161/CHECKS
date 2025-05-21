"""Add created_by_id to Check

Revision ID: d5950ffb56eb
Revises: 
Create Date: 2025-05-21 16:12:42.689565

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5950ffb56eb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('check', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_by_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_check_created_by_user', 'user', ['created_by_id'], ['id'])

def downgrade():
    with op.batch_alter_table('check', schema=None) as batch_op:
        batch_op.drop_constraint('fk_check_created_by_user', type_='foreignkey')
        batch_op.drop_column('created_by_id')

    # ### end Alembic commands ###
