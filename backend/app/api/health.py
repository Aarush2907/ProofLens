from datetime import datetime, timezone

from fastapi import APIRouter, Response

from app.core.config import get_settings
from app.core.database import database_is_reachable
from app.schemas.health import HealthReport

router = APIRouter()


@router.get("/health", response_model=HealthReport)
def read_health(response: Response) -> HealthReport:
    settings = get_settings()
    database_connected = database_is_reachable()
    if not database_connected:
        response.status_code = 503

    return HealthReport(
        status="ok" if database_connected else "degraded",
        service=settings.app_name,
        environment=settings.environment,
        database="connected" if database_connected else "unavailable",
        version=settings.app_version,
        time=datetime.now(timezone.utc),
    )
