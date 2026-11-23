"""Close out runs that a server restart cut off.

A research run is a background task inside the API process, so a restart
ends it without a trace. A run waiting for review is not affected: its state
is in the checkpoint, not in a running task. This assumes one API process.
"""

import logging

from sqlalchemy import update

from app.core.database import SessionLocal
from app.models.research_question import FAILED, RUNNING, ResearchQuestion

logger = logging.getLogger(__name__)

INTERRUPTED_MESSAGE = "This run was interrupted by a server restart. Ask the question again to rerun it."


def mark_interrupted_runs() -> int:
    db = SessionLocal()
    try:
        result = db.execute(
            update(ResearchQuestion)
            .where(ResearchQuestion.status == RUNNING, ResearchQuestion.stage != "awaiting_review")
            .values(status=FAILED, stage="failed", error_message=INTERRUPTED_MESSAGE)
        )
        db.commit()
        count = result.rowcount or 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    if count:
        logger.warning("Marked %s interrupted research run(s) as failed", count)
    return count
