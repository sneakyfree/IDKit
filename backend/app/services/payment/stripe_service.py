"""
Stripe Service

Low-level Stripe API integration.
"""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import stripe
from stripe.error import StripeError

from app.config import settings

logger = logging.getLogger(__name__)


class StripeService:
    """
    Low-level Stripe API wrapper.

    Handles direct communication with Stripe API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.stripe_secret_key
        stripe.api_key = self.api_key

    # =========================================================================
    # Customers
    # =========================================================================

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> stripe.Customer:
        """Create a Stripe customer."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
            )
            logger.info(f"Created Stripe customer: {customer.id}")
            return customer
        except StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise

    async def get_customer(self, customer_id: str) -> Optional[stripe.Customer]:
        """Get a Stripe customer by ID."""
        try:
            return stripe.Customer.retrieve(customer_id)
        except StripeError as e:
            logger.error(f"Failed to retrieve customer {customer_id}: {e}")
            return None

    async def update_customer(
        self,
        customer_id: str,
        **kwargs,
    ) -> stripe.Customer:
        """Update a Stripe customer."""
        try:
            customer = stripe.Customer.modify(customer_id, **kwargs)
            logger.info(f"Updated Stripe customer: {customer_id}")
            return customer
        except StripeError as e:
            logger.error(f"Failed to update customer {customer_id}: {e}")
            raise

    async def delete_customer(self, customer_id: str) -> bool:
        """Delete a Stripe customer."""
        try:
            stripe.Customer.delete(customer_id)
            logger.info(f"Deleted Stripe customer: {customer_id}")
            return True
        except StripeError as e:
            logger.error(f"Failed to delete customer {customer_id}: {e}")
            return False

    # =========================================================================
    # Payment Methods
    # =========================================================================

    async def attach_payment_method(
        self,
        payment_method_id: str,
        customer_id: str,
    ) -> stripe.PaymentMethod:
        """Attach a payment method to a customer."""
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            logger.info(
                f"Attached payment method {payment_method_id} "
                f"to customer {customer_id}"
            )
            return payment_method
        except StripeError as e:
            logger.error(f"Failed to attach payment method: {e}")
            raise

    async def detach_payment_method(
        self,
        payment_method_id: str,
    ) -> stripe.PaymentMethod:
        """Detach a payment method from a customer."""
        try:
            payment_method = stripe.PaymentMethod.detach(payment_method_id)
            logger.info(f"Detached payment method: {payment_method_id}")
            return payment_method
        except StripeError as e:
            logger.error(f"Failed to detach payment method: {e}")
            raise

    async def list_payment_methods(
        self,
        customer_id: str,
        type: str = "card",
    ) -> list[stripe.PaymentMethod]:
        """List payment methods for a customer."""
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type=type,
            )
            return payment_methods.data
        except StripeError as e:
            logger.error(f"Failed to list payment methods: {e}")
            raise

    async def set_default_payment_method(
        self,
        customer_id: str,
        payment_method_id: str,
    ) -> stripe.Customer:
        """Set the default payment method for a customer."""
        try:
            customer = stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    "default_payment_method": payment_method_id,
                },
            )
            logger.info(
                f"Set default payment method {payment_method_id} "
                f"for customer {customer_id}"
            )
            return customer
        except StripeError as e:
            logger.error(f"Failed to set default payment method: {e}")
            raise

    # =========================================================================
    # Subscriptions
    # =========================================================================

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 0,
        metadata: Optional[dict] = None,
        payment_behavior: str = "default_incomplete",
    ) -> stripe.Subscription:
        """Create a subscription."""
        try:
            params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "payment_behavior": payment_behavior,
                "expand": ["latest_invoice.payment_intent"],
                "metadata": metadata or {},
            }

            if trial_days > 0:
                params["trial_period_days"] = trial_days

            subscription = stripe.Subscription.create(**params)
            logger.info(
                f"Created subscription {subscription.id} "
                f"for customer {customer_id}"
            )
            return subscription
        except StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            raise

    async def get_subscription(
        self,
        subscription_id: str,
    ) -> Optional[stripe.Subscription]:
        """Get a subscription by ID."""
        try:
            return stripe.Subscription.retrieve(
                subscription_id,
                expand=["latest_invoice.payment_intent"],
            )
        except StripeError as e:
            logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
            return None

    async def update_subscription(
        self,
        subscription_id: str,
        **kwargs,
    ) -> stripe.Subscription:
        """Update a subscription."""
        try:
            subscription = stripe.Subscription.modify(subscription_id, **kwargs)
            logger.info(f"Updated subscription: {subscription_id}")
            return subscription
        except StripeError as e:
            logger.error(f"Failed to update subscription {subscription_id}: {e}")
            raise

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> stripe.Subscription:
        """Cancel a subscription."""
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)

            logger.info(
                f"Canceled subscription {subscription_id} "
                f"(at_period_end={at_period_end})"
            )
            return subscription
        except StripeError as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
            raise

    async def resume_subscription(
        self,
        subscription_id: str,
    ) -> stripe.Subscription:
        """Resume a canceled subscription (if not yet ended)."""
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False,
            )
            logger.info(f"Resumed subscription: {subscription_id}")
            return subscription
        except StripeError as e:
            logger.error(f"Failed to resume subscription {subscription_id}: {e}")
            raise

    async def change_subscription_plan(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_behavior: str = "create_prorations",
    ) -> stripe.Subscription:
        """Change the plan of an existing subscription."""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            subscription = stripe.Subscription.modify(
                subscription_id,
                items=[
                    {
                        "id": subscription["items"]["data"][0].id,
                        "price": new_price_id,
                    }
                ],
                proration_behavior=proration_behavior,
            )
            logger.info(
                f"Changed subscription {subscription_id} "
                f"to price {new_price_id}"
            )
            return subscription
        except StripeError as e:
            logger.error(f"Failed to change subscription plan: {e}")
            raise

    # =========================================================================
    # Payment Intents
    # =========================================================================

    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        automatic_payment_methods: bool = True,
    ) -> stripe.PaymentIntent:
        """Create a payment intent."""
        try:
            params = {
                "amount": amount,
                "currency": currency,
                "metadata": metadata or {},
            }

            if customer_id:
                params["customer"] = customer_id

            if payment_method_id:
                params["payment_method"] = payment_method_id

            if automatic_payment_methods:
                params["automatic_payment_methods"] = {"enabled": True}

            payment_intent = stripe.PaymentIntent.create(**params)
            logger.info(f"Created payment intent: {payment_intent.id}")
            return payment_intent
        except StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise

    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: Optional[str] = None,
    ) -> stripe.PaymentIntent:
        """Confirm a payment intent."""
        try:
            params = {}
            if payment_method_id:
                params["payment_method"] = payment_method_id

            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **params,
            )
            logger.info(f"Confirmed payment intent: {payment_intent_id}")
            return payment_intent
        except StripeError as e:
            logger.error(f"Failed to confirm payment intent: {e}")
            raise

    async def cancel_payment_intent(
        self,
        payment_intent_id: str,
    ) -> stripe.PaymentIntent:
        """Cancel a payment intent."""
        try:
            payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)
            logger.info(f"Canceled payment intent: {payment_intent_id}")
            return payment_intent
        except StripeError as e:
            logger.error(f"Failed to cancel payment intent: {e}")
            raise

    # =========================================================================
    # Setup Intents (for saving payment methods)
    # =========================================================================

    async def create_setup_intent(
        self,
        customer_id: str,
        metadata: Optional[dict] = None,
    ) -> stripe.SetupIntent:
        """Create a setup intent for saving a payment method."""
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
            )
            logger.info(f"Created setup intent: {setup_intent.id}")
            return setup_intent
        except StripeError as e:
            logger.error(f"Failed to create setup intent: {e}")
            raise

    # =========================================================================
    # Invoices
    # =========================================================================

    async def get_invoice(self, invoice_id: str) -> Optional[stripe.Invoice]:
        """Get an invoice by ID."""
        try:
            return stripe.Invoice.retrieve(invoice_id)
        except StripeError as e:
            logger.error(f"Failed to retrieve invoice {invoice_id}: {e}")
            return None

    async def list_invoices(
        self,
        customer_id: str,
        limit: int = 10,
    ) -> list[stripe.Invoice]:
        """List invoices for a customer."""
        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
            return invoices.data
        except StripeError as e:
            logger.error(f"Failed to list invoices: {e}")
            raise

    async def pay_invoice(self, invoice_id: str) -> stripe.Invoice:
        """Pay an invoice."""
        try:
            invoice = stripe.Invoice.pay(invoice_id)
            logger.info(f"Paid invoice: {invoice_id}")
            return invoice
        except StripeError as e:
            logger.error(f"Failed to pay invoice {invoice_id}: {e}")
            raise

    # =========================================================================
    # Refunds
    # =========================================================================

    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> stripe.Refund:
        """Create a refund."""
        try:
            params = {"payment_intent": payment_intent_id}

            if amount:
                params["amount"] = amount

            if reason:
                params["reason"] = reason

            refund = stripe.Refund.create(**params)
            logger.info(
                f"Created refund for payment intent {payment_intent_id}: "
                f"{refund.id}"
            )
            return refund
        except StripeError as e:
            logger.error(f"Failed to create refund: {e}")
            raise

    # =========================================================================
    # Products & Prices
    # =========================================================================

    async def create_product(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> stripe.Product:
        """Create a product."""
        try:
            product = stripe.Product.create(
                name=name,
                description=description,
                metadata=metadata or {},
            )
            logger.info(f"Created product: {product.id}")
            return product
        except StripeError as e:
            logger.error(f"Failed to create product: {e}")
            raise

    async def create_price(
        self,
        product_id: str,
        unit_amount: int,
        currency: str = "usd",
        recurring_interval: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> stripe.Price:
        """Create a price."""
        try:
            params = {
                "product": product_id,
                "unit_amount": unit_amount,
                "currency": currency,
                "metadata": metadata or {},
            }

            if recurring_interval:
                params["recurring"] = {"interval": recurring_interval}

            price = stripe.Price.create(**params)
            logger.info(f"Created price: {price.id}")
            return price
        except StripeError as e:
            logger.error(f"Failed to create price: {e}")
            raise

    async def list_prices(
        self,
        product_id: Optional[str] = None,
        active: bool = True,
    ) -> list[stripe.Price]:
        """List prices."""
        try:
            params = {"active": active}
            if product_id:
                params["product"] = product_id

            prices = stripe.Price.list(**params)
            return prices.data
        except StripeError as e:
            logger.error(f"Failed to list prices: {e}")
            raise

    # =========================================================================
    # Webhooks
    # =========================================================================

    def construct_webhook_event(
        self,
        payload: bytes,
        sig_header: str,
        webhook_secret: str,
    ) -> stripe.Event:
        """Construct and verify a webhook event."""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                webhook_secret,
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise

    # =========================================================================
    # Checkout Sessions
    # =========================================================================

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        mode: str = "subscription",
        trial_days: int = 0,
        metadata: Optional[dict] = None,
    ) -> stripe.checkout.Session:
        """Create a Stripe Checkout session."""
        try:
            params = {
                "customer": customer_id,
                "line_items": [{"price": price_id, "quantity": 1}],
                "mode": mode,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": metadata or {},
            }

            if mode == "subscription" and trial_days > 0:
                params["subscription_data"] = {
                    "trial_period_days": trial_days,
                }

            session = stripe.checkout.Session.create(**params)
            logger.info(f"Created checkout session: {session.id}")
            return session
        except StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise

    # =========================================================================
    # Customer Portal
    # =========================================================================

    async def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> stripe.billing_portal.Session:
        """Create a billing portal session."""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            logger.info(f"Created billing portal session for {customer_id}")
            return session
        except StripeError as e:
            logger.error(f"Failed to create billing portal session: {e}")
            raise


# Global instance
stripe_service = StripeService()
