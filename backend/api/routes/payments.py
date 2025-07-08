"""Payment API routes."""

from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...core.security import get_current_user, require_company_admin
from ...models import User, Company, Subscription, PaymentMethod, Invoice, Payment
from ...services.stripe_service import StripeService

router = APIRouter()
stripe_service = StripeService()


# Request/Response Models
class SetupIntentResponse(BaseModel):
    """Setup intent response."""
    client_secret: str
    setup_intent_id: str


class PaymentMethodCreate(BaseModel):
    """Payment method creation request."""
    payment_method_id: str
    set_as_default: bool = True


class PaymentMethodResponse(BaseModel):
    """Payment method response."""
    id: UUID
    type: str
    is_default: bool
    display_name: str
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    """Subscription creation request."""
    price_id: str
    payment_method_id: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    """Subscription update request."""
    price_id: str
    prorate: bool = True


class SubscriptionResponse(BaseModel):
    """Subscription response."""
    id: UUID
    status: str
    billing_interval: str
    amount: float
    currency: str
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None
    cancel_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    """Invoice response."""
    id: UUID
    invoice_number: str
    status: str
    total: int
    currency: str
    period_start: datetime
    period_end: datetime
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    invoice_pdf_url: Optional[str] = None
    hosted_invoice_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Payment response."""
    id: UUID
    status: str
    amount: int
    currency: str
    payment_method_type: str
    paid_at: Optional[datetime] = None
    failure_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionPriceResponse(BaseModel):
    """Subscription price response."""
    price_id: str
    product_id: str
    product_name: str
    tier: str
    amount: float
    currency: str
    interval: str
    interval_count: int
    features: List[str]


class UsageRecord(BaseModel):
    """Usage record request."""
    metric_name: str
    quantity: int
    timestamp: Optional[datetime] = None


# Customer endpoints
@router.post("/setup-intent", response_model=SetupIntentResponse)
async def create_setup_intent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a setup intent for collecting payment method."""
    company = current_user.company
    
    # Create Stripe customer if doesn't exist
    if not company.subscriptions.first() and not company.payment_methods.first():
        customer_id = stripe_service.create_customer(company, current_user.email)
    else:
        # Get existing customer ID
        subscription = company.subscriptions.first()
        payment_method = company.payment_methods.first()
        customer_id = subscription.stripe_customer_id if subscription else payment_method.stripe_customer_id
    
    # Create setup intent
    return stripe_service.create_setup_intent(customer_id)


# Payment Methods
@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def list_payment_methods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List company payment methods."""
    company = current_user.company
    payment_methods = company.payment_methods.filter_by(deleted_at=None).all()
    
    return [
        PaymentMethodResponse(
            id=pm.id,
            type=pm.type.value,
            is_default=pm.is_default,
            display_name=pm.display_name,
            card_brand=pm.card_brand,
            card_last4=pm.card_last4,
            card_exp_month=pm.card_exp_month,
            card_exp_year=pm.card_exp_year,
            created_at=pm.created_at
        )
        for pm in payment_methods
    ]


@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def add_payment_method(
    payment_method_data: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_company_admin)
):
    """Add a payment method."""
    company = current_user.company
    
    # Get customer ID
    subscription = company.subscriptions.first()
    payment_method = company.payment_methods.first()
    
    if subscription:
        customer_id = subscription.stripe_customer_id
    elif payment_method:
        customer_id = payment_method.stripe_customer_id
    else:
        customer_id = stripe_service.create_customer(company, current_user.email)
    
    # Save payment method
    pm = stripe_service.save_payment_method(
        db,
        company,
        payment_method_data.payment_method_id,
        customer_id,
        payment_method_data.set_as_default
    )
    
    return PaymentMethodResponse(
        id=pm.id,
        type=pm.type.value,
        is_default=pm.is_default,
        display_name=pm.display_name,
        card_brand=pm.card_brand,
        card_last4=pm.card_last4,
        card_exp_month=pm.card_exp_month,
        card_exp_year=pm.card_exp_year,
        created_at=pm.created_at
    )


@router.delete("/payment-methods/{payment_method_id}")
async def remove_payment_method(
    payment_method_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_company_admin)
):
    """Remove a payment method."""
    company = current_user.company
    pm = db.query(PaymentMethod).filter_by(
        id=payment_method_id,
        company_id=company.id
    ).first()
    
    if not pm:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    # Don't allow removing default payment method if there's an active subscription
    if pm.is_default and company.has_active_subscription:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove default payment method while subscription is active"
        )
    
    # Soft delete
    pm.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Payment method removed"}


# Subscriptions
@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current subscription."""
    company = current_user.company
    subscription = company.active_subscription
    
    if not subscription:
        return None
    
    return SubscriptionResponse(
        id=subscription.id,
        status=subscription.status.value,
        billing_interval=subscription.billing_interval.value,
        amount=float(subscription.amount),
        currency=subscription.currency,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_end=subscription.trial_end,
        cancel_at=subscription.cancel_at,
        created_at=subscription.created_at
    )


