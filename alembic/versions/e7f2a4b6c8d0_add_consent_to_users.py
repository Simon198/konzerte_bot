"""add consent to users

Revision ID: e7f2a4b6c8d0
Revises: d4f8a1b2c3e6
Create Date: 2026-10-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f2a4b6c8d0'
down_revision: Union[str, Sequence[str], None] = 'd4f8a1b2c3e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column(
            'consent_given', sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        'users', sa.Column('consent_date', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'users', sa.Column('consent_version', sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'consent_version')
    op.drop_column('users', 'consent_date')
    op.drop_column('users', 'consent_given')
