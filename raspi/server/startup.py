import os

from gesture_engine.log import get_logger

logger = get_logger(__name__)


def run_uvicorn_with_port_retry(
    app_import_path,
    ip,
    host="0.0.0.0",
    ports_to_try=None,
    log_level=None,
    context_label="Server running at",
):
    import uvicorn

    if ports_to_try is None:
        ports_to_try = [8000, 8001, 8002, 8003, 8004]

    for attempt_port in ports_to_try:
        try:
            logger.info("%s: http://%s:%s", context_label, ip, attempt_port)
            os.environ["SENSEE_PORT"] = str(attempt_port)

            run_kwargs = {
                "app": app_import_path,
                "host": host,
                "port": attempt_port,
            }
            if log_level is not None:
                run_kwargs["log_level"] = log_level

            uvicorn.run(**run_kwargs)
            return attempt_port
        except OSError as e:
            error_str = str(e)
            if "10048" in error_str or "Address already in use" in error_str:
                if attempt_port == ports_to_try[-1]:
                    logger.error("All ports %s are already in use!", ports_to_try)
                    logger.error("Please kill the background process or restart your system.")
                    raise SystemExit(1)
                logger.warning("Port %s in use, trying %s...", attempt_port, attempt_port + 1)
            else:
                raise
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            raise

    raise SystemExit(1)