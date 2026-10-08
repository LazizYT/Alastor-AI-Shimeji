import random
from core.config import WIN32_AVAILABLE
from core.logger import log_info

if WIN32_AVAILABLE:
    import win32gui
    import win32con
    from windows.window_dragger import WindowDragger


class AutonomyManager:
    """
    Manages autonomous demon mischief behavior for Alastor:
    - Minimizing random windows
    - Dragging random windows across the desktop
    - Shuffling/moving/trashing desktop icons
    - Trolling the cursor with playful wiggles
    """

    def __init__(self, mascot, min_interval: int = 20000, max_interval: int = 45000):
        self.m = mascot
        self.min_interval = min_interval
        self.max_interval = max_interval

        self.auto_win_enabled = False
        self.auto_desk_enabled = False
        self.auto_mouse_enabled = False

    def start(self):
        self.m.root.after(5000, self.tick)

    def tick(self):
        if self.auto_win_enabled or self.auto_desk_enabled or self.auto_mouse_enabled:
            actions = []
            if self.auto_win_enabled:
                actions += ["auto_minimize", "auto_drag_window"]
            if self.auto_desk_enabled:
                actions += ["auto_move_icon", "auto_move_icon", "auto_trash_icon"]
            if self.auto_mouse_enabled:
                actions += ["auto_mouse_wiggle", "auto_mouse_wiggle"]
            if actions:
                choice = random.choice(actions)
                self.do_action(choice)

        interval = random.randint(self.min_interval, self.max_interval)
        self.m.root.after(interval, self.tick)

    def do_action(self, action: str):
        if action == "auto_mouse_wiggle":
            self.m.input_ctrl.playful_wiggle()
            self.m.show_speech("Ха-ха! Я поиграл с твоим курсором! 😈", play_audio=True)
            return

        if not WIN32_AVAILABLE:
            return

        if action == "auto_minimize":
            hwnd = WindowDragger.pick_random_window(exclude=self.m._own_hwnd())
            if hwnd:
                title = win32gui.GetWindowText(hwnd)[:20]
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                self.m.show_speech(f"Отправил '{title}' спать! 😴")

        elif action == "auto_drag_window":
            hwnd = WindowDragger.pick_random_window(exclude=self.m._own_hwnd())
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                nx = random.randint(0, max(0, self.m.sw - w))
                ny = random.randint(0, max(0, self.m.sh - h - 80))
                win32gui.MoveWindow(hwnd, nx, ny, w, h, True)
                title = win32gui.GetWindowText(hwnd)[:20]
                self.m.show_speech(f"Сдвинул '{title}' 🪟✨")

        elif action == "auto_move_icon":
            if self.m.desktop_mover:
                icons = self.m.desktop_mover.get_icon_list()
                if icons:
                    idx, name = random.choice(icons)
                    self.m.desktop_mover.move_one_icon(idx)
                    label = name[:18] + ("…" if len(name) > 18 else "")
                    self.m.show_speech(f"Передвинул '{label}' 🎲")

        elif action == "auto_trash_icon":
            if self.m.desktop_mover:
                icons = self.m.desktop_mover.get_icon_list()
                if icons:
                    idx, name = random.choice(icons)
                    ok, msg = self.m.desktop_mover.trash_icon_at_index(idx)
                    if ok:
                        label = msg[:18] + ("…" if len(msg) > 18 else "")
                        self.m.show_speech(f"Ха-ха! Выбросил\n'{label}' 🗑️😈")

    def toggle_auto_win(self):
        self.auto_win_enabled = not self.auto_win_enabled
        state = "ВКЛЮЧЕНА 😈" if self.auto_win_enabled else "ВЫКЛЮЧЕНА 😇"
        self.m.show_speech(f"Автономия окон:\n{state}")

    def toggle_auto_desk(self):
        self.auto_desk_enabled = not self.auto_desk_enabled
        state = "ВКЛЮЧЕНА 😈" if self.auto_desk_enabled else "ВЫКЛЮЧЕНА 😇"
        self.m.show_speech(f"Автономия стола:\n{state}")

    def toggle_auto_mouse(self):
        self.auto_mouse_enabled = not self.auto_mouse_enabled
        state = "ВКЛЮЧЕНА 😈" if self.auto_mouse_enabled else "ВЫКЛЮЧЕНА 😇"
        self.m.show_speech(f"Автономия мыши:\n{state}")
        log_info(f"Автономия мыши: {state}")
