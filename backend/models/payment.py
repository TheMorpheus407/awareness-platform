"""Payment, subscription, and invoice models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSON
import uuid

from .base import BaseUUIDModel

if TYPE_CHECKING:
    from .company import Company


class SubscriptionStatus:
    """Subscription status enumeration."""
    
    TRIALING = "trialing"
    ACTIVE = "active"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class BillingInterval:
    """Billing interval enumeration."""
    
    MONTHLY = "monthly"
    YEARLY = "yearly"


class PaymentMethodType:
    """Payment method type enumeration."""
    
    CARD = "card"
    SEPA_DEBIT = "sepa_debit"
    BANK_TRANSFER = "bank_transfer"
    INVOICE = "invoice"


class InvoiceStatus:
    """Invoice status enumeration."""
    
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    UNCOLLECTIBLE = "uncollectible"
    VOID = "void"


class PaymentStatus:
    """Payment status enumeration."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    REQUIRES_ACTION = "requires_action"


class Subscription(BaseUUIDModel):
    """Subscription model for managing company subscriptions."""
    
    __tablename__ = "subscriptions"
    
    # Foreign Keys
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    # Stripe Information
    stripe_subscription_id = Column(String(255), nullable=False, unique=True, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    stripe_price_id = Column(String(255), nullable=False)
    stripe_product_id = Column(String(255), nullable=False)
    
    # Subscription Details
    status = Column(
        ENUM('trialing', 'active', 'incomplete', 'incomplete_expired', 'past_due', 'canceled', 'unpaid', name='subscriptionstatus', create_type=False),
        nullable=False
    )
    billing_interval = Column(
        ENUM('monthly', 'yearly', name='billinginterval', create_type=False),
        nullable=False
    )
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, server_default='EUR')
    
    # Period Information
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Trial Information
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    
    # Cancellation Information
    cancel_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional Data
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    company: "Company" = relationship("Company", back_populates="subscriptions")
    invoices: List["Invoice"] = relationship("Invoice", back_populates="subscription")
    usage: List["SubscriptionUsage"] = relationship("SubscriptionUsage", back_populates="subscription")
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == SubscriptionStatus.ACTIVE
    
    @property
    def is_trialing(self) -> bool:
        """Check if subscription is in trial period."""
        return self.status == SubscriptionStatus.TRIALING
    
    @property
    def is_canceled(self) -> bool:
        """Check if subscription is canceled."""
        return self.status == SubscriptionStatus.CANCELED
    
    @property
    def has_payment_issues(self) -> bool:
        """Check if subscription has payment issues."""
        return self.status in [
            SubscriptionStatus.PAST_DUE,
            SubscriptionStatus.INCOMPLETE,
            SubscriptionStatus.INCOMPLETE_EXPIRED,
            SubscriptionStatus.UNPAID
        ]
    
    @property
    def monthly_amount(self) -> Decimal:
        """Get monthly amount."""
        if self.billing_interval == BillingInterval.YEARLY:
            return self.amount / 12
        return self.amount
    
    @property
    def yearly_amount(self) -> Decimal:
        """Get yearly amount."""
        if self.billing_interval == BillingInterval.MONTHLY:
            return self.amount * 12
        return self.amount
    
    def __repr__(self) -> str:
        """String representation of Subscription."""
        return f"<Subscription {self.stripe_subscription_id} ({self.status})>"


