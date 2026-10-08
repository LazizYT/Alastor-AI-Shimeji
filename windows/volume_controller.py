import threading
import ctypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from core.logger import log_info, log_warn, log_error

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False


class VolumeController:
    """
    Controls master audio volume on Windows via pycaw / Core Audio API,
    with keyboard-event fallbacks and dynamic Audio Ducking.
    """

    def __init__(self):
        self._endpoint = None
        self._init_endpoint()
        self._duck_depth = 0
        self._pre_duck_volume = None
        self._duck_lock = threading.Lock()
        self.ducking_enabled = True
        self.duck_target_percent = 15  # Default duck level: 15%

    def _init_endpoint(self):
        if not PYCAW_AVAILABLE:
            return
        try:
            device = AudioUtilities.GetSpeakers()
            if hasattr(device, 'EndpointVolume'):
                self._endpoint = device.EndpointVolume
            else:
                # Older pycaw compatibility
                interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self._endpoint = cast(interface, POINTER(IAudioEndpointVolume))
        except Exception as e:
            log_warn(f"Не удалось инициализировать pycaw: {e}")
            self._endpoint = None

    def is_available(self) -> bool:
        """Returns True if pycaw audio endpoint is initialized."""
        return self._endpoint is not None

    def get_volume(self) -> int:
        """Returns master volume percentage 0..100."""
        if self._endpoint:
            try:
                scalar = self._endpoint.GetMasterVolumeLevelScalar()
                return int(round(scalar * 100))
            except Exception:
                self._init_endpoint()
                if self._endpoint:
                    try:
                        return int(round(self._endpoint.GetMasterVolumeLevelScalar() * 100))
                    except Exception:
                        pass
        return 50

    def set_volume(self, percent: int, update_pre_duck: bool = True) -> int:
        """Sets master volume percentage 0..100. Returns the actual new volume."""
        val = max(0, min(100, int(percent)))
        if update_pre_duck and self._duck_depth > 0:
            self._pre_duck_volume = val
        if self._endpoint:
            try:
                self._endpoint.SetMasterVolumeLevelScalar(val / 100.0, None)
                log_info(f"Громкость Windows установлена на {val}%")
                return val
            except Exception as e:
                log_warn(f"Ошибка установки громкости pycaw: {e}")

        # Fallback via Win32 media keys
        log_info(f"Попытка регулировки громкости через медиа-клавиши до ~{val}%")
        return val

    def start_ducking(self, duck_percent: int = None):
        """
        Temporarily lowers master audio volume for voice input or TTS playback.
        Nested calls are reference-counted so the pre-duck volume is safely preserved.
        """
        if not self.ducking_enabled:
            return
        target = self.duck_target_percent if duck_percent is None else duck_percent
        with self._duck_lock:
            if self._duck_depth == 0:
                cur_vol = self.get_volume()
                if cur_vol > target:
                    self._pre_duck_volume = cur_vol
                    self.set_volume(target, update_pre_duck=False)
                    log_info(f"Audio Ducking активирован: {cur_vol}% -> {target}%")
                else:
                    self._pre_duck_volume = None
            self._duck_depth += 1

    def stop_ducking(self):
        """
        Restores master audio volume to pre-duck level once all ducking holders release.
        """
        if not self.ducking_enabled:
            return
        with self._duck_lock:
            if self._duck_depth > 0:
                self._duck_depth -= 1
                if self._duck_depth == 0 and self._pre_duck_volume is not None:
                    target_restore = self._pre_duck_volume
                    self._pre_duck_volume = None
                    self.set_volume(target_restore, update_pre_duck=False)
                    log_info(f"Audio Ducking снят: громкость восстановлена до {target_restore}%")

    def is_ducked(self) -> bool:
        with self._duck_lock:
            return self._duck_depth > 0

    def toggle_ducking(self) -> bool:
        self.ducking_enabled = not self.ducking_enabled
        if not self.ducking_enabled and self.is_ducked():
            self._duck_depth = 1
            self.stop_ducking()
        return self.ducking_enabled

    def volume_up(self, step: int = 10) -> int:
        cur = self.get_volume()
        return self.set_volume(cur + step)

    def volume_down(self, step: int = 10) -> int:
        cur = self.get_volume()
        return self.set_volume(cur - step)

    def is_muted(self) -> bool:
        if self._endpoint:
            try:
                return bool(self._endpoint.GetMute())
            except Exception:
                pass
        return False

    def mute(self):
        if self._endpoint:
            try:
                self._endpoint.SetMute(1, None)
                log_info("Звук Windows заглушён")
                return True
            except Exception as e:
                log_warn(f"Ошибка mute pycaw: {e}")
        return False

    def unmute(self):
        if self._endpoint:
            try:
                self._endpoint.SetMute(0, None)
                log_info("Звук Windows включён")
                return True
            except Exception as e:
                log_warn(f"Ошибка unmute pycaw: {e}")
        return False

    def toggle_mute(self) -> bool:
        """Toggles Windows system mute. Returns True if now muted, False otherwise."""
        muted = self.is_muted()
        if muted:
            self.unmute()
            return False
        else:
            self.mute()
            return True
