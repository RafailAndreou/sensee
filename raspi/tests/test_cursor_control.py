import unittest
from unittest.mock import patch
from pydantic import ValidationError
from gesture_engine.core.cursor_control import CursorController
from server.models import IronmanParams


class CursorControlTests(unittest.TestCase):
    def setUp(self):
        self.controller = CursorController(lambda: {'enabled': True}, start_thread=False)
        self.addCleanup(self.controller.stop)

    def test_small_integer_displacement_is_not_lost_in_interpolation(self):
        params = IronmanParams(delay=0).model_dump()
        with patch('gesture_engine.core.cursor_control.pyautogui.moveRel') as move:
            self.controller._do_cursor(.501, .5, .5, .5, params)
        self.assertEqual(sum(call.args[0] for call in move.call_args_list), -5)
        self.assertTrue(all(isinstance(call.args[0], int) for call in move.call_args_list))

    def test_fractional_displacements_accumulate(self):
        params = IronmanParams(gain=100, sensitivity=0, delay=0).model_dump()
        with patch('gesture_engine.core.cursor_control.pyautogui.moveRel') as move:
            for _ in range(5):
                self.controller._do_cursor(.505, .5, .5, .5, params)
        self.assertEqual(sum(call.args[0] for call in move.call_args_list), -2)

    def test_invalid_runtime_settings_disable_cursor_without_killing_it(self):
        controller = CursorController(lambda: {'enabled': True, 'delay': -1}, start_thread=False)
        self.addCleanup(controller.stop)
        self.assertFalse(controller.get_params()['enabled'])

    def test_api_rejects_negative_unbounded_or_nonfinite_settings(self):
        for params in ({'delay': -1}, {'delay': float('nan')}, {'steps': 100000},
                       {'gain': -10}, {'gesture_map': {'left_click': []}}):
            with self.subTest(params=params), self.assertRaises(ValidationError):
                IronmanParams(**params)
        self.assertEqual(IronmanParams(steps=100, delay=.01).steps, 100)
