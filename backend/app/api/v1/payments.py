"""
Payment API Endpoints

Handles subscription management, payment methods, and billing.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, DB
from app.models.payment import (
    SubscriptionPlan,
    Subscription,
    PaymentMethod,
    Payment,
    Invoice,
    SubscriptionStatus,
)
from app.services.payment import StripeService, stripe_service
from app.services.payment.subscription_service import SubscriptionService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================

class PlanResponse(BaseModel):
    """Subscription plan response."""

    id: UUID
    name: str
    tier: str
    description: Optional[str]
    price_monthly: int
    price_yearly: int
    currency: str
    features: dict
    limits: dict
    trial_days: int
    is_popular: bool

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Subscription response."""

    id: UUID
    plan_id: UUID
    plan_name: str
    plan_tier: str
    status: str
    billing_interval: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentMethodResponse(BaseModel):
    """Payment method response."""

    id: UUID
    type: str
    card_brand: Optional[str]
    card_last4: Optional[str]
    card_exp_month: Optional[int]
    card_exp_year: Optional[int]
    is_default: bool

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Payment response."""

    id: UUID
    amount: int
    currency: str
    status: str
    description: Optional[str]
    receipt_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    """Invoice response."""

    id: UUID
    invoice_number: Optional[str]
    status: str
    amount_due: int
    amount_paid: int
    currency: str
    invoice_date: datetime
    due_date: Optional[datetime]
    paid_at: Optional[datetime]
    hosted_invoice_url: Optional[str]
    invoice_pdf: Optional[str]

    class Config:
        from_attributes = True


class CreateSubscriptionRequest(BaseModel):
    """Create subscription request."""

    plan_id: UUID
    billing_interval: str = Field(default="monthly", pattern="^(monthly|yearly)$")


class AddPaymentMethodRequest(BaseModel):
    """Add payment method request."""

    payment_method_id: str
    set_as_default: bool = True


class ChangePlanRequest(BaseModel):
    """Change plan request."""

    plan_id: UUID
    billing_interval: Optional[str] = None


class UsageLimitResponse(BaseModel):
    """Usage limit check response."""

    feature: str
    limit: int
    used: int
    remaining: int
    exceeded: bool


# =============================================================================
# Plans
# =============================================================================

@router.get("/plans", response_model=list[PlanResponse])
async def get_plans(db: DB):
    """Get all available subscription plans."""
    service = SubscriptionService(db)
    plans = await service.get_plans(active_only=True)
    return plans


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: UUID, db: DB):
    """Get a specific subscription plan."""
    service = SubscriptionService(db)
    plan = await service.get_plan_by_id(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    return plan


# =============================================================================
# Subscriptions
# =============================================================================

@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(user: CurrentUser, db: DB):
    """Get the current user's active subscription."""
    service = SubscriptionService(db)
    subscription = await service.get_active_subscription(user.id)

    if not subscription:
        return None

    plan = await service.get_plan_by_id(subscription.plan_id)

    return SubscriptionResponse(
        id=subscription.id,
        plan_id=subscription.plan_id,
        plan_name=plan.name if plan else "Unknown",
        plan_tier=plan.tier if plan else "free",
        status=subscription.status,
        billing_interval=subscription.billing_interval,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=subscription.canceled_at,
        trial_start=subscription.trial_start,
        trial_end=subscription.trial_end,
    )


