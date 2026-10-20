"""clear band images

Revision ID: 4d5e6f7a8b9c
Revises: 3c4d5e6f7a8b
Create Date: 2026-10-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d5e6f7a8b9c'
down_revision: Union[str, Sequence[str], None] = '3c4d5e6f7a8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Band images were previously downloaded at the largest Deezer size
    # (1000x1000 px). Clear them so the next daily load re-downloads the
    # smaller 500x500 px size now preferred for Telegram display.
    op.execute(sa.text("UPDATE bands SET image_path = NULL"))


def downgrade() -> None:
    """Downgrade schema."""
    # The previously downloaded image paths cannot be restored once cleared.
    pass
