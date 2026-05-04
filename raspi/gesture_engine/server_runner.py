import threading
import time
import webbrowser

import requests

from server.startup import run_uvicorn_with_port_retry


DEFAULT_SERVER_PORTS = [8000, 8001, 8002, 8003, 8004]
SERVER_READY_RETRIES = 60
SERVER_READY_POLL_INTERVAL_SECONDS = 0.25
SERVER_READY_TIMEOUT_SECONDS = 0.4


def _open_dashboard_when_ready(ip: str, ports_to_try: list[int]) -> None:
    for _ in range(SERVER_READY_RETRIES):
        for port in ports_to_try:
            for host in ("sensee.local", ip):
                try:
                    response = requests.get(
                        f"http://{host}:{port}/ping",
                        timeout=SERVER_READY_TIMEOUT_SECONDS,
                    )
                    if response.status_code != 200:
                        continue
                    payload = response.json() if response.content else {}
                    if payload.get("status") != "ok":
                        continue
                    dashboard_url = f"http://{host}:{port}/"
                    print(f"🌍 Opening dashboard: {dashboard_url}")
                    webbrowser.open_new_tab(dashboard_url)
                    return
                except (ValueError, requests.exceptions.RequestException):
                    continue
        time.sleep(SERVER_READY_POLL_INTERVAL_SECONDS)

    print("⚠️ Dashboard auto-open timed out. Open the printed portal URL manually.")


def start_fastapi_server_in_background(get_local_ip, auto_open_dashboard: bool = True):
    ip, _ = get_local_ip()
    ports_to_try = list(DEFAULT_SERVER_PORTS)

    def _run_server():
        run_uvicorn_with_port_retry(
            app_import_path="server.main:app",
            ip=ip,
            ports_to_try=ports_to_try,
            log_level="info",
            context_label="Access the configuration portal at",
        )

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()

    if auto_open_dashboard:
        browser_thread = threading.Thread(
            target=_open_dashboard_when_ready,
            args=(ip, ports_to_try),
            daemon=True,
        )
        browser_thread.start()

    return ip, server_thread
