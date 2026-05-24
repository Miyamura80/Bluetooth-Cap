"""Unified audio capture: real-time FFT spectrum + streaming PCM output."""

from collections.abc import Callable

import numpy as np
import sounddevice as sd


class UnifiedCapture:
    """Captures audio for both spectrum visualization and streaming transcription.

    The sounddevice callback runs on every block:
    - Computes FFT and updates spectrum magnitudes (for visualization)
    - Forwards raw PCM int16 bytes to a callback (for streaming transcription)
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        block_size: int = 1024,
        num_bands: int = 32,
        device: int | None = None,
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.num_bands = num_bands
        self.device = device

        self._magnitudes = np.zeros(num_bands, dtype=np.float64)
        self._smoothed = np.zeros(num_bands, dtype=np.float64)
        self._peak = 1.0
        self._band_edges = np.geomspace(80.0, 2500.0, num_bands + 1)

        self._stream: sd.InputStream | None = None
        self._on_audio: Callable[[bytes], None] | None = None

    def _callback(
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

        rise, decay = 0.6, 0.15
        for i in range(self.num_bands):
            if bands[i] > self._smoothed[i]:
                self._smoothed[i] += (bands[i] - self._smoothed[i]) * rise
            else:
                self._smoothed[i] += (bands[i] - self._smoothed[i]) * decay
        self._magnitudes = self._smoothed.copy()

        if self._on_audio:
            int16 = (mono * 32767).astype(np.int16)
            self._on_audio(int16.tobytes())

    def start(self, on_audio: Callable[[bytes], None] | None = None) -> None:
        self._on_audio = on_audio
        self._stream = sd.InputStream(
            device=self.device,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            dtype="float32",
            callback=self._callback,
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
