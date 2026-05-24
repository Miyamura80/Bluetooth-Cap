"""Real-time audio capture using sounddevice (PortAudio)."""

import numpy as np
import sounddevice as sd


class AudioCapture:
    """Continuously captures audio and exposes the latest FFT magnitudes."""

    def __init__(
        self,
        sample_rate: int = 44100,
        block_size: int = 2048,
        num_bands: int = 32,
        device: int | None = None,
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.num_bands = num_bands
        self.device = device
        self._magnitudes = np.zeros(num_bands, dtype=np.float64)
        self._smoothed = np.zeros(num_bands, dtype=np.float64)
        self._stream: sd.InputStream | None = None
        self._peak = 1.0
        self._band_edges = self._build_log_bands()

    def _build_log_bands(self) -> np.ndarray:
        """Log-spaced frequency bin edges focused on voice range."""
        min_freq = 80.0
        max_freq = 2500.0
        return np.geomspace(min_freq, max_freq, self.num_bands + 1)

    def _audio_callback(
        self,
        indata: np.ndarray,
        _frames: int,
        _time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        mono = indata[:, 0]
        spectrum = np.abs(np.fft.rfft(mono))
        freqs = np.fft.rfftfreq(len(mono), 1.0 / self.sample_rate)

        bands = np.zeros(self.num_bands, dtype=np.float64)
        for i in range(self.num_bands):
            mask = (freqs >= self._band_edges[i]) & (freqs < self._band_edges[i + 1])
            if np.any(mask):
                bands[i] = np.mean(spectrum[mask])

        current_peak = np.max(bands)
        if current_peak > self._peak:
            self._peak = current_peak
        else:
            self._peak = self._peak * 0.97 + current_peak * 0.03

        if self._peak > 0:
            bands /= self._peak

        rise = 0.6
        decay = 0.15
        for i in range(self.num_bands):
            if bands[i] > self._smoothed[i]:
                self._smoothed[i] += (bands[i] - self._smoothed[i]) * rise
            else:
                self._smoothed[i] += (bands[i] - self._smoothed[i]) * decay

        self._magnitudes = self._smoothed.copy()

    def start(self) -> None:
        self._stream = sd.InputStream(
            device=self.device,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    @property
    def magnitudes(self) -> np.ndarray:
        return self._magnitudes.copy()
