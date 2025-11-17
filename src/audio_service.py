import os
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
import asyncio

class AudioProcessor:
    """Handle speech-to-text with Deepgram"""
    
    def __init__(self):
        self.deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
    
    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio to text using Deepgram Nova-3
        Optimized for low latency and high accuracy
        """
        try:
            # Configure for optimal real-time performance
            options = PrerecordedOptions(
                model="nova-3",  # Latest, fastest model
                smart_format=True,  # Auto punctuation/capitalization
                language="en",
                punctuate=True,
                utterances=False,  # Disable for lower latency
                diarize=False
            )
            
            # Create file source from bytes
            source = FileSource(
                buffer=audio_bytes,
                mimetype="audio/webm"  # WebM from browser recording
            )
            
            # Transcribe
            response = self.deepgram.listen.prerecorded.v("1").transcribe_file(
                source, options
            )
            
            # Extract transcript
            transcript = response.results.channels[0].alternatives[0].transcript
            return transcript.strip()
        
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
