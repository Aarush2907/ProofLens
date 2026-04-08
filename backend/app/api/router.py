from fastapi import APIRouter

from app.api import health, research

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(research.router, tags=["research"])
