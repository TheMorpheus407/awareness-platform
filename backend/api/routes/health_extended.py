"""Health_extended routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.dependencies.auth import get_current_active_user

router = APIRouter()


@router.get("/")
async def get_health_extended(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    """Get health_extended data."""
    return {"status": "health_extended endpoint"}
