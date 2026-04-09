import threading

from server.startup import run_uvicorn_with_port_retry


def start_fastapi_server_in_background(get_local_ip):
    ip, _ = get_local_ip()

    def _run_server():
        run_uvicorn_with_port_retry(
            app_import_path="server.main:app",
            ip=ip,
            log_level="info",
            context_label="Access the configuration portal at",
        )

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    return ip, server_thread
