"""Add membership plan fields, benefits, and community_type

Updates ``membershipplan``:
  - Adds slug, is_free, is_public, trial_days, display_order columns
  - Changes ``active`` (boolean) to ``status`` (varchar) with values draft/active/archived
  - Data migration: sets status='active' where active=True, status='draft' otherwise

Creates ``membershipbenefit`` table:
  - Stores per-plan benefit configurations (community, space, course, resource,
    event access, download permissions, AI credits) with a JSON value column.
  - Unique constraint on (plan_id, benefit_type).

Updates ``community``:
  - Adds community_type column (open, paid, invite_only, hidden)

Revision ID: d5e6f7a8b9c0
Revises: a0b1c2d3e4f5
Create Date: 2026-06-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401


revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'a0b1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # ── 1. Update membershipplan table ──
    if 'membershipplan' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('membershipplan')}

        # Add new columns (idempotent)
        if 'slug' not in existing_cols:
            op.add_column('membershipplan', sa.Column('slug', sa.String(), nullable=False, server_default=''))
        if 'is_free' not in existing_cols:
            op.add_column('membershipplan', sa.Column('is_free', sa.Boolean(), nullable=False, server_default='0'))
        if 'is_public' not in existing_cols:
            op.add_column('membershipplan', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='1'))
        if 'trial_days' not in existing_cols:
            op.add_column('membershipplan', sa.Column('trial_days', sa.Integer(), nullable=False, server_default='0'))
        if 'display_order' not in existing_cols:
            op.add_column('membershipplan', sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'))

        # Replace boolean active with varchar status
        if 'active' in existing_cols and 'status' not in existing_cols:
            op.add_column('membershipplan', sa.Column('status', sa.String(20), nullable=False, server_default='draft'))
            # Data migration: convert active=True → status='active', else → 'draft'
            bind.execute(
                sa.text(
                    "UPDATE membershipplan SET status = 'active' WHERE active = 1"
                )
            )
            bind.execute(
                sa.text(
                    "UPDATE membershipplan SET status = 'draft' WHERE active = 0 OR active IS NULL"
                )
            )
            op.drop_column('membershipplan', 'active')
        elif 'status' not in existing_cols:
            op.add_column('membershipplan', sa.Column('status', sa.String(20), nullable=False, server_default='active'))

    # ── 3. Add community_type to community table ──
    if 'community' in existing_tables:
        existing_community_cols = {col['name'] for col in inspector.get_columns('community')}
        if 'community_type' not in existing_community_cols:
            op.add_column('community', sa.Column('community_type', sa.String(20), nullable=False, server_default='open'))

    # ── 2. Create membershipbenefit table ──
    if 'membershipbenefit' not in existing_tables:
        op.create_table(
            'membershipbenefit',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('plan_id', sa.Integer(),
                      sa.ForeignKey('membershipplan.id', ondelete='CASCADE'),
                      nullable=False),
            sa.Column('benefit_type', sa.String(50), nullable=False),
            sa.Column('benefit_value', sa.JSON(), nullable=True),
            sa.Column('creation_date', sa.String(), nullable=False, server_default=''),
            sa.Column('update_date', sa.String(), nullable=False, server_default=''),
        )
        op.create_index('ix_membershipbenefit_plan_id', 'membershipbenefit', ['plan_id'])
        op.create_unique_constraint('uq_plan_benefit_type', 'membershipbenefit', ['plan_id', 'benefit_type'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # Drop membershipbenefit table
    if 'membershipbenefit' in existing_tables:
        op.drop_constraint('uq_plan_benefit_type', 'membershipbenefit', type_='unique')
        op.drop_index('ix_membershipbenefit_plan_id', table_name='membershipbenefit')
        op.drop_table('membershipbenefit')

    # Revert membershipplan changes
    if 'membershipplan' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('membershipplan')}

        # Revert active → status
        if 'status' in existing_cols and 'active' not in existing_cols:
            op.add_column('membershipplan', sa.Column('active', sa.Boolean(), nullable=False, server_default='1'))
            bind.execute(
                sa.text(
                    "UPDATE membershipplan SET active = 1 WHERE status = 'active'"
                )
            )
            bind.execute(
                sa.text(
                    "UPDATE membershipplan SET active = 0 WHERE status != 'active'"
                )
            )
            op.drop_column('membershipplan', 'status')

        # Drop new columns
        for col in ['slug', 'is_free', 'is_public', 'trial_days', 'display_order']:
            if col in existing_cols:
                op.drop_column('membershipplan', col)

    # Drop community_type from community
    if 'community' in existing_tables:
        existing_community_cols = {col['name'] for col in inspector.get_columns('community')}
        if 'community_type' in existing_community_cols:
            op.drop_column('community', 'community_type')
