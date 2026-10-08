import os
import sys

# Platform and optional library availability flags
try:
    import win32gui, win32con, win32api, win32process
    import ctypes
    import ctypes.wintypes
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

try:
    import winshell
    WINSHELL_AVAILABLE = True
except ImportError:
    WINSHELL_AVAILABLE = False

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Paths
if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    if os.path.exists(os.path.join(EXE_DIR, "img")):
        BASE_DIR = EXE_DIR
    elif hasattr(sys, '_MEIPASS') and os.path.exists(os.path.join(sys._MEIPASS, "img")):
        BASE_DIR = sys._MEIPASS
    else:
        BASE_DIR = EXE_DIR
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALASTOR_DIR = os.path.join(BASE_DIR, "img", "794")
SHIMEJI_DIR = os.path.join(BASE_DIR, "img", "Shimeji")

if os.path.exists(ALASTOR_DIR):
    IMG_DIR = ALASTOR_DIR
else:
    IMG_DIR = SHIMEJI_DIR

ACTIONS_FILE = os.path.join(BASE_DIR, "Actions.xml")
BEHAVIORS_FILE = os.path.join(BASE_DIR, "Behaviors.xml")
APPS_CONFIG_FILE = os.path.join(BASE_DIR, "apps_config.json")
VOICE_SETTINGS_FILE = os.path.join(BASE_DIR, "voice_settings.json")
AI_CONFIG_FILE = os.path.join(BASE_DIR, "ai_config.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")

# Automatically populate os.environ from .env if present
if os.path.exists(ENV_FILE):
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    _k = _k.strip()
                    _v = _v.strip().strip("'\"")
                    if _k not in os.environ:
                        os.environ[_k] = _v
    except Exception:
        pass

if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
elif os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]



# Dimensions and Timing
SIZE = 128
FPS = 30
DELAY = int(1000 / FPS)

# Physics Surfaces
SURFACE_FLOOR = "floor"
SURFACE_WALL_L = "wall_left"
SURFACE_WALL_R = "wall_right"
SURFACE_CEILING = "ceiling"
