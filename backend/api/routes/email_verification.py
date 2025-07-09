"""Email_verification routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.dependencies.auth import require_authenticated

router = APIRouter()


@router.get("/")
async def get_email_verification(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_authenticated),
):
    """Get email_verification data."""
    return {"status": "email_verification endpoint"}
