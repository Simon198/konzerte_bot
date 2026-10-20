"""clear audio samples

Revision ID: 3c4d5e6f7a8b
Revises: 2b3c4d5e6f7a
Create Date: 2026-10-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c4d5e6f7a8b'
down_revision: Union[str, Sequence[str], None] = '2b3c4d5e6f7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The audio samples were previously YouTube links; they are now fetched from
    # Deezer. Clear them so the next daily load re-fetches every band's top track.
    op.execute(sa.text("UPDATE bands SET audio_sample = NULL"))


def downgrade() -> None:
    """Downgrade schema."""
    # The previous (YouTube) values cannot be restored once cleared.
    pass
