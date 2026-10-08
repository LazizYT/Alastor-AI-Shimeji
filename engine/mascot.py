import os
import sys
import random
import threading
import tkinter as tk

from core.config import (
    SIZE, DELAY, WIN32_AVAILABLE, PIL_AVAILABLE,
    SOUNDDEVICE_AVAILABLE, REQUESTS_AVAILABLE,
    SURFACE_FLOOR
)
from core.constants import SPEECHES, POKED_SPEECHES, GEMINI_API_KEY
from engine.sprite_manager import SpriteManager
from engine.speech_bubble import SpeechBubbleManager
from engine.physics import MascotPhysics
from engine.command_router import CommandRouter
from engine.autonomy import AutonomyManager
from engine.actions import MascotActions
from engine.context_menu import MascotContextMenu

from windows.window_dragger import WindowDragger
from windows.desktop_icons import DesktopIconMover
from windows.hotkeys import HotkeyManager
from windows.log_viewer import LogViewerWindow
from windows.input_controller import InputController
from windows.tray_icon import TrayIconManager
from windows.volume_controller import VolumeController
from windows.media_downloader import MediaDownloader
from windows.clipboard_assistant import ClipboardAssistant
from windows.window_surface_detector import WindowSurfaceDetector
from voice.app_launcher import AppLauncher

from voice.audio_recorder import record_audio
from voice.speech_to_text import transcribe_audio
from voice.tts_engine import RadioTTSEngine
from voice.wake_word import WakeWordDetector
from ai.chat_window import ChatWindow
from ai.alastor_brain import ALASTOR_VOICE_PROMPT, generate_alastor_reply
from ai.gemini_client import query_gemini
from ai.memory import MemoryManager
from ai.vision_engine import VisionEngine
from windows.deal_manager import DealManager
from windows.aimp_controller import AIMPController
from ai.context_assistant import ContextAssistant
from windows.timer_manager import TimerManager
from windows.workspace_presets import WorkspacePresets
from core.logger import log_info, log_voice, log_ai, log_warn, log_error

if WIN32_AVAILABLE:
    import win32gui
    import win32api
    import win32con


