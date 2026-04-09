import time

import requests


class HAClient:
    def __init__(self, timeout=(0.8, 2.2), session=None):
        self.timeout = timeout
        self.session = session or requests.Session()

    @staticmethod
    def _headers(token: str, include_json=False):
        headers = {"Authorization": f"Bearer {token}"}
        if include_json:
            headers["Content-Type"] = "application/json"
        return headers

    def post_service(self, url_base: str, token: str, domain: str, service: str, data: dict):
        url = f"{url_base}/api/services/{domain}/{service}"
        started = time.perf_counter()
        response = self.session.post(
            url,
            headers=self._headers(token, include_json=True),
            json=data,
            timeout=self.timeout,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return response, elapsed_ms

    def get_entity_state(self, url_base: str, token: str, entity_id: str):
        response = self.session.get(
            f"{url_base}/api/states/{entity_id}",
            headers=self._headers(token),
            timeout=self.timeout,
        )
        if response.status_code != 200:
            return None
        return response.json().get("state")

    def get_all_states(self, url_base: str, token: str):
        return self.session.get(
            f"{url_base}/api/states",
            headers=self._headers(token, include_json=True),
            timeout=self.timeout,
        )