@router.post("/subscription", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_company_admin)
):
    """Create a subscription."""
    company = current_user.company
    
    # Check if already has active subscription
    if company.has_active_subscription:
        raise HTTPException(status_code=400, detail="Company already has an active subscription")
    
    # Get or create customer
    existing_pm = company.payment_methods.first()
    if existing_pm:
        customer_id = existing_pm.stripe_customer_id
    else:
        customer_id = stripe_service.create_customer(company, current_user.email)
    
    # Save payment method if provided
    if subscription_data.payment_method_id:
        stripe_service.save_payment_method(
            db,
            company,
            subscription_data.payment_method_id,
            customer_id,
            set_as_default=True
        )
    
    # Create subscription
    subscription = stripe_service.create_subscription(
        db,
        company,
        customer_id,
        subscription_data.price_id
    )
    
    return SubscriptionResponse(
        id=subscription.id,
        status=subscription.status.value,
        billing_interval=subscription.billing_interval.value,
        amount=float(subscription.amount),
        currency=subscription.currency,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_end=subscription.trial_end,
        cancel_at=subscription.cancel_at,
        created_at=subscription.created_at
    )


@router.put("/subscription", response_model=SubscriptionResponse)
async def update_subscription(
    update_data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_company_admin)
):
    """Update subscription plan."""
    company = current_user.company
    subscription = company.active_subscription
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    # Update subscription
    subscription = stripe_service.update_subscription(
        db,
        subscription,
        update_data.price_id,
        update_data.prorate
    )
    
    return SubscriptionResponse(
        id=subscription.id,
        status=subscription.status.value,
        billing_interval=subscription.billing_interval.value,
        amount=float(subscription.amount),
        currency=subscription.currency,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_end=subscription.trial_end,
        cancel_at=subscription.cancel_at,
        created_at=subscription.created_at
    )


@router.delete("/subscription")
async def cancel_subscription(
    immediate: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_company_admin)
):
    """Cancel subscription."""
    company = current_user.company
    subscription = company.active_subscription
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    # Cancel subscription
    stripe_service.cancel_subscription(db, subscription, immediate)
    
    return {"message": "Subscription cancelled successfully"}


# Invoices
@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List company invoices."""
    company = current_user.company
    invoices = company.invoices.order_by(
        Invoice.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    return [
        InvoiceResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            status=inv.status.value,
            total=inv.total,
            currency=inv.currency,
            period_start=inv.period_start,
            period_end=inv.period_end,
            due_date=inv.due_date,
            paid_at=inv.paid_at,
            invoice_pdf_url=inv.invoice_pdf_url,
            hosted_invoice_url=inv.hosted_invoice_url,
            created_at=inv.created_at
        )
        for inv in invoices
    ]


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get invoice details."""
    company = current_user.company
    invoice = db.query(Invoice).filter_by(
        id=invoice_id,
        company_id=company.id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return InvoiceResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        status=invoice.status.value,
        total=invoice.total,
        currency=invoice.currency,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
        due_date=invoice.due_date,
        paid_at=invoice.paid_at,
        invoice_pdf_url=invoice.invoice_pdf_url,
        hosted_invoice_url=invoice.hosted_invoice_url,
        created_at=invoice.created_at
    )


# Payments
@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List company payments."""
    company = current_user.company
    payments = company.payments.order_by(
        Payment.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    return [
        PaymentResponse(
            id=pay.id,
            status=pay.status.value,
            amount=pay.amount,
            currency=pay.currency,
            payment_method_type=pay.payment_method_type.value,
            paid_at=pay.paid_at,
            failure_message=pay.failure_message,
            created_at=pay.created_at
        )
        for pay in payments
    ]


# Pricing
@router.get("/prices", response_model=List[SubscriptionPriceResponse])
async def get_subscription_prices():
    """Get available subscription prices."""
    prices = stripe_service.get_subscription_prices()
    return prices


# Usage tracking
@router.post("/usage")
async def record_usage(
    usage_data: UsageRecord,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record usage for usage-based billing."""
    company = current_user.company
    subscription = company.active_subscription
    
    if not subscription:
        raise HTTPException(status_code=400, detail="No active subscription found")
    
    # Record usage
    usage = stripe_service.record_usage(
        db,
        subscription,
        usage_data.metric_name,
        usage_data.quantity,
        usage_data.timestamp
    )
    
    return {"message": "Usage recorded", "usage_id": str(usage.id)}


# Webhook endpoint
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db)
):
    """Handle Stripe webhooks."""
    # Get raw body
    payload = await request.body()
    
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")
    
    # Process webhook
    result = stripe_service.process_webhook(db, payload, stripe_signature)
    
    return result