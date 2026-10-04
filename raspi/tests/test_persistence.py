import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from server import file
from server.access import load_pairing_key


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = str(Path(self.directory.name) / "configure.json")
        self.patch = patch.object(file, "CONFIG_FILE_PATH", self.path)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_corruption_recovers_previous_valid_save(self):
        previous = [{"gesture": "Open Palm"}]
        file.save_configure_json(previous)
        file.save_configure_json([{"gesture": "Fist"}])
        Path(self.path).write_text('[{', encoding="utf-8")
        self.assertEqual(file.load_configure_json(), previous)

    def test_missing_primary_recovers_backup(self):
        file.save_configure_json([1])
        file.save_configure_json([2])
        Path(self.path).unlink()
        self.assertEqual(file.load_configure_json(), [1])

    def test_invalid_structure_and_missing_backup_return_empty(self):
        Path(self.path).write_text('{}', encoding="utf-8")
        self.assertEqual(file.load_configure_json(), [])

    def test_failed_replacement_preserves_primary_and_cleans_temporary(self):
        file.save_configure_json([1])
        original_replace = file.os.replace

        def fail_primary(source, destination):
            if destination == self.path:
                raise OSError("simulated interrupted save")
            return original_replace(source, destination)

        with patch.object(file.os, "replace", side_effect=fail_primary):
            with self.assertRaises(OSError):
                file.save_configure_json([2])
        self.assertEqual(file.load_configure_json(), [1])
        self.assertFalse(list(Path(self.directory.name).glob('.sensee-*')))

    def test_concurrent_saves_and_reads_are_complete_documents(self):
        file.save_configure_json([0] * 50)

        def save_and_read(value):
            file.save_configure_json([value] * 50)
            snapshot = file.load_configure_json()
            self.assertEqual(len(snapshot), 50)
            self.assertEqual(len(set(snapshot)), 1)

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(save_and_read, range(20)))
        with open(self.path, encoding="utf-8") as stream:
            self.assertEqual(len(json.load(stream)), 50)

    def test_disabling_wake_gate_removes_backup(self):
        path = str(Path(self.directory.name) / 'gesture_settings.json')
        with patch.object(file, 'GESTURE_SETTINGS_PATH', path):
            file.save_gesture_settings({'wakeEnabled': True})
            file.save_gesture_settings({'wakeEnabled': True})
            file.delete_gesture_settings()
            self.assertFalse(file.load_gesture_settings()['wakeEnabled'])
            self.assertFalse(Path(path + '.bak').exists())

    def test_pairing_key_survives_restart_and_is_replaced_when_revoked(self):
        path = str(Path(self.directory.name) / 'access_config.json')
        with patch.object(file, 'ACCESS_CONFIG_PATH', path):
            key = load_pairing_key()
            self.assertGreaterEqual(len(key), 32)
            self.assertEqual(load_pairing_key(), key)
            Path(path).unlink()
            self.assertNotEqual(load_pairing_key(), key)
