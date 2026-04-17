"""Add telegram_id and username to users, make email nullable

Revision ID: f1a2b3c4d5e6
Revises: e4a1c7f92b05
Create Date: 2026-04-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e4a1c7f92b05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'email', existing_type=sa.String(length=255), nullable=True)
    op.add_column('users', sa.Column('telegram_id', sa.BigInteger(), nullable=True))
    op.add_column('users', sa.Column('username', sa.String(length=255), nullable=True))
    op.create_unique_constraint('uq_users_telegram_id', 'users', ['telegram_id'])


def downgrade() -> None:
    op.drop_constraint('uq_users_telegram_id', 'users', type_='unique')
    op.drop_column('users', 'username')
    op.drop_column('users', 'telegram_id')
    op.alter_column('users', 'email', existing_type=sa.String(length=255), nullable=False)
