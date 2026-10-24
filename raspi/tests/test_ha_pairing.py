import json
import unittest
from unittest.mock import MagicMock, patch

import requests
from fastapi import HTTPException

from server import ha_pairing


class PairingTests(unittest.TestCase):
    def test_discoveries_use_authenticated_websocket(self):
        flows = [{"flow_id": "tv-discovery", "handler": "androidtv_remote"}]
        with patch.object(ha_pairing, "connect") as connect:
            socket = connect.return_value.__enter__.return_value
            socket.recv.side_effect = [json.dumps(message) for message in (
                {"type": "auth_required"}, {"type": "auth_ok"},
                {"id": 1, "success": True, "result": flows})]
            self.assertEqual(ha_pairing.fetch_discovered_flows(
                "https://ha.test/prefix/", "secret", None, (2, 3)), flows)
            self.assertEqual(connect.call_args.args[0], "wss://ha.test/prefix/api/websocket")
            sent = [json.loads(call.args[0]) for call in socket.send.call_args_list]
            self.assertEqual(sent, [{"type": "auth", "access_token": "secret"},
                                    {"id": 1, "type": "config_entries/flow/progress"}])

    def test_authentication_and_permission_errors_are_not_empty_discoveries(self):
        for replies in (
            [{"type": "auth_required"}, {"type": "auth_invalid"}],
            [{"type": "auth_required"}, {"type": "auth_ok"},
             {"id": 1, "success": False, "error": {"code": "unauthorized"}}],
        ):
            with self.subTest(replies=replies), patch.object(ha_pairing, "connect") as connect:
                socket = connect.return_value.__enter__.return_value
                socket.recv.side_effect = [json.dumps(reply) for reply in replies]
                with self.assertRaises(HTTPException) as raised:
                    ha_pairing.fetch_discovered_flows("http://ha.test", "secret", None, (2, 3))
                self.assertEqual(raised.exception.status_code, 502)

    def test_resume_preserves_discovery_id_and_does_not_start_new_flow(self):
        session = MagicMock()
        session.get.return_value.json.return_value = {"type": "form", "step_id": "confirm"}
        ha_pairing.get_pairing_flow_request("http://ha.test/", "secret", "existing", session, (2, 3))
        self.assertEqual(session.get.call_args.args[0], "http://ha.test/api/config/config_entries/flow/existing")
        session.post.assert_not_called()

    def test_android_tv_host_and_pin_are_forwarded_unchanged(self):
        session = MagicMock()
        session.post.return_value.json.return_value = {"type": "form", "errors": {"base": "invalid_auth"}}
        for values in ({"host": "192.168.1.22"}, {"pin": "AB12CD"}, {}):
            result = ha_pairing.submit_pairing_step_request(
                "http://ha.test/", "secret", "existing", values, session, (2, 3))
            self.assertEqual(session.post.call_args.kwargs["json"], values)
            self.assertEqual(result["errors"]["base"], "invalid_auth")

    def test_upstream_failure_does_not_report_pairing_success(self):
        session = MagicMock()
        session.post.return_value.raise_for_status.side_effect = requests.HTTPError("403")
        with self.assertRaises(HTTPException) as raised:
            ha_pairing.start_pairing_flow_request("http://ha.test", "secret", "androidtv_remote", session, (2, 3))
        self.assertEqual(raised.exception.status_code, 502)


