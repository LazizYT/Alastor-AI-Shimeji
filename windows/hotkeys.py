import sys
import threading
from core.config import KEYBOARD_AVAILABLE

if KEYBOARD_AVAILABLE:
    import keyboard

class HotkeyManager:
    """
    Manages global system hotkeys for voice capture.
    Uses Win32 RegisterHotKey in a background thread for layout independence (works in RU and EN).
    Falls back to the keyboard library if needed.
    """
    def __init__(self, on_hotkey_callback, on_wake_word_toggle_callback=None):
        self.callback = on_hotkey_callback
        self.wake_word_callback = on_wake_word_toggle_callback
        self._hotkey_thread_id = None
        self._stop_evt = threading.Event()
        self._thread = None
        self._registered_ids = []

    def start(self):
        # 1. Native Windows Win32 RegisterHotKey in dedicated thread
        if sys.platform == "win32":
            try:
                self._thread = threading.Thread(target=self._win32_hotkey_listener, daemon=True)
                self._thread.start()
            except Exception:
                pass

        # 2. Keyboard library fallback (for non-Windows or additional capture)
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.add_hotkey('f8', self._trigger, suppress=False)
                keyboard.add_hotkey('ctrl+shift+v', self._trigger, suppress=False)
                keyboard.add_hotkey('ctrl+alt+a', self._trigger, suppress=False)
                keyboard.add_hotkey('f9', self._trigger_wake_word, suppress=False)
            except Exception:
                pass

    def _trigger(self):
        if self.callback:
            try:
                self.callback()
            except Exception:
                pass

    def _trigger_wake_word(self):
        if self.wake_word_callback:
            try:
                self.wake_word_callback()
            except Exception:
                pass

    def _win32_hotkey_listener(self):
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            self._hotkey_thread_id = kernel32.GetCurrentThreadId()

            MOD_ALT      = 0x0001
            MOD_CONTROL  = 0x0002
            MOD_SHIFT    = 0x0004
            MOD_NOREPEAT = 0x4000

            # Register hotkeys:
            # 1: F8 (VK_F8 = 0x77) -> Push-to-talk voice capture
            # 2: Ctrl+Shift+V (VK_V = 0x56) -> Voice capture
            # 3: Ctrl+Alt+A (VK_A = 0x41) -> Voice capture
            # 4: F9 (VK_F9 = 0x78) -> Toggle Wake Word «Аластор» Mode
            hotkeys = [
                (1, MOD_NOREPEAT, 0x77),
                (2, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, 0x56),
                (3, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, 0x41),
                (4, MOD_NOREPEAT, 0x78),
            ]
            self._registered_ids = []
            for hk_id, mod, vk in hotkeys:
                if user32.RegisterHotKey(None, hk_id, mod, vk):
                    self._registered_ids.append(hk_id)

            msg = wintypes.MSG()
            while not self._stop_evt.is_set() and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == 0x0312:  # WM_HOTKEY
                    if msg.wParam == 4:
                        self._trigger_wake_word()
                    else:
                        self._trigger()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

            for hk_id in self._registered_ids:
                try:
                    user32.UnregisterHotKey(None, hk_id)
                except Exception:
                    pass
        except Exception:
            pass

    def stop(self):
        self._stop_evt.set()
        if self._hotkey_thread_id and sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.PostThreadMessageW(self._hotkey_thread_id, 0x0012, 0, 0) # WM_QUIT
            except Exception:
                pass
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass
