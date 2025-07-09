"""Payment-related models for Stripe integration."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
import enum
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, Numeric, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .user import User


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    REQUIRES_ACTION = "requires_action"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enumeration."""
    TRIALING = "trialing"
    ACTIVE = "active"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration."""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    UNCOLLECTIBLE = "uncollectible"
    VOID = "void"


class PaymentMethodType(str, enum.Enum):
    """Payment method type enumeration."""
    CARD = "card"
    SEPA_DEBIT = "sepa_debit"
    BANK_TRANSFER = "bank_transfer"
    INVOICE = "invoice"


class BillingInterval(str, enum.Enum):
    """Billing interval enumeration."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Subscription(Base):
    """Subscription model for managing company subscriptions."""
    
    __tablename__ = "subscriptions"
    
    # Foreign keys
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    company = relationship("Company", back_populates="subscriptions")
    
    # Relationships
    invoices = relationship("Invoice", back_populates="subscription", lazy="dynamic")
    usage_records = relationship("SubscriptionUsage", back_populates="subscription", lazy="dynamic")
    
    # Stripe identifiers
    stripe_subscription_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    stripe_price_id = Column(String(255), nullable=False)
    stripe_product_id = Column(String(255), nullable=False)
    
    # Subscription details
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    billing_interval = Column(Enum(BillingInterval), nullable=False, default=BillingInterval.MONTHLY)
    
    # Pricing
    amount = Column(Numeric(10, 2), nullable=False)  # Amount in euros
    currency = Column(String(3), nullable=False, default="EUR")
    
    # Dates
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_subscription_company_status', 'company_id', 'status'),
        Index('idx_subscription_period', 'current_period_start', 'current_period_end'),
    )
    
    def __repr__(self) -> str:
        return f"<Subscription {self.stripe_subscription_id}>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == SubscriptionStatus.ACTIVE
    
    @property
    def is_trialing(self) -> bool:
        """Check if subscription is in trial period."""
        return self.status == SubscriptionStatus.TRIALING
    
    @property
    def is_past_due(self) -> bool:
        """Check if subscription payment is past due."""
        return self.status == SubscriptionStatus.PAST_DUE


class PaymentMethod(Base):
    """Payment method model for storing customer payment methods."""
    
    __tablename__ = "payment_methods"
    
    # Foreign keys
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    company = relationship("Company", back_populates="payment_methods")
    
    # Stripe identifiers
    stripe_payment_method_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    
    # Payment method details
    type = Column(Enum(PaymentMethodType), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    
    # Card details (only for card type)
    card_brand = Column(String(50), nullable=True)
    card_last4 = Column(String(4), nullable=True)
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)
    card_country = Column(String(2), nullable=True)
    
    # Bank account details (for SEPA/bank transfer)
    bank_name = Column(String(255), nullable=True)
    bank_last4 = Column(String(4), nullable=True)
    bank_country = Column(String(2), nullable=True)
    
    # Billing details
    billing_name = Column(String(255), nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_phone = Column(String(50), nullable=True)
    billing_address_line1 = Column(String(255), nullable=True)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_address_city = Column(String(100), nullable=True)
    billing_address_state = Column(String(100), nullable=True)
    billing_address_postal_code = Column(String(20), nullable=True)
    billing_address_country = Column(String(2), nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<PaymentMethod {self.stripe_payment_method_id}>"
    
    @property
    def display_name(self) -> str:
        """Get a display name for the payment method."""
        if self.type == PaymentMethodType.CARD:
            return f"{self.card_brand} •••• {self.card_last4}"
        elif self.type in [PaymentMethodType.SEPA_DEBIT, PaymentMethodType.BANK_TRANSFER]:
            return f"{self.bank_name} •••• {self.bank_last4}"
        return str(self.type.value)


class Invoice(Base):
    """Invoice model for tracking billing history."""
    
    __tablename__ = "invoices"
    
    # Foreign keys
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    company = relationship("Company", back_populates="invoices")
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True, index=True)
    subscription = relationship("Subscription", back_populates="invoices")
    
    # Relationships
    payments = relationship("Payment", back_populates="invoice", lazy="dynamic")
    
    # Stripe identifiers
    stripe_invoice_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    stripe_charge_id = Column(String(255), nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    
    # Invoice details
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT)
    
    # Amounts (in cents)
    subtotal = Column(Integer, nullable=False)
    tax = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False)
    amount_paid = Column(Integer, nullable=False, default=0)
    amount_remaining = Column(Integer, nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="EUR")
    
    # Dates
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)
    
    # URLs
    invoice_pdf_url = Column(Text, nullable=True)
    hosted_invoice_url = Column(Text, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Line items stored as JSON
    line_items = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_invoice_company_status', 'company_id', 'status'),
        Index('idx_invoice_period', 'period_start', 'period_end'),
        Index('idx_invoice_due_date', 'due_date'),
    )
    
    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}>"
    
    @property
    def is_paid(self) -> bool:
        """Check if invoice is paid."""
        return self.status == InvoiceStatus.PAID
    
    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.due_date and self.status == InvoiceStatus.OPEN:
            return datetime.utcnow() > self.due_date
        return False
    
    @property
    def amount_in_euros(self) -> Decimal:
        """Get total amount in euros."""
        return Decimal(self.total) / 100
    
    @property
    def tax_in_euros(self) -> Decimal:
        """Get tax amount in euros."""
        return Decimal(self.tax) / 100


