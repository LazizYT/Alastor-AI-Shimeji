import os
import re
import time
import queue
import collections
import threading
import numpy as np
from core.config import SOUNDDEVICE_AVAILABLE
from core.logger import log_info, log_voice, log_warn, log_error
from voice.speech_to_text import transcribe_audio

if SOUNDDEVICE_AVAILABLE:
    import sounddevice as sd


class WakeWordDetector:
    """
    Continuous background listener for wake-word 'Аластор' / 'Alastor' and phonetic variants.
    Operates with low CPU footprint using a non-blocking streaming audio queue and adaptive RMS VAD.
    
    When wake-word is detected:
      - If followed by a command (e.g. 'Аластор, закрой VS Code', 'Аластор, смотри на мой экран'),
        immediately dispatches it to the mascot's unified command handler.
      - If solitary ('Аластор'), prompts with 'Слушаю вас!' and opens the microphone for speech.
    """

    def __init__(self, mascot_ref=None, sample_rate: int = 16000):
        self.mascot = mascot_ref
        self.sample_rate = sample_rate
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._stream = None
        self._audio_queue = queue.Queue()
        self._lock = threading.Lock()

    def is_running(self) -> bool:
        return self._running

    def _audio_callback(self, indata, frames, time_info, status):
        """Ultra-fast non-blocking PortAudio callback pushing incoming audio blocks to queue."""
        if self._running and not self._stop_event.is_set():
            self._audio_queue.put(indata.copy())

    def start(self):
        with self._lock:
            if self._running:
                return
            if not SOUNDDEVICE_AVAILABLE:
                log_warn("WakeWordDetector: sounddevice недоступен, фоновый триггер отключён")
                return
            self._running = True
            self._stop_event.clear()
            # Drain any stale audio
            while not self._audio_queue.empty():
                try:
                    self._audio_queue.get_nowait()
                except queue.Empty:
                    break
            self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="AlastorWakeWordThread")
            self._thread.start()
            log_info("Фоновый непрерывный детектор триггер-слова «Аластор» запущен")

    def stop(self):
        with self._lock:
            if not self._running:
                return
            self._running = False
            self._stop_event.set()
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        log_info("Фоновый детектор триггер-слова «Аластор» остановлен")

    def _listen_loop(self):
        # 100ms blocks at 16kHz = 1600 samples
        block_samples = int(self.sample_rate * 0.1)

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                blocksize=block_samples,
                callback=self._audio_callback
            )
            self._stream.start()
        except Exception as e:
            log_error(f"Не удалось открыть InputStream для WakeWordDetector: {e}")
            self._running = False
            return

        ambient_baseline = 25.0
        # Rolling pre-speech buffer (retains last 0.5s of audio so the word onset is never clipped)
        pre_speech_blocks = collections.deque(maxlen=5)
        speech_blocks = []
        is_speech_active = False
        silence_after_speech = 0
        cooldown_until = 0.0

        while self._running and not self._stop_event.is_set():
            try:
                try:
                    block = self._audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if not self._running or self._stop_event.is_set():
                    break

                now = time.time()
                if now < cooldown_until:
                    pre_speech_blocks.clear()
                    speech_blocks.clear()
                    is_speech_active = False
                    silence_after_speech = 0
                    continue

                # Skip listening while mascot is actively speaking or recording
                if self.mascot:
                    if getattr(self.mascot, '_is_recording', False):
                        pre_speech_blocks.clear()
                        speech_blocks.clear()
                        is_speech_active = False
                        silence_after_speech = 0
                        time.sleep(0.1)
                        continue
                    tts = getattr(self.mascot, 'tts', None)
                    if tts and getattr(tts, 'is_speaking', lambda: False)():
                        pre_speech_blocks.clear()
                        speech_blocks.clear()
                        is_speech_active = False
                        silence_after_speech = 0
                        time.sleep(0.1)
                        continue

                # Energy & RMS computation
                float_block = block.flatten().astype(np.float32)
                rms = float(np.sqrt(np.mean(float_block ** 2)))
                max_amp = float(np.max(np.abs(block)))

                # Dynamic room noise baseline calibration during quiet periods
                if not is_speech_active and rms < ambient_baseline * 1.3:
                    ambient_baseline = 0.95 * ambient_baseline + 0.05 * rms

                trigger_threshold = max(35.0, ambient_baseline * 1.45)

                if rms >= trigger_threshold and max_amp >= 60:
                    # Voice activity detected
                    if not is_speech_active:
                        is_speech_active = True
                        speech_blocks = list(pre_speech_blocks)
                        speech_blocks.append(block.flatten())
                        silence_after_speech = 0
                    else:
                        speech_blocks.append(block.flatten())
                        silence_after_speech = 0
                else:
                    # Silence or low background noise
                    if not is_speech_active:
                        pre_speech_blocks.append(block.flatten())
                    else:
                        speech_blocks.append(block.flatten())
                        silence_after_speech += 1

                        # Endpointing check: 0.5s pause after speech (5 blocks) or max length reached (~4.0s = 40 blocks)
                        total_blocks = len(speech_blocks)
                        if silence_after_speech >= 5 or total_blocks >= 40:
                            if total_blocks >= 5:
                                full_audio = np.concatenate(speech_blocks)
                                is_speech_active = False
                                speech_blocks.clear()
                                pre_speech_blocks.clear()
                                silence_after_speech = 0

                                # Process utterance asynchronously to keep audio stream responsive
                                threading.Thread(
                                    target=self._process_utterance,
                                    args=(full_audio, rms),
                                    daemon=True
                                ).start()
                                cooldown_until = time.time() + 1.2
                            else:
                                # Too short (click, breath, bump) -> discard
                                is_speech_active = False
                                speech_blocks.clear()
                                silence_after_speech = 0

            except Exception as e:
                log_warn(f"Ошибка в цикле WakeWordDetector: {e}")
                time.sleep(0.1)

    def _process_utterance(self, audio_data: np.ndarray, rms: float):
        try:
            if self.mascot:
                if getattr(self.mascot, '_is_recording', False):
                    return
                tts = getattr(self.mascot, 'tts', None)
                if tts and getattr(tts, 'is_speaking', lambda: False)():
                    return

            text = transcribe_audio(audio_data, sample_rate=self.sample_rate)
            if not text:
                return

            low = text.lower().strip()
            log_voice(f"[Триггер-слушатель] Распознано в эфире: «{text}» (RMS={rms:.1f})")

            # Check for wake word variations (Russian phonetic transcribing variations + English)
            wake_pattern = r'\b(?:ал[аоеи]ст[оеа]р[а-я]*|а\s+ла\s*стор|алистар|аластер|алистер|alastor[a-z]*|alaster[a-z]*)\b'
            wake_match = re.search(wake_pattern, low)
            if not wake_match:
                return

            log_info(f"⚡ ТРИГГЕР-СЛОВО «АЛАСТОР» ОБНАРУЖЕНО: «{text}»")

            # Extract remainder after the wake word
            remainder_pattern = r'^(?:.*?\b(?:ал[аоеи]ст[оеа]р[а-я]*|а\s+ла\s*стор|алистар|аластер|алистер|alastor[a-z]*|alaster[a-z]*)\b[,\s:\-]*)'
            cmd_remainder = re.sub(remainder_pattern, '', text, flags=re.IGNORECASE).strip()

            if cmd_remainder and len(cmd_remainder) > 1:
                log_info(f"Прямая команда по триггер-слову: «{cmd_remainder}»")
                if self.mascot and hasattr(self.mascot, 'handle_recognized_speech'):
                    self.mascot.root.after(0, lambda: self.mascot.handle_recognized_speech(cmd_remainder))
            else:
                log_info("Одиночное триггер-слово «Аластор» — приглашение к диалогу")
                if self.mascot:
                    self.mascot.root.after(0, lambda: self.mascot.show_speech(
                        "🎙️ В эфире! Слушаю вас, мой друг! 📻",
                        play_audio=True
                    ))
                    self.mascot.root.after(800, self.mascot.start_voice_capture)

        except Exception as e:
            log_warn(f"Ошибка обработки фразы триггера: {e}")
