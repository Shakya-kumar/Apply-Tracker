"""Add tenant-aware accounts and revocable sessions."""
from alembic import op
import sqlalchemy as sa

revision = "0001_auth_tenants"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("tenants", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(160), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("email_verified_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("email"))
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("memberships", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(32), nullable=False), sa.UniqueConstraint("tenant_id", "user_id", name="uq_membership_tenant_user"))
    op.create_index("ix_memberships_tenant_id", "memberships", ["tenant_id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_table("user_sessions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("token_digest", sa.String(64), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("token_digest"))
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_token_digest", "user_sessions", ["token_digest"])


def downgrade() -> None:
    op.drop_table("user_sessions")
    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_index("ix_memberships_tenant_id", table_name="memberships")
    op.drop_table("memberships")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("tenants")
