"""store the FashionCLIP anchor vector with each upload

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-20

With image files no longer persisted by default, the FashionCLIP anchor can no longer be
recomputed from a file on disk. Store it alongside the DINO vector at upload time.
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user_uploads", sa.Column("clip_embedding", sa.BLOB(), nullable=True))


def downgrade():
    with op.batch_alter_table("user_uploads") as batch_op:
        batch_op.drop_column("clip_embedding")
