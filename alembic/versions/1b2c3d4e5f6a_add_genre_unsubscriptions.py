"""add genre unsubscriptions

Revision ID: 1b2c3d4e5f6a
Revises: 6f7a8b9c0d1e
Create Date: 2026-10-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b2c3d4e5f6a'
down_revision: Union[str, Sequence[str], None] = '6f7a8b9c0d1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Stores only the genres a user does *not* want to be notified about. Newly
    # created genres are therefore automatically subscribed for every user,
    # without having to touch each user's rows.
    op.create_table(
        'genre_unsubscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('genre_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['genre_id'], ['genres.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('genre_unsubscriptions')
