"""
Deepgram Speech-to-Text service integration.

Design Philosophy:
- Abstraction layer for STT (easy to swap providers)
- Dependency injection of API key
- Immutable result objects
- Type-safe parameter passing
"""

from dataclasses import dataclass
from deepgram import DeepgramClient, PrerecordedOptions


@dataclass(frozen=True)
class TranscriptionResult:
    """
    Immutable result from speech-to-text operation.
    
    Frozen dataclass ensures result cannot be modified after creation.
    Confidence score indicates STT reliability (0.0-1.0).
    """
    transcript: str
    confidence: float
    is_empty: bool = False


class AudioService:
    """
    Deepgram STT service wrapper.
    
    Responsibilities:
    - Convert audio bytes to text using Deepgram API
    - Handle errors gracefully
    - Return structured results
    
    Optimization for sub-2s latency:
    - Uses prerecorded API (not streaming) since we process complete commands
    - Deepgram Nova-3 is fastest model available
    - smart_format reduces downstream processing time
    """
    
    def __init__(self, api_key: str, model: str = "nova-3") -> None:
        """
        Initialize Deepgram service.
        
        Args:
            api_key: Deepgram API key from environment
            model: STT model to use (default: nova-3, fastest/most accurate)
        """
        self._client = DeepgramClient(api_key=api_key)
        self._model = model
    
    def transcribe(
        self,
        audio_bytes: bytes,
        mimetype: str = "audio/webm"
    ) -> TranscriptionResult:
        """
        Convert audio bytes to text with error handling.
        
        Args:
            audio_bytes: Audio data as bytes (typically from browser recording)
            mimetype: Audio format (default: webm from browser MediaRecorder)
            
        Returns:
            TranscriptionResult with transcript and confidence
            
        Raises:
            ValueError: If transcription fails
        """
        if not audio_bytes:
            return TranscriptionResult(
                transcript="",
                confidence=0.0,
                is_empty=True
            )
        
        try:
            # Configure Deepgram for optimal quality and speed
            options = PrerecordedOptions(
                model=self._model,           # Nova-3: fastest + most accurate
                smart_format=True,           # Auto-punctuation and capitalization
                language="en",               # Optimize for English
                punctuate=True               # Ensure proper punctuation
            )
            
            # Prepare file source as a dict (avoid calling a UnionType)
            source = {
                "buffer": audio_bytes,
                "mimetype": mimetype
            }
            
            # Call Deepgram API (typically 200-300ms)
            response = self._client.listen.prerecorded.v("1").transcribe_file(
                source,
                options
            )
            
            # Extract transcript from response hierarchy
            alternatives = response.results.channels[0].alternatives
            if not alternatives:
                return TranscriptionResult(
                    transcript="",
                    confidence=0.0
                )
            
            # Get first (best) alternative
            transcript = alternatives[0].transcript.strip()
            confidence = getattr(alternatives[0], 'confidence', 0.9)
            
            return TranscriptionResult(
                transcript=transcript,
                confidence=confidence
            )
        
        except Exception as e:
            # Wrap in ValueError for consistent error handling
            raise ValueError(f"Transcription failed: {str(e)}")