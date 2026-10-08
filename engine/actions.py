import os
import random
import threading
import tkinter as tk
from tkinter import simpledialog
from core.config import WIN32_AVAILABLE
from core.logger import log_info, log_warn


class MascotActions:
    """
    Action dispatcher for user-triggered or menu-triggered mascot actions:
    - Vision analysis of the screen
    - Clipboard AI analysis and translation
    - Media downloading (MP3 / MP4)
    - Windows Master Audio volume control
    - Window platform navigation (jumping on windows, jumping to floor)
    - Desktop icon manipulation (shuffle, scatter, sort, trash, move)
    - Window trolling (minimize, close, maximize, drag)
    - Interactive text typing
    """

    def __init__(self, mascot):
        self.m = mascot

    # -------------------------------------------------------------------------
    # Vision & Screen Analysis
    # -------------------------------------------------------------------------
    def look_at_screen(self, user_prompt: str = None):
        self.m.show_speech("Настраиваю радио-взор на экран... Секунду! 👀🎙️", play_audio=not self.m.is_muted)

        def _worker():
            ok, reply, prov = self.m.vision_engine.analyze_screen(user_prompt)
            self.m.root.after(0, lambda: self.m.show_speech(reply, play_audio=not self.m.is_muted))
            if self.m.chat_win and tk.Toplevel.winfo_exists(self.m.chat_win.win):
                self.m.root.after(0, lambda: self.m.chat_win.append_message("system", f"👁️ Зрение [{prov}]\n"))
                self.m.root.after(0, lambda: self.m.chat_win.append_message("bot", f"Аластор: {reply}\n\n"))

        threading.Thread(target=_worker, daemon=True).start()

    # -------------------------------------------------------------------------
    # Clipboard Assistant
    # -------------------------------------------------------------------------
    def explain_clipboard(self):
        self.m.show_speech("Вглядываюсь в твой буфер обмена... Секунду! 📋🎙️", play_audio=not self.m.is_muted)

        def _cb(ok, reply):
            self.m.root.after(0, lambda: self.m.show_speech(reply, play_audio=not self.m.is_muted))
            if self.m.chat_win and tk.Toplevel.winfo_exists(self.m.chat_win.win):
                self.m.root.after(0, lambda: self.m.chat_win.append_message("system", "📋 Анализ буфера обмена:\n"))
                self.m.root.after(0, lambda: self.m.chat_win.append_message("bot", f"Аластор: {reply}\n\n"))

        self.m.clipboard_asst.explain_clipboard(on_finish=_cb)

    def translate_clipboard(self):
        self.m.show_speech("Перевожу частоту вещания на твой текст... 🌐🎙️", play_audio=not self.m.is_muted)

        def _cb(ok, reply):
            self.m.root.after(0, lambda: self.m.show_speech(reply, play_audio=not self.m.is_muted))
            if self.m.chat_win and tk.Toplevel.winfo_exists(self.m.chat_win.win):
                self.m.root.after(0, lambda: self.m.chat_win.append_message("system", "🌐 Перевод текста из буфера:\n"))
                self.m.root.after(0, lambda: self.m.chat_win.append_message("bot", f"Аластор: {reply}\n\n"))

        self.m.clipboard_asst.translate_clipboard(on_finish=_cb)

    # -------------------------------------------------------------------------
    # Media Downloader
    # -------------------------------------------------------------------------
    def download_media(self, audio_only: bool = True, url: str = None):
        target_url = url or self.m.clipboard_asst.get_url()
        if not target_url:
            self.m.show_speech("Скопируй ссылку на YouTube, TikTok или VK в буфер (Ctrl+C), дорогуша! 🔗", play_audio=not self.m.is_muted)
            return

        def _on_done(ok, msg, ddir):
            self.m.root.after(0, lambda: self.m.show_speech(msg, play_audio=not self.m.is_muted))
            if self.m.chat_win and tk.Toplevel.winfo_exists(self.m.chat_win.win):
                self.m.root.after(0, lambda: self.m.chat_win.append_message("system", f"📥 {msg}\nПапка: {ddir}\n\n"))

        started, status_msg = self.m.media_downloader.start_download(target_url, audio_only=audio_only, on_complete=_on_done)
        self.m.show_speech(status_msg, play_audio=not self.m.is_muted)
        if self.m.chat_win and tk.Toplevel.winfo_exists(self.m.chat_win.win):
            self.m.chat_win.append_message("system", f"📥 {status_msg}\n")

    # -------------------------------------------------------------------------
    # Windows Master Volume
    # -------------------------------------------------------------------------
    def adjust_volume(self, delta: int):
        new_vol = self.m.volume_ctrl.set_volume(self.m.volume_ctrl.get_volume() + delta)
        self.m.show_speech(f"Громкость Windows: {new_vol}% 🔊", play_audio=not self.m.is_muted)

    def set_volume(self, level: int):
        new_vol = self.m.volume_ctrl.set_volume(level)
        self.m.show_speech(f"Громкость Windows установлена на {new_vol}% 🔊", play_audio=not self.m.is_muted)

    def toggle_win_mute(self):
        muted = self.m.volume_ctrl.toggle_mute()
        state = "Звук Windows заглушён 🔇" if muted else "Звук Windows включён 🔊"
        self.m.show_speech(state, play_audio=not self.m.is_muted)

    # -------------------------------------------------------------------------
    # Window Platforms Navigation
    # -------------------------------------------------------------------------
    def jump_to_window(self):
        if not WIN32_AVAILABLE:
            self.m.show_speech("Требуется Windows для хождения по окнам 😅", play_audio=False)
            return

        target = self.m.surface_detector.get_foreground_window()
        if not target:
            open_wins = self.m.surface_detector.get_open_windows()
            if open_wins:
                target = open_wins[0]

        if not target:
            self.m.show_speech("Не вижу подходящих открытых окон для прыжка, дорогуша! 🪟", play_audio=not self.m.is_muted)
            return

        self.m.physics_engine.jump_to_window(target)
        self.m.x = self.m.physics_engine.x
        self.m.y = self.m.physics_engine.y
        self.m._apply_pos()

        win_title = target["title"][:25]
        self.m.show_speech(f"Запрыгнул на «{win_title}»! Прогуляюсь по вкладкам! 🪟😈", play_audio=not self.m.is_muted)
        log_info(f"Маскот запрыгнул на окно: hwnd={target['hwnd']}, title={win_title}")

    def jump_to_floor(self):
        ok = self.m.physics_engine.jump_to_floor()
        if ok:
            self.m.show_speech("Спускаюсь обратно на грешную землю! ⬇️😈", play_audio=not self.m.is_muted)
            log_info("Маскот спрыгнул с окна на пол экрана")
        else:
            self.m.show_speech("Я и так уже на панели задач! 📻", play_audio=not self.m.is_muted)

    def toggle_walk_on_windows(self):
        self.m.physics_engine.walk_on_windows_enabled = not self.m.physics_engine.walk_on_windows_enabled
        if not self.m.physics_engine.walk_on_windows_enabled and self.m.physics_engine.target_window_hwnd != 0:
            self.jump_to_floor()
        state = "ВКЛЮЧЕНА (гуляю по окнам и вкладкам) 🪟✓" if self.m.physics_engine.walk_on_windows_enabled else "ВЫКЛЮЧЕНА (хожу только по полу) 🛑"
        self.m.show_speech(f"Хождение по окнам:\n{state}", play_audio=not self.m.is_muted)

    # -------------------------------------------------------------------------
    # Text Input Prompt
    # -------------------------------------------------------------------------
    def prompt_type_text(self):
        text = simpledialog.askstring(
            "Ввод текста — Аластор",
            "Какой текст напечатать в активном окне?\n(У вас будет 2 секунды, чтобы переключить окно)"
        )
        if text:
            self.m.show_speech(f"Печатаю через 2 сек:\n«{text[:30]}»... ⌨️", play_audio=False)

            def _delayed():
                import time
                time.sleep(2.0)
                self.m.input_ctrl.type_text(text)

            threading.Thread(target=_delayed, daemon=True).start()

    # -------------------------------------------------------------------------
    # Desktop Icons Management
    # -------------------------------------------------------------------------
    def shuffle_desktop(self):
        if not WIN32_AVAILABLE or not self.m.desktop_mover:
            self.m.show_speech("Требуется pywin32 😅")
            return
        ok = self.m.desktop_mover.shuffle_icons()
        self.m.show_speech("Перемешал значки! 🎲😈" if ok else "Не удалось перемешать 😓")

    def scatter_desktop(self):
        if not WIN32_AVAILABLE or not self.m.desktop_mover:
            self.m.show_speech("Требуется pywin32 😅")
            return
        ok = self.m.desktop_mover.scatter_icons()
        self.m.show_speech("Разбросал значки! 💥😈" if ok else "Не удалось разбросать 😓")

    def sort_desktop(self):
        if not WIN32_AVAILABLE or not self.m.desktop_mover:
            self.m.show_speech("Требуется pywin32 😅")
            return
        ok = self.m.desktop_mover.sort_icons_grid()
        self.m.show_speech("Выровнял по сетке! 🧹✨" if ok else "Не удалось выровнять 😓")

    def move_one_icon(self):
        if not WIN32_AVAILABLE or not self.m.desktop_mover:
            self.m.show_speech("Требуется pywin32 😅")
            return
        icons = self.m.desktop_mover.get_icon_list()
        if not icons:
            self.m.show_speech("Значков на рабочем столе не найдено 🤔")
            return
        idx, name = random.choice(icons)
        ok = self.m.desktop_mover.move_one_icon(idx)
        label = name[:20] + ("…" if len(name) > 20 else "")
        self.m.show_speech(f"Сдвинул '{label}' 🖱️✨" if ok else "Не удалось сдвинуть значок 😓")

    def trash_icon(self):
        if not WIN32_AVAILABLE or not self.m.desktop_mover:
            self.m.show_speech("Требуется pywin32 😅")
            return
        icons = self.m.desktop_mover.get_icon_list()
        if not icons:
            self.m.show_speech("Значков на рабочем столе не найдено 🤔")
            return
        menu = tk.Menu(self.m.root, tearoff=0,
                       bg="#181825", fg="#cdd6f4",
                       activebackground="#313244",
                       activeforeground="#cba6f7",
                       font=("Segoe UI", 10))
        for idx, name in icons:
            lbl = f"🗑️ {name[:24]}" + ("…" if len(name) > 24 else "")

            def _make_cmd(i=idx, n=name):
                def _do():
                    ok, msg = self.m.desktop_mover.trash_icon_at_index(i)
                    if ok:
                        self.m.show_speech(f"Отправил '{msg}'\nв корзину! 🗑️😈")
                    else:
                        self.m.show_speech(f"Не удалось удалить:\n{msg} 😓")
                return _do

            menu.add_command(label=lbl, command=_make_cmd())
        menu.add_separator()
        menu.add_command(label="Отмена", command=lambda: None)
        bx = int(self.m.x) + 64
        by = int(self.m.y)
        try:
            menu.tk_popup(bx, by)
        finally:
            menu.grab_release()

    # -------------------------------------------------------------------------
    # Windows Interactive Actions
    # -------------------------------------------------------------------------
    def troll_minimize(self):
        if not WIN32_AVAILABLE:
            self.m.show_speech("Требуется pywin32 😅")
            return
        ok = self.m.win_dragger.minimize_foreground(exclude=self.m._own_hwnd())
        self.m.show_speech("Свернул окно! Отдыхай! 😴" if ok else "Нет окон для сворачивания 🤔")

    def close_foreground(self):
        if not WIN32_AVAILABLE:
            self.m.show_speech("Требуется pywin32 😅")
            return
        ok = self.m.win_dragger.close_foreground(exclude=self.m._own_hwnd())
        self.m.show_speech("Закрыл активное окно! 😈" if ok else "Нет активного окна 🤔")

    def _wait_click_then(self, action_fn, hint_msg: str):
        if not WIN32_AVAILABLE:
            self.m.show_speech("Требуется pywin32 😅")
            return
        self.m.show_speech(hint_msg)
        overlay = tk.Toplevel(self.m.root)
        overlay.attributes("-fullscreen", True)
        overlay.attributes("-alpha", 0.01)
        overlay.attributes("-topmost", True)
        overlay.config(bg="#000000", cursor="crosshair")

        def _on_overlay_click(ev):
            sx = ev.x_root
            sy = ev.y_root
            overlay.destroy()
            self.m.root.after(50, lambda: action_fn(sx, sy))

        def _on_overlay_cancel(ev):
            overlay.destroy()
            self.m.show_speech("Отменено 🤷")

        overlay.bind("<ButtonPress-1>", _on_overlay_click)
        overlay.bind("<ButtonPress-3>", _on_overlay_cancel)
        overlay.bind("<Escape>",        _on_overlay_cancel)

    def minimize_under_cursor(self):
        self._wait_click_then(
            lambda sx, sy: self.m.show_speech("Свернул! 💤" if self.m.win_dragger.minimize_at(sx, sy) else "Не вышло 😕"),
            "Кликните на окно,\nчтобы свернуть его 💤"
        )

    def close_under_cursor(self):
        self._wait_click_then(
            lambda sx, sy: self.m.show_speech("Закрыл окно! ✖️" if self.m.win_dragger.close_at(sx, sy) else "Не вышло 😕"),
            "Кликните на окно,\nчтобы закрыть его ✖️"
        )

    def maximize_under_cursor(self):
        self._wait_click_then(
            lambda sx, sy: self.m.show_speech("Развернул! 🪟" if self.m.win_dragger.maximize_restore_at(sx, sy) else "Не вышло 😕"),
            "Кликните на окно,\nчтобы развернуть 🪟"
        )

    def start_window_drag(self):
        if not WIN32_AVAILABLE:
            self.m.show_speech("Требуется pywin32")
            return
        self.m.show_speech("Укажите окно,\nкоторое нужно переместить 🪟")
        self.m.canvas.bind("<ButtonPress-1>", self._grab_and_drag)

    def _grab_and_drag(self, e):
        self.m.canvas.bind("<ButtonPress-1>", self.m.on_press)
        sx = self.m.root.winfo_rootx() + e.x
        sy = self.m.root.winfo_rooty() + e.y
        ok = self.m.win_dragger.grab_window_at(sx, sy)
        if ok:
            self.m.dragging_window = True
            self.m.dragging   = True
            self.m.drag_off_x = e.x
            self.m.drag_off_y = e.y
            self.m.show_speech("Поймал! Перетаскивайте 💪")
        else:
            self.m.show_speech("Окно не найдено 😬")
            self.m.dragging = False
