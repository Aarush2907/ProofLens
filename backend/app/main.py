import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import router
from app.core.config import get_settings
from app.core.database import init_database
from app.core.errors import AppError
from app.core.logging import configure_logging, database_dialect

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str, details: list[str] | None = None) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def _validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "The request is not valid."
    message = str(errors[0].get("msg", "The request is not valid."))
    prefix = "Value error, "
    if message.startswith(prefix):
        return message[len(prefix) :]
    return message


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        logger.info(
            "Starting %s %s (%s) with database dialect %s",
            settings.app_name,
            settings.app_version,
            settings.environment,
            database_dialect(settings.database_url),
        )
        try:
            init_database()
        except Exception:
            logger.exception(
                "Database initialisation failed. The API will stay up and report the database as unavailable."
            )
        yield

    docs_url = None if settings.environment == "production" else "/docs"
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "Last-Event-ID"],
    )

    @application.middleware("http")
    async def log_request(request: Request, call_next):
        response = await call_next(request)
        logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
        return response

    @application.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message),
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        details = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error.get("loc", []))
            details.append(f"{location}: {error.get('msg', 'invalid')}")
        return JSONResponse(
            status_code=422,
            content=_error_body("validation_error", _validation_message(exc), details),
        )

    @application.exception_handler(SQLAlchemyError)
    async def handle_database_error(request: Request, exc: SQLAlchemyError):
        logger.exception("Database error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=503,
            content=_error_body(
                "database_unavailable",
                "The database is unavailable, so this request could not be completed.",
            ),
        )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_error_body(
                "internal_error",
                "Something went wrong while handling that request.",
            ),
        )

    @application.get("/")
    def service_index():
        return {
            "service": settings.app_name,
            "health": f"{settings.api_prefix}/health",
            "docs": docs_url,
        }

    application.include_router(router, prefix=settings.api_prefix)
    return application


app = create_app()
