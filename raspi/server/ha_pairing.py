def fetch_discovered_flows(url: str, token: str, http_session, timeout):
    api_url = f"{url}/api/config/config_entries/flow"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = http_session.get(api_url, headers=headers, timeout=timeout)
    if response.status_code == 200:
        return response.json()
    return []


def start_pairing_flow_request(url: str, token: str, handler: str, http_session, timeout):
    api_url = f"{url}/api/config/config_entries/flow"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"handler": handler}
    response = http_session.post(api_url, headers=headers, json=data, timeout=timeout)
    return response.json()


def submit_pairing_step_request(url: str, token: str, flow_id: str, user_input: dict, http_session, timeout):
    api_url = f"{url}/api/config/config_entries/flow/{flow_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = http_session.post(api_url, headers=headers, json=user_input, timeout=timeout)
    return response.json()