class LocalDiscoveryFallbackTests(unittest.TestCase):
    def setUp(self):
        from server import homeassistant
        self.ha = homeassistant
        self.local_tv = {"handler": "androidtv_remote", "host": "192.168.1.22",
                         "context": {"title": "Bedroom TV"}}

    def test_local_tv_is_available_when_ha_cannot_list_discoveries(self):
        with patch.object(self.ha, "get_ha_config", return_value=("http://ha.test", "token")), \
             patch.object(self.ha, "discover_android_tvs", return_value=[self.local_tv]), \
             patch.object(self.ha, "fetch_discovered_flows", side_effect=HTTPException(502, "unavailable")):
            self.assertEqual(self.ha.get_discovered_flows(), [self.local_tv])

    def test_existing_flow_is_preferred_without_hiding_other_tvs(self):
        existing = {"handler": "androidtv_remote", "flow_id": "ha-flow",
                    "context": {"title": "Living Room TV"}}
        duplicate = {**self.local_tv, "context": {"title": "living room tv"}}
        with patch.object(self.ha, "get_ha_config", return_value=("http://ha.test", "token")), \
             patch.object(self.ha, "discover_android_tvs", return_value=[duplicate, self.local_tv]), \
             patch.object(self.ha, "fetch_discovered_flows", return_value=[existing]):
            self.assertEqual(self.ha.get_discovered_flows(), [{**existing, 'host': duplicate['host']}, self.local_tv])

    def test_selected_local_tv_supplies_host_before_pin_step(self):
        with patch.object(self.ha, "get_ha_config", return_value=("http://ha.test", "token")), \
             patch.object(self.ha, "start_pairing_flow_request", return_value={
                 "type": "form", "step_id": "user", "flow_id": "new-flow"}), \
             patch.object(self.ha, "submit_pairing_step_request", return_value={"type": "form", "step_id": "pair"}) as submit:
            result = self.ha.start_pairing_flow("androidtv_remote", "192.168.1.22")
            self.assertEqual(result["step_id"], "pair")
            self.assertEqual(submit.call_args.args[2:4], ("new-flow", {"host": "192.168.1.22"}))


    def test_selected_ha_tv_starts_pairing_after_discovery_confirmation(self):
        with patch.object(self.ha, "get_ha_config", return_value=("http://ha.test", "token")), \
             patch.object(self.ha, "get_pairing_flow", return_value={
                 "handler": "androidtv_remote", "type": "form", "step_id": "zeroconf_confirm", "data_schema": []}), \
             patch.object(self.ha, "submit_pairing_step_request", return_value={"type": "form", "step_id": "pair"}) as submit:
            result = self.ha.resume_pairing_flow("discovered-flow")
            self.assertEqual(result["step_id"], "pair")
            self.assertEqual(submit.call_args.args[2:4], ("discovered-flow", {}))

    def test_pin_step_and_other_integrations_are_not_automatically_submitted(self):
        for form in (
            {"handler": "androidtv_remote", "type": "form", "step_id": "pair", "data_schema": [{"name": "pin"}]},
            {"handler": "other", "type": "form", "step_id": "zeroconf_confirm"},
        ):
            with self.subTest(form=form), patch.object(self.ha, "get_ha_config", return_value=("http://ha.test", "token")), \
                 patch.object(self.ha, "get_pairing_flow", return_value=form), \
                 patch.object(self.ha, "submit_pairing_step_request") as submit:
                self.assertEqual(self.ha.resume_pairing_flow("flow"), form)
                submit.assert_not_called()

    def test_same_tv_is_merged_by_mac_even_when_ha_and_mdns_names_differ(self):
        existing = {"handler": "androidtv_remote", "flow_id": "ha-flow",
                    "context": {"unique_id": "aa:bb:cc:dd:ee:ff", "title": "Android TV"}}
        local = {**self.local_tv, "unique_id": "AA-BB-CC-DD-EE-FF"}
        result = self.ha._merge_tv_discoveries([existing], [local])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["flow_id"], "ha-flow")
        self.assertEqual(result[0]["host"], "192.168.1.22")


    def test_two_different_tvs_with_same_name_are_not_collapsed(self):
        existing = {"handler": "androidtv_remote", "flow_id": "ha-flow",
                    "context": {"title": "Bedroom TV", "unique_id": "aabbccddeeff"}}
        other = {**self.local_tv, "unique_id": "112233445566"}
        self.assertEqual(len(self.ha._merge_tv_discoveries([existing], [other])), 2)
