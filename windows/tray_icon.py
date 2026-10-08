import os
import threading
from PIL import Image, ImageDraw
import pystray
from core.config import BASE_DIR, IMG_DIR
from core.logger import log_info, log_error

class TrayIconManager:
    """
    Manages Alastor's system tray (taskbar notification area) presence.
    Runs in the background, provides a right-click menu, and allows toggling mascot visibility.
    """
    def __init__(self, mascot_ref):
        self.mascot = mascot_ref
        self.icon = None
        self._thread = None
        self.is_running = False

    def _load_icon_image(self) -> Image.Image:
        # Search for Alastor sprite
        potential_paths = [
            os.path.join(IMG_DIR, "shime1.png"),
            os.path.join(BASE_DIR, "img", "794", "shime1.png"),
            os.path.join(BASE_DIR, "img", "Shimeji", "shime1.png")
        ]

        for p in potential_paths:
            if os.path.exists(p):
                try:
                    img = Image.open(p).convert("RGBA")
                    # Resize to crisp 64x64 tray icon
                    return img.resize((64, 64), Image.Resampling.LANCZOS)
                except Exception:
                    pass

        # Fallback: create vintage dark-red radio icon
        img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill="#8b0000", outline="#cba6f7", width=3)
        draw.rectangle([20, 26, 44, 44], fill="#11111b", outline="#cba6f7", width=2)
        draw.line([32, 26, 32, 10], fill="#cba6f7", width=3)
        draw.ellipse([29, 7, 35, 13], fill="#f38ba8")
        return img

    def start(self):
        """Start the system tray icon in a dedicated daemon thread."""
        if self.is_running:
            return

        def _runner():
            try:
                img = self._load_icon_image()
                menu = pystray.Menu(
                    pystray.MenuItem("🎙️ Аластор: Радио-демон", lambda: None, enabled=False),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("💬 Радио-чат с Аластором", self._on_open_chat),
                    pystray.MenuItem("👀 Взглянуть на экран (Зрение ИИ)", self._on_look_at_screen),
                    pystray.MenuItem(self._get_auto_capture_label, self._on_toggle_auto_capture),
                    pystray.MenuItem("🤝 Сделка с демоном (25 мин)", self._on_start_deal),
                    pystray.MenuItem("📻 Радио AIMP (Play/Pause)", self._on_aimp_playpause),
                    pystray.MenuItem("💻 Рабочий сетап (50/50)", self._on_work_preset),
                    pystray.MenuItem("📋 Объяснить буфер обмена", self._on_explain_clipboard),
                    pystray.MenuItem("📥 Скачать медиа по ссылке", self._on_download_media),
                    pystray.MenuItem("🔊 Громкость Windows (+10%)", self._on_vol_up),
                    pystray.MenuItem(self._get_mute_label, self._on_toggle_mute),
                    pystray.MenuItem(self._get_wake_word_label, self._on_toggle_wake_word),
                    pystray.MenuItem(self._get_gesture_label, self._on_toggle_gesture),
                    pystray.MenuItem("🎛️ Настройки голоса...", self._on_open_voice_settings),
                    pystray.MenuItem("📜 Просмотр логов", self._on_open_logs),
                    pystray.MenuItem("🧠 Память и досье", self._on_open_memory),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("👁️ Скрыть / Показать маскота", self._on_toggle_visibility, default=True),
                    pystray.MenuItem("🎲 Случайная цитата", self._on_random_quote),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("✕ Выход из эфира", self._on_exit)
                )

                self.icon = pystray.Icon(
                    "AlastorShimeji",
                    img,
                    "Alastor Shimeji (Фоновое радио)",
                    menu
                )
                self.is_running = True
                log_info("Иконка Аластора в системном трее (панели задач) активирована")
                self.icon.run()
            except Exception as e:
                log_error(f"Ошибка запуска трей-иконки: {e}")
                self.is_running = False

        self._thread = threading.Thread(target=_runner, daemon=True)
        self._thread.start()

    def _on_open_chat(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.open_chat)

    def _on_look_at_screen(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.action_look_at_screen)

    def _on_explain_clipboard(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.action_explain_clipboard)

    def _on_download_media(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, lambda: self.mascot.action_download_media(audio_only=True))

    def _on_vol_up(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, lambda: self.mascot.action_adjust_volume(10))

    def _get_mute_label(self, item=None):
        if self.mascot and getattr(self.mascot, "is_muted", False):
            return "🔊 Включить звук (Unmute)"
        return "🔇 Заглушить звук (Mute)"

    def _on_toggle_mute(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.toggle_mute)

    def _get_wake_word_label(self, item=None):
        if self.mascot and getattr(self.mascot, "wake_word_mode", False):
            return "🎙️ Триггер «Аластор» (F9) [ВКЛ]"
        return "🎙️ Триггер «Аластор» (F9) [ВЫКЛ]"

    def _on_toggle_wake_word(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.toggle_wake_word_mode)

    def _get_gesture_label(self, item=None):
        if self.mascot and getattr(self.mascot, "gesture_launch_mode", False):
            return "🎩 Запуск: Режим жестов и мыши [ВКЛ]"
        return "⚡ Запуск: Прямой запуск (радиоволны)"

    def _on_toggle_gesture(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.toggle_gesture_launch_mode)

    def _get_auto_capture_label(self, item=None):
        if self.mascot and getattr(self.mascot, "auto_capture_enabled", True):
            return "👁️ Автозахват экрана [ВКЛ]"
        return "👁️ Автозахват экрана [ВЫКЛ]"

    def _on_toggle_auto_capture(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.toggle_auto_capture)

    def _on_start_deal(self, icon=None, item=None):
        if self.mascot and hasattr(self.mascot, 'deal_mgr'):
            self.mascot.root.after(0, lambda: self.mascot.show_speech(self.mascot.deal_mgr.start_deal(25)))

    def _on_aimp_playpause(self, icon=None, item=None):
        if self.mascot and hasattr(self.mascot, 'aimp_ctrl'):
            self.mascot.root.after(0, lambda: self.mascot.show_speech(self.mascot.aimp_ctrl.play_pause()[1]))

    def _on_work_preset(self, icon=None, item=None):
        if self.mascot and hasattr(self.mascot, 'workspace_presets'):
            self.mascot.root.after(0, lambda: self.mascot.workspace_presets.apply_preset("рабочий"))

    def _on_open_voice_settings(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.open_voice_settings)

    def _on_open_logs(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.open_log_viewer)

    def _on_open_memory(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.show_memory_dossier)

    def _on_toggle_visibility(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.toggle_visibility)

    def _on_random_quote(self, icon=None, item=None):
        if self.mascot:
            self.mascot.root.after(0, self.mascot.speak_random_quote)

    def _on_exit(self, icon=None, item=None):
        self.stop()
        if self.mascot:
            self.mascot.root.after(0, self.mascot.on_exit)

    def stop(self):
        """Cleanly remove the icon from the system tray."""
        self.is_running = False
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
