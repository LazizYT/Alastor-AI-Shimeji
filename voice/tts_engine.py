import os
import io
import re
import json
import hashlib
import asyncio
import threading
import numpy as np

from core.config import SOUNDDEVICE_AVAILABLE, VOICE_SETTINGS_FILE
from core.logger import log_voice, log_error, log_info
from voice.radio_dsp import RadioDSP, DSP_PROFILES

_EDGE_TTS_AVAILABLE = False
try:
    import edge_tts
    import soundfile as sf
    _EDGE_TTS_AVAILABLE = True
except ImportError:
    pass

if SOUNDDEVICE_AVAILABLE:
    import sounddevice as sd

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

from voice.tts_presets import DEFAULT_SETTINGS, VOICE_PRESETS

class RadioTTSEngine:
    """
    Edge-TTS voice generator with 1930s Radio Demon DSP pipeline,
    customizable voice profiles & live presets, persistent disk pre-caching,
    and Barge-in interruption.
    """
    def __init__(self, voice: str = "ru-RU-DmitryNeural", enabled: bool = True):
        self.dsp = RadioDSP()
        self._ram_cache = {}
        self._cache_lock = threading.Lock()
        self._current_task_id = 0
        self._lock = threading.Lock()
        self._is_playing = False
        self.on_playback_start = None
        self.on_playback_end = None

        # Load persisted settings or initialize defaults
        self.settings = self._load_settings()
        if not enabled:
            self.settings["enabled"] = False
        self._apply_internal_settings(self.settings)

        # Preload disk cache into RAM in background for instant playback
        threading.Thread(target=self._preload_disk_cache, daemon=True).start()

    def _load_settings(self) -> dict:
        data = dict(DEFAULT_SETTINGS)
        if os.path.exists(VOICE_SETTINGS_FILE):
            try:
                with open(VOICE_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    data.update(saved)
            except Exception as e:
                log_error(f"Не удалось прочитать voice_settings.json: {e}")
        else:
            self._save_raw_settings(data)
        return data

    def _save_raw_settings(self, data: dict):
        try:
            with open(VOICE_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_error(f"Ошибка сохранения voice_settings.json: {e}")

    def _apply_internal_settings(self, s: dict):
        self.voice = s.get("voice", DEFAULT_SETTINGS["voice"])
        self.rate = s.get("rate", DEFAULT_SETTINGS["rate"])
        self.pitch = s.get("pitch", DEFAULT_SETTINGS["pitch"])
        self.enabled = s.get("enabled", DEFAULT_SETTINGS["enabled"])
        self.dsp_enabled = s.get("dsp_enabled", DEFAULT_SETTINGS["dsp_enabled"])
        self.filter_profile = s.get("filter_profile", DEFAULT_SETTINGS["filter_profile"])
        self.demon_layer = s.get("demon_layer", DEFAULT_SETTINGS["demon_layer"])
        self.add_vinyl = s.get("add_vinyl", DEFAULT_SETTINGS["add_vinyl"])
        self.vinyl_intensity = float(s.get("vinyl_intensity", DEFAULT_SETTINGS["vinyl_intensity"]))

        self.dsp.update_settings(
            profile_key=self.filter_profile,
            highpass_hz=s.get("highpass_hz", DEFAULT_SETTINGS["highpass_hz"]),
            lowpass_hz=s.get("lowpass_hz", DEFAULT_SETTINGS["lowpass_hz"]),
            drive_db=s.get("drive_db", DEFAULT_SETTINGS["drive_db"]),
            enabled=self.dsp_enabled,
            vinyl_intensity=self.vinyl_intensity,
            demon_layer=self.demon_layer
        )

    def apply_settings(self, new_settings: dict, save: bool = True):
        """Update active engine parameters on the fly."""
        with self._lock:
            self.settings.update(new_settings)
            self._apply_internal_settings(self.settings)
        if save:
            self._save_raw_settings(self.settings)
            log_info(f"Настройки голоса обновлены: Голос={self.voice}, Фильтр={self.filter_profile}, Дубль={self.demon_layer}")

    def get_current_settings(self) -> dict:
        return dict(self.settings)

    def reset_to_preset(self, preset_key: str):
        if preset_key in VOICE_PRESETS:
            preset_data = dict(VOICE_PRESETS[preset_key])
            preset_data.pop("title", None)
            self.apply_settings(preset_data, save=True)

    def is_available(self) -> bool:
        return _EDGE_TTS_AVAILABLE and SOUNDDEVICE_AVAILABLE

    @property
    def is_muted(self) -> bool:
        return not self.enabled

    @is_muted.setter
    def is_muted(self, val: bool):
        self.enabled = not val
        self.settings["enabled"] = not val

    def mute(self):
        self.stop_speech()
        self.apply_settings({"enabled": False}, save=True)
        log_info("Голос Аластора заглушён (Mute)")

    def unmute(self):
        self.apply_settings({"enabled": True}, save=True)
        log_info("Голос Аластора включён (Unmute)")

    def toggle_mute(self) -> bool:
        """Toggles mute state. Returns True if now muted, False if unmuted."""
        if self.is_muted:
            self.unmute()
            return False
        else:
            self.mute()
            return True

    def stop_speech(self):
        """Barge-in: Immediately stops any ongoing speech output."""
        was_playing = False
        with self._lock:
            self._current_task_id += 1
            if SOUNDDEVICE_AVAILABLE:
                try:
                    sd.stop()
                except Exception:
                    pass
            was_playing = self._is_playing
            self._is_playing = False
        if was_playing and self.on_playback_end:
            try:
                self.on_playback_end()
            except Exception:
                pass

    def is_speaking(self) -> bool:
        return self._is_playing

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def _is_default_canon(self) -> bool:
        canon = VOICE_PRESETS["alastor_canon"]
        return (
            self.voice == canon["voice"] and
            self.rate == canon["rate"] and
            self.pitch == canon["pitch"] and
            self.dsp_enabled and
            self.filter_profile == canon["filter_profile"] and
            self.demon_layer == canon["demon_layer"] and
            abs(self.dsp.highpass_hz - canon["highpass_hz"]) < 5 and
            abs(self.dsp.lowpass_hz - canon["lowpass_hz"]) < 5 and
            abs(self.dsp.drive_db - canon["drive_db"]) < 0.5
        )

    def _get_cache_path(self, clean_text: str) -> str:
        canon_key = hashlib.md5(clean_text.encode('utf-8')).hexdigest()
        canon_path = os.path.join(CACHE_DIR, f"{canon_key}.wav")
        if self._is_default_canon():
            return canon_path

        fingerprint = f"{clean_text}_{self.voice}_{self.rate}_{self.pitch}_{self.dsp_enabled}_{self.filter_profile}_{self.demon_layer}_{self.dsp.highpass_hz}_{self.dsp.lowpass_hz}_{self.dsp.drive_db}_{self.add_vinyl}_{self.vinyl_intensity}"
        custom_key = hashlib.md5(fingerprint.encode('utf-8')).hexdigest()
        custom_path = os.path.join(CACHE_DIR, f"{custom_key}.wav")

        if os.path.exists(custom_path):
            return custom_path
        if os.path.exists(canon_path):
            return canon_path
        return custom_path

    def _preload_disk_cache(self):
        """Pre-load existing WAV files from disk into memory for zero latency."""
        if not _EDGE_TTS_AVAILABLE:
            return
        loaded = 0
        try:
            for fname in os.listdir(CACHE_DIR):
                if fname.endswith(".wav"):
                    fpath = os.path.join(CACHE_DIR, fname)
                    try:
                        audio, sr = sf.read(fpath)
                        key = os.path.splitext(fname)[0]
                        with self._cache_lock:
                            self._ram_cache[key] = (audio, sr)
                        loaded += 1
                    except Exception:
                        pass
            if loaded > 0:
                log_info(f"Загружено {loaded} предварительно подготовленных радио-фраз Аластора")
        except Exception:
            pass

    def speak(self, text: str):
        """Synthesize and play speech in a background thread."""
        if not self.enabled or not self.is_available():
            return
        if not text or not text.strip():
            return

        clean_text = self._sanitize_text(text)
        if not clean_text:
            return

        self.stop_speech()

        with self._lock:
            task_id = self._current_task_id

        disk_path = self._get_cache_path(clean_text)
        key = os.path.splitext(os.path.basename(disk_path))[0]

        # 1. Check RAM Cache (0 ms)
        with self._cache_lock:
            cached = self._ram_cache.get(key)
        if cached is not None:
            audio, sr = cached
            self._play_audio(audio, sr, task_id)
            return

        # 2. Check Disk Cache (0-2 ms)
        if os.path.exists(disk_path):
            try:
                audio, sr = sf.read(disk_path)
                with self._cache_lock:
                    self._ram_cache[key] = (audio, sr)
                self._play_audio(audio, sr, task_id)
                return
            except Exception:
                pass

        # 3. Generate via Edge-TTS and DSP pipeline
        threading.Thread(
            target=self._synthesize_and_play,
            args=(clean_text, task_id, key, disk_path, self.voice, self.rate, self.pitch, self.add_vinyl),
            daemon=True
        ).start()

    def test_sample(self, text: str, custom_settings: dict = None, on_finish = None):
        """Synthesizes and plays a live audio sample for configuration testing."""
        if not self.is_available():
            return

        clean_text = self._sanitize_text(text)
        if not clean_text:
            return

        self.stop_speech()
        with self._lock:
            task_id = self._current_task_id

        s = dict(self.settings)
        if custom_settings:
            s.update(custom_settings)

        v_name = s.get("voice", self.voice)
        v_rate = s.get("rate", self.rate)
        v_pitch = s.get("pitch", self.pitch)
        v_dsp_en = s.get("dsp_enabled", self.dsp_enabled)
        v_prof = s.get("filter_profile", self.filter_profile)
        v_demon = s.get("demon_layer", self.demon_layer)
        v_vinyl = s.get("add_vinyl", self.add_vinyl)
        v_int = float(s.get("vinyl_intensity", self.vinyl_intensity))
        v_hp = float(s.get("highpass_hz", self.dsp.highpass_hz))
        v_lp = float(s.get("lowpass_hz", self.dsp.lowpass_hz))
        v_dr = float(s.get("drive_db", self.dsp.drive_db))

        temp_dsp = RadioDSP(
            profile_key=v_prof,
            highpass_hz=v_hp,
            lowpass_hz=v_lp,
            drive_db=v_dr,
            enabled=v_dsp_en,
            vinyl_intensity=v_int,
            demon_layer=v_demon
        )

        def _worker():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                communicate = edge_tts.Communicate(clean_text, v_name, rate=v_rate, pitch=v_pitch)
                mp3_data = bytearray()
                async def _read():
                    async for chunk in communicate.stream():
                        if chunk['type'] == 'audio':
                            mp3_data.extend(chunk['data'])
                loop.run_until_complete(_read())
                loop.close()

                if not mp3_data:
                    return

                with self._lock:
                    if task_id != self._current_task_id:
                        return

                audio, sr = sf.read(io.BytesIO(mp3_data))
                processed = temp_dsp.process(audio, sr, add_vinyl=v_vinyl)

                self._play_audio(processed, sr, task_id)
            except Exception as e:
                log_error(f"Ошибка тестового синтеза: {e}")
            finally:
                if on_finish:
                    try:
                        on_finish()
                    except Exception:
                        pass

        threading.Thread(target=_worker, daemon=True).start()

    def _sanitize_text(self, text: str) -> str:
        cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        cleaned = re.sub(r'\([^\)]*\)', '', cleaned)
        cleaned = re.sub(r'[*_#`~]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def _synthesize_local_sapi5(self, text: str) -> tuple[np.ndarray, int] | None:
        """Instant offline fallback using Windows SAPI5 (300 ms)."""
        try:
            import win32com.client
            import tempfile
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            for i in range(voice.GetVoices().Count):
                v = voice.GetVoices().Item(i)
                desc = v.GetDescription().lower()
                if "russian" in desc or "irina" in desc:
                    voice.Voice = v
                    break
            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            stream.Open(tmp_path, 3, False)
            voice.AudioOutputStream = stream
            voice.Speak(text)
            stream.Close()
            audio, sr = sf.read(tmp_path)
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            return audio, sr
        except Exception as e:
            log_error(f"SAPI5 fallback error: {e}")
            return None

    def _fetch_fish_audio_tts(self, text: str, model_id: str, api_key: str) -> bytes | None:
        """Calls Fish Audio cloud TTS API."""
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "reference_id": model_id,
                "format": "mp3"
            }
            r = requests.post("https://api.fish.audio/v1/tts", headers=headers, json=payload, timeout=8)
            if r.status_code == 200 and len(r.content) > 0:
                log_voice("Синтез речи через Fish Audio выполнен успешно!")
                return r.content
            elif r.status_code == 402:
                log_voice("Fish Audio: недостаточно кредитов (402 Payment Required). Переход на Edge-TTS...")
            else:
                log_voice(f"Fish Audio вернул статус {r.status_code}")
            return None
        except Exception as e:
            log_voice(f"Fish Audio сетевая ошибка ({e}), переход на Edge-TTS...")
            return None

    def _synthesize_and_play(self, text: str, task_id: int, key: str, disk_path: str,
                             voice: str, rate: str, pitch: str, add_vinyl: bool):
        audio = None
        sr = 24000

        # 0. Attempt Fish Audio if API key is present and use_fish_audio is True
        fish_key = os.environ.get("FISH_AUDIO_API_KEY") or os.environ.get("Fish_audio")
        fish_model = self.settings.get("fish_audio_model_id")
        if fish_key and fish_model and self.settings.get("use_fish_audio", False):
            fish_bytes = self._fetch_fish_audio_tts(text, fish_model, fish_key)
            if fish_bytes:
                try:
                    audio, sr = sf.read(io.BytesIO(fish_bytes))
                except Exception:
                    pass

        # 1. Attempt Edge-TTS with strict 3.5s timeout
        if audio is None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_bytes = loop.run_until_complete(self._fetch_edge_tts(text, voice, rate, pitch))
                loop.close()
                if audio_bytes:
                    audio, sr = sf.read(io.BytesIO(audio_bytes))
            except Exception as e:
                log_voice(f"Edge-TTS недоступен или задержка сети ({e}). Мгновенный переход на локальный SAPI5...")

        # 2. Instant offline fallback if Edge-TTS timed out or failed
        if audio is None:
            sapi_res = self._synthesize_local_sapi5(text)
            if sapi_res is not None:
                audio, sr = sapi_res

        if audio is None:
            log_error(f"Не удалось синтезировать речь для: {text[:40]}")
            return

        with self._lock:
            if task_id != self._current_task_id:
                return

        processed = self.dsp.process(audio, sr, add_vinyl=add_vinyl)

        try:
            sf.write(disk_path, processed, sr)
        except Exception:
            pass

        with self._cache_lock:
            self._ram_cache[key] = (processed, sr)

        self._play_audio(processed, sr, task_id)

    async def _fetch_edge_tts(self, text: str, voice: str, rate: str, pitch: str) -> bytearray:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, connect_timeout=3, receive_timeout=4)
        mp3_data = bytearray()
        async def _stream():
            async for chunk in communicate.stream():
                if chunk['type'] == 'audio':
                    mp3_data.extend(chunk['data'])
        await asyncio.wait_for(_stream(), timeout=4.0)
        return mp3_data

    def _play_audio(self, audio: np.ndarray, sample_rate: int, task_id: int):
        with self._lock:
            if task_id != self._current_task_id:
                return
            self._is_playing = True

        if self.on_playback_start:
            try:
                self.on_playback_start()
            except Exception:
                pass

        log_voice(f"Радио-демон в эфире: {len(audio) / sample_rate:.1f} сек")
        try:
            sd.play(audio, sample_rate)
            threading.Thread(
                target=self._wait_playback,
                args=(len(audio) / sample_rate, task_id),
                daemon=True
            ).start()
        except Exception as e:
            log_error(f"Ошибка воспроизведения звука: {e}")
            self._is_playing = False
            if self.on_playback_end:
                try:
                    self.on_playback_end()
                except Exception:
                    pass

    def _wait_playback(self, duration: float, task_id: int):
        import time
        time.sleep(duration)
        with self._lock:
            if task_id == self._current_task_id:
                self._is_playing = False
                if self.on_playback_end:
                    try:
                        self.on_playback_end()
                    except Exception:
                        pass
