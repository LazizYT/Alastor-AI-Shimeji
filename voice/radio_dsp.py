import numpy as np

_PEDALBOARD_AVAILABLE = False
try:
    from pedalboard import (
        Pedalboard, HighpassFilter, LowpassFilter, Distortion, Gain,
        PitchShift, Delay, Reverb, Bitcrush, PeakFilter, Compressor,
        LowShelfFilter, HighShelfFilter
    )
    _PEDALBOARD_AVAILABLE = True
except ImportError:
    pass

_SCIPY_AVAILABLE = False
try:
    import scipy.signal
    from scipy.signal import resample_poly
    _SCIPY_AVAILABLE = True
except ImportError:
    pass

from voice.dsp_profiles import DSP_PROFILES

class RadioDSP:
    """
    Advanced vintage radio and studio vocal processor with Alastor's
    signature demonic doubling layer, tremolo flutter, and vacuum tube rasp.
    """
    def __init__(self, profile_key: str = "canon_radio",
                 highpass_hz: float = 350.0, lowpass_hz: float = 3800.0,
                 drive_db: float = 6.0, enabled: bool = True,
                 vinyl_intensity: float = 1.0,
                 demon_layer: bool = True):
        self.profile_key = profile_key
        self.highpass_hz = float(highpass_hz)
        self.lowpass_hz = float(lowpass_hz)
        self.drive_db = float(drive_db)
        self.enabled = enabled
        self.vinyl_intensity = float(vinyl_intensity)
        self.demon_layer = demon_layer
        self.board = None
        self._rebuild_board()

    @staticmethod
    def alastor_layer(audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Signature Hazbin Hotel Alastor voice processing:
        1. Demonic double: pitch down ~4 semitones + 12ms Haas delay shift
        2. Subtle 5.5 Hz radio tremolo flutter
        3. Non-linear soft clipping (tanh) for vocal rasp and saturation
        """
        if len(audio) == 0:
            return audio
        try:
            # 1. «Демонический» дубль: питч вниз на ~4 полутона + сдвиг ~12 мс
            ratio = 2 ** (-4 / 12)
            if _SCIPY_AVAILABLE:
                low = resample_poly(audio, 1000, int(1000 * ratio))
            else:
                new_len = max(1, int(len(audio) * ratio))
                low = np.interp(np.linspace(0, len(audio) - 1, new_len), np.arange(len(audio)), audio)

            low = np.interp(np.linspace(0, len(low) - 1, len(audio)),
                            np.arange(len(low)), low)  # выравниваем длину
            shift = int(sr * 0.012)
            low = np.concatenate([np.zeros(shift), low])[:len(audio)]
            mixed = audio + 0.18 * low

            # 2. Лёгкое тремоло 5.5 Гц
            t = np.arange(len(mixed)) / sr
            mixed *= (1.0 + 0.025 * np.sin(2 * np.pi * 5.5 * t))

            # 3. Мягкий клиппинг (tanh) для хрипотцы
            mixed = np.tanh(mixed * 1.8) / np.tanh(1.8)

            # нормализация
            peak = np.max(np.abs(mixed)) or 1.0
            return (mixed / peak * 0.9).astype(np.float32)
        except Exception:
            return audio

    def _rebuild_board(self):
        if not _PEDALBOARD_AVAILABLE or not self.enabled:
            self.board = None
            return

        profile = DSP_PROFILES.get(self.profile_key, DSP_PROFILES["canon_radio"])
        chain_type = profile.get("chain_type", "radio")

        hp = max(50.0, min(self.highpass_hz, 2000.0))
        lp = max(1000.0, min(self.lowpass_hz, 16000.0))
        dr = max(0.0, min(self.drive_db, 24.0))

        try:
            if chain_type == "radio":
                self.board = Pedalboard([
                    HighpassFilter(cutoff_frequency_hz=hp),
                    LowpassFilter(cutoff_frequency_hz=lp),
                    Distortion(drive_db=dr),
                    Gain(gain_db=2.0)
                ])
            elif chain_type == "walkie":
                self.board = Pedalboard([
                    HighpassFilter(cutoff_frequency_hz=hp),
                    LowpassFilter(cutoff_frequency_hz=lp),
                    PeakFilter(cutoff_frequency_hz=1600, gain_db=6.0, q=2.0),
                    Bitcrush(bit_depth=8),
                    Distortion(drive_db=dr),
                    Gain(gain_db=2.0)
                ])
            elif chain_type == "telephone":
                self.board = Pedalboard([
                    HighpassFilter(cutoff_frequency_hz=hp),
                    LowpassFilter(cutoff_frequency_hz=lp),
                    PeakFilter(cutoff_frequency_hz=1200, gain_db=4.0, q=1.5),
                    Distortion(drive_db=dr)
                ])
            elif chain_type == "megaphone":
                self.board = Pedalboard([
                    HighpassFilter(cutoff_frequency_hz=hp),
                    LowpassFilter(cutoff_frequency_hz=lp),
                    PeakFilter(cutoff_frequency_hz=1800, gain_db=8.0, q=1.8),
                    Distortion(drive_db=dr)
                ])
            elif chain_type == "demon":
                self.board = Pedalboard([
                    PitchShift(semitones=-2.5),
                    HighpassFilter(cutoff_frequency_hz=hp),
                    LowpassFilter(cutoff_frequency_hz=lp),
                    Distortion(drive_db=dr),
                    Reverb(room_size=0.35, wet_level=0.20)
                ])
            elif chain_type == "shadow":
                self.board = Pedalboard([
                    HighpassFilter(cutoff_frequency_hz=hp),
                    LowpassFilter(cutoff_frequency_hz=lp),
                    Delay(delay_seconds=0.15, feedback=0.3, mix=0.25),
                    Reverb(room_size=0.50, wet_level=0.30)
                ])
            elif chain_type == "studio_warm":
                self.board = Pedalboard([
                    Compressor(threshold_db=-16, ratio=2.5),
                    LowShelfFilter(cutoff_frequency_hz=180, gain_db=2.5),
                    HighShelfFilter(cutoff_frequency_hz=9000, gain_db=1.5),
                    Gain(gain_db=1.0)
                ])
            elif chain_type == "studio_crystal":
                self.board = Pedalboard([
                    Compressor(threshold_db=-14, ratio=2.0),
                    HighShelfFilter(cutoff_frequency_hz=10000, gain_db=2.5),
                    Gain(gain_db=0.5)
                ])
            elif chain_type == "studio_latenight":
                self.board = Pedalboard([
                    Compressor(threshold_db=-18, ratio=3.0),
                    LowShelfFilter(cutoff_frequency_hz=140, gain_db=4.0),
                    Reverb(room_size=0.2, wet_level=0.12),
                    Gain(gain_db=1.0)
                ])
            elif chain_type == "clean":
                self.board = None
            else:
                self.board = Pedalboard([
                    HighpassFilter(cutoff_frequency_hz=hp),
                    LowpassFilter(cutoff_frequency_hz=lp),
                    Distortion(drive_db=dr)
                ])
        except Exception:
            self.board = None

    def update_settings(self, profile_key: str = None,
                        highpass_hz: float = None, lowpass_hz: float = None,
                        drive_db: float = None, enabled: bool = None,
                        vinyl_intensity: float = None,
                        demon_layer: bool = None):
        if profile_key is not None:
            self.profile_key = profile_key
        if highpass_hz is not None:
            self.highpass_hz = float(highpass_hz)
        if lowpass_hz is not None:
            self.lowpass_hz = float(lowpass_hz)
        if drive_db is not None:
            self.drive_db = float(drive_db)
        if enabled is not None:
            self.enabled = bool(enabled)
        if vinyl_intensity is not None:
            self.vinyl_intensity = float(vinyl_intensity)
        if demon_layer is not None:
            self.demon_layer = bool(demon_layer)
        self._rebuild_board()

    def process(self, audio: np.ndarray, sample_rate: int, add_vinyl: bool = True) -> np.ndarray:
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        if np.max(np.abs(audio)) > 1.0:
            audio = audio / np.max(np.abs(audio))

        if not self.enabled:
            return audio.astype(np.float32)

        # 1. Apply demonic Alastor layer (pitch -4 semitones, 12ms Haas shift, 5.5Hz tremolo, tanh rasp)
        if self.demon_layer:
            audio = self.alastor_layer(audio, sample_rate)

        # 2. Primary DSP filtering (Pedalboard or Scipy fallback)
        if self.board is not None:
            try:
                out = self.board(audio, sample_rate)
            except Exception:
                out = self._scipy_fallback(audio, sample_rate)
        else:
            out = audio.copy()

        # 3. Add subtle vintage vinyl crackle & room noise
        if add_vinyl and self.vinyl_intensity > 0 and len(out) > 0:
            out = self._mix_vinyl_crackle(out, self.vinyl_intensity)

        # 4. Peak normalization to avoid digital clipping or low levels
        peak = np.max(np.abs(out))
        if peak > 0.95:
            out = out / peak * 0.92
        elif peak > 0 and peak < 0.25:
            out = out / peak * 0.85

        return out.astype(np.float32)

    def _scipy_fallback(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        if not _SCIPY_AVAILABLE:
            return np.tanh(audio * 1.5)

        nyq = sample_rate / 2.0
        low = min(max(self.highpass_hz / nyq, 0.01), 0.45)
        high = min(max(self.lowpass_hz / nyq, 0.05), 0.90)
        if low >= high:
            low = 0.05
            high = 0.85

        b, a = scipy.signal.butter(4, [low, high], btype='bandpass')
        filtered = scipy.signal.lfilter(b, a, audio)
        saturated = np.tanh(filtered * (1.0 + self.drive_db / 5.0))
        return saturated

    @staticmethod
    def _mix_vinyl_crackle(audio: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        length = len(audio)
        scale = max(0.0, min(float(intensity), 3.0))
        if scale <= 0:
            return audio
        noise = np.random.normal(0, 0.012 * scale, length).astype(np.float32)
        pop_prob = min(0.0004 * scale, 0.005)
        pop_mask = np.random.random(length) < pop_prob
        pops = np.zeros(length, dtype=np.float32)
        pops[pop_mask] = np.random.uniform(-0.08 * scale, 0.08 * scale, np.sum(pop_mask))

        crackle = noise + pops
        return audio + crackle
