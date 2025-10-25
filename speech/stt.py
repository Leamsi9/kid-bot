import asyncio
import io
import gc
import torch
from faster_whisper import WhisperModel

class STT:
    def __init__(self, model):
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        # Use int8 quantization on CPU for much faster inference
        compute_type = 'int8' if device == 'cpu' else 'float16'
        self.model = WhisperModel(
            model, 
            device=device,
            compute_type=compute_type,
            cpu_threads=4,  # Limit CPU threads to prevent overload
            num_workers=1   # Single worker to reduce memory
        )

    async def transcribe(self, audio_bytes):
        # audio_bytes is PCM16k mono bytes
        def _transcribe():
            # Convert bytes to ndarray
            import numpy as np
            pcm = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Log audio level for diagnostics
            audio_level = np.abs(pcm).max()
            audio_rms = np.sqrt(np.mean(pcm**2))
            print(f"Audio level - Max: {audio_level:.3f}, RMS: {audio_rms:.3f}")
            
            try:
                # Optimize transcription settings for speed
                # Disable VAD filter to see if that's causing empty transcriptions
                segments, _ = self.model.transcribe(
                    pcm, 
                    language='en',
                    beam_size=1,           # Greedy decoding for speed
                    best_of=1,             # No alternative sampling
                    temperature=0,         # Deterministic output
                    vad_filter=False,      # Disable VAD - we already have VAD in pipeline
                    condition_on_previous_text=False  # Don't use context (faster)
                )
                result = ''.join(s.text for s in segments)
            finally:
                # Explicit cleanup
                del pcm
                gc.collect()
            
            return result
        return await asyncio.to_thread(_transcribe)