@router.post("/subscription")
async def create_subscription(
    request: CreateSubscriptionRequest,
    user: CurrentUser,
    db: DB,
):
    """
    Create a new subscription.

    Returns a Stripe Checkout URL for the user to complete payment.
    """
    service = SubscriptionService(db)

    # Check if user already has an active subscription
    existing = await service.get_active_subscription(user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active subscription. Use the change plan endpoint instead.",
        )

    # Get the plan
    plan = await service.get_plan_by_id(request.plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    # Create checkout session
    result = await service.create_subscription(
        user=user,
        plan=plan,
        billing_interval=request.billing_interval,
    )

    return result


@router.post("/subscription/cancel")
async def cancel_subscription(
    at_period_end: bool = True,
    user: CurrentUser = None,
    db: DB = None,
):
    """Cancel the current subscription."""
    service = SubscriptionService(db)
    subscription = await service.get_active_subscription(user.id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )

    subscription = await service.cancel_subscription(
        subscription,
        at_period_end=at_period_end,
    )

    plan = await service.get_plan_by_id(subscription.plan_id)

    return SubscriptionResponse(
        id=subscription.id,
        plan_id=subscription.plan_id,
        plan_name=plan.name if plan else "Unknown",
        plan_tier=plan.tier if plan else "free",
        status=subscription.status,
        billing_interval=subscription.billing_interval,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=subscription.canceled_at,
        trial_start=subscription.trial_start,
        trial_end=subscription.trial_end,
    )


@router.post("/subscription/resume")
async def resume_subscription(user: CurrentUser, db: DB):
    """Resume a canceled subscription (if not yet ended)."""
    service = SubscriptionService(db)
    subscription = await service.get_active_subscription(user.id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )

    if not subscription.cancel_at_period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is not scheduled for cancellation",
        )

    subscription = await service.resume_subscription(subscription)
    plan = await service.get_plan_by_id(subscription.plan_id)

    return SubscriptionResponse(
        id=subscription.id,
        plan_id=subscription.plan_id,
        plan_name=plan.name if plan else "Unknown",
        plan_tier=plan.tier if plan else "free",
        status=subscription.status,
        billing_interval=subscription.billing_interval,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=subscription.canceled_at,
        trial_start=subscription.trial_start,
        trial_end=subscription.trial_end,
    )


@router.post("/subscription/change-plan")
async def change_plan(
    request: ChangePlanRequest,
    user: CurrentUser,
    db: DB,
):
    """Change the subscription plan."""
    service = SubscriptionService(db)
    subscription = await service.get_active_subscription(user.id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )

    new_plan = await service.get_plan_by_id(request.plan_id)
    if not new_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    subscription = await service.change_plan(
        subscription,
        new_plan,
        billing_interval=request.billing_interval,
    )

    return SubscriptionResponse(
        id=subscription.id,
        plan_id=subscription.plan_id,
        plan_name=new_plan.name,
        plan_tier=new_plan.tier,
        status=subscription.status,
        billing_interval=subscription.billing_interval,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=subscription.canceled_at,
        trial_start=subscription.trial_start,
        trial_end=subscription.trial_end,
    )


# =============================================================================
# Payment Methods
# =============================================================================

@router.get("/payment-methods", response_model=list[PaymentMethodResponse])
async def get_payment_methods(user: CurrentUser, db: DB):
    """Get all payment methods for the current user."""
    service = SubscriptionService(db)
    return await service.get_payment_methods(user.id)


@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def add_payment_method(
    request: AddPaymentMethodRequest,
    user: CurrentUser,
    db: DB,
):
    """Add a new payment method."""
    service = SubscriptionService(db)

    try:
        payment_method = await service.add_payment_method(
            user=user,
            stripe_payment_method_id=request.payment_method_id,
            set_as_default=request.set_as_default,
        )
        return payment_method
    except Exception as e:
        logger.error(f"Failed to add payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/payment-methods/{payment_method_id}")
async def remove_payment_method(
    payment_method_id: UUID,
    user: CurrentUser,
    db: DB,
):
    """Remove a payment method."""
    from sqlalchemy import select

    result = await db.execute(
        select(PaymentMethod).where(
            PaymentMethod.id == payment_method_id,
            PaymentMethod.user_id == user.id,
        )
    )
    payment_method = result.scalar_one_or_none()

    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found",
        )

    service = SubscriptionService(db)
    await service.remove_payment_method(payment_method)

    return {"message": "Payment method removed"}


