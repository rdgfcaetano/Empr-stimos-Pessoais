"""initial schema

Revision ID: 20260906_0001
Revises:
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

revision = "20260906_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = sa.Enum("ADMIN", "PARTNER", name="userrole")
    interest_type = sa.Enum("MONTHLY", "DAILY", "BOTH", name="interesttype")
    loan_status = sa.Enum("OPEN", "PAID", "OVERDUE", "RENEGOTIATED", name="loanstatus")

    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", user_role, nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("clients", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("partner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("name", sa.String(140), nullable=False), sa.Column("phone", sa.String(40), nullable=False), sa.Column("address", sa.String(255)), sa.Column("notes", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_clients_partner_id", "clients", ["partner_id"])
    op.create_table("loans", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False), sa.Column("partner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("principal", sa.Numeric(12, 2), nullable=False), sa.Column("interest_rate", sa.Numeric(7, 4), nullable=False), sa.Column("interest_type", interest_type, nullable=False), sa.Column("loan_date", sa.Date(), nullable=False), sa.Column("due_date", sa.Date(), nullable=False), sa.Column("late_fee", sa.Numeric(12, 2), nullable=False), sa.Column("late_interest_rate", sa.Numeric(7, 4), nullable=False), sa.Column("status", loan_status, nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_loans_partner_id", "loans", ["partner_id"])
    op.create_table("payments", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("loan_id", sa.Integer(), sa.ForeignKey("loans.id"), nullable=False), sa.Column("responsible_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("paid_at", sa.Date(), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("notes", sa.Text()), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_payments_loan_id", "payments", ["loan_id"])
    op.create_table("audit_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("action", sa.String(80), nullable=False), sa.Column("entity", sa.String(80), nullable=False), sa.Column("entity_id", sa.Integer()), sa.Column("old_value", sa.Text()), sa.Column("new_value", sa.Text()), sa.Column("ip_address", sa.String(80)), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("notifications", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("title", sa.String(160), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("sessions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("token_jti", sa.String(80), nullable=False), sa.Column("ip_address", sa.String(80)), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("revoked_at", sa.DateTime()))
    op.create_index("ix_sessions_token_jti", "sessions", ["token_jti"], unique=True)


def downgrade() -> None:
    op.drop_table("sessions")
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("payments")
    op.drop_table("loans")
    op.drop_table("clients")
    op.drop_table("users")
