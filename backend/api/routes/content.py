"""Content routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.dependencies.auth import require_authenticated

router = APIRouter()


@router.get("/")
async def get_content(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_authenticated),
):
    """Get content data."""
    return {"status": "content endpoint"}
