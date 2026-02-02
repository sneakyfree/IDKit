"""
Intake Service

Core business logic for TurboTax-style onboarding flow.
Handles flow configuration, response processing, and progress tracking.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intake import (
    ContradictionRecord,
    IntakeAnswer,
    IntakeProgress,
    VerificationTask,
)
from app.schemas.intake import (
    ConditionalLogic,
    IntakeFlow,
    IntakeQuestion,
    IntakeSection,
    QuestionType,
    ValidationRule,
)
from app.schemas.source_labeling import DataSourceType
from app.services.contradiction_engine import ContradictionEngine


# Default intake flow configuration
DEFAULT_INTAKE_FLOW = IntakeFlow(
    flow_id="creator_onboarding_v1",
    version="1.0",
    title="Creator Profile Setup",
    description="Let's get to know you and your creator journey",
    estimated_minutes=5,
    sections=[
        IntakeSection(
            id="profile_basics",
            title="Basic Information",
            description="Tell us about yourself",
            icon="user",
            questions=[
                IntakeQuestion(
                    id="creator_name",
                    type=QuestionType.TEXT,
                    label="What name do you go by as a creator?",
                    placeholder="Your creator name or brand",
                    required=True,
                    validation=ValidationRule(min_length=2, max_length=100),
                ),
                IntakeQuestion(
                    id="primary_niche",
                    type=QuestionType.SELECT,
                    label="What's your primary content niche?",
                    required=True,
                    options=[
                        "Tech & Gadgets",
                        "Beauty & Fashion",
                        "Fitness & Health",
                        "Gaming",
                        "Finance & Business",
                        "Lifestyle & Vlog",
                        "Food & Cooking",
                        "Travel",
                        "Education",
                        "Entertainment",
                        "Other",
                    ],
                ),
                IntakeQuestion(
                    id="secondary_niches",
                    type=QuestionType.MULTI_SELECT,
                    label="Any secondary niches?",
                    description="Select all that apply",
                    options=[
                        "Tech", "Beauty", "Fitness", "Gaming", "Finance",
                        "Lifestyle", "Food", "Travel", "Education", "Entertainment",
                    ],
                ),
            ],
        ),
        IntakeSection(
            id="platforms",
            title="Your Platforms",
            description="Where do you create content?",
            icon="share",
            questions=[
                IntakeQuestion(
                    id="primary_platform",
                    type=QuestionType.SELECT,
                    label="What's your main platform?",
                    required=True,
                    options=[
                        "YouTube",
                        "TikTok",
                        "Instagram",
                        "Twitter/X",
                        "LinkedIn",
                        "Podcast",
                        "Blog/Website",
                    ],
                ),
                IntakeQuestion(
                    id="other_platforms",
                    type=QuestionType.MULTI_SELECT,
                    label="Which other platforms do you use?",
                    options=[
                        "YouTube", "TikTok", "Instagram", "Twitter/X",
                        "LinkedIn", "Facebook", "Twitch", "Podcast",
                    ],
                ),
                IntakeQuestion(
                    id="connect_accounts",
                    type=QuestionType.OAUTH_CONNECT,
                    label="Connect your social accounts",
                    description="This helps us verify your stats and provide better insights",
                    help_text="We'll never post without your permission",
                ),
            ],
        ),
        IntakeSection(
            id="audience_metrics",
            title="Your Audience",
            description="Help us understand your reach",
            icon="users",
            questions=[
                IntakeQuestion(
                    id="total_followers",
                    type=QuestionType.NUMBER,
                    label="Approximately how many total followers do you have?",
                    description="Across all platforms combined",
                    validation=ValidationRule(min=0, max=1000000000),
                    can_verify_via_api=True,
                    uncertainty_path="verify_via_oauth",
                ),
                IntakeQuestion(
                    id="monthly_views",
                    type=QuestionType.NUMBER,
                    label="Estimated monthly views/impressions?",
                    validation=ValidationRule(min=0),
                    allow_unsure=True,
                    uncertainty_path="skip",
                ),
                IntakeQuestion(
                    id="engagement_rate",
                    type=QuestionType.PERCENT,
                    label="What's your typical engagement rate?",
                    tooltip="Likes + comments divided by followers",
                    allow_unsure=True,
                    uncertainty_path="calculate_from_api",
                ),
            ],
        ),
        IntakeSection(
            id="revenue_goals",
            title="Revenue & Goals",
            description="Let's understand your business goals",
            icon="dollar-sign",
            questions=[
                IntakeQuestion(
                    id="current_monthly_income",
                    type=QuestionType.CURRENCY,
                    label="Current monthly creator income (approximate)",
                    allow_unsure=True,
                ),
                IntakeQuestion(
                    id="income_goal",
                    type=QuestionType.CURRENCY,
                    label="What's your monthly income goal?",
                    required=True,
                ),
                IntakeQuestion(
                    id="income_sources",
                    type=QuestionType.MULTI_SELECT,
                    label="Which income sources are you interested in?",
                    options=[
                        "Brand Deals & Sponsorships",
                        "Affiliate Marketing",
                        "Subscriptions (Patreon, etc.)",
                        "Digital Products (courses, ebooks)",
                        "Merchandise",
                        "Platform Ad Revenue",
                        "Consulting/Coaching",
                    ],
                ),
            ],
        ),
        IntakeSection(
            id="content_style",
            title="Content Preferences",
            description="How do you like to create?",
            icon="video",
            questions=[
                IntakeQuestion(
                    id="posting_frequency",
                    type=QuestionType.SELECT,
                    label="How often do you typically post?",
                    options=[
                        "Multiple times daily",
                        "Once daily",
                        "Several times a week",
                        "Once a week",
                        "A few times a month",
                        "Irregularly",
                    ],
                ),
                IntakeQuestion(
                    id="content_types",
                    type=QuestionType.MULTI_SELECT,
                    label="What types of content do you create?",
                    options=[
                        "Short-form video (TikTok, Reels, Shorts)",
                        "Long-form video (YouTube)",
                        "Livestreams",
                        "Photos/Graphics",
                        "Written posts/Blogs",
                        "Audio/Podcasts",
                    ],
                ),
                IntakeQuestion(
                    id="ai_interest",
                    type=QuestionType.BOOLEAN,
                    label="Are you interested in using AI tools to create content?",
                    help_text="Like AI avatars, voice cloning, and generated content",
                ),
            ],
        ),
    ],
)


class IntakeService:
    """
    Service for managing the TurboTax-style intake flow.
    
    Responsibilities:
    - Load/configure intake flows
    - Process and validate user responses
    - Track onboarding progress
    - Trigger contradiction detection
    - Generate verification tasks for uncertain data
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.contradiction_engine = ContradictionEngine(db)

    async def get_intake_flow(
        self,
        flow_id: str = "creator_onboarding_v1",
    ) -> IntakeFlow:
        """
        Get intake flow configuration.
        
        Future: Load from database for A/B testing different flows.
        """
        # For now, return default flow
        if flow_id == "creator_onboarding_v1":
            return DEFAULT_INTAKE_FLOW

        return DEFAULT_INTAKE_FLOW

    async def get_or_create_progress(
        self,
        user_id: UUID,
        flow_id: str = "creator_onboarding_v1",
    ) -> IntakeProgress:
        """Get existing progress or create new one."""
        result = await self.db.execute(
            select(IntakeProgress).where(
                IntakeProgress.user_id == user_id,
                IntakeProgress.flow_id == flow_id,
            )
        )
        progress = result.scalar_one_or_none()

        if progress:
            return progress

        # Create new progress
        flow = await self.get_intake_flow(flow_id)
        progress = IntakeProgress(
            user_id=user_id,
            flow_id=flow_id,
            flow_version=flow.version,
            current_section=flow.sections[0].id if flow.sections else "profile_basics",
            total_sections=len(flow.sections),
            started_at=datetime.utcnow(),
        )

        self.db.add(progress)
        await self.db.flush()
        return progress

    async def process_section_response(
        self,
        user_id: UUID,
        section_id: str,
        answers: list[dict[str, Any]],
    ) -> IntakeProgress:
        """
        Process answers for a section.
        
        Args:
            user_id: The user's ID
            section_id: Which section is being submitted
            answers: List of {question_id, value, is_unsure, ...}
        """
        progress = await self.get_or_create_progress(user_id)
        flow = await self.get_intake_flow(progress.flow_id)

        # Find the section
        section = next(
            (s for s in flow.sections if s.id == section_id),
            None
        )
        if not section:
            raise ValueError(f"Section {section_id} not found")

        # Process each answer
        for answer_data in answers:
            question_id = answer_data["question_id"]
            value = answer_data.get("value")
            is_unsure = answer_data.get("is_unsure", False)

            # Validate against question config
            question = next(
                (q for q in section.questions if q.id == question_id),
                None
            )
            if not question:
                continue

            # Determine source and confidence
            source = DataSourceType.USER_INPUT
            confidence = 1.0 if not is_unsure else 0.5

            # Check for existing answer
            existing = await self.db.execute(
                select(IntakeAnswer).where(
                    IntakeAnswer.progress_id == progress.id,
                    IntakeAnswer.question_id == question_id,
                )
            )
            existing_answer = existing.scalar_one_or_none()

            if existing_answer:
                # Update existing
                existing_answer.value = value
                existing_answer.is_unsure = is_unsure
                existing_answer.confidence = confidence
                existing_answer.updated_at = datetime.utcnow()
            else:
                # Create new
                answer = IntakeAnswer(
                    progress_id=progress.id,
                    question_id=question_id,
                    section_id=section_id,
                    value=value,
                    source=source.value,
                    confidence=confidence,
                    is_unsure=is_unsure,
                    needs_verification=is_unsure and question.uncertainty_path == "verify_via_oauth",
                )
                self.db.add(answer)

        # Update progress
        if section_id not in (progress.completed_sections or []):
            completed = progress.completed_sections or []
            completed.append(section_id)
            progress.completed_sections = completed

        progress.percent_complete = (
            len(progress.completed_sections) / progress.total_sections * 100
        )

        # Move to next section
        section_ids = [s.id for s in flow.sections]
        current_idx = section_ids.index(section_id)
        if current_idx + 1 < len(section_ids):
            progress.current_section = section_ids[current_idx + 1]
        else:
            progress.completed_at = datetime.utcnow()

        await self.db.flush()
        return progress

    async def get_section_answers(
        self,
        user_id: UUID,
        section_id: str,
    ) -> list[IntakeAnswer]:
        """Get all answers for a specific section."""
        progress = await self.get_or_create_progress(user_id)

        result = await self.db.execute(
            select(IntakeAnswer).where(
                IntakeAnswer.progress_id == progress.id,
                IntakeAnswer.section_id == section_id,
            )
        )
        return list(result.scalars().all())

    async def verify_with_api_data(
        self,
        user_id: UUID,
        api_data: dict[str, Any],
        field_labels: Optional[dict[str, str]] = None,
    ) -> list[ContradictionRecord]:
        """
        Cross-check user answers against API-verified data.
        
        Returns list of detected contradictions.
        """
        progress = await self.get_or_create_progress(user_id)
        field_labels = field_labels or {}

        # Get all user answers
        result = await self.db.execute(
            select(IntakeAnswer).where(
                IntakeAnswer.progress_id == progress.id,
            )
        )
        answers = result.scalars().all()

        # Build user data dict
        user_data = {a.question_id: a.value for a in answers}

        # Detect contradictions
        alerts = await self.contradiction_engine.detect_contradictions(
            user_id=user_id,
            user_data=user_data,
            api_data=api_data,
            field_labels=field_labels,
        )

        # Save detected contradictions
        records = []
        for alert in alerts:
            label = field_labels.get(alert.field_name, alert.field_name)
            record = await self.contradiction_engine.save_contradiction(
                user_id=user_id,
                alert=alert,
                field_label=label,
            )
            records.append(record)

        return records

    async def get_pending_verifications(
        self,
        user_id: UUID,
    ) -> list[VerificationTask]:
        """Get all pending verification tasks for a user."""
        result = await self.db.execute(
            select(VerificationTask).where(
                VerificationTask.user_id == user_id,
                VerificationTask.is_completed == False,  # noqa: E712
            ).order_by(
                VerificationTask.priority.desc(),
                VerificationTask.created_at,
            )
        )
        return list(result.scalars().all())

    async def complete_intake(
        self,
        user_id: UUID,
    ) -> IntakeProgress:
        """Mark intake as complete."""
        progress = await self.get_or_create_progress(user_id)
        progress.completed_at = datetime.utcnow()
        progress.percent_complete = 100.0
        await self.db.flush()
        return progress

    async def reset_intake(
        self,
        user_id: UUID,
    ) -> IntakeProgress:
        """Reset intake progress (for testing or re-onboarding)."""
        progress = await self.get_or_create_progress(user_id)
        
        # Delete existing answers
        await self.db.execute(
            select(IntakeAnswer).where(
                IntakeAnswer.progress_id == progress.id
            )
        )
        
        # Reset progress
        flow = await self.get_intake_flow(progress.flow_id)
        progress.current_section = flow.sections[0].id if flow.sections else "profile_basics"
        progress.completed_sections = []
        progress.percent_complete = 0.0
        progress.completed_at = None
        progress.started_at = datetime.utcnow()

        await self.db.flush()
        return progress
