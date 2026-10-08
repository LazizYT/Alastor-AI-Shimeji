import os
import random
from core.config import WIN32_AVAILABLE

if WIN32_AVAILABLE:
    import win32gui
    import win32con
    import win32process


class WindowDragger:
    def __init__(self, own_hwnd_getter=None):
        self.target_hwnd      = None
        self.drag_origin_x    = 0
        self.drag_origin_y    = 0
        self.win_origin_x     = 0
        self.win_origin_y     = 0
        self._own_hwnd_getter = own_hwnd_getter

    def _own_hwnd(self):
        if self._own_hwnd_getter:
            return self._own_hwnd_getter()
        return 0

    @staticmethod
    def _top_hwnd(sx, sy, exclude=0):
        if not WIN32_AVAILABLE:
            return 0
        hwnd = win32gui.WindowFromPoint((sx, sy))
        parent = win32gui.GetAncestor(hwnd, 2)
        hwnd = parent if parent else hwnd
        if hwnd == exclude or hwnd == 0:
            return 0
        if not win32gui.IsWindow(hwnd):
            return 0
        return hwnd

    def grab_window_at(self, sx, sy):
        if not WIN32_AVAILABLE:
            return False
        hwnd = self._top_hwnd(sx, sy, exclude=self._own_hwnd())
        if not hwnd:
            return False
        rect = win32gui.GetWindowRect(hwnd)
        self.target_hwnd   = hwnd
        self.drag_origin_x = sx
        self.drag_origin_y = sy
        self.win_origin_x  = rect[0]
        self.win_origin_y  = rect[1]
        return True

    def move_to(self, sx, sy):
        if not WIN32_AVAILABLE or not self.target_hwnd:
            return
        if not win32gui.IsWindow(self.target_hwnd):
            self.target_hwnd = None
            return
        dx = sx - self.drag_origin_x
        dy = sy - self.drag_origin_y
        rect = win32gui.GetWindowRect(self.target_hwnd)
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]
        nx = self.win_origin_x + dx
        ny = self.win_origin_y + dy
        win32gui.MoveWindow(self.target_hwnd, nx, ny, w, h, True)

    def release(self):
        self.target_hwnd = None

    def close_at(self, sx, sy):
        if not WIN32_AVAILABLE:
            return False
        hwnd = self._top_hwnd(sx, sy, exclude=self._own_hwnd())
        if not hwnd:
            return False
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        return True

    def minimize_at(self, sx, sy):
        if not WIN32_AVAILABLE:
            return False
        hwnd = self._top_hwnd(sx, sy, exclude=self._own_hwnd())
        if not hwnd:
            return False
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        return True

    def maximize_restore_at(self, sx, sy):
        if not WIN32_AVAILABLE:
            return False
        hwnd = self._top_hwnd(sx, sy, exclude=self._own_hwnd())
        if not hwnd:
            return False
        placement = win32gui.GetWindowPlacement(hwnd)
        if placement[1] == win32con.SW_SHOWMAXIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        return True

    def get_user_foreground_window(self, exclude=0) -> int:
        """
        Finds the active user window to control, cleanly ignoring Alastor's own
        process, speech bubbles, tray, context menus, and Windows system shells.
        """
        if not WIN32_AVAILABLE:
            return 0
        my_pid = os.getpid()

        fg = win32gui.GetForegroundWindow()
        if fg and win32gui.IsWindow(fg) and win32gui.IsWindowVisible(fg) and not win32gui.IsIconic(fg):
            try:
                _, pid = win32process.GetWindowThreadProcessId(fg)
                cls = win32gui.GetClassName(fg)
                title = win32gui.GetWindowText(fg).strip()
                if pid != my_pid and fg != exclude and cls not in ("Progman", "Shell_TrayWnd", "WorkerW") and title not in ("Program Manager", "Settings", ""):
                    return fg
            except Exception:
                pass

        # If fg is Alastor's own window or shell or 0, find topmost visible user window
        cand = []
        def _enum(h, _):
            if h == exclude or not win32gui.IsWindow(h) or not win32gui.IsWindowVisible(h) or win32gui.IsIconic(h):
                return True
            try:
                _, pid = win32process.GetWindowThreadProcessId(h)
                if pid == my_pid:
                    return True
                style = win32gui.GetWindowLong(h, win32con.GWL_STYLE)
                if style & win32con.WS_CHILD:
                    return True
                cls = win32gui.GetClassName(h)
                if cls in ("Shell_TrayWnd", "Progman", "WorkerW", "EdgeUiInputTopWndClass"):
                    return True
                title = win32gui.GetWindowText(h).strip()
                if not title or title in ("Program Manager", "Settings"):
                    return True
                rect = win32gui.GetWindowRect(h)
                if (rect[2] - rect[0]) < 150 or (rect[3] - rect[1]) < 100:
                    return True
                cand.append(h)
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(_enum, None)
        except Exception:
            pass

        return cand[0] if cand else 0

    def toggle_maximize_foreground(self, exclude=0):
        if not WIN32_AVAILABLE:
            return False
        hwnd = self.get_user_foreground_window(exclude)
        if hwnd:
            try:
                placement = win32gui.GetWindowPlacement(hwnd)
                if placement[1] == win32con.SW_SHOWMAXIMIZED:
                    win32gui.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                else:
                    win32gui.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_MAXIMIZE, 0)
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                return True
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.hotkey('win', 'up')
            return True
        except Exception:
            return False

    def minimize_foreground(self, exclude=0):
        if not WIN32_AVAILABLE:
            return False
        hwnd = self.get_user_foreground_window(exclude)
        if hwnd:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_MINIMIZE, 0)
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                return True
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.hotkey('win', 'down')
            return True
        except Exception:
            return False

    def close_foreground(self, exclude=0):
        if not WIN32_AVAILABLE:
            return False
        hwnd = self.get_user_foreground_window(exclude)
        if hwnd:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                return True
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.hotkey('alt', 'f4')
            return True
        except Exception:
            return False


    @staticmethod
    def pick_random_window(exclude=0):
        if not WIN32_AVAILABLE:
            return 0
        results = []
        def _cb(h, _):
            if h == exclude:
                return
            if win32gui.IsWindow(h) and win32gui.IsWindowVisible(h):
                title = win32gui.GetWindowText(h)
                rect = win32gui.GetWindowRect(h)
                w = rect[2] - rect[0]
                h_px = rect[3] - rect[1]
                if title and w > 200 and h_px > 150:
                    style = win32gui.GetWindowLong(h, win32con.GWL_STYLE)
                    if not (style & win32con.WS_CHILD):
                        results.append(h)
        win32gui.EnumWindows(_cb, None)
        return random.choice(results) if results else 0
