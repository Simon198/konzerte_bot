"""switch band images to stickers

Revision ID: 6f7a8b9c0d1e
Revises: 5e6f7a8b9c0d
Create Date: 2026-10-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f7a8b9c0d1e'
down_revision: Union[str, Sequence[str], None] = '5e6f7a8b9c0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Band images are now sent as WebP stickers, so the observed message is
    # always a plain text message and the ``is_photo`` flag is obsolete.
    op.drop_column('observed_events', 'is_photo')

    # Clear the stored image paths so the next daily load re-downloads each
    # band's image as a WebP sticker.
    op.execute(sa.text("UPDATE bands SET image_path = NULL"))


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'observed_events',
        sa.Column('is_photo', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
