import logging


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    # Uvicorn writes its own access line. The request middleware logs the same
    # request, so the access logger is kept quiet to avoid two lines per call.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def database_dialect(database_url: str) -> str:
    """Return the driver name only. The URL can contain a password."""
    return database_url.split(":", 1)[0]
