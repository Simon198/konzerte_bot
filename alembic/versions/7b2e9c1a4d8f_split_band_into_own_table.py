"""split band into its own table

Revision ID: 7b2e9c1a4d8f
Revises: e7f2a4b6c8d0
Create Date: 2026-10-19 00:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b2e9c1a4d8f'
down_revision: Union[str, Sequence[str], None] = 'e7f2a4b6c8d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'bands',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('audio_sample', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # Add the new foreign key column (nullable for now) so existing rows can be
    # backfilled before the old ``band`` string column is dropped.
    op.add_column('events', sa.Column('band_id', sa.UUID(), nullable=True))

    bind = op.get_bind()
    band_names = [
        row[0]
        for row in bind.execute(
            sa.text("SELECT DISTINCT band FROM events WHERE band IS NOT NULL")
        )
    ]
    for name in band_names:
        band_id = str(uuid.uuid4())
        bind.execute(
            sa.text("INSERT INTO bands (id, name) VALUES (:id, :name)"),
            {"id": band_id, "name": name},
        )
        bind.execute(
            sa.text("UPDATE events SET band_id = :band_id WHERE band = :name"),
            {"band_id": band_id, "name": name},
        )

    # Requires SQLite >= 3.35 (ALTER TABLE ... DROP COLUMN). ``band_id`` is left
    # nullable to avoid a full table rebuild (batch mode) which would drop the
    # foreign keys of ``interested_events`` / ``observed_events`` pointing here.
    op.drop_column('events', 'band')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('events', sa.Column('band', sa.String(), nullable=True))

    bind = op.get_bind()
    for band_id, name in bind.execute(sa.text("SELECT id, name FROM bands")):
        bind.execute(
            sa.text("UPDATE events SET band = :name WHERE band_id = :band_id"),
            {"name": name, "band_id": band_id},
        )

    op.drop_column('events', 'band_id')
    op.drop_table('bands')
