"""Add spaces table and discussion.space_id

Creates the ``space`` table for community sub-sections (General,
Announcements, Questions, etc.) and adds a nullable ``space_id`` foreign
key to the ``discussion`` table so that existing discussions remain valid.

A one-off data migration creates a default "General" space for every
existing community and back-fills its ``space_id`` on all orphan
discussions.

Revision ID: a0b1c2d3e4f5
Revises: z5a6b7c8d9e0
Create Date: 2026-06-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa: F401

revision: str = 'a0b1c2d3e4f5'
down_revision: Union[str, None] = 'z5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # ── 1. Create space table (idempotent) ──
    if 'space' not in existing_tables:
        op.create_table(
            'space',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('community_id', sa.Integer(),
                      sa.ForeignKey('community.id', ondelete='CASCADE'),
                      nullable=False),
            sa.Column('org_id', sa.Integer(),
                      sa.ForeignKey('organization.id', ondelete='CASCADE'),
                      nullable=False),
            sa.Column('space_uuid', sa.String(), nullable=False, index=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('icon', sa.String(50), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('ordering', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('visibility', sa.String(20), nullable=False, server_default='public'),
            sa.Column('creation_date', sa.String(), nullable=False, server_default=''),
            sa.Column('update_date', sa.String(), nullable=False, server_default=''),
        )
        op.create_index('ix_space_community_id', 'space', ['community_id'])
        op.create_index('ix_space_org_id', 'space', ['org_id'])

    # ── 2. Add space_id to discussion (nullable, SET NULL on delete) ──
    if 'discussion' in existing_tables:
        existing_discussion_cols = {col['name'] for col in inspector.get_columns('discussion')}
        if 'space_id' not in existing_discussion_cols:
            op.add_column(
                'discussion',
                sa.Column('space_id', sa.Integer(),
                          sa.ForeignKey('space.id', ondelete='SET NULL'),
                          nullable=True),
            )

    # ── 3. Data migration: create General space per community ──
    # Use raw SQL since SQLModel models may not be importable in migration
    communities = []
    try:
        rows = bind.execute(sa.text(
            "SELECT id, org_id, community_uuid FROM community"
        )).fetchall()
        communities = [(r[0], r[1], r[2]) for r in rows]
    except Exception:
        communities = []

    if communities:
        now = "2026-06-25 00:00:00"
        for community_id, org_id, community_uuid in communities:
            # Check if this community already has any spaces
            existing = bind.execute(
                sa.text("SELECT COUNT(*) FROM space WHERE community_id = :cid"),
                {"cid": community_id},
            ).scalar()
            if existing and existing > 0:
                continue

            # Create General space
            result = bind.execute(
                sa.text(
                    """INSERT INTO space (community_id, org_id, space_uuid, name, icon,
                                          description, ordering, visibility,
                                          creation_date, update_date)
                       VALUES (:cid, :oid, :uuid, 'General', '💬',
                               'General discussions', 0, 'public',
                               :now, :now)
                       RETURNING id"""
                ),
                {"cid": community_id, "oid": org_id,
                 "uuid": f"space_{community_uuid}_general", "now": now},
            )
            general_space_id = result.scalar()

            # Assign all existing discussions to General space
            bind.execute(
                sa.text(
                    "UPDATE discussion SET space_id = :sid "
                    "WHERE community_id = :cid AND space_id IS NULL"
                ),
                {"sid": general_space_id, "cid": community_id},
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Remove space_id from discussion (column drop loses data — back up first)
    if 'discussion' in inspector.get_table_names():
        existing_cols = {col['name'] for col in inspector.get_columns('discussion')}
        if 'space_id' in existing_cols:
            op.drop_column('discussion', 'space_id')

    # Drop space table
    if 'space' in inspector.get_table_names():
        op.drop_index('ix_space_org_id', table_name='space')
        op.drop_index('ix_space_community_id', table_name='space')
        op.drop_table('space')
