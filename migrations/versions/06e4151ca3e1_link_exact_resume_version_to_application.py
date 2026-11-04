"""link exact resume version to application

Revision ID: 06e4151ca3e1
Revises: b9f598aa6529
Create Date: 2026-11-04 13:38:57.001183
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '06e4151ca3e1'
down_revision: Union[str, None] = 'b9f598aa6529'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    with op.batch_alter_table("applications") as batch:
        batch.add_column(sa.Column("resume_version_id", sa.Integer(), nullable=True))
        batch.create_index("ix_applications_resume_version_id", ["resume_version_id"], unique=False)
        batch.create_foreign_key("fk_applications_resume_version", "resume_versions", ["resume_version_id"], ["id"], ondelete="SET NULL")

def downgrade() -> None:
    with op.batch_alter_table("applications") as batch:
        batch.drop_constraint("fk_applications_resume_version", type_="foreignkey")
        batch.drop_index("ix_applications_resume_version_id")
        batch.drop_column("resume_version_id")
