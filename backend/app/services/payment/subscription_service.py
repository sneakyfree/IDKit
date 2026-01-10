"""
Subscription Service

High-level subscription management service.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    PaymentMethod,
    Payment,
    PaymentStatus,
    Invoice,
    UsageRecord,
)
from app.models.user import User
from app.services.payment.stripe_service import stripe_service

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    High-level subscription management.

    Coordinates between database models and Stripe API.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.stripe = stripe_service

    # =========================================================================
    # Plans
    # =========================================================================

    async def get_plans(self, active_only: bool = True) -> list[SubscriptionPlan]:
        """Get all subscription plans."""
        query = select(SubscriptionPlan).order_by(SubscriptionPlan.display_order)

        if active_only:
            query = query.where(SubscriptionPlan.is_active == True)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_plan_by_id(self, plan_id: UUID) -> Optional[SubscriptionPlan]:
        """Get a plan by ID."""
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def get_plan_by_tier(self, tier: str) -> Optional[SubscriptionPlan]:
        """Get a plan by tier name."""
        result = await self.db.execute(
            select(SubscriptionPlan).where(
                and_(
                    SubscriptionPlan.tier == tier,
                    SubscriptionPlan.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    # =========================================================================
    # Customer Management
    # =========================================================================

    async def get_or_create_stripe_customer(self, user: User) -> str:
        """Get or create a Stripe customer for a user."""
        # Check if user already has a subscription with customer ID
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .where(Subscription.stripe_customer_id.isnot(None))
            .limit(1)
        )
        subscription = result.scalar_one_or_none()

        if subscription and subscription.stripe_customer_id:
            return subscription.stripe_customer_id

        # Create new Stripe customer
        customer = await self.stripe.create_customer(
            email=user.email,
            name=user.full_name,
            metadata={"user_id": str(user.id)},
        )

        return customer.id

    # =========================================================================
    # Subscriptions
    # =========================================================================

    async def get_active_subscription(self, user_id: UUID) -> Optional[Subscription]:
        """Get the user's active subscription."""
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIALING,
                ])
            )
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_subscription_by_stripe_id(
        self,
        stripe_subscription_id: str,
    ) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID."""
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        return result.scalar_one_or_none()

    async def create_subscription(
        self,
        user: User,
        plan: SubscriptionPlan,
        billing_interval: str = "monthly",
    ) -> dict:
        """
        Create a new subscription.

        Returns checkout session URL for client to complete payment.
        """
        # Get or create Stripe customer
        customer_id = await self.get_or_create_stripe_customer(user)

        # Get the price ID based on billing interval
        if billing_interval == "yearly":
            price_id = plan.stripe_price_id_yearly
        else:
            price_id = plan.stripe_price_id_monthly

        if not price_id:
            raise ValueError(f"No Stripe price configured for {plan.name} ({billing_interval})")

        # Create checkout session
        from app.config import settings

        session = await self.stripe.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=f"{settings.frontend_url}/settings/billing?success=true",
            cancel_url=f"{settings.frontend_url}/settings/billing?canceled=true",
            mode="subscription",
            trial_days=plan.trial_days,
            metadata={
                "user_id": str(user.id),
                "plan_id": str(plan.id),
                "billing_interval": billing_interval,
            },
        )

        return {
            "checkout_url": session.url,
            "session_id": session.id,
        }

    async def create_subscription_record(
        self,
        user_id: UUID,
        plan_id: UUID,
        stripe_subscription_id: str,
        stripe_customer_id: str,
        status: str,
        billing_interval: str,
        current_period_start: datetime,
        current_period_end: datetime,
        trial_start: Optional[datetime] = None,
        trial_end: Optional[datetime] = None,
    ) -> Subscription:
        """Create a subscription record in the database."""
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            status=status,
            billing_interval=billing_interval,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            trial_start=trial_start,
            trial_end=trial_end,
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        # Update user's subscription tier
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            plan = await self.get_plan_by_id(plan_id)
            if plan:
                user.subscription_tier = plan.tier
                await self.db.commit()

        logger.info(f"Created subscription {subscription.id} for user {user_id}")
        return subscription

    async def update_subscription_status(
        self,
        subscription: Subscription,
        status: str,
        cancel_at_period_end: bool = False,
        canceled_at: Optional[datetime] = None,
        current_period_start: Optional[datetime] = None,
        current_period_end: Optional[datetime] = None,
    ) -> Subscription:
        """Update subscription status."""
        subscription.status = status
        subscription.cancel_at_period_end = cancel_at_period_end

        if canceled_at:
            subscription.canceled_at = canceled_at

        if current_period_start:
            subscription.current_period_start = current_period_start

        if current_period_end:
            subscription.current_period_end = current_period_end

        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(f"Updated subscription {subscription.id} status to {status}")
        return subscription

    async def cancel_subscription(
        self,
        subscription: Subscription,
        at_period_end: bool = True,
    ) -> Subscription:
        """Cancel a subscription."""
        if subscription.stripe_subscription_id:
            await self.stripe.cancel_subscription(
                subscription.stripe_subscription_id,
                at_period_end=at_period_end,
            )

        if at_period_end:
            subscription.cancel_at_period_end = True
            subscription.canceled_at = datetime.now(timezone.utc)
        else:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(subscription)

        # Update user tier if immediate cancellation
        if not at_period_end:
            result = await self.db.execute(
                select(User).where(User.id == subscription.user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.subscription_tier = "free"
                await self.db.commit()

        logger.info(f"Canceled subscription {subscription.id}")
        return subscription

    async def resume_subscription(
        self,
        subscription: Subscription,
    ) -> Subscription:
        """Resume a canceled subscription."""
        if not subscription.cancel_at_period_end:
            raise ValueError("Subscription is not scheduled for cancellation")

        if subscription.stripe_subscription_id:
            await self.stripe.resume_subscription(subscription.stripe_subscription_id)

        subscription.cancel_at_period_end = False
        subscription.canceled_at = None

        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(f"Resumed subscription {subscription.id}")
        return subscription

    async def change_plan(
        self,
        subscription: Subscription,
        new_plan: SubscriptionPlan,
        billing_interval: Optional[str] = None,
    ) -> Subscription:
        """Change the subscription plan."""
        billing_interval = billing_interval or subscription.billing_interval

        # Get the new price ID
        if billing_interval == "yearly":
            new_price_id = new_plan.stripe_price_id_yearly
        else:
            new_price_id = new_plan.stripe_price_id_monthly

        if not new_price_id:
            raise ValueError(f"No Stripe price configured for {new_plan.name}")

        if subscription.stripe_subscription_id:
            await self.stripe.change_subscription_plan(
                subscription.stripe_subscription_id,
                new_price_id,
            )

        subscription.plan_id = new_plan.id
        subscription.billing_interval = billing_interval

        await self.db.commit()
        await self.db.refresh(subscription)

        # Update user tier
        result = await self.db.execute(
            select(User).where(User.id == subscription.user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.subscription_tier = new_plan.tier
            await self.db.commit()

        logger.info(
            f"Changed subscription {subscription.id} to plan {new_plan.name}"
        )
        return subscription

    # =========================================================================
    # Payment Methods
    # =========================================================================

    async def get_payment_methods(self, user_id: UUID) -> list[PaymentMethod]:
        """Get all payment methods for a user."""
        result = await self.db.execute(
            select(PaymentMethod)
            .where(PaymentMethod.user_id == user_id)
            .order_by(PaymentMethod.is_default.desc())
        )
        return list(result.scalars().all())

    async def add_payment_method(
        self,
        user: User,
        stripe_payment_method_id: str,
        set_as_default: bool = True,
    ) -> PaymentMethod:
        """Add a payment method for a user."""
        # Get Stripe customer ID
        customer_id = await self.get_or_create_stripe_customer(user)

        # Attach payment method to customer in Stripe
        pm = await self.stripe.attach_payment_method(
            stripe_payment_method_id,
            customer_id,
        )

        # Create database record
        payment_method = PaymentMethod(
            user_id=user.id,
            stripe_payment_method_id=stripe_payment_method_id,
            type=pm.type,
            card_brand=pm.card.brand if pm.card else None,
            card_last4=pm.card.last4 if pm.card else None,
            card_exp_month=pm.card.exp_month if pm.card else None,
            card_exp_year=pm.card.exp_year if pm.card else None,
            is_default=set_as_default,
        )

        if set_as_default:
            # Unset other defaults
            await self.db.execute(
                PaymentMethod.__table__.update()
                .where(PaymentMethod.user_id == user.id)
                .values(is_default=False)
            )
            # Set as default in Stripe
            await self.stripe.set_default_payment_method(
                customer_id,
                stripe_payment_method_id,
            )

        self.db.add(payment_method)
        await self.db.commit()
        await self.db.refresh(payment_method)

        logger.info(f"Added payment method for user {user.id}")
        return payment_method

    async def remove_payment_method(
        self,
        payment_method: PaymentMethod,
    ) -> None:
        """Remove a payment method."""
        # Detach from Stripe
        await self.stripe.detach_payment_method(
            payment_method.stripe_payment_method_id
        )

        # Delete from database
        await self.db.delete(payment_method)
        await self.db.commit()

        logger.info(f"Removed payment method {payment_method.id}")

    async def create_setup_intent(self, user: User) -> dict:
        """Create a setup intent for adding a new payment method."""
        customer_id = await self.get_or_create_stripe_customer(user)
        setup_intent = await self.stripe.create_setup_intent(
            customer_id,
            metadata={"user_id": str(user.id)},
        )

        return {
            "client_secret": setup_intent.client_secret,
            "setup_intent_id": setup_intent.id,
        }

    # =========================================================================
    # Billing Portal
    # =========================================================================

    async def create_billing_portal_session(self, user: User) -> str:
        """Create a Stripe billing portal session."""
        customer_id = await self.get_or_create_stripe_customer(user)

        from app.config import settings

        session = await self.stripe.create_billing_portal_session(
            customer_id,
            return_url=f"{settings.frontend_url}/settings/billing",
        )

        return session.url

    # =========================================================================
    # Payments & Invoices
    # =========================================================================

    async def get_payments(
        self,
        user_id: UUID,
        limit: int = 20,
    ) -> list[Payment]:
        """Get payments for a user."""
        result = await self.db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_invoices(
        self,
        user_id: UUID,
        limit: int = 20,
    ) -> list[Invoice]:
        """Get invoices for a user."""
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.user_id == user_id)
            .order_by(Invoice.invoice_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_payment_record(
        self,
        user_id: UUID,
        stripe_payment_intent_id: str,
        amount: int,
        currency: str,
        status: str,
        subscription_id: Optional[UUID] = None,
        stripe_invoice_id: Optional[str] = None,
        stripe_charge_id: Optional[str] = None,
        description: Optional[str] = None,
        receipt_url: Optional[str] = None,
    ) -> Payment:
        """Create a payment record."""
        payment = Payment(
            user_id=user_id,
            subscription_id=subscription_id,
            stripe_payment_intent_id=stripe_payment_intent_id,
            stripe_invoice_id=stripe_invoice_id,
            stripe_charge_id=stripe_charge_id,
            amount=amount,
            currency=currency,
            status=status,
            description=description,
            receipt_url=receipt_url,
        )

        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        logger.info(f"Created payment record {payment.id}")
        return payment

    async def create_invoice_record(
        self,
        user_id: UUID,
        stripe_invoice_id: str,
        invoice_number: Optional[str],
        status: str,
        amount_due: int,
        amount_paid: int,
        currency: str,
        invoice_date: datetime,
        subscription_id: Optional[UUID] = None,
        due_date: Optional[datetime] = None,
        paid_at: Optional[datetime] = None,
        hosted_invoice_url: Optional[str] = None,
        invoice_pdf: Optional[str] = None,
    ) -> Invoice:
        """Create an invoice record."""
        invoice = Invoice(
            user_id=user_id,
            subscription_id=subscription_id,
            stripe_invoice_id=stripe_invoice_id,
            invoice_number=invoice_number,
            status=status,
            amount_due=amount_due,
            amount_paid=amount_paid,
            amount_remaining=amount_due - amount_paid,
            currency=currency,
            invoice_date=invoice_date,
            due_date=due_date,
            paid_at=paid_at,
            hosted_invoice_url=hosted_invoice_url,
            invoice_pdf=invoice_pdf,
        )

        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)

        logger.info(f"Created invoice record {invoice.id}")
        return invoice

    # =========================================================================
    # Usage Tracking
    # =========================================================================

    async def record_usage(
        self,
        user_id: UUID,
        feature: str,
        quantity: int = 1,
        metadata: Optional[dict] = None,
    ) -> UsageRecord:
        """Record feature usage."""
        subscription = await self.get_active_subscription(user_id)

        record = UsageRecord(
            user_id=user_id,
            subscription_id=subscription.id if subscription else None,
            feature=feature,
            quantity=quantity,
            period_start=subscription.current_period_start if subscription else datetime.now(timezone.utc),
            period_end=subscription.current_period_end if subscription else datetime.now(timezone.utc),
            metadata=metadata or {},
        )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        return record

    async def get_usage_summary(
        self,
        user_id: UUID,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> dict[str, int]:
        """Get usage summary for a user."""
        query = select(UsageRecord).where(UsageRecord.user_id == user_id)

        if period_start:
            query = query.where(UsageRecord.period_start >= period_start)

        if period_end:
            query = query.where(UsageRecord.period_end <= period_end)

        result = await self.db.execute(query)
        records = result.scalars().all()

        # Aggregate by feature
        summary = {}
        for record in records:
            if record.feature not in summary:
                summary[record.feature] = 0
            summary[record.feature] += record.quantity

        return summary

    async def check_usage_limit(
        self,
        user_id: UUID,
        feature: str,
    ) -> dict:
        """Check if user has reached their usage limit for a feature."""
        subscription = await self.get_active_subscription(user_id)

        if not subscription:
            # Free tier limits
            limits = {"max_ai_twins": 0, "max_videos_per_month": 3}
        else:
            plan = await self.get_plan_by_id(subscription.plan_id)
            limits = plan.limits if plan else {}

        limit_key = f"max_{feature}"
        limit = limits.get(limit_key, 0)

        # Get current usage
        usage_summary = await self.get_usage_summary(
            user_id,
            period_start=subscription.current_period_start if subscription else None,
            period_end=subscription.current_period_end if subscription else None,
        )
        current_usage = usage_summary.get(feature, 0)

        return {
            "feature": feature,
            "limit": limit,
            "used": current_usage,
            "remaining": max(0, limit - current_usage),
            "exceeded": current_usage >= limit,
        }
