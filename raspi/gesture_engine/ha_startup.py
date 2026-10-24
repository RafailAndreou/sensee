"""Start the bundled Home Assistant Compose service without blocking capture."""

import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import threading
from urllib.parse import urlsplit

from gesture_engine.log import get_logger

logger = get_logger(__name__)


def _is_local_url(url):
    if not url:
        return True
    host = urlsplit(url if "://" in url else "http://" + url).hostname
    local_hosts = {"localhost", "127.0.0.1", "::1", socket.gethostname().lower()}
    try:
        local_hosts.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError as error:
        logger.debug("Could not resolve this computer's addresses: %s", error)
    return host is not None and host.lower() in local_hosts


def ensure_home_assistant_started():
    mode = os.getenv("SENSEE_HA_AUTOSTART", "auto").strip().lower()
    if mode in {"0", "false", "off", "no"}:
        logger.info("Home Assistant Docker auto-start is disabled.")
        return False
    if mode == "auto":
        from server.ha_config import get_ha_config

        url, _ = get_ha_config()
        if not _is_local_url(url):
            logger.info("Using a remote Home Assistant; skipping local Docker startup.")
            return False

    root = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
    filename = "docker-compose.linux.yml" if platform.system() == "Linux" else "docker-compose.yml"
    configured = os.getenv("SENSEE_HA_COMPOSE_FILE")
    compose_file = Path(configured).expanduser().resolve() if configured else root / "docker" / filename
    if not compose_file.is_file():
        logger.warning("Home Assistant Compose file missing: %s. Set SENSEE_HA_COMPOSE_FILE to its location.", compose_file)
        return False
    docker = shutil.which("docker")
    if docker is None:
        logger.warning("Docker is not installed or not on PATH. Home Assistant auto-start skipped.")
        return False
    command = [docker, "compose", "-f", str(compose_file), "up", "-d", "--no-recreate", "homeassistant"]
    logger.info("Starting Home Assistant with Docker Compose (%s)...", compose_file)
    try:
        result = subprocess.run(
            command, cwd=str(compose_file.parent), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        logger.warning("Home Assistant Docker startup failed: %s", error)
        return False
    if result.returncode:
        logger.warning("Home Assistant Docker startup failed. Ensure Docker Desktop/Engine is running. %s",
                       (result.stderr or result.stdout).strip()[-2000:])
        return False
    logger.info("Home Assistant container is running. Its API may need a moment to finish starting.")
    return True


def start_home_assistant_in_background():
    worker = threading.Thread(target=ensure_home_assistant_started,
                              name="homeassistant-startup", daemon=True)
    worker.start()
    return worker
