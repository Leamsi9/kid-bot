import io
import asyncio
import wave
from piper import PiperVoice

class TTS:
    def __init__(self):
        try:
            # Load a child-friendly voice, e.g., en_US-amy-medium
            self.voice = PiperVoice.load('en_US-amy-medium')
        except FileNotFoundError:
            print("Piper voice 'en_US-amy-medium' not found. Download from https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-amy-medium.tar.gz and extract to project root.")
            self.voice = None

    async def speak(self, text):
        if not self.voice:
            # Fallback: return empty audio if voice not loaded
            return b'', []
        # Generate audio to temporary file
        import tempfile
        import os
        def _speak():
            # Create temp file for WAV output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            try:
                # Piper synthesize writes to a wave file object
                with wave.open(tmp_path, 'wb') as wav_file:
                    self.voice.synthesize(text, wav_file)
                # Read the WAV file
                with open(tmp_path, 'rb') as f:
                    wav_data = f.read()
                return wav_data
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        wav = await asyncio.to_thread(_speak)
        # Return audio and empty phonemes list (phoneme extraction not supported in this Piper version)
        return wav, []
