"""Add payment tables

Revision ID: 004_add_payment_tables
Revises: 003_add_2fa_fields
Create Date: 2025-01-08 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_add_payment_tables'
down_revision: Union[str, None] = '003_add_2fa_support'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create subscription status enum
    op.execute("""
        CREATE TYPE subscriptionstatus AS ENUM (
            'trialing', 'active', 'incomplete', 'incomplete_expired',
            'past_due', 'canceled', 'unpaid'
        )
    """)
    
    # Create billing interval enum
    op.execute("CREATE TYPE billinginterval AS ENUM ('monthly', 'yearly')")
    
    # Create payment method type enum
    op.execute("CREATE TYPE paymentmethodtype AS ENUM ('card', 'sepa_debit', 'bank_transfer', 'invoice')")
    
    # Create invoice status enum
    op.execute("CREATE TYPE invoicestatus AS ENUM ('draft', 'open', 'paid', 'uncollectible', 'void')")
    
    # Create payment status enum
    op.execute("""
        CREATE TYPE paymentstatus AS ENUM (
            'pending', 'processing', 'succeeded', 'failed',
            'canceled', 'refunded', 'requires_action'
        )
    """)
    
    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=False),
        sa.Column('stripe_price_id', sa.String(length=255), nullable=False),
        sa.Column('stripe_product_id', sa.String(length=255), nullable=False),
        sa.Column('status', postgresql.ENUM('trialing', 'active', 'incomplete', 'incomplete_expired', 'past_due', 'canceled', 'unpaid', name='subscriptionstatus'), nullable=False),
        sa.Column('billing_interval', postgresql.ENUM('monthly', 'yearly', name='billinginterval'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_subscription_id')
    )
    op.create_index(op.f('ix_subscriptions_company_id'), 'subscriptions', ['company_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_stripe_customer_id'), 'subscriptions', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_stripe_subscription_id'), 'subscriptions', ['stripe_subscription_id'], unique=False)
    op.create_index('idx_subscription_company_status', 'subscriptions', ['company_id', 'status'], unique=False)
    op.create_index('idx_subscription_period', 'subscriptions', ['current_period_start', 'current_period_end'], unique=False)
    
    # Create payment_methods table
    op.create_table('payment_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_payment_method_id', sa.String(length=255), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=False),
        sa.Column('type', postgresql.ENUM('card', 'sepa_debit', 'bank_transfer', 'invoice', name='paymentmethodtype'), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('card_brand', sa.String(length=50), nullable=True),
        sa.Column('card_last4', sa.String(length=4), nullable=True),
        sa.Column('card_exp_month', sa.Integer(), nullable=True),
        sa.Column('card_exp_year', sa.Integer(), nullable=True),
        sa.Column('card_country', sa.String(length=2), nullable=True),
        sa.Column('bank_name', sa.String(length=255), nullable=True),
        sa.Column('bank_last4', sa.String(length=4), nullable=True),
        sa.Column('bank_country', sa.String(length=2), nullable=True),
        sa.Column('billing_name', sa.String(length=255), nullable=True),
        sa.Column('billing_email', sa.String(length=255), nullable=True),
        sa.Column('billing_phone', sa.String(length=50), nullable=True),
        sa.Column('billing_address_line1', sa.String(length=255), nullable=True),
        sa.Column('billing_address_line2', sa.String(length=255), nullable=True),
        sa.Column('billing_address_city', sa.String(length=100), nullable=True),
        sa.Column('billing_address_state', sa.String(length=100), nullable=True),
        sa.Column('billing_address_postal_code', sa.String(length=20), nullable=True),
        sa.Column('billing_address_country', sa.String(length=2), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_payment_method_id')
    )
    op.create_index(op.f('ix_payment_methods_company_id'), 'payment_methods', ['company_id'], unique=False)
    op.create_index(op.f('ix_payment_methods_id'), 'payment_methods', ['id'], unique=False)
    op.create_index(op.f('ix_payment_methods_stripe_customer_id'), 'payment_methods', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_payment_methods_stripe_payment_method_id'), 'payment_methods', ['stripe_payment_method_id'], unique=False)
    
    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(length=255), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=False),
        sa.Column('stripe_charge_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True),
        sa.Column('invoice_number', sa.String(length=100), nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'open', 'paid', 'uncollectible', 'void', name='invoicestatus'), nullable=False),
        sa.Column('subtotal', sa.Integer(), nullable=False),
        sa.Column('tax', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('amount_paid', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('amount_remaining', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('voided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invoice_pdf_url', sa.Text(), nullable=True),
        sa.Column('hosted_invoice_url', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('line_items', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number'),
        sa.UniqueConstraint('stripe_invoice_id')
    )
    op.create_index(op.f('ix_invoices_company_id'), 'invoices', ['company_id'], unique=False)
    op.create_index(op.f('ix_invoices_id'), 'invoices', ['id'], unique=False)
    op.create_index(op.f('ix_invoices_invoice_number'), 'invoices', ['invoice_number'], unique=False)
    op.create_index(op.f('ix_invoices_stripe_customer_id'), 'invoices', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_invoices_stripe_invoice_id'), 'invoices', ['stripe_invoice_id'], unique=False)
    op.create_index(op.f('ix_invoices_subscription_id'), 'invoices', ['subscription_id'], unique=False)
    op.create_index('idx_invoice_company_status', 'invoices', ['company_id', 'status'], unique=False)
    op.create_index('idx_invoice_due_date', 'invoices', ['due_date'], unique=False)
    op.create_index('idx_invoice_period', 'invoices', ['period_start', 'period_end'], unique=False)
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payment_method_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=False),
        sa.Column('stripe_charge_id', sa.String(length=255), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'processing', 'succeeded', 'failed', 'canceled', 'refunded', 'requires_action', name='paymentstatus'), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('payment_method_type', postgresql.ENUM('card', 'sepa_debit', 'bank_transfer', 'invoice', name='paymentmethodtype'), nullable=False),
        sa.Column('payment_method_details', sa.JSON(), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refunded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_code', sa.String(length=100), nullable=True),
        sa.Column('failure_message', sa.Text(), nullable=True),
        sa.Column('refund_amount', sa.Integer(), nullable=True),
        sa.Column('refund_reason', sa.String(length=255), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ),
        sa.ForeignKeyConstraint(['payment_method_id'], ['payment_methods.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_payment_intent_id')
    )
    op.create_index(op.f('ix_payments_company_id'), 'payments', ['company_id'], unique=False)
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_invoice_id'), 'payments', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_payments_payment_method_id'), 'payments', ['payment_method_id'], unique=False)
    op.create_index(op.f('ix_payments_stripe_charge_id'), 'payments', ['stripe_charge_id'], unique=False)
    op.create_index(op.f('ix_payments_stripe_payment_intent_id'), 'payments', ['stripe_payment_intent_id'], unique=False)
    op.create_index('idx_payment_company_status', 'payments', ['company_id', 'status'], unique=False)
    op.create_index('idx_payment_paid_at', 'payments', ['paid_at'], unique=False)
    
    # Create subscription_usage table
    op.create_table('subscription_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('stripe_usage_record_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_usage_company_id'), 'subscription_usage', ['company_id'], unique=False)
    op.create_index(op.f('ix_subscription_usage_id'), 'subscription_usage', ['id'], unique=False)
    op.create_index(op.f('ix_subscription_usage_stripe_usage_record_id'), 'subscription_usage', ['stripe_usage_record_id'], unique=False)
    op.create_index(op.f('ix_subscription_usage_subscription_id'), 'subscription_usage', ['subscription_id'], unique=False)
    op.create_index('idx_usage_company_period', 'subscription_usage', ['company_id', 'period_start', 'period_end'], unique=False)
    op.create_index('idx_usage_metric', 'subscription_usage', ['metric_name', 'period_start'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_table('subscription_usage')
    op.drop_table('payments')
    op.drop_table('invoices')
    op.drop_table('payment_methods')
    op.drop_table('subscriptions')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS invoicestatus')
    op.execute('DROP TYPE IF EXISTS paymentmethodtype')
    op.execute('DROP TYPE IF EXISTS billinginterval')
    op.execute('DROP TYPE IF EXISTS subscriptionstatus')