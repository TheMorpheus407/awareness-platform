"""Payment routes."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from api.dependencies.auth import get_current_active_user, require_company_admin
from api.dependencies.common import get_db, get_pagination_params
from models.payment import Payment, PaymentStatus
from models.user import User, UserRole
from schemas.base import PaginatedResponse
from services.stripe_service import StripeService

router = APIRouter()


@router.post("/create-checkout-session")
async def create_checkout_session(
    price_id: str,
    quantity: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Create Stripe checkout session.
    
    Args:
        price_id: Stripe price ID
        quantity: Number of licenses
        db: Database session
        current_user: Current authenticated user (must be company admin)
        
    Returns:
        Checkout session URL
    """
    stripe_service = StripeService()
    
    try:
        # Create checkout session
        session = await stripe_service.create_checkout_session(
            price_id=price_id,
            quantity=quantity,
            customer_email=current_user.email,
            client_reference_id=str(current_user.company_id),
            metadata={
                "company_id": str(current_user.company_id),
                "user_id": str(current_user.id),
            },
        )
        
        # Create payment record
        payment = Payment(
            company_id=current_user.company_id,
            stripe_payment_intent_id=session.payment_intent,
            stripe_checkout_session_id=session.id,
            amount=session.amount_total / 100,  # Convert from cents
            currency=session.currency,
            status=PaymentStatus.PENDING,
            description=f"License purchase - {quantity} seats",
        )
        db.add(payment)
        await db.commit()
        
        return {
            "checkout_url": session.url,
            "session_id": session.id,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/webhook")
async def stripe_webhook(
    payload: dict,
    stripe_signature: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Handle Stripe webhook events.
    
    Args:
        payload: Webhook payload
        stripe_signature: Stripe signature header
        db: Database session
        
    Returns:
        Success response
    """
    stripe_service = StripeService()
    
    try:
        # Verify webhook signature
        event = stripe_service.verify_webhook_signature(
            payload, stripe_signature
        )
        
        # Handle different event types
        if event.type == "checkout.session.completed":
            session = event.data.object
            
            # Update payment record
            result = await db.execute(
                select(Payment).where(
                    Payment.stripe_checkout_session_id == session.id
                )
            )
            payment = result.scalar_one_or_none()
            
            if payment:
                payment.status = PaymentStatus.COMPLETED
                payment.paid_at = datetime.utcnow()
                await db.commit()
                
                # TODO: Activate subscription/licenses
                
        elif event.type == "payment_intent.payment_failed":
            payment_intent = event.data.object
            
            # Update payment record
            result = await db.execute(
                select(Payment).where(
                    Payment.stripe_payment_intent_id == payment_intent.id
                )
            )
            payment = result.scalar_one_or_none()
            
            if payment:
                payment.status = PaymentStatus.FAILED
                await db.commit()
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/history", response_model=PaginatedResponse)
async def get_payment_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
    pagination: tuple[int, int] = Depends(get_pagination_params),
    status: Optional[PaymentStatus] = Query(None, description="Filter by status"),
) -> PaginatedResponse:
    """
    Get payment history for company.
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be company admin)
        pagination: Offset and limit
        status: Filter by payment status
        
    Returns:
        Paginated payment history
    """
    offset, limit = pagination
    
    # Base query
    query = select(Payment).where(
        Payment.company_id == current_user.company_id
    )
    
    # Apply status filter
    if status:
        query = query.where(Payment.status == status)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Payment.created_at.desc()).offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    payments = result.scalars().all()
    
    return PaginatedResponse(
        items=payments,
        total=total,
        page=(offset // limit) + 1,
        size=limit,
        pages=(total + limit - 1) // limit,
    )


@router.get("/subscription/status")
async def get_subscription_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get current subscription status.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Subscription status information
    """
    # TODO: Implement subscription status check
    # This is a placeholder implementation
    
    return {
        "status": "active",
        "plan": "enterprise",
        "seats": 100,
        "used_seats": 45,
        "renewal_date": "2024-12-31",
        "features": [
            "unlimited_courses",
            "phishing_simulations",
            "advanced_analytics",
            "priority_support",
        ],
    }


@router.post("/subscription/cancel")
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_company_admin),
) -> dict:
    """
    Cancel subscription.
    
    Args:
        db: Database session
        current_user: Current authenticated user (must be company admin)
        
    Returns:
        Cancellation confirmation
    """
    # TODO: Implement subscription cancellation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Subscription cancellation not yet implemented"
    )