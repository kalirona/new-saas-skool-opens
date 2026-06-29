"""Add locking, plan assignments, and billing abstraction

Adds:
  - `locked` column to community, space, resource, event, course tables
  - Junction tables: plan_course, plan_space, plan_resource, plan_event
  - Data migration: creates a "Free" plan for every community that has
    zero membership plans, so existing communities continue working
    without disruption.

Revision ID: p1q2r3s4t5u6
Revises: z5a6b7c8d9e0
Create Date: 2026-06-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql
from datetime import datetime
from uuid import uuid4

revision: str = "p1q2r3s4t5u6"
down_revision: Union[str, None] = "z5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Add `locked` column to community ───────────────────────────────
    existing_community_cols = [
        row[0] for row in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'community'"))
    ]
    if "locked" not in existing_community_cols:
        op.add_column("community", sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # ── 2. Add `locked` column to space ───────────────────────────────────
    existing_space_cols = [
        row[0] for row in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'space'"))
    ]
    if "locked" not in existing_space_cols:
        op.add_column("space", sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # ── 3. Add `locked` column to resource ────────────────────────────────
    existing_resource_cols = [
        row[0] for row in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'resource'"))
    ]
    if "locked" not in existing_resource_cols:
        op.add_column("resource", sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # ── 4. Add `locked` column to event ───────────────────────────────────
    existing_event_cols = [
        row[0] for row in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'event'"))
    ]
    if "locked" not in existing_event_cols:
        op.add_column("event", sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # ── 5. Add `locked` column to course ──────────────────────────────────
    existing_course_cols = [
        row[0] for row in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'course'"))
    ]
    if "locked" not in existing_course_cols:
        op.add_column("course", sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # ── 6. Create plan_course junction table ──────────────────────────────
    if not conn.dialect.has_table(conn, "plan_course"):
        op.create_table(
            "plan_course",
            sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
            sa.Column("plan_id", sa.Integer(), sa.ForeignKey("membershipplan.id", ondelete="CASCADE"), nullable=False),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("course.id", ondelete="CASCADE"), nullable=False),
            sa.Column("creation_date", sa.String(), nullable=False, server_default=""),
            sa.Column("update_date", sa.String(), nullable=False, server_default=""),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_plan_course_plan", "plan_course", ["plan_id"])
        op.create_index("ix_plan_course_course", "plan_course", ["course_id"])

    # ── 7. Create plan_space junction table ───────────────────────────────
    if not conn.dialect.has_table(conn, "plan_space"):
        op.create_table(
            "plan_space",
            sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
            sa.Column("plan_id", sa.Integer(), sa.ForeignKey("membershipplan.id", ondelete="CASCADE"), nullable=False),
            sa.Column("space_id", sa.Integer(), sa.ForeignKey("space.id", ondelete="CASCADE"), nullable=False),
            sa.Column("creation_date", sa.String(), nullable=False, server_default=""),
            sa.Column("update_date", sa.String(), nullable=False, server_default=""),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_plan_space_plan", "plan_space", ["plan_id"])
        op.create_index("ix_plan_space_space", "plan_space", ["space_id"])

    # ── 8. Create plan_resource junction table ────────────────────────────
    if not conn.dialect.has_table(conn, "plan_resource"):
        op.create_table(
            "plan_resource",
            sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
            sa.Column("plan_id", sa.Integer(), sa.ForeignKey("membershipplan.id", ondelete="CASCADE"), nullable=False),
            sa.Column("resource_id", sa.Integer(), sa.ForeignKey("resource.id", ondelete="CASCADE"), nullable=False),
            sa.Column("creation_date", sa.String(), nullable=False, server_default=""),
            sa.Column("update_date", sa.String(), nullable=False, server_default=""),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_plan_resource_plan", "plan_resource", ["plan_id"])
        op.create_index("ix_plan_resource_resource", "plan_resource", ["resource_id"])

    # ── 9. Create plan_event junction table ───────────────────────────────
    if not conn.dialect.has_table(conn, "plan_event"):
        op.create_table(
            "plan_event",
            sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
            sa.Column("plan_id", sa.Integer(), sa.ForeignKey("membershipplan.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id", ondelete="CASCADE"), nullable=False),
            sa.Column("creation_date", sa.String(), nullable=False, server_default=""),
            sa.Column("update_date", sa.String(), nullable=False, server_default=""),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_plan_event_plan", "plan_event", ["plan_id"])
        op.create_index("ix_plan_event_event", "plan_event", ["event_id"])

    # ── 10. Create a "Free" plan for existing communities without plans ───
    # This ensures existing communities remain accessible after the locking
    # and plan-assignment features go live.
    communities = conn.execute(
        sa.text("""
            SELECT c.id, c.org_id
            FROM community c
            WHERE c.id NOT IN (
                SELECT DISTINCT mp.community_id
                FROM membershipplan mp
            )
        ")
    ).fetchall()

    default_usergroup_ids: dict[int, int] = {}
    for community_id, org_id in communities:
        # Create a UserGroup for the free plan
        ug_uuid = f"usergroup_{uuid4().hex}"
        now = str(datetime.now())
        ug_result = conn.execute(
            sa.text("""
                INSERT INTO usergroup (name, description, org_id, usergroup_uuid, creation_date, update_date)
                VALUES (:name, :desc, :org_id, :uuid, :now, :now)
                RETURNING id
            """),
            {"name": f"Free Plan Members (Community #{community_id})", "desc": "Auto-created free plan usergroup",
             "org_id": org_id, "uuid": ug_uuid, "now": now},
        )
        ug_id = ug_result.scalar()
        default_usergroup_ids[community_id] = ug_id

        # Link the community to the usergroup so free-plan members get access
        conn.execute(
            sa.text("""
                INSERT INTO usergroup_resource (usergroup_id, resource_uuid, org_id, creation_date, update_date)
                VALUES (:ug_id, :res_uuid, :org_id, :now, :now)
            """),
            {"ug_id": ug_id, "res_uuid": f"community_{community_id}", "org_id": org_id, "now": now},
        )

        # Create the Free plan
        plan_uuid = f"plan_{uuid4().hex}"
        slug = f"free-community-{community_id}"
        conn.execute(
            sa.text("""
                INSERT INTO membershipplan
                    (name, slug, description, price, currency, interval, max_members,
                     is_free, is_public, trial_days, display_order, features, status,
                     community_id, org_id, usergroup_id, plan_uuid, creation_date, update_date)
                VALUES
                    ('Free', :slug, 'Free access to this community', 0, 'usd', 'monthly', 0,
                     true, true, 0, 0, '{}'::json, 'active',
                     :community_id, :org_id, :ug_id, :plan_uuid, :now, :now)
            """),
            {"slug": slug, "community_id": community_id, "org_id": org_id,
             "ug_id": ug_id, "plan_uuid": plan_uuid, "now": now},
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Drop junction tables
    for table in ["plan_course", "plan_space", "plan_resource", "plan_event"]:
        if conn.dialect.has_table(conn, table):
            op.drop_table(table)

    # Remove locked columns
    existing_community_cols = [
        row[0] for row in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'community'"))
    ]
    if "locked" in existing_community_cols:
        op.drop_column("community", "locked")

    existing_space_cols = [
        row[0] for row in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'space'"))
    ]
    if "locked" in existing_space_cols:
        op.drop_column("space", "locked")

    existing_resource_cols = [
        row[0] for row in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'resource'"))
    ]
    if "locked" in existing_resource_cols:
        op.drop_column("resource", "locked")

    existing_event_cols = [
        row[0] for row in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'event'"))
    ]
    if "locked" in existing_event_cols:
        op.drop_column("event", "locked")

    existing_course_cols = [
        row[0] for row in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'course'"))
    ]
    if "locked" in existing_course_cols:
        op.drop_column("course", "locked")

    # Note: auto-created Free plans and their UserGroups are intentionally
    # NOT removed on downgrade. They are harmless and removing them would
    # break existing memberships.
