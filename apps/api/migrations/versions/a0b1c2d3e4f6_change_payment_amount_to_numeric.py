"""Change Payment.amount from Float to Numeric(10,2)

Fixes critical production issue where monetary amounts stored as binary
float cause cumulative rounding errors (e.g. float(\"19.99\") → 19.9899...).

Revision ID: a0b1c2d3e4f6
Revises: z5a6b7c8d9e0
Create Date: 2026-06-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401


revision: str = 'a0b1c2d3e4f6'
down_revision: Union[str, None] = 'z5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'payment' not in inspector.get_table_names():
        return

    existing_columns = {col['name'] for col in inspector.get_columns('payment')}
    if 'amount' not in existing_columns:
        return

    op.alter_column(
        'payment',
        'amount',
        type_=sa.Numeric(10, 2),
        existing_type=sa.Float(),
        postgresql_using='amount::numeric(10,2)',
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'payment' not in inspector.get_table_names():
        return

    existing_columns = {col['name'] for col in inspector.get_columns('payment')}
    if 'amount' not in existing_columns:
        return

    op.alter_column(
        'payment',
        'amount',
        type_=sa.Float(),
        existing_type=sa.Numeric(10, 2),
        postgresql_using='amount::double precision',
    )
