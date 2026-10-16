"""merge afisha stats and reviews heads

Revision ID: 99b73000c91d
Revises: 20261016_02, 20261016_04
Create Date: 2026-10-16 23:31:40.755983
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '99b73000c91d'
down_revision: Union[str, Sequence[str], None] = ('20261016_02', '20261016_04')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
