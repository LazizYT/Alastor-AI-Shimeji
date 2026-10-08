import os
import re
import json
import webbrowser
import urllib.parse
import ctypes
from core.config import APPS_CONFIG_FILE, WIN32_AVAILABLE

class AppLauncher:
    def __init__(self, mascot_ref=None):
        self.mascot = mascot_ref
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(APPS_CONFIG_FILE):
            return self.init_default_config()
        try:
            with open(APPS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return self.init_default_config()

    def init_default_config(self):
        default_cfg = {
            "websites": {
                "youtube": {"keywords": ["ютуб", "youtube", "ютубчик", "ютубе"], "url": "https://www.youtube.com", "reply": "Включаю YouTube! Приятного просмотра, мой друг! 📺"},
                "vk": {"keywords": ["вк", "вконтакте", "vk"], "url": "https://vk.com", "reply": "Открываю ВКонтакте! Поглядим на светские беседы! 💬"},
                "telegram_web": {"keywords": ["телеграм веб", "тг веб"], "url": "https://web.telegram.org", "reply": "Открываю Telegram Web! ✉️"},
                "github": {"keywords": ["гитхаб", "github"], "url": "https://github.com", "reply": "Открываю GitHub! Посмотрим на твои хитроумные алгоритмы! 🐙"},
                "twitch": {"keywords": ["твич", "twitch"], "url": "https://www.twitch.tv", "reply": "Включаю Twitch! Прямой эфир — это моё призвание! 🎮"},
                "kinopoisk": {"keywords": ["кинопоиск", "фильмы", "кино"], "url": "https://www.kinopoisk.ru", "reply": "Открываю Кинопоиск! Время для кинематографа! 🎬"},
                "wikipedia": {"keywords": ["википедия", "вики", "wikipedia"], "url": "https://ru.wikipedia.org", "reply": "Открываю Википедию! Жажда знаний достойна похвалы! 📚"},
                "chatgpt": {"keywords": ["чатгпт", "чат гпт", "chatgpt"], "url": "https://chatgpt.com", "reply": "Открываю ChatGPT! Другой искусственный разум? Занятно... 🤖"},
                "wildberries": {"keywords": ["вайлдберриз", "вайлдберис", "вб", "wildberries"], "url": "https://www.wildberries.ru", "reply": "Открываю Wildberries! Очередная сделка с быстрой доставкой! 🛍️"},
                "ozon": {"keywords": ["озон", "ozon"], "url": "https://www.ozon.ru", "reply": "Открываю Ozon! Приятных покупок! 📦"},
                "music": {"keywords": ["яндекс музыка", "яндекс музыку", "yandex music", "включи музыку", "открой музыку", "спотифай", "spotify"], "url": "https://music.yandex.ru", "reply": "Музыка в эфире! Внимайте ритмам, дамы и господа! 🎷🎶"},
                "mail": {"keywords": ["почта", "почту", "gmail", "мейл"], "url": "https://mail.google.com", "reply": "Открываю почту! Проверим ваши тайные депеши! ✉️"}
            },
            "apps": {
                "telegram": {"keywords": ["телеграм", "телега", "тг", "telegram"], "target": "telegram", "reply": "Запускаю Telegram! Радиоволны несут сообщения! 📱"},
                "steam": {"keywords": ["стим", "steam"], "target": "steam", "reply": "Запускаю Steam! Шоу и игры начинаются! 🎮"},
                "discord": {"keywords": ["дискорд", "диск", "discord"], "target": "discord", "reply": "Запускаю Discord! Собираем почтеннейшую публику! 🎙️"},
                "browser": {"keywords": ["браузер", "интернет", "хром", "chrome", "edge"], "target": "https://www.google.com", "reply": "Открываю браузер! Погружаемся в пучины сети! 🌐"},
                "calculator": {"keywords": ["калькулятор", "кальк", "calc"], "target": "calc.exe", "reply": "Калькулятор запущен! Подсчитаем наши грехи и доходы! 🧮"},
                "notepad": {"keywords": ["блокнот", "заметки", "notepad"], "target": "notepad.exe", "reply": "Открываю Блокнот! Запиши что-нибудь достойное истории! 📝"},
                "explorer": {"keywords": ["проводник", "мой компьютер", "файлы", "папки"], "target": "explorer.exe", "reply": "Открываю Проводник! Исследуем закоулки твоей системы! 📁"},
                "taskmgr": {"keywords": ["диспетчер задач", "диспетчер"], "target": "taskmgr.exe", "reply": "Диспетчер задач! Кто из процессов сегодня провинился? ⚡"},
                "settings": {"keywords": ["настройки", "параметры"], "target": "ms-settings:", "reply": "Открываю параметры Windows! Подкрутим шестерёнки! ⚙️"},
                "terminal": {"keywords": ["терминал", "консоль", "командная строка", "cmd", "powershell"], "target": "cmd.exe", "reply": "Командная строка к твоим услугам! Власть над кодом! 💻"},
                "paint": {"keywords": ["пейнт", "паинт", "paint"], "target": "mspaint.exe", "reply": "Открываю Paint! Твори, мой юный художник! 🎨"}
            }
        }
        try:
            with open(APPS_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return default_cfg

    @staticmethod
    def _matches_keyword(text: str, keyword: str) -> bool:
        kw = keyword.lower().strip()
        txt = text.lower().strip()
        if not kw or not txt:
            return False
        if " " in kw:
            return kw in txt
        pattern = r'(?<![a-zA-Zа-яА-ЯёЁ0-9_])' + re.escape(kw) + r'(?![a-zA-Zа-яА-ЯёЁ0-9_])'
        return bool(re.search(pattern, txt))

    @staticmethod
    def find_app_shortcut(app_name):
        dirs = [
            os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Start Menu\Programs'),
            r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs',
            os.path.expandvars(r'%USERPROFILE%\Desktop'),
            r'C:\Users\Public\Desktop'
        ]
        app_low = app_name.lower().strip()
        for d in dirs:
            if not os.path.exists(d):
                continue
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith(('.lnk', '.exe')):
                        name = os.path.splitext(f)[0].lower()
                        if app_low == name or app_low in name:
                            return os.path.join(root, f)
        return None

    def launch_target(self, target):
        try:
            # Theatrical gesture and mouse movement if gesture_launch_mode is active
            if getattr(self.mascot, 'gesture_launch_mode', False):
                try:
                    if hasattr(self.mascot, 'set_state') and hasattr(self.mascot, 'root'):
                        img_keys = getattr(self.mascot.sprite_mgr, 'images', {})
                        st = "guitar" if "guitar" in img_keys else "walking"
                        self.mascot.root.after(0, lambda: self.mascot.set_state(st))
                    if hasattr(self.mascot, 'input_ctrl'):
                        self.mascot.input_ctrl.move_to_center()
                    import time
                    time.sleep(0.3)
                except Exception:
                    pass

            if target.startswith(('http://', 'https://')):
                webbrowser.open(target)
                return True
            if target.startswith(('ms-', 'steam:', 'tg:', 'discord:', 'calc:', 'mailto:', 'microsoft-edge:')):
                os.startfile(target)
                return True
            if os.path.exists(target):
                os.startfile(target)
                return True
            system_bins = ['calc.exe', 'notepad.exe', 'explorer.exe', 'taskmgr.exe', 'cmd.exe', 'mspaint.exe', 'wt.exe', 'code', 'obs64.exe', 'aimp.exe', 'potplayer64.exe', 'totalcmd64.exe', 'winrar.exe', 'zoom.exe']
            if target.lower() in system_bins:
                os.startfile(target)
                return True
            shortcut = self.find_app_shortcut(target)
            if shortcut and os.path.exists(shortcut):
                os.startfile(shortcut)
                return True
            os.startfile(target)
            return True
        except Exception:
            return False

    @staticmethod
    def adjust_volume(direction):
        try:
            VK_VOLUME_MUTE = 0xAD
            VK_VOLUME_DOWN = 0xAE
            VK_VOLUME_UP   = 0xAF
            key = VK_VOLUME_MUTE if direction == 'mute' else (VK_VOLUME_UP if direction == 'up' else VK_VOLUME_DOWN)
            count = 1 if direction == 'mute' else 5
            for _ in range(count):
                ctypes.windll.user32.keybd_event(key, 0, 0, 0)
                ctypes.windll.user32.keybd_event(key, 0, 2, 0)
            return True
        except Exception:
            return False

    def try_execute_command(self, text: str) -> tuple[bool, str | None]:
        raw = text.strip()
        low = raw.lower()
        cleaned = ''
        for ch in low:
            if ch in ',.!?\"\'«»':
                cleaned += ' '
            else:
                cleaned += ch
        fillers = {'аластор', 'пожалуйста', 'плиз', 'можешь', 'будь', 'добр', 'быстро', 'друг', 'мне', 'нам'}
        tokens = [w for w in cleaned.split() if w not in fillers]
        cmd = ' '.join(tokens)

        questions = ['что такое', 'кто такой', 'как ', 'почему', 'зачем', 'расскажи', 'объясни', 'сколько', 'когда', 'где находится', 'в чем разница']
        if any(q in cmd for q in questions):
            return False, None

        # 1. Volume
        if any(w in cmd for w in ['сделай громче', 'прибавь звук', 'громче звук', 'увеличь громкость', 'погромче']):
            if self.adjust_volume('up'):
                return True, "Прибавил громкость! Да звучит музыка на полную! 🔊📻"
        if any(w in cmd for w in ['сделай тише', 'убавь звук', 'тише звук', 'уменьши громкость', 'потише']):
            if self.adjust_volume('down'):
                return True, "Сделал потише! Приглушим радиопомехи! 🔉"
        if any(w in cmd for w in ['выключи звук', 'заглуши звук', 'без звука', 'включи звук', 'мут', 'мьют']):
            if self.adjust_volume('mute'):
                return True, "Звук переключен! Тишина в эфире... 🔇"

        # 2. Window & Desktop via mascot if available
        if self.mascot:
            if any(w in cmd for w in [
                'закрой окно', 'закрыть окно', 'закрой активное окно', 'закрыть активное окно',
                'закрой эту программу', 'закрыть эту программу', 'закрой программу', 'закрыть программу',
                'закрой приложение', 'закрыть приложение'
            ]) or (cmd in ['закрой', 'закрыть']):
                self.mascot.action_close_foreground()
                return True, "Закрыл активное окно! Шоу окончено! ✖️"
            if any(w in cmd for w in [
                'сверни окно', 'свернуть окно', 'сверни активное окно', 'свернуть активное окно',
                'спрячь окно', 'спрятать окно', 'минимизируй окно', 'минимизировать окно',
                'сверни всё', 'сверни все окна', 'сверни приложение', 'свернуть приложение'
            ]) or (cmd in ['сверни', 'свернуть', 'минимизируй']):
                self.mascot.troll_minimize()
                return True, "Свернул окно отдыхать! 📉"
            if any(w in cmd for w in ['выровняй значки', 'убери на столе', 'порядок на столе', 'сортируй значки']):
                self.mascot.action_sort_desktop()
                return True, "Навёл идеальный порядок на рабочем столе! 🧹✨"

        # 3. Web Search
        search_m = re.search(r'^(?:найди|загугли|поищи|поиск|найди в интернете)\s+(.+)$', cmd)
        if search_m:
            q = search_m.group(1).strip()
            if 'в яндексе' in q:
                q = q.replace('в яндексе', '').strip()
                webbrowser.open(f"https://yandex.ru/search/?text={urllib.parse.quote(q)}")
                return True, f"Ищу в Яндексе «{q}»! 🔍"
            else:
                q = q.replace('в гугле', '').strip()
                webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(q)}")
                return True, f"Ищу в Google «{q}»! Радиоэфир уже передаёт ваш запрос! 🔍"

        # 4. Close specific app by name (MUST precede app launch keywords)
        close_m = re.search(r'^(?:закрой|убей|выключи|заверши|останови|убери)\s+(?:программу\s+|приложение\s+)?(.+)$', cmd)
        if close_m:
            target_name = close_m.group(1).strip()
            # If user said 'окно' or 'активное окно', mascot closes foreground
            if target_name in ['окно', 'активное окно', 'эту программу', 'текущее окно']:
                if self.mascot:
                    self.mascot.action_close_foreground()
                    return True, "Закрыл активное окно! Шоу окончено! ✖️"
            closed = self.close_target(target_name)
            if closed:
                return True, f"Прикрыл лавочку «{target_name.capitalize()}»! В эфире чистота и порядок! ✖️"
            else:
                return True, f"Программа «{target_name.capitalize()}» уже закрыта или не найдена в эфире! 📻"

        # 5. Focus / switch window
        focus_m = re.search(r'^(?:переключись на|перейди в|открой окно|покажи окно|активируй)\s+(?:окно\s+)?(.+)$', cmd)
        if focus_m:
            target_name = focus_m.group(1).strip()
            focused_title = self.focus_window(target_name)
            if focused_title:
                return True, f"Переключил ваше внимание на «{focused_title}»! 👁️✨"

        # 6. Websites (YouTube checked first to ensure priority)
        websites = self.config.get('websites', {})
        if "youtube" in websites and any(self._matches_keyword(cmd, k) for k in websites["youtube"].get('keywords', [])):
            self.launch_target(websites["youtube"]['url'])
            return True, websites["youtube"].get('reply', "Включаю YouTube! Приятного просмотра, мой друг! 📺")

        for site_key, site_info in websites.items():
            if site_key == "youtube":
                continue
            if any(self._matches_keyword(cmd, k) for k in site_info.get('keywords', [])):
                self.launch_target(site_info['url'])
                return True, site_info.get('reply', f"Открываю {site_key}! 🌐")

        # 7. Apps
        apps = self.config.get('apps', {})
        for app_key, app_info in apps.items():
            if any(self._matches_keyword(cmd, k) for k in app_info.get('keywords', [])):
                ok = self.launch_target(app_info['target'])
                if ok:
                    return True, app_info.get('reply', f"Запускаю {app_key}! 🚀")

        # 8. Direct URL / Domain
        url_m = re.search(r'(?:сайт\s+)?([a-zA-Z0-9\-\_]+\.(?:com|ru|org|net|io|dev|app|ai)(?:/[^\s]*)?)', cmd)
        if url_m:
            domain = url_m.group(1)
            target_url = 'https://' + domain if not domain.startswith(('http://', 'https://')) else domain
            self.launch_target(target_url)
            return True, f"Открываю сайт {domain}! 🌐"

        # 9. Generic open/launch
        open_m = re.search(r'^(?:открой|запусти|включи|зайди в)\s+(?:программу\s+|приложение\s+)?(.+)$', cmd)
        if open_m:
            target_name = open_m.group(1).strip()
            shortcut = self.find_app_shortcut(target_name)
            if shortcut:
                self.launch_target(shortcut)
                return True, f"Запускаю «{target_name.capitalize()}»! Наслаждайтесь, мой друг! 🚀"
            try:
                os.startfile(target_name)
                return True, f"Запускаю «{target_name.capitalize()}»! 🚀"
            except Exception:
                pass

        return False, None

    def close_target(self, target_name: str) -> bool:
        """Terminates an application or process by common name or executable name."""
        import subprocess
        low = target_name.lower().strip()

        known_map = {
            "vs code": ["Code.exe", "code.exe"],
            "vscode": ["Code.exe", "code.exe"],
            "вс код": ["Code.exe", "code.exe"],
            "вскод": ["Code.exe", "code.exe"],
            "visual studio code": ["Code.exe", "code.exe"],
            "visual studio": ["devenv.exe", "Code.exe"],
            "вижуал студио": ["Code.exe", "devenv.exe"],
            "вижуал студио код": ["Code.exe"],
            "вижуал": ["Code.exe"],
            "код": ["Code.exe", "code.exe"],
            "code": ["Code.exe", "code.exe"],
            "калькулятор": ["CalculatorApp.exe", "calc.exe"],
            "кальк": ["CalculatorApp.exe", "calc.exe"],
            "блокнот": ["notepad.exe"],
            "пейнт": ["mspaint.exe"],
            "паинт": ["mspaint.exe"],
            "проводник": ["explorer.exe"],
            "диспетчер": ["taskmgr.exe"],
            "диспетчер задач": ["taskmgr.exe"],
            "телеграм": ["Telegram.exe"],
            "тг": ["Telegram.exe"],
            "телега": ["Telegram.exe"],
            "дискорд": ["Discord.exe"],
            "диск": ["Discord.exe"],
            "стим": ["steam.exe", "steamwebhelper.exe"],
            "хром": ["chrome.exe"],
            "браузер": ["chrome.exe", "msedge.exe", "browser.exe", "firefox.exe", "opera.exe"],
            "яндекс браузер": ["browser.exe"],
            "яндекс": ["browser.exe"],
            "эдж": ["msedge.exe"],
            "спотифай": ["Spotify.exe"],
            "аимп": ["AIMP.exe"],
            "потплеер": ["PotPlayer64.exe", "PotPlayer.exe"],
            "тотал": ["TOTALCMD64.exe", "TOTALCMD.exe"],
            "обс": ["obs64.exe", "obs32.exe"],
            "флоу": ["Flow.Launcher.exe"],
            "зум": ["Zoom.exe"],
            "винрар": ["WinRAR.exe"],
            "ножницы": ["SnippingTool.exe"],
            "терминал": ["WindowsTerminal.exe", "wt.exe", "cmd.exe", "powershell.exe"],
            "командная строка": ["cmd.exe"],
            "консоль": ["cmd.exe", "powershell.exe", "WindowsTerminal.exe"],
            "пауэршелл": ["powershell.exe"],
            "контра": ["cs2.exe", "hl.exe"],
            "кс": ["cs2.exe", "hl.exe"],
            "кс2": ["cs2.exe"],
            "нфс": ["speed.exe"],
        }
        for k, v in known_map.items():
            if k == low or k in low or low in k:
                success = False
                for proc in v:
                    try:
                        res = subprocess.run(["taskkill", "/F", "/T", "/IM", proc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        if res.returncode == 0:
                            success = True
                    except Exception:
                        pass
                if success:
                    return True

        apps = self.config.get('apps', {})
        for app_key, app_info in apps.items():
            if any(k in low for k in app_info.get('keywords', [])) or app_key in low:
                tgt = app_info.get('target', '')
                if tgt.lower() in ['code', 'vscode']:
                    candidates = ['Code.exe', 'code.exe']
                elif tgt.endswith('.exe'):
                    candidates = [tgt]
                else:
                    candidates = [f"{tgt}.exe"]
                for proc in candidates:
                    try:
                        res = subprocess.run(["taskkill", "/F", "/T", "/IM", proc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        if res.returncode == 0:
                            return True
                    except Exception:
                        pass

        # Try closing open window by title or killing its PID via Win32
        if WIN32_AVAILABLE:
            try:
                import win32gui, win32process
                matching_hwnds = []
                def _win_finder(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd):
                        wtitle = win32gui.GetWindowText(hwnd).strip()
                        if wtitle:
                            wlow = wtitle.lower()
                            if any(k in low for k in ["vs code", "vscode", "visual studio code", "код", "code"]) and "visual studio code" in wlow:
                                matching_hwnds.append(hwnd)
                            elif low in wlow:
                                matching_hwnds.append(hwnd)
                win32gui.EnumWindows(_win_finder, None)
                if matching_hwnds:
                    for hwnd in matching_hwnds:
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            win32gui.PostMessage(hwnd, 0x0010, 0, 0)
                            if pid > 0:
                                subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            return True
                        except Exception:
                            pass
            except Exception:
                pass

        # Direct executable fallback
        try:
            proc_name = low if low.endswith('.exe') else f"{low}.exe"
            res = subprocess.run(["taskkill", "/F", "/IM", proc_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                return True
        except Exception:
            pass

        return False

    def focus_window(self, query: str) -> str | None:
        """Finds a top-level window by title substring and brings it to foreground."""
        try:
            import win32gui, win32con
            low = query.lower().strip()
            found_title = None

            def _enum_cb(hwnd, _):
                nonlocal found_title
                if found_title:
                    return False
                if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                    title = win32gui.GetWindowText(hwnd).strip()
                    if title and low in title.lower():
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                        found_title = title
                        return False
                return True

            win32gui.EnumWindows(_enum_cb, None)
            return found_title
        except Exception:
            return None

    def launch_quick(self, target_key: str):
        if target_key in self.config.get("websites", {}):
            info = self.config["websites"][target_key]
            self.launch_target(info["url"])
            if self.mascot:
                self.mascot.show_speech(info.get("reply", "Открываю сайт! 🌐"))
        elif target_key in self.config.get("apps", {}):
            info = self.config["apps"][target_key]
            self.launch_target(info["target"])
            if self.mascot:
                self.mascot.show_speech(info.get("reply", "Запускаю программу! 🚀"))

    def open_apps_config_file(self):
        try:
            if not os.path.exists(APPS_CONFIG_FILE):
                self.init_default_config()
            os.startfile(APPS_CONFIG_FILE)
            if self.mascot:
                self.mascot.show_speech("Открыл apps_config.json!\nТам можно настроить любые программы ⚙️")
        except Exception as e:
            if self.mascot:
                self.mascot.show_speech(f"Ошибка открытия: {e}")
