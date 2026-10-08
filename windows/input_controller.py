import time
import math
import random
import threading
import pyautogui
import keyboard
from core.logger import log_info, log_warn

class InputController:
    """
    Controls mouse and keyboard inputs on Windows.
    Enables voice commands, UI actions, and autonomous demon trolling.
    """
    def __init__(self):
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.05

    def get_position(self) -> tuple[int, int]:
        """Returns current mouse cursor position (x, y)."""
        try:
            pos = pyautogui.position()
            return (pos.x, pos.y)
        except Exception:
            return (0, 0)

    def click(self, button: str = "left", clicks: int = 1) -> bool:
        """Click mouse button: 'left', 'right', or 'middle'."""
        try:
            pyautogui.click(button=button, clicks=clicks)
            log_info(f"Ввод: клик мыши ({button}, {clicks}x)")
            return True
        except Exception as e:
            log_warn(f"Ошибка клика мыши: {e}")
            return False

    def double_click(self) -> bool:
        return self.click(button="left", clicks=2)

    def right_click(self) -> bool:
        return self.click(button="right", clicks=1)

    def scroll(self, clicks: int) -> bool:
        """Scroll mouse wheel: positive = up, negative = down."""
        try:
            pyautogui.scroll(clicks * 100)
            direction = "вверх" if clicks > 0 else "вниз"
            log_info(f"Ввод: прокрутка мыши {direction} ({clicks})")
            return True
        except Exception as e:
            log_warn(f"Ошибка скролла: {e}")
            return False

    def move_to(self, x: int, y: int, duration: float = 0.25) -> bool:
        """Smoothly move cursor to absolute screen coordinates."""
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            log_warn(f"Ошибка перемещения курсора: {e}")
            return False

    def move_to_center(self) -> bool:
        try:
            sw, sh = pyautogui.size()
            return self.move_to(sw // 2, sh // 2, duration=0.3)
        except Exception:
            return False

    def get_pos(self) -> tuple[int, int]:
        try:
            p = pyautogui.position()
            return (p.x, p.y)
        except Exception:
            return (0, 0)

    def type_text(self, text: str) -> bool:
        """
        Type text into the active focused window.
        Uses keyboard.write with fallback to clipboard for 100% reliable Cyrillic support.
        """
        clean = text.strip()
        if not clean:
            return False
        try:
            keyboard.write(clean, delay=0.015)
            log_info(f"Ввод текста: «{clean[:40]}»")
            return True
        except Exception:
            try:
                import tkinter as tk
                r = tk.Tk()
                r.withdraw()
                r.clipboard_clear()
                r.clipboard_append(clean)
                r.update()
                r.destroy()
                time.sleep(0.05)
                pyautogui.hotkey('ctrl', 'v')
                log_info(f"Ввод текста через буфер обмена: «{clean[:40]}»")
                return True
            except Exception as e:
                log_warn(f"Ошибка ввода текста: {e}")
                return False

    def press_key(self, key_name: str) -> bool:
        """Press a named key: enter, space, esc, backspace, tab, delete, etc."""
        norm_key = key_name.lower().strip()
        key_map = {
            "ввод": "enter",
            "энтер": "enter",
            "пробел": "space",
            "отмена": "esc",
            "эскейп": "esc",
            "стереть": "backspace",
            "бекспейс": "backspace",
            "удалить": "delete",
            "таб": "tab"
        }
        actual_key = key_map.get(norm_key, norm_key)
        try:
            pyautogui.press(actual_key)
            log_info(f"Ввод: нажата клавиша «{actual_key}»")
            return True
        except Exception as e:
            log_warn(f"Ошибка нажатия клавиши {key_name}: {e}")
            return False

    def hotkey(self, *keys) -> bool:
        """Execute a key combination like ('ctrl', 'c'), ('win', 'd')."""
        try:
            pyautogui.hotkey(*keys)
            log_info(f"Ввод: комбинация клавиш {' + '.join(keys)}")
            return True
        except Exception as e:
            log_warn(f"Ошибка хоткея {' + '.join(keys)}: {e}")
            return False

    def playful_wiggle(self):
        """Alastor's playful spiral cursor wiggle!"""
        def _worker():
            try:
                curr_x, curr_y = pyautogui.position()
                for i in range(14):
                    angle = i * 0.48
                    radius = 16 + i * 2.2
                    nx = int(curr_x + radius * math.cos(angle))
                    ny = int(curr_y + radius * math.sin(angle))
                    pyautogui.moveTo(nx, ny, duration=0.015)
                pyautogui.moveTo(curr_x, curr_y, duration=0.08)
                log_info("Аластор подшутил над курсором мыши")
            except Exception:
                pass
        threading.Thread(target=_worker, daemon=True).start()

    def nudge_towards(self, target_x: int, target_y: int):
        """Slightly nudge the mouse cursor toward a target position."""
        try:
            curr_x, curr_y = pyautogui.position()
            dx = (target_x - curr_x) * 0.15
            dy = (target_y - curr_y) * 0.15
            pyautogui.moveTo(int(curr_x + dx), int(curr_y + dy), duration=0.08)
        except Exception:
            pass
