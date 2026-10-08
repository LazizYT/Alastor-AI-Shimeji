import io
import re
import wave
import numpy as np
from core.config import SR_AVAILABLE
from core.logger import log_voice

if SR_AVAILABLE:
    import speech_recognition as sr

_whisper_model = None

# Known Whisper hallucinations on silence or background noise
WHISPER_HALLUCINATIONS = [
    "динамичная музыка",
    "музыкальная заставка",
    "редактор субтитров",
    "корректор",
    "субтитры",
    "аплодисменты",
    "смех",
    "продолжение следует",
    "спасибо за просмотр",
    "ставьте лайк",
    "подписывайтесь на канал",
    "до скорой встречи",
]

def is_hallucination(text: str) -> bool:
    if not text:
        return True
    low = text.lower().strip()
    # Check if text is enclosed in brackets or music cues e.g. [Музыка], (Музыка)
    if re.match(r'^[\[\(\{].*[\]\)\}]$', low):
        return True
    for h in WHISPER_HALLUCINATIONS:
        if h in low:
            return True
    return False

def transcribe_audio(audio_data, sample_rate: int = 16000) -> str:
    global _whisper_model

    # Check for silence/low amplitude before running heavy models
    if audio_data is not None and len(audio_data) > 0:
        max_amp = float(np.max(np.abs(audio_data)))
        rms = float(np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)))
        if max_amp < 35 and rms < 10:
            log_voice(f"Запись абсолютной тишины отброшена (max_amp={max_amp:.0f}, rms={rms:.1f})")
            return ""

    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    wav_io.seek(0)

    recognized_text = None

    # 1. Quick cloud STT via speech_recognition (Google Free RU)
    if SR_AVAILABLE:
        try:
            r = sr.Recognizer()
            with sr.AudioFile(wav_io) as source:
                audio = r.record(source)
            text = r.recognize_google(audio, language="ru-RU")
            if text and not is_hallucination(text):
                recognized_text = text
        except Exception:
            pass

    # 2. Local fallback via faster_whisper with Silero VAD
    if not recognized_text:
        try:
            import faster_whisper
            if _whisper_model is None:
                _whisper_model = faster_whisper.WhisperModel("tiny", device="cpu", compute_type="int8")
            wav_io.seek(0)
            segs, _ = _whisper_model.transcribe(
                wav_io,
                language="ru",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400),
                no_speech_threshold=0.5
            )
            raw = " ".join([s.text.strip() for s in segs]).strip()
            if raw and not is_hallucination(raw):
                recognized_text = raw
            elif raw and is_hallucination(raw):
                log_voice(f"Отброшена галлюцинация Whisper: «{raw}»")
        except Exception:
            pass

    return recognized_text.strip() if recognized_text else ""

