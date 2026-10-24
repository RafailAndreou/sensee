"""Discover Android TVs on Sensee's LAN, including outside an HA container."""

import threading

from zeroconf import IPVersion, ServiceBrowser, ServiceListener, Zeroconf

from gesture_engine.log import get_logger

logger = get_logger(__name__)
ANDROID_TV_SERVICE = "_androidtvremote2._tcp.local."


class _TVListener(ServiceListener):
    def __init__(self):
        self.devices = {}
        self.lock = threading.Lock()

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name, timeout=500)
        if info is None:
            return
        addresses = info.parsed_addresses(IPVersion.V4Only)
        if not addresses:
            return
        identity = info.properties.get(b"bt", b"")
        if isinstance(identity, bytes):
            identity = identity.decode("utf-8", errors="replace")
        with self.lock:
            self.devices[name] = {
                "handler": "androidtv_remote",
                "host": addresses[0],
                "unique_id": identity,
                "context": {"title": name.removesuffix("." + service_type)},
            }

    def update_service(self, zeroconf, service_type, name):
        self.add_service(zeroconf, service_type, name)

    def remove_service(self, zeroconf, service_type, name):
        with self.lock:
            self.devices.pop(name, None)


def discover_android_tvs(scan_seconds=2.5):
    """Bounded, on-demand scan; never runs in the gesture/camera pipeline."""
    listener = _TVListener()
    try:
        with Zeroconf(ip_version=IPVersion.V4Only) as zeroconf:
            browser = ServiceBrowser(zeroconf, ANDROID_TV_SERVICE, listener)
            try:
                threading.Event().wait(scan_seconds)
            finally:
                browser.cancel()
    except OSError as error:
        logger.warning("Local Android TV discovery failed: %s", error)
        return []
    with listener.lock:
        return list(listener.devices.values())
