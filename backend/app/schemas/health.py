from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthReport(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    environment: str
    database: Literal["connected", "unavailable"]
    qdrant: Literal["connected", "unavailable", "not_configured"]
    version: str
    time: datetime
