"""Stripe service for payment processing."""

import stripe
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging
from uuid import UUID
import json

from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..core.config import get_settings
from ..models import (
    Company, CompanyStatus, SubscriptionTier,
    Subscription, SubscriptionStatus, BillingInterval,
    PaymentMethod, PaymentMethodType,
    Invoice, InvoiceStatus,
    Payment, PaymentStatus,
    SubscriptionUsage
)

logger = logging.getLogger(__name__)
settings = get_settings()


class StripeService:
    """Service for handling Stripe operations."""
    
    def __init__(self):
        """Initialize Stripe with API key."""
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        
    def create_customer(self, company: Company, email: str) -> str:
        """Create a Stripe customer for a company."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=company.name,
                metadata={
                    "company_id": str(company.id),
                    "domain": company.domain
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    def create_setup_intent(self, customer_id: str) -> Dict[str, str]:
        """Create a setup intent for collecting payment method."""
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=["card", "sepa_debit"],
                usage="off_session"
            )
            return {
                "client_secret": setup_intent.client_secret,
                "setup_intent_id": setup_intent.id
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create setup intent: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    def save_payment_method(
        self,
        db: Session,
        company: Company,
        payment_method_id: str,
        customer_id: str,
        set_as_default: bool = True
    ) -> PaymentMethod:
        """Save a payment method from Stripe."""
        try:
            # Retrieve payment method from Stripe
            stripe_pm = stripe.PaymentMethod.retrieve(payment_method_id)
            
            # Attach to customer if not already attached
            if not stripe_pm.customer:
                stripe_pm = stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=customer_id
                )
            
            # Set as default if requested
            if set_as_default:
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={"default_payment_method": payment_method_id}
                )
                # Update other payment methods to not be default
                db.query(PaymentMethod).filter(
                    PaymentMethod.company_id == company.id,
                    PaymentMethod.is_default == True
                ).update({"is_default": False})
            
            # Create payment method record
            payment_method = PaymentMethod(
                company_id=company.id,
                stripe_payment_method_id=payment_method_id,
                stripe_customer_id=customer_id,
                type=PaymentMethodType(stripe_pm.type),
                is_default=set_as_default
            )
            
            # Set card details
            if stripe_pm.type == "card":
                payment_method.card_brand = stripe_pm.card.brand
                payment_method.card_last4 = stripe_pm.card.last4
                payment_method.card_exp_month = stripe_pm.card.exp_month
                payment_method.card_exp_year = stripe_pm.card.exp_year
                payment_method.card_country = stripe_pm.card.country
            
            # Set SEPA details
            elif stripe_pm.type == "sepa_debit":
                payment_method.bank_name = stripe_pm.sepa_debit.bank_code
                payment_method.bank_last4 = stripe_pm.sepa_debit.last4
                payment_method.bank_country = stripe_pm.sepa_debit.country
            
            # Set billing details
            if stripe_pm.billing_details:
                payment_method.billing_name = stripe_pm.billing_details.name
                payment_method.billing_email = stripe_pm.billing_details.email
                payment_method.billing_phone = stripe_pm.billing_details.phone
                
                if stripe_pm.billing_details.address:
                    payment_method.billing_address_line1 = stripe_pm.billing_details.address.line1
                    payment_method.billing_address_line2 = stripe_pm.billing_details.address.line2
                    payment_method.billing_address_city = stripe_pm.billing_details.address.city
                    payment_method.billing_address_state = stripe_pm.billing_details.address.state
                    payment_method.billing_address_postal_code = stripe_pm.billing_details.address.postal_code
                    payment_method.billing_address_country = stripe_pm.billing_details.address.country
            
            db.add(payment_method)
            db.commit()
            db.refresh(payment_method)
            
            return payment_method
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to save payment method: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    def create_subscription(
        self,
        db: Session,
        company: Company,
        customer_id: str,
        price_id: str,
        trial_days: int = 14
    ) -> Subscription:
        """Create a subscription for a company."""
        try:
            # Create Stripe subscription
            stripe_sub = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                trial_period_days=trial_days,
                metadata={
                    "company_id": str(company.id),
                    "company_name": company.name
                }
            )
            
            # Retrieve price and product details
            price = stripe.Price.retrieve(price_id)
            product = stripe.Product.retrieve(price.product)
            
            # Determine billing interval
            interval = BillingInterval.MONTHLY
            if price.recurring and price.recurring.interval == "year":
                interval = BillingInterval.YEARLY
            
            # Create subscription record
            subscription = Subscription(
                company_id=company.id,
                stripe_subscription_id=stripe_sub.id,
                stripe_customer_id=customer_id,
                stripe_price_id=price_id,
                stripe_product_id=product.id,
                status=SubscriptionStatus(stripe_sub.status),
                billing_interval=interval,
                amount=Decimal(price.unit_amount) / 100,  # Convert cents to euros
                currency=price.currency.upper(),
                current_period_start=datetime.fromtimestamp(stripe_sub.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end),
                trial_start=datetime.fromtimestamp(stripe_sub.trial_start) if stripe_sub.trial_start else None,
                trial_end=datetime.fromtimestamp(stripe_sub.trial_end) if stripe_sub.trial_end else None,
                metadata={
                    "product_name": product.name,
                    "price_nickname": price.nickname
                }
            )
            
            db.add(subscription)
            
            # Update company status and tier
            company.status = CompanyStatus.TRIAL
            company.trial_ends_at = subscription.trial_end
            
            # Map product metadata to subscription tier
            tier_mapping = {
                "basic": SubscriptionTier.BASIC,
                "starter": SubscriptionTier.STARTER,
                "premium": SubscriptionTier.PREMIUM,
                "professional": SubscriptionTier.PROFESSIONAL,
                "enterprise": SubscriptionTier.ENTERPRISE
            }
            
            tier = product.metadata.get("tier", "starter").lower()
            company.subscription_tier = tier_mapping.get(tier, SubscriptionTier.STARTER)
            
            # Update max users based on tier
            max_users_mapping = {
                SubscriptionTier.BASIC: 10,
                SubscriptionTier.STARTER: 50,
                SubscriptionTier.PREMIUM: 100,
                SubscriptionTier.PROFESSIONAL: 250,
                SubscriptionTier.ENTERPRISE: 1000
            }
            company.max_users = max_users_mapping.get(company.subscription_tier, 50)
            
            db.commit()
            db.refresh(subscription)
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    def cancel_subscription(
        self,
        db: Session,
        subscription: Subscription,
        immediate: bool = False
    ) -> Subscription:
        """Cancel a subscription."""
        try:
            # Cancel in Stripe
            if immediate:
                stripe_sub = stripe.Subscription.delete(subscription.stripe_subscription_id)
            else:
                stripe_sub = stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            
            # Update subscription record
            subscription.status = SubscriptionStatus(stripe_sub.status)
            subscription.cancel_at = datetime.fromtimestamp(stripe_sub.cancel_at) if stripe_sub.cancel_at else None
            subscription.canceled_at = datetime.fromtimestamp(stripe_sub.canceled_at) if stripe_sub.canceled_at else None
            
            # Update company status if immediate cancellation
            if immediate:
                subscription.company.status = CompanyStatus.CANCELLED
                subscription.company.subscription_tier = SubscriptionTier.FREE
                subscription.company.max_users = 10
            
            db.commit()
            db.refresh(subscription)
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    def update_subscription(
        self,
        db: Session,
        subscription: Subscription,
        new_price_id: str,
        prorate: bool = True
    ) -> Subscription:
        """Update subscription to a different plan."""
        try:
            # Get the subscription item
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            
            # Update the subscription
            updated_sub = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    "id": stripe_sub["items"]["data"][0].id,
                    "price": new_price_id
                }],
                proration_behavior="create_prorations" if prorate else "none"
            )
            
            # Retrieve new price and product details
            price = stripe.Price.retrieve(new_price_id)
            product = stripe.Product.retrieve(price.product)
            
            # Update subscription record
            subscription.stripe_price_id = new_price_id
            subscription.stripe_product_id = product.id
            subscription.amount = Decimal(price.unit_amount) / 100
            subscription.status = SubscriptionStatus(updated_sub.status)
            
            # Update company tier
            tier_mapping = {
                "basic": SubscriptionTier.BASIC,
                "starter": SubscriptionTier.STARTER,
                "premium": SubscriptionTier.PREMIUM,
                "professional": SubscriptionTier.PROFESSIONAL,
                "enterprise": SubscriptionTier.ENTERPRISE
            }
            
            tier = product.metadata.get("tier", "starter").lower()
            subscription.company.subscription_tier = tier_mapping.get(tier, SubscriptionTier.STARTER)
            
            # Update max users
            max_users_mapping = {
                SubscriptionTier.BASIC: 10,
                SubscriptionTier.STARTER: 50,
                SubscriptionTier.PREMIUM: 100,
                SubscriptionTier.PROFESSIONAL: 250,
                SubscriptionTier.ENTERPRISE: 1000
            }
            subscription.company.max_users = max_users_mapping.get(subscription.company.subscription_tier, 50)
            
            db.commit()
            db.refresh(subscription)
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    def create_invoice(
        self,
        db: Session,
        company: Company,
        customer_id: str,
        items: List[Dict[str, Any]],
        due_days: int = 30
    ) -> Invoice:
        """Create a manual invoice."""
        try:
            # Create invoice items
            for item in items:
                stripe.InvoiceItem.create(
                    customer=customer_id,
                    amount=int(item["amount"] * 100),  # Convert to cents
                    currency="eur",
                    description=item["description"],
                    metadata=item.get("metadata", {})
                )
            
            # Create the invoice
            stripe_invoice = stripe.Invoice.create(
                customer=customer_id,
                auto_advance=True,
                collection_method="send_invoice",
                days_until_due=due_days,
                metadata={
                    "company_id": str(company.id),
                    "company_name": company.name
                }
            )
            
            # Finalize the invoice
            stripe_invoice = stripe.Invoice.finalize_invoice(stripe_invoice.id)
            
            # Send the invoice
            stripe.Invoice.send_invoice(stripe_invoice.id)
            
            # Create invoice record
            invoice = self._create_invoice_from_stripe(db, company, stripe_invoice)
            
            db.commit()
            db.refresh(invoice)
            
            return invoice
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create invoice: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    def record_usage(
        self,
        db: Session,
        subscription: Subscription,
        metric_name: str,
        quantity: int,
        timestamp: Optional[datetime] = None
    ) -> SubscriptionUsage:
        """Record usage for usage-based billing."""
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            # Create usage record in database
            usage = SubscriptionUsage(
                company_id=subscription.company_id,
                subscription_id=subscription.id,
                metric_name=metric_name,
                quantity=quantity,
                unit="unit",
                period_start=timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                period_end=(timestamp.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            )
            
            db.add(usage)
            
            # Report to Stripe if subscription has metered component
            # This would require subscription items with usage-based pricing
            # For now, we just store locally
            
            db.commit()
            db.refresh(usage)
            
            return usage
            
        except Exception as e:
            logger.error(f"Failed to record usage: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    def process_webhook(self, db: Session, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
        except ValueError:
            logger.error("Invalid webhook payload")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle the event
        event_type = event["type"]
        event_object = event["data"]["object"]
        
        logger.info(f"Processing webhook event: {event_type}")
        
        if event_type == "customer.subscription.created":
            self._handle_subscription_created(db, event_object)
        
        elif event_type == "customer.subscription.updated":
            self._handle_subscription_updated(db, event_object)
        
        elif event_type == "customer.subscription.deleted":
            self._handle_subscription_deleted(db, event_object)
        
        elif event_type == "invoice.created":
            self._handle_invoice_created(db, event_object)
        
        elif event_type == "invoice.finalized":
            self._handle_invoice_finalized(db, event_object)
        
        elif event_type == "invoice.paid":
            self._handle_invoice_paid(db, event_object)
        
        elif event_type == "invoice.payment_failed":
            self._handle_invoice_payment_failed(db, event_object)
        
        elif event_type == "payment_intent.succeeded":
            self._handle_payment_succeeded(db, event_object)
        
        elif event_type == "payment_intent.payment_failed":
            self._handle_payment_failed(db, event_object)
        
        elif event_type == "payment_method.attached":
            self._handle_payment_method_attached(db, event_object)
        
        elif event_type == "payment_method.detached":
            self._handle_payment_method_detached(db, event_object)
        
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
        
        return {"status": "success", "event_type": event_type}
    
    def _handle_subscription_created(self, db: Session, stripe_sub: Dict[str, Any]):
        """Handle subscription created webhook."""
        # Subscription should already exist from create_subscription
        # This is just a safety check
        subscription = db.query(Subscription).filter_by(
            stripe_subscription_id=stripe_sub["id"]
        ).first()
        
        if not subscription:
            logger.warning(f"Subscription not found for webhook: {stripe_sub['id']}")
            return
        
        # Update status
        subscription.status = SubscriptionStatus(stripe_sub["status"])
        db.commit()
    
    def _handle_subscription_updated(self, db: Session, stripe_sub: Dict[str, Any]):
        """Handle subscription updated webhook."""
        subscription = db.query(Subscription).filter_by(
            stripe_subscription_id=stripe_sub["id"]
        ).first()
        
        if not subscription:
            logger.warning(f"Subscription not found for webhook: {stripe_sub['id']}")
            return
        
        # Update subscription details
        subscription.status = SubscriptionStatus(stripe_sub["status"])
        subscription.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"])
        subscription.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"])
        
        if stripe_sub.get("cancel_at"):
            subscription.cancel_at = datetime.fromtimestamp(stripe_sub["cancel_at"])
        
        if stripe_sub.get("canceled_at"):
            subscription.canceled_at = datetime.fromtimestamp(stripe_sub["canceled_at"])
        
        # Update company status based on subscription
        if subscription.status == SubscriptionStatus.ACTIVE:
            subscription.company.status = CompanyStatus.ACTIVE
        elif subscription.status in [SubscriptionStatus.PAST_DUE, SubscriptionStatus.UNPAID]:
            subscription.company.status = CompanyStatus.SUSPENDED
        
        db.commit()
    
    def _handle_subscription_deleted(self, db: Session, stripe_sub: Dict[str, Any]):
        """Handle subscription deleted webhook."""
        subscription = db.query(Subscription).filter_by(
            stripe_subscription_id=stripe_sub["id"]
        ).first()
        
        if not subscription:
            logger.warning(f"Subscription not found for webhook: {stripe_sub['id']}")
            return
        
        # Update subscription
        subscription.status = SubscriptionStatus.CANCELED
        subscription.ended_at = datetime.utcnow()
        
        # Update company
        subscription.company.status = CompanyStatus.CANCELLED
        subscription.company.subscription_tier = SubscriptionTier.FREE
        subscription.company.max_users = 10
        
        db.commit()
    
    def _handle_invoice_created(self, db: Session, stripe_invoice: Dict[str, Any]):
        """Handle invoice created webhook."""
        # Check if invoice already exists
        invoice = db.query(Invoice).filter_by(
            stripe_invoice_id=stripe_invoice["id"]
        ).first()
        
        if invoice:
            return
        
        # Get company
        company = self._get_company_from_customer_id(db, stripe_invoice["customer"])
        if not company:
            logger.warning(f"Company not found for customer: {stripe_invoice['customer']}")
            return
        
        # Create invoice record
        invoice = self._create_invoice_from_stripe(db, company, stripe_invoice)
        db.commit()
    
    def _handle_invoice_finalized(self, db: Session, stripe_invoice: Dict[str, Any]):
        """Handle invoice finalized webhook."""
        invoice = db.query(Invoice).filter_by(
            stripe_invoice_id=stripe_invoice["id"]
        ).first()
        
        if not invoice:
            # Create if doesn't exist
            company = self._get_company_from_customer_id(db, stripe_invoice["customer"])
            if company:
                invoice = self._create_invoice_from_stripe(db, company, stripe_invoice)
            else:
                return
        
        # Update invoice
        invoice.status = InvoiceStatus.OPEN
        invoice.invoice_pdf_url = stripe_invoice.get("invoice_pdf")
        invoice.hosted_invoice_url = stripe_invoice.get("hosted_invoice_url")
        
        db.commit()
    
    def _handle_invoice_paid(self, db: Session, stripe_invoice: Dict[str, Any]):
        """Handle invoice paid webhook."""
        invoice = db.query(Invoice).filter_by(
            stripe_invoice_id=stripe_invoice["id"]
        ).first()
        
        if not invoice:
            logger.warning(f"Invoice not found for webhook: {stripe_invoice['id']}")
            return
        
        # Update invoice
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.fromtimestamp(stripe_invoice["status_transitions"]["paid_at"])
        invoice.amount_paid = stripe_invoice["amount_paid"]
        invoice.amount_remaining = stripe_invoice["amount_remaining"]
        
        # If this is a subscription invoice, ensure subscription is active
        if invoice.subscription:
            invoice.subscription.status = SubscriptionStatus.ACTIVE
            invoice.subscription.company.status = CompanyStatus.ACTIVE
        
        db.commit()
    
    def _handle_invoice_payment_failed(self, db: Session, stripe_invoice: Dict[str, Any]):
        """Handle invoice payment failed webhook."""
        invoice = db.query(Invoice).filter_by(
            stripe_invoice_id=stripe_invoice["id"]
        ).first()
        
        if not invoice:
            logger.warning(f"Invoice not found for webhook: {stripe_invoice['id']}")
            return
        
        # Update invoice
        invoice.status = InvoiceStatus.OPEN
        
        # If this is a subscription invoice, update subscription status
        if invoice.subscription:
            invoice.subscription.status = SubscriptionStatus.PAST_DUE
            invoice.subscription.company.status = CompanyStatus.SUSPENDED
        
        db.commit()
    
    def _handle_payment_succeeded(self, db: Session, payment_intent: Dict[str, Any]):
        """Handle payment succeeded webhook."""
        payment = db.query(Payment).filter_by(
            stripe_payment_intent_id=payment_intent["id"]
        ).first()
        
        if not payment:
            # Create payment record
            company = self._get_company_from_customer_id(db, payment_intent["customer"])
            if not company:
                return
            
            payment = Payment(
                company_id=company.id,
                stripe_payment_intent_id=payment_intent["id"],
                stripe_charge_id=payment_intent["charges"]["data"][0]["id"] if payment_intent["charges"]["data"] else None,
                status=PaymentStatus.SUCCEEDED,
                amount=payment_intent["amount"],
                currency=payment_intent["currency"].upper(),
                payment_method_type=PaymentMethodType.CARD,  # Default, update based on actual
                paid_at=datetime.fromtimestamp(payment_intent["created"]),
                metadata=payment_intent.get("metadata", {})
            )
            
            # Link to invoice if exists
            if payment_intent.get("invoice"):
                invoice = db.query(Invoice).filter_by(
                    stripe_invoice_id=payment_intent["invoice"]
                ).first()
                if invoice:
                    payment.invoice_id = invoice.id
            
            db.add(payment)
        else:
            # Update existing payment
            payment.status = PaymentStatus.SUCCEEDED
            payment.paid_at = datetime.utcnow()
        
        db.commit()
    
    def _handle_payment_failed(self, db: Session, payment_intent: Dict[str, Any]):
        """Handle payment failed webhook."""
        payment = db.query(Payment).filter_by(
            stripe_payment_intent_id=payment_intent["id"]
        ).first()
        
        if not payment:
            # Create payment record
            company = self._get_company_from_customer_id(db, payment_intent["customer"])
            if not company:
                return
            
            payment = Payment(
                company_id=company.id,
                stripe_payment_intent_id=payment_intent["id"],
                status=PaymentStatus.FAILED,
                amount=payment_intent["amount"],
                currency=payment_intent["currency"].upper(),
                payment_method_type=PaymentMethodType.CARD,  # Default
                failed_at=datetime.utcnow(),
                failure_code=payment_intent["last_payment_error"]["code"] if payment_intent.get("last_payment_error") else None,
                failure_message=payment_intent["last_payment_error"]["message"] if payment_intent.get("last_payment_error") else None,
                metadata=payment_intent.get("metadata", {})
            )
            db.add(payment)
        else:
            # Update existing payment
            payment.status = PaymentStatus.FAILED
            payment.failed_at = datetime.utcnow()
            if payment_intent.get("last_payment_error"):
                payment.failure_code = payment_intent["last_payment_error"]["code"]
                payment.failure_message = payment_intent["last_payment_error"]["message"]
        
        db.commit()
    
    def _handle_payment_method_attached(self, db: Session, payment_method: Dict[str, Any]):
        """Handle payment method attached webhook."""
        # Payment method should already exist from save_payment_method
        # This is just for cases where it's attached outside our app
        existing = db.query(PaymentMethod).filter_by(
            stripe_payment_method_id=payment_method["id"]
        ).first()
        
        if existing:
            return
        
        company = self._get_company_from_customer_id(db, payment_method["customer"])
        if not company:
            return
        
        # Create payment method record
        pm = PaymentMethod(
            company_id=company.id,
            stripe_payment_method_id=payment_method["id"],
            stripe_customer_id=payment_method["customer"],
            type=PaymentMethodType(payment_method["type"]),
            is_default=False
        )
        
        # Set type-specific details
        if payment_method["type"] == "card":
            pm.card_brand = payment_method["card"]["brand"]
            pm.card_last4 = payment_method["card"]["last4"]
            pm.card_exp_month = payment_method["card"]["exp_month"]
            pm.card_exp_year = payment_method["card"]["exp_year"]
            pm.card_country = payment_method["card"]["country"]
        
        db.add(pm)
        db.commit()
    
    def _handle_payment_method_detached(self, db: Session, payment_method: Dict[str, Any]):
        """Handle payment method detached webhook."""
        pm = db.query(PaymentMethod).filter_by(
            stripe_payment_method_id=payment_method["id"]
        ).first()
        
        if pm:
            db.delete(pm)
            db.commit()
    
    def _create_invoice_from_stripe(self, db: Session, company: Company, stripe_invoice: Dict[str, Any]) -> Invoice:
        """Create invoice record from Stripe invoice object."""
        invoice = Invoice(
            company_id=company.id,
            stripe_invoice_id=stripe_invoice["id"],
            stripe_customer_id=stripe_invoice["customer"],
            invoice_number=stripe_invoice["number"] or f"INV-{stripe_invoice['id'][-8:]}",
            status=InvoiceStatus(stripe_invoice["status"]) if stripe_invoice["status"] != "draft" else InvoiceStatus.DRAFT,
            subtotal=stripe_invoice["subtotal"],
            tax=stripe_invoice["tax"] or 0,
            total=stripe_invoice["total"],
            amount_paid=stripe_invoice["amount_paid"],
            amount_remaining=stripe_invoice["amount_remaining"],
            currency=stripe_invoice["currency"].upper(),
            period_start=datetime.fromtimestamp(stripe_invoice["period_start"]),
            period_end=datetime.fromtimestamp(stripe_invoice["period_end"]),
            metadata=stripe_invoice.get("metadata", {})
        )
        
        # Set optional fields
        if stripe_invoice.get("due_date"):
            invoice.due_date = datetime.fromtimestamp(stripe_invoice["due_date"])
        
        if stripe_invoice.get("charge"):
            invoice.stripe_charge_id = stripe_invoice["charge"]
        
        if stripe_invoice.get("payment_intent"):
            invoice.stripe_payment_intent_id = stripe_invoice["payment_intent"]
        
        if stripe_invoice.get("invoice_pdf"):
            invoice.invoice_pdf_url = stripe_invoice["invoice_pdf"]
        
        if stripe_invoice.get("hosted_invoice_url"):
            invoice.hosted_invoice_url = stripe_invoice["hosted_invoice_url"]
        
        # Link to subscription if exists
        if stripe_invoice.get("subscription"):
            subscription = db.query(Subscription).filter_by(
                stripe_subscription_id=stripe_invoice["subscription"]
            ).first()
            if subscription:
                invoice.subscription_id = subscription.id
        
        # Store line items
        if stripe_invoice.get("lines"):
            invoice.line_items = [
                {
                    "description": line["description"],
                    "amount": line["amount"],
                    "quantity": line["quantity"],
                    "price_id": line["price"]["id"] if line.get("price") else None
                }
                for line in stripe_invoice["lines"]["data"]
            ]
        
        db.add(invoice)
        return invoice
    
    def _get_company_from_customer_id(self, db: Session, customer_id: str) -> Optional[Company]:
        """Get company from Stripe customer ID."""
        # First try to find by subscription
        subscription = db.query(Subscription).filter_by(
            stripe_customer_id=customer_id
        ).first()
        
        if subscription:
            return subscription.company
        
        # Try payment method
        payment_method = db.query(PaymentMethod).filter_by(
            stripe_customer_id=customer_id
        ).first()
        
        if payment_method:
            return payment_method.company
        
        # Try to get from Stripe customer metadata
        try:
            customer = stripe.Customer.retrieve(customer_id)
            if customer.metadata.get("company_id"):
                company = db.query(Company).filter_by(
                    id=UUID(customer.metadata["company_id"])
                ).first()
                return company
        except:
            pass
        
        return None
    
    def get_subscription_prices(self) -> List[Dict[str, Any]]:
        """Get available subscription prices from Stripe."""
        try:
            prices = stripe.Price.list(
                active=True,
                type="recurring",
                expand=["data.product"]
            )
            
            result = []
            for price in prices.data:
                if price.product.active and price.product.metadata.get("tier"):
                    result.append({
                        "price_id": price.id,
                        "product_id": price.product.id,
                        "product_name": price.product.name,
                        "tier": price.product.metadata["tier"],
                        "amount": price.unit_amount / 100,  # Convert to euros
                        "currency": price.currency,
                        "interval": price.recurring.interval,
                        "interval_count": price.recurring.interval_count,
                        "features": json.loads(price.product.metadata.get("features", "[]"))
                    })
            
            return sorted(result, key=lambda x: x["amount"])
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get subscription prices: {str(e)}")
            return []