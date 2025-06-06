"""Initial migration

Revision ID: 84dda9b5ee25
Revises: 
Create Date: 2025-06-02 14:07:51.006166
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '84dda9b5ee25'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Optional cleanup (be careful if this table exists with needed data!)
    op.drop_table('_alembic_tmp_check')

    with op.batch_alter_table('check', schema=None) as batch_op:
        batch_op.alter_column(
            'company_id',
            existing_type=sa.INTEGER(),
            nullable=True
        )

    with op.batch_alter_table('employee', schema=None) as batch_op:
        batch_op.add_column(sa.Column('client_id', sa.Integer(), nullable=True))
        batch_op.alter_column(
            'company_id',
            existing_type=sa.INTEGER(),
            nullable=True
        )
        # ✅ Fix: Give the constraint a name
        batch_op.create_foreign_key(
            'fk_employee_client_id',
            'company_client',
            ['client_id'],
            ['id']
        )


def downgrade():
    with op.batch_alter_table('employee', schema=None) as batch_op:
        batch_op.drop_constraint('fk_employee_client_id', type_='foreignkey')
        batch_op.alter_column(
            'company_id',
            existing_type=sa.INTEGER(),
            nullable=False
        )
        batch_op.drop_column('client_id')

    with op.batch_alter_table('check', schema=None) as batch_op:
        batch_op.alter_column(
            'company_id',
            existing_type=sa.INTEGER(),
            nullable=False
        )

    op.create_table(
        '_alembic_tmp_check',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('check_number', sa.INTEGER(), nullable=False),
        sa.Column('amount', sa.NUMERIC(10, 2), nullable=False),
        sa.Column('date', sa.DATE(), nullable=False),
        sa.Column('flagged_by_user', sa.BOOLEAN(), nullable=True),
        sa.Column('flag_reason', sa.VARCHAR(255), nullable=True),
        sa.Column('hours_worked', sa.NUMERIC(6, 2), nullable=True),
        sa.Column('pay_rate', sa.NUMERIC(10, 2), nullable=True),
        sa.Column('overtime_hours', sa.NUMERIC(6, 2), nullable=True),
        sa.Column('overtime_rate', sa.NUMERIC(10, 2), nullable=True),
        sa.Column('holiday_hours', sa.NUMERIC(6, 2), nullable=True),
        sa.Column('holiday_rate', sa.NUMERIC(10, 2), nullable=True),
        sa.Column('memo', sa.VARCHAR(200), nullable=True),
        sa.Column('bank_id', sa.INTEGER(), nullable=False),
        sa.Column('company_id', sa.INTEGER(), nullable=True),
        sa.Column('employee_id', sa.INTEGER(), nullable=False),
        sa.Column('client_id', sa.INTEGER(), nullable=True),
        sa.Column('created_by_id', sa.INTEGER(), nullable=True),
        sa.ForeignKeyConstraint(['bank_id'], ['bank.id']),
        sa.ForeignKeyConstraint(['company_id'], ['company.id']),
        sa.ForeignKeyConstraint(['employee_id'], ['employee.id']),
        sa.ForeignKeyConstraint(['client_id'], ['company_client.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )
