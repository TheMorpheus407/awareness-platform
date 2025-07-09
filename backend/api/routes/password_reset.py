"""Password_reset routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.dependencies.auth import require_authenticated

router = APIRouter()


@router.get("/")
async def get_password_reset(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_authenticated),
):
    """Get password_reset data."""
    return {"status": "password_reset endpoint"}
