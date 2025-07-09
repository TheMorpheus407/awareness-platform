"""Tests for payment API endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import status
from sqlalchemy.orm import Session

from models.company import Company
from models.user import User
from models.payment import Subscription, PaymentMethod, Invoice, Payment, SubscriptionStatus, PaymentMethodType, InvoiceStatus, PaymentStatus
from services.stripe_service import StripeService


class TestPaymentEndpoints:
    """Test payment-related endpoints."""
    
    @patch('services.stripe_service.stripe')
    def test_create_setup_intent(self, mock_stripe, client, auth_headers, db_session):
        """Test creating a setup intent."""
        # Mock Stripe response
        mock_stripe.SetupIntent.create.return_value = MagicMock(
            id="seti_test123",
            client_secret="seti_test123_secret"
        )
        
        response = client.post(
            "/api/v1/payments/setup-intent",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "client_secret" in data
        assert "setup_intent_id" in data
    
    @patch('services.stripe_service.stripe')
    def test_add_payment_method(self, mock_stripe, client, auth_headers, test_company, db_session):
        """Test adding a payment method."""
        # Mock Stripe responses
        mock_pm = MagicMock(
            id="pm_test123",
            type="card",
            customer="cus_test123",
            card=MagicMock(
                brand="visa",
                last4="4242",
                exp_month=12,
                exp_year=2025,
                country="US"
            ),
            billing_details=MagicMock(
                name="Test User",
                email="test@example.com",
                phone=None,
                address=None
            )
        )
        mock_stripe.PaymentMethod.retrieve.return_value = mock_pm
        mock_stripe.PaymentMethod.attach.return_value = mock_pm
        mock_stripe.Customer.create.return_value = MagicMock(id="cus_test123")
        
        response = client.post(
            "/api/v1/payments/payment-methods",
            json={
                "payment_method_id": "pm_test123",
                "set_as_default": True
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["type"] == "card"
        assert data["is_default"] is True
        assert data["card_last4"] == "4242"
        
        # Verify database
        pm = db_session.query(PaymentMethod).filter_by(
            stripe_payment_method_id="pm_test123"
        ).first()
        assert pm is not None
        assert pm.company_id == test_company.id
    
    def test_list_payment_methods(self, client, auth_headers, test_company, db_session):
        """Test listing payment methods."""
        # Create test payment methods
        pm1 = PaymentMethod(
            company_id=test_company.id,
            stripe_payment_method_id="pm_test1",
            stripe_customer_id="cus_test123",
            type=PaymentMethodType.CARD,
            is_default=True,
            card_brand="visa",
            card_last4="4242",
            card_exp_month=12,
            card_exp_year=2025
        )
        pm2 = PaymentMethod(
            company_id=test_company.id,
            stripe_payment_method_id="pm_test2",
            stripe_customer_id="cus_test123",
            type=PaymentMethodType.SEPA_DEBIT,
            is_default=False,
            bank_name="Test Bank",
            bank_last4="1234"
        )
        db_session.add_all([pm1, pm2])
        db_session.commit()
        
        response = client.get(
            "/api/v1/payments/payment-methods",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["is_default"] is True
        assert data[0]["card_last4"] == "4242"
        assert data[1]["type"] == "sepa_debit"
    
    @patch('services.stripe_service.stripe')
    def test_create_subscription(self, mock_stripe, client, auth_headers, test_company, db_session):
        """Test creating a subscription."""
        # Mock Stripe responses
        mock_sub = MagicMock(
            id="sub_test123",
            status="trialing",
            items=MagicMock(data=[MagicMock(price="price_test123")]),
            current_period_start=int(datetime.utcnow().timestamp()),
            current_period_end=int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            trial_start=int(datetime.utcnow().timestamp()),
            trial_end=int((datetime.utcnow() + timedelta(days=14)).timestamp()),
            cancel_at=None,
            canceled_at=None
        )
        mock_stripe.Subscription.create.return_value = mock_sub
        
        mock_price = MagicMock(
            unit_amount=4900,
            currency="eur",
            recurring=MagicMock(interval="month"),
            product="prod_test123"
        )
        mock_stripe.Price.retrieve.return_value = mock_price
        
        mock_product = MagicMock(
            id="prod_test123",
            name="Starter Plan",
            metadata={"tier": "starter"}
        )
        mock_stripe.Product.retrieve.return_value = mock_product
        
        mock_stripe.Customer.create.return_value = MagicMock(id="cus_test123")
        
        # Create payment method first
        pm = PaymentMethod(
            company_id=test_company.id,
            stripe_payment_method_id="pm_test123",
            stripe_customer_id="cus_test123",
            type=PaymentMethodType.CARD,
            is_default=True
        )
        db_session.add(pm)
        db_session.commit()
        
        response = client.post(
            "/api/v1/payments/subscription",
            json={
                "price_id": "price_test123",
                "payment_method_id": "pm_test123"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "trialing"
        assert data["billing_interval"] == "monthly"
        assert data["amount"] == 49.0
        
        # Verify database
        sub = db_session.query(Subscription).filter_by(
            stripe_subscription_id="sub_test123"
        ).first()
        assert sub is not None
        assert sub.company_id == test_company.id
        assert sub.status == SubscriptionStatus.TRIALING
    
    def test_get_subscription(self, client, auth_headers, test_company, db_session):
        """Test getting current subscription."""
        # Create test subscription
        sub = Subscription(
            company_id=test_company.id,
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            stripe_price_id="price_test123",
            stripe_product_id="prod_test123",
            status=SubscriptionStatus.ACTIVE,
            billing_interval="monthly",
            amount=49.00,
            currency="EUR",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(sub)
        db_session.commit()
        
        response = client.get(
            "/api/v1/payments/subscription",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "active"
        assert data["amount"] == 49.0
        assert data["billing_interval"] == "monthly"
    
    @patch('services.stripe_service.stripe')
    def test_cancel_subscription(self, mock_stripe, client, auth_headers, test_company, db_session):
        """Test canceling a subscription."""
        # Create test subscription
        sub = Subscription(
            company_id=test_company.id,
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            stripe_price_id="price_test123",
            stripe_product_id="prod_test123",
            status=SubscriptionStatus.ACTIVE,
            billing_interval="monthly",
            amount=49.00,
            currency="EUR",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(sub)
        db_session.commit()
        
        # Mock Stripe response
        mock_stripe.Subscription.modify.return_value = MagicMock(
            status="active",
            cancel_at_period_end=True,
            cancel_at=int((datetime.utcnow() + timedelta(days=30)).timestamp()),
            canceled_at=int(datetime.utcnow().timestamp())
        )
        
        response = client.delete(
            "/api/v1/payments/subscription",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify subscription was updated
        db_session.refresh(sub)
        assert sub.cancel_at is not None
    
    def test_list_invoices(self, client, auth_headers, test_company, db_session):
        """Test listing invoices."""
        # Create test invoices
        inv1 = Invoice(
            company_id=test_company.id,
            stripe_invoice_id="in_test1",
            stripe_customer_id="cus_test123",
            invoice_number="INV-2024-001",
            status=InvoiceStatus.PAID,
            subtotal=4900,
            tax=931,
            total=5831,
            amount_paid=5831,
            amount_remaining=0,
            currency="EUR",
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            paid_at=datetime.utcnow() - timedelta(days=25)
        )
        inv2 = Invoice(
            company_id=test_company.id,
            stripe_invoice_id="in_test2",
            stripe_customer_id="cus_test123",
            invoice_number="INV-2024-002",
            status=InvoiceStatus.OPEN,
            subtotal=4900,
            tax=931,
            total=5831,
            amount_paid=0,
            amount_remaining=5831,
            currency="EUR",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=30),
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        db_session.add_all([inv1, inv2])
        db_session.commit()
        
        response = client.get(
            "/api/v1/payments/invoices",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["status"] == "open"  # Most recent first
        assert data[0]["total"] == 5831
        assert data[1]["status"] == "paid"
    
    def test_get_pricing(self, client, db_session):
        """Test getting subscription pricing."""
        with patch('backend.services.stripe_service.stripe') as mock_stripe:
            # Mock Stripe price list
            mock_prices = MagicMock()
            mock_prices.data = [
                MagicMock(
                    id="price_starter",
                    unit_amount=4900,
                    currency="eur",
                    recurring=MagicMock(interval="month", interval_count=1),
                    product=MagicMock(
                        id="prod_starter",
                        name="Starter Plan",
                        active=True,
                        metadata={"tier": "starter", "features": '["Feature 1", "Feature 2"]'}
                    )
                ),
                MagicMock(
                    id="price_premium",
                    unit_amount=14900,
                    currency="eur",
                    recurring=MagicMock(interval="month", interval_count=1),
                    product=MagicMock(
                        id="prod_premium",
                        name="Premium Plan",
                        active=True,
                        metadata={"tier": "premium", "features": '["All features", "Priority support"]'}
                    )
                )
            ]
            mock_stripe.Price.list.return_value = mock_prices
            
            response = client.get("/api/v1/payments/prices")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["amount"] == 49.0  # Sorted by amount
            assert data[0]["tier"] == "starter"
            assert len(data[0]["features"]) == 2
            assert data[1]["amount"] == 149.0
            assert data[1]["tier"] == "premium"
    
    @patch('services.stripe_service.stripe')
    def test_webhook_subscription_updated(self, mock_stripe, client, test_company, db_session):
        """Test handling subscription updated webhook."""
        # Create test subscription
        sub = Subscription(
            company_id=test_company.id,
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            stripe_price_id="price_test123",
            stripe_product_id="prod_test123",
            status=SubscriptionStatus.TRIALING,
            billing_interval="monthly",
            amount=49.00,
            currency="EUR",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(sub)
        db_session.commit()
        
        # Mock webhook event
        event_data = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "status": "active",
                    "current_period_start": int(datetime.utcnow().timestamp()),
                    "current_period_end": int((datetime.utcnow() + timedelta(days=30)).timestamp()),
                    "cancel_at": None,
                    "canceled_at": None
                }
            }
        }
        
        mock_stripe.Webhook.construct_event.return_value = event_data
        
        response = client.post(
            "/api/v1/payments/webhook",
            data=b"test_payload",
            headers={"Stripe-Signature": "test_signature"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify subscription was updated
        db_session.refresh(sub)
        assert sub.status == SubscriptionStatus.ACTIVE
        
        # Verify company status was updated
        db_session.refresh(test_company)
        assert test_company.status.value == "active"