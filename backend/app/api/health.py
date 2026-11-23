import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Response

from app.core.config import get_settings
from app.core.database import database_is_reachable
from app.schemas.health import HealthReport

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthReport)
def read_health(response: Response) -> HealthReport:
    settings = get_settings()
    database_connected = database_is_reachable()
    qdrant = qdrant_status()
    healthy = database_connected and qdrant != "unavailable"
    if not healthy:
        response.status_code = 503

    return HealthReport(
        status="ok" if healthy else "degraded",
        service=settings.app_name,
        environment=settings.environment,
        database="connected" if database_connected else "unavailable",
        qdrant=qdrant,
        version=settings.app_version,
        time=datetime.now(timezone.utc),
    )


def qdrant_status() -> str:
    """Report a configured Qdrant URL. An empty URL is local file mode and is not probed.

    Probing the local file store from the API would open the same path the MCP
    process locks. The URL check uses HTTP only.
    """

    url = get_settings().qdrant_url.strip()
    if not url:
        return "not_configured"
    ready = url.rstrip("/") + "/readyz"
    try:
        response = httpx.get(ready, timeout=get_settings().qdrant_health_timeout_seconds)
    except httpx.HTTPError as exc:
        logger.warning("Qdrant is not reachable: %s", exc.__class__.__name__)
        return "unavailable"
    if response.status_code != 200:
        logger.warning("Qdrant readiness returned status %s", response.status_code)
        return "unavailable"
    return "connected"
