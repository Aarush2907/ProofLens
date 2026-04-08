"""Process entry point.

From the backend directory:

    uvicorn main:app --reload
"""

from app.main import app

__all__ = ["app"]
