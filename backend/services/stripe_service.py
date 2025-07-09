"""
Stripe payment integration service for handling subscriptions and payments.
"""

import stripe
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import logging
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from core.config import settings
from core.exceptions import PaymentError, ValidationError
from models import (
    User, Company, Subscription, SubscriptionStatus, BillingInterval,
    PaymentMethod, PaymentMethodType, Invoice, InvoiceStatus,
    Payment, PaymentStatus, SubscriptionUsage, SubscriptionTier
)

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for handling Stripe payments and subscriptions."""

    def __init__(self, db: AsyncSession):
        """Initialize Stripe service."""
        self.db = db
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    async def create_customer(
        self,
        user: User,
        company: Optional[Company] = None
    ) -> str:
        """
        Create a Stripe customer for a user.

        Returns:
            Stripe customer ID
        """
        try:
            # Check if customer already exists
            if user.stripe_customer_id:
                return user.stripe_customer_id

            # Create customer in Stripe
            customer_data = {
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
                "metadata": {
                    "user_id": str(user.id),
                    "company_id": str(company.id) if company else "",
                }
            }

            if company:
                customer_data["description"] = f"Company: {company.name}"
                if company.billing_email:
                    customer_data["email"] = company.billing_email

            customer = stripe.Customer.create(**customer_data)

            # Save customer ID to user
            user.stripe_customer_id = customer.id
            await self.db.commit()

            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {str(e)}")
            raise PaymentError(f"Failed to create customer: {str(e)}")

    async def create_subscription(
        self,
        company_id: int,
        tier: SubscriptionTier,
        billing_interval: BillingInterval = BillingInterval.MONTHLY,
        payment_method_id: Optional[str] = None,
        trial_days: int = 0,
    ) -> Subscription:
        """
        Create a subscription for a company.

        Args:
            company_id: Company ID
            tier: Subscription tier
            billing_interval: Monthly or yearly billing
            payment_method_id: Stripe payment method ID
            trial_days: Number of trial days

        Returns:
            Created Subscription
        """
        # Get company and admin user
        company = await self.db.get(Company, company_id)
        if not company:
            raise ValidationError("Company not found")

        # Get company admin
        stmt = select(User).where(
            User.company_id == company_id,
            User.role == "admin"
        ).limit(1)
        result = await self.db.execute(stmt)
        admin = result.scalar_one_or_none()

        if not admin:
            raise ValidationError("No admin user found for company")

        # Create Stripe customer if needed
        customer_id = await self.create_customer(admin, company)

        # Attach payment method if provided
        if payment_method_id:
            try:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=customer_id,
                )
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={"default_payment_method": payment_method_id}
                )
            except stripe.error.StripeError as e:
                logger.error(f"Failed to attach payment method: {str(e)}")
                raise PaymentError(f"Invalid payment method: {str(e)}")

        # Get price ID based on tier and interval
        price_id = self._get_price_id(tier, billing_interval)

        try:
            # Create subscription in Stripe
            subscription_data = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": {
                    "company_id": str(company_id),
                    "tier": tier.value,
                },
            }

            if trial_days > 0:
                subscription_data["trial_period_days"] = trial_days

            stripe_subscription = stripe.Subscription.create(**subscription_data)

            # Create subscription in database
            subscription = Subscription(
                company_id=company_id,
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=customer_id,
                tier=tier,
                billing_interval=billing_interval,
                status=SubscriptionStatus.ACTIVE if not trial_days else SubscriptionStatus.TRIALING,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None,
                cancel_at_period_end=stripe_subscription.cancel_at_period_end,
            )

            self.db.add(subscription)

            # Update company subscription tier
            company.subscription_tier = tier
            
            await self.db.commit()
            await self.db.refresh(subscription)

            logger.info(f"Created subscription {subscription.id} for company {company_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {str(e)}")
            raise PaymentError(f"Failed to create subscription: {str(e)}")

    def _get_price_id(self, tier: SubscriptionTier, interval: BillingInterval) -> str:
        """Get Stripe price ID for tier and interval."""
        # These would be configured in Stripe dashboard
        price_mapping = {
            (SubscriptionTier.STARTER, BillingInterval.MONTHLY): "price_starter_monthly",
            (SubscriptionTier.STARTER, BillingInterval.YEARLY): "price_starter_yearly",
            (SubscriptionTier.PROFESSIONAL, BillingInterval.MONTHLY): "price_professional_monthly",
            (SubscriptionTier.PROFESSIONAL, BillingInterval.YEARLY): "price_professional_yearly",
            (SubscriptionTier.ENTERPRISE, BillingInterval.MONTHLY): "price_enterprise_monthly",
            (SubscriptionTier.ENTERPRISE, BillingInterval.YEARLY): "price_enterprise_yearly",
        }

        price_id = price_mapping.get((tier, interval))
        if not price_id:
            raise ValidationError(f"No price configured for {tier} {interval}")

        return price_id

    async def update_subscription(
        self,
        subscription_id: int,
        tier: Optional[SubscriptionTier] = None,
        billing_interval: Optional[BillingInterval] = None,
    ) -> Subscription:
        """Update a subscription (upgrade/downgrade)."""
        subscription = await self.db.get(Subscription, subscription_id)
        if not subscription:
            raise ValidationError("Subscription not found")

        if not subscription.stripe_subscription_id:
            raise ValidationError("No Stripe subscription linked")

        try:
            # Get current Stripe subscription
            stripe_subscription = stripe.Subscription.retrieve(
                subscription.stripe_subscription_id
            )

            # Update subscription
            update_data = {}
            
            new_tier = tier or subscription.tier
            new_interval = billing_interval or subscription.billing_interval
            
            if new_tier != subscription.tier or new_interval != subscription.billing_interval:
                # Change subscription plan
                new_price_id = self._get_price_id(new_tier, new_interval)
                
                # Update subscription item
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        "id": stripe_subscription["items"]["data"][0].id,
                        "price": new_price_id,
                    }],
                    proration_behavior="create_prorations",
                )

                # Update database
                subscription.tier = new_tier
                subscription.billing_interval = new_interval

                # Update company tier
                company = await self.db.get(Company, subscription.company_id)
                if company:
                    company.subscription_tier = new_tier

            await self.db.commit()
            await self.db.refresh(subscription)

            logger.info(f"Updated subscription {subscription_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {str(e)}")
            raise PaymentError(f"Failed to update subscription: {str(e)}")

    async def cancel_subscription(
        self,
        subscription_id: int,
        immediately: bool = False
    ) -> Subscription:
        """Cancel a subscription."""
        subscription = await self.db.get(Subscription, subscription_id)
        if not subscription:
            raise ValidationError("Subscription not found")

        if subscription.status == SubscriptionStatus.CANCELLED:
            raise ValidationError("Subscription already cancelled")

        try:
            # Cancel in Stripe
            if immediately:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.ended_at = datetime.utcnow()
            else:
                # Cancel at end of period
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True

            await self.db.commit()
            await self.db.refresh(subscription)

            logger.info(f"Cancelled subscription {subscription_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {str(e)}")
            raise PaymentError(f"Failed to cancel subscription: {str(e)}")

    async def reactivate_subscription(self, subscription_id: int) -> Subscription:
        """Reactivate a cancelled subscription before period end."""
        subscription = await self.db.get(Subscription, subscription_id)
        if not subscription:
            raise ValidationError("Subscription not found")

        if not subscription.cancel_at_period_end:
            raise ValidationError("Subscription not scheduled for cancellation")

        try:
            # Reactivate in Stripe
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=False
            )

            subscription.cancel_at_period_end = False
            
            await self.db.commit()
            await self.db.refresh(subscription)

            logger.info(f"Reactivated subscription {subscription_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error reactivating subscription: {str(e)}")
            raise PaymentError(f"Failed to reactivate subscription: {str(e)}")

    async def add_payment_method(
        self,
        user_id: int,
        payment_method_id: str,
        set_as_default: bool = True
    ) -> PaymentMethod:
        """Add a payment method for a user."""
        user = await self.db.get(User, user_id)
        if not user:
            raise ValidationError("User not found")

        # Ensure customer exists
        customer_id = await self.create_customer(user)

        try:
            # Attach payment method to customer
            stripe_pm = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )

            if set_as_default:
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={"default_payment_method": payment_method_id}
                )

            # Save to database
            payment_method = PaymentMethod(
                user_id=user_id,
                stripe_payment_method_id=payment_method_id,
                type=PaymentMethodType(stripe_pm.type),
                card_last4=stripe_pm.card.last4 if stripe_pm.type == "card" else None,
                card_brand=stripe_pm.card.brand if stripe_pm.type == "card" else None,
                is_default=set_as_default,
            )

            # Set other payment methods as non-default
            if set_as_default:
                stmt = update(PaymentMethod).where(
                    PaymentMethod.user_id == user_id,
                    PaymentMethod.id != payment_method.id
                ).values(is_default=False)
                await self.db.execute(stmt)

            self.db.add(payment_method)
            await self.db.commit()
            await self.db.refresh(payment_method)

            logger.info(f"Added payment method for user {user_id}")
            return payment_method

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error adding payment method: {str(e)}")
            raise PaymentError(f"Failed to add payment method: {str(e)}")

    async def remove_payment_method(self, payment_method_id: int) -> bool:
        """Remove a payment method."""
        payment_method = await self.db.get(PaymentMethod, payment_method_id)
        if not payment_method:
            raise ValidationError("Payment method not found")

        try:
            # Detach from Stripe
            stripe.PaymentMethod.detach(payment_method.stripe_payment_method_id)

            # Remove from database
            await self.db.delete(payment_method)
            await self.db.commit()

            logger.info(f"Removed payment method {payment_method_id}")
            return True

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error removing payment method: {str(e)}")
            raise PaymentError(f"Failed to remove payment method: {str(e)}")

    async def create_setup_intent(self, user_id: int) -> Dict[str, str]:
        """Create a setup intent for adding payment methods."""
        user = await self.db.get(User, user_id)
        if not user:
            raise ValidationError("User not found")

        customer_id = await self.create_customer(user)

        try:
            intent = stripe.SetupIntent.create(
                customer=customer_id,
                metadata={"user_id": str(user_id)},
            )

            return {
                "client_secret": intent.client_secret,
                "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating setup intent: {str(e)}")
            raise PaymentError(f"Failed to create setup intent: {str(e)}")

    async def process_webhook(
        self,
        payload: bytes,
        sig_header: str
    ) -> Dict[str, Any]:
        """Process Stripe webhook events."""
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        except ValueError:
            logger.error("Invalid webhook payload")
            raise ValidationError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise ValidationError("Invalid signature")

        # Handle event
        event_type = event["type"]
        event_data = event["data"]["object"]

        logger.info(f"Processing webhook event: {event_type}")

        if event_type == "customer.subscription.created":
            await self._handle_subscription_created(event_data)
        elif event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(event_data)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(event_data)
        elif event_type == "invoice.payment_succeeded":
            await self._handle_invoice_paid(event_data)
        elif event_type == "invoice.payment_failed":
            await self._handle_invoice_failed(event_data)
        elif event_type == "customer.subscription.trial_will_end":
            await self._handle_trial_ending(event_data)

        return {"status": "success", "event": event_type}

    async def _handle_subscription_created(self, stripe_subscription: Dict[str, Any]):
        """Handle subscription creation webhook."""
        # This is usually handled by our create_subscription method
        # But we update status to ensure consistency
        stmt = select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription["id"]
        )
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = SubscriptionStatus(stripe_subscription["status"])
            subscription.current_period_start = datetime.fromtimestamp(
                stripe_subscription["current_period_start"]
            )
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription["current_period_end"]
            )
            await self.db.commit()

    async def _handle_subscription_updated(self, stripe_subscription: Dict[str, Any]):
        """Handle subscription update webhook."""
        stmt = select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription["id"]
        )
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription:
            # Update subscription details
            subscription.status = SubscriptionStatus(stripe_subscription["status"])
            subscription.current_period_start = datetime.fromtimestamp(
                stripe_subscription["current_period_start"]
            )
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription["current_period_end"]
            )
            subscription.cancel_at_period_end = stripe_subscription["cancel_at_period_end"]
            
            if stripe_subscription.get("canceled_at"):
                subscription.ended_at = datetime.fromtimestamp(
                    stripe_subscription["canceled_at"]
                )

            await self.db.commit()

    async def _handle_subscription_deleted(self, stripe_subscription: Dict[str, Any]):
        """Handle subscription deletion webhook."""
        stmt = select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription["id"]
        )
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.ended_at = datetime.utcnow()

            # Update company to free tier
            company = await self.db.get(Company, subscription.company_id)
            if company:
                company.subscription_tier = SubscriptionTier.FREE

            await self.db.commit()

    async def _handle_invoice_paid(self, invoice: Dict[str, Any]):
        """Handle successful invoice payment."""
        # Create payment record
        payment = Payment(
            stripe_payment_intent_id=invoice.get("payment_intent"),
            stripe_invoice_id=invoice["id"],
            amount=Decimal(str(invoice["amount_paid"] / 100)),  # Convert from cents
            currency=invoice["currency"].upper(),
            status=PaymentStatus.SUCCEEDED,
            description=f"Invoice {invoice['number']}",
            metadata={
                "invoice_number": invoice["number"],
                "customer": invoice["customer"],
            }
        )

        self.db.add(payment)

        # Update subscription if this is a subscription invoice
        if invoice.get("subscription"):
            stmt = select(Subscription).where(
                Subscription.stripe_subscription_id == invoice["subscription"]
            )
            result = await self.db.execute(stmt)
            subscription = result.scalar_one_or_none()

            if subscription:
                subscription.status = SubscriptionStatus.ACTIVE
                payment.subscription_id = subscription.id

        await self.db.commit()

    async def _handle_invoice_failed(self, invoice: Dict[str, Any]):
        """Handle failed invoice payment."""
        # Create payment record
        payment = Payment(
            stripe_payment_intent_id=invoice.get("payment_intent"),
            stripe_invoice_id=invoice["id"],
            amount=Decimal(str(invoice["amount_due"] / 100)),
            currency=invoice["currency"].upper(),
            status=PaymentStatus.FAILED,
            description=f"Failed invoice {invoice['number']}",
            metadata={
                "invoice_number": invoice["number"],
                "customer": invoice["customer"],
                "failure_reason": invoice.get("failure_message", "Unknown"),
            }
        )

        self.db.add(payment)

        # Update subscription status
        if invoice.get("subscription"):
            stmt = select(Subscription).where(
                Subscription.stripe_subscription_id == invoice["subscription"]
            )
            result = await self.db.execute(stmt)
            subscription = result.scalar_one_or_none()

            if subscription:
                subscription.status = SubscriptionStatus.PAST_DUE
                payment.subscription_id = subscription.id

        await self.db.commit()

    async def _handle_trial_ending(self, stripe_subscription: Dict[str, Any]):
        """Handle trial ending notification."""
        # Send notification email to company
        stmt = select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription["id"]
        )
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if subscription:
            # This would trigger an email notification
            logger.info(f"Trial ending for subscription {subscription.id}")

    async def get_billing_portal_url(self, user_id: int) -> str:
        """Get Stripe billing portal URL for a user."""
        user = await self.db.get(User, user_id)
        if not user or not user.stripe_customer_id:
            raise ValidationError("No customer record found")

        try:
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=f"{settings.FRONTEND_URL}/settings/billing",
            )

            return session.url

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {str(e)}")
            raise PaymentError(f"Failed to create billing portal: {str(e)}")

    async def get_invoices(
        self,
        company_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get invoices for a company."""
        # Get subscription
        stmt = select(Subscription).where(
            Subscription.company_id == company_id
        ).order_by(Subscription.created_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if not subscription or not subscription.stripe_customer_id:
            return []

        try:
            # Get invoices from Stripe
            invoices = stripe.Invoice.list(
                customer=subscription.stripe_customer_id,
                limit=limit,
            )

            return [
                {
                    "id": invoice.id,
                    "number": invoice.number,
                    "amount": invoice.amount_paid / 100,
                    "currency": invoice.currency.upper(),
                    "status": invoice.status,
                    "created": datetime.fromtimestamp(invoice.created),
                    "pdf_url": invoice.invoice_pdf,
                    "hosted_url": invoice.hosted_invoice_url,
                }
                for invoice in invoices.data
            ]

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error fetching invoices: {str(e)}")
            return []

    async def record_usage(
        self,
        company_id: int,
        metric: str,
        quantity: int,
        timestamp: Optional[datetime] = None
    ) -> SubscriptionUsage:
        """Record usage for metered billing."""
        # Get active subscription
        stmt = select(Subscription).where(
            Subscription.company_id == company_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).limit(1)
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValidationError("No active subscription found")

        # Record usage in database
        usage = SubscriptionUsage(
            subscription_id=subscription.id,
            metric=metric,
            quantity=quantity,
            timestamp=timestamp or datetime.utcnow(),
        )

        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)

        # Report to Stripe if configured for metered billing
        # This would be implemented based on specific pricing model

        return usage