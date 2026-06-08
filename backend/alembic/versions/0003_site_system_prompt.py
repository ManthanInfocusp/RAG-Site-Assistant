"""Add system_prompt column to sites.

Revision ID: 0003_site_system_prompt
Revises: 0002_visitor_identifier
Create Date: 2026-06-05
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_site_system_prompt"
down_revision: Union[str, None] = "0002_visitor_identifier"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sites", sa.Column("system_prompt", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("sites", "system_prompt")
