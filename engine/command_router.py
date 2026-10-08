import re


from engine.action_chain import ActionChainPlanner


class CommandRouter:
    """
    Interprets natural language voice transcriptions and chat inputs,
    routing them to system automation actions, UI controls, audio levels,
    window navigation, and media downloads.
    """

    def __init__(self, mascot):
        self.m = mascot
        self.chain_planner = ActionChainPlanner(mascot)

    def route_command(self, text: str) -> tuple[bool, str]:
        # Strip wake-word prefix if user said "Аластор, ..."
        low = text.lower().strip()
        wake_prefix_pat = r'^(?:ал[аоеи]ст[оеа]р[а-я]*|а\s+ла\s*стор|алистар|аластер|алистер|alastor[a-z]*|alaster[a-z]*)[,\s:\-]+'
        low = re.sub(wake_prefix_pat, '', low).strip()
        cleaned_text = re.sub(wake_prefix_pat, '', text, flags=re.IGNORECASE).strip()

        # 0. Multi-step Chained Actions (e.g. "открой браузер, зайди в ютуб и поищи ...")
        if self.chain_planner and self.chain_planner.is_chained_command(cleaned_text):
            handled, reply = self.chain_planner.execute_chain(cleaned_text)
            if handled:
                return True, reply

        # Wake word mode toggles
        if any(w in low for w in ["выключи триггер", "отключи триггер", "выключи режим триггер", "выключи постоянное слушание", "отключи режим аластор"]):
            if hasattr(self.m, 'set_wake_word_mode'):
                self.m.set_wake_word_mode(False)
            return True, "Фоновый режим триггер-слова «Аластор» отключён! Теперь я слушаю только по кнопке или клику! 🔇"

        if any(w in low for w in ["включи триггер", "включи режим триггер", "слушай постоянно", "режим триггер", "включи режим аластор", "слушай по слову аластор"]):
            if hasattr(self.m, 'set_wake_word_mode'):
                self.m.set_wake_word_mode(True)
            return True, "Режим триггер-слова «Аластор» активирован! Теперь просто назовите моё имя — и я тут же отзовусь в эфире! 🎙️📻✨"

        # Window Controls (Minimization, Closing, Maximizing)
        if any(w in low for w in [
            "сверни окно", "свернуть окно", "сверни активное окно", "свернуть активное окно",
            "сверни это окно", "свернуть это окно", "сверни приложение", "свернуть приложение",
            "минимизируй окно", "минимизировать окно", "минимизируй", "минимизировать",
            "спрячь окно", "спрятать окно", "сверни его", "свернуть его"
        ]) or (low in ["сверни", "свернуть"]):
            ok = self.m.troll_minimize()
            return True, "Свернул окно отдыхать! 📉" if ok else "Нет активных окон для сворачивания! 🤔"

        if any(w in low for w in [
            "закрой окно", "закрыть окно", "закрой активное окно", "закрыть активное окно",
            "закрой это окно", "закрыть это окно", "закрой текущее окно", "закрыть текущее окно",
            "закрой эту программу", "закрыть эту программу", "закрой программу", "закрыть программу",
            "закрой приложение", "закрыть приложение", "закрой его", "закрыть его"
        ]) or (low in ["закрой", "закрыть"]):
            ok = self.m.action_close_foreground()
            return True, "Закрыл активное окно! Шоу окончено! ✖️" if ok else "Нет окна для закрытия! 🤔"

        if any(w in low for w in [
            "разверни окно", "развернуть окно", "разверни активное окно", "развернуть активное окно",
            "на весь экран", "окно на весь экран", "полный экран", "на полный экран",
            "разверни приложение", "развернуть приложение", "разверни его", "развернуть его"
        ]) or (low in ["разверни", "развернуть"]):
            if hasattr(self.m, 'win_dragger') and self.m.win_dragger:
                ok = self.m.win_dragger.toggle_maximize_foreground(exclude=self.m._own_hwnd())
                return True, "Развернул окно на весь экран! 🪟🔍" if ok else "Нет окна для разворачивания!"


        # Gesture launch mode toggles (Disable MUST precede Enable to avoid substring collision)
        if any(w in low for w in ["выключи режим жестов", "выключи жесты", "отключи жесты", "прямой запуск", "открывай напрямую", "обычный запуск", "быстрый запуск"]):
            if hasattr(self.m, 'set_gesture_launch_mode'):
                self.m.set_gesture_launch_mode(False)
            else:
                self.m.gesture_launch_mode = False
            return True, "Режим прямого запуска активирован! Запускаю программы мгновенно через радиоволны! ⚡"

        if any(w in low for w in ["включи режим жестов", "включи жесты", "открывай мышкой", "запуск мышью", "запуск жестами", "режим жестов"]):
            if hasattr(self.m, 'set_gesture_launch_mode'):
                self.m.set_gesture_launch_mode(True)
            else:
                self.m.gesture_launch_mode = True
            return True, "Режим жестов и мыши активирован! Теперь я буду лично наводить курсор и жестикулировать при открытии программ! 🎩🖱️✨"

        # Auto-capture mode toggles (Disable MUST precede Enable to avoid substring collision)
        if any(w in low for w in [
            "выключи автозахват", "отключи автозахват", "выключи автозрение", "отключи автозрение",
            "выключи автоматическое зрение", "отключи автоматическое зрение", "автозахват выключи",
            "автозрение выключи", "выключи авто захват", "отключи авто захват", "не смотри на экран сам"
        ]):
            if hasattr(self.m, 'set_auto_capture'):
                self.m.set_auto_capture(False)
            return True, "Автозахват экрана отключён! 🙈 Буду смотреть на экран только по вашей прямой просьбе!"

        if any(w in low for w in [
            "включи автозахват", "включи автозрение", "включи автоматическое зрение", "автозахват включи",
            "автозрение включи", "включи авто захват", "автоматический захват", "смотри на экран сам",
            "автоматически смотри на экран", "авто захват включи"
        ]):
            if hasattr(self.m, 'set_auto_capture'):
                self.m.set_auto_capture(True)
            return True, "Автозахват экрана активирован! 👁️📻 Буду поглядывать на экран каждые 2-5 минут и комментировать!"

        # 1. Mouse Clicks
        if any(w in low for w in ["двойной клик", "кликни дважды", "два клика"]):
            self.m.input_ctrl.double_click()
            return True, "Двойной щелчок выполнен! 🖱️"

        if any(w in low for w in ["правый клик", "кликни правой", "нажми правую кнопку"]):
            self.m.input_ctrl.right_click()
            return True, "Кликнул правой кнопкой мыши! 🖱️"

        if any(w in low for w in ["кликни", "клик мыши", "нажми мышь", "левый клик", "кликни сюда"]):
            self.m.input_ctrl.click()
            return True, "Клик выполнен! 🖱️"

        # 2. Scrolling
        if any(w in low for w in ["прокрути вниз", "скролл вниз", "листай вниз"]):
            self.m.input_ctrl.scroll(-6)
            return True, "Прокручиваю вниз! 📜"

        if any(w in low for w in ["прокрути вверх", "скролл вверх", "листай вверх"]):
            self.m.input_ctrl.scroll(6)
            return True, "Прокручиваю вверх! 📜"

        # 3. Typing
        type_m = re.search(r'(?:напечатай|напиши|введи|текст)\s+(.+)', text, re.IGNORECASE)
        if type_m:
            to_type = type_m.group(1).strip()
            if to_type:
                self.m.input_ctrl.type_text(to_type)
                return True, f"Напечатал в активном окне: «{to_type[:30]}»! ⌨️"

        # 4. Keys
        if any(w in low for w in ["нажми enter", "нажми ввод", "нажми энтер", "клавиша enter", "жми enter"]):
            self.m.input_ctrl.press_key('enter')
            return True, "Клавиша Enter нажата! ⌨️"

        if any(w in low for w in ["нажми пробел", "клавиша пробел"]):
            self.m.input_ctrl.press_key('space')
            return True, "Пробел нажат! ⌨️"

        if any(w in low for w in ["нажми esc", "нажми эскейп", "нажми отмена"]):
            self.m.input_ctrl.press_key('esc')
            return True, "Клавиша Escape нажата! ⌨️"

        if any(w in low for w in ["нажми backspace", "сотри", "стереть"]):
            self.m.input_ctrl.press_key('backspace')
            return True, "Символ удалён! ⌨️"

        # 5. Hotkeys
        if any(w in low for w in ["скопируй", "копировать", "нажми ctrl c", "ctrl c"]):
            self.m.input_ctrl.hotkey('ctrl', 'c')
            return True, "Скопировал в буфер обмена! 📋"

        if any(w in low for w in ["вставь", "вставить", "нажми ctrl v", "ctrl v"]):
            self.m.input_ctrl.hotkey('ctrl', 'v')
            return True, "Вставил из буфера обмена! 📋"

        if any(w in low for w in ["выдели всё", "выделить всё", "ctrl a"]):
            self.m.input_ctrl.hotkey('ctrl', 'a')
            return True, "Выделил всё! 📋"

        if any(w in low for w in ["сверни все окна", "покажи рабочий стол"]):
            self.m.input_ctrl.hotkey('win', 'd')
            return True, "Свернул все окна на рабочий стол! 🖥️"

        # 6. Cursor tricks
        if any(w in low for w in ["поиграй с мышкой", "подвигай мышь", "потряси курсор", "покрути курсор"]):
            self.m.input_ctrl.playful_wiggle()
            return True, "Ха-ха! Твоя мышь танцует под звуки радио! 😈"

        if any(w in low for w in ["курсор в центр", "мышь в центр", "перемести курсор в центр"]):
            self.m.input_ctrl.move_to_center()
            return True, "Курсор перемещён в центр экрана! 🎯"

        # 7. Tray hide
        if any(w in low for w in ["скройся", "спрячься в трей", "уйди в трей", "исчезни"]):
            self.m.toggle_visibility()
            return True, "Ухожу в тень радиоволн! Ищи меня в трее! 📻"

        # 8. Mute / Unmute
        if any(w in low for w in ["замолчи", "тихо", "без звука", "выключи звук", "заглуши", "мут", "mute"]):
            self.m.set_mute(True)
            return True, "Трансляция заглушена! (Mute активирован) 🔇"

        if any(w in low for w in ["включи звук", "звук включи", "говори", "размут", "размуть", "unmute"]):
            self.m.set_mute(False)
            return True, "Звук включён! Радио-эфир снова на связи! 🔊"

        # 9. Vision & Multimodal Screen Analysis
        vision_triggers = [
            "смотри на мой экран", "посмотри на мой экран", "глянь на мой экран", "взгляни на мой экран",
            "смотри в мой экран", "посмотри в мой экран", "смотри на экран", "посмотри на экран",
            "глянь на экран", "взгляни на экран", "что ты видишь", "что ты видишь на экране",
            "что на экране", "что происходит на экране", "что сейчас на экране", "опиши экран",
            "опиши мой экран", "посмотри вокруг", "что видишь", "проанализируй экран",
            "активируй зрение", "включи зрение", "покажи зрение", "включи глаза", "смотри в экран", "посмотри в экран"
        ]
        is_vision_cmd = (
            any(w in low for w in vision_triggers)
            or bool(re.search(r'\b(?:смотри|посмотри|глянь|взгляни|опиши|проанализируй|проверь|что)\b.*?\b(?:экран[а-я]*|дисплей[а-я]*|монитор[а-я]*)\b', low))
        )
        if is_vision_cmd:
            self.m.action_look_at_screen(user_prompt=cleaned_text)
            return True, ""

        # 10. Windows System Volume
        vol_set_m = re.search(r'(?:громкость|звук)(?:\s+на|\s+до)?\s+(\d+)', low)
        if vol_set_m:
            target_vol = int(vol_set_m.group(1))
            new_v = self.m.volume_ctrl.set_volume(target_vol)
            return True, f"Громкость Windows установлена на {new_v}% 🔊"

        if any(w in low for w in ["потише", "тише", "убавь звук", "убавь громкость", "сделай тише", "сделай потише"]):
            new_v = self.m.volume_ctrl.set_volume(self.m.volume_ctrl.get_volume() - 10)
            return True, f"Убавил громкость Windows до {new_v}% 🔉"

        if any(w in low for w in ["погромче", "громче", "прибавь звук", "прибавь громкость", "сделай громче", "сделай погромче"]):
            new_v = self.m.volume_ctrl.set_volume(self.m.volume_ctrl.get_volume() + 10)
            return True, f"Прибавил громкость Windows до {new_v}% 🔊"

        if any(w in low for w in ["заглуши винду", "выключи звук виндовс", "выключи звук в винде", "мут винды", "заглуши компьютер"]):
            self.m.volume_ctrl.mute()
            return True, "Звук Windows заглушён! 🔇"

        if any(w in low for w in ["включи звук виндовс", "включи звук в винде", "размут винды"]):
            self.m.volume_ctrl.unmute()
            return True, "Звук Windows снова включён! 🔊"

        # Audio Ducking control
        if any(w in low for w in ["включи приглушение", "включи дакинг", "включи автоприглушение"]):
            if hasattr(self.m, 'volume_ctrl'):
                self.m.volume_ctrl.ducking_enabled = True
                return True, "Авто-приглушение музыки (Audio Ducking) включено! 🔉📻"

        if any(w in low for w in ["выключи приглушение", "выключи дакинг", "выключи автоприглушение"]):
            if hasattr(self.m, 'volume_ctrl'):
                self.m.volume_ctrl.ducking_enabled = False
                return True, "Авто-приглушение музыки отключено! 🔊"

        if any(w in low for w in ["приглуши музыку", "приглуши звук", "сделай музыку потише", "сделай музыку тише"]):
            if hasattr(self.m, 'volume_ctrl'):
                self.m.volume_ctrl.start_ducking(15)
                return True, "Приглушил музыку до 15%! Скажите «верни громкость» или дождитесь окончания реплики! 🔉"

        if any(w in low for w in ["верни громкость", "верни звук", "сними приглушение"]):
            if hasattr(self.m, 'volume_ctrl'):
                self.m.volume_ctrl.stop_ducking()
                return True, f"Восстановил громкость до {self.m.volume_ctrl.get_volume()}%! 🔊"

        # 11. Clipboard Assistant
        if any(w in low for w in ["объясни скопированное", "объясни буфер", "что это за код", "объясни код", "разбери буфер", "что в буфере"]):
            self.m.action_explain_clipboard()
            return True, "Изучаю твой буфер обмена... 📋🎙️"

        if any(w in low for w in ["переведи буфер", "переведи скопированное", "переведи текст из буфера"]):
            self.m.action_translate_clipboard()
            return True, "Перевожу текст из буфера обмена... 🌐🎙️"

        # 12. Media Downloader
        if any(w in low for w in ["скачай музыку", "скачай песню", "скачай трек", "скачай аудио", "скачай mp3"]):
            url_match = self.m.media_downloader.extract_url(text)
            self.m.action_download_media(audio_only=True, url=url_match)
            return True, "Запускаю скачивание аудиодорожки! 🎵📥"

        if any(w in low for w in ["скачай видео", "скачай ролик", "скачай клип", "скачай mp4"]):
            url_match = self.m.media_downloader.extract_url(text)
            self.m.action_download_media(audio_only=False, url=url_match)
            return True, "Запускаю скачивание видеоролика! 🎬📥"

        if "скачай" in low and ("http://" in low or "https://" in low):
            url_match = self.m.media_downloader.extract_url(text)
            self.m.action_download_media(audio_only=True, url=url_match)
            return True, "Запускаю скачивание по найденной ссылке! 📥✨"

        # 13. Window Platforms Navigation
        if any(w in low for w in ["запрыгни на окно", "прыгай на окно", "прыгни на окно", "встань на окно", "иди на вкладки", "на окно", "залезь на окно", "запрыгнуть на окно"]):
            self.m.action_jump_to_window()
            return True, "Запрыгиваю на верх активного окна! 🪟✨"

        if any(w in low for w in ["спустись на пол", "прыгай вниз", "слезь с окна", "спрыгни с окна", "на пол", "спустись вниз", "слезай"]):
            self.m.action_jump_to_floor()
            return True, "Спрыгиваю на рабочий стол! ⬇️😈"

        if any(w in low for w in ["не ходи по окнам", "выключи хождение по окнам", "перестань ходить по окнам"]):
            self.m.walk_on_windows_enabled = False
            self.m.action_jump_to_floor()
            return True, "Хождение по окнам выключено! 🛑"

        if any(w in low for w in ["ходи по окнам", "включи хождение по окнам"]):
            self.m.walk_on_windows_enabled = True
            return True, "Хождение по окнам и вкладкам включено! 🪟✓"

        # 14. Memory Dossier query
        if any(w in low for w in ["что ты помнишь", "что помнишь обо мне", "мое досье", "моё досье"]):
            if hasattr(self.m, 'memory') and self.m.memory:
                return True, self.m.memory.get_readable_summary()

        # 15. Demonic Deals (Focus & Anti-procrastination)
        if any(w in low for w in ["сделк", "договор", "фокус режим", "режим фокуса"]):
            if any(w in low for w in ["разорви", "отмени", "расторгни", "сдаюсь", "я сдаюсь", "стоп"]):
                if hasattr(self.m, 'deal_mgr'):
                    return True, self.m.deal_mgr.cancel_deal()
            elif any(w in low for w in ["статус", "что со сделк", "сколько осталось", "как там сделк", "проверь сделк"]):
                if hasattr(self.m, 'deal_mgr'):
                    return True, self.m.deal_mgr.get_status()
            deal_m = re.search(r'(?:сделк[а-я]*|договор[а-я]*|режим фокуса)\s+(?:на\s+)?(\d+)\s*(?:минут[а-я]*)?(?:\s+(?:по\s+)?(.+))?', low)
            if deal_m and hasattr(self.m, 'deal_mgr'):
                mins = int(deal_m.group(1))
                task = deal_m.group(2) or ""
                return True, self.m.deal_mgr.start_deal(mins, task)
            elif any(w in low for w in ["заключим", "давай", "начнем", "начни"]):
                if hasattr(self.m, 'deal_mgr'):
                    return True, self.m.deal_mgr.start_deal(30)

        # 16. Universal Music & Vintage Radio (AIMP / Spotify / YouTube)
        if any(w in low for w in ["пауза в музыке", "поставь на паузу", "пауза", "останови музыку", "стоп музыка", "выключи музыку", "выруби музыку"]):
            if hasattr(self.m, 'aimp_ctrl'):
                ok, reply = self.m.aimp_ctrl.pause()
                return True, reply

        play_triggers = [
            "включи радио", "запусти радио", "включи музыку", "музыку в эфир", "запусти аимп", "включи аимп",
            "играй музыку", "продолжи музыку", "возобнови музыку", "плей", "играй", "поставь музыку",
            "поставь песню", "послушать песни", "послушать песню", "послушать музыку", "хочу послушать",
            "вруби музыку", "вруби песню", "вруби трек", "включи трек", "поставь трек", "включи песню",
            "сыграй что-нибудь", "поставь что-нибудь"
        ]
        is_play_request = any(w in low for w in play_triggers) or (
            ("хочу" in low or "давай" in low or "поставь" in low or "включи" in low or "вруби" in low) and
            ("музык" in low or "песн" in low or "трек" in low or "радио" in low)
        )
        if is_play_request:
            if hasattr(self.m, 'aimp_ctrl'):
                ok, reply = self.m.aimp_ctrl.play()
                return True, reply

        if any(w in low for w in ["переключи трек", "следующий трек", "следующая песня", "следующая пластинка", "следующий", "скипни трек", "перелистни трек"]):
            if hasattr(self.m, 'aimp_ctrl'):
                ok, reply = self.m.aimp_ctrl.next_track()
                return True, reply

        if any(w in low for w in ["предыдущий трек", "предыдущая песня", "назад песню", "прошлый трек", "трек назад"]):
            if hasattr(self.m, 'aimp_ctrl'):
                ok, reply = self.m.aimp_ctrl.prev_track()
                return True, reply

        if any(w in low for w in ["выключи радио", "стоп радио", "останови радио"]):
            if hasattr(self.m, 'aimp_ctrl'):
                ok, reply = self.m.aimp_ctrl.stop()
                return True, reply

        if any(w in low for w in ["что играет", "какой трек", "название трека", "какая песня играет", "что за песня", "что за трек", "какая музыка играет"]):
            if hasattr(self.m, 'aimp_ctrl'):
                track = self.m.aimp_ctrl.get_current_track()
                if track:
                    return True, f"В радио-эфире звучит: «{track}»! 🎷📻"
                return True, "Радио-эфир сейчас молчит или трек не распознан! 📻"

        # 17. Smart Context Assistant (Code debugging, screen text summarization)
        if any(w in low for w in ["помоги с кодом", "объясни ошибку на экране", "почему ошибка", "разбери ошибку", "что за ошибка", "найди ошибку"]):
            if hasattr(self.m, 'context_asst'):
                self.m.context_asst.explain_active_error()
                return True, ""

        if any(w in low for w in ["кратко перескажи экран", "сделай выжимку", "перескажи статью", "перескажи страницу", "выжимка экрана"]):
            if hasattr(self.m, 'context_asst'):
                self.m.context_asst.summarize_active_screen()
                return True, ""

        # 18. Timers, Alarms & Reminders
        if hasattr(self.m, 'timer_mgr'):
            handled, reply = self.m.timer_mgr.try_parse_and_schedule(cleaned_text)
            if handled:
                return True, reply

        # 19. Workspace Presets
        preset_matches = (
            any(w in low for w in [
                "рабочий сетап", "рабочий setup", "рабочий режим", "настрой рабочее место",
                "игровой сетап", "игровой setup", "время игр", "музыкальный сетап", "музыкальный setup",
                "расставь окна", "окна по бокам", "чистый стол"
            ])
            or ("рабоч" in low and ("сетап" in low or "setup" in low or "режим" in low or "мест" in low))
            or ("игр" in low and ("сетап" in low or "setup" in low or "режим" in low))
        )
        if preset_matches:
            if hasattr(self.m, 'workspace_presets'):
                handled, reply = self.m.workspace_presets.apply_preset(cleaned_text)
                if handled:
                    return True, reply

        # 20. Applications and Websites (AppLauncher)
        if hasattr(self.m, 'app_launcher') and self.m.app_launcher:
            handled, reply = self.m.app_launcher.try_execute_command(text)
            if handled:
                return True, reply

        return False, ""
