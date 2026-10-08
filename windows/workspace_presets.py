import time
import threading
from core.config import WIN32_AVAILABLE
from core.logger import log_info, log_warn

if WIN32_AVAILABLE:
    import win32gui
    import win32con


class WorkspacePresets:
    """
    Manages multi-app workspace launch presets and automatic window arrangement / tiling.
    Examples:
      - «рабочий сетап» / «рабочий режим» (VS Code слева, Браузер справа)
      - «игровой сетап» (Steam + Discord)
      - «музыкальный режим» (AIMP / Радио)
      - «окна по бокам» / «расставь окна» (снап двух окон 50/50)
    """

    def __init__(self, mascot):
        self.m = mascot

    def apply_preset(self, preset_name: str) -> tuple[bool, str]:
        low = preset_name.lower().strip()
        if "рабоч" in low or "код" in low or "work" in low:
            threading.Thread(target=self._launch_work_workspace, daemon=True).start()
            return True, "Принято! Настраиваю рабочий сетап: запускаю VS Code и браузер, расставляю по экрану! 💻🌐✨"

        if "игр" in low or "гейм" in low or "game" in low:
            threading.Thread(target=self._launch_gaming_workspace, daemon=True).start()
            return True, "Время развлечений! Запускаю Steam и Discord! 🎮🎙️"

        if "музык" in low or "радио" in low:
            if hasattr(self.m, 'aimp_ctrl'):
                ok, reply = self.m.aimp_ctrl.play()
                return ok, reply
            return True, "Включаю музыку! 🎷"

        if "чист" in low or "очисти" in low:
            if hasattr(self.m, 'input_ctrl'):
                self.m.input_ctrl.hotkey('win', 'd')
            return True, "Свернул все окна на рабочий стол! Идеальная чистота! 🖥️🧹"

        if "по бокам" in low or "расставь" in low or "плитк" in low:
            ok = self.tile_two_top_windows()
            if ok:
                return True, "Расставил два активных окна по бокам экрана 50/50! 🪟⚖️"
            return False, "Недостаточно окон для расстановки по бокам!"

        return False, ""

    def _launch_work_workspace(self):
        """Asynchronously launches VS Code and Browser and tiles them side-by-side."""
        log_info("Запуск рабочего пресета...")
        sw = getattr(self.m, 'sw', 1920)
        sh = getattr(self.m, 'sh', 1080)
        half_w = sw // 2
        work_h = sh - 40  # Leave room for taskbar

        # 1. Launch apps via mascot launcher
        if hasattr(self.m, 'app_launcher'):
            self.m.app_launcher.launch_target("vscode")
            time.sleep(1.0)
            self.m.app_launcher.launch_target("browser")

        time.sleep(2.5)

        # 2. Arrange windows if Win32 available
        if not WIN32_AVAILABLE or not hasattr(self.m, 'surface_detector'):
            return

        open_wins = self.m.surface_detector.get_open_windows()
        code_win = None
        browser_win = None

        for w in open_wins:
            t_low = w["title"].lower()
            if ("visual studio code" in t_low or "vs code" in t_low) and not code_win:
                code_win = w
            elif ("edge" in t_low or "chrome" in t_low or "browser" in t_low) and not browser_win:
                browser_win = w

        # Snap Code to left half
        if code_win:
            try:
                win32gui.ShowWindow(code_win["hwnd"], win32con.SW_RESTORE)
                win32gui.MoveWindow(code_win["hwnd"], 0, 0, half_w, work_h, True)
                log_info(f"VS Code привязан к левой половине: hwnd={code_win['hwnd']}")
            except Exception:
                pass

        # Snap Browser to right half
        if browser_win:
            try:
                win32gui.ShowWindow(browser_win["hwnd"], win32con.SW_RESTORE)
                win32gui.MoveWindow(browser_win["hwnd"], half_w, 0, half_w, work_h, True)
                log_info(f"Браузер привязан к правой половине: hwnd={browser_win['hwnd']}")
            except Exception:
                pass

        msg = "Рабочий сетап готов! Слева ваш код, справа браузер! Приятной продуктивности! 🎩💻"
        self.m.root.after(0, lambda: self.m.show_speech(msg, play_audio=not self.m.is_muted))

    def _launch_gaming_workspace(self):
        log_info("Запуск игрового пресета...")
        if hasattr(self.m, 'app_launcher'):
            self.m.app_launcher.launch_target("steam")
            time.sleep(1.0)
            self.m.app_launcher.launch_target("discord")

    def tile_two_top_windows(self) -> bool:
        """Tiles the two topmost open windows side by side (50% left, 50% right)."""
        if not WIN32_AVAILABLE or not hasattr(self.m, 'surface_detector'):
            return False

        open_wins = self.m.surface_detector.get_open_windows()
        if len(open_wins) < 2:
            return False

        sw = getattr(self.m, 'sw', 1920)
        sh = getattr(self.m, 'sh', 1080)
        half_w = sw // 2
        work_h = sh - 40

        w1 = open_wins[0]
        w2 = open_wins[1]

        try:
            win32gui.ShowWindow(w1["hwnd"], win32con.SW_RESTORE)
            win32gui.MoveWindow(w1["hwnd"], 0, 0, half_w, work_h, True)

            win32gui.ShowWindow(w2["hwnd"], win32con.SW_RESTORE)
            win32gui.MoveWindow(w2["hwnd"], half_w, 0, half_w, work_h, True)
            return True
        except Exception:
            return False