class PaymentMethod(BaseUUIDModel):
    """Payment method model for storing customer payment methods."""
    
    __tablename__ = "payment_methods"
    
    # Foreign Keys
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    
    # Stripe Information
    stripe_payment_method_id = Column(String(255), nullable=False, unique=True, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    
    # Payment Method Details
    type = Column(
        ENUM('card', 'sepa_debit', 'bank_transfer', 'invoice', name='paymentmethodtype', create_type=False),
        nullable=False
    )
    is_default = Column(Boolean, nullable=False, server_default=text('false'))
    
    # Card Information (if type is card)
    card_brand = Column(String(50), nullable=True)
    card_last4 = Column(String(4), nullable=True)
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)
    card_country = Column(String(2), nullable=True)
    
    # Bank Information (if type is sepa_debit or bank_transfer)
    bank_name = Column(String(255), nullable=True)
    bank_last4 = Column(String(4), nullable=True)
    bank_country = Column(String(2), nullable=True)
    
    # Billing Information
    billing_name = Column(String(255), nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_phone = Column(String(50), nullable=True)
    billing_address_line1 = Column(String(255), nullable=True)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_address_city = Column(String(100), nullable=True)
    billing_address_state = Column(String(100), nullable=True)
    billing_address_postal_code = Column(String(20), nullable=True)
    billing_address_country = Column(String(2), nullable=True)
    
    # Additional Data
    extra_data = Column(JSON, nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company: "Company" = relationship("Company", back_populates="payment_methods")
    payments: List["Payment"] = relationship("Payment", back_populates="payment_method")
    
    @property
    def is_card(self) -> bool:
        """Check if payment method is a card."""
        return self.type == PaymentMethodType.CARD
    
    @property
    def is_bank_account(self) -> bool:
        """Check if payment method is a bank account."""
        return self.type in [PaymentMethodType.SEPA_DEBIT, PaymentMethodType.BANK_TRANSFER]
    
    @property
    def display_name(self) -> str:
        """Get display name for payment method."""
        if self.is_card:
            return f"{self.card_brand} ****{self.card_last4}"
        elif self.is_bank_account:
            return f"{self.bank_name} ****{self.bank_last4}"
        return str(self.type)
    
    @property
    def is_expired(self) -> bool:
        """Check if payment method is expired (for cards)."""
        if not self.is_card:
            return False
        now = datetime.utcnow()
        if self.card_exp_year and self.card_exp_month:
            exp_date = datetime(self.card_exp_year, self.card_exp_month, 1)
            return now > exp_date
        return False
    
    def __repr__(self) -> str:
        """String representation of PaymentMethod."""
        return f"<PaymentMethod {self.type} {self.display_name}>"


class Invoice(BaseUUIDModel):
    """Invoice model for subscription billing."""
    
    __tablename__ = "invoices"
    
    # Foreign Keys
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=True, index=True)
    
    # Stripe Information
    stripe_invoice_id = Column(String(255), nullable=False, unique=True, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    stripe_charge_id = Column(String(255), nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    
    # Invoice Details
    invoice_number = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(
        ENUM('draft', 'open', 'paid', 'uncollectible', 'void', name='invoicestatus', create_type=False),
        nullable=False
    )
    
    # Amounts (in cents)
    subtotal = Column(Integer, nullable=False)
    tax = Column(Integer, nullable=False, server_default=text('0'))
    total = Column(Integer, nullable=False)
    amount_paid = Column(Integer, nullable=False, server_default=text('0'))
    amount_remaining = Column(Integer, nullable=False, server_default=text('0'))
    currency = Column(String(3), nullable=False, server_default='EUR')
    
    # Period Information
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Dates
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)
    
    # URLs
    invoice_pdf_url = Column(Text, nullable=True)
    hosted_invoice_url = Column(Text, nullable=True)
    
    # Additional Data
    extra_data = Column(JSON, nullable=True)
    line_items = Column(JSON, nullable=True)
    
    # Relationships
    company: "Company" = relationship("Company", back_populates="invoices")
    subscription: Optional["Subscription"] = relationship("Subscription", back_populates="invoices")
    payments: List["Payment"] = relationship("Payment", back_populates="invoice")
    
    @property
    def is_paid(self) -> bool:
        """Check if invoice is paid."""
        return self.status == InvoiceStatus.PAID
    
    @property
    def is_open(self) -> bool:
        """Check if invoice is open."""
        return self.status == InvoiceStatus.OPEN
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if not self.due_date or self.is_paid:
            return False
        return datetime.utcnow() > self.due_date
    
    @property
    def amount_in_currency(self) -> Decimal:
        """Get total amount in currency units (not cents)."""
        return Decimal(self.total) / 100
    
    @property
    def tax_rate(self) -> Decimal:
        """Calculate tax rate percentage."""
        if self.subtotal == 0:
            return Decimal(0)
        return (Decimal(self.tax) / Decimal(self.subtotal)) * 100
    
    def __repr__(self) -> str:
        """String representation of Invoice."""
        return f"<Invoice {self.invoice_number} ({self.status})>"


class Payment(BaseUUIDModel):
    """Payment model for tracking payment transactions."""
    
    __tablename__ = "payments"
    
    # Foreign Keys
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id'), nullable=True, index=True)
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey('payment_methods.id'), nullable=True, index=True)
    
    # Stripe Information
    stripe_payment_intent_id = Column(String(255), nullable=False, unique=True, index=True)
    stripe_charge_id = Column(String(255), nullable=True, index=True)
    
    # Payment Details
    status = Column(
        ENUM('pending', 'processing', 'succeeded', 'failed', 'canceled', 'refunded', 'requires_action', name='paymentstatus', create_type=False),
        nullable=False
    )
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), nullable=False, server_default='EUR')
    description = Column(Text, nullable=True)
    
    # Payment Method Information
    payment_method_type = Column(
        ENUM('card', 'sepa_debit', 'bank_transfer', 'invoice', name='paymentmethodtype', create_type=False),
        nullable=False
    )
    payment_method_details = Column(JSON, nullable=True)
    
    # Timestamps
    paid_at = Column(DateTime(timezone=True), nullable=True, index=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Failure Information
    failure_code = Column(String(100), nullable=True)
    failure_message = Column(Text, nullable=True)
    
    # Refund Information
    refund_amount = Column(Integer, nullable=True)  # Amount in cents
    refund_reason = Column(String(255), nullable=True)
    
    # Additional Data
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    company: "Company" = relationship("Company", back_populates="payments")
    invoice: Optional["Invoice"] = relationship("Invoice", back_populates="payments")
    payment_method: Optional["PaymentMethod"] = relationship("PaymentMethod", back_populates="payments")
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == PaymentStatus.SUCCEEDED
    
    @property
    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.FAILED
    
    @property
    def is_refunded(self) -> bool:
        """Check if payment was refunded."""
        return self.status == PaymentStatus.REFUNDED or self.refunded_at is not None
    
    @property
    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self.status in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]
    
    @property
    def amount_in_currency(self) -> Decimal:
        """Get amount in currency units (not cents)."""
        return Decimal(self.amount) / 100
    
    @property
    def refund_amount_in_currency(self) -> Optional[Decimal]:
        """Get refund amount in currency units (not cents)."""
        if self.refund_amount is None:
            return None
        return Decimal(self.refund_amount) / 100
    
    @property
    def net_amount(self) -> int:
        """Get net amount after refunds (in cents)."""
        if self.refund_amount:
            return self.amount - self.refund_amount
        return self.amount
    
    def __repr__(self) -> str:
        """String representation of Payment."""
        return f"<Payment {self.stripe_payment_intent_id} ({self.status})>"


class SubscriptionUsage(BaseUUIDModel):
    """Subscription usage tracking model for metered billing."""
    
    __tablename__ = "subscription_usage"
    
    # Foreign Keys
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False, index=True)
    
    # Usage Information
    metric_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=False)
    
    # Period Information
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Billing Information
    unit_price = Column(Numeric(precision=10, scale=4), nullable=True)
    total_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    
    # Stripe Information
    stripe_usage_record_id = Column(String(255), nullable=True, index=True)
    
    # Relationships
    company: "Company" = relationship("Company", back_populates="subscription_usage")
    subscription: "Subscription" = relationship("Subscription", back_populates="usage")
    
    @property
    def is_billable(self) -> bool:
        """Check if usage is billable."""
        return self.unit_price is not None and self.unit_price > 0
    
    def calculate_amount(self) -> Decimal:
        """Calculate total amount for usage."""
        if self.unit_price:
            return Decimal(self.quantity) * self.unit_price
        return Decimal(0)
    
    def __repr__(self) -> str:
        """String representation of SubscriptionUsage."""
        return f"<SubscriptionUsage {self.metric_name} ({self.quantity} {self.unit})>"