@router.post("/payment-methods/setup-intent")
async def create_setup_intent(user: CurrentUser, db: DB):
    """Create a setup intent for adding a new payment method via Stripe.js."""
    service = SubscriptionService(db)
    result = await service.create_setup_intent(user)
    return result


# =============================================================================
# Billing Portal
# =============================================================================

@router.post("/billing-portal")
async def create_billing_portal(user: CurrentUser, db: DB):
    """Create a Stripe billing portal session."""
    service = SubscriptionService(db)
    url = await service.create_billing_portal_session(user)
    return {"url": url}


# =============================================================================
# Payments & Invoices
# =============================================================================

@router.get("/payments", response_model=list[PaymentResponse])
async def get_payments(
    user: CurrentUser,
    db: DB,
    limit: int = 20,
):
    """Get payment history."""
    service = SubscriptionService(db)
    return await service.get_payments(user.id, limit=limit)


@router.get("/invoices", response_model=list[InvoiceResponse])
async def get_invoices(
    user: CurrentUser,
    db: DB,
    limit: int = 20,
):
    """Get invoice history."""
    service = SubscriptionService(db)
    return await service.get_invoices(user.id, limit=limit)


# =============================================================================
# Usage
# =============================================================================

@router.get("/usage/{feature}", response_model=UsageLimitResponse)
async def check_usage_limit(
    feature: str,
    user: CurrentUser,
    db: DB,
):
    """Check usage limit for a specific feature."""
    service = SubscriptionService(db)
    return await service.check_usage_limit(user.id, feature)


@router.get("/usage")
async def get_usage_summary(user: CurrentUser, db: DB):
    """Get usage summary for the current billing period."""
    service = SubscriptionService(db)
    subscription = await service.get_active_subscription(user.id)

    if subscription:
        summary = await service.get_usage_summary(
            user.id,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
        )
    else:
        summary = await service.get_usage_summary(user.id)

    return {"usage": summary}


# =============================================================================
# Webhooks
# =============================================================================

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: DB):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header",
        )

    try:
        event = stripe_service.construct_webhook_event(
            payload,
            sig_header,
            settings.stripe_webhook_secret,
        )
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    service = SubscriptionService(db)

    # Handle different event types
    try:
        if event.type == "checkout.session.completed":
            await _handle_checkout_completed(event.data.object, service)

        elif event.type == "customer.subscription.created":
            await _handle_subscription_created(event.data.object, service)

        elif event.type == "customer.subscription.updated":
            await _handle_subscription_updated(event.data.object, service)

        elif event.type == "customer.subscription.deleted":
            await _handle_subscription_deleted(event.data.object, service)

        elif event.type == "invoice.paid":
            await _handle_invoice_paid(event.data.object, service)

        elif event.type == "invoice.payment_failed":
            await _handle_invoice_payment_failed(event.data.object, service)

        else:
            logger.info(f"Unhandled webhook event type: {event.type}")

    except Exception as e:
        logger.error(f"Error handling webhook {event.type}: {e}")
        # Return 200 to acknowledge receipt even if processing fails
        # This prevents Stripe from retrying

    return {"received": True}


async def _handle_checkout_completed(session, service: SubscriptionService):
    """Handle checkout.session.completed event."""
    logger.info(f"Checkout completed: {session.id}")

    # Get subscription details from session
    if session.mode == "subscription" and session.subscription:
        # The subscription.created event will handle creating the record
        pass


