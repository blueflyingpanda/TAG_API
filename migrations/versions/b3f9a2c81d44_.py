"""Drop difficulty, played_count, last_played from themes

Revision ID: b3f9a2c81d44
Revises: a82581816a20
Create Date: 2026-04-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b3f9a2c81d44'
down_revision: Union[str, Sequence[str], None] = 'a82581816a20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('themes', 'difficulty')
    op.drop_column('themes', 'played_count')
    op.drop_column('themes', 'last_played')


def downgrade() -> None:
    op.add_column('themes', sa.Column('last_played', sa.DateTime(timezone=True), nullable=True))
    op.add_column('themes', sa.Column('played_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('themes', sa.Column('difficulty', sa.Integer(), nullable=False, server_default='1'))