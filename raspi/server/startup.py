import errno
import os
import socket
import threading

from gesture_engine.log import get_logger

logger = get_logger(__name__)


def run_uvicorn_with_port_retry(app_import_path, ip, host="0.0.0.0", ports_to_try=None,
                                log_level=None, context_label="Server running at", stop_event=None):
    """Reserve the socket before startup so only bind failures trigger retries."""
    import uvicorn

    ports = [8000, 8001, 8002, 8003, 8004] if ports_to_try is None else ports_to_try
    for port in ports:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind((host, port))
        except OSError as error:
            listener.close()
            if error.errno != errno.EADDRINUSE:
                raise
            logger.warning("Port %s is in use; trying the next candidate.", port)
            continue
        try:
            actual_port = listener.getsockname()[1]
            listener.listen(128)
            listener.setblocking(False)
            os.environ["SENSEE_PORT"] = str(actual_port)
            config = uvicorn.Config(app_import_path, host=host, port=actual_port,
                                    log_level=log_level or "info")
            server = uvicorn.Server(config)
            monitor = None
            if stop_event is not None:
                def monitor_shutdown():
                    stop_event.wait()
                    server.should_exit = True
                monitor = threading.Thread(target=monitor_shutdown, daemon=True)
                monitor.start()
            logger.info("%s: http://%s:%s", context_label, ip, actual_port)
            try:
                server.run(sockets=[listener])
            finally:
                if monitor is not None:
                    stop_event.set()
                    monitor.join(timeout=1)
            return actual_port
        finally:
            listener.close()
    raise OSError(errno.EADDRINUSE, f"All candidate ports are in use: {ports}")
