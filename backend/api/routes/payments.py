"""Payments routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.dependencies.auth import get_current_active_user

router = APIRouter()


@router.get("/")
async def get_payments(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get payments data."""
    return {"status": "payments endpoint"}
