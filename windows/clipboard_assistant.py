import re
import threading
from core.logger import log_info, log_warn, log_error
from ai.alastor_brain import generate_alastor_reply

try:
    import win32clipboard
    WIN32_CLIP_AVAILABLE = True
except ImportError:
    WIN32_CLIP_AVAILABLE = False


class ClipboardAssistant:
    """
    Inspects Windows clipboard text/code and provides Alastor's AI explanations,
    translations, and URL extraction.
    """

    def __init__(self, mascot_ref=None):
        self.mascot = mascot_ref

    def get_clipboard_text(self) -> str:
        """Safely retrieves text from Windows clipboard."""
        if WIN32_CLIP_AVAILABLE:
            try:
                win32clipboard.OpenClipboard()
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    return data.strip() if data else ""
            except Exception as e:
                log_warn(f"Ошибка чтения буфера win32: {e}")
            finally:
                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass

        # Fallback via Tkinter
        try:
            import tkinter as tk
            r = tk.Tk()
            r.withdraw()
            txt = r.clipboard_get()
            r.destroy()
            return txt.strip() if txt else ""
        except Exception:
            return ""

    def get_url(self) -> str | None:
        text = self.get_clipboard_text()
        if not text:
            return None
        match = re.search(r'https?://[^\s<>"]+', text)
        return match.group(0).rstrip(".,;!?:)'\"") if match else None

    def explain_clipboard(self, on_finish=None) -> tuple[bool, str]:
        text = self.get_clipboard_text()
        if not text:
            msg = "Твой буфер обмена пуст, дорогуша! Скопируй любой текст или код (Ctrl+C), и я разложу его по полочкам! 📋😈"
            if on_finish:
                on_finish(False, msg)
            return False, msg

        preview = text[:60].replace("\n", " ")
        log_info(f"Анализ буфера обмена: «{preview}...»")

        prompt = (
            f"Ты — Аластор, Радио-демон из Hazbin Hotel. "
            f"Пользователь скопировал следующий фрагмент в буфер обмена:\n\n"
            f"\"\"\"\n{text[:2000]}\n\"\"\"\n\n"
            f"Объясни кратко и ёмко (в 2-4 предложениях), что это такое, в чём суть или есть ли тут ошибки (если это код). "
            f"Отвечай в своём фирменном винтажном радио-стиле: саркастично, харизматично, с улыбкой и радио-метафорами на русском языке!"
        )

        def _worker():
            reply = self._query_ai(prompt, fallback_seed=f"объясни: {preview}")
            if on_finish:
                on_finish(True, reply)

        threading.Thread(target=_worker, daemon=True).start()
        return True, "Вглядываюсь в твой буфер обмена... Секунду! 📋🎙️"

    def translate_clipboard(self, on_finish=None) -> tuple[bool, str]:
        text = self.get_clipboard_text()
        if not text:
            msg = "Буфер обмена пуст! Скопируй иностранный текст, и я озвучу его на нашем великом радио! 🌐📻"
            if on_finish:
                on_finish(False, msg)
            return False, msg

        prompt = (
            f"Ты — Аластор, Радио-демон. Переведи следующий текст из буфера обмена на русский язык "
            f"(или на английский, если он уже русский):\n\n"
            f"\"\"\"\n{text[:2000]}\n\"\"\"\n\n"
            f"Дай точный перевод, сохранив винтажный джентльменский тон и харизму радиоведущего 1930-х годов!"
        )

        def _worker():
            reply = self._query_ai(prompt, fallback_seed="перевод")
            if on_finish:
                on_finish(True, reply)

        threading.Thread(target=_worker, daemon=True).start()
        return True, "Перевожу частоту вещания на твой текст... 🌐🎙️"

    def _query_ai(self, prompt: str, fallback_seed: str = "") -> str:
        # Try Gemini API first
        if self.mascot and hasattr(self.mascot, "api_key_var"):
            key = self.mascot.api_key_var.get().strip()
            if key:
                try:
                    from ai.gemini_client import query_gemini
                    from ai.alastor_brain import ALASTOR_SYSTEM_PROMPT
                    reply = query_gemini(key, [{"role": "user", "parts": [{"text": prompt}]}], ALASTOR_SYSTEM_PROMPT, max_tokens=600)
                    if reply:
                        return reply
                except Exception as e:
                    log_warn(f"Gemini clipboard error: {e}")

        # Fallback to local heuristic / brain
        return generate_alastor_reply(fallback_seed)
