"""Initial database schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================================================
    # CORE USER TABLES
    # ==========================================================================

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('username', sa.String(50), unique=True, nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('is_admin', sa.Boolean, default=False),
        sa.Column('subscription_tier', sa.String(50), default='free'),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('google_id', sa.String(255), nullable=True),
        sa.Column('apple_id', sa.String(255), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('suspended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('suspension_reason', sa.Text, nullable=True),
        sa.Column('suspension_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_google_id', 'users', ['google_id'])
    op.create_index('ix_users_apple_id', 'users', ['apple_id'])

    # User profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('avatar_url', sa.Text, nullable=True),
        sa.Column('cover_image_url', sa.Text, nullable=True),
        sa.Column('website_url', sa.Text, nullable=True),
        sa.Column('follower_count', sa.Integer, default=0),
        sa.Column('following_count', sa.Integer, default=0),
        sa.Column('post_count', sa.Integer, default=0),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('niche_tags', postgresql.JSONB, default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Refresh tokens
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('token', sa.String(500), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # ==========================================================================
    # SOCIAL FEED TABLES
    # ==========================================================================

    # Feed posts
    op.create_table(
        'feed_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('post_type', sa.String(50), nullable=False),
        sa.Column('content_text', sa.Text, nullable=True),
        sa.Column('media_urls', postgresql.JSONB, default=[]),
        sa.Column('thumbnail_url', sa.Text, nullable=True),
        sa.Column('view_count', sa.Integer, default=0),
        sa.Column('like_count', sa.Integer, default=0),
        sa.Column('comment_count', sa.Integer, default=0),
        sa.Column('share_count', sa.Integer, default=0),
        sa.Column('save_count', sa.Integer, default=0),
        sa.Column('engagement_score', sa.Float, default=0),
        sa.Column('viral_score', sa.Float, default=0),
        sa.Column('trending_score', sa.Float, default=0),
        sa.Column('hashtags', postgresql.JSONB, default=[]),
        sa.Column('mentions', postgresql.JSONB, default=[]),
        sa.Column('ai_generated', sa.Boolean, default=False),
        sa.Column('source_content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('visibility', sa.String(20), default='public'),
        sa.Column('is_pinned', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_feed_posts_user_id', 'feed_posts', ['user_id'])
    op.create_index('ix_feed_posts_created_at', 'feed_posts', ['created_at'])
    op.create_index('ix_feed_posts_visibility', 'feed_posts', ['visibility'])

    # Feed likes
    op.create_table(
        'feed_likes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('feed_posts.id', ondelete='CASCADE')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('post_id', 'user_id', name='uq_feed_likes_post_user'),
    )

    # Feed comments
    op.create_table(
        'feed_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('feed_posts.id', ondelete='CASCADE')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('parent_comment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('feed_comments.id'), nullable=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('like_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Feed saves
    op.create_table(
        'feed_saves',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('feed_posts.id', ondelete='CASCADE')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('collection_name', sa.String(100), default='Saved'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('post_id', 'user_id', 'collection_name', name='uq_feed_saves_post_user_collection'),
    )

    # Follows
    op.create_table(
        'follows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('follower_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('following_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('follower_id', 'following_id', name='uq_follows_follower_following'),
    )

    # Hashtags
    op.create_table(
        'hashtags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tag', sa.String(100), unique=True, nullable=False),
        sa.Column('post_count', sa.Integer, default=0),
        sa.Column('trending_score', sa.Float, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # ==========================================================================
    # AI TWIN TABLES
    # ==========================================================================

    # AI Twins
    op.create_table(
        'ai_twins',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('avatar_id', sa.String(255), nullable=True),
        sa.Column('voice_id', sa.String(255), nullable=True),
        sa.Column('avatar_provider', sa.String(50), nullable=True),
        sa.Column('voice_provider', sa.String(50), nullable=True),
        sa.Column('avatar_url', sa.Text, nullable=True),
        sa.Column('personality_config', postgresql.JSONB, default={}),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('media_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Media uploads
    op.create_table(
        'media_uploads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('storage_key', sa.Text, nullable=False),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('file_size', sa.BigInteger, nullable=True),
        sa.Column('media_type', sa.String(50), nullable=True),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # GPU Jobs
    op.create_table(
        'gpu_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('queue_name', sa.String(50), default='default'),
        sa.Column('task_name', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('priority', sa.Integer, default=0),
        sa.Column('args', postgresql.JSONB, default={}),
        sa.Column('result', postgresql.JSONB, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('retries', sa.Integer, default=0),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('instance_id', sa.String(255), nullable=True),
        sa.Column('cost_cents', sa.Integer, default=0),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_gpu_jobs_status', 'gpu_jobs', ['status'])
    op.create_index('ix_gpu_jobs_user_id', 'gpu_jobs', ['user_id'])

    # ==========================================================================
    # CONTENT TABLES
    # ==========================================================================

    # Brand voices
    op.create_table(
        'brand_voices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('tone', sa.String(50), nullable=True),
        sa.Column('style_guidelines', sa.Text, nullable=True),
        sa.Column('vocabulary', postgresql.JSONB, default=[]),
        sa.Column('examples', postgresql.JSONB, default=[]),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Content items
    op.create_table(
        'content_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('media_urls', postgresql.JSONB, default=[]),
        sa.Column('thumbnail_url', sa.Text, nullable=True),
        sa.Column('brand_voice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('brand_voices.id'), nullable=True),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('platform_data', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # ==========================================================================
    # PODCAST TABLES
    # ==========================================================================

    # Podcasts
    op.create_table(
        'podcasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('cover_art_url', sa.Text, nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('host_type', sa.String(20), default='user'),
        sa.Column('ai_twin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ai_twins.id'), nullable=True),
        sa.Column('brand_voice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('brand_voices.id'), nullable=True),
        sa.Column('rss_feed_url', sa.Text, nullable=True),
        sa.Column('episode_count', sa.Integer, default=0),
        sa.Column('subscriber_count', sa.Integer, default=0),
        sa.Column('total_plays', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Podcast episodes
    op.create_table(
        'podcast_episodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('podcast_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('podcasts.id', ondelete='CASCADE')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('episode_number', sa.Integer, nullable=True),
        sa.Column('season_number', sa.Integer, default=1),
        sa.Column('script', sa.Text, nullable=True),
        sa.Column('show_notes', sa.Text, nullable=True),
        sa.Column('transcript', sa.Text, nullable=True),
        sa.Column('audio_url', sa.Text, nullable=True),
        sa.Column('video_url', sa.Text, nullable=True),
        sa.Column('thumbnail_url', sa.Text, nullable=True),
        sa.Column('chapters', postgresql.JSONB, default=[]),
        sa.Column('host_type', sa.String(20), default='user'),
        sa.Column('ai_twin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ai_twins.id'), nullable=True),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('publish_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_published', sa.Boolean, default=False),
        sa.Column('play_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # ==========================================================================
    # PAYMENT TABLES
    # ==========================================================================

    # Subscription plans
    op.create_table(
        'subscription_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('tier', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('price_monthly', sa.Integer, nullable=False),
        sa.Column('price_yearly', sa.Integer, nullable=True),
        sa.Column('stripe_product_id', sa.String(255), nullable=True),
        sa.Column('stripe_price_id_monthly', sa.String(255), nullable=True),
        sa.Column('stripe_price_id_yearly', sa.String(255), nullable=True),
        sa.Column('features', postgresql.JSONB, default=[]),
        sa.Column('limits', postgresql.JSONB, default={}),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscription_plans.id')),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean, default=False),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Payments
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(255), nullable=True),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(10), default='usd'),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # ==========================================================================
    # NOTIFICATION TABLES
    # ==========================================================================

    # Notifications
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('data', postgresql.JSONB, default={}),
        sa.Column('is_read', sa.Boolean, default=False),
        sa.Column('action_url', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])

    # ==========================================================================
    # MODERATION TABLES
    # ==========================================================================

    # Moderation reports
    op.create_table(
        'moderation_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('reason', sa.String(100), nullable=False),
        sa.Column('details', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action_taken', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_moderation_reports_status', 'moderation_reports', ['status'])

    # Moderation logs
    op.create_table(
        'moderation_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('content_type', sa.String(50), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('reason', sa.String(100), nullable=True),
        sa.Column('automated', sa.Boolean, default=False),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # ==========================================================================
    # ADMIN TABLES
    # ==========================================================================

    # Admin audit log
    op.create_table(
        'admin_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=True),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB, default={}),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_admin_audit_log_admin_id', 'admin_audit_log', ['admin_id'])
    op.create_index('ix_admin_audit_log_action', 'admin_audit_log', ['action'])

    # Feature flags
    op.create_table(
        'feature_flags',
        sa.Column('name', sa.String(100), primary_key=True),
        sa.Column('enabled', sa.Boolean, default=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('rollout_percentage', sa.Integer, default=100),
        sa.Column('user_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # Announcements
    op.create_table(
        'announcements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('type', sa.String(50), default='info'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('target_audience', sa.String(50), default='all'),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    # ==========================================================================
    # SOCIAL ACCOUNTS TABLES
    # ==========================================================================

    # Social accounts (external platform connections)
    op.create_table(
        'social_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('platform_user_id', sa.String(255), nullable=False),
        sa.Column('platform_username', sa.String(255), nullable=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.Text, nullable=True),
        sa.Column('access_token', sa.Text, nullable=True),
        sa.Column('refresh_token', sa.Text, nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scopes', postgresql.JSONB, default=[]),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('user_id', 'platform', 'platform_user_id', name='uq_social_accounts_user_platform'),
    )

    # WebSocket sessions (for tracking)
    op.create_table(
        'websocket_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('connection_id', sa.String(255), nullable=False),
        sa.Column('rooms', postgresql.ARRAY(sa.String(255)), default=[]),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('last_active', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('websocket_sessions')
    op.drop_table('social_accounts')
    op.drop_table('announcements')
    op.drop_table('feature_flags')
    op.drop_table('admin_audit_log')
    op.drop_table('moderation_logs')
    op.drop_table('moderation_reports')
    op.drop_table('notifications')
    op.drop_table('payments')
    op.drop_table('subscriptions')
    op.drop_table('subscription_plans')
    op.drop_table('podcast_episodes')
    op.drop_table('podcasts')
    op.drop_table('content_items')
    op.drop_table('brand_voices')
    op.drop_table('gpu_jobs')
    op.drop_table('media_uploads')
    op.drop_table('ai_twins')
    op.drop_table('hashtags')
    op.drop_table('follows')
    op.drop_table('feed_saves')
    op.drop_table('feed_comments')
    op.drop_table('feed_likes')
    op.drop_table('feed_posts')
    op.drop_table('refresh_tokens')
    op.drop_table('user_profiles')
    op.drop_table('users')
