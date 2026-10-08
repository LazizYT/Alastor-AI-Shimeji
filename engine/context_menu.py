import random
import tkinter as tk
from core.config import WIN32_AVAILABLE
from core.constants import SPEECHES


class MascotContextMenu:
    """
    Constructs and renders the dark-themed right-click context menu for Alastor.
    Organizes actions into clean cascading categories:
    - Quick Launch
    - Windows Actions (Trolling, dragging, walking on tabs)
    - Desktop Actions (Icons management)
    - Mouse & Keyboard Automation
    - Clipboard Assistant & Media Downloads
    - Windows Master Volume
    - Vision, Voice & System Logs
    """

    def __init__(self, mascot):
        self.m = mascot

    def show(self, event):
        menu = tk.Menu(self.m.root, tearoff=0,
                       bg="#181825", fg="#cdd6f4",
                       activebackground="#313244",
                       activeforeground="#cba6f7",
                       font=("Segoe UI", 10),
                       bd=0)

        menu.add_command(label="📻 Открыть чат с Аластором", command=self.m.open_chat,
                         font=("Segoe UI", 10, "bold"))
        menu.add_separator()

        # 1. Quick Launch
        launch_menu = tk.Menu(menu, tearoff=0,
                              bg="#181825", fg="#cdd6f4",
                              activebackground="#313244",
                              activeforeground="#cba6f7",
                              font=("Segoe UI", 10))
        gest_label = "🎩 Режим: Жесты и мышь [ВКЛ]" if getattr(self.m, 'gesture_launch_mode', False) else "⚡ Режим: Прямой запуск"
        launch_menu.add_command(label=gest_label, command=self.m.toggle_gesture_launch_mode)
        launch_menu.add_separator()
        launch_menu.add_command(label="🎮 Steam",       command=lambda: self.m.app_launcher.launch_quick("steam"))
        launch_menu.add_command(label="💻 VS Code",     command=lambda: self.m.app_launcher.launch_quick("vscode"))
        launch_menu.add_command(label="🌐 Браузер",    command=lambda: self.m.app_launcher.launch_quick("browser"))
        launch_menu.add_command(label="💬 Telegram",    command=lambda: self.m.app_launcher.launch_quick("telegram"))
        launch_menu.add_command(label="🎙️ Discord",     command=lambda: self.m.app_launcher.launch_quick("discord"))
        launch_menu.add_command(label="🔴 OBS Studio",   command=lambda: self.m.app_launcher.launch_quick("obs"))
        launch_menu.add_command(label="🧮 Калькулятор", command=lambda: self.m.app_launcher.launch_quick("calculator"))
        launch_menu.add_command(label="📝 Блокнот",     command=lambda: self.m.app_launcher.launch_quick("notepad"))
        launch_menu.add_command(label="📁 Проводник",   command=lambda: self.m.app_launcher.launch_quick("explorer"))
        launch_menu.add_separator()
        launch_menu.add_command(label="⚙️ Настроить команды (apps_config.json)", command=self.m.app_launcher.open_apps_config_file)
        menu.add_cascade(label="🚀 Быстрый запуск ▸", menu=launch_menu)
        menu.add_separator()

        # 2. Windows Management & Platforms
        if WIN32_AVAILABLE:
            win_lbl = ("🪟 Окна Windows [АВТО ВКЛ] ▸" if self.m.autonomy_mgr.auto_win_enabled
                       else "🪟 Окна Windows ▸")
            win_menu = tk.Menu(menu, tearoff=0,
                               bg="#181825", fg="#cdd6f4",
                               activebackground="#313244",
                               activeforeground="#cba6f7",
                               font=("Segoe UI", 10))
            win_menu.add_command(label="🪟 Запрыгнуть на активное окно",   command=self.m.actions.jump_to_window)
            win_menu.add_command(label="⬇️ Спуститься на рабочий стол",    command=self.m.actions.jump_to_floor)
            walk_win_lbl = ("👣 Ходить по окнам [ВКЛ] ✓" if self.m.physics_engine.walk_on_windows_enabled
                            else "👣 Ходить по окнам [ВЫКЛ]")
            win_menu.add_command(label=walk_win_lbl, command=self.m.actions.toggle_walk_on_windows)
            win_menu.add_separator()
            win_menu.add_command(label="📉 Свернуть активное окно",        command=self.m.actions.troll_minimize)
            win_menu.add_command(label="✖️ Закрыть активное окно",           command=self.m.actions.close_foreground)
            win_menu.add_separator()
            win_menu.add_command(label="📉 Свернуть окно (курсором)",     command=self.m.actions.minimize_under_cursor)
            win_menu.add_command(label="✖️ Закрыть окно (курсором)",        command=self.m.actions.close_under_cursor)
            win_menu.add_command(label="⬜ Развернуть/Восстановить",       command=self.m.actions.maximize_under_cursor)
            win_menu.add_command(label="🪟 Перетащить окно",              command=self.m.actions.start_window_drag)
            win_menu.add_separator()
            auto_win_lbl = ("😈 Автономия окон: ВКЛ  → выключить" if self.m.autonomy_mgr.auto_win_enabled
                            else "😇 Автономия окон: ВЫКЛ → включить")
            win_menu.add_command(label=auto_win_lbl, command=self.m.autonomy_mgr.toggle_auto_win)
            menu.add_cascade(label=win_lbl, menu=win_menu)

            # 3. Desktop Icons Management
            desk_lbl = ("🖥️ Рабочий стол [АВТО ВКЛ] ▸" if self.m.autonomy_mgr.auto_desk_enabled
                        else "🖥️ Рабочий стол ▸")
            desk_menu = tk.Menu(menu, tearoff=0,
                                bg="#181825", fg="#cdd6f4",
                                activebackground="#313244",
                                activeforeground="#cba6f7",
                                font=("Segoe UI", 10))
            desk_menu.add_command(label="🎲 Перемешать все значки",       command=self.m.actions.shuffle_desktop)
            desk_menu.add_command(label="💥 Разбросать значки",           command=self.m.actions.scatter_desktop)
            desk_menu.add_command(label="🧹 Выровнять по сетке",          command=self.m.actions.sort_desktop)
            desk_menu.add_command(label="🖱️ Сдвинуть случайный значок",    command=self.m.actions.move_one_icon)
            desk_menu.add_command(label="🗑️ Отправить значок в корзину",   command=self.m.actions.trash_icon)
            desk_menu.add_separator()
            auto_desk_lbl = ("😈 Автономия стола: ВКЛ  → выключить" if self.m.autonomy_mgr.auto_desk_enabled
                             else "😇 Автономия стола: ВЫКЛ → включить")
            desk_menu.add_command(label=auto_desk_lbl, command=self.m.autonomy_mgr.toggle_auto_desk)
            menu.add_cascade(label=desk_lbl, menu=desk_menu)
        else:
            menu.add_command(label="🪟 Действия с окнами (нужен pywin32)", state=tk.DISABLED)
            menu.add_command(label="🖥️ Рабочий стол (нужен pywin32)",     state=tk.DISABLED)

        # 4. Mouse and Keyboard
        input_menu = tk.Menu(menu, tearoff=0,
                             bg="#181825", fg="#cdd6f4",
                             activebackground="#313244",
                             activeforeground="#cba6f7",
                             font=("Segoe UI", 10))
        input_menu.add_command(label="🖱️ Кликнуть левой кнопкой",    command=self.m.input_ctrl.click)
        input_menu.add_command(label="🖱️ Двойной клик",              command=self.m.input_ctrl.double_click)
        input_menu.add_command(label="🖱️ Кликнуть правой кнопкой",   command=self.m.input_ctrl.right_click)
        input_menu.add_separator()
        input_menu.add_command(label="📜 Прокрутить вниз (Скролл)",  command=lambda: self.m.input_ctrl.scroll(-6))
        input_menu.add_command(label="📜 Прокрутить вверх (Скролл)",  command=lambda: self.m.input_ctrl.scroll(6))
        input_menu.add_separator()
        input_menu.add_command(label="⌨️ Напечатать текст...",        command=self.m.actions.prompt_type_text)
        input_menu.add_command(label="⌨️ Нажать Enter",              command=lambda: self.m.input_ctrl.press_key('enter'))
        input_menu.add_command(label="⌨️ Нажать Пробел",             command=lambda: self.m.input_ctrl.press_key('space'))
        input_menu.add_separator()
        input_menu.add_command(label="📋 Скопировать (Ctrl+C)",      command=lambda: self.m.input_ctrl.hotkey('ctrl', 'c'))
        input_menu.add_command(label="📋 Вставить (Ctrl+V)",         command=lambda: self.m.input_ctrl.hotkey('ctrl', 'v'))
        input_menu.add_command(label="🖥️ Свернуть всё (Win+D)",      command=lambda: self.m.input_ctrl.hotkey('win', 'd'))
        input_menu.add_separator()
        input_menu.add_command(label="😈 Поиграть с курсором",       command=self.m.input_ctrl.playful_wiggle)
        auto_mouse_lbl = ("😈 Автономия мыши: ВКЛ  → выключить" if self.m.autonomy_mgr.auto_mouse_enabled
                          else "😇 Автономия мыши: ВЫКЛ → включить")
        input_menu.add_command(label=auto_mouse_lbl, command=self.m.autonomy_mgr.toggle_auto_mouse)
        menu.add_cascade(label="🖱️ Мышь и клавиатура ▸", menu=input_menu)

        # 5. Clipboard Assistant & Downloads
        clip_menu = tk.Menu(menu, tearoff=0,
                            bg="#181825", fg="#cdd6f4",
                            activebackground="#313244",
                            activeforeground="#cba6f7",
                            font=("Segoe UI", 10))
        clip_menu.add_command(label="🔍 Объяснить скопированное (ИИ)", command=self.m.actions.explain_clipboard)
        clip_menu.add_command(label="🌐 Перевести скопированное",      command=self.m.actions.translate_clipboard)
        clip_menu.add_separator()
        clip_menu.add_command(label="🎵 Скачать MP3 по ссылке",       command=lambda: self.m.actions.download_media(audio_only=True))
        clip_menu.add_command(label="🎬 Скачать MP4 по ссылке",       command=lambda: self.m.actions.download_media(audio_only=False))
        menu.add_cascade(label="📋 Буфер и Загрузки ▸", menu=clip_menu)

        # 6. Windows Master Volume
        vol_menu = tk.Menu(menu, tearoff=0,
                           bg="#181825", fg="#cdd6f4",
                           activebackground="#313244",
                           activeforeground="#cba6f7",
                           font=("Segoe UI", 10))
        vol_menu.add_command(label="🔊 Громче (+10%)", command=lambda: self.m.actions.adjust_volume(10))
        vol_menu.add_command(label="🔉 Тише (-10%)",  command=lambda: self.m.actions.adjust_volume(-10))
        vol_menu.add_separator()
        vol_menu.add_command(label="🔈 Уровень: 20%",  command=lambda: self.m.actions.set_volume(20))
        vol_menu.add_command(label="🔈 Уровень: 50%",  command=lambda: self.m.actions.set_volume(50))
        vol_menu.add_command(label="🔈 Уровень: 80%",  command=lambda: self.m.actions.set_volume(80))
        vol_menu.add_command(label="🔈 Уровень: 100%", command=lambda: self.m.actions.set_volume(100))
        vol_menu.add_separator()
        vol_menu.add_command(label="🔇 Заглушить Windows", command=self.m.actions.toggle_win_mute)
        menu.add_cascade(label="🔊 Громкость Windows ▸", menu=vol_menu)

        menu.add_separator()

        # 7. Demonic Deals (Focus Mode)
        deal_menu = tk.Menu(menu, tearoff=0, bg="#181825", fg="#cdd6f4",
                            activebackground="#313244", activeforeground="#cba6f7", font=("Segoe UI", 10))
        deal_menu.add_command(label="🤝 Сделка на 25 минут (Помодоро)", command=lambda: self.m.show_speech(self.m.deal_mgr.start_deal(25)))
        deal_menu.add_command(label="🤝 Сделка на 45 минут (Глубокий фокус)", command=lambda: self.m.show_speech(self.m.deal_mgr.start_deal(45)))
        deal_menu.add_command(label="🤝 Сделка на 60 минут (Адский темп)", command=lambda: self.m.show_speech(self.m.deal_mgr.start_deal(60)))
        deal_menu.add_separator()
        deal_menu.add_command(label="⏳ Статус сделки", command=lambda: self.m.show_speech(self.m.deal_mgr.get_status(), play_audio=False))
        deal_menu.add_command(label="❌ Расторгнуть сделку (Сдаться)", command=lambda: self.m.show_speech(self.m.deal_mgr.cancel_deal()))
        menu.add_cascade(label="📜 Сделка с Демоном (Фокус) ▸", menu=deal_menu)

        # 8. Vintage Radio AIMP
        radio_menu = tk.Menu(menu, tearoff=0, bg="#181825", fg="#cdd6f4",
                             activebackground="#313244", activeforeground="#cba6f7", font=("Segoe UI", 10))
        radio_menu.add_command(label="▶️ Включить радио / AIMP", command=lambda: self.m.show_speech(self.m.aimp_ctrl.play()[1]))
        radio_menu.add_command(label="⏸️ Пауза",                 command=lambda: self.m.show_speech(self.m.aimp_ctrl.pause()[1]))
        radio_menu.add_command(label="⏭️ Следующий трек",         command=lambda: self.m.show_speech(self.m.aimp_ctrl.next_track()[1]))
        radio_menu.add_command(label="⏮️ Предыдущий трек",        command=lambda: self.m.show_speech(self.m.aimp_ctrl.prev_track()[1]))
        radio_menu.add_command(label="⏹️ Остановить вещание",     command=lambda: self.m.show_speech(self.m.aimp_ctrl.stop()[1]))
        menu.add_cascade(label="📻 Винтажное Радио AIMP ▸", menu=radio_menu)

        # 9. Workspace Presets
        ws_menu = tk.Menu(menu, tearoff=0, bg="#181825", fg="#cdd6f4",
                          activebackground="#313244", activeforeground="#cba6f7", font=("Segoe UI", 10))
        ws_menu.add_command(label="💻 Рабочий сетап (Код + Браузер 50/50)", command=lambda: self.m.workspace_presets.apply_preset("рабочий"))
        ws_menu.add_command(label="🎮 Игровой сетап (Steam + Discord)",     command=lambda: self.m.workspace_presets.apply_preset("игры"))
        ws_menu.add_command(label="⚖️ Расставить окна по бокам (50/50)",     command=lambda: self.m.show_speech(self.m.workspace_presets.apply_preset("по бокам")[1]))
        ws_menu.add_command(label="🧹 Чистый стол (Свернуть всё)",           command=lambda: self.m.workspace_presets.apply_preset("чисто"))
        menu.add_cascade(label="🚀 Рабочие сетапы ▸", menu=ws_menu)

        # 10. Smart Assistant & Timers
        asst_menu = tk.Menu(menu, tearoff=0, bg="#181825", fg="#cdd6f4",
                            activebackground="#313244", activeforeground="#cba6f7", font=("Segoe UI", 10))
        asst_menu.add_command(label="🛠️ Объяснить ошибку на экране", command=self.m.context_asst.explain_active_error)
        asst_menu.add_command(label="📰 Кратко пересказать экран",   command=self.m.context_asst.summarize_active_screen)
        asst_menu.add_separator()
        asst_menu.add_command(label="⏰ Таймер на 5 минут",           command=lambda: self.m.show_speech(self.m.timer_mgr.add_timer(300, "Таймер 5 минут")))
        asst_menu.add_command(label="⏰ Таймер на 15 минут",          command=lambda: self.m.show_speech(self.m.timer_mgr.add_timer(900, "Таймер 15 минут")))
        asst_menu.add_command(label="⏰ Список активных таймеров",    command=lambda: self.m.show_speech(self.m.timer_mgr.get_active_summary(), play_audio=False))
        menu.add_cascade(label="🧠 Умный помощник и Таймеры ▸", menu=asst_menu)

        menu.add_separator()
        follow_cursor_lbl = ("👁️ Следовать за курсором [ВКЛ] ✓" if self.m.physics_engine.follow_cursor_enabled
                             else "👁️ Следовать за курсором [ВЫКЛ]")
        menu.add_command(label=follow_cursor_lbl, command=self.m._toggle_follow_cursor)
        menu.add_separator()
        menu.add_command(label="👀 Что ты видишь? (Зрение ИИ)", command=self.m.actions.look_at_screen)
        auto_cap_lbl = ("👁️ Автозахват экрана (2-5 мин) [ВКЛ] ✓" if getattr(self.m, 'auto_capture_enabled', True)
                        else "👁️ Автозахват экрана (2-5 мин) [ВЫКЛ]")
        menu.add_command(label=auto_cap_lbl, command=self.m.toggle_auto_capture)
        mute_lbl = ("🔇 Заглушить голос (Mute)" if not self.m.is_muted else "🔊 Включить голос (Unmute)")
        menu.add_command(label=mute_lbl, command=self.m.toggle_mute)
        wake_word_lbl = ("🎙️ Триггер «Аластор» (F9) [ВКЛ] ✓" if getattr(self.m, 'wake_word_mode', False)
                         else "🎙️ Триггер «Аластор» (F9) [ВЫКЛ]")
        menu.add_command(label=wake_word_lbl, command=self.m.toggle_wake_word_mode)
        menu.add_command(label="🎙️ Настройки голоса и радио...", command=self.m.open_voice_settings)
        menu.add_command(label="📜 Просмотр логов", command=self.m.open_log_viewer)
        menu.add_command(label="🧠 Досье и память Аластора", command=self.m.show_memory_dossier)
        menu.add_command(label="👁️ Свернуть в трей (Панель задач)", command=self.m.toggle_visibility)
        menu.add_separator()
        menu.add_command(label="💬 Сказать фразу", command=lambda: self.m.show_speech(random.choice(SPEECHES), play_audio=True))
        menu.add_separator()
        menu.add_command(label="✕ Закрыть маскота", command=self.m.on_exit,
                         foreground="#f38ba8", activeforeground="#f38ba8")

        try:
            rx = self.m.root.winfo_rootx() + event.x
            ry = self.m.root.winfo_rooty() + event.y
            menu.tk_popup(rx, ry)
        finally:
            menu.grab_release()
