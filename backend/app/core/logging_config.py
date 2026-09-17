import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging() -> None:
    """Send the app's own loggers (app.*) to stderr at INFO.

    Uvicorn only configures its own loggers. Without this, INFO messages from
    app code - such as the startup storage mode - are dropped, and warnings
    print with no timestamp or level. Records still propagate, so an outer
    logging setup (or pytest's caplog) sees them too.
    """
    logger = logging.getLogger("app")
    if logger.handlers:
        return  # already configured, e.g. the module was imported twice
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
