#!/usr/bin/env python3
"""
Alastor Voice AI Shimeji Companion (Windows Desktop Mascot)
Launcher & Compatibility Entry Point.
"""

import os
import sys

# Hide console window immediately if started in terminal on Windows
if sys.platform == "win32":
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

# Ensure project root is in sys.path
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Auto-install essential dependencies if running from source (not frozen exe)
if not getattr(sys, 'frozen', False):
    try:
        from PIL import Image, ImageTk
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pillow"])
        from PIL import Image, ImageTk

    try:
        import requests
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"])
        import requests

def ensure_single_instance():
    """Prevents duplicate Alastor instances from running simultaneously."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Global\\AlastorShimeji_SingleInstance_Mutex_98765"
        mutex = kernel32.CreateMutexW(None, False, mutex_name)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            ctypes.windll.user32.MessageBoxW(
                0,
                "Аластор уже запущен и находится на экране или в трее (возле часов Windows).\n\n"
                "• Чтобы открыть меню, нажмите ПКМ по маскоту или по его иконке в трее.\n"
                "• Чтобы завершить работу, запустите stop.bat или выберите «Выход из эфира» в трее.",
                "Alastor Shimeji (Уже запущен)",
                0x40  # MB_ICONINFORMATION
            )
            sys.exit(0)
        return mutex
    except Exception:
        return None

if __name__ == "__main__":
    _mutex = ensure_single_instance()
    try:
        from engine.mascot import Shimeji
        app = Shimeji()
    except Exception as e:
        import traceback
        err_text = traceback.format_exc()
        try:
            log_path = os.path.join(BASE_DIR, "alastor_error.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(err_text)
        except Exception:
            pass
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Ошибка запуска Аластора:\n\n{e}\n\nПодробности записаны в alastor_error.log",
                "Ошибка запуска Alastor",
                0x10  # MB_ICONERROR
            )
        sys.exit(1)