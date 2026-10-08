import re
import time
import urllib.parse
import webbrowser
import threading
from core.logger import log_info, log_warn


class ActionChainPlanner:
    """
    Interprets and orchestrates multi-step, sequential user commands.
    Examples:
      - "открой браузер, зайди в YouTube и поищи [песню]"
      - "открой блокнот, напиши [текст] и сохрани"
      - "открой калькулятор, подожди 2 секунды и закрой его"
    """

    def __init__(self, mascot):
        self.m = mascot

    def is_chained_command(self, text: str) -> bool:
        low = text.lower().strip()
        # 1. YouTube compound search
        if any(w in low for w in ["ютуб", "youtube"]) and any(w in low for w in ["поищи", "найди", "включи", "поставь", "песн", "трек", "клип"]):
            if any(w in low for w in ["открой", "зайди", "перейди"]):
                return True

        # 2. Notepad compound writing
        if any(w in low for w in ["блокнот", "notepad"]) and any(w in low for w in ["напиши", "напечатай", "введи", "запиши"]):
            return True

        # 3. Explicit sequential conjunctions
        delimiters = [", затем ", ", потом ", " и затем ", " и потом ", ", а потом ", " после этого ", ", после чего "]
        return any(d in low for d in delimiters)

    def execute_chain(self, text: str) -> tuple[bool, str]:
        low = text.lower().strip()

        # Pattern A: "открой браузер, зайди в YouTube и поищи песню ..."
        yt_m = re.search(
            r'(?:открой|запусти)?\s*(?:браузер|хром|edge|интернет)?,?\s*(?:зайди в|перейди на|открой)?\s*(?:ютуб|youtube)\s*(?:и|,)?\s*(?:поищи|найди|включи|поставь)\s*(?:эту\s+)?(?:песню|трек|музыку|видео|ролик)?\s*[:«"\'\s](.+?)[»"\'\s]*$',
            low
        )
        if not yt_m:
            # Fallback regex for "найди в ютубе песню ..."
            yt_m = re.search(r'(?:в\s+)?(?:ютубе?|youtube)\s+(?:поищи|найди|включи)\s+(?:песню|трек|музыку|видео)?\s*[:«"\'\s](.+?)[»"\'\s]*$', low)

        if yt_m:
            query = yt_m.group(1).strip().strip('«»"\'.,!?')
            if query:
                threading.Thread(target=self._chain_youtube_search, args=(query,), daemon=True).start()
                return True, f"Приступаю к операции! Открываю YouTube и ищу «{query}»! 🌐📺🎷"

        # Pattern B: "открой блокнот, напиши [текст] (и сохрани)?"
        np_m = re.search(r'(?:открой|запусти)?\s*(?:блокнот|notepad)\s*(?:и|,)\s*(?:напиши|напечатай|введи|запиши)\s*[:«"\'\s](.+?)[»"\'\s]*$', low)
        if np_m:
            content = np_m.group(1).strip().strip('«»"\'')
            save_after = "сохрани" in low
            if content:
                threading.Thread(target=self._chain_notepad_write, args=(content, save_after), daemon=True).start()
                return True, f"Открываю Блокнот и записываю ваши слова: «{content[:25]}...» 📝"

        # Pattern C: Generic step-by-step splitting
        steps = self._split_steps(text)
        if len(steps) > 1:
            threading.Thread(target=self._chain_generic_steps, args=(steps,), daemon=True).start()
            return True, f"Принято! Выполняю последовательность из {len(steps)} действий... 🎭"

        return False, ""

    def _split_steps(self, text: str) -> list[str]:
        # Normalize conjunctions into unique separator
        s = text
        for d in [", затем ", ", потом ", " и затем ", " и потом ", ", а потом ", " после этого ", ", после чего "]:
            s = s.replace(d, " ||| ")
        steps = [step.strip() for step in s.split(" ||| ") if step.strip()]
        return steps

    def _chain_youtube_search(self, song_name: str):
        """Asynchronous execution: Browser -> YouTube -> Search Input -> Play/Show -> Vision Check."""
        try:
            log_info(f"Запуск цепочки действий YouTube для запроса: «{song_name}»")
            
            # Step 1: Theatrical Mascot Gesture
            if getattr(self.m, 'gesture_launch_mode', False):
                self._perform_mascot_gesture("Захожу на YouTube через радиоволны! 🎩🖱️")
                if hasattr(self.m, 'input_ctrl'):
                    self.m.input_ctrl.move_to_center()

            # Step 2: Open YouTube Search
            encoded = urllib.parse.quote_plus(song_name)
            search_url = f"https://www.youtube.com/results?search_query={encoded}"
            webbrowser.open(search_url)

            # Step 3: Wait for browser window to load
            time.sleep(2.5)

            # Step 4: If gesture mode is active, simulate clicking and typing
            if getattr(self.m, 'gesture_launch_mode', False) and hasattr(self.m, 'input_ctrl'):
                # In YouTube, pressing '/' focuses the search box
                self.m.input_ctrl.press_key('/')
                time.sleep(0.3)
                self.m.input_ctrl.type_text(song_name)
                time.sleep(0.3)
                self.m.input_ctrl.press_key('enter')

            # Step 5: Announce success
            reply = f"Песня «{song_name}» найдена и звучит в эфире YouTube! Приятного прослушивания! 🎷📺"
            self.m.root.after(0, lambda: self.m.show_speech(reply, play_audio=True))
            log_info("Цепочка действий YouTube успешно завершена")

            # Step 6: Optional Vision Glance
            time.sleep(2.0)
            if hasattr(self.m, 'vision_engine') and self.m.vision_engine:
                ok, vis_text, _ = self.m.vision_engine.analyze_screen(
                    custom_prompt=f"Ты — Аластор. Пользователь только что открыл на YouTube поиск по запросу «{song_name}». Взгляни кратко (1-2 предложения) на открывшуюся страницу с результатами и прокомментируй."
                )
                if ok and vis_text:
                    self.m.root.after(0, lambda: self.m.show_speech(f"Взглянул на результаты:\n{vis_text[:120]}... 👀", play_audio=False))

        except Exception as e:
            log_warn(f"Ошибка в цепочке YouTube: {e}")

    def _chain_notepad_write(self, content: str, save_after: bool = False):
        """Asynchronous execution: Open Notepad -> Focus -> Type Text -> Save if requested."""
        try:
            log_info(f"Запуск цепочки действий Блокнот: «{content[:30]}»")
            
            # Step 1: Open Notepad
            if hasattr(self.m, 'app_launcher'):
                self.m.app_launcher.launch_target("notepad.exe")

            # Step 2: Theatrical Gesture if enabled
            if getattr(self.m, 'gesture_launch_mode', False):
                self._perform_mascot_gesture("Открываю Блокнот взмахом руки! 📝✨")

            # Step 3: Wait for Notepad window to initialize
            time.sleep(1.8)

            # Step 4: Focus Notepad
            if hasattr(self.m, 'app_launcher'):
                self.m.app_launcher.focus_window("notepad")
                self.m.app_launcher.focus_window("блокнот")
            time.sleep(0.5)

            # Step 5: Type content
            if hasattr(self.m, 'input_ctrl'):
                self.m.input_ctrl.type_text(content)
                self.m.input_ctrl.press_key('enter')

            # Step 6: Save if requested
            if save_after and hasattr(self.m, 'input_ctrl'):
                time.sleep(0.5)
                self.m.input_ctrl.hotkey('ctrl', 's')

            # Step 7: Confirmation
            msg = f"Текст «{content[:25]}...» успешно напечатан в Блокноте! 📝"
            self.m.root.after(0, lambda: self.m.show_speech(msg, play_audio=True))
            log_info("Цепочка действий Блокнот завершена")

        except Exception as e:
            log_warn(f"Ошибка в цепочке Блокнот: {e}")

    def _chain_generic_steps(self, steps: list[str]):
        """Executes a list of individual command steps sequentially."""
        try:
            for idx, step in enumerate(steps):
                log_info(f"Выполнение шага {idx + 1}/{len(steps)}: «{step}»")
                if hasattr(self.m, 'command_router'):
                    # Execute single step avoiding recursing back into chain planner
                    low_step = step.lower().strip()
                    self.m.root.after(0, lambda s=step: self.m.show_speech(f"Шаг {idx+1}: «{s}»...", play_audio=False))
                    handled, reply = self._execute_single_step(step)
                    if handled and reply:
                        time.sleep(1.5)
                time.sleep(1.2)

            self.m.root.after(0, lambda: self.m.show_speech("Все шаги цепочки успешно выполнены! Шоу продолжается! 🎩✨", play_audio=True))
        except Exception as e:
            log_warn(f"Ошибка общей цепочки шагов: {e}")

    def _execute_single_step(self, step_text: str) -> tuple[bool, str]:
        """Dispatches a single step through app launcher, input controller, or window commands."""
        # 1. Close
        if hasattr(self.m, 'app_launcher'):
            handled, reply = self.m.app_launcher.try_execute_command(step_text)
            if handled:
                return True, reply

        # 2. Window navigation
        low = step_text.lower().strip()
        if "окно" in low and ("запрыгни" in low or "прыгай" in low):
            self.m.action_jump_to_window()
            return True, "Прыгнул на окно"
        if "пол" in low or "вниз" in low:
            self.m.action_jump_to_floor()
            return True, "Спрыгнул на пол"

        return False, ""

    def _perform_mascot_gesture(self, message: str = ""):
        """Visual animation on mascot canvas when performing gesture actions."""
        try:
            if hasattr(self.m, 'set_state'):
                if "guitar" in getattr(self.m.sprite_mgr, 'images', {}):
                    self.m.root.after(0, lambda: self.m.set_state("guitar"))
            if message:
                self.m.root.after(0, lambda: self.m.show_speech(message, play_audio=False))
        except Exception:
            pass
