import time
import re
import threading
from core.logger import log_info, log_warn


class TimerManager:
    """
    Manages background voice-activated timers, countdowns, alarms, and reminders.
    Supports parsing natural Russian time phrases:
    - «напомни через 15 минут проверить духовку»
    - «таймер на 5 минут»
    - «будильник на 18:30»
    """

    def __init__(self, mascot):
        self.m = mascot
        self.timers = []
        self._lock = threading.Lock()
        self._thread = None
        self._stop_event = threading.Event()
        self._start_runner()

    def _start_runner(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def add_timer(self, delay_seconds: float, text: str, timer_type: str = "напоминание") -> str:
        """Schedules a new timer or reminder."""
        delay_seconds = max(1.0, float(delay_seconds))
        expires_at = time.time() + delay_seconds
        
        timer_id = int(time.time() * 1000) % 100000
        item = {
            "id": timer_id,
            "expires_at": expires_at,
            "text": text.strip() or "Таймер",
            "type": timer_type,
            "initial_delay": delay_seconds
        }

        with self._lock:
            self.timers.append(item)

        minutes = int(delay_seconds // 60)
        seconds = int(delay_seconds % 60)
        time_str = f"{minutes} мин" if minutes > 0 else f"{seconds} сек"
        if minutes > 0 and seconds > 0:
            time_str = f"{minutes} мин {seconds} сек"

        log_info(f"Создан {timer_type}: «{text}» на {time_str}")
        return f"Принято! Поставил {timer_type} на {time_str}: «{text}»! Я позову вас в эфире! ⏰📻"

    def cancel_all(self) -> str:
        with self._lock:
            count = len(self.timers)
            self.timers.clear()
        return f"Сбросил все активные таймеры ({count} шт.)! В эфире чистота! ⏰✖️"

    def get_active_summary(self) -> str:
        with self._lock:
            if not self.timers:
                return "Сейчас нет активных таймеров или напоминаний! ⏰"
            lines = ["⏰ Активные таймеры в эфире:"]
            now = time.time()
            for t in self.timers:
                rem = max(0, int(t["expires_at"] - now))
                m, s = divmod(rem, 60)
                lines.append(f"  • «{t['text']}» — осталось {m}м {s}с")
        return "\n".join(lines)

    def try_parse_and_schedule(self, text: str) -> tuple[bool, str]:
        """Tries to extract time and reminder task from user speech."""
        low = text.lower().strip()

        # 1. Cancel commands
        if any(w in low for w in ["отмени таймеры", "сбрось таймеры", "удали таймеры", "отмени напоминания"]):
            return True, self.cancel_all()

        # 2. List commands
        if any(w in low for w in ["какие таймеры", "список таймеров", "какие напоминания"]):
            return True, self.get_active_summary()

        # 3. "напомни через X (минут/секунд/часов) [текст]"
        remind_m = re.search(r'напомни\s+(?:мне\s+)?через\s+(\d+)\s*(минут[ыа-я]*|сек[унда-я]*|час[а-я]*)(?:\s+(.+))?', low)
        if remind_m:
            qty = int(remind_m.group(1))
            unit = remind_m.group(2)
            task = remind_m.group(3) or "Время вышло!"
            mult = 60
            if "сек" in unit:
                mult = 1
            elif "час" in unit:
                mult = 3600
            delay = qty * mult
            reply = self.add_timer(delay, task, "напоминание")
            return True, reply

        # 4. "таймер на X (минут/секунд/часов)"
        timer_m = re.search(r'таймер\s+(?:на\s+)?(\d+)\s*(минут[ыа-я]*|сек[унда-я]*|час[а-я]*)(?:\s+(.+))?', low)
        if timer_m:
            qty = int(timer_m.group(1))
            unit = timer_m.group(2)
            task = timer_m.group(3) or f"Таймер {qty} {unit}"
            mult = 60
            if "сек" in unit:
                mult = 1
            elif "час" in unit:
                mult = 3600
            delay = qty * mult
            reply = self.add_timer(delay, task, "таймер")
            return True, reply

        # 5. "будильник на HH:MM"
        alarm_m = re.search(r'будильник\s+(?:на\s+)?(\d{1,2})[:\s](\d{2})', low)
        if alarm_m:
            target_h = int(alarm_m.group(1))
            target_m = int(alarm_m.group(2))
            now_lt = time.localtime()
            cur_sec = now_lt.tm_hour * 3600 + now_lt.tm_min * 60 + now_lt.tm_sec
            target_sec = target_h * 3600 + target_m * 60
            diff = target_sec - cur_sec
            if diff <= 0:
                diff += 86400  # Next day
            task = f"Будильник на {target_h:02d}:{target_m:02d}"
            reply = self.add_timer(diff, task, "будильник")
            return True, reply

        return False, ""

    def _check_loop(self):
        """Thread worker that evaluates expired timers every 1 second."""
        while not self._stop_event.is_set():
            now = time.time()
            triggered = []
            with self._lock:
                remaining_timers = []
                for t in self.timers:
                    if now >= t["expires_at"]:
                        triggered.append(t)
                    else:
                        remaining_timers.append(t)
                self.timers = remaining_timers

            for t in triggered:
                self._dispatch_timer_alert(t)

            time.sleep(1.0)

    def _dispatch_timer_alert(self, item: dict):
        """Notifies mascot and user about fired timer."""
        text = item["text"]
        t_type = item["type"]
        log_info(f"Сработал {t_type}: «{text}»!")

        msg = f"⏰ Дзинь-дзинь! Внимание в эфире!\n{t_type.capitalize()}: «{text}»!\nПора действовать, мой друг! 📻✨"
        try:
            self.m.root.after(0, lambda: self.m.show_speech(msg, play_audio=not self.m.is_muted))
            if self.m.chat_win and hasattr(self.m.chat_win, 'append_message'):
                self.m.root.after(0, lambda: self.m.chat_win.append_message("system", f"⏰ {t_type.capitalize()} сработал!\n"))
                self.m.root.after(0, lambda: self.m.chat_win.append_message("bot", f"Аластор: «{text}»\n\n"))
        except Exception:
            pass
