import re
import threading
from core.config import WIN32_AVAILABLE
from core.logger import log_info, log_warn, log_ai

if WIN32_AVAILABLE:
    import win32gui
    import win32process


class ContextAssistant:
    """
    Smart context-aware assistant for Alastor.
    Inspects the currently active application/window and provides specialized intelligence:
    - Code debugging & terminal error diagnosis (VS Code, Terminals, IDEs)
    - Web article / documentation summarization (Browsers)
    - In-character awareness of gaming, productivity, and document workflows.
    """

    CODE_PROCESSES = ["code.exe", "devenv.exe", "pycharm64.exe", "windowsterminal.exe", "wt.exe", "cmd.exe", "powershell.exe", "sublime_text.exe"]
    BROWSER_PROCESSES = ["msedge.exe", "chrome.exe", "firefox.exe", "browser.exe", "opera.exe", "brave.exe"]

    def __init__(self, mascot):
        self.m = mascot

    def get_foreground_info(self) -> dict:
        """Returns details about the currently focused user window."""
        info = {"hwnd": 0, "title": "", "process": "", "category": "general"}
        if not WIN32_AVAILABLE:
            return info
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd and hwnd != getattr(self.m, '_my_hwnd', 0):
                info["hwnd"] = hwnd
                info["title"] = win32gui.GetWindowText(hwnd).strip()
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                # Query process name via Win32 or psutil/wmi if available
                import psutil
                try:
                    p = psutil.Process(pid)
                    info["process"] = p.name().lower()
                except Exception:
                    pass

                proc = info["process"]
                title_low = info["title"].lower()

                if any(cp in proc for cp in self.CODE_PROCESSES) or ("code" in title_low) or ("visual studio" in title_low):
                    info["category"] = "code"
                elif any(bp in proc for bp in self.BROWSER_PROCESSES):
                    info["category"] = "browser"
                elif "steam" in proc or "game" in title_low or "dota" in title_low or "cs2" in title_low:
                    info["category"] = "gaming"
                elif "notepad" in proc or "word" in proc or "document" in title_low:
                    info["category"] = "document"
        except Exception as e:
            log_warn(f"Ошибка получения активного окна: {e}")
        return info

    def explain_active_error(self):
        """Captures screen and analyzes coding/terminal errors or bugs."""
        ctx = self.get_foreground_info()
        title = ctx["title"][:30] if ctx["title"] else "активное окно"
        self.m.show_speech(f"Вглядываюсь в твои исходники и терминал... ({title}) 🔍💻", play_audio=not self.m.is_muted)

        def _worker():
            prompt = (
                "Ты — Аластор, легендарный Радио-демон из Hazbin Hotel, но при этом великолепно разбираешься в программировании. "
                "Перед тобой снимок экрана пользователя, где открыт редактор кода или терминал. "
                "Внимательно найди ошибку компиляции, трассировку стека (traceback), баг или проблемную строку на снимке. "
                "Объясни в 2-4 предложениях суть проблемы и предложи конкретное исправление кода. "
                "Отвечай с фирменной харизмой радиоведущего 1930-х годов, остроумно и на русском языке."
            )
            ok, reply, prov = self.m.vision_engine.analyze_screen(user_prompt=prompt)
            if ok and reply:
                self.m.root.after(0, lambda: self.m.show_speech(reply, play_audio=not self.m.is_muted))
                if self.m.chat_win and hasattr(self.m.chat_win, 'append_message'):
                    self.m.root.after(0, lambda: self.m.chat_win.append_message("system", f"🛠️ Анализ кода [{prov}]\n"))
                    self.m.root.after(0, lambda: self.m.chat_win.append_message("bot", f"Аластор: {reply}\n\n"))

        threading.Thread(target=_worker, daemon=True).start()

    def summarize_active_screen(self):
        """Captures screen and produces an executive summary of the open page or text."""
        ctx = self.get_foreground_info()
        self.m.show_speech("Настраиваю радио-фокус на текст... Секунду, мой друг! 📰👓", play_audio=not self.m.is_muted)

        def _worker():
            prompt = (
                "Ты — Аластор из Hazbin Hotel. "
                "Перед тобой снимок экрана пользователя (статья, документация или страница). "
                "Сделай краткую выжимку (3 ключевых тезиса с маркерами), о чем здесь написано. "
                "Сохрани стиль винтажного радио-комментатора 1930-х годов. Отвечай только на русском языке."
            )
            ok, reply, prov = self.m.vision_engine.analyze_screen(user_prompt=prompt)
            if ok and reply:
                self.m.root.after(0, lambda: self.m.show_speech(reply, play_audio=not self.m.is_muted))
                if self.m.chat_win and hasattr(self.m.chat_win, 'append_message'):
                    self.m.root.after(0, lambda: self.m.chat_win.append_message("system", f"📰 Выжимка экрана [{prov}]\n"))
                    self.m.root.after(0, lambda: self.m.chat_win.append_message("bot", f"Аластор: {reply}\n\n"))

        threading.Thread(target=_worker, daemon=True).start()
