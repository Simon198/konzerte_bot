"""add sticker file id to bands

Revision ID: a1b2c3d4e5f6
Revises: 9a1f3c5d7e8b
Create Date: 2026-11-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9a1f3c5d7e8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Telegram ``file_id`` of the band's sticker, so it only has to be uploaded
    # once and can then be sent to any chat by id. ``None`` until first upload.
    op.add_column('bands', sa.Column('sticker_file_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('bands', 'sticker_file_id')
