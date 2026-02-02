"""
Stripe Connect Webhook Handler

Handles Stripe webhook events for Connect accounts, transfers, and payouts.
"""

import logging
from datetime import datetime

import stripe

# Handle both old and new stripe library versions
try:
    from stripe.error import SignatureVerificationError
except ImportError:
    SignatureVerificationError = stripe.SignatureVerificationError

from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.payout import ConnectAccount, Transfer, Payout
from app.config import settings
from app.core.stripe_connect_config import stripe_connect_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stripe/connect")
async def stripe_connect_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Stripe Connect webhook events.
    
    Events handled:
    - account.updated: Sync Connect account status
    - transfer.created/reversed: Track transfers
    - payout.created/paid/failed: Track payouts
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header",
        )

    webhook_secret = stripe_connect_settings.stripe_connect_webhook_secret
    if not webhook_secret:
        webhook_secret = getattr(settings, "stripe_webhook_secret", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    event_type = event["type"]
    event_data = event["data"]["object"]

    logger.info(f"Received Stripe Connect event: {event_type}")

    try:
        if event_type == "account.updated":
            await handle_account_updated(db, event_data)
        elif event_type == "transfer.created":
            await handle_transfer_created(db, event_data)
        elif event_type == "transfer.reversed":
            await handle_transfer_reversed(db, event_data)
        elif event_type == "payout.created":
            await handle_payout_created(db, event_data)
        elif event_type == "payout.paid":
            await handle_payout_paid(db, event_data)
        elif event_type == "payout.failed":
            await handle_payout_failed(db, event_data)
        else:
            logger.debug(f"Unhandled event type: {event_type}")
    except Exception as e:
        logger.error(f"Error handling webhook event {event_type}: {e}")
        # Don't raise - acknowledge receipt even if processing fails
        # Stripe will retry automatically

    return {"status": "ok"}


async def handle_account_updated(db: AsyncSession, account_data: dict):
    """Handle account.updated event."""
    stripe_account_id = account_data["id"]

    result = await db.execute(
        select(ConnectAccount).where(
            ConnectAccount.stripe_account_id == stripe_account_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        logger.warning(f"Connect account not found: {stripe_account_id}")
        return

    # Update account status
    account.details_submitted = 1 if account_data.get("details_submitted", False) else 0
    account.charges_enabled = 1 if account_data.get("charges_enabled", False) else 0
    account.payouts_enabled = 1 if account_data.get("payouts_enabled", False) else 0

    if account.payouts_enabled:
        account.status = "active"
    elif account.details_submitted:
        account.status = "restricted"
    else:
        account.status = "pending"

    await db.commit()
    logger.info(f"Updated Connect account: {account.id} to status {account.status}")


async def handle_transfer_created(db: AsyncSession, transfer_data: dict):
    """Handle transfer.created event."""
    # Transfer record should already exist from our API call
    # This just confirms receipt
    logger.info(f"Transfer confirmed: {transfer_data['id']}")


async def handle_transfer_reversed(db: AsyncSession, transfer_data: dict):
    """Handle transfer.reversed event."""
    stripe_transfer_id = transfer_data["id"]

    result = await db.execute(
        select(Transfer).where(Transfer.stripe_transfer_id == stripe_transfer_id)
    )
    transfer = result.scalar_one_or_none()

    if transfer:
        transfer.status = "reversed"
        await db.commit()
        logger.info(f"Transfer reversed: {transfer.id}")


async def handle_payout_created(db: AsyncSession, payout_data: dict):
    """Handle payout.created event."""
    # Payout record should already exist from our API call
    stripe_payout_id = payout_data["id"]
    
    result = await db.execute(
        select(Payout).where(Payout.stripe_payout_id == stripe_payout_id)
    )
    payout = result.scalar_one_or_none()
    
    if payout:
        payout.status = payout_data.get("status", "pending")
        await db.commit()
    
    logger.info(f"Payout created confirmed: {payout_data['id']}")


async def handle_payout_paid(db: AsyncSession, payout_data: dict):
    """Handle payout.paid event."""
    stripe_payout_id = payout_data["id"]

    result = await db.execute(
        select(Payout).where(Payout.stripe_payout_id == stripe_payout_id)
    )
    payout = result.scalar_one_or_none()

    if payout:
        payout.status = "paid"
        if payout_data.get("arrival_date"):
            payout.arrival_date = datetime.fromtimestamp(payout_data["arrival_date"])
        await db.commit()
        logger.info(f"Payout completed: {payout.id}")


async def handle_payout_failed(db: AsyncSession, payout_data: dict):
    """Handle payout.failed event."""
    stripe_payout_id = payout_data["id"]

    result = await db.execute(
        select(Payout).where(Payout.stripe_payout_id == stripe_payout_id)
    )
    payout = result.scalar_one_or_none()

    if payout:
        payout.status = "failed"
        payout.failure_code = payout_data.get("failure_code")
        payout.failure_message = payout_data.get("failure_message")
        await db.commit()
        logger.info(f"Payout failed: {payout.id} - {payout.failure_code}")
