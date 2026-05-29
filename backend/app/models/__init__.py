"""
Database Models

Export all SQLAlchemy models for easy importing.
"""

from app.models.base import Base
from app.models.user import User, UserSettings, DataRequest, ConsentLog
from app.models.feed import (
    UserProfile,
    FeedPost,
    FeedLike,
    FeedComment,
    FeedSave,
    Follow,
    Hashtag,
)
from app.models.ai_twin import (
    AiTwin,
    TwinMediaUpload,
    AvatarConfig,
    VoiceConfig,
    TwinTrainingJob,
    TwinGeneratedAsset,
)
from app.models.social import (
    SocialAccount,
    SocialPost,
    PublishQueue,
    SocialComment,
    SocialDMConversation,
    SocialDMMessage,
    SocialAnalytics,
    SocialWebhookEvent,
    AnalyticsDaily,
)
# Import content BEFORE podcast (podcast references brand_voices from content)
from app.models.content import (
    ContentItem,
    BrandVoice,
)
from app.models.podcast import (
    Podcast,
    PodcastEpisode,
    PodcastClip,
    PodcastLiveSession,
    PodcastStatus,
)
from app.models.enterprise import (
    Organization,
    TeamMember,
    TeamInvite,
    SSOConfiguration,
    APIKey,
    AuditLog,
    ContentApproval,
)
from app.models.payout import (
    ConnectAccount,
    Transfer,
    Payout,
    ConnectAccountStatus,
    TransferStatus,
    PayoutStatus,
)
from app.models.roi import (
    ROIReport,
    CostEntry,
)
from app.models.agent_memory import (
    AgentMemory,
    AgentContext,
    GuardrailConfig,
    MemoryType,
)
from app.models.sponsorship import (
    Sponsorship,
    SponsorshipDeliverable,
)
from app.models.contract import (
    Contract,
    ContractTemplate,
    ContractDeliverable,
)
from app.models.tax import (
    TaxProfile,
    TaxDocument,
)
from app.models.listening import (
    ListeningQuery,
    ListeningMention,
)
from app.models.report import Report
from app.models.compliance import (
    ComplianceReport,
    ComplianceCheck,
    Backup,
    BackupSchedule,
)
from app.models.collaboration import (
    CollaborationProject,
    CollaborationMember,
    CollaborationMessage,
)
from app.models.revenue_sharing import (
    RevenueAgreement,
    RevenueDistribution,
)
from app.models.performance import PerformanceMetric

from app.models.agent import AgentTask, AgentActionLog, PendingApproval
from app.models.audit import AuditSnapshotRecord, VersionRecord, DeltaReportRecord
from app.models.intake import IntakeProgress, IntakeAnswer, ContradictionRecord, VerificationTask
from app.models.notification import NotificationType, Notification, NotificationSettings
from app.models.payment import SubscriptionPlan, Subscription, PaymentMethod, Payment, UsageRecord, Invoice
from app.models.revenue import BrandDealRecord, RevenueEntryRecord, PayoutRecord, PricingBenchmarkRecord
from app.models.scenario import SavedScenario, BlockerRecord, UnlockerProgress, SimulationRecord
from app.models.schedule import ScheduledPost
# NOTE: app/models/twin.py is intentionally NOT imported - dead duplicate of
# ai_twin.py (redefines ai_twins, collides). See state-of-union audit 2026-05-28.

__all__ = [
    "Base",
    "User",
    "UserSettings",
    "DataRequest",
    "ConsentLog",
    "UserProfile",
    "FeedPost",
    "FeedLike",
    "FeedComment",
    "FeedSave",
    "Follow",
    "Hashtag",
    "AiTwin",
    "TwinMediaUpload",
    "AvatarConfig",
    "VoiceConfig",
    "TwinTrainingJob",
    "TwinGeneratedAsset",
    "SocialAccount",
    "SocialPost",
    "PublishQueue",
    "SocialComment",
    "SocialDMConversation",
    "SocialDMMessage",
    "SocialAnalytics",
    "SocialWebhookEvent",
    "Podcast",
    "PodcastEpisode",
    "PodcastClip",
    "PodcastLiveSession",
    "PodcastStatus",
    "Organization",
    "TeamMember",
    "TeamInvite",
    "SSOConfiguration",
    "APIKey",
    "AuditLog",
    "ContentApproval",
    "ConnectAccount",
    "Transfer",
    "Payout",
    "ConnectAccountStatus",
    "TransferStatus",
    "PayoutStatus",
    "ROIReport",
    "CostEntry",
    # New models — gap closure
    "Sponsorship",
    "SponsorshipDeliverable",
    "Contract",
    "ContractTemplate",
    "ContractDeliverable",
    "TaxProfile",
    "TaxDocument",
    "ListeningQuery",
    "ListeningMention",
    "Report",
    "ComplianceReport",
    "ComplianceCheck",
    "Backup",
    "BackupSchedule",
    "CollaborationProject",
    "CollaborationMember",
    "CollaborationMessage",
    "RevenueAgreement",
    "RevenueDistribution",
    "PerformanceMetric",
    "AgentTask",
    "AgentActionLog",
    "PendingApproval",
    "AuditSnapshotRecord",
    "VersionRecord",
    "DeltaReportRecord",
    "IntakeProgress",
    "IntakeAnswer",
    "ContradictionRecord",
    "VerificationTask",
    "NotificationType",
    "Notification",
    "NotificationSettings",
    "SubscriptionPlan",
    "Subscription",
    "PaymentMethod",
    "Payment",
    "UsageRecord",
    "Invoice",
    "BrandDealRecord",
    "RevenueEntryRecord",
    "PayoutRecord",
    "PricingBenchmarkRecord",
    "SavedScenario",
    "BlockerRecord",
    "UnlockerProgress",
    "SimulationRecord",
    "ScheduledPost",
]


