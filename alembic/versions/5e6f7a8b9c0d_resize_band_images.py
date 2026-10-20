"""resize band images

Revision ID: 5e6f7a8b9c0d
Revises: 4d5e6f7a8b9c
Create Date: 2026-10-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e6f7a8b9c0d'
down_revision: Union[str, Sequence[str], None] = '4d5e6f7a8b9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Band images are now resized to a small thumbnail before being stored.
    # Clear the stored paths so the next daily load re-downloads every band's
    # image at the new size.
    op.execute(sa.text("UPDATE bands SET image_path = NULL"))


def downgrade() -> None:
    """Downgrade schema."""
    # The previously downloaded image paths cannot be restored once cleared.
    pass
