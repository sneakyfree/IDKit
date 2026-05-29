"""
Payouts API

REST API endpoints for creator payout management via Stripe Connect.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.payout import ConnectAccount, Transfer, Payout
from app.schemas.payout import (
    ConnectAccountResponse,
    OnboardingLinkResponse,
    BalanceResponse,
    BalanceAmount,
    PayoutHistoryResponse,
    TransferResponse,
    PayoutResponse,
    InitiatePayoutRequest,
    InitiatePayoutResponse,
    AccountRequirements,
)
from app.services.payment.stripe_service import stripe_service
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/onboard", response_model=OnboardingLinkResponse)
async def start_onboarding(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start Stripe Connect onboarding for a creator.
    
    Returns a URL to redirect the user to for completing verification.
    """
    # Check if user already has a Connect account
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    existing_account = result.scalar_one_or_none()

    if existing_account and existing_account.payouts_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active payout account",
        )

    # Create or retrieve Stripe Connect account
    if existing_account:
        stripe_account_id = existing_account.stripe_account_id
    else:
        try:
            account_data = await stripe_service.create_connect_account(
                user_id=current_user.id,
                email=current_user.email,
            )
        except Exception as e:
            logger.error(f"Failed to create Connect account: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payout account",
            )

        new_account = ConnectAccount(
            id=str(uuid4()),
            user_id=current_user.id,
            stripe_account_id=account_data["account_id"],
        )
        db.add(new_account)
        await db.commit()
        stripe_account_id = account_data["account_id"]

    # Create onboarding link
    frontend_url = getattr(settings, "frontend_url", "http://localhost:3000")
    try:
        onboarding_url = await stripe_service.create_account_link(
            account_id=stripe_account_id,
            refresh_url=f"{frontend_url}/settings/payouts?refresh=true",
            return_url=f"{frontend_url}/settings/payouts?onboarding=complete",
        )
    except Exception as e:
        logger.error(f"Failed to create onboarding link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create onboarding link",
        )

    return OnboardingLinkResponse(url=onboarding_url)


@router.get("/account", response_model=Optional[ConnectAccountResponse])
async def get_account_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the status of the user's Connect account."""
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()

    if not account:
        return None

    # Fetch latest status from Stripe
    try:
        stripe_status = await stripe_service.get_connect_account_status(
            account.stripe_account_id
        )
    except Exception as e:
        logger.error(f"Failed to get Stripe account status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch account status",
        )

    # Update local record
    account.details_submitted = 1 if stripe_status["details_submitted"] else 0
    account.charges_enabled = 1 if stripe_status["charges_enabled"] else 0
    account.payouts_enabled = 1 if stripe_status["payouts_enabled"] else 0

    if stripe_status["payouts_enabled"]:
        account.status = "active"
    elif stripe_status["details_submitted"]:
        account.status = "restricted"
    else:
        account.status = "pending"

    await db.commit()
    await db.refresh(account)

    return ConnectAccountResponse(
        id=account.id,
        stripe_account_id=account.stripe_account_id,
        status=account.status,
        details_submitted=bool(account.details_submitted),
        charges_enabled=bool(account.charges_enabled),
        payouts_enabled=bool(account.payouts_enabled),
        country=account.country,
        default_currency=account.default_currency,
        requirements=AccountRequirements(**stripe_status.get("requirements", {})),
        created_at=account.created_at,
    )


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current balance for the user's Connect account."""
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payout account found",
        )

    try:
        balance = await stripe_service.get_connect_balance(account.stripe_account_id)
    except Exception as e:
        logger.error(f"Failed to get balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch balance",
        )

    total_available = sum(b["amount"] for b in balance["available"])
    total_pending = sum(b["amount"] for b in balance["pending"])

    return BalanceResponse(
        available=[
            BalanceAmount(amount_cents=b["amount"], currency=b["currency"])
            for b in balance["available"]
        ],
        pending=[
            BalanceAmount(amount_cents=b["amount"], currency=b["currency"])
            for b in balance["pending"]
        ],
        total_available_cents=total_available,
        total_pending_cents=total_pending,
    )


@router.get("/history", response_model=PayoutHistoryResponse)
async def get_payout_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    """Get transfer and payout history."""
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payout account found",
        )

    # Get transfers
    transfers_result = await db.execute(
        select(Transfer)
        .where(Transfer.connect_account_id == account.id)
        .order_by(Transfer.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transfers = transfers_result.scalars().all()

    # Get payouts
    payouts_result = await db.execute(
        select(Payout)
        .where(Payout.connect_account_id == account.id)
        .order_by(Payout.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    payouts = payouts_result.scalars().all()

    total_transferred = sum(
        t.amount_cents for t in transfers if t.status == "completed"
    )
    total_paid_out = sum(p.amount_cents for p in payouts if p.status == "paid")

    return PayoutHistoryResponse(
        transfers=[TransferResponse.model_validate(t) for t in transfers],
        payouts=[PayoutResponse.model_validate(p) for p in payouts],
        total_transferred_cents=total_transferred,
        total_paid_out_cents=total_paid_out,
    )


@router.post("/initiate", response_model=InitiatePayoutResponse)
async def initiate_payout(
    request: InitiatePayoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initiate a payout to the creator's bank account."""
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payout account found",
        )

    if not account.payouts_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payouts are not enabled for this account",
        )

    # Check balance
    try:
        balance = await stripe_service.get_connect_balance(account.stripe_account_id)
    except Exception as e:
        logger.error(f"Failed to get balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check balance",
        )

    available = sum(
        b["amount"] for b in balance["available"] if b["currency"] == request.currency
    )

    if available < request.amount_cents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Available: {available} cents",
        )

    # Create payout
    try:
        payout_data = await stripe_service.create_connect_payout(
            account_id=account.stripe_account_id,
            amount_cents=request.amount_cents,
            currency=request.currency,
        )
    except Exception as e:
        logger.error(f"Failed to create payout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate payout",
        )

    # Record in database
    payout = Payout(
        id=str(uuid4()),
        connect_account_id=account.id,
        stripe_payout_id=payout_data["payout_id"],
        amount_cents=payout_data["amount"],
        currency=payout_data["currency"],
        status=payout_data["status"],
        arrival_date=(
            datetime.fromtimestamp(payout_data["arrival_date"])
            if payout_data.get("arrival_date")
            else None
        ),
    )
    db.add(payout)
    await db.commit()

    return InitiatePayoutResponse(
        payout_id=payout.id,
        amount_cents=payout.amount_cents,
        currency=payout.currency,
        status=payout.status,
        estimated_arrival=payout.arrival_date,
    )


@router.get("/dashboard-link")
async def get_dashboard_link(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a link to the Stripe Express Dashboard."""
    result = await db.execute(
        select(ConnectAccount).where(ConnectAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payout account found",
        )

    if not account.details_submitted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete account setup first",
        )

    try:
        url = await stripe_service.create_login_link(account.stripe_account_id)
        return {"url": url}
    except Exception as e:
        logger.error(f"Failed to create dashboard link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create dashboard link",
        )
