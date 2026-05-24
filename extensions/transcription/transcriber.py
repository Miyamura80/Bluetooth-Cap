"""AssemblyAI v3 real-time streaming transcription."""

import os
import threading
from collections.abc import Callable

import assemblyai as aai
from assemblyai.streaming.v3 import (
    SpeechModel,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    TurnEvent,
)


class Transcriber:
    """Streams audio to AssemblyAI v3 and collects transcribed text."""

    def __init__(self) -> None:
        aai.settings.api_key = os.environ.get("ASSEMBLY_AI_API_KEY", "")
        self._client: StreamingClient | None = None
        self._on_text: Callable[[str], None] | None = None
        self._error: str | None = None
        self._lock = threading.Lock()

    def start(self, on_text: Callable[[str], None], sample_rate: int = 16000) -> None:
        self._on_text = on_text

        self._client = StreamingClient(
            StreamingClientOptions(api_key=aai.settings.api_key)
        )

        def on_turn(_client: StreamingClient, event: TurnEvent) -> None:
            if event.end_of_turn:
                text = event.transcript.strip()
                if text and self._on_text:
                    self._on_text(text)

        def on_error(_client: StreamingClient, error: StreamingError) -> None:
            with self._lock:
                self._error = str(error)

        self._client.on(StreamingEvents.Turn, on_turn)
        self._client.on(StreamingEvents.Error, on_error)

        self._client.connect(
            StreamingParameters(
                sample_rate=sample_rate,
                speech_model=SpeechModel.universal_streaming_english,
            )
        )

    def send_audio(self, pcm_data: bytes) -> None:
        if self._client:
            self._client.stream(pcm_data)

    def get_error(self) -> str | None:
        with self._lock:
            err = self._error
            self._error = None
            return err

    def stop(self) -> None:
        if self._client:
            self._client.disconnect()
            self._client = None
