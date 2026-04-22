import sys
from pathlib import Path
import unittest


RASPI_DIR = Path(__file__).resolve().parents[1]
if str(RASPI_DIR) not in sys.path:
    sys.path.insert(0, str(RASPI_DIR))

from gesture_engine.core.matching import (  # noqa: E402
    canonical_gesture_name,
    find_matched_config,
    gesture_matches,
    normalize_name,
    normalized_parts,
)


class MatchingTests(unittest.TestCase):
    def test_normalize_name_handles_spacing_and_symbols(self):
        self.assertEqual(normalize_name("  Thumb_Index + Open Palm  "), "thumb index   open palm")

    def test_canonical_gesture_name_maps_known_aliases(self):
        self.assertEqual(canonical_gesture_name("Middle Thumb"), "thumb middle")
        self.assertEqual(canonical_gesture_name("Index Thumb"), "thumb index")

    def test_gesture_matches_accepts_ordered_variants(self):
        self.assertTrue(gesture_matches("Thumb Middle", "Middle Thumb"))

    def test_gesture_matches_rejects_unrelated_gestures(self):
        self.assertFalse(gesture_matches("Open Palm", "Thumb Middle"))

    def test_find_matched_config_respects_detected_hand(self):
        active_configs = [
            {"gesture": "Thumb Middle", "hand": "Left Hand", "action": "Left action"},
            {"gesture": "Thumb Middle", "hand": "Right Hand", "action": "Right action"},
        ]

        self.assertEqual(
            find_matched_config(active_configs, "Middle Thumb", "Right Hand"),
            active_configs[1],
        )

    def test_find_matched_config_accepts_both_hands(self):
        active_configs = [
            {"gesture": "Open Palm", "hand": "Both Hands", "action": "Shared action"},
        ]

        self.assertEqual(
            find_matched_config(active_configs, "Open Palm", "Unknown"),
            active_configs[0],
        )

    def test_normalized_parts_split_multiple_words(self):
        self.assertEqual(normalized_parts("Thumb / Index + Open Palm"), ["thumb", "index", "open", "palm"])


if __name__ == "__main__":
    unittest.main()