class Shimeji:
    """
    Main coordinator for the Alastor Desktop Mascot (Shimeji).
    Manages GUI canvas rendering, user mouse gestures, audio/speech playback,
    and connects the physics engine, autonomy manager, and system automation.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Alastor Shimeji")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "#000001")
        self.root.config(bg="#000001")

        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()

        self._my_hwnd = 0
        self.dragging = False
        self.drag_off_x = 0
        self.drag_off_y = 0
        self.dragging_window = False
        self.is_visible = True
        self._is_recording = False

        # 1. Core Subsystems & Managers
        self.sprite_mgr = SpriteManager()
        self.bubble_mgr = SpeechBubbleManager(self.root)
        self.win_dragger = WindowDragger(own_hwnd_getter=self._own_hwnd)
        self.desktop_mover = DesktopIconMover() if WIN32_AVAILABLE else None
        self.app_launcher = AppLauncher(mascot_ref=self)
        self.hotkey_mgr = HotkeyManager(
            on_hotkey_callback=self._on_hotkey_voice,
            on_wake_word_toggle_callback=self._on_hotkey_wake_word_toggle
        )
        self.tts = RadioTTSEngine(enabled=True)
        self.is_muted = self.tts.is_muted
        self.gesture_launch_mode = False
        self.wake_word_mode = True
        self.auto_capture_enabled = True
        self.vision_engine = VisionEngine()
        self.wake_word_detector = WakeWordDetector(mascot_ref=self)
        self.memory = MemoryManager()
        self.input_ctrl = InputController()
        self.tray_mgr = TrayIconManager(self)
        self.volume_ctrl = VolumeController()
        if hasattr(self, 'tts'):
            self.tts.on_playback_start = self.volume_ctrl.start_ducking
            self.tts.on_playback_end = self.volume_ctrl.stop_ducking
        self.media_downloader = MediaDownloader()
        self.clipboard_asst = ClipboardAssistant(mascot_ref=self)
        self.surface_detector = WindowSurfaceDetector(own_hwnd_getter=self._own_hwnd)
        self.deal_mgr = DealManager(self)
        self.aimp_ctrl = AIMPController(self)
        self.context_asst = ContextAssistant(self)
        self.timer_mgr = TimerManager(self)
        self.workspace_presets = WorkspacePresets(self)

        # 2. Physics & Autonomy Engines
        self.physics_engine = MascotPhysics(self.sw, self.sh, surface_detector=self.surface_detector)
        self.autonomy_mgr = AutonomyManager(self)
        self.actions = MascotActions(self)
        self.command_router = CommandRouter(self)
        self.context_menu = MascotContextMenu(self)

        # Windows
        self.chat_win = None
        self.log_win = None
        self.voice_settings_win = None
        initial_key = (
            os.environ.get("GOOGLE_API_KEY", "")
            or os.environ.get("GEMINI_API_KEY", "")
            or self.vision_engine.config.get("gemini_api_key", "")
            or GEMINI_API_KEY
        )
        self.api_key_var = tk.StringVar(value=initial_key)

        # 3. Canvas & Bindings
        self.canvas = tk.Canvas(
            self.root, width=SIZE, height=SIZE,
            bg="#000001", highlightthickness=0, bd=0
        )
        self.canvas.pack()
        self.sprite_item = self.canvas.create_image(0, 0, anchor="nw")

        self.canvas.bind("<ButtonPress-1>",   self.on_press)
        self.canvas.bind("<B1-Motion>",        self.on_drag)
        self.canvas.bind("<ButtonRelease-1>",  self.on_release)
        self.canvas.bind("<ButtonPress-3>",    self.on_right_click)
        self.canvas.bind("<Double-Button-1>",  self.on_double_click)

        # Start loops & daemons
        self.schedule_random_speech()
        self.schedule_auto_capture()
        self.set_state("standing")
        self.root.after(DELAY, self.tick)
        self.root.after(500, self._cache_own_hwnd)
        self.autonomy_mgr.start()
        self.hotkey_mgr.start()
        if self.wake_word_mode and hasattr(self, 'wake_word_detector'):
            self.wake_word_detector.start()
        self.tray_mgr.start()

        log_info("Экранный маскот Аластор инициализирован (Радио-DSP + TTS + Трей активны)")
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.root.mainloop()

    # -------------------------------------------------------------------------
    # Physics Property Proxies (Backward-Compatible)
    # -------------------------------------------------------------------------
    @property
    def x(self): return self.physics_engine.x
    @x.setter
    def x(self, val): self.physics_engine.x = float(val)

    @property
    def y(self): return self.physics_engine.y
    @y.setter
    def y(self, val): self.physics_engine.y = float(val)

    @property
    def vel_x(self): return self.physics_engine.vel_x
    @vel_x.setter
    def vel_x(self, val): self.physics_engine.vel_x = float(val)

    @property
    def vel_y(self): return self.physics_engine.vel_y
    @vel_y.setter
    def vel_y(self, val): self.physics_engine.vel_y = float(val)

    @property
    def state(self): return self.physics_engine.state
    @state.setter
    def state(self, val): self.physics_engine.state = val

    @property
    def surface(self): return self.physics_engine.surface
    @surface.setter
    def surface(self, val): self.physics_engine.surface = val

    @property
    def current_anim(self): return self.physics_engine.current_anim
    @current_anim.setter
    def current_anim(self, val): self.physics_engine.current_anim = val

    @property
    def frame_idx(self): return self.physics_engine.frame_idx
    @frame_idx.setter
    def frame_idx(self, val): self.physics_engine.frame_idx = val

    @property
    def frame_timer(self): return self.physics_engine.frame_timer
    @frame_timer.setter
    def frame_timer(self, val): self.physics_engine.frame_timer = val

    @property
    def frame_delay(self): return self.physics_engine.frame_delay
    @frame_delay.setter
    def frame_delay(self, val): self.physics_engine.frame_delay = val

    @property
    def flipped(self): return self.physics_engine.flipped
    @flipped.setter
    def flipped(self, val): self.physics_engine.flipped = val

    @property
    def rotation(self): return self.physics_engine.rotation
    @rotation.setter
    def rotation(self, val): self.physics_engine.rotation = val

    @property
    def target_window_hwnd(self): return self.physics_engine.target_window_hwnd
    @target_window_hwnd.setter
    def target_window_hwnd(self, val): self.physics_engine.target_window_hwnd = val

    @property
    def walk_on_windows_enabled(self): return self.physics_engine.walk_on_windows_enabled
    @walk_on_windows_enabled.setter
    def walk_on_windows_enabled(self, val): self.physics_engine.walk_on_windows_enabled = val

    @property
    def ground_y(self): return self.physics_engine.ground_y
    @property
    def ceiling_y(self): return self.physics_engine.ceiling_y
    @property
    def wall_lx(self): return self.physics_engine.wall_lx
    @property
    def wall_rx(self): return self.physics_engine.wall_rx
    @property
    def current_floor_y(self): return self.physics_engine.current_floor_y
    @current_floor_y.setter
    def current_floor_y(self, val): self.physics_engine.current_floor_y = val

    # -------------------------------------------------------------------------
    # Main Loop, Physics & Animation
    # -------------------------------------------------------------------------
    def set_state(self, state: str, surface: str = None):
        self.physics_engine.set_state(state, surface=surface)
        self.update_sprite()

    def tick(self):
        if not self.dragging and not self.dragging_window:
            self.physics_engine.update_physics()
            self._apply_pos()
            self.animate()
        self.root.after(DELAY, self.tick)

    def animate(self):
        self.frame_timer += 1
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(self.current_anim)
            self.update_sprite()

            if self.frame_idx == 0 and self.state not in ("falling", "climb_left", "climb_right", "ceiling_walk"):
                if random.random() < 0.25:
                    if self.surface == SURFACE_FLOOR:
                        self.physics_engine.choose_next_floor_state()
                    else:
                        self.physics_engine.choose_next_ceiling_state()

    def update_sprite(self):
        if not self.current_anim:
            return
        frame_id = self.current_anim[self.frame_idx % len(self.current_anim)]
        img = self.sprite_mgr.get(frame_id, flipped=self.flipped, rotation=self.rotation)
        if img:
            self.canvas.itemconfig(self.sprite_item, image=img)

    def _apply_pos(self):
        ix = int(self.x)
        iy = int(self.y)
        self.root.geometry(f"{SIZE}x{SIZE}+{ix}+{iy}")
        self.bubble_mgr.update_position(self.x, self.y, self.sw, self.sh)

    # -------------------------------------------------------------------------
    # Mouse Gestures & Dragging
    # -------------------------------------------------------------------------
    def on_press(self, e):
        self.dragging   = True
        self.drag_off_x = e.x
        self.drag_off_y = e.y
        self.vel_x = 0
        self.vel_y = 0
        self.target_window_hwnd = 0
        self.bubble_mgr.hide()
        self.set_state("carry")

    def on_drag(self, e):
        if self.dragging_window and WIN32_AVAILABLE:
            dx = e.x - self.drag_off_x
            dy = e.y - self.drag_off_y
            self.win_dragger.drag_by(dx, dy)
        elif self.dragging:
            self.x = self.root.winfo_x() + (e.x - self.drag_off_x)
            self.y = self.root.winfo_y() + (e.y - self.drag_off_y)
            self.x = max(float(self.wall_lx), min(self.x, float(self.wall_rx)))
            self.y = max(float(self.ceiling_y), min(self.y, float(self.ground_y)))
            self._apply_pos()

    def on_release(self, _e):
        if self.dragging_window:
            self.dragging_window = False
            self.dragging = False
            self.win_dragger.release()
            self.show_speech("Хе-хе, переставил! 😈")
            self.set_state("standing", surface=SURFACE_FLOOR)
            return

        self.dragging = False
        if self.y < self.ground_y:
            self.set_state("falling", surface=SURFACE_FLOOR)
        else:
            self.physics_engine.choose_next_floor_state()

    def on_double_click(self, _e):
        self.show_speech(random.choice(POKED_SPEECHES), play_audio=True)
        if "blob" in self.sprite_mgr.images:
            self.set_state("blob", surface=SURFACE_FLOOR)

    def on_right_click(self, e):
        self.context_menu.show(e)

    # -------------------------------------------------------------------------
    # Win32 Helpers & Actions Routing
    # -------------------------------------------------------------------------
    def _cache_own_hwnd(self):
        if not WIN32_AVAILABLE:
            return
        def _cb(hwnd, _):
            if win32gui.GetWindowText(hwnd) == "Alastor Shimeji":
                self._my_hwnd = hwnd
        win32gui.EnumWindows(_cb, None)

    def _own_hwnd(self):
        return self._my_hwnd

    def _toggle_follow_cursor(self):
        self.physics_engine.follow_cursor_enabled = not self.physics_engine.follow_cursor_enabled
        state = "следую за тобой~ 👁️" if self.physics_engine.follow_cursor_enabled else "свободен 🦋"
        self.show_speech(f"Следование:\n{state}")

    # Action Delegates
    def action_jump_to_window(self): self.actions.jump_to_window()
    def action_jump_to_floor(self): self.actions.jump_to_floor()
    def action_look_at_screen(self, prompt: str = None): self.actions.look_at_screen(prompt)
    def action_explain_clipboard(self): self.actions.explain_clipboard()
    def action_translate_clipboard(self): self.actions.translate_clipboard()
    def action_download_media(self, audio_only: bool = True, url: str = None): self.actions.download_media(audio_only, url)
    def action_adjust_volume(self, delta: int): self.actions.adjust_volume(delta)
    def action_set_volume(self, level: int): self.actions.set_volume(level)
    def action_toggle_win_mute(self): self.actions.toggle_win_mute()
    def action_prompt_type_text(self): self.actions.prompt_type_text()
    def troll_minimize(self) -> bool:
        if hasattr(self, 'win_dragger') and self.win_dragger:
            return self.win_dragger.minimize_foreground(exclude=self._own_hwnd())
        elif hasattr(self, 'actions'):
            self.actions.troll_minimize()
            return True
        return False

    def action_close_foreground(self) -> bool:
        if hasattr(self, 'win_dragger') and self.win_dragger:
            return self.win_dragger.close_foreground(exclude=self._own_hwnd())
        elif hasattr(self, 'actions'):
            self.actions.close_foreground()
            return True
        return False

    def action_sort_desktop(self):
        if hasattr(self, 'desktop_icons') and self.desktop_icons:
            self.desktop_icons.arrange_grid()

    def try_execute_input_command(self, text: str) -> tuple[bool, str]:
        return self.command_router.route_command(text)

    # -------------------------------------------------------------------------
    # Speech, Audio & Voice Recognition
    # -------------------------------------------------------------------------
    def show_speech(self, text: str, play_audio: bool = True):
        self.bubble_mgr.show_speech(text, self.x, self.y, self.sw, self.sh)
        log_info(f"Реплика Аластора: {text[:80]}")
        if getattr(self, 'is_muted', False):
            play_audio = False
        if play_audio and hasattr(self, 'tts') and self.tts.enabled:
            self.tts.speak(text)

    def schedule_random_speech(self):
        # 5x reduced chatter frequency: checks every 1.5 - 2.5 minutes with ~40% chance (~5 minutes between random speeches)
        self.root.after(random.randint(90000, 150000), self.random_speech_tick)

    def random_speech_tick(self):
        if not getattr(self, '_is_recording', False) and not self.dragging:
            tts = getattr(self, 'tts', None)
            if not (tts and getattr(tts, 'is_speaking', lambda: False)()):
                if random.random() < 0.40:
                    self.show_speech(random.choice(SPEECHES), play_audio=True)
        self.schedule_random_speech()

    def schedule_auto_capture(self):
        # Auto capture screen every 2 to 5 minutes (120,000 to 300,000 ms)
        interval = random.randint(120000, 300000)
        self.root.after(interval, self.auto_capture_tick)

    def auto_capture_tick(self):
        if not getattr(self, 'auto_capture_enabled', True):
            self.schedule_auto_capture()
            return

        if getattr(self, '_is_recording', False) or getattr(self, 'dragging', False) or getattr(self, 'dragging_window', False):
            self.schedule_auto_capture()
            return

        tts = getattr(self, 'tts', None)
        if tts and getattr(tts, 'is_speaking', lambda: False)():
            self.schedule_auto_capture()
            return

        threading.Thread(target=self._auto_capture_worker, daemon=True).start()
        self.schedule_auto_capture()

    def _auto_capture_worker(self):
        try:
            log_ai("Автозахват экрана (интервал 2-5 мин): анализ рабочего стола...")
            auto_prompt = (
                "Ты — Аластор, легендарный Радио-демон из Hazbin Hotel. "
                "Перед тобой снимок экрана твоего компаньона. "
                "Сделай спонтанный, краткий (1-3 предложения), остроумный и живой радио-комментарий к тому, "
                "что прямо сейчас происходит на экране пользователя (какая программа открыта, игра, видео, код или рабочий стол). "
                "Обязательно добавь характерную харизму, легкую демоническую иронию и улыбку радиоведущего 1930-х годов! "
                "Отвечай только на русском языке."
            )
            ok, reply, prov = self.vision_engine.analyze_screen(user_prompt=auto_prompt)
            if ok and reply:
                log_ai(f"Автозахват экрана успешен [{prov}]: {reply[:60]}")
                self.root.after(0, lambda: self.show_speech(reply, play_audio=not self.is_muted))
                if self.chat_win and tk.Toplevel.winfo_exists(self.chat_win.win):
                    self.root.after(0, lambda: self.chat_win.append_message("system", f"👁️ Автозахват экрана [{prov}]\n"))
                    self.root.after(0, lambda: self.chat_win.append_message("bot", f"Аластор: {reply}\n\n"))
        except Exception as ex:
            log_warn(f"Ошибка фонового автозахвата экрана: {ex}")

    def open_chat(self):
        if self.chat_win and tk.Toplevel.winfo_exists(self.chat_win.win):
            self.chat_win.win.lift()
            return
        self.chat_win = ChatWindow(self.root, self.api_key_var, self)

    def open_log_viewer(self):
        if self.log_win and tk.Toplevel.winfo_exists(self.log_win.win):
            self.log_win.win.lift()
            self.log_win.refresh_logs()
            return
        self.log_win = LogViewerWindow(self.root)

    def open_voice_settings(self):
        if self.voice_settings_win and tk.Toplevel.winfo_exists(self.voice_settings_win.win):
            self.voice_settings_win.win.lift()
            self.voice_settings_win.win.focus_force()
            return
        from windows.voice_settings import VoiceSettingsWindow
        self.voice_settings_win = VoiceSettingsWindow(self.root, self.tts)

    def toggle_mute(self):
        self.is_muted = self.tts.toggle_mute()
        state = "Трансляция заглушена! В эфире тишина... (Mute) 🔇" if self.is_muted else "Звук включён! Радио-эфир снова на связи! 🔊"
        self.show_speech(state, play_audio=not self.is_muted)
        log_info(f"Mute статус переключен: {self.is_muted}")

    def set_mute(self, muted: bool):
        if muted:
            self.tts.mute()
            self.is_muted = True
            self.show_speech("Трансляция заглушена! (Mute активирован) 🔇", play_audio=False)
        else:
            self.tts.unmute()
            self.is_muted = False
            self.show_speech("Звук включён! Радио-эфир снова на связи! 🔊", play_audio=True)

    def toggle_gesture_launch_mode(self):
        self.gesture_launch_mode = not self.gesture_launch_mode
        st = "ВКЛЮЧЁН 🎩🖱️ (навожу курсор и жестикулирую)" if self.gesture_launch_mode else "ВЫКЛЮЧЕН ⚡ (прямой запуск через радиоволны)"
        self.show_speech(f"Режим жестов и мыши {st}!", play_audio=True)
        log_info(f"Режим запуска жестами изменен: {self.gesture_launch_mode}")

    def set_gesture_launch_mode(self, enabled: bool):
        self.gesture_launch_mode = enabled
        st = "ВКЛЮЧЁН 🎩🖱️" if enabled else "ВЫКЛЮЧЕН ⚡"
        log_info(f"Режим запуска жестами установлен: {self.gesture_launch_mode}")

    def toggle_auto_capture(self):
        self.set_auto_capture(not getattr(self, 'auto_capture_enabled', True))

    def set_auto_capture(self, enabled: bool):
        self.auto_capture_enabled = enabled
        st = "ВКЛЮЧЁН 👁️📻 (взгляну на экран каждые 2-5 минут)" if enabled else "ВЫКЛЮЧЕН 🙈"
        self.show_speech(f"Автозахват экрана:\n{st}!", play_audio=not self.is_muted)
        log_info(f"Режим автозахвата экрана изменен: {self.auto_capture_enabled}")

    def show_memory_dossier(self):
        summary = self.memory.get_readable_summary()
        self.show_speech(summary, play_audio=False)

    def _on_hotkey_voice(self):
        try:
            self.root.after(0, self.start_voice_capture)
        except Exception:
            pass

    def _on_hotkey_wake_word_toggle(self):
        try:
            log_info("Горячая клавиша F9: переключение режима триггер-слова")
            self.root.after(0, self.toggle_wake_word_mode)
        except Exception:
            pass

    def set_wake_word_mode(self, enabled: bool):
        self.wake_word_mode = enabled
        if enabled:
            if hasattr(self, 'wake_word_detector'):
                self.wake_word_detector.start()
            self.show_speech("🎙️ Режим триггер-слова «Аластор» включён!\nПозовите меня по имени! 📻✨", play_audio=True)
            log_info("Режим триггер-слова «Аластор» активирован (F9)")
        else:
            if hasattr(self, 'wake_word_detector'):
                self.wake_word_detector.stop()
            self.show_speech("Фоновый режим триггера выключен! 🔇", play_audio=False)
            log_info("Режим триггер-слова «Аластор» отключён (F9)")

    def toggle_wake_word_mode(self):
        self.set_wake_word_mode(not self.wake_word_mode)

    def start_voice_capture(self):
        if hasattr(self, 'tts'):
            self.tts.stop_speech()
        if self._is_recording:
            return
        if not SOUNDDEVICE_AVAILABLE:
            self.show_speech("⚠️ Библиотека sounddevice\nне установлена!", play_audio=False)
            return
        self._is_recording = True
        log_voice("Запуск голосового захвата (микрофон открыт)...")
        self.show_speech("🎙️ В эфире! Слушаю вас...\n(говорите в микрофон)", play_audio=False)
        if "guitar" in self.sprite_mgr.images:
            self.set_state("guitar", surface=SURFACE_FLOOR)
        threading.Thread(target=self._voice_record_worker, daemon=True).start()

    def _voice_record_worker(self):
        if hasattr(self, 'volume_ctrl'):
            self.volume_ctrl.start_ducking()
        try:
            audio_data = record_audio(duration=4.5, sample_rate=16000)
            self.root.after(0, lambda: self.show_speech("📻 Обрабатываю радиоволны...\n(распознавание речи)", play_audio=False))

            recognized_text = transcribe_audio(audio_data, sample_rate=16000)
            if not recognized_text:
                log_voice("Речь не распознана (тишина в эфире)")
                self.root.after(0, lambda: self.show_speech("Ха-ха! Тишина в эфире...\nЯ ничего не услышал! 📻", play_audio=True))
                return

            self.handle_recognized_speech(recognized_text)

        except Exception as ex:
            log_error(f"Ошибка голосового ввода: {ex}")
            self.root.after(0, lambda: self.show_speech(f"Помехи в эфире:\n{str(ex)[:40]} 📻", play_audio=False))
        finally:
            if hasattr(self, 'volume_ctrl'):
                self.volume_ctrl.stop_ducking()
            self._is_recording = False

    def handle_recognized_speech(self, raw_text: str):
        """Unified processor for speech from push-to-talk OR wake-word background trigger."""
        clean_text = raw_text.strip()
        log_voice(f"Распознано: «{clean_text}»")

        self.memory.extract_facts(clean_text)
        self.memory.record_interaction()

        handled, reply = self.command_router.route_command(clean_text)
        if handled and reply:
            log_info(f"Команда выполнена: {reply}")
            self.root.after(0, lambda: self.show_speech(reply, play_audio=True))
            if self.chat_win and tk.Toplevel.winfo_exists(self.chat_win.win):
                self.root.after(0, lambda: self.chat_win.append_message("user", f"Вы (голос): {clean_text}\n"))
                self.root.after(0, lambda: self.chat_win.append_message("bot", f"Аластор: {reply}\n\n"))
            return
        elif handled:
            # Action handled asynchronously or showed its own announcement (e.g. vision or chain)
            if self.chat_win and tk.Toplevel.winfo_exists(self.chat_win.win):
                self.root.after(0, lambda: self.chat_win.append_message("user", f"Вы (голос): {clean_text}\n"))
            return

        self.root.after(0, lambda: self.show_speech(f"🎙️ Вы: «{clean_text}»\n\nРазмышляю...", play_audio=False))
        threading.Thread(target=self._query_ai_for_voice, args=(clean_text,), daemon=True).start()

    def _query_ai_for_voice(self, user_text: str):
        api_key = (
            self.api_key_var.get().strip()
            or os.environ.get("GOOGLE_API_KEY", "")
            or os.environ.get("GEMINI_API_KEY", "")
            or self.vision_engine.config.get("gemini_api_key", "")
        )
        mem_ctx = self.memory.get_prompt_context()
        prompt_with_memory = f"{ALASTOR_VOICE_PROMPT}\n\n{mem_ctx}"

        reply = None

        # Tier 1: Google Gemini Flash
        if api_key and REQUESTS_AVAILABLE:
            try:
                log_ai(f"Запрос к Gemini Flash: «{user_text}»")
                reply = query_gemini(
                    api_key,
                    [{"role": "user", "parts": [{"text": user_text}]}],
                    prompt_with_memory,
                    max_tokens=512,
                    temperature=0.85,
                    timeout=12
                )
                if reply:
                    log_ai(f"Ответ Gemini: {reply[:60]}")
            except Exception as e:
                log_warn(f"Gemini API вернул ошибку, перехожу на резервные ИИ: {e}")

        # Tier 2: OpenRouter API Fallback
        if not reply and REQUESTS_AVAILABLE:
            or_key = self.vision_engine.config.get("openrouter_api_key", "") or os.environ.get("OPENROUTER_API_KEY", "")
            if or_key:
                try:
                    import requests
                    headers = {
                        "Authorization": f"Bearer {or_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/MegatronF0id5la4yer/bocchi-shimeji-con-ia-local-y-api",
                        "X-Title": "Alastor Shimeji Voice"
                    }
                    payload = {
                        "model": "google/gemini-2.0-flash-exp:free",
                        "messages": [
                            {"role": "system", "content": prompt_with_memory},
                            {"role": "user", "content": user_text}
                        ],
                        "max_tokens": 150,
                        "temperature": 0.85
                    }
                    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        reply = data["choices"][0]["message"]["content"].strip()
                        log_ai(f"Ответ OpenRouter: {reply[:60]}")
                except Exception as e:
                    log_warn(f"OpenRouter резервный запрос не удался: {e}")

        # Tier 3: Local Ollama Fallback
        if not reply and REQUESTS_AVAILABLE:
            try:
                import requests
                ollama_url = self.vision_engine.config.get("ollama_url", "http://localhost:11434")
                payload = {
                    "model": "llama3.2",
                    "prompt": f"{prompt_with_memory}\n\nПользователь: {user_text}\nАластор:",
                    "stream": False
                }
                resp = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    reply = data.get("response", "").strip()
                    if reply:
                        log_ai(f"Ответ Ollama: {reply[:60]}")
            except Exception:
                pass

        # Tier 4: Local Canon Dialogue Engine (Ultimate Offline Fallback)
        if not reply:
            reply = generate_alastor_reply(user_text)
            log_ai(f"Локальный ответ: {reply[:60]}")

        self.root.after(0, lambda: self.show_speech(reply, play_audio=True))
        if self.chat_win and tk.Toplevel.winfo_exists(self.chat_win.win):
            self.root.after(0, lambda: self.chat_win.append_message("user", f"Вы (голос): {user_text}\n"))
            self.root.after(0, lambda: self.chat_win.append_message("bot", f"Аластор: {reply}\n\n"))

    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        if self.is_visible:
            self.root.deiconify()
            self.root.lift()
            self.show_speech("Я вернулся в эфир! 🎙️", play_audio=True)
            log_info("Маскот восстановлен из системного трея")
        else:
            self.root.withdraw()
            log_info("Маскот свернут в системный трей (фоновый режим)")

    def on_exit(self):
        try:
            if hasattr(self, 'wake_word_detector'):
                self.wake_word_detector.stop()
            if hasattr(self, 'tray_mgr'):
                self.tray_mgr.stop()
            if hasattr(self, 'tts'):
                self.tts.stop_speech()
            if hasattr(self, 'hotkey_mgr'):
                self.hotkey_mgr.stop()
            if hasattr(self, 'deal_mgr'):
                self.deal_mgr.cancel_deal()
            if hasattr(self, 'timer_mgr'):
                self.timer_mgr.stop()
            if hasattr(self, 'autonomy_mgr'):
                self.autonomy_mgr.stop()
            log_info("Завершение работы маскота Аластора")
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)