async def _handle_subscription_created(subscription, service: SubscriptionService):
    """Handle customer.subscription.created event."""
    logger.info(f"Subscription created: {subscription.id}")

    # Get metadata
    metadata = subscription.metadata or {}
    user_id = metadata.get("user_id")
    plan_id = metadata.get("plan_id")
    billing_interval = metadata.get("billing_interval", "monthly")

    if not user_id or not plan_id:
        logger.warning(f"Missing metadata in subscription {subscription.id}")
        return

    # Create subscription record
    await service.create_subscription_record(
        user_id=UUID(user_id),
        plan_id=UUID(plan_id),
        stripe_subscription_id=subscription.id,
        stripe_customer_id=subscription.customer,
        status=subscription.status,
        billing_interval=billing_interval,
        current_period_start=datetime.fromtimestamp(
            subscription.current_period_start,
            tz=timezone.utc,
        ),
        current_period_end=datetime.fromtimestamp(
            subscription.current_period_end,
            tz=timezone.utc,
        ),
        trial_start=datetime.fromtimestamp(subscription.trial_start, tz=timezone.utc)
        if subscription.trial_start else None,
        trial_end=datetime.fromtimestamp(subscription.trial_end, tz=timezone.utc)
        if subscription.trial_end else None,
    )


async def _handle_subscription_updated(subscription, service: SubscriptionService):
    """Handle customer.subscription.updated event."""
    logger.info(f"Subscription updated: {subscription.id}")

    db_subscription = await service.get_subscription_by_stripe_id(subscription.id)
    if not db_subscription:
        logger.warning(f"Subscription {subscription.id} not found in database")
        return

    await service.update_subscription_status(
        db_subscription,
        status=subscription.status,
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=datetime.fromtimestamp(subscription.canceled_at, tz=timezone.utc)
        if subscription.canceled_at else None,
        current_period_start=datetime.fromtimestamp(
            subscription.current_period_start,
            tz=timezone.utc,
        ),
        current_period_end=datetime.fromtimestamp(
            subscription.current_period_end,
            tz=timezone.utc,
        ),
    )


async def _handle_subscription_deleted(subscription, service: SubscriptionService):
    """Handle customer.subscription.deleted event."""
    logger.info(f"Subscription deleted: {subscription.id}")

    db_subscription = await service.get_subscription_by_stripe_id(subscription.id)
    if not db_subscription:
        logger.warning(f"Subscription {subscription.id} not found in database")
        return

    await service.update_subscription_status(
        db_subscription,
        status=SubscriptionStatus.CANCELED,
        canceled_at=datetime.now(timezone.utc),
    )


async def _handle_invoice_paid(invoice, service: SubscriptionService):
    """Handle invoice.paid event."""
    logger.info(f"Invoice paid: {invoice.id}")

    # Get user from customer
    metadata = invoice.metadata or {}
    user_id = metadata.get("user_id")

    if not user_id and invoice.subscription:
        # Try to get from subscription
        sub = await service.get_subscription_by_stripe_id(invoice.subscription)
        if sub:
            user_id = str(sub.user_id)

    if not user_id:
        logger.warning(f"Could not determine user for invoice {invoice.id}")
        return

    await service.create_invoice_record(
        user_id=UUID(user_id),
        stripe_invoice_id=invoice.id,
        invoice_number=invoice.number,
        status=invoice.status,
        amount_due=invoice.amount_due,
        amount_paid=invoice.amount_paid,
        currency=invoice.currency,
        invoice_date=datetime.fromtimestamp(invoice.created, tz=timezone.utc),
        paid_at=datetime.fromtimestamp(invoice.status_transitions.paid_at, tz=timezone.utc)
        if invoice.status_transitions.paid_at else None,
        hosted_invoice_url=invoice.hosted_invoice_url,
        invoice_pdf=invoice.invoice_pdf,
    )


async def _handle_invoice_payment_failed(invoice, service: SubscriptionService):
    """Handle invoice.payment_failed event."""
    logger.warning(f"Invoice payment failed: {invoice.id}")

    # Update subscription status to past_due if applicable
    if invoice.subscription:
        db_subscription = await service.get_subscription_by_stripe_id(
            invoice.subscription
        )
        if db_subscription:
            await service.update_subscription_status(
                db_subscription,
                status=SubscriptionStatus.PAST_DUE,
            )
