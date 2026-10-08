import numpy as np
from core.config import SOUNDDEVICE_AVAILABLE

if SOUNDDEVICE_AVAILABLE:
    import sounddevice as sd

def record_audio(duration: float = 4.5, sample_rate: int = 16000, silence_timeout: float = 0.85, min_duration: float = 1.0):
    """
    Records audio from default microphone with dynamic Voice Activity Detection (VAD).
    Terminates early once speech has concluded and a silence interval is observed,
    dramatically reducing latency.
    """
    if not SOUNDDEVICE_AVAILABLE:
        raise RuntimeError("sounddevice не доступен в системе!")

    chunk_duration = 0.1  # 100ms
    chunk_samples = int(chunk_duration * sample_rate)
    max_chunks = int(duration / chunk_duration)
    min_chunks = int(min_duration / chunk_duration)
    silence_limit_chunks = int(silence_timeout / chunk_duration)

    recorded_chunks = []
    speech_detected = False
    consecutive_silence = 0
    ambient_samples = []

    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
            # Baseline calibration (first 2 chunks, 200ms)
            for _ in range(2):
                chunk, _ = stream.read(chunk_samples)
                recorded_chunks.append(chunk)
                ambient_samples.append(float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2))))

            ambient_baseline = float(np.mean(ambient_samples)) if ambient_samples else 20.0
            noise_threshold = max(32.0, ambient_baseline * 1.45)

            for _ in range(max_chunks - 2):
                chunk, _ = stream.read(chunk_samples)
                recorded_chunks.append(chunk)

                rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
                if rms > noise_threshold:
                    speech_detected = True
                    consecutive_silence = 0
                else:
                    if speech_detected:
                        consecutive_silence += 1
                        if consecutive_silence >= silence_limit_chunks and len(recorded_chunks) >= min_chunks:
                            # User stopped talking, return immediately
                            break

        if recorded_chunks:
            return np.concatenate(recorded_chunks, axis=0)
    except Exception:
        # Fallback to standard blocking record if stream fails
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        return audio_data

    return np.zeros((int(duration * sample_rate), 1), dtype='int16')

