import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, Mock

from gesture_engine import ha_startup


class HomeAssistantStartupTests(unittest.TestCase):
    def test_disabled_mode_never_runs_docker(self):
        with patch.dict(os.environ, {"SENSEE_HA_AUTOSTART": "0"}), patch.object(ha_startup.subprocess, "run") as run:
            self.assertFalse(ha_startup.ensure_home_assistant_started())
            run.assert_not_called()

    def test_remote_home_assistant_does_not_start_local_container(self):
        with patch.dict(os.environ, {"SENSEE_HA_AUTOSTART": "auto"}), patch("server.ha_config.get_ha_config", return_value=("https://remote.example", "token")), patch.object(ha_startup.subprocess, "run") as run:
            self.assertFalse(ha_startup.ensure_home_assistant_started())
            run.assert_not_called()

    def test_runs_compose_from_its_directory_without_recreating_container(self):
        with tempfile.TemporaryDirectory() as directory:
            compose = Path(directory) / "docker-compose.yml"
            compose.write_text("services: {}", encoding="utf-8")
            with patch.dict(os.environ, {"SENSEE_HA_AUTOSTART": "1", "SENSEE_HA_COMPOSE_FILE": str(compose)}), patch.object(ha_startup.shutil, "which", return_value="docker"), patch.object(ha_startup.subprocess, "run", return_value=Mock(returncode=0)) as run:
                self.assertTrue(ha_startup.ensure_home_assistant_started())
                self.assertEqual(run.call_args.args[0], ["docker", "compose", "-f", str(compose), "up", "-d", "--no-recreate", "homeassistant"])
                self.assertEqual(run.call_args.kwargs["cwd"], directory)

    def test_docker_unavailable_and_timeouts_are_logged_without_crashing(self):
        with patch.dict(os.environ, {"SENSEE_HA_AUTOSTART": "1"}), patch.object(ha_startup.Path, "is_file", return_value=True), patch.object(ha_startup.shutil, "which", return_value="docker"):
            for outcome in (OSError("Docker unavailable"), subprocess.TimeoutExpired("docker", 180)):
                with self.subTest(outcome=outcome), patch.object(ha_startup.subprocess, "run", side_effect=outcome):
                    with self.assertLogs(ha_startup.logger.name, level="WARNING"):
                        self.assertFalse(ha_startup.ensure_home_assistant_started())

    def test_failed_compose_is_not_reported_as_success(self):
        with patch.dict(os.environ, {"SENSEE_HA_AUTOSTART": "1"}), patch.object(ha_startup.Path, "is_file", return_value=True), patch.object(ha_startup.shutil, "which", return_value="docker"), patch.object(ha_startup.subprocess, "run", return_value=Mock(returncode=1, stderr="daemon unavailable")):
            self.assertFalse(ha_startup.ensure_home_assistant_started())
