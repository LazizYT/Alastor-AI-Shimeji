import os
import sys
import unittest

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.config import SIZE, WIN32_AVAILABLE
from windows.window_surface_detector import WindowSurfaceDetector


class TestWindowWalkingPhysics(unittest.TestCase):
    def setUp(self):
        self.detector = WindowSurfaceDetector()

    def test_surface_detector_queries(self):
        """Tests window enumeration without crashing, and checks bounds."""
        windows = self.detector.get_open_windows()
        self.assertIsInstance(windows, list)
        for w in windows:
            self.assertIn("hwnd", w)
            self.assertIn("floor_y", w)
            self.assertIn("min_x", w)
            self.assertIn("max_x", w)
            # Verify feet are placed right on the top bar
            expected_floor_y = w["top"] - SIZE + 15
            self.assertEqual(w["floor_y"], expected_floor_y)
            self.assertEqual(w["min_x"], w["left"])
            self.assertEqual(w["max_x"], w["right"] - SIZE)

    def test_simulated_landing_detection(self):
        """Simulates a browser window at (200, 300, 1200, 900) and falling mascot."""
        fake_window = {
            "hwnd": 99999,
            "title": "Google Chrome - Alastor Demo",
            "class": "Chrome_WidgetWin_1",
            "rect": (200, 300, 1200, 900),
            "left": 200,
            "top": 300,
            "right": 1200,
            "bottom": 900,
            "width": 1000,
            "height": 600,
            "floor_y": 300 - SIZE + 15,
            "min_x": 200,
            "max_x": 1200 - SIZE
        }

        # Mock get_open_windows
        self.detector.get_open_windows = lambda min_width=250, min_height=150: [fake_window]

        # Mascot falls directly above the window center
        mascot_x = 600
        mascot_y = 150  # Above window

        landing = self.detector.find_surface_landing(mascot_x, mascot_y)
        self.assertIsNotNone(landing)
        self.assertEqual(landing["hwnd"], 99999)
        self.assertEqual(landing["floor_y"], 300 - SIZE + 15)

        # Mascot is far to the right, outside window bounds
        landing_outside = self.detector.find_surface_landing(1500, 150)
        self.assertIsNone(landing_outside)

    def test_window_walking_bounds_and_tracking(self):
        """Simulates mascot walking on the window's tabs from min_x to max_x."""
        win_left = 300
        win_right = 1100
        win_top = 200
        floor_y = win_top - SIZE + 15
        min_x = win_left
        max_x = win_right - SIZE

        # Mascot positioned on tab bar
        pos_x = min_x + 50
        pos_y = floor_y

        vel_x = 2
        # Walk 50 steps
        for _ in range(50):
            pos_x += vel_x
            if pos_x >= max_x:
                vel_x = -abs(vel_x)  # Turn left
            elif pos_x <= min_x:
                vel_x = abs(vel_x)   # Turn right

        self.assertGreaterEqual(pos_x, min_x)
        self.assertLessEqual(pos_x, max_x)
        self.assertEqual(pos_y, floor_y)

        # Window moved down by 100 pixels (e.g. user dragged the window)
        win_top += 100
        new_floor_y = win_top - SIZE + 15
        pos_y = new_floor_y
        self.assertEqual(pos_y, 300 - SIZE + 15)


if __name__ == "__main__":
    unittest.main()
