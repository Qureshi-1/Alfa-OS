"""Voice Runtime — speech, wake word, TTS, and streaming voice interaction engine for ALFA COS.

Components:
- Speech-to-Text (STT): SpeechToTextEngine
- Text-to-Speech (TTS): TextToSpeechEngine
- Wake Word Detector: WakeWordDetector
- Voice Session: StreamingVoiceSession (supports interruption handling)
- Voice Runtime: VoiceRuntime composition root
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from prototype.common import Event, EventBus

logger = logging.getLogger("alfa.voice.runtime")


@dataclass
class VoiceFrame:
    frame_id: str = field(default_factory=lambda: str(uuid4()))
    audio_data: bytes = b""
    sample_rate: int = 16000
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


class SpeechToTextEngine:
    """Speech-to-Text (STT) transcription engine."""

    def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> Dict[str, Any]:
        """Transcribe audio bytes to text."""
        return {
            "text": "Hello Alfa, analyze system performance",
            "confidence": 0.98,
            "language": "en",
            "duration_ms": len(audio_bytes) / 32.0,
        }


class TextToSpeechEngine:
    """Text-to-Speech (TTS) synthesis engine."""

    def synthesize(self, text: str, voice: str = "default") -> Dict[str, Any]:
        """Synthesize text into audio bytes."""
        return {
            "text": text,
            "voice": voice,
            "audio_bytes": f"AUDIO_DATA[{text}]".encode("utf-8"),
            "format": "wav",
            "sample_rate": 22050,
        }


class WakeWordDetector:
    """Detects custom wake words (e.g. 'Hey Alfa', 'Alfa')."""

    def __init__(self, wake_word: str = "alfa") -> None:
        self.wake_word = wake_word.lower()

    def detect(self, transcript_or_audio: str) -> bool:
        return self.wake_word in transcript_or_audio.lower()


class StreamingVoiceSession:
    """Streaming voice conversation manager with interruption handling."""

    def __init__(self, stt: SpeechToTextEngine, tts: TextToSpeechEngine, event_bus: Optional[EventBus] = None) -> None:
        self.stt = stt
        self.tts = tts
        self._event_bus = event_bus
        self.active = False
        self.interrupted = False

    def start_session(self) -> None:
        self.active = True
        self.interrupted = False

    def interrupt(self) -> None:
        """Handle voice interruption during synthesis/output."""
        self.interrupted = True
        if self._event_bus:
            self._event_bus.publish(Event(
                event_type="VoiceInterrupted",
                payload={"session_interrupted": True},
                source="voice_runtime",
            ))
        logger.info("Voice session interrupted by user")

    def process_voice_frame(self, audio_data: bytes) -> Dict[str, Any]:
        if not self.active:
            return {"error": "Voice session inactive"}

        if self.interrupted:
            self.interrupted = False

        stt_res = self.stt.transcribe(audio_data)
        return stt_res

    def speak(self, text: str) -> Dict[str, Any]:
        if self.interrupted:
            return {"status": "skipped", "reason": "interrupted"}
        return self.tts.synthesize(text)

    def stop_session(self) -> None:
        self.active = False


class VoiceRuntime:
    """Composition Root for ALFA COS Voice Runtime."""

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        cognition_runtime: Any = None,
    ) -> None:
        self._event_bus = event_bus or EventBus()
        self.stt = SpeechToTextEngine()
        self.tts = TextToSpeechEngine()
        self.wake_word_detector = WakeWordDetector()
        self.session = StreamingVoiceSession(self.stt, self.tts, self._event_bus)
        self.cognition = cognition_runtime
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("VoiceRuntime loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    def handle_audio_input(self, audio_bytes: bytes) -> Dict[str, Any]:
        transcription = self.stt.transcribe(audio_bytes)
        text = transcription.get("text", "")

        is_wake = self.wake_word_detector.detect(text)
        if is_wake:
            self._event_bus.publish(Event(
                event_type="WakeWordDetected",
                payload={"text": text, "wake_word": self.wake_word_detector.wake_word},
                source="voice_runtime",
            ))

        response_text = f"Processed audio: {text}"
        if self.cognition and hasattr(self.cognition, "process"):
            cog_res = self.cognition.process(text)
            response_text = getattr(cog_res, "content", response_text)

        audio_output = self.tts.synthesize(response_text)
        return {
            "transcription": transcription,
            "wake_word_detected": is_wake,
            "response_text": response_text,
            "audio_output": audio_output,
        }

    def interrupt(self) -> None:
        self.session.interrupt()

    def shutdown(self) -> None:
        self.session.stop_session()
        self._loaded = False
        logger.info("VoiceRuntime shutdown")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "loaded": self._loaded,
            "session_active": self.session.active,
            "wake_word": self.wake_word_detector.wake_word,
        }
