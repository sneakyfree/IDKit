"""Add GDPR compliance tables

Revision ID: 002_gdpr_tables
Revises: 001_initial_schema
Create Date: 2024-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_gdpr_tables'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User settings table
    op.create_table(
        'user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notification_preferences', postgresql.JSONB(), nullable=True),
        sa.Column('privacy_settings', postgresql.JSONB(), nullable=True),
        sa.Column('theme', sa.String(20), nullable=False, server_default='system'),
        sa.Column('language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='UTC'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id'),
    )

    # Data requests table (GDPR export/delete requests)
    op.create_table(
        'data_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('categories', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('download_url', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_data_requests_user_id', 'data_requests', ['user_id'])
    op.create_index('ix_data_requests_status', 'data_requests', ['status'])

    # Consent logs table (GDPR consent tracking)
    op.create_table(
        'consent_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('consent_type', sa.String(50), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_consent_logs_user_id', 'consent_logs', ['user_id'])
    op.create_index('ix_consent_logs_consent_type', 'consent_logs', ['consent_type'])

    # Rate limit tracking table
    op.create_table(
        'rate_limit_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('identifier', sa.String(255), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rate_limit_tracking_identifier', 'rate_limit_tracking', ['identifier'])
    op.create_index('ix_rate_limit_tracking_window', 'rate_limit_tracking', ['identifier', 'endpoint', 'window_start'])

    # Search history table
    op.create_table(
        'search_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('query', sa.String(200), nullable=False),
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('search_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_search_history_user_id', 'search_history', ['user_id'])
    op.create_index('ix_search_history_query', 'search_history', ['query'])
    op.create_index('ix_search_history_created_at', 'search_history', ['created_at'])


def downgrade() -> None:
    op.drop_table('search_history')
    op.drop_table('rate_limit_tracking')
    op.drop_table('consent_logs')
    op.drop_table('data_requests')
    op.drop_table('user_settings')
