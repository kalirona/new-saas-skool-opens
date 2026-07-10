"""Merge remaining heads: membership plans, payment amount, locking

Resolves the 3 orphan heads into the main line at f7a8b9c0d1e2 so that
``alembic upgrade head`` succeeds without requiring --branchname flags.

Revision ID: a9b0c1d2e3f4
Revises: f7a8b9c0d1e2, d5e6f7a8b9c0, a0b1c2d3e4f6, p1q2r3s4t5u6
Create Date: 2026-07-10
"""
from typing import Sequence, Union


revision: str = "a9b0c1d2e3f4"
down_revision: Union[str, Sequence[str], None] = (
    "f7a8b9c0d1e2",
    "d5e6f7a8b9c0",
    "a0b1c2d3e4f6",
    "p1q2r3s4t5u6",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
