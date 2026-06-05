"""Add visitor_identifier to conversations.

Revision ID: 0002_visitor_identifier
Revises: 0001_initial
Create Date: 2026-06-04
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_visitor_identifier"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("visitor_identifier", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversations", "visitor_identifier")
