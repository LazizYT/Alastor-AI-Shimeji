import os
import time
import subprocess
from core.config import WIN32_AVAILABLE
from core.logger import log_info, log_warn

if WIN32_AVAILABLE:
    import win32gui
    import win32con
    import win32api


class AIMPController:
    """
    Manages Alastor's Vintage Radio via AIMP media player.
    Supports play, pause, next/prev tracks, and reading the currently playing track.
    If AIMP is not running, launches it and triggers playback seamlessly.
    """

    WM_AIMP_COMMAND = 0x0400 + 0x75  # WM_USER + 0x75 (0x0475)
    AIMP_REMOTE_CLASS = "AIMP2_RemoteClass"

    # Command codes from official AIMP SDK
    CMD_STOP      = 11
    CMD_PAUSE     = 12
    CMD_PLAY      = 13
    CMD_PLAYPAUSE = 14
    CMD_PREV      = 15
    CMD_NEXT      = 16
    CMD_VOL_DOWN  = 17
    CMD_VOL_UP    = 18

    COMMON_AIMP_PATHS = [
        r"C:\Program Files\AIMP\AIMP.exe",
        r"C:\Program Files (x86)\AIMP\AIMP.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\AIMP\AIMP.exe"),
        os.path.expandvars(r"%APPDATA%\AIMP\AIMP.exe"),
    ]

    def __init__(self, mascot=None):
        self.m = mascot
        self.aimp_exe = self._locate_aimp()

    def _locate_aimp(self) -> str:
        for p in self.COMMON_AIMP_PATHS:
            if os.path.exists(p):
                return p
        return "aimp.exe"

    def _get_aimp_hwnd(self) -> int:
        if not WIN32_AVAILABLE:
            return 0
        try:
            return win32gui.FindWindow(self.AIMP_REMOTE_CLASS, None)
        except Exception:
            return 0

    def _ensure_aimp_running(self) -> bool:
        hwnd = self._get_aimp_hwnd()
        if hwnd:
            return True

        if os.path.exists(self.aimp_exe):
            try:
                log_info(f"Запуск AIMP: {self.aimp_exe}")
                os.startfile(self.aimp_exe)
                # Wait up to 3 seconds for AIMP window to initialize
                for _ in range(15):
                    time.sleep(0.2)
                    hwnd = self._get_aimp_hwnd()
                    if hwnd:
                        return True
            except Exception as e:
                log_warn(f"Ошибка запуска AIMP: {e}")
        return False

    def send_command(self, cmd_id: int) -> bool:
        if not WIN32_AVAILABLE:
            return False
        if not self._ensure_aimp_running():
            return False

        hwnd = self._get_aimp_hwnd()
        if not hwnd:
            return False

        try:
            win32gui.SendMessage(hwnd, self.WM_AIMP_COMMAND, cmd_id, 0)
            return True
        except Exception as e:
            log_warn(f"Ошибка отправки команды AIMP ({cmd_id}): {e}")
            return False

    # Global Windows Media Keys
    VK_MEDIA_NEXT_TRACK = 0xB0
    VK_MEDIA_PREV_TRACK = 0xB1
    VK_MEDIA_STOP       = 0xB2
    VK_MEDIA_PLAY_PAUSE = 0xB3

    def send_media_key(self, vk_code: int) -> bool:
        """Sends a global Windows multimedia key event (controls Spotify, YouTube, browsers, AIMP)."""
        if WIN32_AVAILABLE:
            try:
                win32api.keybd_event(vk_code, 0, 0, 0)
                win32api.keybd_event(vk_code, 0, 2, 0)  # KEYEVENTF_KEYUP
                return True
            except Exception as e:
                log_warn(f"Ошибка keybd_event: {e}")
        try:
            import pyautogui
            mapping = {0xB0: 'nexttrack', 0xB1: 'prevtrack', 0xB2: 'stop', 0xB3: 'playpause'}
            if vk_code in mapping:
                pyautogui.press(mapping[vk_code])
                return True
        except Exception:
            pass
        return False

    def play(self) -> tuple[bool, str]:
        ok = self.send_command(self.CMD_PLAY)
        if not ok:
            self.send_media_key(self.VK_MEDIA_PLAY_PAUSE)

        if self.m and hasattr(self.m, 'set_state'):
            try:
                self.m.set_state("guitar")
            except Exception:
                pass
        track = self.get_current_track()
        t_msg = f" «{track}»" if track else ""
        return True, f"Радио-эфир запущен! Музыка в эфире!{t_msg} 🎷📻🎶"

    def play_pause(self) -> tuple[bool, str]:
        ok = self.send_command(self.CMD_PLAYPAUSE)
        if not ok:
            self.send_media_key(self.VK_MEDIA_PLAY_PAUSE)
        return True, "Переключил воспроизведение музыки! 📻✨"

    def pause(self) -> tuple[bool, str]:
        ok = self.send_command(self.CMD_PAUSE)
        if not ok:
            self.send_media_key(self.VK_MEDIA_PLAY_PAUSE)
        return True, "Поставил музыку на паузу! В эфире временное затишье... ⏸️"

    def stop(self) -> tuple[bool, str]:
        ok = self.send_command(self.CMD_STOP)
        if not ok:
            self.send_media_key(self.VK_MEDIA_STOP)
        return True, "Воспроизведение музыки остановлено! ⏹️"

    def next_track(self) -> tuple[bool, str]:
        ok = self.send_command(self.CMD_NEXT)
        if not ok:
            self.send_media_key(self.VK_MEDIA_NEXT_TRACK)
        time.sleep(0.3)
        track = self.get_current_track()
        t_msg = f": «{track}»" if track else "!"
        return True, f"Следующая композиция в эфире{t_msg} ⏭️🎷"

    def prev_track(self) -> tuple[bool, str]:
        ok = self.send_command(self.CMD_PREV)
        if not ok:
            self.send_media_key(self.VK_MEDIA_PREV_TRACK)
        time.sleep(0.3)
        track = self.get_current_track()
        t_msg = f": «{track}»" if track else "!"
        return True, f"Возвращаемся к предыдущему треку{t_msg} ⏮️📻"

    def get_current_track(self) -> str:
        """Attempts to read currently playing track title from AIMP or open media windows (YouTube, Spotify, etc.)."""
        if not WIN32_AVAILABLE:
            return ""
        try:
            found_title = []
            import re
            def _enum_win(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).strip()
                    if not title:
                        return
                    t_low = title.lower()
                    if "aimp" in t_low:
                        clean = re.sub(r'\s*-\s*AIMP.*$', '', title, flags=re.IGNORECASE).strip()
                        if clean and clean.lower() != "aimp":
                            found_title.append(clean)
                    elif "youtube" in t_low:
                        clean = re.sub(r'^\(\d+\)\s*', '', title)
                        clean = re.sub(r'\s*-\s*YouTube.*$', '', clean, flags=re.IGNORECASE).strip()
                        if clean and clean.lower() != "youtube":
                            found_title.append(f"{clean} (YouTube)")
                    elif "spotify" in t_low and (" - " in title):
                        clean = re.sub(r'\s*-\s*Spotify.*$', '', title, flags=re.IGNORECASE).strip()
                        if clean:
                            found_title.append(f"{clean} (Spotify)")
                    elif "яндекс музыка" in t_low or "yandex music" in t_low:
                        clean = re.sub(r'\s*[-—]\s*Яндекс\s*Музыка.*$', '', title, flags=re.IGNORECASE).strip()
                        if clean:
                            found_title.append(f"{clean} (Яндекс Музыка)")

            win32gui.EnumWindows(_enum_win, None)
            if found_title:
                return found_title[0]
        except Exception:
            pass
        return ""


# Alias for unified music & media control
MusicController = AIMPController
