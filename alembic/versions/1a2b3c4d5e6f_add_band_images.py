"""add band images

Revision ID: 1a2b3c4d5e6f
Revises: 7b2e9c1a4d8f
Create Date: 2026-10-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = '7b2e9c1a4d8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Path to the locally stored band image (``None`` until it is downloaded).
    op.add_column('bands', sa.Column('image_path', sa.String(), nullable=True))

    # Whether the observed message was sent as a photo, so we can pick between
    # ``edit_message_text`` and ``edit_message_caption`` when updating it.
    op.add_column(
        'observed_events',
        sa.Column('is_photo', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('observed_events', 'is_photo')
    op.drop_column('bands', 'image_path')