class Payment(Base):
    """Payment model for tracking individual payments."""
    
    __tablename__ = "payments"
    
    # Foreign keys
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    company = relationship("Company", back_populates="payments")
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True, index=True)
    invoice = relationship("Invoice", back_populates="payments")
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey("payment_methods.id"), nullable=True, index=True)
    payment_method = relationship("PaymentMethod")
    
    # Stripe identifiers
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_charge_id = Column(String(255), nullable=True, index=True)
    
    # Payment details
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), nullable=False, default="EUR")
    description = Column(Text, nullable=True)
    
    # Payment method details (snapshot at time of payment)
    payment_method_type = Column(Enum(PaymentMethodType), nullable=False)
    payment_method_details = Column(JSON, nullable=True)
    
    # Dates
    paid_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error details
    failure_code = Column(String(100), nullable=True)
    failure_message = Column(Text, nullable=True)
    
    # Refund details
    refund_amount = Column(Integer, nullable=True)
    refund_reason = Column(String(255), nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_company_status', 'company_id', 'status'),
        Index('idx_payment_paid_at', 'paid_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Payment {self.stripe_payment_intent_id}>"
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == PaymentStatus.SUCCEEDED
    
    @property
    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.FAILED
    
    @property
    def amount_in_euros(self) -> Decimal:
        """Get amount in euros."""
        return Decimal(self.amount) / 100


class SubscriptionUsage(Base):
    """Track usage-based billing metrics."""
    
    __tablename__ = "subscription_usage"
    
    # Foreign keys
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    company = relationship("Company", back_populates="usage_records")
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False, index=True)
    subscription = relationship("Subscription", back_populates="usage_records")
    
    # Usage details
    metric_name = Column(String(100), nullable=False)  # e.g., 'active_users', 'training_completions'
    quantity = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=False)  # e.g., 'user', 'completion'
    
    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Billing
    unit_price = Column(Numeric(10, 4), nullable=True)  # Price per unit in euros
    total_amount = Column(Numeric(10, 2), nullable=True)  # Total amount in euros
    
    # Stripe
    stripe_usage_record_id = Column(String(255), nullable=True, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_company_period', 'company_id', 'period_start', 'period_end'),
        Index('idx_usage_metric', 'metric_name', 'period_start'),
    )
    
    def __repr__(self) -> str:
        return f"<SubscriptionUsage {self.metric_name} - {self.quantity}>"


# Update relationships in existing models
# This will be done in a separate step to update company.py and user.py