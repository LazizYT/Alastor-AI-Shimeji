import time
import re
import random
import threading
from core.config import WIN32_AVAILABLE
from core.logger import log_info, log_warn

if WIN32_AVAILABLE:
    import win32gui
    import win32con
    import win32process


class DealManager:
    """
    «Сделка с Радио-демоном» (Focus & Anti-Procrastination Contract).
    
    When a deal is struck, Alastor enforces focus:
    - Monitors active window titles for distracting services (YouTube, Twitch, VK, Games, etc.)
    - Monitors system audio output sessions (via pycaw) to detect hidden videos or music players
    - Reprimands the user with authentic in-character radio demon voice lines
    - If distraction continues, minimizes or terminates distracting windows
    - Celebrates triumphant contract completion when time expires!
    """

    DISTRACTION_KEYWORDS = [
        "youtube", "ютуб", "twitch", "твич", "vk.com", "вконтакте", "tiktok", "тикток",
        "netflix", "нетфликс", "kinopoisk", "кинопоиск", "аниме", "anime",
        "dota", "cs2", "counter-strike", "steam", "игры", "shorts", "reels"
    ]

    DISTRACTION_PROCESSES = [
        "vlc.exe", "potplayer64.exe", "potplayer.exe", "mpc-hc.exe", "mpc-hc64.exe",
        "cs2.exe", "dota2.exe", "steam.exe"
    ]

    def __init__(self, mascot):
        self.m = mascot
        self.is_active = False
        self.start_time = 0.0
        self.end_time = 0.0
        self.duration_minutes = 0
        self.strikes = 0
        self.last_warning_time = 0.0
        self.allow_music = False
        self._thread = None
        self._stop_event = threading.Event()

    def start_deal(self, minutes: int = 30, task_name: str = "", allow_music: bool = False) -> str:
        """Starts a demonic deal / focus contract for a given number of minutes."""
        if self.is_active:
            rem = max(1, int((self.end_time - time.time()) / 60))
            return f"У нас уже заключена действующая сделка, мой друг! Осталось ещё {rem} минут! За дело! 😈"

        minutes = max(1, min(240, minutes))
        self.duration_minutes = minutes
        self.start_time = time.time()
        self.end_time = self.start_time + (minutes * 60)
        self.task_description = task_name.strip()
        self.allow_music = allow_music or ("музык" in self.task_description.lower())
        self.strikes = 0
        self.last_warning_time = 0.0
        self.is_active = True
        self._stop_event.clear()

        # Start background monitor thread
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

        task_msg = f" по задаче «{self.task_description}»" if self.task_description else ""
        log_info(f"Сделка с Радио-демоном заключена на {minutes} минут{task_msg}!")
        return (
            f"Ха-ха-ха! Превосходно! Сделка заключена на {minutes} минут{task_msg}! 🤝📻😈\n"
            f"Никакой праздности, никаких соцсетей и развлечений — только дело!\n"
            f"А если нарушишь уговор... расплата будет скорой!"
        )

    def cancel_deal(self) -> str:
        """Cancels an active deal early with in-character commentary."""
        if not self.is_active:
            return "В эфире нет активных сделок! Но я всегда готов пожать руку, ха-ха! 🤝"

        self.is_active = False
        self._stop_event.set()
        rem = max(1, int((self.end_time - time.time()) / 60))
        log_info(f"Сделка расторгнута пользователем досрочно (оставалось {rem} мин)")
        return (
            f"Сдаёшься за {rem} минут до финала?! Какое досадное разочарование... 😒\n"
            f"Что ж, сделка расторгнута! Но осадочек в радиоволнах остался!"
        )

    def get_status(self) -> str:
        """Returns the current status of the deal."""
        if not self.is_active:
            return "Сейчас сделка не активна. Скажите «сделка на 30 минут», чтобы заключить договор! 📜"

        remaining = self.end_time - time.time()
        if remaining <= 0:
            return "Сделка завершается прямо сейчас! 🏁"

        rem_m = int(remaining // 60)
        rem_s = int(remaining % 60)
        task_str = f" («{self.task_description}»)" if self.task_description else ""
        return (
            f"📜 Сделка в силе{task_str}!\n"
            f"⏳ Осталось: {rem_m} мин {rem_s} сек\n"
            f"⚠️ Нарушений зафиксировано: {self.strikes} 😈"
        )

    def _monitor_loop(self):
        """Continuously inspects active windows and audio sessions every 4 seconds."""
        while not self._stop_event.is_set() and self.is_active:
            try:
                now = time.time()
                if now >= self.end_time:
                    self._on_deal_completed()
                    break

                # 1. Check window distractions
                distraction_win = self._check_distraction_window()

                # 2. Check system audio distractions (e.g. video playing in background tab)
                audio_distraction = self._check_audio_distraction()

                if distraction_win or audio_distraction:
                    self._handle_infraction(distraction_win, audio_distraction)

            except Exception as e:
                log_warn(f"Ошибка монитора сделки: {e}")

            time.sleep(4.0)

    def _check_distraction_window(self) -> dict | None:
        """Checks if foreground or visible window matches distraction keywords."""
        if not WIN32_AVAILABLE:
            return None
        try:
            fg_hwnd = win32gui.GetForegroundWindow()
            if fg_hwnd:
                title = win32gui.GetWindowText(fg_hwnd).lower().strip()
                _, pid = win32process.GetWindowThreadProcessId(fg_hwnd)
                for kw in self.DISTRACTION_KEYWORDS:
                    if kw in title:
                        return {"hwnd": fg_hwnd, "title": title[:40], "pid": pid, "reason": kw}
        except Exception:
            pass
        return None

    def _check_audio_distraction(self) -> str | None:
        """Detects if a distraction app or browser is currently emitting active audio."""
        if self.allow_music:
            return None
        try:
            from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
            sessions = AudioUtilities.GetAllSessions()
            for s in sessions:
                proc = s.Process
                if not proc:
                    continue
                pname = proc.name().lower()
                # Check known video/audio players or browsers emitting sound
                if any(dp in pname for dp in self.DISTRACTION_PROCESSES) or ("chrome" in pname) or ("msedge" in pname):
                    try:
                        meter = s._ctl.QueryInterface(IAudioMeterInformation)
                        peak = meter.GetPeakValue()
                        if peak > 0.02:  # Active sound stream
                            return f"{pname} (громкость: {int(peak * 100)}%)"
                    except Exception:
                        pass
        except Exception:
            pass
        return None

    def _handle_infraction(self, win_info: dict | None, audio_info: str | None):
        """Reacts to detected procrastination during active deal."""
        now = time.time()
        # Cooldown between reprimands: 15 seconds
        if now - self.last_warning_time < 15.0:
            return

        self.last_warning_time = now
        self.strikes += 1

        details = win_info["title"] if win_info else (audio_info or "развлечения")
        log_info(f"Нарушение сделки #{self.strikes}: {details}")

        if self.strikes == 1:
            msg = (
                f"Я слышу звуки праздности в эфире! ({details}) 📻👁️\n"
                f"У нас же сделка, мой друг! Не искушай мою демоническую натуру! За работу!"
            )
            self._dispatch_speech(msg)

        elif self.strikes == 2:
            # Second infraction: minimize window
            msg = (
                f"Второе предупреждение, любезный! Сворачиваю '{details}'! 📉😈\n"
                f"Уговор дороже души! Фокусируйся!"
            )
            if win_info and WIN32_AVAILABLE:
                try:
                    win32gui.ShowWindow(win_info["hwnd"], win32con.SW_MINIMIZE)
                except Exception:
                    pass
            self._dispatch_speech(msg)

        else:
            # Persistent violation: close foreground or enforce discipline
            msg = (
                f"Ха-ха-ха! Ты испытываешь моё терпение! Закрываю '{details}'! ✖️😈\n"
                f"Сделка продолжается, и я не потерплю нарушений!"
            )
            if win_info and WIN32_AVAILABLE:
                try:
                    win32gui.PostMessage(win_info["hwnd"], win32con.WM_CLOSE, 0, 0)
                except Exception:
                    pass
            self._dispatch_speech(msg)

    def _on_deal_completed(self):
        """Called when deal duration expires successfully."""
        self.is_active = False
        log_info(f"Сделка на {self.duration_minutes} минут успешно завершена!")
        compl_msg = (
            f"🎉 БРАВО, МОЙ ДРУГ! ГРАНДИОЗНЫЙ ТРИУМФ! 🎙️✨\n"
            f"Наша {self.duration_minutes}-минутная сделка успешно выполнена!\n"
            f"Вы доказали силу воли перед лицом Радио-демона! Можете немного передохнуть!"
        )
        self._dispatch_speech(compl_msg)

    def _dispatch_speech(self, text: str):
        """Safely dispatches speech line to mascot on GUI thread."""
        try:
            self.m.root.after(0, lambda: self.m.show_speech(text, play_audio=not self.m.is_muted))
        except Exception:
            pass
