"""Add difficulty to games

Revision ID: e4a1c7f92b05
Revises: b3f9a2c81d44
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e4a1c7f92b05'
down_revision: Union[str, Sequence[str], None] = 'b3f9a2c81d44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('games', sa.Column('difficulty', sa.Integer(), nullable=False, server_default='5'))


def downgrade() -> None:
    op.drop_column('games', 'difficulty')