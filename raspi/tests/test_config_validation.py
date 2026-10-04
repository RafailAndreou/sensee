import unittest

from server.config_validation import validate_configuration_payload  # noqa: E402


class ConfigurationValidationTests(unittest.TestCase):
    def test_aliases_and_hand_variants_cannot_duplicate_mapping(self):
        for gesture in ('Middle Thumb', 'Thumb+Middle', ' Thumb / Middle '):
            with self.subTest(gesture=gesture):
                self.assertIsNotNone(validate_configuration_payload([
                    {'gesture': 'Thumb Middle', 'hand': 'Left Hand'},
                    {'gesture': gesture, 'hand': 'Left'},
                ]))

    def test_fist_aliases_cannot_mix_both_and_one_hand(self):
        self.assertIsNotNone(validate_configuration_payload([
            {'gesture': 'Closed Fist', 'hand': 'Both Hands'},
            {'gesture': 'Fist', 'hand': 'Right Hand'},
        ]))

    def test_empty_hand_is_the_same_wildcard_as_both_hands(self):
        self.assertIsNotNone(validate_configuration_payload([
            {'gesture': 'Open Palm', 'hand': ''},
            {'gesture': 'Open Palm', 'hand': 'Both Hands'},
        ]))
    def test_validate_configuration_payload_accepts_valid_config(self):
        payload = [
            {"gesture": "Open Palm", "hand": "Both Hands"},
            {"gesture": "Thumb Middle", "hand": "Left Hand"},
        ]

        self.assertIsNone(validate_configuration_payload(payload))

    def test_validate_configuration_payload_rejects_duplicate_gesture_hand(self):
        payload = [
            {"gesture": "Open Palm", "hand": "Left Hand"},
            {"gesture": "Open Palm", "hand": "Left Hand"},
        ]

        self.assertEqual(
            validate_configuration_payload(payload),
            "Duplicate gesture+hand mapping is not allowed: Open Palm / Left Hand",
        )

    def test_validate_configuration_payload_rejects_both_plus_left_or_right(self):
        payload = [
            {"gesture": "Open Palm", "hand": "Both Hands"},
            {"gesture": "Open Palm", "hand": "Right Hand"},
        ]

        self.assertEqual(
            validate_configuration_payload(payload),
            "Invalid hand combination for gesture 'open palm': Both Hands cannot coexist with Left/Right Hand mappings",
        )


if __name__ == "__main__":
    unittest.main()
