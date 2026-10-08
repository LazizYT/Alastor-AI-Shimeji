import os
import sys
import time
import threading
from collections import deque
from core.config import BASE_DIR

LOG_FILE = os.path.join(BASE_DIR, "alastor.log")
_LOG_LOCK = threading.Lock()
_LOG_BUFFER = deque(maxlen=500)

def _format_time():
    return time.strftime("%H:%M:%S")

def _write_entry(level: str, message: str):
    timestamp = _format_time()
    date_str = time.strftime("%Y-%m-%d")
    entry = {
        "time": timestamp,
        "date": date_str,
        "level": level.upper(),
        "message": str(message).strip()
    }
    line = f"[{date_str} {timestamp}] [{entry['level']}] {entry['message']}\n"

    with _LOG_LOCK:
        _LOG_BUFFER.append(entry)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

def log_info(message: str):
    _write_entry("INFO", message)

def log_voice(message: str):
    _write_entry("VOICE", message)

def log_ai(message: str):
    _write_entry("AI", message)

def log_warn(message: str):
    _write_entry("WARN", message)

def log_error(message: str):
    _write_entry("ERROR", message)

def get_recent_logs() -> list:
    with _LOG_LOCK:
        return list(_LOG_BUFFER)

def clear_logs():
    with _LOG_LOCK:
        _LOG_BUFFER.clear()
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Журнал очищен.\n")
        except Exception:
            pass

def get_log_filepath() -> str:
    return LOG_FILE

# Write initial startup log
log_info("Инициализация подсистемы логирования Alastor Shimeji")
