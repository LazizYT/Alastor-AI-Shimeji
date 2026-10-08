import os
from core.config import WIN32_AVAILABLE, SIZE
from core.logger import log_info, log_warn

if WIN32_AVAILABLE:
    import win32gui
    import win32con


class WindowSurfaceDetector:
    """
    Detects visible top-level application windows on Windows and calculates
    walkable horizontal surfaces (tabs, title bars, window top edges) for the mascot.
    """

    def __init__(self, own_hwnd_getter=None):
        self._own_hwnd_getter = own_hwnd_getter

    def _own_hwnd(self):
        if self._own_hwnd_getter:
            try:
                return self._own_hwnd_getter()
            except Exception:
                pass
        return 0

    def get_open_windows(self, min_width: int = 250, min_height: int = 150) -> list[dict]:
        """
        Enumerates all visible, non-minimized desktop windows that can serve as platforms.
        """
        if not WIN32_AVAILABLE:
            return []

        exclude = self._own_hwnd()
        windows = []

        def _enum_cb(hwnd, _):
            if hwnd == exclude or not win32gui.IsWindow(hwnd):
                return True
            try:
                if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                    return True

                # Filter child controls and tooltips
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                if style & win32con.WS_CHILD:
                    return True

                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]

                # Filter tiny or offscreen windows
                if w < min_width or h < min_height:
                    return True

                title = win32gui.GetWindowText(hwnd).strip()
                # Ignore invisible system shells and program manager
                if not title or title in ("Program Manager", "Settings", "Microsoft Text Input Application"):
                    return True

                class_name = win32gui.GetClassName(hwnd)
                if class_name in ("Shell_TrayWnd", "Progman", "WorkerW", "EdgeUiInputTopWndClass"):
                    return True

                floor_y = rect[1] - SIZE + 15
                windows.append({
                    "hwnd": hwnd,
                    "title": title,
                    "class": class_name,
                    "rect": rect,
                    "left": rect[0],
                    "top": rect[1],
                    "right": rect[2],
                    "bottom": rect[3],
                    "width": w,
                    "height": h,
                    "floor_y": floor_y,
                    "min_x": rect[0],
                    "max_x": rect[2] - SIZE
                })
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(_enum_cb, None)
        except Exception as e:
            log_warn(f"Ошибка EnumWindows: {e}")

        # Sort so higher windows (smaller top) or focused windows come first
        return windows

    def get_foreground_window(self) -> dict | None:
        """Returns surface info for currently active foreground window."""
        if not WIN32_AVAILABLE:
            return None
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd or hwnd == self._own_hwnd() or not win32gui.IsWindow(hwnd):
                return None
            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            if w < 200 or h < 150:
                return None
            title = win32gui.GetWindowText(hwnd).strip()
            return {
                "hwnd": hwnd,
                "title": title,
                "rect": rect,
                "left": rect[0],
                "top": rect[1],
                "right": rect[2],
                "bottom": rect[3],
                "width": w,
                "height": h,
                "floor_y": rect[1] - SIZE + 15,
                "min_x": rect[0],
                "max_x": rect[2] - SIZE
            }
        except Exception:
            return None

    def find_surface_landing(self, mascot_x: int, mascot_y: int) -> dict | None:
        """
        Finds the highest window surface directly below mascot's feet that he could land on while falling.
        """
        windows = self.get_open_windows()
        feet_x = mascot_x + SIZE // 2
        feet_y = mascot_y + SIZE

        best = None
        best_diff = 999999

        for win in windows:
            # Check horizontal overlap
            if win["left"] <= feet_x <= win["right"]:
                # Surface top edge
                surf_y = win["floor_y"]
                # Must be below current mascot_y but above screen floor
                if surf_y >= mascot_y:
                    diff = surf_y - mascot_y
                    if diff < best_diff:
                        best_diff = diff
                        best = win

        return best
